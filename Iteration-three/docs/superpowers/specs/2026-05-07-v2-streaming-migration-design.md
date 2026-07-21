# V2 Streaming Migration Design

**Date:** 2026-05-07
**Status:** Approved
**Problem:** Multiple tools' streaming tokens are mixed together in output, no source attribution for tokens.

## Problem Analysis

Three layers of issues cause tokens from different tools/sub-agents to be mixed:

1. **SSE format mismatch** — Backend emits `event: token\ndata: {"token": "..."}` but frontend expects `data: {"type": "content", "content": "..."}`. Real streaming is broken in production.
2. **No token source attribution** — All `on_chat_model_stream` events emit identical `event: token` with no source identifier. Cannot distinguish orchestrator tokens from sub-agent tokens.
3. **Legacy API** — Uses `astream_events(version="v1")` instead of recommended `astream(stream_mode, version="v2")`. All LLMs set to `streaming=False`.

## Solution: Full Migration to LangGraph V2 Streaming

Migrate from `astream_events(v1)` to `astream(stream_mode=["messages", "updates", "custom"], subgraphs=True, version="v2")`.

### Architecture Changes

#### 1. Enable streaming on all LLMs

- Orchestrator LLM in `builder.py`: `streaming=True`
- All 5 sub-agent LLMs in `langchain_subagents.py`: `streaming=True`

#### 2. Convert sub-agent @tool wrappers to async

Current sync wrappers use `asyncio.run(subagent.ainvoke(...))` which creates a new event loop and breaks streaming callback propagation. Convert to `async def` with `await`:

```python
# Before
@tool
def delegate_to_world_builder(task: str) -> str:
    result = asyncio.run(subagent.ainvoke({"messages": [...]}))
    return str(result["messages"][-1].content)

# After
@tool
async def delegate_to_world_builder(task: str) -> str:
    result = await subagent.ainvoke({"messages": [...]})
    return str(result["messages"][-1].content)
```

This ensures streaming callbacks propagate through the same event loop, allowing sub-agent LLM tokens to appear in the parent graph's stream with correct `langgraph_node` metadata.

#### 3. Migrate streaming API

```python
# Before
graph.astream_events(initial_state, config, version="v1", recursion_limit=25)

# After
graph.astream(
    initial_state, config,
    stream_mode=["messages", "updates", "custom"],
    subgraphs=True,
    version="v2",
    recursion_limit=25,
)
```

V2 StreamPart format:
```json
{"type": "messages"|"updates"|"custom", "ns": (), "data": ...}
```

- `type` — corresponds to stream mode
- `ns` — namespace tuple, empty for main agent, non-empty for subgraphs
- `data` — payload (varies by type)

### SSE Event Protocol

Following SSE best practices aligned with LangGraph Platform:

#### Event format

```
event: <stream_mode>
id: <monotonic_counter>
data: <json_payload>

```

#### Event types

| SSE Event | Trigger | Payload |
|-----------|---------|---------|
| `event: messages` | `chunk["type"] == "messages"` with text content | `{"token": "...", "source": "orchestrator"\|"world_builder"\|..., "langgraph_node": "..."}` |
| `event: messages` | `chunk["type"] == "messages"` with reasoning block | `{"thinking": "...", "source": "..."}` |
| `event: updates` | `chunk["type"] == "updates"` with tool_calls | `{"type": "tool_start", "tool": "...", "tool_call_id": "...", "args": {...}}` |
| `event: updates` | `chunk["type"] == "updates"` with ToolMessage | `{"type": "tool_end", "tool": "...", "tool_call_id": "...", "result": "..."}` |
| `event: custom` | `chunk["type"] == "custom"` | `{"type": "progress", "message": "...", "source": "..."}` |
| `event: done` | Stream complete | `{"full_content": "..."}` |
| `event: error` | Exception | `{"error_code": "...", "message": "...", "retryable": bool}` |

#### Source attribution

Map `metadata["langgraph_node"]` to human-readable source:

```python
NODE_TO_SOURCE = {
    "agent": "orchestrator",
    "delegate_to_world_builder": "world_builder",
    "delegate_to_character": "character",
    "delegate_to_plot": "plot",
    "delegate_to_chapter": "chapter",
    "delegate_to_review": "review",
}
```

#### Best practices applied

- `event:` field maps to LangGraph stream mode (not custom event names)
- `data:` is always JSON
- `id:` on every event for resumability (monotonic counter)
- Heartbeat comments (`: heartbeat\n\n`) every 15s during idle
- `event: done` signals stream completion

### File Changes

#### `backend/app/core/graph/builder.py`

- Set `streaming=True` on orchestrator LLM (line 53)
- Convert 5 `delegate_to_*` @tool functions from sync to async
- Replace `asyncio.run(subagent.ainvoke(...))` with `await subagent.ainvoke(...)`

#### `backend/app/core/agent/langchain_subagents.py`

- Set `streaming=True` on all 5 sub-agent LLMs (line 169)

#### `backend/app/api/v1/chat.py`

- Rewrite `stream_with_save()` to use `graph.astream()` with v2 stream modes
- Process `chunk["type"]` to emit appropriate SSE events
- Extract `metadata["langgraph_node"]` for source attribution
- Add heartbeat mechanism for long-running operations
- Add `event: done` at stream completion
- Remove all `astream_events` v1 handling code

#### No changes required

- `tool_factory.py` — Tools remain sync, run in thread pool
- `state.py` — State definition unchanged
- `orchestrator.py` — System prompt unchanged
- Frontend — Not in scope for this change

### Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Sub-agent token propagation via async @tool | Verify with integration test; fallback to `get_stream_writer()` if callbacks don't propagate |
| Anthropic streaming + thinking blocks | Already handled in SSE thinking branch |
| async @tool compatibility with LangGraph | Test coverage for async tool execution |

### Testing

| Test Type | Coverage |
|-----------|----------|
| Unit | `NODE_TO_SOURCE` mapping, SSE formatting, chunk dispatch |
| Integration | `stream_with_save()` with mock v2 chunk output |
| E2E | Dev server, verify SSE event sequence correctness |
| Regression | Non-streaming API unaffected |

### Verification Checklist

1. V2 chunk `type`/`ns`/`data` fields correctly parsed
2. `metadata["langgraph_node"]` correctly identifies sub-agent source (critical)
3. SSE `id` field monotonically increasing
4. `event: error` emitted on exceptions
5. `event: done` emitted on normal completion
6. Heartbeat sent during idle periods

### Out of Scope

- Frontend adaptation to new SSE format
- Frontend UI for sub-agent token display
- `Last-Event-ID` reconnection handling (frontend side)
