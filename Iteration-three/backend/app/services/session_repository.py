"""Session repository for chat session lifecycle and project binding.

Provides CRUD operations for chat sessions and utilities to verify
that a session belongs to a specific project.
"""

from __future__ import annotations

import uuid
from typing import Any

import aiosqlite


async def create_session(
    db: aiosqlite.Connection,
    project_id: str,
    title: str | None = None,
) -> dict[str, Any]:
    """Create a new chat session linked to a project.

    Args:
        db: An active aiosqlite connection.
        project_id: The project UUID to associate with the session.
        title: Optional human-readable title for the session.

    Returns:
        The newly created session row as a dictionary.
    """
    session_id = str(uuid.uuid4())

    await db.execute(
        """
        INSERT INTO chat_sessions (id, project_id, title)
        VALUES (?, ?, ?)
        """,
        (session_id, project_id, title),
    )
    await db.commit()

    cursor = await db.execute("SELECT * FROM chat_sessions WHERE id = ?", (session_id,))
    row = await cursor.fetchone()
    assert row is not None
    return dict(row)


async def get_session(db: aiosqlite.Connection, session_id: str) -> dict[str, Any] | None:
    """Retrieve a session by its unique ID.

    Args:
        db: An active aiosqlite connection.
        session_id: The session UUID.

    Returns:
        The session row as a dictionary, or ``None`` if not found.
    """
    cursor = await db.execute("SELECT * FROM chat_sessions WHERE id = ?", (session_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def verify_project_binding(db: aiosqlite.Connection, session_id: str, project_id: str) -> bool:
    """Check whether a session belongs to the given project.

    Args:
        db: An active aiosqlite connection.
        session_id: The session UUID.
        project_id: The project UUID.

    Returns:
        ``True`` if the session is bound to the project, otherwise ``False``.
    """
    cursor = await db.execute(
        "SELECT 1 FROM chat_sessions WHERE id = ? AND project_id = ?",
        (session_id, project_id),
    )
    row = await cursor.fetchone()
    return row is not None


async def list_sessions_by_project(
    db: aiosqlite.Connection, project_id: str, limit: int = 50, offset: int = 0
) -> list[dict[str, Any]]:
    """List sessions for a project ordered by most recent activity.

    Args:
        db: An active aiosqlite connection.
        project_id: The project UUID.
        limit: Maximum number of rows to return.
        offset: Number of rows to skip for pagination.

    Returns:
        A list of session dictionaries.
    """
    cursor = await db.execute(
        """
        SELECT * FROM chat_sessions
        WHERE project_id = ?
        ORDER BY last_active_at DESC
        LIMIT ? OFFSET ?
        """,
        (project_id, limit, offset),
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def update_session_activity(db: aiosqlite.Connection, session_id: str) -> None:
    """Bump the ``last_active_at`` timestamp for a session.

    Args:
        db: An active aiosqlite connection.
        session_id: The session UUID to update.
    """
    await db.execute(
        "UPDATE chat_sessions SET last_active_at = CURRENT_TIMESTAMP WHERE id = ?",
        (session_id,),
    )
    await db.commit()


async def update_session_title(db: aiosqlite.Connection, session_id: str, title: str | None) -> dict[str, Any] | None:
    """Update the title of a session.

    Args:
        db: An active aiosqlite connection.
        session_id: The session UUID to update.
        title: The new title (may be ``None`` to clear it).

    Returns:
        The updated session row as a dictionary, or ``None`` if not found.
    """
    await db.execute(
        "UPDATE chat_sessions SET title = ? WHERE id = ?",
        (title, session_id),
    )
    await db.commit()
    return await get_session(db, session_id)


async def delete_session(db: aiosqlite.Connection, session_id: str) -> bool:
    """Remove a session from the database.

    Args:
        db: An active aiosqlite connection.
        session_id: The session UUID to delete.

    Returns:
        ``True`` if deletion completed successfully.
    """
    await db.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
    await db.commit()
    return True
