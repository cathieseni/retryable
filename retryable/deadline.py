"""Deadline-based retry stopping strategy.

Provides a RetryDeadline class that limits retry attempts based on
elapsed wall-clock time rather than a fixed number of attempts.
"""

import time
from typing import Optional


class RetryDeadline:
    """Stops retrying once a wall-clock deadline has been exceeded.

    Example::

        deadline = RetryDeadline(timeout=5.0)

        @retry(stop=deadline.should_stop)
        def flaky():
            ...
    """

    def __init__(self, timeout: float, *, clock=None) -> None:
        """Initialise the deadline.

        Args:
            timeout: Maximum number of seconds to keep retrying.
            clock: Callable that returns the current time in seconds.
                   Defaults to :func:`time.monotonic`. Useful for testing.
        """
        if timeout <= 0:
            raise ValueError("timeout must be a positive number")

        self._timeout = timeout
        self._clock = clock or time.monotonic
        self._start: Optional[float] = None

    @property
    def timeout(self) -> float:
        """The configured timeout in seconds."""
        return self._timeout

    @property
    def elapsed(self) -> float:
        """Seconds elapsed since the deadline was first checked."""
        if self._start is None:
            return 0.0
        return self._clock() - self._start

    @property
    def remaining(self) -> float:
        """Seconds remaining before the deadline expires (never negative)."""
        return max(0.0, self._timeout - self.elapsed)

    def reset(self) -> None:
        """Reset the deadline so it starts fresh on the next check."""
        self._start = None

    def should_stop(self, attempt: int) -> bool:
        """Return True when the deadline has been exceeded.

        On the very first call the start time is recorded, so the
        deadline begins counting from the first retry check.

        Args:
            attempt: Current attempt number (1-based). Not used directly
                     but kept consistent with other stop-predicate signatures.
        """
        if self._start is None:
            self._start = self._clock()

        return self.elapsed >= self._timeout
