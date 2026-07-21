"""Chat API for streaming conversation with the orchestrator agent.

This module provides REST endpoints for real-time chat interactions via Server-Sent Events (SSE),
integrating with the LangGraph orchestrator to handle multi-agent novel generation workflows.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.messages.utils import count_tokens_approximately, trim_messages
from pydantic import BaseModel

from app.core.errors import AIError, ErrorCode, classify_llm_error
from app.core.graph.builder import create_orchestrator_graph
from app.core.graph.state import OrchestratorState
from app.core.logging_utils import get_logger, log_ai_error, log_stream_complete
from app.core.serialization_utils import safe_json_value
from app.db.checkpointer import get_checkpointer
from app.db.connection import get_db
from app.services.content import ContentService
from app.services.novel_context_builder import NovelContextBuilder
from app.services.project_repository import get_project
from app.services.session_repository import (
    create_session,
    delete_session,
    get_session,
    list_sessions_by_project,
    update_session_activity,
    verify_project_binding,
)

router = APIRouter(prefix="/projects/{project_id}/sessions", tags=["chat"])

logger = get_logger("chat")

MAX_HISTORY_TOKENS = 12000
MAX_HISTORY_MESSAGES = 40


class CreateSessionRequest(BaseModel):
    """Request payload for creating a new chat session.

    Attributes:
        title: Optional human-readable title for the session.
    """

    title: str | None = None


class ChatRequest(BaseModel):
    """Request payload for sending a chat message.

    Attributes:
        message: The user's message content to send to the orchestrator agent.
    """

    message: str


def _messages_to_history_dicts(messages: list[BaseMessage]) -> list[dict[str, Any]]:
    """Convert LangChain BaseMessage objects to frontend-compatible history dicts.

    Args:
        messages: List of LangChain BaseMessage objects from the graph state.

    Returns:
        List of dictionaries with keys: role, content, thinking_content, tool_calls, tool_call_id.
    """
    result = []
    for msg in messages:
        entry: dict[str, Any] = {
            "role": "",
            "content": "",
            "thinking_content": None,
            "tool_calls": None,
            "tool_call_id": None,
        }
        if isinstance(msg, HumanMessage):
            entry["role"] = "user"
            entry["content"] = msg.content
        elif isinstance(msg, AIMessage):
            entry["role"] = "assistant"
            if msg.tool_calls:
                entry["tool_calls"] = msg.tool_calls
            # Handle content: may be string or list of blocks (extended thinking)
            if isinstance(msg.content, list):
                text_parts = []
                thinking = None
                if hasattr(msg, "additional_kwargs"):
                    thinking = msg.additional_kwargs.get("thinking")
                for block in msg.content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                    elif block.get("type") == "thinking" and not thinking:
                        thinking = block.get("thinking", "")
                entry["content"] = "".join(text_parts)
                if thinking:
                    entry["thinking_content"] = thinking
            else:
                entry["content"] = msg.content
                thinking = None
                if hasattr(msg, "additional_kwargs"):
                    thinking = msg.additional_kwargs.get("thinking")
                if thinking:
                    entry["thinking_content"] = thinking
        elif isinstance(msg, ToolMessage):
            entry["role"] = "tool"
            entry["content"] = msg.content
            entry["tool_call_id"] = msg.tool_call_id
        result.append(entry)
    return result


@router.post("/{session_id}/chat/stream")
async def chat_stream_endpoint(
    project_id: str,
    session_id: str,
    request: ChatRequest,
) -> StreamingResponse:
    """Stream chat responses via SSE using the orchestrator graph.

    Args:
        project_id: ID of the project this session belongs to.
        session_id: ID of the chat session to stream messages for.
        request: ChatRequest containing the user's message.

    Returns:
        StreamingResponse with SSE events for tokens, thinking, tool calls, and errors.

    Raises:
        HTTPException: 403 if session does not belong to project, 404 if session not found.
    """
    async with get_db() as db:
        is_valid = await verify_project_binding(db, session_id, project_id)
        if not is_valid:
            raise HTTPException(
                status_code=403,
                detail="Session does not belong to this project",
            )

        session = await get_session(db, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        await update_session_activity(db, session_id)

        content_service = ContentService(db)
        project, world_settings, characters, outline, chapters = await asyncio.gather(
            get_project(db, project_id),
            content_service.get_all_world_settings(project_id),
            content_service.get_all_characters(project_id),
            content_service.get_root_outline(project_id),
            content_service.get_all_chapters(project_id),
        )
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Build novel-specific context (last 2 chapters, foreshadowing, protagonist)
        novel_context_str: str = ""
        try:
            novel_builder = NovelContextBuilder(db)
            novel_context_str = await novel_builder.build_context(
                project_id=project_id,
                characters=characters,
                chapters_meta=chapters,
            )
        except Exception:
            logger.warning("Failed to build novel context (non-blocking)", exc_info=True)

    checkpointer = await get_checkpointer()
    graph = create_orchestrator_graph(project_id, checkpointer=checkpointer, novel_context=novel_context_str)

    config = {"configurable": {"thread_id": session_id}}

    # Retrieve existing history and truncate to prevent state bloat
    try:
        existing_state = await graph.aget_state(config)
        existing_messages = existing_state.values.get("messages", []) if hasattr(existing_state, "values") else []
    except Exception:
        existing_messages = []

    try:
        truncated_history = trim_messages(
            existing_messages,
            strategy="last",
            token_counter=count_tokens_approximately,
            max_tokens=MAX_HISTORY_TOKENS,
            start_on="human",
            end_on=("human", "tool"),
        )
    except Exception:
        # Fallback: truncate by message count if token trimming fails
        truncated_history = (
            existing_messages[-MAX_HISTORY_MESSAGES:]
            if len(existing_messages) > MAX_HISTORY_MESSAGES
            else existing_messages
        )

    messages = list(truncated_history) + [HumanMessage(content=request.message)]

    initial_state: OrchestratorState = {
        "messages": messages,
        "session_id": session_id,
        "project_id": project_id,
        "project_context": {
            "project_name": project["name"],
            "project_description": project.get("description"),
            "world_settings": world_settings,
            "characters": characters,
            "outline": outline,
            "chapters": chapters,
        },
    }

    async def stream_with_save() -> AsyncGenerator[str, Any]:
        """Async generator that streams events from the orchestrator graph using v2 streaming.

        Uses graph.astream() with stream_mode=["messages", "updates", "custom"]
        and subgraphs=True to get structured StreamPart chunks with namespace info.

        Yields SSE-formatted strings with event types:
            - 'messages': LLM tokens with source attribution
            - 'updates': Tool start/end events
            - 'custom': Progress updates from sub-agents
            - 'done': Stream completion with full content
            - 'error': Error details
        """
        full_content: list[str] = []
        full_thinking: list[str] = []
        event_counter = 0
        stream_error = False
        seen_tool_starts: set[str] = set()
        seen_tool_ends: set[str] = set()

        def next_id() -> int:
            nonlocal event_counter
            event_counter += 1
            return event_counter

        try:
            async for chunk in graph.astream(
                initial_state,
                config,
                stream_mode=["messages", "updates", "custom"],
                subgraphs=True,
                version="v2",
                recursion_limit=25,
            ):
                chunk_type = chunk["type"]
                chunk_data = chunk["data"]

                if chunk_type == "messages":
                    token, metadata = chunk_data
                    # Skip ToolMessage — already handled by the updates stream
                    if isinstance(token, ToolMessage):
                        continue
                    source = metadata.get("lc_agent_name", "orchestrator")

                    # Handle content blocks (list) or plain string
                    if isinstance(token.content, list):
                        for block in token.content:
                            if not isinstance(block, dict):
                                continue
                            block_type = block.get("type", "")
                            if block_type == "thinking":
                                thinking_text = block.get("thinking", "")
                                if thinking_text:
                                    full_thinking.append(thinking_text)
                                    payload = json.dumps(safe_json_value({"thinking": thinking_text, "source": source}))
                                    yield f"event: messages\nid: {next_id()}\ndata: {payload}\n\n"
                            elif block_type == "text":
                                text = block.get("text", "")
                                if text:
                                    full_content.append(text)
                                    payload = json.dumps(
                                        safe_json_value(
                                            {
                                                "token": text,
                                                "source": source,
                                                "langgraph_node": metadata.get("langgraph_node", "agent"),
                                            }
                                        )
                                    )
                                    yield f"event: messages\nid: {next_id()}\ndata: {payload}\n\n"
                    elif isinstance(token.content, str) and token.content:
                        full_content.append(token.content)
                        payload = json.dumps(
                            safe_json_value(
                                {
                                    "token": token.content,
                                    "source": source,
                                    "langgraph_node": metadata.get("langgraph_node", "agent"),
                                }
                            )
                        )
                        yield f"event: messages\nid: {next_id()}\ndata: {payload}\n\n"

                elif chunk_type == "updates":
                    for _node_name, data in chunk_data.items():
                        msgs = data.get("messages", []) if isinstance(data, dict) else []
                        for msg in msgs:
                            # Tool call start (dedupe by tool_call_id)
                            if hasattr(msg, "tool_calls") and msg.tool_calls:
                                for tc in msg.tool_calls:
                                    tc_id = tc.get("id", "")
                                    if tc_id and tc_id in seen_tool_starts:
                                        continue
                                    if tc_id:
                                        seen_tool_starts.add(tc_id)
                                    payload = json.dumps(
                                        safe_json_value(
                                            {
                                                "type": "tool_start",
                                                "tool": tc.get("name", ""),
                                                "tool_call_id": tc_id,
                                                "args": tc.get("args", {}),
                                            }
                                        )
                                    )
                                    yield f"event: updates\nid: {next_id()}\ndata: {payload}\n\n"

                            # Tool message (result, dedupe by tool_call_id)
                            if isinstance(msg, ToolMessage):
                                tc_id = getattr(msg, "tool_call_id", "")
                                if tc_id and tc_id in seen_tool_ends:
                                    continue
                                if tc_id:
                                    seen_tool_ends.add(tc_id)
                                payload = json.dumps(
                                    safe_json_value(
                                        {
                                            "type": "tool_end",
                                            "tool": getattr(msg, "name", ""),
                                            "tool_call_id": tc_id,
                                            "result": msg.content,
                                        }
                                    )
                                )
                                yield f"event: updates\nid: {next_id()}\ndata: {payload}\n\n"

                elif chunk_type == "custom":
                    payload = json.dumps(safe_json_value(chunk_data))
                    yield f"event: custom\nid: {next_id()}\ndata: {payload}\n\n"

        except AIError as exc:
            error_payload = {
                "error_code": exc.error_code.value if exc.error_code else ErrorCode.UNKNOWN.value,
                "message": exc.message,
                "retryable": exc.retryable,
            }
            yield f"event: error\nid: {next_id()}\ndata: {json.dumps(safe_json_value(error_payload))}\n\n"
            stream_error = True
            log_ai_error(
                logger,
                exc,
                session_id=session_id,
                project_id=project_id,
                user_content=request.message,
            )
        except Exception as exc:
            classified = classify_llm_error(exc)
            error_payload = {
                "error_code": classified.error_code.value if classified.error_code else ErrorCode.UNKNOWN.value,
                "message": str(exc),
                "retryable": classified.retryable,
            }
            yield f"event: error\nid: {next_id()}\ndata: {json.dumps(safe_json_value(error_payload))}\n\n"
            stream_error = True
            log_ai_error(
                logger,
                classified,
                session_id=session_id,
                project_id=project_id,
                user_content=request.message,
            )

        # Send done event (skip if an error occurred)
        if not stream_error:
            combined_content = "".join(full_content)
            combined_thinking = "".join(full_thinking)
            done_payload = {"full_content": combined_content, "full_thinking": combined_thinking}
            yield f"event: done\nid: {next_id()}\ndata: {json.dumps(safe_json_value(done_payload))}\n\n"

            if combined_content or combined_thinking:
                log_stream_complete(
                    logger, session_id=session_id, token_count=len(combined_content) + len(combined_thinking)
                )

    return StreamingResponse(
        stream_with_save(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/")
async def create_session_endpoint(
    project_id: str,
    request: CreateSessionRequest | None = None,
) -> dict[str, Any]:
    """Create a new chat session.

    Args:
        project_id: ID of the project to create the session under.
        request: Optional payload containing the session title.

    Returns:
        Dictionary containing the created session data with id, title, and timestamps.
    """
    title = request.title if request else None
    async with get_db() as db:
        session = await create_session(db, project_id, title=title)
        return session


@router.get("/")
async def list_sessions_endpoint(project_id: str, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
    """List all sessions for a project with pagination.

    Args:
        project_id: ID of the project to list sessions for.
        limit: Maximum number of sessions to return (default 50).
        offset: Number of sessions to skip for pagination (default 0).

    Returns:
        List of session dictionaries ordered by last activity.
    """
    async with get_db() as db:
        sessions = await list_sessions_by_project(db, project_id, limit, offset)
        return sessions


@router.delete("/{session_id}")
async def delete_session_endpoint(project_id: str, session_id: str) -> dict[str, str]:
    """Delete a session and its checkpoint thread.

    Args:
        project_id: ID of the project the session belongs to.
        session_id: ID of the session to delete.

    Returns:
        Dictionary with status 'deleted' and the deleted session_id.

    Raises:
        HTTPException: 403 if session does not belong to project.
    """
    async with get_db() as db:
        is_valid = await verify_project_binding(db, session_id, project_id)
        if not is_valid:
            raise HTTPException(
                status_code=403,
                detail="Session does not belong to this project",
            )
        await delete_session(db, session_id)

    # Delete checkpoint thread for this session
    checkpointer = await get_checkpointer()
    await checkpointer.adelete_thread(session_id)

    return {"status": "deleted", "session_id": session_id}


@router.get("/{session_id}/history")
async def get_chat_history_endpoint(project_id: str, session_id: str) -> list[dict[str, Any]]:
    """Get chat history for a session from the checkpointer.

    Args:
        project_id: ID of the project the session belongs to.
        session_id: ID of the session to retrieve history for.

    Returns:
        List of message dictionaries converted from LangChain BaseMessage objects.

    Raises:
        HTTPException: 403 if session does not belong to project.
    """
    async with get_db() as db:
        is_valid = await verify_project_binding(db, session_id, project_id)
        if not is_valid:
            raise HTTPException(
                status_code=403,
                detail="Session does not belong to this project",
            )

    checkpointer = await get_checkpointer()
    graph = create_orchestrator_graph(project_id, checkpointer=checkpointer)
    config = {"configurable": {"thread_id": session_id}}

    try:
        state = await graph.aget_state(config)
    except Exception:
        return []

    messages = state.values.get("messages", []) if hasattr(state, "values") else []
    return _messages_to_history_dicts(messages)
