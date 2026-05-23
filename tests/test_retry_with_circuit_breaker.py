"""Integration tests for retry_with_circuit_breaker."""

import pytest
from retryable.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError, CircuitState
from retryable.retry_with_circuit_breaker import retry_with_circuit_breaker


class TestRetryWithCircuitBreakerSuccess:
    def test_returns_value_on_first_success(self):
        cb = CircuitBreaker(failure_threshold=3)

        @retry_with_circuit_breaker(cb, max_attempts=3)
        def always_succeeds():
            return 42

        assert always_succeeds() == 42

    def test_records_success_on_circuit_breaker(self):
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()  # one failure already

        @retry_with_circuit_breaker(cb, max_attempts=3)
        def succeeds():
            return "ok"

        succeeds()
        assert cb.failure_count == 0
        assert cb.state is CircuitState.CLOSED

    def test_retries_on_exception_then_succeeds(self):
        cb = CircuitBreaker(failure_threshold=5)
        calls = []

        @retry_with_circuit_breaker(cb, max_attempts=3)
        def flaky():
            calls.append(1)
            if len(calls) < 3:
                raise ValueError("not yet")
            return "done"

        result = flaky()
        assert result == "done"
        assert len(calls) == 3


class TestRetryWithCircuitBreakerFailure:
    def test_raises_last_exception_after_exhausting_attempts(self):
        cb = CircuitBreaker(failure_threshold=10)

        @retry_with_circuit_breaker(cb, max_attempts=3)
        def always_fails():
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            always_fails()

    def test_records_failure_on_circuit_breaker(self):
        cb = CircuitBreaker(failure_threshold=10)

        @retry_with_circuit_breaker(cb, max_attempts=2)
        def always_fails():
            raise ValueError("err")

        with pytest.raises(ValueError):
            always_fails()

        assert cb.failure_count == 2

    def test_opens_circuit_when_threshold_reached(self):
        cb = CircuitBreaker(failure_threshold=3)

        @retry_with_circuit_breaker(cb, max_attempts=3)
        def always_fails():
            raise RuntimeError("fail")

        with pytest.raises(RuntimeError):
            always_fails()

        assert cb.state is CircuitState.OPEN


class TestRetryWithOpenCircuit:
    def test_raises_circuit_breaker_open_error_immediately(self):
        cb = CircuitBreaker(failure_threshold=1)
        cb.record_failure()  # open the circuit

        call_count = 0

        @retry_with_circuit_breaker(cb, max_attempts=5)
        def fn():
            nonlocal call_count
            call_count += 1
            return "value"

        with pytest.raises(CircuitBreakerOpenError):
            fn()

        assert call_count == 0  # underlying fn never called


class TestRetryOnRetryCallback:
    def test_on_retry_called_between_attempts(self):
        cb = CircuitBreaker(failure_threshold=10)
        retries = []

        @retry_with_circuit_breaker(
            cb, max_attempts=3, on_retry=lambda attempt, exc: retries.append(attempt)
        )
        def flaky():
            if len(retries) < 2:
                raise ValueError("retry me")
            return "ok"

        result = flaky()
        assert result == "ok"
        assert retries == [1, 2]
