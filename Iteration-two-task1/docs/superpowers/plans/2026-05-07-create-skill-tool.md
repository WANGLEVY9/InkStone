# Create Skill Tool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `create_skill` LangChain tool so the orchestrator agent can create new skills at runtime.

**Architecture:** New `skill_tools.py` module with a `create_skill_tools()` factory function (no `project_id`, optional `skills_dir` override). Single `create_skill` tool with validation for name, domain, and tags. Integrated into orchestrator in `builder.py`.

**Tech Stack:** Python 3.13, LangChain (`@tool`), SkillService (file-based), pytest

---

### Task 1: Write tests for create_skill tool

**Files:**
- Create: `backend/tests/test_skill_tools.py`

- [ ] **Step 1: Create test file with all test cases**

```python
"""Tests for the create_skill LangChain tool."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core.agent.skill_tools import create_skill_tools


@pytest.fixture()
def skill_tool(tmp_path: Path) -> object:
    """Return the create_skill tool bound to a temp skills directory."""
    tools = create_skill_tools(skills_dir=tmp_path)
    return tools[0]


class TestCreateSkill:
    """Tests for the create_skill tool function."""

    def test_create_skill_success(self, skill_tool: object, tmp_path: Path) -> None:
        """Valid inputs create a skill file and return success."""
        result = skill_tool.invoke({
            "name": "test-skill",
            "description": "A test skill",
            "content": "# Test\nSome content here.",
        })
        assert "Successfully created skill" in result
        assert "test-skill" in result
        # Verify file exists
        skill_file = tmp_path / "test-skill.md"
        assert skill_file.exists()
        raw = skill_file.read_text(encoding="utf-8")
        assert "name: test-skill" in raw
        assert "A test skill" in raw
        assert "# Test" in raw

    def test_create_skill_with_domain(self, skill_tool: object, tmp_path: Path) -> None:
        """Domain is written to frontmatter."""
        result = skill_tool.invoke({
            "name": "chapter-style",
            "description": "A chapter style",
            "content": "# Style\nBody.",
            "domain": "chapter",
        })
        assert "Successfully created skill" in result
        raw = (tmp_path / "chapter-style.md").read_text(encoding="utf-8")
        assert "domain: chapter" in raw

    def test_create_skill_with_tags(self, skill_tool: object, tmp_path: Path) -> None:
        """Comma-separated tags string is parsed to list and written."""
        result = skill_tool.invoke({
            "name": "tagged-skill",
            "description": "A tagged skill",
            "content": "# Tagged\nBody.",
            "tags": "武侠, 写作风格",
        })
        assert "Successfully created skill" in result
        raw = (tmp_path / "tagged-skill.md").read_text(encoding="utf-8")
        assert "武侠" in raw
        assert "写作风格" in raw

    def test_create_skill_global(self, skill_tool: object, tmp_path: Path) -> None:
        """Empty domain creates a global skill (domain field absent or empty)."""
        result = skill_tool.invoke({
            "name": "global-skill",
            "description": "A global skill",
            "content": "# Global\nBody.",
        })
        assert "Successfully created skill" in result
        raw = (tmp_path / "global-skill.md").read_text(encoding="utf-8")
        # domain should be empty/None in frontmatter
        assert "domain:" in raw

    def test_create_skill_duplicate(self, skill_tool: object, tmp_path: Path) -> None:
        """Creating a skill with an existing name returns an error string."""
        skill_tool.invoke({
            "name": "dup-skill",
            "description": "First",
            "content": "# First\nBody.",
        })
        result = skill_tool.invoke({
            "name": "dup-skill",
            "description": "Second",
            "content": "# Second\nBody.",
        })
        assert "Error" in result
        assert "already exists" in result

    def test_create_skill_invalid_domain(self, skill_tool: object) -> None:
        """Invalid domain returns an error string."""
        result = skill_tool.invoke({
            "name": "bad-domain",
            "description": "Bad domain",
            "content": "# Bad\nBody.",
            "domain": "invalid",
        })
        assert "Error" in result
        assert "invalid" in result.lower()

    def test_create_skill_invalid_name(self, skill_tool: object) -> None:
        """Non-kebab-case name returns an error string."""
        result = skill_tool.invoke({
            "name": "Not Valid Name",
            "description": "Bad name",
            "content": "# Bad\nBody.",
        })
        assert "Error" in result
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/test_skill_tools.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.core.agent.skill_tools'`

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_skill_tools.py
git commit -m "test(skill): add tests for create_skill tool"
```

---

### Task 2: Implement create_skill_tools factory

**Files:**
- Create: `backend/app/core/agent/skill_tools.py`

- [ ] **Step 1: Write the implementation**

```python
"""Skill management tools for LangChain agents.

Provides a ``create_skill`` tool that allows the orchestrator to create
new skill files at runtime via ``SkillService``.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from langchain.tools import tool

from app.services.skill import SkillService

VALID_DOMAINS = {"world", "character", "plot", "chapter", "review"}
_NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def create_skill_tools(skills_dir: Path | None = None) -> list[Any]:
    """Create skill management tools.

    Args:
        skills_dir: Optional override for the skills directory.
            Defaults to ``SkillService``'s default (``backend/data/skills/``).

    Returns:
        List containing the ``create_skill`` tool function.
    """
    skill_service = SkillService(skills_dir=skills_dir)

    @tool
    def create_skill(
        name: str,
        description: str,
        content: str,
        domain: str = "",
        tags: str = "",
    ) -> str:
        """Create a new skill that agents can use for specialized guidance.

        Skills are markdown files with YAML frontmatter stored in the skills
        directory.  After creation, the skill becomes immediately available
        to agents via the load_skill tool.

        Args:
            name: Skill identifier in kebab-case (e.g., "my-writing-style").
            description: One-line summary shown in agent system prompts.
            content: Full skill content in markdown format.
            domain: Target agent domain — one of "world", "character", "plot",
                "chapter", "review", or empty string for global.
            tags: Comma-separated tags (e.g., "武侠,写作风格").

        Returns:
            Success message with skill metadata, or error description.
        """
        # Validate name
        if not name or not _NAME_PATTERN.match(name):
            return (
                f"Error: Invalid skill name '{name}'. "
                "Must be kebab-case (lowercase letters, digits, hyphens only), "
                "e.g., 'my-writing-style'."
            )

        # Validate domain
        if domain and domain not in VALID_DOMAINS:
            valid = ", ".join(sorted(VALID_DOMAINS))
            return f"Error: Invalid domain '{domain}'. Must be one of: {valid}, or empty for global."

        # Parse tags
        tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

        # Check duplicate
        existing = skill_service.get_skill(name)
        if existing is not None:
            return f"Error: Skill '{name}' already exists. Use the REST API to update it."

        # Create
        try:
            result = skill_service.create_skill(
                name=name,
                description=description,
                content=content,
                domain=domain or None,
                tags=tag_list,
            )
        except Exception as exc:
            return f"Error: Failed to create skill '{name}' - {exc}"

        domain_display = result.get("domain") or "global"
        tags_display = ", ".join(result.get("tags", [])) or "none"
        return (
            f"Successfully created skill '{name}'.\n"
            f"  Domain: {domain_display}\n"
            f"  Tags: {tags_display}\n"
            f"  Description: {description}"
        )

    return [create_skill]
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/test_skill_tools.py -v`
Expected: All 7 tests PASS

- [ ] **Step 3: Commit**

```bash
git add backend/app/core/agent/skill_tools.py
git commit -m "feat(skill): add create_skill_tools factory with create_skill tool"
```

---

### Task 3: Integrate into orchestrator

**Files:**
- Modify: `backend/app/core/graph/builder.py`

- [ ] **Step 1: Add import and wire tool into orchestrator**

In `builder.py`, add the import:

```python
from app.core.agent.skill_tools import create_skill_tools
```

Then in `create_orchestrator_graph()`, after the `read_tools` line (line 103), add:

```python
    # Skill creation tool (global, no project_id)
    skill_tools = create_skill_tools()
```

And update the tools list to include `*skill_tools`:

```python
        tools=[
            delegate_to_world_builder,
            delegate_to_character,
            delegate_to_plot,
            delegate_to_chapter,
            delegate_to_review,
            *read_tools,
            *skill_tools,
            *skill_middleware.tools,
        ],
```

- [ ] **Step 2: Run orchestrator tests to verify no regressions**

Run: `cd backend && uv run pytest tests/test_orchestrator.py -v`
Expected: All tests PASS

- [ ] **Step 3: Run full test suite**

Run: `cd backend && uv run pytest`
Expected: All tests PASS

- [ ] **Step 4: Run type check and lint**

Run: `cd backend && uv run mypy app && uv run ruff check app tests`
Expected: All checks pass

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/graph/builder.py
git commit -m "feat(agent): integrate create_skill tool into orchestrator"
```

---

### Task 4: Final verification and squash-ready commit

**Files:**
- None (verification only)

- [ ] **Step 1: Run full test suite with coverage**

Run: `cd backend && uv run pytest tests/test_skill_tools.py tests/test_skill_service.py tests/test_skill_middleware.py tests/test_orchestrator.py -v`
Expected: All tests PASS

- [ ] **Step 2: Verify the tool is correctly registered**

Run: `cd backend && uv run python -c "from app.core.agent.skill_tools import create_skill_tools; tools = create_skill_tools(); print(f'Tool name: {tools[0].name}'); print(f'Tool description: {tools[0].description[:80]}...')"`
Expected: Output shows tool name `create_skill` and description
