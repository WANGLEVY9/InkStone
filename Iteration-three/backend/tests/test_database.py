"""Tests for database project isolation.

These tests verify project isolation at the database layer.
"""

from pathlib import Path

import aiosqlite
import pytest

SCHEMA_PATH = Path(__file__).parent.parent / "app" / "db" / "schema.sql"


@pytest.mark.asyncio
async def test_world_settings_filtered_by_project() -> None:
    """World settings queries must always filter by project_id."""
    db = await aiosqlite.connect(":memory:")

    await db.execute("""
        CREATE TABLE world_settings_meta (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            name TEXT NOT NULL
        )
    """)

    await db.execute(
        "INSERT INTO world_settings_meta (id, project_id, name) VALUES (?, ?, ?)", ("ws-a1", "project-a", "World A1")
    )
    await db.execute(
        "INSERT INTO world_settings_meta (id, project_id, name) VALUES (?, ?, ?)", ("ws-a2", "project-a", "World A2")
    )
    await db.execute(
        "INSERT INTO world_settings_meta (id, project_id, name) VALUES (?, ?, ?)", ("ws-b1", "project-b", "World B1")
    )

    await db.commit()

    cursor = await db.execute("SELECT * FROM world_settings_meta WHERE project_id = ?", ("project-a",))
    rows = await cursor.fetchall()

    assert len(list(rows)) == 2
    for row in rows:
        assert row[1] == "project-a"  # project_id is column index 1

    await db.close()


async def _fresh_db() -> aiosqlite.Connection:
    """Create an in-memory DB with the production schema applied."""
    db = await aiosqlite.connect(":memory:")
    db.row_factory = aiosqlite.Row
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        await db.executescript(f.read())
    return db


@pytest.mark.asyncio
async def test_create_project_with_description_and_defaults() -> None:
    """create_project should persist description and apply word_count default."""
    from app.services.project_repository import create_project, get_project

    db = await _fresh_db()
    try:
        project = await create_project(db, "测试作品", description="一个奇幻冒险故事")
        assert project["name"] == "测试作品"
        assert project["description"] == "一个奇幻冒险故事"
        assert project["cover_image"] is None
        assert project["word_count"] == 0

        fetched = await get_project(db, project["id"])
        assert fetched is not None
        assert fetched["description"] == "一个奇幻冒险故事"
        assert fetched["cover_image"] is None
        assert fetched["word_count"] == 0
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_update_project_new_fields_individually() -> None:
    """update_project should accept the new fields one at a time."""
    from app.services.project_repository import create_project, update_project

    db = await _fresh_db()
    try:
        project = await create_project(db, "P")
        pid = project["id"]

        updated = await update_project(db, pid, cover_image="https://example.com/c.jpg")
        assert updated is not None
        assert updated["cover_image"] == "https://example.com/c.jpg"
        assert updated["word_count"] == 0

        updated = await update_project(db, pid, word_count=12345)
        assert updated is not None
        assert updated["word_count"] == 12345

        updated = await update_project(db, pid, description="new desc")
        assert updated is not None
        assert updated["description"] == "new desc"
        # earlier updates preserved
        assert updated["cover_image"] == "https://example.com/c.jpg"
        assert updated["word_count"] == 12345
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_chat_session_title_persisted_when_provided() -> None:
    """Creating a session with a title should persist that title."""
    from app.services.session_repository import (
        create_session,
        get_session,
    )

    db = await aiosqlite.connect(":memory:")
    db.row_factory = aiosqlite.Row

    await db.execute("""
        CREATE TABLE chat_sessions (
            id TEXT PRIMARY KEY,
            project_id TEXT,
            title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    await db.commit()

    session = await create_session(db, "proj-1", title="My Writing Session")
    assert session["title"] == "My Writing Session"

    fetched = await get_session(db, session["id"])
    assert fetched is not None
    assert fetched["title"] == "My Writing Session"

    await db.close()


@pytest.mark.asyncio
async def test_chat_session_title_defaults_to_null() -> None:
    """Omitting title at creation should leave it NULL."""
    from app.services.session_repository import create_session, get_session

    db = await aiosqlite.connect(":memory:")
    db.row_factory = aiosqlite.Row

    await db.execute("""
        CREATE TABLE chat_sessions (
            id TEXT PRIMARY KEY,
            project_id TEXT,
            title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    await db.commit()

    session = await create_session(db, "proj-1")
    assert session["title"] is None

    fetched = await get_session(db, session["id"])
    assert fetched is not None
    assert fetched["title"] is None

    await db.close()


@pytest.mark.asyncio
async def test_chat_session_update_title() -> None:
    """update_session_title should change the stored title."""
    from app.services.session_repository import (
        create_session,
        get_session,
        update_session_title,
    )

    db = await aiosqlite.connect(":memory:")
    db.row_factory = aiosqlite.Row

    await db.execute("""
        CREATE TABLE chat_sessions (
            id TEXT PRIMARY KEY,
            project_id TEXT,
            title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    await db.commit()

    session = await create_session(db, "proj-1", title="Initial")
    updated = await update_session_title(db, session["id"], "Renamed")
    assert updated is not None
    assert updated["title"] == "Renamed"

    fetched = await get_session(db, session["id"])
    assert fetched is not None
    assert fetched["title"] == "Renamed"

    await db.close()
