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

# Skill domains match sub-agent names (used by SkillMiddleware for filtering).
# Note: content tools in tool_factory.py use "outline" instead of "plot".
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
