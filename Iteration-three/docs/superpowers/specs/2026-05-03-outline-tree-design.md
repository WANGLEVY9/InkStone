# Outline Tree Structure Redesign

## Problem Statement

The `outlines_meta` table uses an adjacency list (`parent_id` self-reference) that fully supports tree structures, but the service and API layers don't properly utilize it:

- `OutlineService.create` returns incomplete data (missing `parent_id`, `type`, `sort_order`)
- No cascade delete — deleting a parent node violates the FK constraint
- No endpoint to fetch the full tree in one request
- AI tools can only create root-level outlines (no `parent_id` support) — deferred to future work

## Design Decisions

| Decision | Choice |
|----------|--------|
| Tree depth | Fixed 3 levels: root (全书大纲) → volume (卷) → chapter (章) |
| Node content | Each node stores outline description (not prose); actual chapter text lives in `chapters` table |
| `get_tree` format | Nested `{ id, title, type, sort_order, children }` without `content` |
| API conventions | Keep existing: `POST /{id}/update`, `POST /{id}/delete` |
| Scope | Service layer + API layer only; agent tools and graph state deferred |

## Changes

### 1. Service Layer (`backend/app/services/outline.py`)

#### 1.1 Fix `create` return value

Current return: `{id, project_id, title, file_path}`

Change to return all metadata fields: `{id, project_id, parent_id, title, type, sort_order, file_path, created_at, updated_at}`

#### 1.2 Cascade delete

Replace the current single-node `DELETE` with recursive deletion:

1. Query all descendant node IDs using a recursive CTE:
   ```sql
   WITH RECURSIVE descendants AS (
       SELECT id FROM outlines_meta WHERE id = ?
       UNION ALL
       SELECT om.id FROM outlines_meta om JOIN descendants d ON om.parent_id = d.id
   )
   SELECT id FROM descendants
   ```
2. For each descendant (leaf-first): delete the Markdown file, then delete the metadata row
3. Delete the target node itself last

This avoids FK constraint violations without needing `ON DELETE CASCADE`.

#### 1.3 New `get_tree(node_id)` method

Returns the subtree rooted at `node_id` as a nested structure **without content**.

Implementation:
1. Query all descendants with a recursive CTE (same as cascade delete)
2. Fetch metadata for all nodes in one query: `SELECT id, parent_id, title, type, sort_order FROM outlines_meta WHERE id IN (...)`
3. Build nested tree in application layer using a dict lookup

Return format:
```python
{
    "id": "root-uuid",
    "title": "全书大纲",
    "type": "root",
    "sort_order": 0,
    "children": [
        {
            "id": "vol-uuid",
            "title": "第一卷",
            "type": "volume",
            "sort_order": 1,
            "children": [
                {
                    "id": "ch-uuid",
                    "title": "第一章",
                    "type": "chapter",
                    "sort_order": 1,
                    "children": []
                }
            ]
        }
    ]
}
```

Individual node content is still fetched via the existing `GET /{outline_id}` endpoint.

#### 1.4 Level validation in `create`

Enforce the fixed 3-level hierarchy:

| `type` | `parent_id` constraint |
|--------|----------------------|
| `root` | Must be `NULL`. Only one root per project allowed. |
| `volume` | Parent must have `type = "root"` |
| `chapter` | Parent must have `type = "volume"` |

Raise `ValueError` with a descriptive message on violation.

### 2. API Layer (`backend/app/api/v1/outlines.py`)

#### 2.1 New endpoint: `GET /{outline_id}/tree`

```python
@router.get("/{outline_id}/tree")
async def get_outline_tree(outline_id: str, project_id: str) -> dict:
```

Returns the nested tree structure (without content) rooted at `outline_id`. Delegates to `OutlineService.get_tree()`.

#### 2.2 Existing `POST /` (create outline)

`CreateOutlineRequest` already has `parent_id` — no interface change needed. Ensure the `parent_id` value is passed through to `OutlineService.create()` (currently it may be ignored).

#### 2.3 Existing `POST /{outline_id}/delete`

The delete endpoint itself doesn't change, but the underlying service call now cascades to children.

#### 2.4 `ContentService` facade

Add `get_outline_tree` delegation method to `ContentService` for consistency.

### 3. Files to Modify

| File | Changes |
|------|---------|
| `backend/app/services/outline.py` | Fix `create` return, cascade `delete`, add `get_tree`, add level validation |
| `backend/app/services/content.py` | Add `get_outline_tree` delegation |
| `backend/app/api/v1/outlines.py` | Add `GET /{outline_id}/tree` endpoint, ensure `parent_id` passthrough in create |

### 4. Testing

- Test cascade delete: create root → volume → chapter, delete root, verify all gone
- Test `get_tree`: create a small tree, verify nested structure returned correctly
- Test level validation: attempt to create a chapter under a root (should fail)
- Test single-root constraint: attempt to create two roots for same project (should fail)
- Test `create` return value: verify all fields present in response

### 5. Out of Scope (Deferred)

- Agent tool modifications (adding `parent_id` to `create_outline` tool)
- Graph state changes (`ProjectContext.outline` type)
- Frontend changes
- Bulk tree endpoint (`PUT /tree`)
