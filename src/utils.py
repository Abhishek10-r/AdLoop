"""Shared helpers used by more than one agent."""
import json
import re


def safe_json_extract(raw_text: str, fallback: dict) -> dict:
    """
    Pulls the first {...} JSON object out of a raw LLM response and parses it.
    Falls back to a safe default dict (rather than raising) if parsing fails,
    since a malformed structured-output response should degrade gracefully,
    not crash a multi-agent pipeline mid-run.
    """
    try:
        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        payload = match.group(0) if match else raw_text
        return json.loads(payload)
    except (json.JSONDecodeError, AttributeError) as e:
        print(f"[safe_json_extract] Falling back to defaults — could not parse: {e}")
        return fallback
