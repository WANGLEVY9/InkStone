"""Error classification system for AI/LLM operations."""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum


class ErrorCode(Enum):
    """Categorized error codes for LLM API failures.

    Each member maps to a specific class of error returned by the LLM provider,
    allowing downstream logic (retry, logging, alerting) to react consistently.
    """

    RATE_LIMIT = "rate_limit"
    MODEL_UNAVAILABLE = "model_unavailable"
    TIMEOUT = "timeout"
    NETWORK_ERROR = "network_error"
    AUTHENTICATION = "authentication"
    BAD_REQUEST = "bad_request"
    PERMISSION_DENIED = "permission_denied"
    CONTEXT_WINDOW_EXCEEDED = "context_window_exceeded"
    CONFIG_NOT_SET = "config_not_set"
    UNKNOWN = "unknown"


class AIError(Exception):
    """A classified AI/LLM error with retry metadata.

    Wraps the original exception together with a structured error code and a
    flag indicating whether the operation should be retried.
    """

    def __init__(
        self,
        error_code: ErrorCode | None,
        message: str,
        retryable: bool,
        original_exception: Exception | None = None,
    ) -> None:
        self.error_code = error_code
        self.message = message
        self.retryable = retryable
        self.original_exception = original_exception
        super().__init__(message)

    def __repr__(self) -> str:
        return f"AIError(error_code={self.error_code}, message={self.message!r}, retryable={self.retryable})"

    def __str__(self) -> str:
        return self.message


def classify_llm_error(exc: Exception) -> AIError:
    """Classify an exception from LLM API call.

    Args:
        exc: The exception from LLM API call

    Returns:
        AIError with classified error code and retry flag
    """
    # Check both exception class name and status_code because different LLM
    # providers use different naming conventions (e.g. "RateLimitError" vs
    # status_code=429). This dual-check ensures broader provider compatibility.
    error_message = str(exc)
    exc_class_name = exc.__class__.__name__

    if "RateLimitError" in exc_class_name or getattr(exc, "status_code", None) == 429:
        return AIError(
            error_code=ErrorCode.RATE_LIMIT,
            message=error_message,
            retryable=True,
            original_exception=exc,
        )

    if "ServiceUnavailableError" in exc_class_name or getattr(exc, "status_code", None) == 503:
        return AIError(
            error_code=ErrorCode.MODEL_UNAVAILABLE,
            message=error_message,
            retryable=True,
            original_exception=exc,
        )

    if "AuthenticationError" in exc_class_name or getattr(exc, "status_code", None) == 401:
        return AIError(
            error_code=ErrorCode.AUTHENTICATION,
            message=error_message,
            retryable=False,
            original_exception=exc,
        )

    if "BadRequestError" in exc_class_name or getattr(exc, "status_code", None) == 400:
        return AIError(
            error_code=ErrorCode.BAD_REQUEST,
            message=error_message,
            retryable=False,
            original_exception=exc,
        )

    if "PermissionDeniedError" in exc_class_name or getattr(exc, "status_code", None) == 403:
        return AIError(
            error_code=ErrorCode.PERMISSION_DENIED,
            message=error_message,
            retryable=False,
            original_exception=exc,
        )

    if "Timeout" in exc_class_name or isinstance(exc, TimeoutError) or "timeout" in error_message.lower():
        return AIError(
            error_code=ErrorCode.TIMEOUT,
            message=error_message,
            retryable=True,
            original_exception=exc,
        )

    if "Connect" in exc_class_name or "Network" in exc_class_name or "RemoteProtocol" in exc_class_name:
        return AIError(
            error_code=ErrorCode.NETWORK_ERROR,
            message=error_message,
            retryable=True,
            original_exception=exc,
        )

    if "context window" in error_message.lower() or "token limit" in error_message.lower():
        return AIError(
            error_code=ErrorCode.CONTEXT_WINDOW_EXCEEDED,
            message=error_message,
            retryable=False,
            original_exception=exc,
        )

    # Default: unknown error, retryable (conservative approach)
    return AIError(
        error_code=ErrorCode.UNKNOWN,
        message=error_message,
        retryable=True,
        original_exception=exc,
    )


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_attempts: int = int(os.environ.get("LLM_MAX_RETRIES", "3"))
    base_delay: float = float(os.environ.get("LLM_RETRY_BASE_DELAY", "1.0"))
    max_delay: float = 30.0
    jitter: bool = True
