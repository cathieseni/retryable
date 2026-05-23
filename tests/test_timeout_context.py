"""Tests for AttemptTimeout context manager."""

import time
import pytest

from retryable.timeout_context import AttemptTimeout
from retryable.retry_with_timeout import AttemptTimeoutError


class TestAttemptTimeoutInit:
    def test_stores_seconds(self):
        ctx = AttemptTimeout(seconds=3.0)
        assert ctx.seconds == 3.0

    def test_raises_on_zero_seconds(self):
        with pytest.raises(ValueError, match="positive"):
            AttemptTimeout(seconds=0)

    def test_raises_on_negative_seconds(self):
        with pytest.raises(ValueError, match="positive"):
            AttemptTimeout(seconds=-1.0)


class TestAttemptTimeoutContextManager:
    def test_does_not_raise_when_block_completes_in_time(self):
        with AttemptTimeout(seconds=2.0):
            result = 1 + 1
        assert result == 2

    def test_raises_attempt_timeout_error_on_slow_block(self):
        with pytest.raises(AttemptTimeoutError):
            with AttemptTimeout(seconds=0.05):
                time.sleep(5)

    def test_does_not_suppress_other_exceptions(self):
        with pytest.raises(ValueError, match="oops"):
            with AttemptTimeout(seconds=2.0):
                raise ValueError("oops")

    def test_timer_cancelled_after_successful_block(self):
        """Ensure the timer is disarmed so it doesn't fire after the block."""
        with AttemptTimeout(seconds=0.1):
            pass
        # If the timer were still armed, sleeping here would trigger it.
        time.sleep(0.15)

    def test_timer_cancelled_after_exception(self):
        """Ensure the timer is disarmed even when an exception propagates."""
        with pytest.raises(RuntimeError):
            with AttemptTimeout(seconds=0.1):
                raise RuntimeError("early exit")
        time.sleep(0.15)

    def test_nested_contexts_restore_outer_handler(self):
        """Inner context should restore the outer handler on exit."""
        outer_fired = []

        with AttemptTimeout(seconds=2.0):
            with AttemptTimeout(seconds=1.0):
                pass
            # Outer context is still active and should not have fired.
            outer_fired.append(True)

        assert outer_fired == [True]
