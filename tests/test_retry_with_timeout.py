"""Tests for retry_with_timeout decorator."""

import time
import pytest

from retryable.retry_with_timeout import retry_with_timeout, AttemptTimeoutError


def no_sleep(_delay):
    pass


def no_backoff(_attempt):
    return 0.0


class TestRetryWithTimeoutSuccess:
    def test_returns_value_on_first_success(self):
        @retry_with_timeout(attempts=3, attempt_timeout=2.0, backoff=no_backoff, sleep=no_sleep)
        def always_succeeds():
            return 42

        assert always_succeeds() == 42

    def test_called_once_on_success(self):
        calls = []

        @retry_with_timeout(attempts=3, attempt_timeout=2.0, backoff=no_backoff, sleep=no_sleep)
        def fn():
            calls.append(1)
            return "ok"

        fn()
        assert len(calls) == 1


class TestRetryWithTimeoutRetries:
    def test_retries_on_matching_exception(self):
        calls = []

        @retry_with_timeout(
            attempts=3,
            attempt_timeout=2.0,
            exceptions=(ValueError,),
            backoff=no_backoff,
            sleep=no_sleep,
        )
        def flaky():
            calls.append(1)
            if len(calls) < 3:
                raise ValueError("not yet")
            return "done"

        result = flaky()
        assert result == "done"
        assert len(calls) == 3

    def test_does_not_retry_on_unmatched_exception(self):
        calls = []

        @retry_with_timeout(
            attempts=3,
            attempt_timeout=2.0,
            exceptions=(ValueError,),
            backoff=no_backoff,
            sleep=no_sleep,
        )
        def fn():
            calls.append(1)
            raise TypeError("wrong type")

        with pytest.raises(TypeError):
            fn()
        assert len(calls) == 1

    def test_raises_last_exception_after_exhausting_attempts(self):
        @retry_with_timeout(
            attempts=3,
            attempt_timeout=2.0,
            exceptions=(RuntimeError,),
            backoff=no_backoff,
            sleep=no_sleep,
        )
        def always_fails():
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            always_fails()


class TestRetryWithTimeoutAttemptTimeout:
    def test_raises_attempt_timeout_error_on_slow_function(self):
        @retry_with_timeout(
            attempts=1,
            attempt_timeout=0.05,
            backoff=no_backoff,
            sleep=no_sleep,
        )
        def slow():
            time.sleep(5)
            return "never"

        with pytest.raises(AttemptTimeoutError):
            slow()

    def test_retries_after_timeout(self):
        calls = []

        @retry_with_timeout(
            attempts=3,
            attempt_timeout=0.05,
            backoff=no_backoff,
            sleep=no_sleep,
        )
        def sometimes_slow():
            calls.append(1)
            if len(calls) < 2:
                time.sleep(5)
            return "fast"

        result = sometimes_slow()
        assert result == "fast"
        assert len(calls) == 2


class TestRetryWithTimeoutOnRetryCallback:
    def test_on_retry_called_with_attempt_and_exception(self):
        events = []

        @retry_with_timeout(
            attempts=3,
            attempt_timeout=2.0,
            exceptions=(ValueError,),
            backoff=no_backoff,
            sleep=no_sleep,
            on_retry=lambda attempt, exc: events.append((attempt, exc)),
        )
        def flaky():
            if len(events) < 2:
                raise ValueError("retry me")
            return "ok"

        flaky()
        assert len(events) == 2
        assert all(isinstance(exc, ValueError) for _, exc in events)
