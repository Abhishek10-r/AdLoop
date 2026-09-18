"""Typed records that pass between agents. See README for the full data flow."""
from dataclasses import dataclass


@dataclass
class CampaignBrief:
    """The strategist's output — the single source of truth every downstream agent reads from."""
    product: str
    target_audience: str = ""
    funnel_stage: str = ""      # "awareness" | "consideration" | "conversion"
    key_message: str = ""
    primary_kpi: str = ""


@dataclass
class ContentPiece:
    """One piece of marketing content moving through the writer -> editor loop."""
    channel: str                # "social_post" | "email" | "ad_copy"
    text: str
    status: str = "draft"       # draft | needs_revision | approved | approved_with_flag
    revision_notes: str = ""
    revision_loops: int = 0


@dataclass
class PerformanceRecord:
    """Synthetic (clearly-fake) performance numbers standing in for a real ads-platform report."""
    channel: str
    ctr: float
    conversion_rate: float
    cac: float
    roas: float
