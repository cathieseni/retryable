"""Context manager for per-block attempt timeouts using SIGALRM."""

import signal
from types import TracebackType
from typing import Optional, Type

from retryable.retry_with_timeout import AttemptTimeoutError, _timeout_handler


class AttemptTimeout:
    """Context manager that raises AttemptTimeoutError if the block exceeds
    the given number of seconds.

    Uses POSIX SIGALRM via setitimer for sub-second precision.

    Example::

        with AttemptTimeout(seconds=2.5):
            result = slow_operation()
    """

    def __init__(self, seconds: float) -> None:
        if seconds <= 0:
            raise ValueError("seconds must be positive")
        self._seconds = seconds
        self._old_handler = None

    def __enter__(self) -> "AttemptTimeout":
        self._old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
        signal.setitimer(signal.ITIMER_REAL, self._seconds)
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> bool:
        signal.setitimer(signal.ITIMER_REAL, 0)
        if self._old_handler is not None:
            signal.signal(signal.SIGALRM, self._old_handler)
        # Do not suppress exceptions
        return False

    @property
    def seconds(self) -> float:
        """The configured timeout in seconds."""
        return self._seconds
