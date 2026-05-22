"""Tests for retryable.backoff strategy functions."""

import pytest
from unittest.mock import patch

from retryable.backoff import constant, exponential, exponential_with_jitter, full_jitter


class TestConstant:
    def test_returns_given_delay(self):
        assert constant(5.0) == 5.0

    def test_returns_zero(self):
        assert constant(0) == 0


class TestExponential:
    def test_first_attempt_returns_base_delay(self):
        assert exponential(0, base_delay=1.0) == 1.0

    def test_second_attempt_doubles_by_default(self):
        assert exponential(1, base_delay=1.0, multiplier=2.0) == 2.0

    def test_third_attempt(self):
        assert exponential(2, base_delay=1.0, multiplier=2.0) == 4.0

    def test_custom_multiplier(self):
        assert exponential(2, base_delay=2.0, multiplier=3.0) == 18.0

    def test_max_delay_caps_result(self):
        result = exponential(10, base_delay=1.0, multiplier=2.0, max_delay=30.0)
        assert result == 30.0

    def test_max_delay_not_exceeded(self):
        for attempt in range(20):
            assert exponential(attempt, base_delay=1.0, max_delay=60.0) <= 60.0

    def test_no_max_delay(self):
        result = exponential(10, base_delay=1.0, multiplier=2.0)
        assert result == 1024.0


class TestExponentialWithJitter:
    def test_result_is_non_negative(self):
        for attempt in range(10):
            assert exponential_with_jitter(attempt, base_delay=1.0) >= 0.0

    def test_result_within_expected_range(self):
        with patch("retryable.backoff.random.random", return_value=0.5):
            # jitter = delay * 0.5 * (2*0.5 - 1) = 0 => result == delay
            result = exponential_with_jitter(1, base_delay=1.0, multiplier=2.0)
            assert result == pytest.approx(2.0)

    def test_max_delay_respected_before_jitter(self):
        # Even with jitter, base cap should be applied before jitter
        with patch("retryable.backoff.random.random", return_value=1.0):
            result = exponential_with_jitter(
                10, base_delay=1.0, multiplier=2.0, max_delay=10.0, jitter_factor=0.5
            )
            # delay = 10, jitter = 10 * 0.5 * (2*1 - 1) = 5 => 15
            assert result == pytest.approx(15.0)


class TestFullJitter:
    def test_result_is_non_negative(self):
        for attempt in range(10):
            assert full_jitter(attempt, base_delay=1.0) >= 0.0

    def test_result_does_not_exceed_cap(self):
        with patch("retryable.backoff.random.uniform", side_effect=lambda a, b: b):
            result = full_jitter(3, base_delay=1.0, multiplier=2.0, max_delay=5.0)
            assert result <= 5.0

    def test_uniform_called_with_correct_range(self):
        with patch("retryable.backoff.random.uniform") as mock_uniform:
            mock_uniform.return_value = 3.0
            full_jitter(2, base_delay=1.0, multiplier=2.0)
            mock_uniform.assert_called_once_with(0, 4.0)
