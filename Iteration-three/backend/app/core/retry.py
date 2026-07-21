"""Retry utilities with exponential backoff for LLM calls.

Provides a configurable retry mechanism with exponential backoff
and optional jitter to prevent thundering herd problems.
"""

from __future__ import annotations

import asyncio
import random
from collections.abc import Callable
from typing import Any, TypeVar

from app.core.errors import AIError, RetryConfig, classify_llm_error

T = TypeVar("T")

__all__ = ["with_retry", "RetryConfig"]


async def with_retry(
    coro_factory: Callable[[], Any],
    config: RetryConfig,
    on_retry: Callable[[int, float, AIError], None] | None = None,
) -> Any:
    """Execute a coroutine with retry on retryable errors.

    Args:
        coro_factory: Callable that returns a coroutine to execute
        config: RetryConfig with max_attempts, delays, and jitter settings
        on_retry: Optional callback called before each retry (attempt, delay, error)

    Returns:
        Result of the coroutine

    Raises:
        AIError: If error is not retryable or all retries exhausted
        Exception: If error is not an AIError subclass
    """
    last_error: AIError | None = None

    for attempt in range(1, config.max_attempts + 1):
        try:
            return await coro_factory()
        except AIError as exc:
            # Non-retryable errors (e.g. auth failures) should fail immediately
            # without consuming an attempt, so we re-raise before checking attempt count.
            if not exc.retryable:
                raise

            last_error = exc

            # Exhausted all attempts — propagate the error upward.
            if attempt >= config.max_attempts:
                raise

            delay = _calculate_delay(attempt, config)

            if on_retry and last_error:
                on_retry(attempt, delay, last_error)

            await asyncio.sleep(delay)

        except Exception as exc:
            # Non-AIError exceptions are classified as retryable by default
            # (conservative approach). If classification yields a non-retryable
            # error, re-raise immediately to avoid unnecessary retries.
            classified = classify_llm_error(exc)
            last_error = classified

            if not classified.retryable:
                raise

            if attempt >= config.max_attempts:
                raise

            delay = _calculate_delay(attempt, config)

            if on_retry:
                on_retry(attempt, delay, classified)

            await asyncio.sleep(delay)

    # Fallback: raised only if the loop produced no result and last_error is set.
    if last_error:
        raise last_error
    raise AIError(
        error_code=None,
        message="All retries exhausted",
        retryable=False,
        original_exception=None,
    )


def _calculate_delay(attempt: int, config: RetryConfig) -> float:
    """Calculate delay for given attempt number.

    Args:
        attempt: Current attempt number (1-indexed)
        config: RetryConfig with base_delay, max_delay, and jitter settings

    Returns:
        Delay in seconds before next retry
    """
    delay = config.base_delay * (2 ** (attempt - 1))
    delay = float(min(delay, config.max_delay))

    if config.jitter:
        delay = delay * (0.5 + random.random())

    return delay
