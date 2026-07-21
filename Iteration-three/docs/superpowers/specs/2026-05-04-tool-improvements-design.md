# Tool Module Improvements Design

## Summary

This design addresses multiple gaps in the current tool module (`backend/app/core/agent/tool_factory.py`):
1. Missing CRUD operations (delete, get-by-ID) across all domains
2. Incomplete supervisor context tools (missing outlines listing, reviews listing)
3. Code duplication in async wrapper pattern (12+ repeated `asyncio.run` + `get_db` blocks)
4. Sub-agent capability asymmetry (system promises search but tools don't provide it)
5. Centralized error handling via `_run_async` helper

## Current State Analysis

### Tools vs Services Gap

| Capability | Service Layer | Tools Layer |
|------------|--------------|-------------|
| Delete | All 5 domains | **None** |
| Get by ID | All 5 domains | Only `get_story_outline` (root only) |
| Search | world, character | Missing for outline, chapter, review |
| Outline tree | `get_tree`, `get_children`, `get_root` | **None** |
| List outlines | `list_all` | **Missing from supervisor** |
| List reviews | `list_all` | **None** |

### Sub-Agent Capability Asymmetry

Each sub-agent's system prompt mentions search capabilities, but actual tools:
- world_builder: has `search_world_setting` ✅
- character: has `search_characters` ✅
- plot: **no search tools** ❌ (prompt says "Search world settings and characters")
- chapter: **no search tools** ❌ (prompt says "Search for relevant context")
- review: **no search tools** ❌ (prompt says "Review for consistency")

## Design Decisions

### 1. Unified Read Tools (3 Generic Tools)

Replace ~10 specialized read tools with 3 generic read tools:

**`query_content(domain, query?)`**
- Lists or searches content across all domains
- `domain`: `"world"` | `"character"` | `"outline"` | `"chapter"` | `"review"`
- `query` (optional): Search keyword. Empty = list all, present = search by name/summary
- Uses Pydantic `args_schema` for type safety (LangChain best practice)

**`get_content(domain, id)`**
- Retrieves full content (metadata + markdown) by ID
- Same `domain` enum constraint

**`get_outline_tree(outline_id?)`**
- Retrieves outline hierarchy
- `outline_id` (optional): Empty = root + entire tree, present = subtree from that node

### 2. Add Delete Tools

Add delete tools to each domain factory:

| Factory | New Tool | Service Method |
|---------|----------|---------------|
| `create_world_tools` | `delete_world_setting(world_setting_id)` | `WorldSettingService.delete` |
| `create_character_tools` | `delete_character(character_id)` | `CharacterService.delete` |
| `create_plot_tools` | `delete_outline(outline_id)` | `OutlineService.delete` (cascade) |
| `create_chapter_tools` | `delete_chapter(chapter_id)` | `ChapterService.delete` |
| `create_review_tools` | `delete_review(review_id)` | `ReviewService.delete` (new) |

Tool descriptions should warn agents to confirm with user before deleting.

### 3. Refactor Async Wrapper Pattern

Extract repeated pattern into helper:

```python
def _run_async[T](coro_factory: Callable[[ContentService], Awaitable[T]]) -> T:
    """Run an async ContentService operation from sync context."""
    async def _wrapper() -> T:
        async with get_db() as db:
            service = ContentService(db)
            return await coro_factory(service)
    return asyncio.run(_wrapper())
```

Usage:
```python
result = _run_async(lambda svc: svc.get_world_setting(id, project_id))
```

### 4. Unified Read Tool Injection

All agents (orchestrator + 5 sub-agents) receive the same 3 read tools:

| Agent | Write Tools | Read Tools (uniform) |
|-------|-------------|---------------------|
| orchestrator | 5 delegate tools | `query_content`, `get_content`, `get_outline_tree` |
| world_builder | 4 world tools | Same 3 read tools |
| character | 4 character tools | Same 3 read tools |
| plot | 3 plot tools | Same 3 read tools |
| chapter | 3 chapter tools | Same 3 read tools |
| review | 2 review tools | Same 3 read tools |

`create_read_tools(project_id)` is called once and shared across all agent constructions.

### 5. Add Search to Remaining Services

Add `search` methods to services that lack them:

**`OutlineService.search(project_id, query)`**
```sql
SELECT * FROM outlines_meta
WHERE project_id = ? AND title LIKE ?
```
Note: `outlines_meta` has no `summary` column; search only on `title`.

**`ChapterService.search(project_id, query)`**
```sql
SELECT * FROM chapters_meta
WHERE project_id = ? AND (title LIKE ? OR summary LIKE ?)
```

**`ReviewService.search(project_id, query)`**
```sql
SELECT * FROM reviews
WHERE project_id = ? AND (content_type LIKE ? OR content_id LIKE ?)
```

### 6. Add ReviewService.delete

```python
async def delete(self, review_id: str, project_id: str) -> bool:
    """Delete a review by ID."""
    cursor = await self.db.execute(
        "DELETE FROM reviews WHERE id = ? AND project_id = ?",
        (review_id, project_id),
    )
    await self.db.commit()
    return cursor.rowcount > 0
```

## Implementation Plan

### Phase 1: Service Layer Extensions

1. Add `search` methods to `OutlineService`, `ChapterService`, `ReviewService`
2. Add `delete` method to `ReviewService`
3. Update `ContentService` facade to expose new methods
4. Add tests for new service methods

### Phase 2: Refactor tool_factory.py

1. Extract `_run_async` helper
2. Create `create_read_tools(project_id)` with 3 generic read tools using Pydantic schemas
3. Add delete tools to each domain factory
4. Refactor all existing tools to use `_run_async`
5. Remove `create_supervisor_tools` (replaced by `create_read_tools`)
6. Add tests for new tools

### Phase 3: Update Sub-Agent Construction

1. Update `langchain_subagents.py` to inject read tools into all sub-agents
2. Update sub-agent system prompts to mention read tool capabilities
3. Update `builder.py` orchestrator construction to use `create_read_tools`
4. Update `ORCHESTRATOR_SYSTEM` prompt with accurate tool descriptions

### Phase 4: Testing

1. Unit tests for new service methods
2. Unit tests for new tools (query_content, get_content, get_outline_tree, all deletes)
3. Integration tests verifying tool registration in sub-agents
4. Verify orchestrator routing works with updated descriptions

## Files to Modify

| File | Changes |
|------|---------|
| `backend/app/services/outline.py` | Add `search` method |
| `backend/app/services/chapter.py` | Add `search` method |
| `backend/app/services/review.py` | Add `search` and `delete` methods |
| `backend/app/services/content.py` | Expose new service methods |
| `backend/app/core/agent/tool_factory.py` | Major refactor: `_run_async`, `create_read_tools`, delete tools |
| `backend/app/core/agent/langchain_subagents.py` | Inject read tools, update prompts |
| `backend/app/core/graph/builder.py` | Use `create_read_tools`, update delegate descriptions |
| `backend/app/core/prompts/orchestrator.py` | Update tool list in prompt |
| `backend/tests/` | New test files for added functionality |

## Error Handling Strategy

The refactored `_run_async` helper centralizes error handling:

```python
def _run_async[T](coro_factory: Callable[[ContentService], Awaitable[T]]) -> T:
    """Run an async ContentService operation from sync context."""
    try:
        async def _wrapper() -> T:
            async with get_db() as db:
                service = ContentService(db)
                return await coro_factory(service)
        return asyncio.run(_wrapper())
    except (sqlite3.Error, RuntimeError) as exc:
        return _format_error("database operation", str(exc))
    except Exception as exc:
        return _format_error("unexpected error", str(exc))
```

For tools that combine LLM generation + storage (e.g., `create_world_setting`), keep the two-phase pattern: sync LLM call first, then `_run_async` for storage. LLM errors and storage errors are handled separately with appropriate messages.

## Backward Compatibility

- **Kept**: Domain-specific search tools (`search_world_setting`, `search_characters`) remain in their respective factories. Sub-agents can use either the generic `query_content` or the specific tools.
- **Removed**: `create_supervisor_tools` is replaced by `create_read_tools`. All references in `builder.py` must be updated.
- **New**: Delete tools are additions; no existing tools change names or signatures.

## Risks and Mitigations

| Risk | Mitigation |
|------|-----------|
| LLM confused by generic tools vs specific tools | Clear docstrings with examples, Literal enum for domain |
| Delete called without confirmation | Tool description explicitly warns to confirm |
| `_run_async` breaks with nested event loops | Keep sync design (LangGraph thread pool handles this) |
| Breaking change to existing tool names | `create_supervisor_tools` removal is breaking; update all references |
