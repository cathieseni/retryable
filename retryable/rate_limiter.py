"""Token bucket rate limiter for controlling retry attempt frequency."""

import time
from threading import Lock
from typing import Callable, Optional


class RateLimitExceededError(Exception):
    """Raised when the rate limiter cannot acquire a token."""
    pass


class TokenBucketRateLimiter:
    """A thread-safe token bucket rate limiter.

    Tokens are replenished at a fixed rate. Each retry attempt consumes one token.
    If no tokens are available, acquisition either blocks or raises an error.
    """

    def __init__(
        self,
        rate: float,
        capacity: int,
        clock: Optional[Callable[[], float]] = None,
    ) -> None:
        """
        Args:
            rate: Tokens replenished per second.
            capacity: Maximum number of tokens in the bucket.
            clock: Optional callable returning current time (for testing).
        """
        if rate <= 0:
            raise ValueError("rate must be positive")
        if capacity <= 0:
            raise ValueError("capacity must be positive")

        self._rate = rate
        self._capacity = capacity
        self._tokens = float(capacity)
        self._clock = clock or time.monotonic
        self._last_refill = self._clock()
        self._lock = Lock()

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def rate(self) -> float:
        return self._rate

    def _refill(self) -> None:
        now = self._clock()
        elapsed = now - self._last_refill
        added = elapsed * self._rate
        self._tokens = min(self._capacity, self._tokens + added)
        self._last_refill = now

    def acquire(self, blocking: bool = False) -> bool:
        """Attempt to acquire a token.

        Args:
            blocking: If True, wait until a token is available.
                      If False, return False immediately when no token available.

        Returns:
            True if a token was acquired, False otherwise.
        """
        with self._lock:
            self._refill()
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return True
            if not blocking:
                return False

        # Blocking path: wait outside the lock to allow refill
        wait_time = (1.0 - self._tokens) / self._rate
        time.sleep(wait_time)
        with self._lock:
            self._refill()
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return True
            return False

    def available_tokens(self) -> float:
        with self._lock:
            self._refill()
            return self._tokens
