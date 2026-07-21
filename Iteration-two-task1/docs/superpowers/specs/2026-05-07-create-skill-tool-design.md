# Design: `create_skill` LangChain Tool

**Date:** 2026-05-07
**Status:** Approved
**Scope:** Add a `create_skill` tool that the orchestrator agent can use to create new skills at runtime.

## Problem

The existing `create_skill.md` meta-skill guides agents through creating skills, but there is no actual LangChain `@tool` for it. Agents can only load existing skills (`load_skill` from SkillMiddleware) — they cannot programmatically create new ones. The `SkillService.create_skill()` method exists but is not exposed as a tool.

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Agent scope | Orchestrator only | Skill creation is a global administrative action; sub-agents should only load/use skills |
| File location | `backend/app/core/agent/skill_tools.py` | New file, keeps skill tools separate from content tools |
| CRUD scope | Create only | Update/delete are rare and potentially destructive; REST API covers those |
| `project_id` | None | Skills are global (stored in `backend/data/skills/`), not per-project |
| DI for SkillService | Self-contained factory with `skills_dir` override | SkillService is stateless (file I/O); `skills_dir` param enables test isolation without full DI |

## Architecture

### New file: `backend/app/core/agent/skill_tools.py`

A factory function `create_skill_tools()` that returns a list containing one `@tool` function.

```python
def create_skill_tools(skills_dir: Path | None = None) -> list[Any]:
    skill_service = SkillService(skills_dir=skills_dir)

    @tool
    def create_skill(
        name: str,
        description: str,
        content: str,
        domain: str = "",
        tags: str = "",
    ) -> str:
        """Create a new skill that agents can use for specialized guidance."""
        # 1. Validate name (kebab-case, non-empty)
        # 2. Validate domain (empty or one of world/character/plot/chapter/review)
        # 3. Parse tags (comma-separated string → list[str])
        # 4. Check duplicate via skill_service.get_skill()
        # 5. Call skill_service.create_skill()
        # 6. Return success message with created skill metadata

    return [create_skill]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | `str` | Yes | Skill identifier, kebab-case (e.g., `my-writing-style`) |
| `description` | `str` | Yes | One-line summary shown in agent system prompts |
| `content` | `str` | Yes | Full skill content in markdown |
| `domain` | `str` | No | Target agent: `world`/`character`/`plot`/`chapter`/`review`, or empty for global |
| `tags` | `str` | No | Comma-separated tags (e.g., `"武侠,写作风格"`) |

#### Validation rules

1. **Name**: Must be non-empty, kebab-case (lowercase letters, digits, hyphens only). Pattern: `^[a-z0-9]+(-[a-z0-9]+)*$`
2. **Domain**: Must be empty string or one of `{"world", "character", "plot", "chapter", "review"}`
3. **Tags**: Parsed from comma-separated string to `list[str]`. Empty string → empty list. Whitespace trimmed.
4. **Duplicate**: If `skill_service.get_skill(name)` returns non-null, return error message (not raise)

#### Error handling

Uses `_format_error()` pattern consistent with other tools:
- Validation failures → descriptive error string
- Duplicate name → `"Error: Skill 'X' already exists"` with suggestion to use update instead
- Unexpected exceptions → caught and formatted

#### No `asyncio.run()`

Unlike content tools that wrap async DB calls, `SkillService` is synchronous file I/O. The tool calls `SkillService.create_skill()` directly.

### Modified file: `backend/app/core/graph/builder.py`

Add `create_skill_tools()` to the orchestrator's tool list:

```python
from app.core.agent.skill_tools import create_skill_tools

# In create_orchestrator_graph():
skill_tools = create_skill_tools()  # uses default skills_dir
tools = [*read_tools, *skill_tools, *delegate_tools]
```

The orchestrator agent now has:
- `create_skill` (from skill_tools) — create new skills
- `load_skill` (from SkillMiddleware) — load existing skills into context
- `query_content`, `get_content`, `get_outline_tree` (from read_tools)
- `delegate_to_*` (from sub-agent wrappers)

### New file: `backend/tests/test_skill_tools.py`

Tests pass `skills_dir=tmp_path` to the factory for isolation (no monkeypatch needed):

1. **`test_create_skill_success`** — valid inputs, verifies file written and metadata correct
2. **`test_create_skill_with_domain`** — creates domain-specific skill
3. **`test_create_skill_with_tags`** — comma-separated tags parsed correctly
4. **`test_create_skill_duplicate`** — returns error string, not exception
5. **`test_create_skill_invalid_domain`** — returns error for bad domain
6. **`test_create_skill_invalid_name`** — returns error for non-kebab-case name
7. **`test_create_skill_global`** — empty domain creates global skill


## Integration Flow

After this change, the skill creation flow becomes:

1. User asks orchestrator to create a skill (e.g., "create a writing style skill for detective noir")
2. Orchestrator sees `create_skill.md` meta-skill in its system prompt (via SkillMiddleware)
3. Orchestrator loads the meta-skill via `load_skill("create_skill")` for guidance
4. Orchestrator calls `create_skill(name="detective-noir", description="...", content="...", domain="chapter")`
5. Skill is written to `backend/data/skills/detective-noir.md`
6. On next model call, `SkillMiddleware` picks up the new skill and injects it into system prompts

## Files Changed

| File | Change |
|------|--------|
| `backend/app/core/agent/skill_tools.py` | **New** — `create_skill_tools()` factory |
| `backend/app/core/graph/builder.py` | Add skill_tools to orchestrator |
| `backend/tests/test_skill_tools.py` | **New** — unit tests |

## Out of Scope

- Update/delete tools (covered by REST API)
- Project-scoped skills (skills are global by design)
- Sub-agent access to create_skill (orchestrator only)
- Moving `load_skill` out of SkillMiddleware (no need to change working code)
