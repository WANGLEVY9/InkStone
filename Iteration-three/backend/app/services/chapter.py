"""Chapter domain service.

Encapsulates CRUD and listing operations for chapters.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.services.base import BaseContentService

ALLOWED_CHAPTER_UPDATE: dict[str, str] = {
    "title": "title = ?",
    "word_count": "word_count = ?",
    "status": "status = ?",
    "chapter_number": "chapter_number = ?",
    "summary": "summary = ?",
    "published_at": "published_at = ?",
}


class ChapterMetadata(BaseModel):
    """Optional metadata fields for chapter creation / update.

    Attributes:
        chapter_number: Ordinal chapter number.
        summary: Short summary of the chapter.
        published_at: ISO-format publication timestamp.
    """

    chapter_number: int | None = Field(default=None)
    summary: str | None = Field(default=None)
    published_at: str | None = Field(default=None)


class ChapterService(BaseContentService):
    """Service for chapter metadata and content."""

    async def create(
        self,
        project_id: str,
        chapter_id: str,
        title: str,
        content: str,
        word_count: int = 0,
        chapter_number: int | None = None,
        summary: str | None = None,
        published_at: str | None = None,
    ) -> dict[str, Any]:
        """Create a chapter: insert metadata and write content file.

        Args:
            project_id: Identifier of the owning project.
            chapter_id: Unique identifier for the chapter.
            title: Display title of the chapter.
            content: Full Markdown content.
            word_count: Estimated word count (overridden by server-side calculation).
            chapter_number: Optional ordinal chapter number.
            summary: Optional short summary.
            published_at: Optional ISO-format publication timestamp.

        Returns:
            A dictionary containing the created metadata.
        """
        computed_word_count = len(content.split())
        # If client provides a word_count, use it as a validation hint but prefer computed
        if word_count and word_count != computed_word_count:
            # Allow override if explicitly provided and different
            final_word_count = word_count
        else:
            final_word_count = computed_word_count

        file_path = Path(project_id) / "chapters" / f"{chapter_id}.md"
        await self.storage.write(file_path, content)

        await self.db.execute(
            """
            INSERT INTO chapters_meta
                (id, project_id, title, file_path, word_count,
                 chapter_number, summary, published_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                chapter_id,
                project_id,
                title,
                str(file_path),
                final_word_count,
                chapter_number if chapter_number is not None else 1,
                summary,
                published_at,
            ),
        )
        await self.db.commit()

        return {
            "id": chapter_id,
            "project_id": project_id,
            "title": title,
            "file_path": str(file_path),
            "word_count": final_word_count,
            "chapter_number": chapter_number if chapter_number is not None else 1,
            "summary": summary,
            "published_at": published_at,
        }

    async def get(self, chapter_id: str, project_id: str) -> dict[str, Any] | None:
        """Retrieve a chapter by ID, merging metadata with Markdown content.

        Args:
            chapter_id: Unique identifier of the chapter.
            project_id: Identifier of the owning project.

        Returns:
            A dictionary with metadata and content, or None if not found.
        """
        cursor = await self.db.execute(
            "SELECT * FROM chapters_meta WHERE id = ? AND project_id = ?",
            (chapter_id, project_id),
        )
        row = await cursor.fetchone()
        if not row:
            return None

        content = await self.storage.read(Path(row["file_path"]))
        return {**dict(row), "content": content}

    async def update(
        self,
        chapter_id: str,
        project_id: str,
        content: str,
        **kwargs: str | int | None,
    ) -> dict[str, Any] | None:
        """Update a chapter's Markdown content and optionally its metadata.

        Args:
            chapter_id: Unique identifier of the chapter.
            project_id: Identifier of the owning project.
            content: New Markdown content.
            **kwargs: Optional metadata fields to update.

        Returns:
            The updated chapter dictionary, or None if not found.
        """
        cursor = await self.db.execute(
            "SELECT * FROM chapters_meta WHERE id = ? AND project_id = ?",
            (chapter_id, project_id),
        )
        row = await cursor.fetchone()
        if not row:
            return None

        await self.storage.write(Path(row["file_path"]), content)

        # Recompute word_count from new content unless explicitly overridden
        if "word_count" not in kwargs:
            kwargs = dict(kwargs)
            kwargs["word_count"] = len(content.split())

        await self._update_metadata(
            "chapters_meta",
            ALLOWED_CHAPTER_UPDATE,
            chapter_id,
            project_id,
            **kwargs,
        )

        result = dict(row)
        result.update({k: v for k, v in kwargs.items() if k in ALLOWED_CHAPTER_UPDATE and v is not None})
        result["content"] = content
        return result

    async def delete(self, chapter_id: str, project_id: str) -> bool:
        """Delete a chapter and its content file.

        Args:
            chapter_id: Unique identifier of the chapter.
            project_id: Identifier of the owning project.

        Returns:
            True if the entity existed and was deleted, False otherwise.
        """
        cursor = await self.db.execute(
            "SELECT file_path FROM chapters_meta WHERE id = ? AND project_id = ?",
            (chapter_id, project_id),
        )
        row = await cursor.fetchone()
        if not row:
            return False

        await self.db.execute(
            "DELETE FROM chapters_meta WHERE id = ? AND project_id = ?",
            (chapter_id, project_id),
        )
        await self.db.commit()
        await self.storage.delete(Path(row["file_path"]))
        return True

    async def list_all(self, project_id: str) -> list[dict[str, Any]]:
        """List all chapter metadata for a project, excluding Markdown content.

        Args:
            project_id: Identifier of the owning project.

        Returns:
            A list of metadata dictionaries.
        """
        cursor = await self.db.execute(
            """
            SELECT id, project_id, title, word_count, status,
                   chapter_number, summary, published_at, created_at, updated_at
            FROM chapters_meta WHERE project_id = ?
            """,
            (project_id,),
        )
        return [dict(row) for row in await cursor.fetchall()]

    async def search(self, project_id: str, query: str) -> list[dict[str, Any]]:
        """Search chapters by title or summary using a LIKE query.

        Args:
            project_id: Identifier of the owning project.
            query: Search term to match against chapter title or summary.

        Returns:
            A list of matching metadata dictionaries.
        """
        cursor = await self.db.execute(
            "SELECT * FROM chapters_meta WHERE project_id = ? AND (title LIKE ? OR summary LIKE ?)",
            (project_id, f"%{query}%", f"%{query}%"),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
