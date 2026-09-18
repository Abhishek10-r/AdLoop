"""
Basic tests, runnable with zero API key (everything here exercises MOCK_MODE
paths and pure functions — no network calls).

Run with:  pytest tests/
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils import safe_json_extract
from src.schemas import CampaignBrief, ContentPiece
from src.performance import generate_synthetic_performance
from src import config

config.MOCK_MODE = True  # force mock mode for these tests regardless of environment


def test_safe_json_extract_parses_clean_json():
    assert safe_json_extract('{"a": 1}', {}) == {"a": 1}


def test_safe_json_extract_parses_json_wrapped_in_prose():
    raw = 'Sure, here you go:\n{"approved": false, "notes": "too aggressive"}\nLet me know.'
    assert safe_json_extract(raw, {}) == {"approved": False, "notes": "too aggressive"}


def test_safe_json_extract_falls_back_on_garbage():
    assert safe_json_extract("not json at all", {"approved": True}) == {"approved": True}


def test_generate_synthetic_performance_shapes():
    pieces = [ContentPiece(channel="email", text="hi"), ContentPiece(channel="ad_copy", text="buy")]
    records = generate_synthetic_performance(pieces, seed=1)
    assert len(records) == 2
    assert all(0 <= r.ctr <= 1 for r in records)
    assert all(r.cac > 0 for r in records)


def test_researcher_agent_mock_mode_returns_string():
    from src.agents import ResearcherAgent
    agent = ResearcherAgent()
    result = agent.run("a test product")
    assert isinstance(result, str) and len(result) > 0


def test_strategist_agent_mock_mode_returns_brief():
    from src.agents import StrategistAgent
    agent = StrategistAgent()
    brief = agent.run("a test product", "some research")
    assert isinstance(brief, CampaignBrief)
    assert brief.funnel_stage in {"awareness", "consideration", "conversion"}


def test_full_campaign_runs_end_to_end_in_mock_mode():
    from src.orchestrator import MarketingTeamOrchestrator
    orch = MarketingTeamOrchestrator(max_revision_loops=1)
    result = orch.run_full_campaign("a test product", auto_approve_human=True)
    assert "round1_performance" in result
    assert "round2_performance" in result
    assert len(result["history"]) > 0
