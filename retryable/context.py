"""Retry context providing metadata about the current retry state."""

from dataclasses import dataclass, field
from typing import Any, Optional, Type
import time


@dataclass
class RetryContext:
    """Holds state and metadata for a single retry lifecycle."""

    attempt: int = 0
    max_attempts: int = 1
    delay: float = 0.0
    elapsed: float = 0.0
    exception: Optional[BaseException] = None
    result: Any = None
    start_time: float = field(default_factory=time.monotonic)

    @property
    def is_first_attempt(self) -> bool:
        """Return True if no retries have occurred yet."""
        return self.attempt == 0

    @property
    def is_last_attempt(self) -> bool:
        """Return True if this is the final allowed attempt."""
        return self.attempt >= self.max_attempts - 1

    @property
    def has_exception(self) -> bool:
        """Return True if the last attempt raised an exception."""
        return self.exception is not None

    def advance(self, delay: float = 0.0) -> "RetryContext"
        """Return a new context representing the next attempt."""
        return RetryContext(
            attempt=self.attempt + 1,
            max_attempts=self.max_attempts,
            delay=delay,
            elapsed=time.monotonic() - self.start_time,
            exception=None,
            result=None,
            start_time=self.start_time,
        )

    def with_exception(self, exc: BaseException) -> "RetryContext":
        """Return a copy of this context with the given exception recorded."""
        return RetryContext(
            attempt=self.attempt,
            max_attempts=self.max_attempts,
            delay=self.delay,
            elapsed=time.monotonic() - self.start_time,
            exception=exc,
            result=None,
            start_time=self.start_time,
        )

    def with_result(self, result: Any) -> "RetryContext":
        """Return a copy of this context with the given result recorded."""
        return RetryContext(
            attempt=self.attempt,
            max_attempts=self.max_attempts,
            delay=self.delay,
            elapsed=time.monotonic() - self.start_time,
            exception=None,
            result=result,
            start_time=self.start_time,
        )
