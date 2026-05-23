"""Integrates CircuitBreaker with the retry decorator.

Provides a convenience wrapper that wires a CircuitBreaker into the
existing retry machinery so that an open circuit causes an immediate
failure without consuming retry budget or sleeping.
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable, Optional, Type

from retryable.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from retryable.retry import retry


def retry_with_circuit_breaker(
    circuit_breaker: CircuitBreaker,
    *,
    max_attempts: int = 3,
    exceptions: tuple[Type[BaseException], ...] = (Exception,),
    backoff: Optional[Callable[[int], float]] = None,
    on_retry: Optional[Callable[..., None]] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator factory that combines retry logic with a circuit breaker.

    The decorated function will:
    1. Raise :class:`CircuitBreakerOpenError` immediately if the circuit is open.
    2. Record a success or failure on the circuit breaker after each call.
    3. Otherwise behave identically to the plain :func:`retry` decorator.

    Args:
        circuit_breaker: A :class:`CircuitBreaker` instance to consult.
        max_attempts: Maximum total call attempts.
        exceptions: Exception types that trigger a retry.
        backoff: Optional backoff callable ``(attempt: int) -> float``.
        on_retry: Optional callback invoked before each retry.
    """

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempt = 0
            last_exc: Optional[BaseException] = None

            while attempt < max_attempts:
                if not circuit_breaker.allow_request():
                    raise CircuitBreakerOpenError(
                        f"Circuit is open after {circuit_breaker.failure_count} "
                        "consecutive failures."
                    )

                try:
                    result = fn(*args, **kwargs)
                    circuit_breaker.record_success()
                    return result
                except exceptions as exc:  # type: ignore[misc]
                    circuit_breaker.record_failure()
                    last_exc = exc
                    attempt += 1

                    if attempt < max_attempts and on_retry is not None:
                        on_retry(attempt, exc)

                    if backoff is not None and attempt < max_attempts:
                        import time
                        delay = backoff(attempt)
                        if delay > 0:
                            time.sleep(delay)

            raise last_exc  # type: ignore[misc]

        return wrapper

    return decorator
