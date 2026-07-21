"""Structured logging utilities for AI operations."""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

from app.core.errors import AIError
from app.core.serialization_utils import safe_json_value


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if hasattr(record, "extra_fields"):
            log_data.update(safe_json_value(record.extra_fields))

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger with JSON formatting."""
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger


def log_ai_error(
    logger: logging.Logger,
    error: AIError,
    session_id: str | None = None,
    project_id: str | None = None,
    user_content: str | None = None,
    **context: Any,
) -> None:
    """Log an AI error with full context."""
    extra = {
        "error_code": error.error_code.value if error.error_code else None,
        "error_message": error.message,
        "retryable": error.retryable,
        "session_id": session_id,
        "project_id": project_id,
        "user_content": user_content,
        "failed_message": {
            "session_id": session_id,
            "project_id": project_id,
            "user_content": user_content,
            "error_code": error.error_code.value if error.error_code else None,
            "error_message": error.message,
        },
        **context,
    }

    # Strip None values so the logged JSON is clean and compact.
    extra["failed_message"] = {k: v for k, v in extra["failed_message"].items() if v is not None}

    logger.error(error.message, extra={"extra_fields": extra})


def log_retry_attempt(
    logger: logging.Logger,
    attempt: int,
    delay: float,
    error: AIError,
    session_id: str | None = None,
    project_id: str | None = None,
    **context: Any,
) -> None:
    """Log a retry attempt with context."""
    extra = {
        "retry_attempt": attempt,
        "retry_delay": delay,
        "error_code": error.error_code.value if error.error_code else None,
        "error_message": error.message,
        "retryable": error.retryable,
        "session_id": session_id,
        "project_id": project_id,
        **context,
    }

    logger.warning(f"Retrying after {delay:.2f}s (attempt {attempt})", extra={"extra_fields": extra})


def log_stream_complete(
    logger: logging.Logger,
    session_id: str,
    token_count: int | None = None,
    **context: Any,
) -> None:
    """Log stream completion."""
    extra = {
        "session_id": session_id,
        "token_count": token_count,
        "stream_status": "complete",
        **context,
    }

    logger.info("Stream completed", extra={"extra_fields": extra})
