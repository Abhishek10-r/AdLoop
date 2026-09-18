"""
Central configuration: which model to use, whether we're in MOCK_MODE,
and the shared Anthropic client. Every agent reads MOCK_MODE from this
module at call time (not via `from config import MOCK_MODE`, which would
freeze a stale copy), so setting it once here governs the whole pipeline.
"""
import os

MODEL = "claude-sonnet-5"  # swap for any current Claude model string
MOCK_MODE = False
client = None


def _load_api_key() -> str | None:
    """Tries Colab's secret manager first (if running there), then env var."""
    try:
        from google.colab import userdata  # type: ignore
        key = userdata.get("ANTHROPIC_API_KEY")
        if key:
            return key
    except Exception:
        pass
    return os.environ.get("ANTHROPIC_API_KEY")


def init():
    """Call this once at startup. Sets MOCK_MODE and the client as a side effect."""
    global MOCK_MODE, client

    try:
        import anthropic
    except ImportError:
        print("`anthropic` package not installed — forcing MOCK_MODE.")
        MOCK_MODE = True
        return

    api_key = _load_api_key()
    if not api_key:
        print("No ANTHROPIC_API_KEY found — running in MOCK_MODE "
              "(the full pipeline still runs end to end, using canned responses; "
              "no cost, no key needed).")
        MOCK_MODE = True
        return

    client = anthropic.Anthropic(api_key=api_key)
    MOCK_MODE = False
    print("Live API key detected — agents will call Claude for real.")


init()
