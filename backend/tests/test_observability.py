import pytest

from src.services.ai.config import get_langfuse_callbacks, langfuse_enabled


def test_langfuse_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    assert langfuse_enabled() is False
    assert get_langfuse_callbacks() == []


def test_langfuse_enabled_requires_both_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    assert langfuse_enabled() is False


def test_langfuse_enabled_with_both_keys_returns_callback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    assert langfuse_enabled() is True
    callbacks = get_langfuse_callbacks()
    assert len(callbacks) == 1
