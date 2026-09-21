"""Shared LLM-calling logic for every agent in the team."""
import time
from .. import config


def _traceable(name: str):
    """
    Wraps a call so it shows up as a run in LangSmith when tracing is on
    (LANGSMITH_TRACING=true and LANGSMITH_API_KEY set). Without the langsmith
    package it's a no-op, so tracing never becomes a hard dependency.
    """
    try:
        from langsmith import traceable
    except ImportError:
        return lambda fn: fn
    return traceable(name=name, run_type="llm")


class BaseAgent:
    """
    Retries with exponential backoff on transient API errors, and falls back
    to a mock response when config.MOCK_MODE is on (or no backend is configured).

    The call itself goes through whichever backend config.init() selected —
    Vertex AI, the Gemini API or Anthropic — so agents stay provider-agnostic.
    Each call is traced to LangSmith under the agent's name when tracing is enabled.
    """

    def __init__(self, name: str, system_prompt: str, max_retries: int = 3):
        self.name = name
        self.system_prompt = system_prompt
        self.max_retries = max_retries
        self._complete = _traceable(name)(self._complete_once)

    def _complete_once(self, user_message: str) -> str:
        return config.client.complete(
            system_prompt=self.system_prompt,
            user_message=user_message,
            max_tokens=1024,
        )

    def _call_llm(self, user_message: str) -> str:
        if config.MOCK_MODE:
            return self._mock_response(user_message)

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                return self._complete(user_message)
            except Exception as e:
                last_error = e
                wait = 2 ** attempt
                print(f"[{self.name}] {config.PROVIDER} API error "
                      f"(attempt {attempt}/{self.max_retries}): {e}. "
                      f"Retrying in {wait}s...")
                time.sleep(wait)

        # Every retry failed — fail loudly rather than silently returning bad data.
        raise RuntimeError(f"{self.name} failed after {self.max_retries} attempts: {last_error}")

    def _mock_response(self, user_message: str) -> str:
        return "[MOCK OUTPUT]"

    def run(self, *args, **kwargs):
        raise NotImplementedError("Each agent must implement its own run().")
