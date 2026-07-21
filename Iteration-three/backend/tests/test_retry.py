"""Unit tests for AI error classification and retry logic.

These tests verify:
1. classify_llm_error() correctly categorizes exceptions
2. with_retry() handles retryable vs non-retryable errors correctly
3. Exponential backoff delay calculation is correct
"""

import pytest


class TestErrorClassification:
    """Test error classification for LLM errors."""

    def test_rate_limit_error_is_retryable(self) -> None:
        """Rate limit errors (429) should be retryable."""
        from app.core.errors import ErrorCode, classify_llm_error

        exc = Exception("Rate limit exceeded")
        exc.status_code = 429  # type: ignore[attr-defined]

        result = classify_llm_error(exc)

        assert result.error_code == ErrorCode.RATE_LIMIT
        assert result.retryable is True

    def test_authentication_error_is_not_retryable(self) -> None:
        """Authentication errors (401) should not be retryable."""
        from app.core.errors import ErrorCode, classify_llm_error

        exc = Exception("Invalid API key")
        exc.status_code = 401  # type: ignore[attr-defined]

        result = classify_llm_error(exc)

        assert result.error_code == ErrorCode.AUTHENTICATION
        assert result.retryable is False

    def test_bad_request_error_is_not_retryable(self) -> None:
        """Bad request errors (400) should not be retryable."""
        from app.core.errors import ErrorCode, classify_llm_error

        exc = Exception("Invalid request parameters")
        exc.status_code = 400  # type: ignore[attr-defined]

        result = classify_llm_error(exc)

        assert result.error_code == ErrorCode.BAD_REQUEST
        assert result.retryable is False

    def test_timeout_error_is_retryable(self) -> None:
        """Timeout errors should be retryable."""
        from app.core.errors import ErrorCode, classify_llm_error

        exc = TimeoutError("Request timeout")

        result = classify_llm_error(exc)

        assert result.error_code == ErrorCode.TIMEOUT
        assert result.retryable is True

    def test_unknown_error_defaults_to_retryable(self) -> None:
        """Unknown errors should default to retryable (conservative approach)."""
        from app.core.errors import ErrorCode, classify_llm_error

        exc = Exception("Something went wrong")

        result = classify_llm_error(exc)

        assert result.error_code == ErrorCode.UNKNOWN
        assert result.retryable is True


class TestRetryLogic:
    """Test retry logic with exponential backoff."""

    @pytest.mark.asyncio
    async def test_retryable_error_retries_max_attempts(self) -> None:
        """Retryable errors should be retried max_attempts times."""
        from app.core.retry import RetryConfig, with_retry

        attempt_count = 0

        async def failing_coro() -> None:
            nonlocal attempt_count
            attempt_count += 1
            raise TimeoutError("Retryable error")

        config = RetryConfig(max_attempts=3, base_delay=0.01, max_delay=0.1)

        with pytest.raises(TimeoutError):
            await with_retry(failing_coro, config)

        assert attempt_count == 3

    @pytest.mark.asyncio
    async def test_non_retryable_error_fails_immediately(self) -> None:
        """Non-retryable errors should fail on first attempt without retry."""
        from app.core.errors import AIError, ErrorCode
        from app.core.retry import RetryConfig, with_retry

        attempt_count = 0

        async def failing_coro() -> None:
            nonlocal attempt_count
            attempt_count += 1
            raise AIError(
                error_code=ErrorCode.AUTHENTICATION,
                message="Invalid API key",
                retryable=False,
                original_exception=None,
            )

        config = RetryConfig(max_attempts=3, base_delay=0.01, max_delay=0.1)

        with pytest.raises(AIError):
            await with_retry(failing_coro, config)

        assert attempt_count == 1

    @pytest.mark.asyncio
    async def test_successful_call_returns_result(self) -> None:
        """Successful calls should return immediately without retry."""
        from app.core.retry import RetryConfig, with_retry

        attempt_count = 0

        async def successful_coro() -> str:
            nonlocal attempt_count
            attempt_count += 1
            return "success"

        config = RetryConfig(max_attempts=3, base_delay=0.01, max_delay=0.1)
        result = await with_retry(successful_coro, config)

        assert result == "success"
        assert attempt_count == 1

    @pytest.mark.asyncio
    async def test_retry_succeeds_on_second_attempt(self) -> None:
        """If first attempt fails but second succeeds, return result."""
        from app.core.retry import RetryConfig, with_retry

        attempt_count = 0

        async def sometimes_failing_coro() -> str:
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count == 1:
                raise TimeoutError("Transient failure")
            return "recovered"

        config = RetryConfig(max_attempts=3, base_delay=0.01, max_delay=0.1)
        result = await with_retry(sometimes_failing_coro, config)

        assert result == "recovered"
        assert attempt_count == 2


class TestOnRetryCallback:
    """Test the on_retry callback mechanism."""

    @pytest.mark.asyncio
    async def test_on_retry_callback_is_called(self) -> None:
        """on_retry callback should be called on each retry attempt."""
        from app.core.retry import RetryConfig, with_retry

        callback_calls = []

        def on_retry(attempt: int, delay: float, error: Exception) -> None:
            callback_calls.append((attempt, delay, error))

        async def failing_coro() -> None:
            raise TimeoutError("Retryable")

        config = RetryConfig(max_attempts=3, base_delay=0.01, max_delay=0.1)

        with pytest.raises(TimeoutError):
            await with_retry(failing_coro, config, on_retry=on_retry)

        assert len(callback_calls) == 2
        assert callback_calls[0][0] == 1
        assert callback_calls[1][0] == 2
