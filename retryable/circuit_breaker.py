"""Circuit breaker integration for retryable.

Provides a CircuitBreaker that can halt retry attempts when a failure
threshold is exceeded, preventing cascading failures.
"""

from __future__ import annotations

import time
from enum import Enum, auto
from typing import Callable, Optional


class CircuitState(Enum):
    CLOSED = auto()   # Normal operation
    OPEN = auto()     # Failing; reject calls
    HALF_OPEN = auto()  # Probing for recovery


class CircuitBreakerOpenError(Exception):
    """Raised when a call is attempted while the circuit is open."""


class CircuitBreaker:
    """Tracks consecutive failures and opens the circuit when a threshold
    is exceeded.  After a recovery timeout the circuit moves to HALF_OPEN
    and allows a single probe attempt.

    Args:
        failure_threshold: Number of consecutive failures before opening.
        recovery_timeout: Seconds to wait before transitioning to HALF_OPEN.
        clock: Callable returning the current time (default: time.monotonic).
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        clock: Optional[Callable[[], float]] = None,
    ) -> None:
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be >= 1")
        if recovery_timeout < 0:
            raise ValueError("recovery_timeout must be >= 0")

        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._clock = clock or time.monotonic

        self._state: CircuitState = CircuitState.CLOSED
        self._failure_count: int = 0
        self._opened_at: Optional[float] = None

    @property
    def state(self) -> CircuitState:
        if self._state is CircuitState.OPEN:
            if self._clock() - self._opened_at >= self._recovery_timeout:  # type: ignore[operator]
                self._state = CircuitState.HALF_OPEN
        return self._state

    @property
    def failure_count(self) -> int:
        return self._failure_count

    def allow_request(self) -> bool:
        """Return True if a request should be attempted."""
        return self.state in (CircuitState.CLOSED, CircuitState.HALF_OPEN)

    def record_success(self) -> None:
        """Reset the breaker after a successful call."""
        self._failure_count = 0
        self._opened_at = None
        self._state = CircuitState.CLOSED

    def record_failure(self) -> None:
        """Increment the failure counter and open the circuit if needed."""
        self._failure_count += 1
        if self._failure_count >= self._failure_threshold:
            self._state = CircuitState.OPEN
            self._opened_at = self._clock()

    def reset(self) -> None:
        """Manually reset the circuit breaker to a closed state."""
        self._failure_count = 0
        self._opened_at = None
        self._state = CircuitState.CLOSED
