"""LLM service for creating configured client instances.

Provides a factory for LangChain-compatible LLM clients and helpers for
extracting plain text from various response formats.
"""

from __future__ import annotations

import os
from typing import Any

from langchain_anthropic import ChatAnthropic
from pydantic import SecretStr


def create_llm_client(
    provider: str | None = None,
    model: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
    streaming: bool = True,
    tags: list[str] | None = None,
) -> Any:
    """Create a configured LangChain LLM client.

    Falls back to environment variables for any omitted arguments.
    Currently only Anthropic is supported.

    Args:
        provider: LLM provider name (default: env ``LLM_PROVIDER`` or ``anthropic``).
        model: Model identifier (default: env ``LLM_MODEL`` or ``claude-sonnet-4-20250514``).
        base_url: Custom API base URL (default: env ``LLM_BASE_URL``).
        api_key: API key for authentication (default: env ``ANTHROPIC_API_KEY``).
        streaming: Whether to enable streaming mode.
        tags: Optional list of tags to attach to LLM invocations (visible in
            streaming metadata for filtering / source attribution).

    Returns:
        A LangChain chat model instance (e.g. ``ChatAnthropic``).

    Raises:
        ValueError: If ``api_key`` is empty or the provider is unsupported.
    """
    actual_provider = provider or os.getenv("LLM_PROVIDER", "anthropic")
    actual_model = model or os.getenv("LLM_MODEL", "claude-sonnet-4-20250514")
    actual_base_url = base_url or os.getenv("LLM_BASE_URL")
    actual_api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "").strip()

    if not actual_api_key:
        raise ValueError("ANTHROPIC_API_KEY is not set")

    if actual_provider == "anthropic":
        return ChatAnthropic(  # type: ignore[call-arg]
            model=actual_model,
            api_key=SecretStr(actual_api_key),
            base_url=actual_base_url,
            timeout=float(os.getenv("LLM_TIMEOUT", "86400.0")),
            max_retries=3,
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "65536")),
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
        # Handle list of content blocks - extract text from each.
        # Blocks may be plain strings or dicts with a "text" field.
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
