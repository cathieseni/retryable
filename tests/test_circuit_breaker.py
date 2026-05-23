"""Tests for retryable.circuit_breaker."""

import pytest
from retryable.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitState,
)


class FakeClock:
    def __init__(self, start: float = 0.0) -> None:
        self._time = start

    def __call__(self) -> float:
        return self._time

    def advance(self, seconds: float) -> None:
        self._time += seconds


class TestCircuitBreakerInit:
    def test_initial_state_is_closed(self):
        cb = CircuitBreaker()
        assert cb.state is CircuitState.CLOSED

    def test_initial_failure_count_is_zero(self):
        cb = CircuitBreaker()
        assert cb.failure_count == 0

    def test_invalid_threshold_raises(self):
        with pytest.raises(ValueError):
            CircuitBreaker(failure_threshold=0)

    def test_negative_recovery_timeout_raises(self):
        with pytest.raises(ValueError):
            CircuitBreaker(recovery_timeout=-1)


class TestCircuitBreakerClosed:
    def test_allow_request_when_closed(self):
        cb = CircuitBreaker()
        assert cb.allow_request() is True

    def test_failure_below_threshold_stays_closed(self):
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        assert cb.state is CircuitState.CLOSED

    def test_failure_at_threshold_opens_circuit(self):
        cb = CircuitBreaker(failure_threshold=3)
        for _ in range(3):
            cb.record_failure()
        assert cb.state is CircuitState.OPEN

    def test_success_resets_failure_count(self):
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        assert cb.failure_count == 0
        assert cb.state is CircuitState.CLOSED


class TestCircuitBreakerOpen:
    def test_allow_request_false_when_open(self):
        clock = FakeClock()
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=30, clock=clock)
        cb.record_failure()
        assert cb.allow_request() is False

    def test_transitions_to_half_open_after_timeout(self):
        clock = FakeClock()
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=30, clock=clock)
        cb.record_failure()
        clock.advance(30)
        assert cb.state is CircuitState.HALF_OPEN

    def test_stays_open_before_timeout(self):
        clock = FakeClock()
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=30, clock=clock)
        cb.record_failure()
        clock.advance(29)
        assert cb.state is CircuitState.OPEN


class TestCircuitBreakerHalfOpen:
    def test_allow_request_true_when_half_open(self):
        clock = FakeClock()
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=10, clock=clock)
        cb.record_failure()
        clock.advance(10)
        assert cb.allow_request() is True

    def test_success_in_half_open_closes_circuit(self):
        clock = FakeClock()
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=10, clock=clock)
        cb.record_failure()
        clock.advance(10)
        cb.record_success()
        assert cb.state is CircuitState.CLOSED

    def test_failure_in_half_open_reopens_circuit(self):
        clock = FakeClock()
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=10, clock=clock)
        cb.record_failure()
        clock.advance(10)
        cb.record_failure()
        assert cb.state is CircuitState.OPEN


class TestCircuitBreakerReset:
    def test_reset_clears_state(self):
        cb = CircuitBreaker(failure_threshold=1)
        cb.record_failure()
        cb.reset()
        assert cb.state is CircuitState.CLOSED
        assert cb.failure_count == 0
