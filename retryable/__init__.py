"""retryable — Decorator-based retry library with backoff and jitter."""

from retryable.backoff import (
    constant,
    exponential,
    exponential_with_jitter,
    full_jitter,
)
from retryable.budget import RetryBudget, UnlimitedBudget
from retryable.predicates import (
    combine,
    on_exception,
    on_predicate,
    on_result,
)
from retryable.retry import retry

__all__ = [
    # core
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
    "combine",
    # budgets
    "RetryBudget",
    "UnlimitedBudget",
]
