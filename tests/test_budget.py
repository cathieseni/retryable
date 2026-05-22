"""Tests for retryable.budget."""

import threading

import pytest

from retryable.budget import RetryBudget, UnlimitedBudget


class TestRetryBudget:
    def test_initial_remaining_equals_total(self):
        budget = RetryBudget(5)
        assert budget.remaining == 5

    def test_acquire_decrements_remaining(self):
        budget = RetryBudget(3)
        budget.acquire()
        assert budget.remaining == 2

    def test_acquire_returns_true_while_tokens_available(self):
        budget = RetryBudget(2)
        assert budget.acquire() is True
        assert budget.acquire() is True

    def test_acquire_returns_false_when_exhausted(self):
        budget = RetryBudget(1)
        budget.acquire()
        assert budget.acquire() is False

    def test_remaining_never_goes_below_zero(self):
        budget = RetryBudget(1)
        budget.acquire()
        budget.acquire()  # extra call
        assert budget.remaining == 0

    def test_reset_restores_tokens(self):
        budget = RetryBudget(3)
        budget.acquire()
        budget.acquire()
        budget.reset()
        assert budget.remaining == 3

    def test_zero_budget_never_allows_retry(self):
        budget = RetryBudget(0)
        assert budget.acquire() is False

    def test_negative_total_raises(self):
        with pytest.raises(ValueError):
            RetryBudget(-1)

    def test_thread_safety(self):
        """Concurrent acquires must not over-spend the budget."""
        budget = RetryBudget(50)
        results = []
        lock = threading.Lock()

        def worker():
            result = budget.acquire()
            with lock:
                results.append(result)

        threads = [threading.Thread(target=worker) for _ in range(100)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert results.count(True) == 50
        assert results.count(False) == 50
        assert budget.remaining == 0


class TestUnlimitedBudget:
    def test_acquire_always_returns_true(self):
        budget = UnlimitedBudget()
        for _ in range(1000):
            assert budget.acquire() is True

    def test_total_is_none(self):
        assert UnlimitedBudget().total is None

    def test_remaining_is_none(self):
        assert UnlimitedBudget().remaining is None

    def test_reset_is_noop(self):
        UnlimitedBudget().reset()  # should not raise
