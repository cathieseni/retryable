"""Tests for retryable.retry_with_deadline."""

from __future__ import annotations

import pytest

from retryable.retry_with_deadline import retry_with_deadline


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class FakeClock:
    def __init__(self, start: float = 0.0):
        self._time = start

    def __call__(self) -> float:
        return self._time

    def advance(self, seconds: float) -> None:
        self._time += seconds


def no_sleep(_delay: float) -> None:
    """Sleep stub that does nothing."""


# ---------------------------------------------------------------------------
# Success path
# ---------------------------------------------------------------------------

class TestRetryWithDeadlineSuccess:
    def test_returns_value_on_first_success(self):
        @retry_with_deadline(5.0, sleep=no_sleep)
        def always_succeeds():
            return 42

        assert always_succeeds() == 42

    def test_returns_value_after_transient_failure(self):
        calls = []

        @retry_with_deadline(5.0, sleep=no_sleep)
        def flaky():
            calls.append(1)
            if len(calls) < 3:
                raise ValueError("not yet")
            return "ok"

        assert flaky() == "ok"
        assert len(calls) == 3


# ---------------------------------------------------------------------------
# Deadline enforcement
# ---------------------------------------------------------------------------

class TestRetryWithDeadlineExpiry:
    def test_raises_timeout_when_deadline_exceeded(self):
        clock = FakeClock()
        slept: list[float] = []

        def fake_sleep(delay: float) -> None:
            slept.append(delay)
            clock.advance(delay)

        @retry_with_deadline(1.0, sleep=fake_sleep, clock=clock, backoff=lambda _: 0.6)
        def always_fails():
            clock.advance(0.0)  # no extra time, sleep drives the clock
            raise RuntimeError("boom")

        with pytest.raises(TimeoutError):
            always_fails()

    def test_does_not_sleep_beyond_remaining_time(self):
        clock = FakeClock()
        slept: list[float] = []

        def fake_sleep(delay: float) -> None:
            slept.append(delay)
            clock.advance(delay)

        # backoff returns a very long delay; it must be capped to remaining time
        @retry_with_deadline(1.0, sleep=fake_sleep, clock=clock, backoff=lambda _: 999.0)
        def always_fails():
            raise RuntimeError("boom")

        with pytest.raises((TimeoutError, RuntimeError)):
            always_fails()

        assert all(s <= 1.0 for s in slept), f"Sleep exceeded deadline: {slept}"


# ---------------------------------------------------------------------------
# Non-retryable exceptions
# ---------------------------------------------------------------------------

class TestRetryWithDeadlineNonRetryable:
    def test_does_not_retry_unlisted_exception(self):
        calls = []

        @retry_with_deadline(5.0, exceptions=(ValueError,), sleep=no_sleep)
        def raises_key_error():
            calls.append(1)
            raise KeyError("nope")

        with pytest.raises(KeyError):
            raises_key_error()

        assert len(calls) == 1


# ---------------------------------------------------------------------------
# max_attempts enforcement
# ---------------------------------------------------------------------------

class TestRetryWithDeadlineMaxAttempts:
    def test_stops_after_max_attempts(self):
        calls = []

        @retry_with_deadline(60.0, max_attempts=3, sleep=no_sleep)
        def always_fails():
            calls.append(1)
            raise RuntimeError("fail")

        with pytest.raises(RuntimeError):
            always_fails()

        assert len(calls) == 3
