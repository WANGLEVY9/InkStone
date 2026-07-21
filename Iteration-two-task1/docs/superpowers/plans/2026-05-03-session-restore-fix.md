# Session Restore Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix session restore in agent-tester so that tool calls, agent identity, thinking blocks, and timestamps all survive session switching.

**Architecture:** Backend `_messages_to_history_dicts` gets minimal fix (thinking extraction). Frontend `loadHistory` is rewritten to reconstruct timeline from raw messages: matching tool_calls to tool results, inferring agent identity from delegate tool names, and building tool-card entries with completed status.

**Tech Stack:** Python (FastAPI), JavaScript (Vue 3, vanilla in agent-tester/index.html)

---

### Task 1: Fix backend thinking extraction

**Files:**
- Modify: `backend/app/api/v1/chat.py:65-99` — `_messages_to_history_dicts`

The current code only checks `msg.additional_kwargs.get("thinking")` for thinking content. Anthropic's API may return thinking as part of `msg.content` (structured dict format with `{"type": "thinking", ...}` items). Add fallback.

- [ ] **Step 1: Read current implementation**

Read `backend/app/api/v1/chat.py` lines 65-99 to confirm current thinking extraction logic.

- [ ] **Step 2: Fix thinking extraction**

In `_messages_to_history_dicts`, replace the thinking extraction block (lines 91-93) with:

```python
            # Extract thinking: try additional_kwargs first, then content dict
            thinking = None
            if hasattr(msg, "additional_kwargs"):
                thinking = msg.additional_kwargs.get("thinking")
            if not thinking and isinstance(msg.content, list):
                for block in msg.content:
                    if isinstance(block, dict) and block.get("type") == "thinking":
                        thinking = block.get("thinking", "")
                        break
            if thinking:
                entry["thinking_content"] = thinking
```

- [ ] **Step 3: Run backend tests**

Run: `cd backend && uv run pytest tests/test_chat_error_handling.py -v`

Expected: PASS (existing tests still pass)

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/v1/chat.py
git commit -m "fix(api): extract thinking from content dict fallback in history"
```

---

### Task 2: Rewrite frontend loadHistory

**Files:**
- Modify: `agent-tester/index.html:1757-1788` — `loadHistory` function

Complete rewrite to properly reconstruct timeline from raw history messages.

- [ ] **Step 1: Read current implementation**

Read `agent-tester/index.html` lines 1757-1788 to confirm current `loadHistory`.

- [ ] **Step 2: Replace loadHistory function**

Replace the entire `loadHistory` function (lines 1757-1788) with:

```javascript
        const loadHistory = async () => {
          if (!currentSessionId.value) return;
          messages.value = [];
          try {
            const res = await fetch(`${API_BASE}/projects/${currentProjectId.value}/sessions/${currentSessionId.value}/history`);
            if (!res.ok) return;
            const history = await res.json();

            const pendingToolResults = {};

            for (const m of history) {
              if (m.role === 'user') {
                messages.value.push({ type: 'user', content: m.content });
                continue;
              }

              if (m.role === 'tool') {
                // Store tool result for later matching
                if (m.tool_call_id) {
                  pendingToolResults[m.tool_call_id] = m.content;
                }
                continue;
              }

              // role === 'assistant'
              const tl = [];

              // Thinking
              if (m.thinking_content) {
                tl.push(reactive({ type: 'thinking', content: m.thinking_content, expanded: false }));
              }

              // Text content
              if (m.content) {
                tl.push(reactive({ type: 'text', content: m.content }));
              }

              // Tool calls
              let agentName = 'Agent';
              if (m.tool_calls && m.tool_calls.length) {
                for (const tc of m.tool_calls) {
                  const isDelegate = DELEGATE_TOOLS.has(tc.name);
                  const isReadOnly = READ_ONLY_TOOLS.has(tc.name);
                  const result = pendingToolResults[tc.id] ?? null;
                  delete pendingToolResults[tc.id];

                  const toolEntry = reactive({
                    type: 'tool',
                    name: tc.name,
                    toolCallId: tc.id,
                    status: 'completed',
                    result: result,
                    expanded: isDelegate,
                    isDelegate,
                    isReadOnly,
                    duration: null,
                    subTimeline: undefined
                  });

                  // Build sub-timeline for delegate calls
                  if (isDelegate && result) {
                    toolEntry.subTimeline = [
                      reactive({ type: 'text', content: result })
                    ];
                  }

                  tl.push(toolEntry);

                  // Infer agent identity from delegate calls
                  const delegateAgentMap = {
                    'delegate_to_world_builder': 'WorldBuilder',
                    'delegate_to_character': 'Character',
                    'delegate_to_plot': 'Plot',
                    'delegate_to_chapter': 'Chapter',
                    'delegate_to_review': 'Review'
                  };
                  if (delegateAgentMap[tc.name]) {
                    agentName = delegateAgentMap[tc.name];
                  }
                }
              }

              messages.value.push({
                type: 'agent',
                content: m.content,
                agent: agentName,
                timestamp: new Date().toLocaleTimeString(),
                streaming: false,
                timeline: tl
              });
            }

            // Handle any orphaned tool results (no matching tool_call_id)
            for (const [toolCallId, result] of Object.entries(pendingToolResults)) {
              const lastAgent = [...messages.value].reverse().find(m => m.type === 'agent');
              if (lastAgent) {
                lastAgent.timeline.push(reactive({
                  type: 'tool',
                  name: 'tool_result',
                  toolCallId,
                  status: 'completed',
                  result,
                  expanded: false,
                  isDelegate: false,
                  isReadOnly: false,
                  duration: null
                }));
              }
            }

            scrollToBottom();
          } catch (e) { console.error('loadHistory failed', e); }
        };
```

- [ ] **Step 3: Manual test**

1. Open `http://localhost:8080`
2. Select a project that has chat history with tool calls
3. Switch to a session with history
4. Verify: agent blocks show correct agent badges (WorldBuilder, Character, etc.)
5. Verify: tool cards appear with status "completed" and are expandable
6. Verify: thinking blocks are collapsible
7. Verify: no "Invalid Date" in timestamps
8. Verify: delegate sub-agents show their text in sub-timeline

- [ ] **Step 4: Commit**

```bash
git add agent-tester/index.html
git commit -m "fix(tester): rewrite loadHistory to restore tool calls and agent identity"
```

---

### Task 3: Verify end-to-end

**Files:** None (manual verification)

- [ ] **Step 1: Start dev environment**

Run: `cd backend && uv run uvicorn app.main:app --reload` (port 8000)
Run: `cd agent-tester && python -m http.server 8080` (port 8080)

- [ ] **Step 2: Create fresh test scenario**

1. Open `http://localhost:8080`
2. Create a new project (or select existing)
3. Create a new session
4. Send: "请帮我创建一个科幻世界观"
5. Wait for response to complete (should see tool calls in live view)
6. Note the session

- [ ] **Step 3: Test session restore**

1. Switch to a different session (or create a new one)
2. Switch back to the session from Step 2
3. Verify all of:
   - Agent badge shows "WorldBuilder" (not "Agent")
   - Tool cards for `delegate_to_world_builder` are visible and expandable
   - Sub-agent text appears in delegate sub-timeline
   - Thinking blocks are collapsible (if any)
   - Timestamps show valid time (not "Invalid Date")

- [ ] **Step 4: Commit any fixes**

If any issues found during testing, fix and commit.
