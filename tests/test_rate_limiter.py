"""Tests for the TokenBucketRateLimiter."""

import pytest
from retryable.rate_limiter import TokenBucketRateLimiter, RateLimitExceededError


class FakeClock:
    def __init__(self, start: float = 0.0) -> None:
        self._time = start

    def __call__(self) -> float:
        return self._time

    def advance(self, seconds: float) -> None:
        self._time += seconds


class TestTokenBucketRateLimiterInit:
    def test_raises_on_zero_rate(self):
        with pytest.raises(ValueError, match="rate must be positive"):
            TokenBucketRateLimiter(rate=0, capacity=5)

    def test_raises_on_negative_rate(self):
        with pytest.raises(ValueError, match="rate must be positive"):
            TokenBucketRateLimiter(rate=-1.0, capacity=5)

    def test_raises_on_zero_capacity(self):
        with pytest.raises(ValueError, match="capacity must be positive"):
            TokenBucketRateLimiter(rate=1.0, capacity=0)

    def test_exposes_rate(self):
        rl = TokenBucketRateLimiter(rate=2.0, capacity=10)
        assert rl.rate == 2.0

    def test_exposes_capacity(self):
        rl = TokenBucketRateLimiter(rate=2.0, capacity=10)
        assert rl.capacity == 10


class TestTokenBucketAcquire:
    def test_acquire_succeeds_when_tokens_available(self):
        clock = FakeClock()
        rl = TokenBucketRateLimiter(rate=1.0, capacity=5, clock=clock)
        assert rl.acquire() is True

    def test_acquire_decrements_tokens(self):
        clock = FakeClock()
        rl = TokenBucketRateLimiter(rate=1.0, capacity=5, clock=clock)
        rl.acquire()
        assert rl.available_tokens() == pytest.approx(4.0)

    def test_acquire_returns_false_when_empty(self):
        clock = FakeClock()
        rl = TokenBucketRateLimiter(rate=1.0, capacity=2, clock=clock)
        rl.acquire()
        rl.acquire()
        assert rl.acquire() is False

    def test_acquire_drains_all_capacity(self):
        clock = FakeClock()
        rl = TokenBucketRateLimiter(rate=1.0, capacity=3, clock=clock)
        results = [rl.acquire() for _ in range(3)]
        assert all(results)
        assert rl.acquire() is False


class TestTokenBucketRefill:
    def test_tokens_refill_over_time(self):
        clock = FakeClock()
        rl = TokenBucketRateLimiter(rate=2.0, capacity=5, clock=clock)
        rl.acquire()
        rl.acquire()
        clock.advance(1.0)  # Should add 2 tokens
        assert rl.available_tokens() == pytest.approx(4.0)

    def test_tokens_do_not_exceed_capacity(self):
        clock = FakeClock()
        rl = TokenBucketRateLimiter(rate=10.0, capacity=3, clock=clock)
        clock.advance(10.0)  # Would add 100 tokens, capped at 3
        assert rl.available_tokens() == pytest.approx(3.0)

    def test_acquire_after_refill_succeeds(self):
        clock = FakeClock()
        rl = TokenBucketRateLimiter(rate=1.0, capacity=1, clock=clock)
        rl.acquire()  # drain
        assert rl.acquire() is False
        clock.advance(1.0)  # refill 1 token
        assert rl.acquire() is True

    def test_partial_refill(self):
        clock = FakeClock()
        rl = TokenBucketRateLimiter(rate=2.0, capacity=10, clock=clock)
        for _ in range(10):
            rl.acquire()  # drain
        clock.advance(0.25)  # adds 0.5 tokens, not enough
        assert rl.acquire() is False
        clock.advance(0.25)  # total 0.5 + 0.5 = 1 token
        assert rl.acquire() is True
