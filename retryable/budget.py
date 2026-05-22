"""Retry budget — limits the total number of retry attempts across a process."""

import threading
from typing import Optional


class RetryBudget:
    """Thread-safe token bucket that caps the total retries allowed.

    A budget is shared across all callers that reference the same instance.
    Each failed attempt consumes one token; when the budget is exhausted no
    further retries are permitted.

    Args:
        total: Maximum number of retry tokens available.
    """

    def __init__(self, total: int) -> None:
        if total < 0:
            raise ValueError(f"total must be >= 0, got {total}")
        self._total = total
        self._remaining = total
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def total(self) -> int:
        """The initial token count."""
        return self._total

    @property
    def remaining(self) -> int:
        """Tokens still available (thread-safe snapshot)."""
        with self._lock:
            return self._remaining

    def acquire(self) -> bool:
        """Attempt to consume one retry token.

        Returns:
            True if a token was available and consumed; False otherwise.
        """
        with self._lock:
            if self._remaining > 0:
                self._remaining -= 1
                return True
            return False

    def reset(self) -> None:
        """Restore all tokens to the initial total."""
        with self._lock:
            self._remaining = self._total

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"{self.__class__.__name__}("
            f"total={self._total}, remaining={self.remaining})"
        )


class UnlimitedBudget:
    """A no-op budget that always allows retries."""

    @property
    def total(self) -> Optional[int]:
        return None

    @property
    def remaining(self) -> Optional[int]:
        return None

    def acquire(self) -> bool:
        return True

    def reset(self) -> None:
        pass
