"""Retry decorator with deadline (timeout) enforcement."""

from __future__ import annotations

import functools
import time
from typing import Callable, Optional, Type

from retryable.backoff import exponential_with_jitter
from retryable.deadline import RetryDeadline
from retryable.predicates import on_exception


def retry_with_deadline(
    timeout: float,
    *,
    max_attempts: int = 10,
    backoff: Callable[[int], float] = exponential_with_jitter,
    exceptions: tuple[Type[BaseException], ...] = (Exception,),
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> Callable:
    """Decorator that retries a function until a deadline is exceeded.

    Args:
        timeout: Maximum total time in seconds to keep retrying.
        max_attempts: Hard cap on the number of attempts regardless of time.
        backoff: Callable that receives the attempt number and returns delay.
        exceptions: Tuple of exception types that trigger a retry.
        sleep: Callable used to sleep between attempts (injectable for testing).
        clock: Callable returning current time in seconds (injectable for testing).

    Returns:
        A decorator that wraps the target function with retry-with-deadline logic.
    """
    should_retry = on_exception(*exceptions)

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            deadline = RetryDeadline(timeout=timeout, clock=clock)
            attempt = 0

            while True:
                try:
                    result = fn(*args, **kwargs)
                    return result
                except BaseException as exc:
                    attempt += 1

                    if not should_retry(exc):
                        raise

                    if attempt >= max_attempts:
                        raise

                    if deadline.is_expired():
                        raise TimeoutError(
                            f"Retry deadline of {timeout}s exceeded after "
                            f"{attempt} attempt(s)."
                        ) from exc

                    delay = backoff(attempt)
                    remaining = deadline.remaining()

                    # Do not sleep longer than the remaining deadline allows.
                    capped_delay = min(delay, remaining)
                    if capped_delay > 0:
                        sleep(capped_delay)

                    if deadline.is_expired():
                        raise TimeoutError(
                            f"Retry deadline of {timeout}s exceeded after "
                            f"{attempt} attempt(s)."
                        ) from exc

        return wrapper

    return decorator
