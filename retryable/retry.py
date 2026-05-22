"""Core retry decorator implementation."""

import time
import functools
from typing import Callable, Optional, Type

from retryable.backoff import constant
from retryable.hooks import HookRegistry, RetryEvent


def retry(
    max_attempts: int = 3,
    predicate: Optional[Callable] = None,
    backoff: Optional[Callable[[int], float]] = None,
    hooks: Optional[HookRegistry] = None,
    exceptions: tuple[Type[BaseException], ...] = (Exception,),
):
    """Decorator factory that adds retry logic to a function.

    Args:
        max_attempts: Maximum number of total attempts (including first call).
        predicate: Optional callable(result) -> bool; retry when True.
        backoff: Callable(attempt) -> float returning delay in seconds.
        hooks: Optional HookRegistry for lifecycle callbacks.
        exceptions: Tuple of exception types that trigger a retry.
    """
    if backoff is None:
        backoff = constant(0)
    if hooks is None:
        hooks = HookRegistry()

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            last_exc: Optional[BaseException] = None
            for attempt in range(1, max_attempts + 1):
                try:
                    result = fn(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    delay = backoff(attempt)
                    hooks.fire_retry(RetryEvent(attempt=attempt, delay=delay, exception=exc))
                    if attempt < max_attempts:
                        time.sleep(delay)
                    continue

                if predicate is not None and predicate(result):
                    delay = backoff(attempt)
                    hooks.fire_retry(RetryEvent(attempt=attempt, delay=delay, result=result))
                    if attempt < max_attempts:
                        time.sleep(delay)
                    continue

                hooks.fire_success(attempt, result)
                return result

            hooks.fire_failure(max_attempts, last_exc)
            if last_exc is not None:
                raise last_exc
            return result  # type: ignore[return-value]

        return wrapper
    return decorator
