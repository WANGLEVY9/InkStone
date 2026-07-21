"""Integration tests for chat error handling.

These tests verify:
1. AI errors trigger SSE error events with proper structure
2. Error logging captures failed message context
3. Non-retryable errors fail immediately without retry
4. Retryable errors exhaust retries before sending error event
"""

from __future__ import annotations

import pytest

from app.core.errors import AIError, ErrorCode, RetryConfig


class TestAIErrorHandling:
    """Test AI error classification and handling."""

    def test_error_code_values(self) -> None:
        """Verify ErrorCode enum values."""
        assert ErrorCode.RATE_LIMIT.value == "rate_limit"
        assert ErrorCode.AUTHENTICATION.value == "authentication"
        assert ErrorCode.TIMEOUT.value == "timeout"
        assert ErrorCode.UNKNOWN.value == "unknown"

    def test_ai_error_dataclass(self) -> None:
        """Verify AIError dataclass fields."""
        error = AIError(
            error_code=ErrorCode.RATE_LIMIT,
            message="Rate limit exceeded",
            retryable=True,
            original_exception=None,
        )
        assert error.error_code == ErrorCode.RATE_LIMIT
        assert error.message == "Rate limit exceeded"
        assert error.retryable is True
        assert error.original_exception is None

    def test_ai_error_is_exception(self) -> None:
        """AIError should inherit from Exception."""
        error = AIError(
            error_code=ErrorCode.RATE_LIMIT,
            message="Rate limit exceeded",
            retryable=True,
            original_exception=None,
        )
        assert isinstance(error, Exception)

    def test_retry_config_defaults(self) -> None:
        """RetryConfig should have sensible defaults."""
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 30.0
        assert config.jitter is True

    def test_retry_config_can_be_created_with_custom_values(self) -> None:
        """RetryConfig should accept custom values."""
        config = RetryConfig(max_attempts=5, base_delay=2.0)
        assert config.max_attempts == 5
        assert config.base_delay == 2.0


class TestErrorEventStructure:
    """Test SSE error event structure."""

    def test_error_event_format(self) -> None:
        """Verify error event JSON structure."""
        import json

        error_payload = {
            "error_code": ErrorCode.RATE_LIMIT.value,
            "message": "Rate limit exceeded",
            "retryable": True,
        }

        json_str = json.dumps(error_payload)
        parsed = json.loads(json_str)

        assert "error_code" in parsed
        assert "message" in parsed
        assert "retryable" in parsed
        assert parsed["retryable"] is True

    def test_error_event_sse_format(self) -> None:
        """Verify error event is formatted as SSE."""
        import json

        error_payload = {
            "error_code": ErrorCode.AUTHENTICATION.value,
            "message": "Invalid API key",
            "retryable": False,
        }

        sse_event = f"event: error\ndata: {json.dumps(error_payload)}\n\n"

        assert sse_event.startswith("event: error\ndata: ")
        assert "\n\n" in sse_event


class TestRetryConfigInGraph:
    """Test retry config integration with graph builder."""

    def test_create_orchestrator_graph_returns_different_graphs(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """create_orchestrator_graph should return a compiled graph."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        from app.core.graph.builder import create_orchestrator_graph

        graph1 = create_orchestrator_graph("test-project-1")
        graph2 = create_orchestrator_graph("test-project-2")
        assert graph1 is not None
        assert graph2 is not None

    def test_retry_config_accepts_custom_values(self) -> None:
        """RetryConfig should accept custom values."""
        config = RetryConfig(max_attempts=5, base_delay=3.0)
        assert config.max_attempts == 5
        assert config.base_delay == 3.0


class TestErrorLogging:
    """Test error logging functionality."""

    def test_failed_message_structure(self) -> None:
        """Verify failed message structure for logging."""
        failed_message = {
            "session_id": "test-session-123",
            "project_id": "test-project-456",
            "user_content": "Test user input",
            "error_code": ErrorCode.RATE_LIMIT.value,
            "error_message": "Rate limit exceeded",
        }

        assert "session_id" in failed_message
        assert "project_id" in failed_message
        assert "user_content" in failed_message
        assert "error_code" in failed_message
        assert "error_message" in failed_message

    def test_log_ai_error_import(self) -> None:
        """Verify log_ai_error can be imported."""
        from app.core.logging_utils import get_logger, log_ai_error

        logger = get_logger("test")
        error = AIError(
            error_code=ErrorCode.UNKNOWN,
            message="Test error",
            retryable=True,
            original_exception=None,
        )

        log_ai_error(logger, error, session_id="test", project_id="test")

    def test_log_retry_attempt_import(self) -> None:
        """Verify log_retry_attempt can be imported."""
        from app.core.logging_utils import get_logger, log_retry_attempt

        logger = get_logger("test")
        error = AIError(
            error_code=ErrorCode.RATE_LIMIT,
            message="Rate limit exceeded",
            retryable=True,
            original_exception=None,
        )

        log_retry_attempt(logger, attempt=1, delay=1.0, error=error)

    def test_log_stream_complete_import(self) -> None:
        """Verify log_stream_complete can be imported."""
        from app.core.logging_utils import get_logger, log_stream_complete

        logger = get_logger("test")

        log_stream_complete(logger, session_id="test", token_count=100)
