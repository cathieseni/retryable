"""Tests for retryable.deadline.RetryDeadline."""

import pytest
from retryable.deadline import RetryDeadline


class FakeClock:
    """Controllable monotonic clock for deterministic tests."""

    def __init__(self, start: float = 0.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class TestRetryDeadlineInit:
    def test_stores_timeout(self):
        d = RetryDeadline(timeout=10.0)
        assert d.timeout == 10.0

    def test_raises_on_zero_timeout(self):
        with pytest.raises(ValueError, match="positive"):
            RetryDeadline(timeout=0)

    def test_raises_on_negative_timeout(self):
        with pytest.raises(ValueError, match="positive"):
            RetryDeadline(timeout=-1.0)


class TestRetryDeadlineElapsed:
    def test_elapsed_is_zero_before_first_check(self):
        clock = FakeClock()
        d = RetryDeadline(timeout=5.0, clock=clock)
        assert d.elapsed == 0.0

    def test_elapsed_after_first_check(self):
        clock = FakeClock()
        d = RetryDeadline(timeout=5.0, clock=clock)
        d.should_stop(1)
        clock.advance(2.0)
        assert d.elapsed == pytest.approx(2.0)


class TestRetryDeadlineRemaining:
    def test_remaining_equals_timeout_before_first_check(self):
        clock = FakeClock()
        d = RetryDeadline(timeout=5.0, clock=clock)
        # Before the first call elapsed is 0, so remaining == timeout
        assert d.remaining == pytest.approx(5.0)

    def test_remaining_decreases_over_time(self):
        clock = FakeClock()
        d = RetryDeadline(timeout=5.0, clock=clock)
        d.should_stop(1)
        clock.advance(3.0)
        assert d.remaining == pytest.approx(2.0)

    def test_remaining_never_negative(self):
        clock = FakeClock()
        d = RetryDeadline(timeout=2.0, clock=clock)
        d.should_stop(1)
        clock.advance(10.0)
        assert d.remaining == 0.0


class TestRetryDeadlineShouldStop:
    def test_does_not_stop_before_timeout(self):
        clock = FakeClock()
        d = RetryDeadline(timeout=5.0, clock=clock)
        clock.advance(3.0)
        assert d.should_stop(1) is False

    def test_stops_after_timeout(self):
        clock = FakeClock()
        d = RetryDeadline(timeout=5.0, clock=clock)
        d.should_stop(1)          # records start at t=0
        clock.advance(6.0)        # now at t=6, past deadline
        assert d.should_stop(2) is True

    def test_stops_exactly_at_timeout(self):
        clock = FakeClock()
        d = RetryDeadline(timeout=5.0, clock=clock)
        d.should_stop(1)
        clock.advance(5.0)
        assert d.should_stop(2) is True

    def test_reset_restarts_deadline(self):
        clock = FakeClock()
        d = RetryDeadline(timeout=5.0, clock=clock)
        d.should_stop(1)
        clock.advance(6.0)
        assert d.should_stop(2) is True

        d.reset()
        # After reset the start is cleared; next call re-anchors to current time
        assert d.should_stop(3) is False
