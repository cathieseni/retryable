"""Retry decorator that integrates with RetryBudget to limit total retry attempts
across multiple calls, rather than per-call attempt limits."""

from functools import wraps
from typing import Callable, Optional, Type, Tuple

from retryable.budget import RetryBudget
from retryable.backoff import constant
from retryable.context import RetryContext


def retry_with_budget(
    budget: RetryBudget,
    *,
    on: Tuple[Type[BaseException], ...] = (Exception,),
    backoff: Callable[[int], float] = constant(0.0),
    sleep: Callable[[float], None] = None,
    max_attempts: Optional[int] = None,
) -> Callable:
    """Decorator that retries a function while the shared budget has tokens.

    Args:
        budget: A shared RetryBudget instance controlling total retries allowed.
        on: Tuple of exception types that should trigger a retry.
        backoff: Callable accepting attempt number, returning seconds to wait.
        sleep: Callable used to sleep between retries (defaults to time.sleep).
        max_attempts: Optional per-call attempt cap (in addition to budget).
    """
    import time

    _sleep = sleep if sleep is not None else time.sleep

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            ctx = RetryContext(max_attempts=max_attempts)

            while True:
                try:
                    result = fn(*args, **kwargs)
                    budget.record_success()
                    return result
                except on as exc:
                    ctx.advance(exception=exc)

                    budget_available = budget.acquire()
                    per_call_exhausted = (
                        max_attempts is not None and ctx.attempt >= max_attempts
                    )

                    if not budget_available or per_call_exhausted:
                        raise

                    delay = backoff(ctx.attempt)
                    if delay > 0:
                        _sleep(delay)

        return wrapper

    return decorator
