from .base import BaseAgent
from ..schemas import CampaignBrief, ContentPiece


class WriterAgent(BaseAgent):
    """Drafts marketing copy for a given channel, brief, and (optionally) editor feedback."""

    CHANNELS = ["social_post", "email", "ad_copy"]

    def __init__(self):
        super().__init__(
            name="Writer",
            system_prompt=(
                "You are a marketing copywriter. Write on-brand marketing content "
                "for the given channel, audience and message. Keep it tight and punchy."
            ),
        )
        self._current_channel = "ad_copy"  # used only by the mock fallback

    def run(self, brief: CampaignBrief, channel: str, revision_notes: str = "") -> ContentPiece:
        self._current_channel = channel
        prompt = (
            f"Channel: {channel}\n"
            f"Target audience: {brief.target_audience}\n"
            f"Funnel stage: {brief.funnel_stage}\n"
            f"Key message: {brief.key_message}\n"
        )
        if revision_notes:
            prompt += f"\nEditor feedback to address: {revision_notes}\n"
        prompt += "\nWrite the content now."
        text = self._call_llm(prompt)
        return ContentPiece(channel=channel, text=text)

    def _mock_response(self, user_message: str) -> str:
        samples = {
            "social_post": "Real protein. Real taste. Zero compromises. Try it today. #FuelYourGains",
            "email": ("Subject: Your gains just got tastier\n\n"
                      "Meet the protein bar that finally doesn't taste like cardboard."),
            "ad_copy": "Stop settling for chalky protein bars. 20g of plant protein that actually tastes good.",
        }
        return samples.get(self._current_channel, "[MOCK CONTENT]")
