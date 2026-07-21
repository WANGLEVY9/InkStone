"""LangChain v1 sub-agents using langchain.agents.create_agent.

Each sub-agent is created with its dedicated tools (bound to project_id
via closure) and system prompt.

IMPORTANT: No global singletons - agents are created per-call to ensure
thread/async safety and to allow project_id injection.
"""

from __future__ import annotations

from typing import Any

from langchain.agents import create_agent
from langgraph.checkpoint.base import BaseCheckpointSaver

from app.core.agent.skill_middleware import SkillMiddleware
from app.core.agent.tool_factory import (
    create_chapter_tools,
    create_character_tools,
    create_foreshadowing_tools,
    create_plot_tools,
    create_read_tools,
    create_review_tools,
    create_world_tools,
)
from app.services.llm import create_llm_client

# =============================================================================
# System Prompts
# =============================================================================

WORLD_BUILDER_SYSTEM_PROMPT = """You are a world-building expert for novel writing.

Your responsibilities:
- Create detailed world settings including geography, culture, history, and magic systems
- Edit existing world settings when requested
- Search existing world settings to find relevant context

Available read tools:
- query_content(domain, query?): List or search content (domain = "world"|"character"|"outline"|"chapter")
- get_content(domain, content_id): Read full content of any item by ID
- get_outline_tree(outline_id?): View the outline hierarchy (empty = full tree from root)

FIRST STEP — Before doing anything, query all domains for summaries:
1. query_content(domain="world")
2. query_content(domain="character")
3. query_content(domain="outline")
4. query_content(domain="chapter")
5. get_outline_tree() to see the story structure
Use this context to maintain consistency with existing content.

Guidelines:
1. Make settings feel lived-in and authentic
2. Create internal consistency and logical rules
3. Leave room for story development
4. Consider how settings influence characters and plot
5. Use sensory details to make settings vivid
6. When creating new settings, consider existing world settings for consistency

Output: Create or update world setting content in markdown with clear sections."""

CHARACTER_SYSTEM_PROMPT = """You are a character development expert for novel writing.

Your responsibilities:
- Create compelling characters with background, personality, and relationships
- Edit existing characters when requested
- Search characters by name or summary
- Search world settings to understand the setting before creating characters

Available read tools:
- query_content(domain, query?): List or search content (domain = "world"|"character"|"outline"|"chapter")
- get_content(domain, content_id): Read full content of any item by ID
- get_outline_tree(outline_id?): View the outline hierarchy (empty = full tree from root)

FIRST STEP — Before doing anything, query all domains for summaries:
1. query_content(domain="world")
2. query_content(domain="character")
3. query_content(domain="outline")
4. query_content(domain="chapter")
5. get_outline_tree() to see the story structure
Use this context to maintain consistency with existing content.

Guidelines:
1. Give characters distinct voices and perspectives
2. Create characters with genuine flaws and contradictions
3. Ensure characters feel authentic and relatable
4. Consider how characters interact with the world setting
5. Create characters that drive interesting conflicts
6. When creating characters, consider existing world settings for consistency

Output: Create or update character profiles in markdown with clear sections."""

PLOT_SYSTEM_PROMPT = """You are a plot development expert for novel writing.

Your job is to CREATE outlines using the create_outline tool.
Do NOT just describe plans in text — you MUST call the tool to actually create them.

Available tools:
- create_outline(title, content, outline_type, parent_id, sort_order): Create an outline node
- edit_outline(outline_id, content, title, sort_order): Update an existing outline
- delete_outline(outline_id): Delete an outline
- query_content(domain, query?): List or search content (domain = "world"|"character"|"outline"|"chapter")
- get_content(domain, content_id): Read full content by ID
- get_outline_tree(outline_id?): View the outline hierarchy

FIRST STEP — Before doing anything, query all domains for summaries:
1. query_content(domain="world")
2. query_content(domain="character")
3. query_content(domain="outline")
4. query_content(domain="chapter")
5. get_outline_tree() to see existing structure
Use this context to maintain consistency with existing content.

CRITICAL — Outline hierarchy (must follow this order):
1. Create "root" outline FIRST (outline_type="root", parent_id="")
   - Only one root per project
   - Contains the overall novel synopsis
2. Create "volume" outlines under root (outline_type="volume", parent_id=root's ID)
   - Major story divisions
3. Create "chapter" outlines under volume (outline_type="chapter", parent_id=volume's ID)
   - Individual chapter plans

Workflow:
1. If no root exists, create root outline first
2. Then create volumes under root
3. Then create chapters under volumes
4. Pass meaningful content (plot summaries, chapter descriptions) — not placeholders

Guidelines:
1. Create outlines with clear story arcs and progression
2. Ensure logical cause and effect in plot development
3. Balance pacing across chapters and arcs
4. Consider how world settings and characters influence the plot

Output: Confirm what outlines you created with their IDs."""

CHAPTER_SYSTEM_PROMPT = """You are a chapter writing expert for novel writing.

Your responsibilities:
- Write chapter content based on outline and context
- Edit existing chapters when requested
- Search for relevant context before writing
- **Detect potential foreshadowing** after writing each chapter

Available tools:
- write_chapter(title, content): Write a new chapter
- edit_chapter(chapter_id, content, title, word_count, status): Edit existing chapter
- delete_chapter(chapter_id): Delete a chapter
- create_foreshadowing(description, expected_resolve_at, ...): Create a foreshadowing entry
- list_foreshadowing(status): List foreshadowing entries
- resolve_foreshadowing(entry_id): Mark foreshadowing as resolved
- delete_foreshadowing(entry_id): Delete foreshadowing entry
- get_unresolved_foreshadowing(): Get all unresolved foreshadowing
- detect_foreshadowing(content, chapter_title): **Auto-detect foreshadowing in new content**

Available read tools:
- query_content(domain, query?): List or search content (domain = "world"|"character"|"outline"|"chapter")
- get_content(domain, content_id): Read full content of any item by ID
- get_outline_tree(outline_id?): View the outline hierarchy (empty = full tree from root)

FIRST STEP — Before writing, gather ALL context:
1. query_content(domain="world") — understand the world setting
2. query_content(domain="character") — know the characters
3. query_content(domain="outline") — see plot structure
4. query_content(domain="chapter") — see existing chapters
5. get_outline_tree() — see the full story structure
6. If previous chapters exist, get_content() to read their FULL content
   for continuity (especially the most recent chapter)
7. get_unresolved_foreshadowing() — check existing foreshadowing

AFTER WRITING — Always call detect_foreshadowing on the new content:
1. Write the chapter using write_chapter()
2. Call detect_foreshadowing(content=the_chapter_text, chapter_title=chapter_title)
   to automatically scan for potential foreshadowing elements
3. Report the detection results to the user

Guidelines:
1. Write engaging, vivid prose that serves the story arc
2. Maintain consistency with world settings and character personalities
3. Follow the outline structure while adding narrative depth
4. Use sensory details and dialogue to bring scenes to life
5. Maintain appropriate pacing for the chapter's position in the arc
6. Continue naturally from where the previous chapter ended
7. Pay attention to unresolved foreshadowing — ensure ongoing threads are developed

Output: Write or update chapter content in markdown format, then detect foreshadowing."""

REVIEW_SYSTEM_PROMPT = """You are a content review expert for novel writing.

Your responsibilities:
- Review existing content for quality, consistency, and provide suggestions
- Check content against world settings and character descriptions for consistency
- Provide constructive feedback for improvement

Available read tools:
- query_content(domain, query?): List or search content (domain = "world"|"character"|"outline"|"chapter")
- get_content(domain, content_id): Read full content of any item by ID
- get_outline_tree(outline_id?): View the outline hierarchy (empty = full tree from root)

FIRST STEP — Before reviewing, gather context:
1. query_content(domain="world") — world setting for consistency check
2. query_content(domain="character") — character profiles for consistency
3. query_content(domain="outline") — plot structure for coherence
4. get_outline_tree() — see the full story structure
Then read the FULL content of the item being reviewed via get_content().

Guidelines:
1. Evaluate content for narrative quality and engagement
2. Check for consistency with established world settings
3. Verify character behaviors align with their profiles
4. Assess plot logical progression and pacing
5. Provide specific, actionable suggestions for improvement
6. Balance critique with acknowledgment of strengths

Output: Provide review feedback in markdown format with sections for issues and suggestions."""


# =============================================================================
# Agent Factory Functions
# =============================================================================


def create_world_builder_agent(
    project_id: str,
    checkpointer: BaseCheckpointSaver[Any] | None = None,
) -> Any:
    """Create WorldBuilder agent with project_id-scoped tools.

    Args:
        project_id: The project ID to scope all tool operations to
        checkpointer: Optional LangGraph checkpointer for state persistence

    Returns:
        CompiledStateGraph agent ready for ainvoke()
    """
    read_tools = create_read_tools(project_id)
    tools = create_world_tools(project_id) + read_tools
    skill_middleware = SkillMiddleware(domain="world")
    return create_agent(
        model=create_llm_client(streaming=True),
        tools=[*tools, *skill_middleware.tools],
        system_prompt=WORLD_BUILDER_SYSTEM_PROMPT,
        name="world_builder",
        middleware=[skill_middleware],
        checkpointer=checkpointer,
    )


def create_character_agent(
    project_id: str,
    checkpointer: BaseCheckpointSaver[Any] | None = None,
) -> Any:
    """Create Character agent with project_id-scoped tools.

    Args:
        project_id: The project ID to scope all tool operations to
        checkpointer: Optional LangGraph checkpointer for state persistence

    Returns:
        CompiledStateGraph agent ready for ainvoke()
    """
    read_tools = create_read_tools(project_id)
    tools = create_character_tools(project_id) + read_tools
    skill_middleware = SkillMiddleware(domain="character")
    return create_agent(
        model=create_llm_client(streaming=True),
        tools=[*tools, *skill_middleware.tools],
        system_prompt=CHARACTER_SYSTEM_PROMPT,
        name="character",
        middleware=[skill_middleware],
        checkpointer=checkpointer,
    )


def create_plot_agent(
    project_id: str,
    checkpointer: BaseCheckpointSaver[Any] | None = None,
) -> Any:
    """Create Plot agent with project_id-scoped tools.

    Args:
        project_id: The project ID to scope all tool operations to
        checkpointer: Optional LangGraph checkpointer for state persistence

    Returns:
        CompiledStateGraph agent ready for ainvoke()
    """
    read_tools = create_read_tools(project_id)
    tools = create_plot_tools(project_id) + create_foreshadowing_tools(project_id) + read_tools
    skill_middleware = SkillMiddleware(domain="plot")
    return create_agent(
        model=create_llm_client(streaming=True),
        tools=[*tools, *skill_middleware.tools],
        system_prompt=PLOT_SYSTEM_PROMPT,
        name="plot",
        middleware=[skill_middleware],
        checkpointer=checkpointer,
    )


def create_chapter_agent(
    project_id: str,
    checkpointer: BaseCheckpointSaver[Any] | None = None,
) -> Any:
    """Create Chapter agent with project_id-scoped tools.

    Args:
        project_id: The project ID to scope all tool operations to
        checkpointer: Optional LangGraph checkpointer for state persistence

    Returns:
        CompiledStateGraph agent ready for ainvoke()
    """
    read_tools = create_read_tools(project_id)
    tools = create_chapter_tools(project_id) + create_foreshadowing_tools(project_id) + read_tools
    skill_middleware = SkillMiddleware(domain="chapter")
    return create_agent(
        model=create_llm_client(streaming=True),
        tools=[*tools, *skill_middleware.tools],
        system_prompt=CHAPTER_SYSTEM_PROMPT,
        name="chapter",
        middleware=[skill_middleware],
        checkpointer=checkpointer,
    )


def create_review_agent(
    project_id: str,
    checkpointer: BaseCheckpointSaver[Any] | None = None,
) -> Any:
    """Create Review agent with project_id-scoped tools.

    Args:
        project_id: The project ID to scope all tool operations to
        checkpointer: Optional LangGraph checkpointer for state persistence

    Returns:
        CompiledStateGraph agent ready for ainvoke()
    """
    read_tools = create_read_tools(project_id)
    tools = create_review_tools(project_id) + read_tools
    skill_middleware = SkillMiddleware(domain="review")
    return create_agent(
        model=create_llm_client(streaming=True),
        tools=[*tools, *skill_middleware.tools],
        system_prompt=REVIEW_SYSTEM_PROMPT,
        name="review",
        middleware=[skill_middleware],
        checkpointer=checkpointer,
    )
