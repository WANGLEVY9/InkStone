# Frontend P0 Fixes + Module Cleanup

**Date:** 2026-05-09
**Scope:** 5 P0 bug fixes + review module removal + related P1 improvements
**Strategy:** Approach B — fix P0 issues and co-located P1 issues in the same files

## Summary

This iteration fixes 5 P0 functional defects and removes the unused review module from the frontend. Changes are concentrated in 13 files across the AI chat, content management, and layout subsystems.

## Changes

### 1. Remove Review Module (Frontend Only)

Delete files:
- `frontend/src/pages/reviews/ReviewList.tsx`
- `frontend/src/api/reviews.ts`

Modify files:
- `frontend/src/App.tsx` — remove `/projects/:id/reviews` route and its lazy import
- `frontend/src/components/layout/SecondaryNav.tsx` — remove "审阅" menu item
- `frontend/src/types/index.ts` — remove `Review`, `CreateReviewRequest` interfaces

Backend API, database schema, and `backend/data/` review files are untouched.

### 2. AI Chat Fixes

#### 2a. Session History Loading (`ChatPanel.tsx`)

When switching sessions via the Select dropdown:
1. Call `sessionsApi.getHistory(selectedSessionId)` to fetch previous messages
2. Convert returned `ChatMessage[]` to `SSEMessage[]` format (mapping `role` field)
3. Replace current messages with loaded history
4. Show `Spin` indicator during load

Currently `clearMessages()` is called but history is never loaded, so switching sessions shows an empty chat.

Error handling: if `getHistory` fails, show `message.error('加载会话历史失败')` and leave messages empty (do not crash).

#### 2b. Markdown Rendering (`MessageBubble.tsx`)

For `role === 'agent'` messages:
- Parse content with `marked.parse()` (already installed as `marked@14`)
- Sanitize with `DOMPurify.sanitize()` (already installed as `dompurify@3`)
- Render via `dangerouslySetInnerHTML` wrapped in Ant Design `Typography`
- Keep `whiteSpace: 'pre-wrap'` for user messages (plain text is appropriate)

#### 2c. Loading Indicator (`MessageBubble.tsx`)

When `isLoading` is true and the agent message content is empty:
- Show `Spin` component inside the message bubble
- Prevents the user from seeing a blank bubble while waiting for the first token

#### 2d. SSE Stream Cancellation (`useSSE.ts` + `ChatPanel.tsx`)

`useSSE` changes:
- Create `AbortController` at the start of `sendMessage`
- Pass `signal` to the `fetch` call
- Return a `cancel()` function from `sendMessage` that calls `controller.abort()`
- Store the cancel function in a `useRef` so ChatPanel can access it

`ChatPanel` changes:
- Show a "停止生成" `Button` (with `StopOutlined` icon) when `isLoading` is true
- Clicking it calls the cancel function from the hook
- Hide the send button while loading, show cancel button instead

### 3. Content Management Fixes

#### 3a. World Setting Deletion (`WorldList.tsx`)

- Add a delete icon button to each `WorldCard` (or wrap card actions)
- Use `Popconfirm` for confirmation: "确定删除这个世界观设定？"
- On confirm: call `worldApi.delete(worldId)`
- On success: remove from local state, show `message.success('已删除')`

#### 3b. Preserve Character Frontmatter (`CharacterEdit.tsx`)

Current bug: `serializeWithFrontmatter` is called with only `{ tags }`, so other parsed fields (type, age, etc.) are lost on save.

Fix:
1. On load, store the full parsed `CharacterMeta` object in component state
2. On save, merge the stored meta with any user edits: `serializeWithFrontmatter(content, { ...storedMeta, tags: currentTags })`
3. This preserves all frontmatter fields even if the edit page only exposes tag editing

#### 3c. Chapter Auto-Renumbering (`ChapterList.tsx`)

After deleting a chapter:
1. Filter the deleted chapter from local state
2. Sort remaining chapters by `sort_order`
3. Reassign `chapter_number` sequentially: 1, 2, 3, ...
4. Call `chaptersApi.update(chapterId, { chapter_number: newNumber })` for each chapter whose number changed (fire-and-forget; do not block UI on each call)

New chapter creation:
- Use `Math.max(0, ...chapters.map(c => c.chapter_number)) + 1` instead of `chapters.length + 1`
- This ensures no gaps even if renumbering hasn't completed yet

### 4. Co-located P1 Fixes

#### 4a. PageHeader Breadcrumbs (`PageHeader.tsx`)

Replace `<a href={item.path}>` with `<Link to={item.path}>` from `react-router-dom`.
This enables client-side navigation instead of full page reloads.

#### 4b. Edit Page Loading Spinners

**WorldEdit.tsx:** When `loading || !world`, render `<div style={{textAlign:'center',padding:100}}><Spin size="large" /></div>` instead of returning `null`.

**CharacterEdit.tsx:** Same pattern — show a centered `Spin` during load.

#### 4c. useSSE Stability (`useSSE.ts`)

- The `processEvent` function is defined inside `sendMessage`'s callback but called from `setMessages` updater, creating a stale closure
- Fix: use functional update form `setMessages(prev => ...)` and move `processEvent` logic inline or use `useRef` for the setter
- Handle `response.body === null` case: throw a descriptive error instead of the current `!` assertion that produces an opaque TypeError

## File Change Summary

| File | Action | Changes |
|------|--------|---------|
| `pages/reviews/ReviewList.tsx` | DELETE | Remove review page |
| `api/reviews.ts` | DELETE | Remove review API client |
| `App.tsx` | MODIFY | Remove review route |
| `components/layout/SecondaryNav.tsx` | MODIFY | Remove review nav item |
| `types/index.ts` | MODIFY | Remove Review types |
| `components/ai/ChatPanel.tsx` | MODIFY | Session history loading, cancel button |
| `components/ai/MessageBubble.tsx` | MODIFY | Markdown rendering, loading indicator |
| `hooks/useSSE.ts` | MODIFY | AbortController, cancel function, closure fix |
| `pages/world/WorldList.tsx` | MODIFY | Delete functionality |
| `pages/world/WorldEdit.tsx` | MODIFY | Loading spinner |
| `pages/characters/CharacterEdit.tsx` | MODIFY | Frontmatter preservation, loading spinner |
| `pages/chapters/ChapterList.tsx` | MODIFY | Auto-renumbering after delete |
| `components/common/PageHeader.tsx` | MODIFY | Breadcrumb Link fix |

Total: 2 files deleted, 11 files modified.

## Out of Scope

These items are explicitly NOT included in this iteration:
- CSS/styling refactor (inline styles remain)
- Route-level code splitting / lazy loading
- Error boundaries and 404 page
- Responsive layout
- Frontend testing framework
- SSE code deduplication (sessionsApi.stream vs useSSE)
- Auto-save on edit pages
- CharacterList delete functionality (not reported as P0)
