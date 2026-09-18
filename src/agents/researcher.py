from .base import BaseAgent


class ResearcherAgent(BaseAgent):
    """Looks up market/competitor context for the given product."""

    def __init__(self):
        super().__init__(
            name="Researcher",
            system_prompt=(
                "You are a market research analyst. Given a product description, "
                "produce a concise market/competitor summary: target market size, "
                "2-3 likely competitors and their positioning, and 2-3 audience pain points. "
                "Be specific and concise, under 200 words."
            ),
        )

    def run(self, product_description: str) -> str:
        prompt = f"Product: {product_description}\n\nProvide the market research summary."
        return self._call_llm(prompt)

    def _mock_response(self, user_message: str) -> str:
        return (
            "Market summary (mock): Growing niche market with 3 established competitors "
            "focused on convenience and taste. Audience pain points: price sensitivity, "
            "skepticism about health claims, decision fatigue from too many similar options."
        )
