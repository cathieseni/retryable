import time
import functools
import logging
from typing import Callable, Optional, Tuple, Type, Union

from retryable.backoff import exponential_with_jitter

logger = logging.getLogger(__name__)

ExceptionTypes = Union[Type[Exception], Tuple[Type[Exception], ...]]


def retry(
    max_attempts: int = 3,
    exceptions: ExceptionTypes = Exception,
    backoff_strategy: Optional[Callable[[int], float]] = None,
    on_retry: Optional[Callable[[int, Exception], None]] = None,
):
    """
    Decorator that retries a function on failure with a configurable backoff strategy.

    :param max_attempts: Maximum number of attempts before giving up.
    :param exceptions: Exception type(s) that trigger a retry.
    :param backoff_strategy: Callable(attempt) -> seconds to sleep. Defaults to exponential_with_jitter.
    :param on_retry: Optional callback invoked on each retry with (attempt, exception).
    """
    if backoff_strategy is None:
        backoff_strategy = exponential_with_jitter()

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception: Optional[Exception] = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exception = exc
                    if attempt == max_attempts:
                        logger.warning(
                            "Function '%s' failed after %d attempt(s): %s",
                            func.__name__,
                            attempt,
                            exc,
                        )
                        raise
                    delay = backoff_strategy(attempt)
                    logger.debug(
                        "Attempt %d/%d for '%s' failed: %s. Retrying in %.2fs.",
                        attempt,
                        max_attempts,
                        func.__name__,
                        exc,
                        delay,
                    )
                    if on_retry is not None:
                        on_retry(attempt, exc)
                    time.sleep(delay)
            raise last_exception  # pragma: no cover

        return wrapper

    return decorator
