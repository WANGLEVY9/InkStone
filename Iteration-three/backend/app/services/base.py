"""Base service providing shared utilities for content domain services.

All domain-specific services inherit from ``BaseContentService`` to gain
database connection, storage backend, and common helpers.
"""

from __future__ import annotations

from typing import Any

import aiosqlite

from app.services.storage import ContentStorage, FileSystemStorage


class BaseContentService:
    """Shared infrastructure for content services.

    Attributes:
        db: An aiosqlite connection for metadata queries.
        storage: File storage backend.
    """

    def __init__(self, db: aiosqlite.Connection, storage: ContentStorage | None = None):
        """Initialize the service with a database connection and optional storage backend.

        Args:
            db: An aiosqlite connection for metadata queries.
            storage: File storage backend; defaults to FileSystemStorage.
        """
        self.db = db
        self.storage = storage or FileSystemStorage()

    async def _update_metadata(
        self,
        table: str,
        allowed_fields: dict[str, str],
        entity_id: str,
        project_id: str,
        **kwargs: Any,
    ) -> bool:
        """Build and execute a filtered UPDATE statement for metadata tables.

        Only keys present in *allowed_fields* are used, preventing accidental
        SQL injection via arbitrary kwargs.

        Args:
            table: Target table name (e.g. ``world_settings_meta``).
            allowed_fields: Mapping ``field_name -> "column = ?"`` for allowed updates.
            entity_id: Primary key of the row to update.
            project_id: Project identifier for the row.
            **kwargs: Optional metadata fields to update.

        Returns:
            ``True`` if at least one column was updated, ``False`` otherwise.
        """
        if not kwargs:
            return False

        updates: list[str] = []
        values: list[Any] = []
        for key, value in kwargs.items():
            if key in allowed_fields:
                updates.append(allowed_fields[key])
                values.append(value)

        if not updates:
            return False

        values.extend([entity_id, project_id])
        sql = f"UPDATE {table} SET {', '.join(updates)} WHERE id = ? AND project_id = ?"
        await self.db.execute(sql, values)
        await self.db.commit()
        return True
