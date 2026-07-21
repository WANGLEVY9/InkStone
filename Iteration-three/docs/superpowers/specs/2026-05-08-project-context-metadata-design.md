# Add Project Name & Description to Agent Context

**Date:** 2026-05-08
**Status:** Proposed

## Problem

The orchestrator and sub-agents operate on a project but have no awareness of the project's name or description. The `ProjectContext` TypedDict only carries content data (world settings, characters, outline, chapters). The project's own metadata from the `projects` table (`name`, `description`) is never loaded into the graph state.

This means agents cannot reference the project's identity when generating content or responding to users.

## Approach

Add `project_name` and `project_description` fields to `ProjectContext`, and fetch them in `chat_stream_endpoint` alongside the existing content data. Read-only — no new agent tools.

## Changes

### 1. `backend/app/core/graph/state.py` — Extend `ProjectContext`

Add two fields to the TypedDict:

```python
class ProjectContext(TypedDict):
    project_name: str
    project_description: str | None
    world_settings: list[dict[str, str]]
    characters: list[dict[str, str]]
    outline: dict[str, str] | None
    chapters: list[dict[str, str]]
```

### 2. `backend/app/api/v1/chat.py` — Fetch and include project metadata

In `chat_stream_endpoint`, fetch the project record and include `name`/`description` in `project_context`:

- Import `get_project` from `project_repository`
- Call `get_project(db, project_id)` to get the project row
- Add `project_name` and `project_description` to the `project_context` dict in `initial_state`

The project fetch can run in parallel with the existing `asyncio.gather` for content data.

### 3. No orchestrator prompt changes

The orchestrator system prompt (`orchestrator.py`) does not need updating — the project context is available in the graph state and agents can reference it naturally through conversation. Adding explicit prompt instructions is unnecessary for this read-only context injection.

### 4. No new tools

The agent cannot modify `name` or `description`. This is intentional — project metadata management is a user-facing operation, not an agent operation.

## Files Touched

| File | Change |
|------|--------|
| `backend/app/core/graph/state.py` | Add `project_name`, `project_description` to `ProjectContext` |
| `backend/app/api/v1/chat.py` | Fetch project record, include in `project_context` |
| `backend/tests/` | Update any tests that construct `ProjectContext` or `OrchestratorState` dicts |

## Verification

- Run `uv run pytest` — all existing tests pass
- Run `uv run mypy app` — type-check passes
- Manual test: send a chat message and verify the agent can reference the project name in its responses
