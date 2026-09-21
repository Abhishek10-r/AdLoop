"""
Central configuration: which LLM backend to use, whether we're in MOCK_MODE,
and the shared client.

Three backends are supported:

    LLM_PROVIDER=vertex      Gemini via Vertex AI on GCP     (application default
                                                              credentials + project id)
    LLM_PROVIDER=gemini      Gemini via the Gemini API       (GEMINI_API_KEY from
                                                              Google AI Studio)
    LLM_PROVIDER=anthropic   Claude via the Anthropic API    (ANTHROPIC_API_KEY)

Leave LLM_PROVIDER unset and the pipeline uses whichever is configured, in the
order above. If none is available it runs in MOCK_MODE: the whole
workflow still executes end to end on canned responses, with no key and no cost.

Every agent reads MOCK_MODE from this module at call time (not via
`from config import MOCK_MODE`, which would freeze a stale copy), so setting it
once here governs the whole pipeline.
"""
import os

# Model per backend.
MODEL = "claude-sonnet-5"          # Anthropic
# Google retires Gemini model versions regularly; override with GEMINI_MODEL
# rather than editing code when the default stops being available.
VERTEX_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")  # Vertex AI / Gemini API
VERTEX_LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

MOCK_MODE = False
PROVIDER = None   # "vertex" | "gemini" | "anthropic" | None while mocking
client = None     # backend instance exposing .complete(system, user, max_tokens)


def _load_api_key(name: str) -> str | None:
    """Tries Colab's secret manager first (if running there), then the environment."""
    try:
        from google.colab import userdata  # type: ignore
        key = userdata.get(name)
        if key:
            return key
    except Exception:
        pass
    return os.environ.get(name)


class VertexBackend:
    """
    Gemini via Vertex AI. Authenticates with application default credentials, so
    there is no API key to leak:

        gcloud auth application-default login
        export GOOGLE_CLOUD_PROJECT=your-project-id
    """

    name = "vertex"

    def __init__(self, project: str, location: str = VERTEX_LOCATION):
        from google import genai
        self._client = genai.Client(vertexai=True, project=project, location=location)

    def complete(self, system_prompt: str, user_message: str, max_tokens: int = 1024) -> str:
        from google.genai import types
        response = self._client.models.generate_content(
            model=VERTEX_MODEL,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=max_tokens,
            ),
        )
        return response.text


class GeminiBackend(VertexBackend):
    """
    Same Gemini models through the Gemini Developer API, authenticated with an
    API key from Google AI Studio - no Google Cloud project or gcloud needed.
    """

    name = "gemini"

    def __init__(self, api_key: str):
        from google import genai
        self._client = genai.Client(api_key=api_key)


class AnthropicBackend:
    """Claude via the Anthropic Messages API."""

    name = "anthropic"

    def __init__(self, api_key: str):
        import anthropic
        self._client = anthropic.Anthropic(api_key=api_key)

    def complete(self, system_prompt: str, user_message: str, max_tokens: int = 1024) -> str:
        response = self._client.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text


def _try_vertex() -> bool:
    """Returns True if the Vertex backend was configured successfully."""
    global client, PROVIDER

    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project:
        return False
    try:
        client = VertexBackend(project=project)
    except ImportError:
        print("`google-genai` not installed — skipping Vertex AI "
              "(pip install google-genai).")
        return False
    except Exception as e:
        print(f"Vertex AI unavailable ({e}) — skipping.")
        return False

    PROVIDER = "vertex"
    print(f"Vertex AI configured — agents will call {VERTEX_MODEL} "
          f"in project {project} ({VERTEX_LOCATION}).")
    return True


def _try_gemini() -> bool:
    """Returns True if the Gemini Developer API backend was configured successfully."""
    global client, PROVIDER

    api_key = _load_api_key("GEMINI_API_KEY") or _load_api_key("GOOGLE_API_KEY")
    if not api_key:
        return False
    try:
        client = GeminiBackend(api_key=api_key)
    except ImportError:
        print("`google-genai` not installed — skipping Gemini (pip install google-genai).")
        return False
    except Exception as e:
        print(f"Gemini API unavailable ({e}) — skipping.")
        return False

    PROVIDER = "gemini"
    print(f"Gemini API key detected — agents will call {VERTEX_MODEL}.")
    return True


def _try_anthropic() -> bool:
    """Returns True if the Anthropic backend was configured successfully."""
    global client, PROVIDER

    api_key = _load_api_key("ANTHROPIC_API_KEY")
    if not api_key:
        return False
    try:
        client = AnthropicBackend(api_key=api_key)
    except ImportError:
        print("`anthropic` package not installed — skipping Claude "
              "(pip install anthropic).")
        return False

    PROVIDER = "anthropic"
    print(f"Anthropic API key detected — agents will call {MODEL} for real.")
    return True


def init():
    """Call once at startup. Sets MOCK_MODE, PROVIDER and client as a side effect."""
    global MOCK_MODE, PROVIDER, client

    MOCK_MODE = False
    PROVIDER = None
    client = None

    requested = (os.environ.get("LLM_PROVIDER") or "").strip().lower()

    if requested == "vertex":
        ok = _try_vertex()
    elif requested == "gemini":
        ok = _try_gemini()
    elif requested == "anthropic":
        ok = _try_anthropic()
    elif requested in ("", "auto"):
        ok = _try_vertex() or _try_gemini() or _try_anthropic()
    else:
        print(f"Unknown LLM_PROVIDER={requested!r} — expected 'vertex', 'gemini' or 'anthropic'.")
        ok = False

    if not ok:
        print("No live LLM backend configured — running in MOCK_MODE "
              "(the full pipeline still runs end to end, using canned responses; "
              "no cost, no key needed).")
        MOCK_MODE = True


init()
