"""Foreshadowing domain service.

Encapsulates CRUD and query operations for foreshadowing entries
with JSON serialization helpers for list fields.
"""

from __future__ import annotations

import json
import uuid
from typing import Any, cast

import aiosqlite


class ForeshadowingService:
    """Service for foreshadowing management."""

    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    @staticmethod
    def _serialize_list(data: list[str]) -> str:
        return json.dumps(data)

    @staticmethod
    def _deserialize_list(value: str | None) -> list[str]:
        if not value:
            return []
        return cast(list[str], json.loads(value))

    async def create(
        self,
        project_id: str,
        description: str,
        foreshadowed_at: str = "",
        expected_resolve_at: str = "",
        target_chapter_id: str = "",
        related_entities: list[str] | None = None,
        notes: str = "",
    ) -> dict[str, Any]:
        """Create a new foreshadowing entry.

        Args:
            project_id: Project identifier.
            description: Description of the foreshadowing.
            foreshadowed_at: Where/when this was foreshadowed (chapter reference).
            expected_resolve_at: Expected resolution point.
            target_chapter_id: Associated chapter ID.
            related_entities: List of related entity IDs.
            notes: Additional notes.

        Returns:
            The created foreshadowing dict.
        """
        entry_id = str(uuid.uuid4())
        entities_json = self._serialize_list(related_entities or [])
        await self.db.execute(
            """
            INSERT INTO foreshadowing
                (id, project_id, description, foreshadowed_at, expected_resolve_at,
                 status, target_chapter_id, related_entities, notes)
            VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, ?)
            """,
            (
                entry_id,
                project_id,
                description,
                foreshadowed_at,
                expected_resolve_at,
                target_chapter_id,
                entities_json,
                notes,
            ),
        )
        await self.db.commit()
        entry = await self.get(entry_id, project_id)
        if entry is None:
            raise RuntimeError(f"Failed to retrieve foreshadowing entry {entry_id}")
        return entry

    async def get(self, entry_id: str, project_id: str) -> dict[str, Any] | None:
        """Get a foreshadowing entry by ID."""
        cursor = await self.db.execute(
            "SELECT * FROM foreshadowing WHERE id = ? AND project_id = ?",
            (entry_id, project_id),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return self._deserialize_row(row)

    def _deserialize_row(self, row: aiosqlite.Row) -> dict[str, Any]:
        result: dict[str, Any] = dict(row)
        result["related_entities"] = self._deserialize_list(result.get("related_entities"))
        return result

    async def list_by_project(
        self,
        project_id: str,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        """List foreshadowing entries for a project, optionally filtered by status."""
        if status:
            cursor = await self.db.execute(
                "SELECT * FROM foreshadowing WHERE project_id = ? AND status = ? ORDER BY created_at DESC",
                (project_id, status),
            )
        else:
            cursor = await self.db.execute(
                "SELECT * FROM foreshadowing WHERE project_id = ? ORDER BY created_at DESC",
                (project_id,),
            )
        rows = await cursor.fetchall()
        return [self._deserialize_row(r) for r in rows]

    async def update(
        self,
        entry_id: str,
        project_id: str,
        **kwargs: Any,
    ) -> dict[str, Any] | None:
        """Update a foreshadowing entry.

        Allowed fields: description, foreshadowed_at, expected_resolve_at,
        status, target_chapter_id, notes.
        """
        allowed = {
            "description": "description = ?",
            "foreshadowed_at": "foreshadowed_at = ?",
            "expected_resolve_at": "expected_resolve_at = ?",
            "status": "status = ?",
            "target_chapter_id": "target_chapter_id = ?",
            "notes": "notes = ?",
        }
        updates: list[str] = []
        values: list[Any] = []
        for key, value in kwargs.items():
            if key in allowed:
                updates.append(allowed[key])
                values.append(value)

        if not updates:
            return await self.get(entry_id, project_id)

        values.extend([entry_id, project_id])
        update_sql = (
            f"UPDATE foreshadowing SET {', '.join(updates)}, "
            "updated_at = CURRENT_TIMESTAMP WHERE id = ? AND project_id = ?"
        )
        await self.db.execute(
            update_sql,
            values,
        )
        await self.db.commit()
        return await self.get(entry_id, project_id)

    async def delete(self, entry_id: str, project_id: str) -> bool:
        """Delete a foreshadowing entry."""
        cursor = await self.db.execute(
            "DELETE FROM foreshadowing WHERE id = ? AND project_id = ?",
            (entry_id, project_id),
        )
        await self.db.commit()
        return cursor.rowcount > 0

    async def resolve(self, entry_id: str, project_id: str) -> dict[str, Any] | None:
        """Mark a foreshadowing entry as resolved."""
        return await self.update(entry_id, project_id, status="resolved")

    async def get_unresolved(self, project_id: str) -> list[dict[str, Any]]:
        """Get all unresolved (pending or active) foreshadowing entries."""
        cursor = await self.db.execute(
            """
            SELECT * FROM foreshadowing
            WHERE project_id = ? AND status IN ('pending', 'active')
            ORDER BY created_at DESC
            """,
            (project_id,),
        )
        rows = await cursor.fetchall()
        return [self._deserialize_row(r) for r in rows]

    async def search(self, project_id: str, query: str) -> list[dict[str, Any]]:
        """Search foreshadowing entries by description."""
        cursor = await self.db.execute(
            "SELECT * FROM foreshadowing WHERE project_id = ? AND description LIKE ? ORDER BY created_at DESC",
            (project_id, f"%{query}%"),
        )
        rows = await cursor.fetchall()
        return [self._deserialize_row(r) for r in rows]
