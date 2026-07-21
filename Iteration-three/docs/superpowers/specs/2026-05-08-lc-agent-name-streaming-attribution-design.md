# Design: lc_agent_name Streaming Attribution

**Date:** 2026-05-08
**Problem:** Sub-agent tool call chunks have incorrect source attribution in SSE stream.
**Solution:** Replace `tags`/`langgraph_node` attribution with LangChain's `lc_agent_name` metadata.

## Problem

The current streaming source attribution in `chat.py` uses two mechanisms:
1. `TAG_TO_SOURCE` — maps LLM `tags` (e.g., `["world_builder"]`) to source names
2. `NODE_TO_SOURCE` — maps `langgraph_node` values to source names as fallback

This has several issues:
- **Fragile**: Adding a new sub-agent requires updating both dictionaries
- **Incorrect for tool call chunks**: When the orchestrator generates `delegate_to_*` tool calls, those chunks come from the orchestrator LLM (no domain tag), so they're attributed to `"orchestrator"` instead of the target sub-agent
- **Redundant**: LangChain provides a first-class `lc_agent_name` metadata field for this exact purpose

## Solution

Per the LangChain docs ([Streaming from sub-agents](https://docs.langchain.com/oss/python/langchain/streaming)), the correct approach is:
1. Pass `name` to each `create_agent()` call
2. Read `metadata.get("lc_agent_name")` in the streaming loop

## Changes

### 1. `backend/app/core/agent/langchain_subagents.py`

Add `name` parameter to all 5 sub-agent `create_agent()` calls. Remove `tags` from `create_llm_client()`.

**Before:**
```python
return create_agent(
    model=create_llm_client(streaming=True, tags=["world_builder"]),
    tools=[*tools, *skill_middleware.tools],
    system_prompt=WORLD_BUILDER_SYSTEM_PROMPT,
    middleware=[skill_middleware],
)
```

**After:**
```python
return create_agent(
    model=create_llm_client(streaming=True),
    tools=[*tools, *skill_middleware.tools],
    system_prompt=WORLD_BUILDER_SYSTEM_PROMPT,
    name="world_builder",
    middleware=[skill_middleware],
)
```

Repeat for: `character`, `plot`, `chapter`, `review`.

### 2. `backend/app/core/graph/builder.py`

Add `name="orchestrator"` to the orchestrator's `create_agent()` call.

**Before:**
```python
return create_agent(
    model=llm,
    tools=[...],
    system_prompt=ORCHESTRATOR_SYSTEM,
    checkpointer=checkpointer,
    middleware=[skill_middleware],
)
```

**After:**
```python
return create_agent(
    model=llm,
    tools=[...],
    system_prompt=ORCHESTRATOR_SYSTEM,
    name="orchestrator",
    checkpointer=checkpointer,
    middleware=[skill_middleware],
)
```

Also fix the docstring: change `streaming=False` to `streaming=True`.

### 3. `backend/app/api/v1/chat.py`

**Delete:**
- `NODE_TO_SOURCE` dict (lines 39-46)
- `TAG_TO_SOURCE` dict (lines 48-54)

**Replace attribution logic (lines 268-274):**

Before:
```python
tags = metadata.get("tags", [])
node = metadata.get("langgraph_node", "agent")
source = next(
    (TAG_TO_SOURCE[t] for t in tags if t in TAG_TO_SOURCE),
    NODE_TO_SOURCE.get(node, "orchestrator"),
)
```

After:
```python
source = metadata.get("lc_agent_name", "orchestrator")
```

## Expected Behavior

After the change, the SSE stream will correctly attribute tokens:

| Event | `lc_agent_name` | Source shown to client |
|-------|-----------------|----------------------|
| Orchestrator LLM thinking | `"orchestrator"` | `orchestrator` |
| Orchestrator generates `delegate_to_*` tool call | `"orchestrator"` | `orchestrator` |
| Sub-agent LLM tokens (inside `ainvoke`) | `"world_builder"` / `"character"` / etc. | `world_builder` / `character` / etc. |
| Sub-agent internal tool calls | Sub-agent name | Correct sub-agent |

## Testing

- Existing streaming tests should pass with updated source expectations
- Verify `lc_agent_name` appears in metadata by adding a debug log in the streaming loop
- Test that each sub-agent's tokens are attributed to the correct source name
