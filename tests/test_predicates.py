"""Tests for retryable.predicates."""

import pytest

from retryable.predicates import combine, on_exception, on_predicate, on_result


# ---------------------------------------------------------------------------
# on_exception
# ---------------------------------------------------------------------------


class TestOnException:
    def test_matches_exact_type(self):
        predicate = on_exception(ValueError)
        assert predicate(ValueError("boom")) is True

    def test_matches_subclass(self):
        predicate = on_exception(OSError)
        assert predicate(FileNotFoundError("missing")) is True

    def test_does_not_match_unrelated_type(self):
        predicate = on_exception(ValueError)
        assert predicate(TypeError("wrong")) is False

    def test_multiple_types(self):
        predicate = on_exception(ValueError, KeyError)
        assert predicate(ValueError()) is True
        assert predicate(KeyError()) is True
        assert predicate(RuntimeError()) is False

    def test_requires_at_least_one_type(self):
        with pytest.raises(ValueError):
            on_exception()

    def test_has_descriptive_name(self):
        predicate = on_exception(ValueError, KeyError)
        assert "ValueError" in predicate.__name__
        assert "KeyError" in predicate.__name__


# ---------------------------------------------------------------------------
# on_result
# ---------------------------------------------------------------------------


class TestOnResult:
    def test_matches_bad_result(self):
        predicate = on_result(None)
        assert predicate(None) is True

    def test_does_not_match_good_result(self):
        predicate = on_result(None)
        assert predicate(42) is False

    def test_works_with_custom_sentinel(self):
        sentinel = object()
        predicate = on_result(sentinel)
        assert predicate(sentinel) is True
        assert predicate(object()) is False

    def test_has_descriptive_name(self):
        predicate = on_result(-1)
        assert "-1" in predicate.__name__


# ---------------------------------------------------------------------------
# on_predicate
# ---------------------------------------------------------------------------


class TestOnPredicate:
    def test_returns_same_callable(self):
        fn = lambda x: x > 0  # noqa: E731
        assert on_predicate(fn) is fn

    def test_raises_on_non_callable(self):
        with pytest.raises(TypeError):
            on_predicate(42)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# combine
# ---------------------------------------------------------------------------


class TestCombine:
    def test_true_when_any_matches(self):
        combined = combine(on_result(None), on_result(-1))
        assert combined(None) is True
        assert combined(-1) is True

    def test_false_when_none_match(self):
        combined = combine(on_result(None), on_result(-1))
        assert combined(42) is False

    def test_requires_at_least_one_predicate(self):
        with pytest.raises(ValueError):
            combine()
