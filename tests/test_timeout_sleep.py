"""Tests for retryable.timeout_sleep."""

import pytest
from unittest.mock import MagicMock

from retryable.timeout_sleep import capped_sleep, make_sleep


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


# ---------------------------------------------------------------------------
# make_sleep
# ---------------------------------------------------------------------------

class TestMakeSleep:
    def test_returns_callable(self):
        sleep_fn = make_sleep()
        assert callable(sleep_fn)

    def test_with_fake_clock_advances_clock(self):
        clock = FakeClock(0.0)
        sleep_fn = make_sleep(clock=clock)
        sleep_fn(3.5)
        assert clock() == pytest.approx(3.5)

    def test_with_fake_clock_multiple_calls(self):
        clock = FakeClock(0.0)
        sleep_fn = make_sleep(clock=clock)
        sleep_fn(1.0)
        sleep_fn(2.0)
        assert clock() == pytest.approx(3.0)

    def test_no_clock_returns_real_sleep(self):
        import time
        sleep_fn = make_sleep()
        assert sleep_fn is time.sleep


# ---------------------------------------------------------------------------
# capped_sleep
# ---------------------------------------------------------------------------

class TestCappedSleep:
    def _mock_sleep(self):
        return MagicMock()

    def test_sleeps_full_delay_when_no_deadline(self):
        mock = self._mock_sleep()
        result = capped_sleep(2.0, sleep_fn=mock)
        mock.assert_called_once_with(2.0)
        assert result == pytest.approx(2.0)

    def test_caps_sleep_to_deadline_remaining(self):
        mock = self._mock_sleep()
        result = capped_sleep(5.0, deadline_remaining=1.5, sleep_fn=mock)
        mock.assert_called_once_with(1.5)
        assert result == pytest.approx(1.5)

    def test_uses_full_delay_when_deadline_is_larger(self):
        mock = self._mock_sleep()
        result = capped_sleep(1.0, deadline_remaining=10.0, sleep_fn=mock)
        mock.assert_called_once_with(1.0)
        assert result == pytest.approx(1.0)

    def test_zero_delay_does_not_call_sleep(self):
        mock = self._mock_sleep()
        result = capped_sleep(0.0, sleep_fn=mock)
        mock.assert_not_called()
        assert result == pytest.approx(0.0)

    def test_negative_deadline_remaining_does_not_call_sleep(self):
        mock = self._mock_sleep()
        result = capped_sleep(3.0, deadline_remaining=-1.0, sleep_fn=mock)
        mock.assert_not_called()
        assert result == pytest.approx(0.0)

    def test_returns_actual_sleep_duration(self):
        mock = self._mock_sleep()
        result = capped_sleep(4.0, deadline_remaining=2.0, sleep_fn=mock)
        assert result == pytest.approx(2.0)
