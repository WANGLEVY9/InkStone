"""Project repository for CRUD and lifecycle operations.

Manages project records in SQLite, including cascading deletion of
related metadata and on-disk content directories.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import aiosqlite


async def create_project(
    db: aiosqlite.Connection,
    name: str,
    description: str | None = None,
    cover_image: str | None = None,
    word_count: int = 0,
) -> dict[str, Any]:
    """Create a new project with a unique ID and dedicated data path.

    Args:
        db: An active aiosqlite connection.
        name: Human-readable project name.
        description: Optional short description shown in project listings.
        cover_image: Optional URL/path to a cover image.
        word_count: Initial total word count for the project (defaults to 0).

    Returns:
        The newly created project row as a dictionary.
    """
    project_id = str(uuid.uuid4())
    data_path = str(Path("data") / project_id)

    await db.execute(
        """
        INSERT INTO projects (id, name, status, data_path, description, cover_image, word_count)
        VALUES (?, ?, 'active', ?, ?, ?, ?)
        """,
        (project_id, name, data_path, description, cover_image, word_count),
    )
    await db.commit()

    cursor = await db.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    row = await cursor.fetchone()
    assert row is not None
    return dict(row)


async def get_project(db: aiosqlite.Connection, project_id: str) -> dict[str, Any] | None:
    """Retrieve a project by its unique ID.

    Args:
        db: An active aiosqlite connection.
        project_id: The project UUID.

    Returns:
        The project row as a dictionary, or ``None`` if not found.
    """
    cursor = await db.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def update_project(db: aiosqlite.Connection, project_id: str, **kwargs: Any) -> dict[str, Any] | None:
    """Update mutable fields of an existing project.

    Only ``name``, ``status``, ``description``, ``cover_image``, and
    ``word_count`` are whitelisted to prevent accidental overwrites of
    internal columns.

    Args:
        db: An active aiosqlite connection.
        project_id: The project UUID to update.
        **kwargs: Key-value pairs for the fields to change.

    Returns:
        The updated project row, or ``None`` if the project does not exist.
    """
    project = await get_project(db, project_id)
    if not project:
        return None

    allowed = {"name", "status", "description", "cover_image", "word_count"}
    updates = []
    values = []
    for key, value in kwargs.items():
        if key in allowed:
            updates.append(f"{key} = ?")
            values.append(value)

    if not updates:
        return project

    values.append(project_id)
    await db.execute(f"UPDATE projects SET {', '.join(updates)} WHERE id = ?", values)
    await db.commit()
    return await get_project(db, project_id)


async def list_projects(db: aiosqlite.Connection, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
    """List projects ordered by creation time (newest first).

    Args:
        db: An active aiosqlite connection.
        limit: Maximum number of rows to return.
        offset: Number of rows to skip for pagination.

    Returns:
        A list of project dictionaries.
    """
    cursor = await db.execute(
        "SELECT * FROM projects ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (limit, offset),
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def delete_project(db: aiosqlite.Connection, project_id: str) -> bool:
    """Delete a project and all associated data.

    Performs cascading deletion across related tables and removes the
    project's on-disk content directory if it exists.

    Args:
        db: An active aiosqlite connection.
        project_id: The project UUID to delete.

    Returns:
        ``True`` if deletion completed successfully.
    """
    await db.execute("DELETE FROM chat_sessions WHERE project_id = ?", (project_id,))
    await db.execute("DELETE FROM chapters_meta WHERE project_id = ?", (project_id,))
    await db.execute("DELETE FROM outlines_meta WHERE project_id = ?", (project_id,))
    await db.execute("DELETE FROM characters_meta WHERE project_id = ?", (project_id,))
    await db.execute("DELETE FROM world_settings_meta WHERE project_id = ?", (project_id,))
    await db.execute("DELETE FROM reviews WHERE project_id = ?", (project_id,))
    await db.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    await db.commit()

    data_path = Path("data") / project_id
    if data_path.exists():
        import shutil

        shutil.rmtree(data_path)

    return True
