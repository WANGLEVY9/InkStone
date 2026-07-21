# Session Restore Fix Design

## Problem

Session restore in `agent-tester/index.html` is broken. When switching sessions, `loadHistory()` fails to properly reconstruct the chat timeline:

1. **Tool calls invisible** — `tool_calls` from `AIMessage` are ignored
2. **Tool results orphaned** — `role: "tool"` messages rendered as standalone agent blocks
3. **Timestamps crash** — `created_at` not returned by backend, produces "Invalid Date"
4. **Agent identity lost** — always shows "Agent" instead of WorldBuilder/Character/etc.
5. **Thinking may be missing** — extracted from wrong field (`additional_kwargs` vs content dict)

## Approach

**Chosen: B — Backend returns raw data, frontend reconstructs timeline.**

Backend `_messages_to_history_dicts` stays mostly unchanged (minimal fixes). Frontend `loadHistory` does the heavy lifting: matching tool_calls to tool results, inferring agent identity, and building the timeline structure.

### Why not A (backend enriches)?
Backend changes are more invasive and harder to iterate on for display logic.

### Why not C (new endpoint)?
Adds maintenance burden of two history formats.

## Design

### Backend: `chat.py` `_messages_to_history_dicts`

Minimal changes to the existing function (lines 65-99):

1. **Ensure `tool_calls` is returned** — already done (`entry["tool_calls"] = msg.tool_calls`)
2. **Ensure `tool_call_id` is returned** — already done for `ToolMessage`
3. **Fix thinking extraction** — currently only checks `msg.additional_kwargs.get("thinking")`. Add fallback to check `msg.content` if it's a list of dicts (Anthropic's structured content format where `{"type": "thinking", "thinking": "..."}` may appear)
4. **No new fields needed** — `created_at` and agent identity are handled by frontend

### Frontend: `agent-tester/index.html` `loadHistory`

Complete rewrite of the `loadHistory` function. New algorithm:

```
1. Initialize: messages = [], pendingToolResults = {}

2. For each message m in history:
   a. If m.role === "user":
      - Push {type: "user", content: m.content}

   b. If m.role === "tool":
      - Store in pendingToolResults[m.tool_call_id] = m.content

   c. If m.role === "assistant":
      - Start new agent block: {type: "agent", streaming: false, timeline: []}

      - If m.thinking_content:
        - Push {type: "thinking", content: ..., expanded: false} to timeline

      - If m.content:
        - Push {type: "text", content: ...} to timeline

      - If m.tool_calls:
        - For each tc in m.tool_calls:
          - Determine isDelegate (tc.name in DELEGATE_TOOLS)
          - Determine isReadOnly (tc.name in READ_ONLY_TOOLS)
          - Look up result from pendingToolResults[tc.id]
          - Push {type: "tool", name: tc.name, status: "completed",
                  result: ..., expanded: isDelegate, isDelegate, isReadOnly}
            to timeline
          - If isDelegate and result is non-empty, parse result as
            sub-agent content and build subTimeline

      - Infer agent identity from tool_calls:
        - If any tc.name === "delegate_to_world_builder" → "WorldBuilder"
        - If any tc.name === "delegate_to_character" → "Character"
        - If any tc.name === "delegate_to_plot" → "Plot"
        - If any tc.name === "delegate_to_chapter" → "Chapter"
        - If any tc.name === "delegate_to_review" → "Review"
        - Else → "Agent"

      - Set timestamp to new Date().toLocaleTimeString()
        (checkpointer doesn't store timestamps)

      - Push agent block to messages
```

### Delegate Sub-Timeline Reconstruction

When a tool call is a delegate (e.g., `delegate_to_world_builder`), its result contains the sub-agent's response text. The frontend should:

1. Treat the result string as the sub-agent's text output
2. Build a `subTimeline` with a single `{type: "text", content: result}` entry
3. This matches the live streaming structure where delegate results appear as sub-agent text

### Edge Cases

- **Multiple consecutive assistant messages**: Each starts a new agent block (this matches LangGraph behavior where the supervisor may emit multiple messages)
- **Tool message without matching tool_call_id**: Append result to the last agent block's timeline as a standalone tool entry
- **Empty tool_calls array**: Treat as a regular text message
- **Assistant message with only tool_calls and no content**: Still create the agent block (tool calls are the content)

## Files Changed

| File | Change |
|------|--------|
| `backend/app/api/v1/chat.py` | Fix thinking extraction in `_messages_to_history_dicts` |
| `agent-tester/index.html` | Rewrite `loadHistory` function |

## Testing

1. Create a project, send a message that triggers tool calls (e.g., "创建一个世界观")
2. Switch to another session, then switch back
3. Verify: agent block shows correct agent badge, tool cards are expandable with results, thinking blocks are collapsible, no "Invalid Date"
4. Verify: delegate sub-agents show their text in sub-timeline
