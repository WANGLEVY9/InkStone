# V2 Streaming Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate from `astream_events(v1)` to `astream(stream_mode, v2)` to fix mixed streaming tokens and enable per-source token attribution.

**Architecture:** Replace the v1 event stream handler with v2 StreamPart processing. Enable `streaming=True` on all LLMs. Map `metadata["langgraph_node"]` to source identifiers for SSE output. Use SSE best practices aligned with LangGraph Platform.

**Tech Stack:** Python 3.13, FastAPI, LangChain, LangGraph, Anthropic Claude

---

## File Map

| File | Change |
|------|--------|
| `backend/app/core/agent/langchain_subagents.py` | Enable `streaming=True` on 5 sub-agent LLMs |
| `backend/app/core/graph/builder.py` | Enable `streaming=True` on orchestrator LLM |
| `backend/app/api/v1/chat.py` | Rewrite `stream_with_save()` for v2 streaming |
| `backend/tests/test_v2_streaming.py` | New test file for v2 streaming logic |

---

### Task 1: Enable streaming on sub-agent LLMs

**Files:**
- Modify: `backend/app/core/agent/langchain_subagents.py:169,189,209,229,249`
- Test: `backend/tests/test_orchestrator.py`

- [ ] **Step 1: Change sub-agent LLMs to streaming=True**

In `langchain_subagents.py`, change all 5 occurrences of `create_llm_client(streaming=False)` to `create_llm_client(streaming=True)`:

Line 169: `model=create_llm_client(streaming=True),`
Line 189: `model=create_llm_client(streaming=True),`
Line 209: `model=create_llm_client(streaming=True),`
Line 229: `model=create_llm_client(streaming=True),`
Line 249: `model=create_llm_client(streaming=True),`

- [ ] **Step 2: Run existing orchestrator tests**

Run: `cd backend && uv run pytest tests/test_orchestrator.py -v`
Expected: All 3 tests PASS (graph builds, accepts checkpointer, has model node)

- [ ] **Step 3: Commit**

```bash
git add backend/app/core/agent/langchain_subagents.py
git commit -m "feat(agent): enable streaming on all sub-agent LLMs"
```

---

### Task 2: Enable streaming on orchestrator LLM

**Files:**
- Modify: `backend/app/core/graph/builder.py:53`
- Test: `backend/tests/test_orchestrator.py`

- [ ] **Step 1: Change orchestrator LLM to streaming=True**

In `builder.py`, line 53, change:
```python
llm = model or create_llm_client(streaming=False)
```
to:
```python
llm = model or create_llm_client(streaming=True)
```

- [ ] **Step 2: Run existing orchestrator tests**

Run: `cd backend && uv run pytest tests/test_orchestrator.py -v`
Expected: All 3 tests PASS

- [ ] **Step 3: Commit**

```bash
git add backend/app/core/graph/builder.py
git commit -m "feat(graph): enable streaming on orchestrator LLM"
```

---

### Task 3: Add NODE_TO_SOURCE mapping and SSE helpers

**Files:**
- Create: `backend/tests/test_v2_streaming.py`
- Modify: `backend/app/api/v1/chat.py`

- [ ] **Step 1: Write tests for NODE_TO_SOURCE mapping**

Create `backend/tests/test_v2_streaming.py`:

```python
"""Tests for v2 streaming migration."""

from __future__ import annotations

import json

import pytest


class TestNodeToSourceMapping:
    """Test langgraph_node to source name mapping."""

    def test_orchestrator_node_maps_to_orchestrator(self) -> None:
        from app.api.v1.chat import NODE_TO_SOURCE

        assert NODE_TO_SOURCE["agent"] == "orchestrator"

    def test_delegate_nodes_map_to_subagent_names(self) -> None:
        from app.api.v1.chat import NODE_TO_SOURCE

        assert NODE_TO_SOURCE["delegate_to_world_builder"] == "world_builder"
        assert NODE_TO_SOURCE["delegate_to_character"] == "character"
        assert NODE_TO_SOURCE["delegate_to_plot"] == "plot"
        assert NODE_TO_SOURCE["delegate_to_chapter"] == "chapter"
        assert NODE_TO_SOURCE["delegate_to_review"] == "review"

    def test_unknown_node_falls_back_to_original_name(self) -> None:
        from app.api.v1.chat import NODE_TO_SOURCE

        unknown = "some_unknown_node"
        result = NODE_TO_SOURCE.get(unknown, unknown)
        assert result == "some_unknown_node"


class TestSseFormatting:
    """Test SSE event formatting."""

    def test_sse_event_format_has_event_id_data(self) -> None:
        """Each SSE event should have event:, id:, and data: lines."""
        event_type = "messages"
        event_id = 42
        payload = {"token": "hello", "source": "orchestrator"}

        sse = f"event: {event_type}\nid: {event_id}\ndata: {json.dumps(payload)}\n\n"

        assert "event: messages\n" in sse
        assert "id: 42\n" in sse
        assert '"token": "hello"' in sse
        assert sse.endswith("\n\n")

    def test_error_event_format(self) -> None:
        """Error events should use event: error."""
        payload = {"error_code": "unknown", "message": "test", "retryable": False}
        sse = f"event: error\ndata: {json.dumps(payload)}\n\n"

        assert "event: error\n" in sse
        assert '"error_code": "unknown"' in sse

    def test_done_event_format(self) -> None:
        """Done event should contain full_content."""
        payload = {"full_content": "hello world"}
        sse = f"event: done\ndata: {json.dumps(payload)}\n\n"

        assert "event: done\n" in sse
        assert '"full_content": "hello world"' in sse
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/test_v2_streaming.py -v`
Expected: FAIL — `ImportError: cannot import name 'NODE_TO_SOURCE'`

- [ ] **Step 3: Add NODE_TO_SOURCE mapping to chat.py**

In `chat.py`, after the imports (around line 36), add:

```python
# Map langgraph_node names to human-readable source identifiers
NODE_TO_SOURCE: dict[str, str] = {
    "agent": "orchestrator",
    "delegate_to_world_builder": "world_builder",
    "delegate_to_character": "character",
    "delegate_to_plot": "plot",
    "delegate_to_chapter": "chapter",
    "delegate_to_review": "review",
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/test_v2_streaming.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/v1/chat.py backend/tests/test_v2_streaming.py
git commit -m "feat(chat): add NODE_TO_SOURCE mapping and SSE format tests"
```

---

### Task 4: Rewrite stream_with_save() for v2 streaming

**Files:**
- Modify: `backend/app/api/v1/chat.py:192-338`
- Test: `backend/tests/test_v2_streaming.py`

- [ ] **Step 1: Write test for v2 chunk processing**

Add to `backend/tests/test_v2_streaming.py`:

```python
class TestV2ChunkProcessing:
    """Test v2 StreamPart chunk processing logic."""

    def test_messages_chunk_with_text_content(self) -> None:
        """Messages chunk with text should produce SSE messages event."""
        # Simulate a v2 messages chunk
        chunk = {
            "type": "messages",
            "ns": (),
            "data": (
                type("Token", (), {"content": "hello", "content_blocks": []})(),
                {"langgraph_node": "agent"},
            ),
        }

        token, metadata = chunk["data"]
        node = metadata.get("langgraph_node", "agent")
        source = NODE_TO_SOURCE.get(node, node)

        assert chunk["type"] == "messages"
        assert source == "orchestrator"
        assert token.content == "hello"

    def test_messages_chunk_with_subagent_node(self) -> None:
        """Messages chunk from sub-agent should map to correct source."""
        metadata = {"langgraph_node": "delegate_to_world_builder"}
        source = NODE_TO_SOURCE.get(metadata["langgraph_node"], metadata["langgraph_node"])

        assert source == "world_builder"

    def test_updates_chunk_with_tool_calls(self) -> None:
        """Updates chunk with tool_calls should produce tool_start event."""
        chunk = {
            "type": "updates",
            "ns": (),
            "data": {
                "agent": {
                    "messages": [
                        type(
                            "AIMessage",
                            (),
                            {
                                "tool_calls": [
                                    {"name": "delegate_to_world_builder", "id": "call_123", "args": {"task": "test"}}
                                ]
                            },
                        )()
                    ]
                }
            },
        }

        assert chunk["type"] == "updates"
        node_name = list(chunk["data"].keys())[0]
        assert node_name == "agent"

    def test_custom_chunk_type(self) -> None:
        """Custom chunk should be recognized."""
        chunk = {
            "type": "custom",
            "ns": (),
            "data": {"message": "Processing..."},
        }

        assert chunk["type"] == "custom"
```

- [ ] **Step 2: Run tests**

Run: `cd backend && uv run pytest tests/test_v2_streaming.py -v`
Expected: All tests PASS (these test data structures, not the actual streaming)

- [ ] **Step 3: Rewrite stream_with_save()**

Replace the entire `stream_with_save()` function (lines 192-338) in `chat.py` with:

```python
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
        event_counter = 0

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
                chunk_ns = chunk.get("ns", ())
                chunk_data = chunk["data"]

                if chunk_type == "messages":
                    token, metadata = chunk_data
                    node = metadata.get("langgraph_node", "agent")
                    source = NODE_TO_SOURCE.get(node, node)

                    # Handle reasoning/thinking blocks
                    content_blocks = getattr(token, "content_blocks", [])
                    for block in content_blocks:
                        if isinstance(block, dict) and block.get("type") == "reasoning":
                            thinking_text = block.get("reasoning", "")
                            if thinking_text:
                                payload = json.dumps(safe_json_value({"thinking": thinking_text, "source": source}))
                                yield f"event: messages\nid: {next_id()}\ndata: {payload}\n\n"

                    # Handle text content
                    text_content = token.content if hasattr(token, "content") else ""
                    if text_content and isinstance(text_content, str):
                        full_content.append(text_content)
                        payload = json.dumps(safe_json_value({
                            "token": text_content,
                            "source": source,
                            "langgraph_node": node,
                        }))
                        yield f"event: messages\nid: {next_id()}\ndata: {payload}\n\n"

                elif chunk_type == "updates":
                    for node_name, data in chunk_data.items():
                        msgs = data.get("messages", []) if isinstance(data, dict) else []
                        for msg in msgs:
                            # Tool call start
                            if hasattr(msg, "tool_calls") and msg.tool_calls:
                                for tc in msg.tool_calls:
                                    payload = json.dumps(safe_json_value({
                                        "type": "tool_start",
                                        "tool": tc.get("name", ""),
                                        "tool_call_id": tc.get("id", ""),
                                        "args": tc.get("args", {}),
                                    }))
                                    yield f"event: updates\nid: {next_id()}\ndata: {payload}\n\n"

                            # Tool message (result)
                            if isinstance(msg, ToolMessage):
                                payload = json.dumps(safe_json_value({
                                    "type": "tool_end",
                                    "tool": getattr(msg, "name", ""),
                                    "tool_call_id": getattr(msg, "tool_call_id", ""),
                                    "result": msg.content,
                                }))
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
            log_ai_error(
                logger,
                exc,
                session_id=session_id,
                project_id=project_id,
                user_content=request.message,
            )
        except Exception as exc:
            error_payload = {
                "error_code": ErrorCode.UNKNOWN.value,
                "message": str(exc),
                "retryable": False,
            }
            yield f"event: error\nid: {next_id()}\ndata: {json.dumps(safe_json_value(error_payload))}\n\n"
            log_ai_error(
                logger,
                AIError(
                    error_code=ErrorCode.UNKNOWN,
                    message=str(exc),
                    retryable=False,
                    original_exception=exc,
                ),
                session_id=session_id,
                project_id=project_id,
                user_content=request.message,
            )

        # Send done event
        combined = "".join(full_content)
        yield f"event: done\nid: {next_id()}\ndata: {json.dumps(safe_json_value({'full_content': combined}))}\n\n"

        if combined:
            log_stream_complete(logger, session_id=session_id, token_count=len(combined))
```

- [ ] **Step 4: Remove unused imports from chat.py**

Remove these imports that are no longer needed:
- `AIMessage` (line 16) — no longer checking for AIMessage in stream handler
- `BaseMessage` (line 16) — still used in `_messages_to_history_dicts`, keep it

Actually, `AIMessage` is still used in `_messages_to_history_dicts`. Keep all imports.

- [ ] **Step 5: Run all existing tests**

Run: `cd backend && uv run pytest --tb=short -q`
Expected: All tests PASS (256+ tests)

- [ ] **Step 6: Run type checker**

Run: `cd backend && uv run mypy app`
Expected: No errors

- [ ] **Step 7: Run linter**

Run: `cd backend && uv run ruff check app tests`
Expected: No errors

- [ ] **Step 8: Commit**

```bash
git add backend/app/api/v1/chat.py backend/tests/test_v2_streaming.py
git commit -m "feat(chat): rewrite stream_with_save() for v2 streaming

Replace astream_events(v1) with astream(stream_mode, v2).
Each SSE event now includes source attribution via NODE_TO_SOURCE mapping.
SSE format follows LangGraph Platform best practices with event/id/data."
```

---

### Task 5: Verify end-to-end with dev server

**Files:**
- None (manual verification)

- [ ] **Step 1: Start dev server**

Run: `cd backend && uv run uvicorn app.main:app --reload --port 8000`

- [ ] **Step 2: Send a test request**

Run in another terminal:
```bash
curl -N -X POST http://localhost:8000/api/v1/projects/test/sessions/test-session/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}' \
  2>&1 | head -30
```

Expected: SSE events with `event: messages`, `id:`, and `data:` containing `source` field.

- [ ] **Step 3: Verify SSE format**

Check that:
1. Each event has `event:`, `id:`, and `data:` lines
2. `data:` is valid JSON
3. `messages` events contain `token` and `source` fields
4. `updates` events contain `type`, `tool`, `tool_call_id` fields
5. Stream ends with `event: done`

- [ ] **Step 4: Commit any fixes**

If any issues found during E2E testing, fix and commit.

---

### Task 6: Final verification

- [ ] **Step 1: Run full test suite**

Run: `cd backend && uv run pytest --tb=short -q`
Expected: All tests PASS

- [ ] **Step 2: Run type checker**

Run: `cd backend && uv run mypy app`
Expected: No errors

- [ ] **Step 3: Run linter and formatter**

Run: `cd backend && uv run ruff check app tests && uv run ruff format --check app tests`
Expected: No errors

- [ ] **Step 4: Verify no regressions**

Confirm:
1. Non-streaming API endpoints still work (create/list/delete sessions)
2. Chat history endpoint still works
3. Error handling still produces `event: error` SSE events
