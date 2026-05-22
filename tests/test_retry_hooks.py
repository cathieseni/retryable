"""Integration tests for retry decorator with HookRegistry."""

import pytest
from retryable.retry import retry
from retryable.hooks import HookRegistry, RetryEvent


class TestRetryWithHooks:
    def test_on_retry_hook_called_on_exception(self):
        registry = HookRegistry()
        events = []
        registry.register_on_retry(lambda e: events.append(e))

        call_count = 0

        @retry(max_attempts=3, hooks=registry)
        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("not yet")
            return "done"

        result = flaky()
        assert result == "done"
        assert len(events) == 2
        assert all(isinstance(e, RetryEvent) for e in events)

    def test_on_success_hook_called_with_correct_attempts(self):
        registry = HookRegistry()
        success_calls = []
        registry.register_on_success(lambda a, r: success_calls.append((a, r)))

        @retry(max_attempts=3, hooks=registry)
        def always_succeeds():
            return 42

        always_succeeds()
        assert success_calls == [(1, 42)]

    def test_on_failure_hook_called_when_exhausted(self):
        registry = HookRegistry()
        failure_calls = []
        registry.register_on_failure(lambda a, e: failure_calls.append((a, e)))

        @retry(max_attempts=3, hooks=registry)
        def always_fails():
            raise RuntimeError("fail")

        with pytest.raises(RuntimeError):
            always_fails()

        assert len(failure_calls) == 1
        attempts, exc = failure_calls[0]
        assert attempts == 3
        assert isinstance(exc, RuntimeError)

    def test_retry_event_contains_exception(self):
        registry = HookRegistry()
        events = []
        registry.register_on_retry(lambda e: events.append(e))

        @retry(max_attempts=2, hooks=registry)
        def raises_once():
            if not events:
                raise TypeError("first")
            return "ok"

        raises_once()
        assert events[0].has_exception is True
        assert isinstance(events[0].exception, TypeError)

    def test_on_retry_hook_called_on_predicate_match(self):
        registry = HookRegistry()
        events = []
        registry.register_on_retry(lambda e: events.append(e))

        attempts = 0

        @retry(max_attempts=3, predicate=lambda r: r != "ready", hooks=registry)
        def eventually_ready():
            nonlocal attempts
            attempts += 1
            return "ready" if attempts >= 2 else "not ready"

        result = eventually_ready()
        assert result == "ready"
        assert len(events) == 1
        assert events[0].result == "not ready"
