"""retryable — Decorator-based retry library with backoff and jitter strategies."""

from retryable.retry import retry
from retryable.backoff import (
    constant,
    exponential,
    exponential_with_jitter,
    full_jitter,
)
from retryable.predicates import on_exception, on_result, on_predicate
from retryable.budget import RetryBudget
from retryable.hooks import RetryEvent, HookRegistry
from retryable.deadline import RetryDeadline
from retryable.context import RetryContext

__all__ = [
    "retry",
    # backoff strategies
    "constant",
    "exponential",
    "exponential_with_jitter",
    "full_jitter",
    # predicates
    "on_exception",
    "on_result",
    "on_predicate",
    # utilities
    "RetryBudget",
    "RetryEvent",
    "HookRegistry",
    "RetryDeadline",
    "RetryContext",
]
