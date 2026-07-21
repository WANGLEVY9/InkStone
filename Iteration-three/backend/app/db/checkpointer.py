"""Global AsyncSqliteSaver checkpointer instance.

Provides a singleton AsyncSqliteSaver for LangGraph checkpointing.
The checkpointer is initialized during the FastAPI lifespan and shared
across the application for workflow-state persistence.
"""

from __future__ import annotations

from contextlib import AsyncExitStack

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

import app.db.connection as db_conn

_checkpointer: AsyncSqliteSaver | None = None
_exit_stack: AsyncExitStack | None = None


async def init_checkpointer() -> AsyncSqliteSaver:
    """Initialize the global checkpointer.

    Creates an ``AsyncSqliteSaver`` backed by the same SQLite file used by
    the application database and runs its setup routine. The resulting
    instance is cached as a singleton.

    Returns:
        The initialized ``AsyncSqliteSaver`` instance.

    Must be called within an async context.
    """
    global _checkpointer, _exit_stack
    if _checkpointer is not None:
        return _checkpointer

    _exit_stack = AsyncExitStack()
    cm = AsyncSqliteSaver.from_conn_string(str(db_conn.DATABASE_PATH))
    _checkpointer = await _exit_stack.enter_async_context(cm)
    await _checkpointer.setup()
    return _checkpointer


async def get_checkpointer() -> AsyncSqliteSaver:
    """Get the global checkpointer instance.

    Automatically initializes the checkpointer if it has not been created
    yet.

    Returns:
        The initialized ``AsyncSqliteSaver``.
    """
    global _checkpointer
    if _checkpointer is None:
        return await init_checkpointer()
    return _checkpointer


async def close_checkpointer() -> None:
    """Close the global checkpointer and release all resources.

    Idempotent: safe to call even if the checkpointer was never initialized.
    After closing, the singleton is reset so ``init_checkpointer`` can be
    called again if needed.
    """
    global _checkpointer, _exit_stack
    if _exit_stack is not None:
        await _exit_stack.aclose()
    _checkpointer = None
    _exit_stack = None
