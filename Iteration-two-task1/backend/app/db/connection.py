"""Database connection utilities for aiosqlite.

Provides helpers to initialize the SQLite schema and obtain
connections (plain or transactional) with automatic cleanup.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import aiofiles
import aiosqlite

DATABASE_PATH = Path(__file__).parent.parent.parent / "novel.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"

# Module-level global connection and lock for safe concurrent access.
_db_connection: aiosqlite.Connection | None = None
_db_lock = asyncio.Lock()


async def _get_global_db() -> aiosqlite.Connection:
    """Return the singleton aiosqlite connection, creating it if necessary.

    The connection is opened lazily on first call and reused for the
    lifetime of the process.  ``row_factory`` is set to ``aiosqlite.Row``.
    """
    global _db_connection  # noqa: PLW0603

    if _db_connection is None:
        async with _db_lock:
            if _db_connection is None:
                _db_connection = await aiosqlite.connect(DATABASE_PATH)
                _db_connection.row_factory = aiosqlite.Row
                # Enable WAL mode for concurrent read/write access
                await _db_connection.execute("PRAGMA journal_mode=WAL")
                # Wait up to 30 seconds for locks to be released
                await _db_connection.execute("PRAGMA busy_timeout=30000")
    return _db_connection


async def init_db() -> None:
    """Initialize the database by executing the schema script.

    Creates tables and indices defined in ``schema.sql`` if they do not
    already exist. The global connection is reused when available.
    """
    async with aiofiles.open(SCHEMA_PATH, encoding="utf-8") as f:
        schema = await f.read()

    db = await _get_global_db()
    await db.executescript(schema)
    await db.commit()


@asynccontextmanager
async def get_db() -> AsyncGenerator[aiosqlite.Connection]:
    """Yield the shared aiosqlite connection.

    Yields:
        An open ``aiosqlite.Connection`` configured with ``Row`` factory.

    The connection is *not* closed when the context manager exits; it is
    reused across callers.  Callers must not close it themselves.
    """
    db = await _get_global_db()
    original_factory = db.row_factory
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        db.row_factory = original_factory


@asynccontextmanager
async def get_transaction() -> AsyncGenerator[aiosqlite.Connection]:
    """Yield the shared aiosqlite connection inside an explicit transaction.

    Yields:
        An open ``aiosqlite.Connection`` with ``BEGIN`` already issued.

    On normal exit the transaction is committed; on exception it is rolled
    back and the exception is re-raised.  The underlying connection is kept
    open for reuse.
    """
    db = await _get_global_db()
    original_factory = db.row_factory
    db.row_factory = aiosqlite.Row
    try:
        await db.execute("BEGIN")
        yield db
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    finally:
        db.row_factory = original_factory
