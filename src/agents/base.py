"""Shared LLM-calling logic for every agent in the team."""
import time
from .. import config


class BaseAgent:
    """
    Retries with exponential backoff on transient API errors, and falls back
    to a mock response when config.MOCK_MODE is on (or no backend is configured).

    The call itself goes through whichever backend config.init() selected —
    Vertex AI (Gemini) or Anthropic (Claude) — so agents stay provider-agnostic.
    """

    def __init__(self, name: str, system_prompt: str, max_retries: int = 3):
        self.name = name
        self.system_prompt = system_prompt
        self.max_retries = max_retries

    def _call_llm(self, user_message: str) -> str:
        if config.MOCK_MODE:
            return self._mock_response(user_message)

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                return config.client.complete(
                    system_prompt=self.system_prompt,
                    user_message=user_message,
                    max_tokens=1024,
                )
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
