"""Tests for retry_with_rate_limiter decorator."""

import pytest
from unittest.mock import MagicMock
from retryable.retry_with_rate_limiter import retry_with_rate_limiter
from retryable.rate_limiter import TokenBucketRateLimiter, RateLimitExceededError


class FakeClock:
    def __init__(self, start: float = 0.0) -> None:
        self._time = start

    def __call__(self) -> float:
        return self._time

    def advance(self, seconds: float) -> None:
        self._time += seconds


class TestRetryWithRateLimiterSuccess:
    def test_returns_value_on_first_success(self):
        clock = FakeClock()
        rl = TokenBucketRateLimiter(rate=10.0, capacity=5, clock=clock)

        @retry_with_rate_limiter(rl)
        def always_succeeds():
            return 42

        assert always_succeeds() == 42

    def test_consumes_one_token_on_success(self):
        clock = FakeClock()
        rl = TokenBucketRateLimiter(rate=1.0, capacity=5, clock=clock)

        @retry_with_rate_limiter(rl)
        def always_succeeds():
            return "ok"

        always_succeeds()
        assert rl.available_tokens() == pytest.approx(4.0)


class TestRetryWithRateLimiterRetries:
    def test_retries_on_exception_and_succeeds(self):
        clock = FakeClock()
        rl = TokenBucketRateLimiter(rate=1.0, capacity=5, clock=clock)
        call_count = 0

        @retry_with_rate_limiter(rl, max_attempts=3)
        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("not yet")
            return "done"

        result = flaky()
        assert result == "done"
        assert call_count == 3

    def test_consumes_token_per_attempt(self):
        clock = FakeClock()
        rl = TokenBucketRateLimiter(rate=1.0, capacity=5, clock=clock)
        call_count = 0

        @retry_with_rate_limiter(rl, max_attempts=3)
        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RuntimeError("fail")
            return "ok"

        flaky()
        assert rl.available_tokens() == pytest.approx(2.0)

    def test_raises_last_exception_after_max_attempts(self):
        clock = FakeClock()
        rl = TokenBucketRateLimiter(rate=10.0, capacity=10, clock=clock)

        @retry_with_rate_limiter(rl, max_attempts=3)
        def always_fails():
            raise ValueError("always fails")

        with pytest.raises(ValueError, match="always fails"):
            always_fails()


class TestRetryWithRateLimiterRateLimit:
    def test_raises_rate_limit_exceeded_when_bucket_empty(self):
        clock = FakeClock()
        rl = TokenBucketRateLimiter(rate=1.0, capacity=1, clock=clock)
        rl.acquire()  # drain the bucket

        @retry_with_rate_limiter(rl, max_attempts=3)
        def fn():
            return "ok"

        with pytest.raises(RateLimitExceededError):
            fn()

    def test_on_rate_limit_exceeded_callback_called(self):
        clock = FakeClock()
        rl = TokenBucketRateLimiter(rate=1.0, capacity=1, clock=clock)
        rl.acquire()  # drain

        callback = MagicMock()

        @retry_with_rate_limiter(rl, max_attempts=3, on_rate_limit_exceeded=callback)
        def fn():
            return "ok"

        with pytest.raises(RateLimitExceededError):
            fn()

        callback.assert_called_once()

    def test_rate_limit_exceeded_after_tokens_drained_mid_retry(self):
        clock = FakeClock()
        # Only 2 tokens: first attempt uses 1, second uses 1, third raises
        rl = TokenBucketRateLimiter(rate=0.0001, capacity=2, clock=clock)
        call_count = 0

        @retry_with_rate_limiter(rl, max_attempts=5)
        def flaky():
            nonlocal call_count
            call_count += 1
            raise RuntimeError("fail")

        with pytest.raises(RateLimitExceededError):
            flaky()

        assert call_count == 2
