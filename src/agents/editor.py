import json
import random
from .base import BaseAgent
from ..schemas import CampaignBrief, ContentPiece
from ..utils import safe_json_extract


class EditorAgent(BaseAgent):
    """Reviews a ContentPiece against the brief; approves or sends it back with notes."""

    def __init__(self):
        super().__init__(
            name="Editor",
            system_prompt=(
                'You are a brand editor. Review the content against the campaign brief. '
                'Respond with STRICT JSON: {"approved": true/false, "notes": "..."}. '
                "Reject if off-brand, off-message, or factually risky. Be concise."
            ),
        )

    def run(self, content: ContentPiece, brief: CampaignBrief) -> ContentPiece:
        prompt = (
            f"Campaign key message: {brief.key_message}\n"
            f"Audience: {brief.target_audience}\n"
            f"Content ({content.channel}):\n{content.text}\n\n"
            "Review and return the JSON verdict."
        )
        raw = self._call_llm(prompt)
        data = safe_json_extract(raw, {"approved": True, "notes": ""})
        content.status = "approved" if data.get("approved", True) else "needs_revision"
        content.revision_notes = data.get("notes", "")
        return content

    def _mock_response(self, user_message: str) -> str:
        # Approves ~70% of the time so the revision loop actually gets demonstrated on a typical run.
        approved = random.random() > 0.3
        notes = "" if approved else "Tone is slightly too aggressive for the target audience — soften the CTA."
        return json.dumps({"approved": approved, "notes": notes})
