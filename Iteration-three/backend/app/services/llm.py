"""LLM service for creating configured client instances.

Provides a factory for LangChain-compatible LLM clients and helpers for
extracting plain text from various response formats. Config is read from
the database (app_config table) with fallback to environment variables.
"""

from __future__ import annotations

import os
from typing import Any

from langchain_anthropic import ChatAnthropic
from pydantic import SecretStr


def _read_config_from_db() -> dict[str, str | None]:
    """Read LLM config from the database synchronously.

    This is a synchronous helper that creates a new event loop if needed,
    since create_llm_client may be called from both sync and async contexts.
    """
    import asyncio

    import aiosqlite

    from app.db.connection import DATABASE_PATH

    async def _fetch() -> dict[str, str | None]:
        db = await aiosqlite.connect(DATABASE_PATH)
        db.row_factory = aiosqlite.Row
        try:
            result: dict[str, str | None] = {}
            for key in ("anthropic_api_key", "llm_model", "llm_base_url", "llm_max_tokens"):
                try:
                    async with db.execute("SELECT value FROM app_config WHERE key = ?", (key,)) as cur:
                        row = await cur.fetchone()
                        result[key] = row[0] if row else None
                except Exception:
                    # Table may not exist yet (e.g. before init_db runs)
                    result[key] = None
            return result
        finally:
            await db.close()

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # We're inside an async context -- use a thread to avoid nested loops
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, _fetch()).result()
    else:
        return asyncio.run(_fetch())


def create_llm_client(
    provider: str | None = None,
    model: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
    streaming: bool = True,
    tags: list[str] | None = None,
) -> Any:
    """Create a configured LangChain LLM client.

    Reads configuration from the database (app_config table). Falls back
    to environment variables if database values are not set.

    Args:
        provider: LLM provider name (default: env ``LLM_PROVIDER`` or ``anthropic``).
        model: Model identifier (default: from DB or env ``LLM_MODEL``).
        base_url: Custom API base URL (default: from DB or env ``LLM_BASE_URL``).
        api_key: API key for authentication (default: from DB or env ``ANTHROPIC_API_KEY``).
        streaming: Whether to enable streaming mode.
        tags: Optional list of tags to attach to LLM invocations.

    Returns:
        A LangChain chat model instance (e.g. ``ChatAnthropic``).

    Raises:
        ValueError: If ``api_key`` is empty or the provider is unsupported.
    """
    db_config = _read_config_from_db()

    actual_provider = provider or os.getenv("LLM_PROVIDER", "anthropic")
    actual_model = model or db_config.get("llm_model") or os.getenv("LLM_MODEL", "claude-sonnet-4-20250514")
    actual_base_url = base_url or db_config.get("llm_base_url") or os.getenv("LLM_BASE_URL")
    actual_api_key = api_key or db_config.get("anthropic_api_key") or os.getenv("ANTHROPIC_API_KEY", "").strip()
    max_tokens_str = db_config.get("llm_max_tokens") or os.getenv("LLM_MAX_TOKENS", "65536") or "65536"

    if not actual_api_key:
        raise ValueError("ANTHROPIC_API_KEY is not set")

    if actual_provider == "anthropic":
        return ChatAnthropic(  # type: ignore[call-arg]
            model=actual_model,
            api_key=SecretStr(actual_api_key),
            base_url=actual_base_url,
            timeout=float(os.getenv("LLM_TIMEOUT", "86400.0")),
            max_retries=3,
            max_tokens=int(max_tokens_str),
            tags=tags if tags else None,
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {actual_provider}")


def extract_content(response: Any) -> str:
    """Extract plain text from an LLM response.

    Handles multiple content shapes: raw strings, lists of strings, and
    LangChain-style dict blocks with ``type`` / ``text`` keys.

    Args:
        response: An LLM response object exposing a ``content`` attribute.

    Returns:
        Concatenated text extracted from the response.
    """
    content = response.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
                elif "text" in block:
                    parts.append(str(block["text"]))
        return "\n".join(parts)
    return str(content)
