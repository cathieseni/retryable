"""Tests for retryable.hooks module."""

import pytest
from retryable.hooks import RetryEvent, HookRegistry


class TestRetryEvent:
    def test_has_exception_true_when_exception_set(self):
        exc = ValueError("boom")
        event = RetryEvent(attempt=1, delay=0.5, exception=exc)
        assert event.has_exception is True

    def test_has_exception_false_when_no_exception(self):
        event = RetryEvent(attempt=1, delay=0.5)
        assert event.has_exception is False

    def test_result_defaults_to_none(self):
        event = RetryEvent(attempt=2, delay=1.0)
        assert event.result is None

    def test_exception_defaults_to_none(self):
        event = RetryEvent(attempt=1, delay=0.0)
        assert event.exception is None


class TestHookRegistry:
    def test_on_retry_hook_is_called(self):
        registry = HookRegistry()
        calls = []
        registry.register_on_retry(lambda e: calls.append(e))
        event = RetryEvent(attempt=1, delay=1.0)
        registry.fire_retry(event)
        assert len(calls) == 1
        assert calls[0] is event

    def test_multiple_on_retry_hooks_all_called(self):
        registry = HookRegistry()
        calls = []
        registry.register_on_retry(lambda e: calls.append("first"))
        registry.register_on_retry(lambda e: calls.append("second"))
        registry.fire_retry(RetryEvent(attempt=1, delay=0.0))
        assert calls == ["first", "second"]

    def test_on_success_hook_receives_attempts_and_result(self):
        registry = HookRegistry()
        received = []
        registry.register_on_success(lambda a, r: received.append((a, r)))
        registry.fire_success(3, "ok")
        assert received == [(3, "ok")]

    def test_on_failure_hook_receives_attempts_and_exception(self):
        registry = HookRegistry()
        received = []
        registry.register_on_failure(lambda a, e: received.append((a, e)))
        exc = RuntimeError("fail")
        registry.fire_failure(5, exc)
        assert received == [(5, exc)]

    def test_no_hooks_does_not_raise(self):
        registry = HookRegistry()
        registry.fire_retry(RetryEvent(attempt=1, delay=0.0))
        registry.fire_success(1, None)
        registry.fire_failure(1, None)

    def test_on_failure_hook_accepts_none_exception(self):
        registry = HookRegistry()
        received = []
        registry.register_on_failure(lambda a, e: received.append(e))
        registry.fire_failure(2, None)
        assert received == [None]
