from typing import List
from .base import BaseAgent
from ..schemas import PerformanceRecord


class AnalystAgent(BaseAgent):
    """Reads performance data and produces concrete recommendations for the next round."""

    def __init__(self):
        super().__init__(
            name="Analyst",
            system_prompt=(
                "You are a performance marketing analyst. Given performance metrics "
                "per channel, identify what worked, what didn't, and give 2-3 concrete "
                "recommendations for the next round of content. Be specific and concise."
            ),
        )

    def run(self, performance: List[PerformanceRecord]) -> str:
        lines = [
            f"{p.channel}: CTR={p.ctr:.2%}, Conversion={p.conversion_rate:.2%}, "
            f"CAC=${p.cac:.2f}, ROAS={p.roas:.2f}x"
            for p in performance
        ]
        prompt = "Performance data:\n" + "\n".join(lines) + "\n\nWhat should round 2 do differently?"
        return self._call_llm(prompt)

    def _mock_response(self, user_message: str) -> str:
        return (
            "Recommendations (mock): The email channel underperformed on conversion — "
            "sharpen the subject line and lead with the strongest benefit. "
            "Social had the best CTR — double down on that tone and format for ad copy too."
        )
