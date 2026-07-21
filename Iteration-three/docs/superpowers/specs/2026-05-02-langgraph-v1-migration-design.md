# LangGraph v1 Migration Design

**Date**: 2026-05-02
**Status**: Proposed
**Scope**: Full migration of agent layer to LangGraph v1 / LangChain v1 APIs

## Problem

The current agent architecture uses deprecated LangGraph APIs:

1. **`create_react_agent`** (from `langgraph.prebuilt`) is deprecated in LangGraph v1. Replacement: `create_agent` (from `langchain.agents`).
2. **`langgraph-supervisor`** package and `create_supervisor` are replaced by the subagents-as-tools pattern: wrap each subagent as a `@tool` using `create_agent`, then pass tools to the main agent.
3. **Handoff tools** in `handoff_tools.py` are dead code — never wired into the supervisor.
4. **`streaming.py`** is unused — `chat.py` has its own inline streaming logic.
5. **`OrchestratorState`** has fields that are initialized but never consumed.

## Approach

Big bang migration — replace all deprecated APIs in one coherent change. The codebase is small (5 sub-agents, 1 orchestrator) and the v1 patterns are well-documented.

## Design

### 1. Subagents: `create_react_agent` → `create_agent`

**File**: `backend/app/core/agent/langchain_subagents.py`

Each of the 5 agent factories changes:

```python
# Old
from langgraph.prebuilt import create_react_agent

def create_world_builder_agent(project_id: str) -> Any:
    llm = create_llm_client(streaming=False)
    tools = create_world_tools(project_id)
    return create_react_agent(llm, tools=tools, prompt=WORLD_BUILDER_SYSTEM_PROMPT, name="world_builder")

# New
from langchain.agents import create_agent

def create_world_builder_agent(project_id: str) -> Any:
    tools = create_world_tools(project_id)
    return create_agent(
        model=create_llm_client(streaming=False),
        tools=tools,
        system_prompt=WORLD_BUILDER_SYSTEM_PROMPT,
    )
```

Changes applied to all 5 factories (`create_world_builder_agent`, `create_character_agent`, `create_plot_agent`, `create_chapter_agent`, `create_review_agent`):

- `from langgraph.prebuilt import create_react_agent` → `from langchain.agents import create_agent`
- `create_react_agent(llm, tools=..., prompt=..., name=...)` → `create_agent(model=llm, tools=..., system_prompt=...)`
- `prompt=` → `system_prompt=`
- Remove `name=` parameter (not supported in `create_agent`)
- Remove separate `llm` variable; pass directly to `model=`
- Keep `-> Any` return type annotation (required for mypy)

System prompts are unchanged.

### 2. Orchestrator: `create_supervisor` → Subagents-as-Tools

**Files**: `backend/app/core/graph/builder.py`, `backend/app/core/prompts/orchestrator.py`

Replace `langgraph_supervisor.create_supervisor` with `langchain.agents.create_agent`, where each subagent is wrapped as a `@tool`.

**New builder.py**:

```python
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
from app.core.agent.tool_factory import create_supervisor_tools
from app.core.prompts.orchestrator import ORCHESTRATOR_SYSTEM
from app.services.llm import create_llm_client


def create_orchestrator_graph(
    project_id: str,
    model: Any = None,
    checkpointer: BaseCheckpointSaver[Any] | None = None,
) -> Any:
    llm = model or create_llm_client(streaming=False)

    # Create subagents (each is a compiled LangGraph graph)
    world_builder = create_world_builder_agent(project_id)
    character = create_character_agent(project_id)
    plot = create_plot_agent(project_id)
    chapter = create_chapter_agent(project_id)
    review = create_review_agent(project_id)

    # Wrap subagents as tools
    @tool("delegate_to_world_builder",
          description="Create, edit, or search world settings (geography, culture, history, magic systems)")
    async def delegate_to_world_builder(task: str) -> str:
        result = await world_builder.ainvoke({"messages": [{"role": "user", "content": task}]})
        return result["messages"][-1].content

    @tool("delegate_to_character",
          description="Create, edit, or search character profiles, relationships, and personality")
    async def delegate_to_character(task: str) -> str:
        result = await character.ainvoke({"messages": [{"role": "user", "content": task}]})
        return result["messages"][-1].content

    @tool("delegate_to_plot",
          description="Create or edit story outlines, plot structure, and chapter breakdowns")
    async def delegate_to_plot(task: str) -> str:
        result = await plot.ainvoke({"messages": [{"role": "user", "content": task}]})
        return result["messages"][-1].content

    @tool("delegate_to_chapter",
          description="Write or edit chapter content based on outline and context")
    async def delegate_to_chapter(task: str) -> str:
        result = await chapter.ainvoke({"messages": [{"role": "user", "content": task}]})
        return result["messages"][-1].content

    @tool("delegate_to_review",
          description="Review content for quality, consistency, and provide suggestions")
    async def delegate_to_review(task: str) -> str:
        result = await review.ainvoke({"messages": [{"role": "user", "content": task}]})
        return result["messages"][-1].content

    # Read-only supervisor tools (list_world_settings, list_characters, etc.)
    supervisor_tools = create_supervisor_tools(project_id)

    # Main orchestrator agent
    return create_agent(
        model=llm,
        tools=[
            delegate_to_world_builder,
            delegate_to_character,
            delegate_to_plot,
            delegate_to_chapter,
            delegate_to_review,
            *supervisor_tools,
        ],
        system_prompt=ORCHESTRATOR_SYSTEM,
        checkpointer=checkpointer,
    )
```

**Updated orchestrator prompt** (`orchestrator.py`):

```python
ORCHESTRATOR_SYSTEM = """You are a novel writing assistant orchestrator.

Your job is to understand the user's request and delegate to the appropriate sub-agent.

Available tools:
- delegate_to_world_builder: For creating, editing, or searching world settings
- delegate_to_character: For creating, editing, or searching characters
- delegate_to_plot: For creating or editing story outlines
- delegate_to_chapter: For writing or editing chapters
- delegate_to_review: For reviewing content quality and consistency
- list_world_settings, list_characters, get_story_outline, list_chapters: For reading project context

Rules:
1. Use the appropriate delegate_to_* tool based on the user's request
2. When delegating, provide the full task description and relevant context
3. If the request is ambiguous, ask clarifying questions
4. Use the list_* tools to gather context before delegating if needed

Always provide a clear, detailed task description when delegating to sub-agents."""
```

### 3. Tools: Keep Synchronous

**File**: `backend/app/core/agent/tool_factory.py`

Tools remain synchronous as designed. The `asyncio.run()` pattern works because LangGraph runs sync tools in a thread pool (no nested event loop). Add a documentation comment:

```python
# NOTE: Tools are synchronous by design. LangGraph runs sync tools in a
# thread pool, so asyncio.run() is safe here (no nested event loop).
# Async migration is planned for a future iteration.
```

No functional changes to `tool_factory.py`.

### 4. Cleanup

#### 4a. Delete dead code

| File | Action | Reason |
|------|--------|--------|
| `backend/app/core/agent/handoff_tools.py` | **Delete** | Replaced by `delegate_to_*` tools in builder.py |
| `backend/app/core/graph/streaming.py` | **Delete** | Unused — chat.py has inline streaming |
| `backend/app/core/agent/registry.py` | **Delete if placeholder** | Per CLAUDE.md: "placeholder, kept for legacy import compat" |

#### 4b. Simplify OrchestratorState

**File**: `backend/app/core/graph/state.py`

Remove unused fields:

```python
class OrchestratorState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    session_id: str
    project_id: str
    project_context: ProjectContext
```

Removed: `pending_tool_calls`, `streaming_tokens`, `tool_results`, `active_agent`, `remaining_steps`.

Note: `OrchestratorState` is still used in `chat.py` to construct the initial state dict, but is no longer passed to the graph builder (which uses `create_agent`'s built-in state).

#### 4c. Update dependencies

**File**: `backend/pyproject.toml`

```toml
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.34.0",
    "pydantic>=2.10.0",
    "pydantic-settings>=2.7.0",
    "langchain>=1.0.0",
    "langchain-core>=0.3.0",
    "langchain-anthropic>=0.3.0",
    "langgraph>=0.4.0",
    "aiosqlite>=0.20.0",
    "aiofiles>=23.0.0",
    "python-dotenv>=1.0.0",
    "langgraph-checkpoint-sqlite>=3.0.3",
]
```

Removed: `langgraph-supervisor>=0.0.31`. Updated: `langchain>=0.3.0` → `langchain>=1.0.0`.

#### 4d. Update chat.py streaming filter

**File**: `backend/app/api/v1/chat.py`

Add `"model"` to the nested chain name filter (v1 renames the agent node from `"agent"` to `"model"`):

```python
nested_names = {"world_builder", "character", "plot", "chapter", "review", "tools", "model"}
```

## Files Changed

| File | Change Type |
|------|-------------|
| `backend/app/core/agent/langchain_subagents.py` | Modify (create_react_agent → create_agent) |
| `backend/app/core/graph/builder.py` | Rewrite (create_supervisor → subagents-as-tools) |
| `backend/app/core/prompts/orchestrator.py` | Modify (update tool names in prompt) |
| `backend/app/core/graph/state.py` | Modify (remove unused fields) |
| `backend/app/api/v1/chat.py` | Modify (add "model" to nested_names) |
| `backend/pyproject.toml` | Modify (remove langgraph-supervisor, update langchain) |
| `backend/app/core/agent/handoff_tools.py` | **Delete** |
| `backend/app/core/graph/streaming.py` | **Delete** |
| `backend/app/core/agent/registry.py` | **Delete** (if placeholder) |

## Verification

1. `uv run ruff check app tests` — lint passes
2. `uv run mypy app` — type-check passes
3. `uv run pytest` — all tests pass
4. Manual: start dev server, send a chat message, verify agent routing works

## Implementation Notes

- **`create_agent` state handling**: The v1 `create_agent` uses its own internal state (based on `AgentState`). Custom fields like `session_id`, `project_id`, `project_context` may need to be passed via the `context` parameter (v1 pattern) rather than as state dict fields. Verify during implementation and adjust `chat.py` accordingly.
- **`checkpointer` parameter**: Verify that `create_agent` accepts a `checkpointer` parameter. If not, the graph may need to be compiled separately with `.compile(checkpointer=checkpointer)`.
- **`registry.py`**: Check if it contains any actual code or is truly a placeholder before deleting.

## Out of Scope

- Async tool migration (tools stay sync, planned for future iteration)
- Graph caching (graph still created per request)
- `langchain` package removal (may still be needed as transitive dependency)
