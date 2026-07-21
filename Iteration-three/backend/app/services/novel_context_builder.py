"""Novel-specific context builder for chat sessions.

Extends the generic compression strategy with novel-specific context:
- Full text of the last 2 chapters
- All unresolved foreshadowing entries
- Protagonist current state summary

This context is injected as a SystemMessage at the start of each
chat turn, giving the agent a rich understanding of the current
narrative state.
"""

from __future__ import annotations

from typing import Any

import aiosqlite

from app.services.content import ContentService

# Keywords in character name/summary that indicate a protagonist role
_PROTAGONIST_KEYWORDS = {"主角", "protagonist", "main character", "主人公", "主角人物"}


def _is_protagonist(name: str, summary: str) -> bool:
    """Check if a character is likely the protagonist based on name or summary."""
    lower_name = name.lower()
    lower_summary = summary.lower() if summary else ""
    for keyword in _PROTAGONIST_KEYWORDS:
        if keyword.lower() in lower_name or keyword.lower() in lower_summary:
            return True
    return False


class NovelContextBuilder:
    """Builds novel-specific context for AI chat sessions.

    Collects the last 2 chapters' full text, unresolved foreshadowing,
    and protagonist state to provide narrative continuity beyond what
    generic message compression can capture.
    """

    def __init__(self, db: aiosqlite.Connection):
        self.db = db
        self._content_service: ContentService | None = None

    @property
    def content(self) -> ContentService:
        if self._content_service is None:
            self._content_service = ContentService(self.db)
        return self._content_service

    async def build_context(
        self,
        project_id: str,
        characters: list[dict[str, Any]],
        chapters_meta: list[dict[str, Any]],
    ) -> str:
        """Build a novel-specific context string.

        Args:
            project_id: The project to build context for.
            characters: List of character metadata dicts (from project_context).
            chapters_meta: List of chapter metadata dicts (from project_context).

        Returns:
            A formatted context string, or empty string if no novel data exists.
        """
        parts: list[str] = []

        # 1. Last 2 chapters full text
        last_chapters_text = await self._get_last_chapters_text(project_id, chapters_meta)
        if last_chapters_text:
            parts.append("【最近章节正文】\n" + last_chapters_text)

        # 2. Unresolved foreshadowing
        foreshadowing_text = await self._get_foreshadowing_text(project_id)
        if foreshadowing_text:
            parts.append("【未回收伏笔】\n" + foreshadowing_text)

        # 3. Protagonist state
        protagonist_text = await self._get_protagonist_text(project_id, characters)
        if protagonist_text:
            parts.append("【主角状态】\n" + protagonist_text)

        if not parts:
            return ""

        return "\n\n".join(parts)

    async def _get_last_chapters_text(
        self,
        project_id: str,
        chapters_meta: list[dict[str, Any]],
    ) -> str:
        """Get the full text of the last 2 chapters."""
        if not chapters_meta:
            return ""

        # Sort by chapter_number descending, take last 2
        sorted_chapters = sorted(
            chapters_meta,
            key=lambda c: c.get("chapter_number") or 0,
            reverse=True,
        )
        recent = sorted_chapters[:2]

        chapter_texts: list[str] = []
        for ch in reversed(recent):  # chronological order
            chapter_id = ch["id"]
            full = await self.content.get_chapter(chapter_id, project_id)
            if full and full.get("content"):
                title = full.get("title", "Untitled")
                content = full["content"]
                # Truncate very long chapters (beyond 4000 chars) to stay within context
                if len(content) > 4000:
                    content = content[:4000] + "\n\n...(截断)"
                chapter_texts.append(f"### 第{ch.get('chapter_number', '?')}章：{title}\n{content}")

        return "\n\n".join(chapter_texts) if chapter_texts else ""

    async def _get_foreshadowing_text(self, project_id: str) -> str:
        """Get formatted unresolved foreshadowing entries."""
        entries = await self.content.get_unresolved_foreshadowing(project_id)
        if not entries:
            return ""

        lines: list[str] = []
        for entry in entries:
            desc = entry.get("description", "").strip()
            if desc:
                status_icon = "⏳" if entry.get("status") == "pending" else "🔍"
                lines.append(f"- {status_icon} {desc}")
                # Include notes if available
                notes = entry.get("notes", "").strip()
                if notes:
                    lines.append(f"  └ {notes[:100]}")

        return "\n".join(lines) if lines else ""

    async def _get_protagonist_text(
        self,
        project_id: str,
        characters: list[dict[str, Any]],
    ) -> str:
        """Get protagonist state summary from character data."""
        if not characters:
            return ""

        # Identify protagonist(s)
        protagonists = [c for c in characters if _is_protagonist(c.get("name", ""), c.get("summary", ""))]

        # If no explicit protagonist, take the first character as presumed
        if not protagonists and characters:
            protagonists = [characters[0]]

        lines: list[str] = []
        for protag in protagonists:
            name = protag.get("name", "Unknown")
            summary = protag.get("summary", "")
            lines.append(f"- {name}: {summary[:200] if summary else '（无摘要）'}" if summary else f"- {name}")

        return "\n".join(lines) if lines else ""
