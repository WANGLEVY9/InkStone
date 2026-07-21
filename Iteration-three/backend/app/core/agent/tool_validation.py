"""Tool input validation for pre-execution conflict detection.

Provides a ``ToolInputValidator`` that checks tool parameters against
the project's world settings before execution, helping prevent
inconsistent creative generation (e.g. western fantasy elements in a
xianxia novel).
"""

from __future__ import annotations

from typing import Any

from app.db.connection import get_db
from app.services.content import ContentService

# Genre keywords that help detect setting mismatches
_XIANXIA_KEYWORDS = frozenset(
    {
        "修仙",
        "仙侠",
        "修真",
        "筑基",
        "金丹",
        "元婴",
        "化神",
        "灵气",
        "灵根",
        "丹田",
        "功法",
        "法宝",
        "炼丹",
        "渡劫",
        "xianxia",
        "cultivation",
        "xiuxian",
    }
)

_WESTERN_FANTASY_KEYWORDS = frozenset(
    {
        "西方魔幻",
        "剑与魔法",
        "龙与地下城",
        "骑士",
        "魔法师",
        "wizard",
        "knight",
        "dragon",
        "fantasy",
        "西方奇幻",
        "魔法",
        "斗气",
        "精灵",
        "矮人",
        "兽人",
    }
)

_URBAN_KEYWORDS = frozenset(
    {
        "都市",
        "现代",
        "校园",
        "职场",
        "现实",
        "urban",
        "modern",
        "city",
    }
)


class ToolInputValidator:
    """Validates tool inputs against project context for conflict detection.

    Checks tool parameters (e.g. style, genre, entity names) against the
    project's world settings and warns about potential inconsistencies.
    """

    def __init__(self, project_id: str):
        self.project_id = project_id
        self._world_settings: list[dict[str, Any]] | None = None

    async def _load_world_settings(self) -> list[dict[str, Any]]:
        """Load project world settings, caching for multiple checks."""
        if self._world_settings is None:
            async with get_db() as db:
                service = ContentService(db)
                self._world_settings = await service.get_all_world_settings(self.project_id)
        return self._world_settings

    def _detect_project_genre(self, settings: list[dict[str, Any]]) -> str | None:
        """Detect the project's genre from world setting content.

        Scans world setting names and content for genre-indicative keywords.
        Returns a genre label or None if undetermined.
        """
        combined_text = " ".join(
            s.get("name", "") + " " + s.get("content", "") + " " + s.get("summary", "") for s in settings
        ).lower()

        xianxia_score = sum(1 for kw in _XIANXIA_KEYWORDS if kw.lower() in combined_text)
        western_score = sum(1 for kw in _WESTERN_FANTASY_KEYWORDS if kw.lower() in combined_text)
        urban_score = sum(1 for kw in _URBAN_KEYWORDS if kw.lower() in combined_text)

        scores = [
            ("xianxia", xianxia_score),
            ("western_fantasy", western_score),
            ("urban", urban_score),
        ]
        scores.sort(key=lambda x: -x[1])

        if scores[0][1] > 0:
            return scores[0][0]
        return None

    def check_style_conflict(self, input_text: str) -> str | None:
        """Check if *input_text* conflicts with the project's detected genre.

        Args:
            input_text: The tool input parameter to check (e.g. a style description).

        Returns:
            A warning message if conflict is detected, or ``None`` if no conflict.
        """
        import asyncio

        try:
            settings = asyncio.run(self._load_world_settings())
        except RuntimeError:
            return None

        genre = self._detect_project_genre(settings)
        if not genre:
            return None

        input_lower = input_text.lower()

        # Check for conflicts
        if genre == "xianxia":
            conflicts = [kw for kw in _WESTERN_FANTASY_KEYWORDS | _URBAN_KEYWORDS if kw.lower() in input_lower]
            if conflicts:
                return (
                    f"⚠ Style conflict detected: project appears to be a xianxia/cultivation "
                    f"story, but the input contains western/urban elements ({', '.join(conflicts)}). "
                    f"Consider adapting the concept to fit the xianxia setting."
                )

        elif genre == "western_fantasy":
            conflicts = [kw for kw in _XIANXIA_KEYWORDS | _URBAN_KEYWORDS if kw.lower() in input_lower]
            if conflicts:
                return (
                    f"⚠ Style conflict detected: project appears to be a western fantasy "
                    f"story, but the input contains xianxia/urban elements ({', '.join(conflicts)}). "
                    f"Consider adapting the concept to fit the fantasy setting."
                )

        return None

    def check_entity_exists(self, entity_name: str, domain: str) -> str | None:
        """Check if an entity with *entity_name* already exists in the project.

        Args:
            entity_name: Name to check.
            domain: Domain to search in (world/character/outline/chapter).

        Returns:
            A warning if a similar name exists, or ``None``.
        """
        import asyncio

        settings = None
        try:
            settings = asyncio.run(self._load_world_settings())
        except RuntimeError:
            return None

        if not settings:
            return None

        names = [s.get("name", "").lower() for s in settings if s.get("name")]
        input_lower = entity_name.lower().strip()

        for existing_name in names:
            if existing_name == input_lower:
                return (
                    f"⚠ Entity '{entity_name}' already exists in project settings. "
                    "Consider using edit instead of create to avoid duplication."
                )

        return None


def validate_style(
    project_id: str,
    input_text: str,
    field_name: str = "content",
) -> str | None:
    """Synchronous helper to check style conflicts for use inside @tool functions.

    Args:
        project_id: The project ID.
        input_text: Tool input text to validate.
        field_name: Label for the field being validated.

    Returns:
        Warning message if conflict detected, or ``None``.
    """
    try:
        import asyncio

        async def _check() -> str | None:
            validator = ToolInputValidator(project_id)
            await validator._load_world_settings()
            return validator.check_style_conflict(input_text)

        return asyncio.run(_check())
    except Exception:
        return None
