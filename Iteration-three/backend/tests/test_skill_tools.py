"""Tests for the create_skill LangChain tool."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from app.core.agent.skill_tools import create_skill_tools


@pytest.fixture()
def skill_tool(tmp_path: Path) -> Any:
    """Return the create_skill tool bound to a temp skills directory."""
    tools = create_skill_tools(skills_dir=tmp_path)
    return tools[0]


class TestCreateSkill:
    """Tests for the create_skill tool function."""

    def test_create_skill_success(self, skill_tool: Any, tmp_path: Path) -> None:
        """Valid inputs create a skill file and return success."""
        result = skill_tool.invoke(
            {
                "name": "test-skill",
                "description": "A test skill",
                "content": "# Test\nSome content here.",
            }
        )
        assert "Successfully created skill" in result
        assert "test-skill" in result
        # Verify file exists
        skill_file = tmp_path / "test-skill.md"
        assert skill_file.exists()
        raw = skill_file.read_text(encoding="utf-8")
        assert "name: test-skill" in raw
        assert "A test skill" in raw
        assert "# Test" in raw

    def test_create_skill_with_domain(self, skill_tool: Any, tmp_path: Path) -> None:
        """Domain is written to frontmatter."""
        result = skill_tool.invoke(
            {
                "name": "chapter-style",
                "description": "A chapter style",
                "content": "# Style\nBody.",
                "domain": "chapter",
            }
        )
        assert "Successfully created skill" in result
        raw = (tmp_path / "chapter-style.md").read_text(encoding="utf-8")
        assert "domain: chapter" in raw

    def test_create_skill_with_tags(self, skill_tool: Any, tmp_path: Path) -> None:
        """Comma-separated tags string is parsed to list and written."""
        result = skill_tool.invoke(
            {
                "name": "tagged-skill",
                "description": "A tagged skill",
                "content": "# Tagged\nBody.",
                "tags": "武侠, 写作风格",
            }
        )
        assert "Successfully created skill" in result
        raw = (tmp_path / "tagged-skill.md").read_text(encoding="utf-8")
        assert "武侠" in raw
        assert "写作风格" in raw

    def test_create_skill_global(self, skill_tool: Any, tmp_path: Path) -> None:
        """Empty domain creates a global skill (domain field absent or empty)."""
        result = skill_tool.invoke(
            {
                "name": "global-skill",
                "description": "A global skill",
                "content": "# Global\nBody.",
            }
        )
        assert "Successfully created skill" in result
        raw = (tmp_path / "global-skill.md").read_text(encoding="utf-8")
        # domain should be empty/None in frontmatter
        assert "domain:" in raw

    def test_create_skill_duplicate(self, skill_tool: Any, tmp_path: Path) -> None:
        """Creating a skill with an existing name returns an error string."""
        skill_tool.invoke(
            {
                "name": "dup-skill",
                "description": "First",
                "content": "# First\nBody.",
            }
        )
        result = skill_tool.invoke(
            {
                "name": "dup-skill",
                "description": "Second",
                "content": "# Second\nBody.",
            }
        )
        assert "Error" in result
        assert "already exists" in result

    def test_create_skill_invalid_domain(self, skill_tool: Any) -> None:
        """Invalid domain returns an error string."""
        result = skill_tool.invoke(
            {
                "name": "bad-domain",
                "description": "Bad domain",
                "content": "# Bad\nBody.",
                "domain": "invalid",
            }
        )
        assert "Error" in result
        assert "invalid" in result.lower()

    def test_create_skill_invalid_name(self, skill_tool: Any) -> None:
        """Non-kebab-case name returns an error string."""
        result = skill_tool.invoke(
            {
                "name": "Not Valid Name",
                "description": "Bad name",
                "content": "# Bad\nBody.",
            }
        )
        assert "Error" in result
