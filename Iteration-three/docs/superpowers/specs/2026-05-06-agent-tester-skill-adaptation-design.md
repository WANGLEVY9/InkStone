# Agent-Tester Skill System Adaptation

**Date:** 2026-05-06
**Scope:** Adapt `agent-tester/index.html` to support the skill system (CRUD at `/api/v1/skills/`, `load_skill` tool, `SkillMiddleware`).

## Problem

The agent-tester has no awareness of the skill system:
- `load_skill` tool is not in `READ_ONLY_TOOLS`, so it displays with a "write" badge in the timeline
- No UI for browsing, creating, editing, or deleting skills
- Skills are global resources (not project-scoped) with their own API endpoints

## Design

### 1. Tool Recognition

Add `'load_skill'` to the `READ_ONLY_TOOLS` Set so it renders with a "read" tag in the tool timeline.

### 2. Skills Panel

A new right-side panel (same pattern as the Files panel) for managing skills.

**State:**
- `showSkillsPanel` (ref, boolean) — panel visibility toggle
- `skills` (ref, array) — list of `{name, description, domain, tags}`
- `selectedSkill` (ref, object|null) — currently viewed skill with full content
- `isCreatingSkill` (ref, boolean) — whether create form is active
- `isEditingSkill` (ref, boolean) — whether edit form is active
- `skillForm` (reactive) — `{name, description, content, domain, tags}`

**Layout:**
```
┌─────────────────────────────┐
│ Skills           [×] close  │
├─────────────────────────────┤
│ [+ New Skill]               │
├─────────────────────────────┤
│ skill cards (scrollable)    │
│   name / description / tags │
├─────────────────────────────┤
│ Content area or form        │
│   [Edit] [Delete]           │
└─────────────────────────────┘
```

**API calls:**
- List: `GET /api/v1/skills/`
- Get: `GET /api/v1/skills/{name}`
- Create: `POST /api/v1/skills/` with `{name, description, content, domain?, tags?}`
- Update: `POST /api/v1/skills/{name}/update` with `{description?, content?, domain?, tags?}`
- Delete: `POST /api/v1/skills/{name}/delete`

### 3. Header Integration

Add a "skills" toggle button in the header bar, next to the existing "files" button. Same styling as `.debug-toggle.files-toggle`.

### 4. CSS

New classes following existing patterns:
- `.skills-section` — same dimensions/positioning as `.files-section`
- `.skill-card` — individual skill entry in the list
- `.skill-tag` — domain/tags chip display
- `.skill-form-*` — form field styles (reuse existing input/select styles)

### 5. Integration

- Skills panel renders in `<div class="main-layout">` alongside chat, debug, and files panels
- Skills panel is independent of project selection (skills are global)
- `loadFileCategories` is called on project change; `loadSkills` should be called on panel open (no project dependency)

## Files Changed

| File | Change |
|------|--------|
| `agent-tester/index.html` | Add skills panel UI, state, API calls, CSS, and `load_skill` to READ_ONLY_TOOLS |

Single file, no backend changes needed.
