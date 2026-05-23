"""Tests for retry_with_budget decorator."""

import pytest
from unittest.mock import MagicMock, call

from retryable.budget import RetryBudget
from retryable.retry_with_budget import retry_with_budget


class TestRetryWithBudgetSuccess:
    def test_returns_value_on_first_success(self):
        budget = RetryBudget(total=5)

        @retry_with_budget(budget, sleep=lambda s: None)
        def always_succeeds():
            return 42

        assert always_succeeds() == 42

    def test_does_not_consume_budget_on_success(self):
        budget = RetryBudget(total=5)

        @retry_with_budget(budget, sleep=lambda s: None)
        def always_succeeds():
            return "ok"

        always_succeeds()
        assert budget.remaining == 5

    def test_retries_until_success(self):
        budget = RetryBudget(total=5)
        attempts = []

        @retry_with_budget(budget, sleep=lambda s: None)
        def flaky():
            attempts.append(1)
            if len(attempts) < 3:
                raise ValueError("not yet")
            return "done"

        result = flaky()
        assert result == "done"
        assert len(attempts) == 3

    def test_budget_decrements_on_each_retry(self):
        budget = RetryBudget(total=5)
        attempts = []

        @retry_with_budget(budget, sleep=lambda s: None)
        def flaky():
            attempts.append(1)
            if len(attempts) < 3:
                raise ValueError("fail")
            return "ok"

        flaky()
        assert budget.remaining == 3  # 5 - 2 retries consumed


class TestRetryWithBudgetExhausted:
    def test_raises_when_budget_exhausted(self):
        budget = RetryBudget(total=2)

        @retry_with_budget(budget, sleep=lambda s: None)
        def always_fails():
            raise RuntimeError("boom")

        # Drain the budget with first call
        with pytest.raises(RuntimeError):
            always_fails()

        assert budget.remaining == 0

        # Second call should fail immediately (no budget)
        with pytest.raises(RuntimeError):
            always_fails()

    def test_raises_when_max_attempts_reached(self):
        budget = RetryBudget(total=10)

        @retry_with_budget(budget, max_attempts=2, sleep=lambda s: None)
        def always_fails():
            raise ValueError("fail")

        with pytest.raises(ValueError):
            always_fails()

    def test_only_retries_on_specified_exception(self):
        budget = RetryBudget(total=5)

        @retry_with_budget(budget, on=(ValueError,), sleep=lambda s: None)
        def raises_runtime():
            raise RuntimeError("unexpected")

        with pytest.raises(RuntimeError):
            raises_runtime()

        # Budget should not have been consumed since exception didn't match
        assert budget.remaining == 5


class TestRetryWithBudgetBackoff:
    def test_sleep_called_between_retries(self):
        budget = RetryBudget(total=5)
        sleep_mock = MagicMock()
        attempts = []

        from retryable.backoff import constant

        @retry_with_budget(budget, backoff=constant(1.5), sleep=sleep_mock)
        def flaky():
            attempts.append(1)
            if len(attempts) < 3:
                raise ValueError("retry me")
            return "ok"

        flaky()
        assert sleep_mock.call_count == 2
        sleep_mock.assert_called_with(1.5)
