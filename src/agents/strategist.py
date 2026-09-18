import json
from .base import BaseAgent
from ..schemas import CampaignBrief
from ..utils import safe_json_extract


class StrategistAgent(BaseAgent):
    """Turns product + research into a structured CampaignBrief."""

    def __init__(self):
        super().__init__(
            name="Strategist",
            system_prompt=(
                "You are a marketing strategist. Given a product and market research, "
                "produce a campaign brief as STRICT JSON with keys: "
                "target_audience, funnel_stage (one of: awareness, consideration, conversion), "
                "key_message, primary_kpi. No prose, JSON only."
            ),
        )

    def run(self, product_description: str, research_summary: str) -> CampaignBrief:
        prompt = (
            f"Product: {product_description}\nResearch: {research_summary}\n\n"
            "Return the campaign brief JSON."
        )
        raw = self._call_llm(prompt)
        fallback = {
            "target_audience": "general audience",
            "funnel_stage": "awareness",
            "key_message": f"Discover {product_description}.",
            "primary_kpi": "CTR",
        }
        data = safe_json_extract(raw, fallback)
        return CampaignBrief(
            product=product_description,
            target_audience=data.get("target_audience", fallback["target_audience"]),
            funnel_stage=data.get("funnel_stage", fallback["funnel_stage"]),
            key_message=data.get("key_message", fallback["key_message"]),
            primary_kpi=data.get("primary_kpi", fallback["primary_kpi"]),
        )

    def _mock_response(self, user_message: str) -> str:
        return json.dumps({
            "target_audience": "Health-conscious gym-goers aged 22-35",
            "funnel_stage": "consideration",
            "key_message": "Real protein, real taste, no compromises.",
            "primary_kpi": "conversion_rate",
        })
