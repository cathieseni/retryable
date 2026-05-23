"""Retry decorator with per-attempt timeout support."""

import functools
import signal
from typing import Callable, Optional, Type, Tuple

from retryable.backoff import exponential_with_jitter
from retryable.predicates import on_exception


class AttemptTimeoutError(Exception):
    """Raised when a single attempt exceeds its allowed timeout."""


def _timeout_handler(signum, frame):
    raise AttemptTimeoutError("Attempt timed out")


def retry_with_timeout(
    attempts: int = 3,
    attempt_timeout: float = 5.0,
    exceptions: Tuple[Type[BaseException], ...] = (Exception,),
    backoff: Callable[[int], float] = exponential_with_jitter(),
    sleep: Callable[[float], None] = None,
    on_retry: Optional[Callable] = None,
):
    """Retry decorator that enforces a per-attempt timeout using SIGALRM.

    Args:
        attempts: Maximum number of attempts.
        attempt_timeout: Seconds allowed per attempt before AttemptTimeoutError.
        exceptions: Exception types that trigger a retry.
        backoff: Callable returning delay in seconds given attempt number.
        sleep: Sleep function (defaults to time.sleep).
        on_retry: Optional callback invoked before each retry with (attempt, exc).
    """
    import time as _time

    _sleep = sleep if sleep is not None else _time.sleep
    should_retry = on_exception(*exceptions)

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, attempts + 1):
                old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
                signal.setitimer(signal.ITIMER_REAL, attempt_timeout)
                try:
                    result = fn(*args, **kwargs)
                    return result
                except AttemptTimeoutError as exc:
                    last_exc = exc
                    if on_retry is not None:
                        on_retry(attempt, exc)
                except BaseException as exc:
                    if not should_retry(exc):
                        raise
                    last_exc = exc
                    if on_retry is not None:
                        on_retry(attempt, exc)
                finally:
                    signal.setitimer(signal.ITIMER_REAL, 0)
                    signal.signal(signal.SIGALRM, old_handler)

                if attempt < attempts:
                    delay = backoff(attempt)
                    if delay > 0:
                        _sleep(delay)

            raise last_exc

        return wrapper

    return decorator
