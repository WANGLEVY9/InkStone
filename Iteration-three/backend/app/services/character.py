"""Character domain service.

Encapsulates CRUD and search operations for characters.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.services.base import BaseContentService

ALLOWED_CHARACTER_UPDATE: dict[str, str] = {
    "name": "name = ?",
    "summary": "summary = ?",
}


class CharacterService(BaseContentService):
    """Service for character metadata and content."""

    async def create(
        self,
        project_id: str,
        character_id: str,
        name: str,
        content: str,
        summary: str = "",
    ) -> dict[str, Any]:
        """Create a character: insert metadata and write content file.

        Args:
            project_id: Identifier of the owning project.
            character_id: Unique identifier for the character.
            name: Display name of the character.
            content: Full Markdown content.
            summary: Optional short summary.

        Returns:
            A dictionary containing the created metadata.
        """
        file_path = Path(project_id) / "characters" / f"{character_id}.md"
        await self.storage.write(file_path, content)

        await self.db.execute(
            """
            INSERT INTO characters_meta (id, project_id, name, file_path, summary)
            VALUES (?, ?, ?, ?, ?)
            """,
            (character_id, project_id, name, str(file_path), summary),
        )
        await self.db.commit()

        return {
            "id": character_id,
            "project_id": project_id,
            "name": name,
            "file_path": str(file_path),
        }

    async def get(self, character_id: str, project_id: str) -> dict[str, Any] | None:
        """Retrieve a character by ID, merging metadata with Markdown content.

        Args:
            character_id: Unique identifier of the character.
            project_id: Identifier of the owning project.

        Returns:
            A dictionary with metadata and content, or None if not found.
        """
        cursor = await self.db.execute(
            "SELECT * FROM characters_meta WHERE id = ? AND project_id = ?",
            (character_id, project_id),
        )
        row = await cursor.fetchone()
        if not row:
            return None

        content = await self.storage.read(Path(row["file_path"]))
        return {**dict(row), "content": content}

    async def update(
        self,
        character_id: str,
        project_id: str,
        content: str,
        **kwargs: str | None,
    ) -> dict[str, Any] | None:
        """Update a character's Markdown content and optionally its metadata.

        Args:
            character_id: Unique identifier of the character.
            project_id: Identifier of the owning project.
            content: New Markdown content.
            **kwargs: Optional metadata fields to update (e.g., name, summary).

        Returns:
            The updated character dictionary, or None if not found.
        """
        cursor = await self.db.execute(
            "SELECT * FROM characters_meta WHERE id = ? AND project_id = ?",
            (character_id, project_id),
        )
        row = await cursor.fetchone()
        if not row:
            return None

        await self.storage.write(Path(row["file_path"]), content)
        await self._update_metadata(
            "characters_meta",
            ALLOWED_CHARACTER_UPDATE,
            character_id,
            project_id,
            **kwargs,
        )

        result = dict(row)
        result.update({k: v for k, v in kwargs.items() if k in ALLOWED_CHARACTER_UPDATE and v is not None})
        result["content"] = content
        return result

    async def delete(self, character_id: str, project_id: str) -> bool:
        """Delete a character and its content file.

        Args:
            character_id: Unique identifier of the character.
            project_id: Identifier of the owning project.

        Returns:
            True if the entity existed and was deleted, False otherwise.
        """
        cursor = await self.db.execute(
            "SELECT file_path FROM characters_meta WHERE id = ? AND project_id = ?",
            (character_id, project_id),
        )
        row = await cursor.fetchone()
        if not row:
            return False

        await self.db.execute(
            "DELETE FROM characters_meta WHERE id = ? AND project_id = ?",
            (character_id, project_id),
        )
        await self.db.commit()
        await self.storage.delete(Path(row["file_path"]))
        return True

    async def search(self, project_id: str, query: str) -> list[dict[str, Any]]:
        """Search characters by name or summary using a LIKE query.

        Args:
            project_id: Identifier of the owning project.
            query: Search string to match against name and summary.

        Returns:
            A list of matching metadata dictionaries.
        """
        cursor = await self.db.execute(
            """
            SELECT * FROM characters_meta
            WHERE project_id = ? AND (name LIKE ? OR summary LIKE ?)
            """,
            (project_id, f"%{query}%", f"%{query}%"),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def list_all(self, project_id: str) -> list[dict[str, Any]]:
        """List all character metadata for a project, excluding Markdown content.

        Args:
            project_id: Identifier of the owning project.

        Returns:
            A list of metadata dictionaries.
        """
        cursor = await self.db.execute(
            """
            SELECT id, project_id, name, summary, created_at, updated_at
            FROM characters_meta WHERE project_id = ?
            """,
            (project_id,),
        )
        return [dict(row) for row in await cursor.fetchall()]
