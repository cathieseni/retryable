"""Backoff strategy implementations for retry delays."""

import random
from typing import Optional


def constant(delay: float) -> float:
    """Return a constant delay regardless of attempt number."""
    return delay


def exponential(
    attempt: int,
    base_delay: float = 1.0,
    multiplier: float = 2.0,
    max_delay: Optional[float] = None,
) -> float:
    """Calculate exponential backoff delay.

    Args:
        attempt: The current attempt number (0-indexed).
        base_delay: The initial delay in seconds.
        multiplier: The factor by which the delay increases each attempt.
        max_delay: Optional cap on the maximum delay in seconds.

    Returns:
        Computed delay in seconds.
    """
    delay = base_delay * (multiplier ** attempt)
    if max_delay is not None:
        delay = min(delay, max_delay)
    return delay


def exponential_with_jitter(
    attempt: int,
    base_delay: float = 1.0,
    multiplier: float = 2.0,
    max_delay: Optional[float] = None,
    jitter_factor: float = 0.5,
) -> float:
    """Calculate exponential backoff delay with random jitter.

    Jitter helps avoid the thundering herd problem by randomising
    delays across concurrent retrying clients.

    Args:
        attempt: The current attempt number (0-indexed).
        base_delay: The initial delay in seconds.
        multiplier: The factor by which the delay increases each attempt.
        max_delay: Optional cap on the maximum delay in seconds.
        jitter_factor: Fraction of the computed delay to use as jitter range.
                       E.g. 0.5 means ±50% of the computed delay.

    Returns:
        Computed delay with jitter applied, in seconds.
    """
    delay = exponential(attempt, base_delay, multiplier, max_delay)
    jitter = delay * jitter_factor * (2 * random.random() - 1)
    return max(0.0, delay + jitter)


def full_jitter(
    attempt: int,
    base_delay: float = 1.0,
    multiplier: float = 2.0,
    max_delay: Optional[float] = None,
) -> float:
    """Calculate full-jitter backoff (uniform random between 0 and cap).

    This is the strategy recommended by AWS for distributed systems.

    Args:
        attempt: The current attempt number (0-indexed).
        base_delay: The initial delay in seconds.
        multiplier: The factor by which the cap increases each attempt.
        max_delay: Optional hard cap on the maximum delay in seconds.

    Returns:
        A uniformly random delay between 0 and the computed cap.
    """
    cap = exponential(attempt, base_delay, multiplier, max_delay)
    return random.uniform(0, cap)
