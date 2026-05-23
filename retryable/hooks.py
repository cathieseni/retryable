"""Hooks for observing retry lifecycle events."""

from typing import Callable, Optional, Any
from dataclasses import dataclass, field


@dataclass
class RetryEvent:
    """Represents a single retry attempt event."""
    attempt: int
    delay: float
    exception: Optional[BaseException] = None
    result: Optional[Any] = None

    @property
    def has_exception(self) -> bool:
        return self.exception is not None


OnRetryHook = Callable[[RetryEvent], None]
OnSuccessHook = Callable[[int, Any], None]
OnFailureHook = Callable[[int, Optional[BaseException]], None]


@dataclass
class HookRegistry:
    """Registry that holds lifecycle hooks for retry operations."""
    on_retry: list[OnRetryHook] = field(default_factory=list)
    on_success: list[OnSuccessHook] = field(default_factory=list)
    on_failure: list[OnFailureHook] = field(default_factory=list)

    def register_on_retry(self, hook: OnRetryHook) -> None:
        """Register a hook called before each retry attempt."""
        self.on_retry.append(hook)

    def register_on_success(self, hook: OnSuccessHook) -> None:
        """Register a hook called when the operation eventually succeeds."""
        self.on_success.append(hook)

    def register_on_failure(self, hook: OnFailureHook) -> None:
        """Register a hook called when all retries are exhausted."""
        self.on_failure.append(hook)

    def fire_retry(self, event: RetryEvent) -> None:
        for hook in self.on_retry:
            hook(event)

    def fire_success(self, attempts: int, result: Any) -> None:
        for hook in self.on_success:
            hook(attempts, result)

    def fire_failure(self, attempts: int, last_exception: Optional[BaseException]) -> None:
        for hook in self.on_failure:
            hook(attempts, last_exception)

    def clear(self, hook_type: Optional[str] = None) -> None:
        """Remove registered hooks.

        Args:
            hook_type: One of ``'on_retry'``, ``'on_success'``, or
                ``'on_failure'``.  If *None*, all hook lists are cleared.

        Raises:
            ValueError: If an unrecognised *hook_type* is provided.
        """
        valid_types = {"on_retry", "on_success", "on_failure"}
        if hook_type is None:
            self.on_retry.clear()
            self.on_success.clear()
            self.on_failure.clear()
        elif hook_type in valid_types:
            getattr(self, hook_type).clear()
        else:
            raise ValueError(
                f"Unknown hook_type {hook_type!r}. Must be one of {sorted(valid_types)}."
            )
