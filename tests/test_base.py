import pytest

from src import config
from src.agents.base import BaseAgent, _is_permanent


class _ApiError(Exception):
    def __init__(self, code):
        super().__init__(f"HTTP {code}")
        self.code = code


class _FailingBackend:
    def __init__(self, code):
        self.code = code
        self.calls = 0

    def complete(self, system_prompt, user_message, max_tokens=1024):
        self.calls += 1
        raise _ApiError(self.code)


def test_permanent_errors_are_client_errors_except_rate_limits():
    assert _is_permanent(_ApiError(404))
    assert _is_permanent(_ApiError(401))
    assert not _is_permanent(_ApiError(429))
    assert not _is_permanent(_ApiError(503))
    assert not _is_permanent(ValueError("no code"))


def test_permanent_error_fails_fast_without_retrying(monkeypatch):
    backend = _FailingBackend(404)
    monkeypatch.setattr(config, "MOCK_MODE", False)
    monkeypatch.setattr(config, "client", backend)
    agent = BaseAgent("Test", "system")
    with pytest.raises(RuntimeError, match="not retrying"):
        agent._call_llm("hi")
    assert backend.calls == 1
