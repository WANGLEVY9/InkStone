"""Build and compile the orchestrator LangGraph using the subagents-as-tools pattern.

This module constructs a LangGraph agent via ``langchain.agents.create_agent``
that coordinates multiple specialized sub-agents.  Each sub-agent is wrapped
as a ``@tool`` function that calls ``subagent.invoke()`` and returns the
result.  The main orchestrator agent decides which sub-agent tool to call
based on the user's request.
"""

from __future__ import annotations

from typing import Any

from langchain.agents import create_agent
from langchain.tools import tool
from langgraph.checkpoint.base import BaseCheckpointSaver

from app.core.agent.langchain_subagents import (
    create_chapter_agent,
    create_character_agent,
    create_plot_agent,
    create_review_agent,
    create_world_builder_agent,
)
from app.core.agent.skill_middleware import SkillMiddleware
from app.core.agent.skill_tools import create_skill_tools
from app.core.agent.tool_factory import create_read_tools
from app.core.prompts.orchestrator import ORCHESTRATOR_SYSTEM
from app.services.llm import create_llm_client


def create_orchestrator_graph(
    project_id: str,
    model: Any = None,
    checkpointer: BaseCheckpointSaver[Any] | None = None,
) -> Any:
    """Build and compile the orchestrator agent with subagent wrapper tools.

    Creates a main orchestrator agent backed by a system prompt, with each
    sub-agent wrapped as a tool.  Sub-agents receive ``project_id`` through
    closure so that downstream tool calls are automatically scoped.

    Args:
        project_id: The project ID to scope all agent operations to.
        model: Optional LLM model. If not provided, creates one via
            ``create_llm_client`` with ``streaming=True``.
        checkpointer: Optional LangGraph checkpointer for state persistence
            and human-in-the-loop resumption.

    Returns:
        Compiled LangGraph workflow (orchestrator + subagent tools).
    """
    llm = model or create_llm_client(streaming=True)

    # Create subagents (each is a compiled LangGraph graph)
    world_builder = create_world_builder_agent(project_id)
    character = create_character_agent(project_id)
    plot = create_plot_agent(project_id)
    chapter = create_chapter_agent(project_id)
    review = create_review_agent(project_id)

    # Wrap subagents as tools — sub-agent LLM tokens propagate to the
    # parent stream via callbacks when the orchestrator uses stream()
    @tool(
        "delegate_to_world_builder",
        description="Create, edit, delete, or search world settings (geography, culture, history, magic systems)",
    )
    def delegate_to_world_builder(task: str) -> str:
        result = world_builder.invoke({"messages": [{"role": "user", "content": task}]})
        return result["messages"][-1].text  # type: ignore[no-any-return]

    @tool(
        "delegate_to_character",
        description="Create, edit, delete, or search character profiles, relationships, and personality",
    )
    def delegate_to_character(task: str) -> str:
        result = character.invoke({"messages": [{"role": "user", "content": task}]})
        return result["messages"][-1].text  # type: ignore[no-any-return]

    @tool(
        "delegate_to_plot",
        description="Create, edit, delete, or search story outlines, plot structure, and chapter breakdowns",
    )
    def delegate_to_plot(task: str) -> str:
        result = plot.invoke({"messages": [{"role": "user", "content": task}]})
        return result["messages"][-1].text  # type: ignore[no-any-return]

    @tool(
        "delegate_to_chapter",
        description="Write, edit, or delete chapter content based on outline and context",
    )
    def delegate_to_chapter(task: str) -> str:
        result = chapter.invoke({"messages": [{"role": "user", "content": task}]})
        return result["messages"][-1].text  # type: ignore[no-any-return]

    @tool(
        "delegate_to_review",
        description="Review content for quality, consistency, and provide suggestions; delete reviews",
    )
    def delegate_to_review(task: str) -> str:
        result = review.invoke({"messages": [{"role": "user", "content": task}]})
        return result["messages"][-1].text  # type: ignore[no-any-return]

    # Generic read tools (query_content, get_content, get_outline_tree)
    read_tools = create_read_tools(project_id)

    # Skill creation tool (global, no project_id)
    skill_tools = create_skill_tools()

    # Skill middleware (global, no domain filter)
    skill_middleware = SkillMiddleware(domain=None)

    # Main orchestrator agent
    return create_agent(
        model=llm,
        tools=[
            delegate_to_world_builder,
            delegate_to_character,
            delegate_to_plot,
            delegate_to_chapter,
            delegate_to_review,
            *read_tools,
            *skill_tools,
            *skill_middleware.tools,
        ],
        system_prompt=ORCHESTRATOR_SYSTEM,
        name="orchestrator",
        checkpointer=checkpointer,
        middleware=[skill_middleware],
    )
