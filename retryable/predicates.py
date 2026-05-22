"""Retry predicates for determining whether a retry should occur."""

from typing import Callable, Optional, Sequence, Type


def on_exception(
    *exception_types: Type[BaseException],
) -> Callable[[BaseException], bool]:
    """Return a predicate that retries on specific exception types.

    Args:
        *exception_types: Exception classes that should trigger a retry.

    Returns:
        A callable that accepts an exception and returns True if it matches
        any of the given exception types.
    """
    if not exception_types:
        raise ValueError("At least one exception type must be provided.")

    def predicate(exc: BaseException) -> bool:
        return isinstance(exc, tuple(exception_types))

    predicate.__name__ = "on_exception({})".format(
        ", ".join(t.__name__ for t in exception_types)
    )
    return predicate


def on_result(bad_result: object) -> Callable[[object], bool]:
    """Return a predicate that retries when the result equals *bad_result*.

    Args:
        bad_result: The sentinel value that should trigger a retry.

    Returns:
        A callable that accepts a return value and returns True when it
        equals *bad_result*.
    """

    def predicate(result: object) -> bool:
        return result == bad_result

    predicate.__name__ = f"on_result({bad_result!r})"
    return predicate


def on_predicate(fn: Callable[[object], bool]) -> Callable[[object], bool]:
    """Wrap an arbitrary callable as a result predicate.

    This is a thin wrapper that documents intent; it simply returns *fn*
    unchanged after validating that it is callable.

    Args:
        fn: A callable that accepts a result and returns True when a retry
            should occur.

    Returns:
        The same callable.
    """
    if not callable(fn):
        raise TypeError(f"Expected a callable, got {type(fn).__name__!r}")
    return fn


def combine(*predicates: Callable) -> Callable:
    """Combine multiple predicates with logical OR.

    A retry is triggered when *any* predicate returns True.

    Args:
        *predicates: Predicate callables to combine.

    Returns:
        A single callable that returns True if any predicate matches.
    """
    if not predicates:
        raise ValueError("At least one predicate must be provided.")

    def combined(value: object) -> bool:
        return any(p(value) for p in predicates)

    return combined
