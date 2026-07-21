"""Repository functions for the app_config key-value store."""

from __future__ import annotations

import aiosqlite

VALID_KEYS = {
    "llm_base_url",
    "anthropic_api_key",
    "langsmith_api_key",
    "langsmith_tracing",
    "langsmith_endpoint",
    "langsmith_project",
    "llm_model",
    "llm_max_tokens",
}

SENSITIVE_KEYS = {"anthropic_api_key", "langsmith_api_key"}

KEEP_SENTINEL = "__KEEP_EXISTING__"


def mask_value(key: str, value: str | None) -> str | None:
    """Mask sensitive config values for API responses."""
    if value is None or key not in SENSITIVE_KEYS:
        return value
    if len(value) < 8:
        return "***"
    return f"{value[:4]}...{value[-4:]}"


async def get_config(db: aiosqlite.Connection, key: str) -> str | None:
    """Read a single config value from the database."""
    async with db.execute("SELECT value FROM app_config WHERE key = ?", (key,)) as cursor:
        row = await cursor.fetchone()
        return row[0] if row else None


async def get_all_config(db: aiosqlite.Connection) -> dict[str, str | None]:
    """Read all config values. Returns dict keyed by config key."""
    result: dict[str, str | None] = {k: None for k in VALID_KEYS}
    async with db.execute("SELECT key, value FROM app_config") as cursor:
        async for row in cursor:
            if row[0] in VALID_KEYS:
                result[row[0]] = row[1]
    return result


async def update_config(db: aiosqlite.Connection, updates: dict[str, str | None]) -> None:
    """Batch upsert config values. None values are skipped."""
    for key, value in updates.items():
        if key not in VALID_KEYS:
            continue
        if value is None or value == KEEP_SENTINEL:
            continue
        await db.execute(
            "INSERT INTO app_config (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP",
            (key, value),
        )
    await db.commit()
