"""Tests for retryable.context.RetryContext."""

import time
import pytest
from retryable.context import RetryContext


class TestRetryContextDefaults:
    def test_attempt_starts_at_zero(self):
        ctx = RetryContext(max_attempts=3)
        assert ctx.attempt == 0

    def test_is_first_attempt_true_initially(self):
        ctx = RetryContext(max_attempts=3)
        assert ctx.is_first_attempt is True

    def test_is_first_attempt_false_after_advance(self):
        ctx = RetryContext(max_attempts=3).advance(delay=1.0)
        assert ctx.is_first_attempt is False

    def test_has_exception_false_by_default(self):
        ctx = RetryContext(max_attempts=3)
        assert ctx.has_exception is False

    def test_result_defaults_to_none(self):
        ctx = RetryContext(max_attempts=3)
        assert ctx.result is None

    def test_exception_defaults_to_none(self):
        ctx = RetryContext(max_attempts=3)
        assert ctx.exception is None


class TestRetryContextIsLastAttempt:
    def test_last_attempt_when_single_attempt(self):
        ctx = RetryContext(max_attempts=1)
        assert ctx.is_last_attempt is True

    def test_not_last_attempt_on_first_of_many(self):
        ctx = RetryContext(max_attempts=3)
        assert ctx.is_last_attempt is False

    def test_last_attempt_after_advancing_to_final(self):
        ctx = RetryContext(max_attempts=3)
        ctx = ctx.advance()
        ctx = ctx.advance()
        assert ctx.is_last_attempt is True


class TestRetryContextAdvance:
    def test_advance_increments_attempt(self):
        ctx = RetryContext(max_attempts=5)
        next_ctx = ctx.advance(delay=2.0)
        assert next_ctx.attempt == 1

    def test_advance_stores_delay(self):
        ctx = RetryContext(max_attempts=5)
        next_ctx = ctx.advance(delay=3.5)
        assert next_ctx.delay == 3.5

    def test_advance_preserves_max_attempts(self):
        ctx = RetryContext(max_attempts=5)
        next_ctx = ctx.advance()
        assert next_ctx.max_attempts == 5

    def test_advance_resets_exception(self):
        ctx = RetryContext(max_attempts=5).with_exception(ValueError("oops"))
        next_ctx = ctx.advance()
        assert next_ctx.exception is None


class TestRetryContextWithException:
    def test_with_exception_sets_exception(self):
        exc = RuntimeError("fail")
        ctx = RetryContext(max_attempts=3).with_exception(exc)
        assert ctx.exception is exc

    def test_with_exception_has_exception_true(self):
        ctx = RetryContext(max_attempts=3).with_exception(ValueError())
        assert ctx.has_exception is True

    def test_with_exception_clears_result(self):
        ctx = RetryContext(max_attempts=3, result="old").with_exception(ValueError())
        assert ctx.result is None


class TestRetryContextWithResult:
    def test_with_result_stores_value(self):
        ctx = RetryContext(max_attempts=3).with_result(42)
        assert ctx.result == 42

    def test_with_result_clears_exception(self):
        ctx = RetryContext(max_attempts=3).with_exception(ValueError()).with_result("ok")
        assert ctx.exception is None

    def test_with_result_has_exception_false(self):
        ctx = RetryContext(max_attempts=3).with_result("done")
        assert ctx.has_exception is False
