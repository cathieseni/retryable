"""Sleep utilities with deadline-aware interruption for retry loops."""

import time
from typing import Callable, Optional


_default_sleep: Callable[[float], None] = time.sleep


def make_sleep(clock: Optional[Callable[[], float]] = None) -> Callable[[float], None]:
    """Create a sleep function backed by the given clock (for testing).

    When a real clock is used this simply delegates to ``time.sleep``.  In
    tests a fake clock can be supplied so that sleeping advances the clock
    without actually blocking.
    """
    if clock is None:
        return _default_sleep

    def _sleep(seconds: float) -> None:
        # Advance the fake clock by the requested duration.
        # The clock object must expose an ``advance`` method (see FakeClock in
        # the test suite).
        clock.advance(seconds)  # type: ignore[attr-defined]

    return _sleep


def capped_sleep(
    delay: float,
    *,
    deadline_remaining: Optional[float] = None,
    sleep_fn: Optional[Callable[[float], None]] = None,
) -> float:
    """Sleep for *delay* seconds, but never beyond the remaining deadline.

    Parameters
    ----------
    delay:
        Desired sleep duration in seconds.
    deadline_remaining:
        Seconds left before the overall retry deadline expires.  When
        provided the actual sleep is ``min(delay, deadline_remaining)``.
    sleep_fn:
        Callable used to perform the sleep.  Defaults to ``time.sleep``.

    Returns
    -------
    float
        The actual number of seconds slept.
    """
    if sleep_fn is None:
        sleep_fn = _default_sleep

    actual = delay
    if deadline_remaining is not None:
        actual = min(delay, max(0.0, deadline_remaining))

    if actual > 0:
        sleep_fn(actual)

    return actual
