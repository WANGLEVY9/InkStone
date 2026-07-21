"""Typed state definitions for the Orchestrator LangGraph workflow."""

from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


class ProjectContext(TypedDict):
    """Project context passed between tools - all scoped to project_id."""

    project_name: str
    project_description: str | None
    world_settings: list[dict[str, str]]
    characters: list[dict[str, str]]
    outline: dict[str, str] | None
    chapters: list[dict[str, str]]


class OrchestratorState(TypedDict):
    """State for the orchestrator graph.

    Used in chat.py to construct the initial state dict. The graph itself
    uses create_agent's built-in state; these fields are merged in.
    """

    messages: Annotated[list[BaseMessage], add_messages]
    session_id: str
    project_id: str
    project_context: ProjectContext
