"""
The Manager/Orchestrator: coordinates the full workflow across two rounds,
decides whether content needs another writer pass, and briefs round two
using what the Analyst learned from round one. This is the piece that makes
the system agentic rather than a fixed script.
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .agents import ResearcherAgent, StrategistAgent, WriterAgent, EditorAgent, AnalystAgent
from .schemas import CampaignBrief, ContentPiece
from .performance import generate_synthetic_performance, human_checkpoint


class MarketingTeamOrchestrator:
    """
    Coordinates: research -> strategy -> (write <-> edit)* -> human approval ->
    synthetic performance -> analysis -> a second, learnings-informed round.
    Keeps a full audit trail of every step.
    """

    def __init__(self, max_revision_loops: int = 2):
        self.researcher = ResearcherAgent()
        self.strategist = StrategistAgent()
        self.writer = WriterAgent()
        self.editor = EditorAgent()
        self.analyst = AnalystAgent()
        self.max_revision_loops = max_revision_loops
        self.history: List[dict] = []

    def _log(self, step: str, detail: str):
        self.history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "step": step,
            "detail": detail,
        })

    def produce_content_with_review(self, brief: CampaignBrief, channel: str) -> ContentPiece:
        """The Writer <-> Editor loop for a single channel, capped at max_revision_loops."""
        revision_notes = ""
        content = None
        for loop in range(self.max_revision_loops + 1):
            content = self.writer.run(brief, channel, revision_notes)
            content = self.editor.run(content, brief)
            self._log("editor_review", f"{channel} loop {loop}: {content.status}")

            if content.status == "approved":
                content.revision_loops = loop
                return content

            revision_notes = content.revision_notes
            print(f"[Manager] {channel} sent back for revision (loop {loop + 1}): {revision_notes}")

        print(f"[Manager] Max revision loops reached for {channel}; flagging for manual review.")
        content.status = "approved_with_flag"
        content.revision_loops = self.max_revision_loops
        return content

    def run_round(
        self, product_description: str,
        brief: Optional[CampaignBrief] = None, learnings: str = "",
    ) -> Dict:
        if brief is None:
            print("[Manager] Kicking off Researcher...")
            research = self.researcher.run(product_description)
            self._log("research", research)

            print("[Manager] Kicking off Strategist...")
            brief = self.strategist.run(product_description, research)
            self._log("strategy", str(brief))
        else:
            print("[Manager] Round 2 — briefing with prior learnings...")
            brief.key_message = f"{brief.key_message} (Refined based on results: {learnings[:100]}...)"

        content_pieces = []
        for channel in WriterAgent.CHANNELS:
            print(f"[Manager] Producing + reviewing content for: {channel}")
            content_pieces.append(self.produce_content_with_review(brief, channel))

        return {"brief": brief, "content": content_pieces}

    def run_full_campaign(self, product_description: str, auto_approve_human: bool = True) -> Dict:
        print("=" * 60); print("ROUND 1"); print("=" * 60)
        round1 = self.run_round(product_description)

        approved = human_checkpoint(round1["content"], auto_approve=auto_approve_human)
        if not approved:
            print("[Manager] Human rejected round 1 content — stopping here.")
            return {"round1": round1}

        performance = generate_synthetic_performance(round1["content"], seed=42)
        self._log("performance_r1", str(performance))

        print("\n[Manager] Kicking off Analyst on round 1 performance...")
        learnings = self.analyst.run(performance)
        self._log("analysis", learnings)
        print(f"[Analyst] {learnings}")

        print("\n" + "=" * 60); print("ROUND 2 (informed by round 1 results)"); print("=" * 60)
        round2 = self.run_round(product_description, brief=round1["brief"], learnings=learnings)
        performance_r2 = generate_synthetic_performance(round2["content"], seed=99)
        self._log("performance_r2", str(performance_r2))

        return {
            "round1": round1, "round1_performance": performance,
            "round2": round2, "round2_performance": performance_r2,
            "learnings": learnings, "history": self.history,
        }
