import pytest
from unittest.mock import MagicMock, patch, call

from retryable.retry import retry


class TestRetrySuccessOnFirstAttempt:
    def test_returns_value(self):
        @retry(max_attempts=3)
        def always_succeeds():
            return 42

        assert always_succeeds() == 42

    def test_called_once(self):
        mock_fn = MagicMock(return_value="ok")

        @retry(max_attempts=3)
        def fn():
            return mock_fn()

        fn()
        mock_fn.assert_called_once()


class TestRetryOnFailure:
    def test_retries_up_to_max_attempts(self):
        call_count = {"n": 0}

        @retry(max_attempts=3, backoff_strategy=lambda _: 0)
        def flaky():
            call_count["n"] += 1
            raise ValueError("fail")

        with pytest.raises(ValueError):
            flaky()

        assert call_count["n"] == 3

    def test_succeeds_on_second_attempt(self):
        results = iter([ValueError("first"), "success"])

        @retry(max_attempts=3, backoff_strategy=lambda _: 0)
        def sometimes_fails():
            val = next(results)
            if isinstance(val, Exception):
                raise val
            return val

        assert sometimes_fails() == "success"

    def test_raises_last_exception(self):
        @retry(max_attempts=2, backoff_strategy=lambda _: 0)
        def always_fails():
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            always_fails()


class TestRetryExceptionFiltering:
    def test_does_not_retry_unspecified_exception(self):
        call_count = {"n": 0}

        @retry(max_attempts=3, exceptions=ValueError, backoff_strategy=lambda _: 0)
        def raises_type_error():
            call_count["n"] += 1
            raise TypeError("wrong type")

        with pytest.raises(TypeError):
            raises_type_error()

        assert call_count["n"] == 1

    def test_retries_on_specified_exception(self):
        call_count = {"n": 0}

        @retry(max_attempts=3, exceptions=ValueError, backoff_strategy=lambda _: 0)
        def raises_value_error():
            call_count["n"] += 1
            raise ValueError("bad value")

        with pytest.raises(ValueError):
            raises_value_error()

        assert call_count["n"] == 3


class TestRetryCallbacks:
    def test_on_retry_called_on_each_retry(self):
        on_retry = MagicMock()

        @retry(max_attempts=3, backoff_strategy=lambda _: 0, on_retry=on_retry)
        def always_fails():
            raise ValueError("err")

        with pytest.raises(ValueError):
            always_fails()

        assert on_retry.call_count == 2

    def test_on_retry_receives_attempt_and_exception(self):
        received = []

        def capture(attempt, exc):
            received.append((attempt, exc))

        @retry(max_attempts=2, backoff_strategy=lambda _: 0, on_retry=capture)
        def always_fails():
            raise RuntimeError("oops")

        with pytest.raises(RuntimeError):
            always_fails()

        assert len(received) == 1
        assert received[0][0] == 1
        assert isinstance(received[0][1], RuntimeError)


class TestRetryBackoffSleep:
    def test_sleeps_with_backoff_delay(self):
        backoff = MagicMock(return_value=1.5)

        @retry(max_attempts=2, backoff_strategy=backoff)
        def always_fails():
            raise ValueError()

        with patch("retryable.retry.time.sleep") as mock_sleep:
            with pytest.raises(ValueError):
                always_fails()

            mock_sleep.assert_called_once_with(1.5)
