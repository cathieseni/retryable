"""Retry decorator integrated with a TokenBucketRateLimiter."""

import time
from functools import wraps
from typing import Callable, Optional, Tuple, Type

from retryable.rate_limiter import TokenBucketRateLimiter, RateLimitExceededError
from retryable.backoff import constant


def retry_with_rate_limiter(
    rate_limiter: TokenBucketRateLimiter,
    max_attempts: int = 3,
    exceptions: Tuple[Type[BaseException], ...] = (Exception,),
    backoff: Optional[Callable[[int], float]] = None,
    on_rate_limit_exceeded: Optional[Callable[[], None]] = None,
) -> Callable:
    """Retry decorator that respects a shared token bucket rate limiter.

    Each attempt (including the first) must acquire a token from the rate limiter.
    If no token is available and blocking is disabled, a RateLimitExceededError
    is raised immediately.

    Args:
        rate_limiter: A TokenBucketRateLimiter instance shared across calls.
        max_attempts: Maximum number of total attempts.
        exceptions: Exception types that trigger a retry.
        backoff: Callable(attempt) -> seconds to sleep between retries.
        on_rate_limit_exceeded: Optional callback invoked when rate limit blocks a retry.

    Returns:
        A decorator that wraps a function with rate-limited retry logic.
    """
    if backoff is None:
        backoff = constant(0.0)

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_attempts):
                if not rate_limiter.acquire(blocking=False):
                    if on_rate_limit_exceeded is not None:
                        on_rate_limit_exceeded()
                    raise RateLimitExceededError(
                        f"Rate limit exceeded on attempt {attempt + 1}"
                    )

                try:
                    return fn(*args, **kwargs)
                except exceptions as exc:
                    last_exception = exc
                    if attempt < max_attempts - 1:
                        delay = backoff(attempt)
                        if delay > 0:
                            time.sleep(delay)

            raise last_exception

        return wrapper

    return decorator
