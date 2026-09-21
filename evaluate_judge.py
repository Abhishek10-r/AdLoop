"""
Measure how well the Editor agent (AdLoop's LLM-as-a-judge) agrees with a human.

Step 1 - generate drafts to label (needs a live LLM backend):
    python evaluate_judge.py generate

    Writes eval/to_label.csv. Half the rows pair a draft with the brief it was
    written for; the other half pair it with a different brief, so there are
    genuinely off-brief drafts for the judge to catch. Which is which is kept
    in eval/answer_key.csv, not in the file you label, so it can't bias you.

Step 2 - label it yourself:
    Open eval/to_label.csv and put "pass" or "fail" in the human_label column:
    would this draft be acceptable to ship for THIS brief?

Step 3 - score the judge (needs a live LLM backend):
    python evaluate_judge.py score

    Runs the Editor on every labelled row and prints agreement, precision,
    recall and F1 for catching "fail" drafts, and Cohen's kappa. Per-row
    verdicts are saved to eval/judge_results.csv.

MOCK_MODE is refused: the mock Editor approves at random, so its numbers
would be meaningless.
"""
import argparse
import csv
import random
import sys
from pathlib import Path

from src import config
from src.agents import EditorAgent, WriterAgent
from src.evaluation import evaluate, normalise
from src.schemas import CampaignBrief, ContentPiece

EVAL_DIR = Path("eval")
TO_LABEL = EVAL_DIR / "to_label.csv"
ANSWER_KEY = EVAL_DIR / "answer_key.csv"
RESULTS = EVAL_DIR / "judge_results.csv"

# Deliberately varied briefs, so a draft paired with the wrong one is clearly off-brief.
BRIEFS = [
    CampaignBrief("Plant-based protein bar", "Gym-goers aged 18-35", "consideration",
                  "20g of plant protein that actually tastes good", "CTR"),
    CampaignBrief("Retirement savings app", "Adults aged 50-65 planning retirement", "awareness",
                  "See exactly when you can afford to retire", "Sign-ups"),
    CampaignBrief("Kids' coding course", "Parents of children aged 8-12", "conversion",
                  "Your child builds their first game in 4 weeks", "Enrolments"),
    CampaignBrief("B2B cybersecurity audit", "IT directors at mid-sized firms", "consideration",
                  "Find your weak points before attackers do", "Demo requests"),
    CampaignBrief("Luxury skincare serum", "Women aged 30-50", "conversion",
                  "Visibly firmer skin in 28 days, dermatologist tested", "Purchases"),
    CampaignBrief("Budget airline flash sale", "Students and young travellers", "conversion",
                  "Flights across Europe from 19 euros this weekend only", "Bookings"),
    CampaignBrief("Electric cargo bike", "Urban parents doing the school run", "awareness",
                  "Replace the second car for the daily school run", "Test rides"),
    CampaignBrief("Online Dutch language course", "Expats who have just moved to the Netherlands", "consideration",
                  "Hold everyday conversations in Dutch within 3 months", "Trial starts"),
]
FIELDS = ["id", "product", "target_audience", "funnel_stage", "key_message", "channel", "text", "human_label"]


def _require_live_backend():
    if config.MOCK_MODE:
        sys.exit("A live LLM backend is required (set GOOGLE_CLOUD_PROJECT for Vertex AI, "
                 "or ANTHROPIC_API_KEY). The mock Editor approves at random.")


def generate(seed: int) -> None:
    _require_live_backend()
    rng = random.Random(seed)
    writer = WriterAgent()
    drafts = []
    for brief_idx, brief in enumerate(BRIEFS):
        for channel in WriterAgent.CHANNELS:
            print(f"Writing {channel} for: {brief.product}")
            drafts.append((brief_idx, channel, writer.run(brief, channel).text))

    rows, key = [], []
    for brief_idx, channel, text in drafts:
        # One row with the brief the draft was written for...
        rows.append((brief_idx, channel, text, "matched"))
        # ...and one with a different brief, so it should read as off-brief.
        other = rng.choice([i for i in range(len(BRIEFS)) if i != brief_idx])
        rows.append((other, channel, text, "mismatched"))
    rng.shuffle(rows)

    EVAL_DIR.mkdir(exist_ok=True)
    with TO_LABEL.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for i, (brief_idx, channel, text, pairing) in enumerate(rows, 1):
            b = BRIEFS[brief_idx]
            w.writerow({"id": i, "product": b.product, "target_audience": b.target_audience,
                        "funnel_stage": b.funnel_stage, "key_message": b.key_message,
                        "channel": channel, "text": text, "human_label": ""})
            key.append({"id": i, "pairing": pairing})
    with ANSWER_KEY.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "pairing"])
        w.writeheader()
        w.writerows(key)
    print(f"\nWrote {len(rows)} rows to {TO_LABEL}. Label the human_label column, then run: "
          f"python evaluate_judge.py score")


def score() -> None:
    _require_live_backend()
    if not TO_LABEL.exists():
        sys.exit(f"{TO_LABEL} not found - run 'python evaluate_judge.py generate' first.")
    with TO_LABEL.open(encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["human_label"].strip()]
    if not rows:
        sys.exit("No labelled rows yet - fill in the human_label column first.")

    editor = EditorAgent()
    human, judge, out = [], [], []
    for r in rows:
        brief = CampaignBrief(r["product"], r["target_audience"], r["funnel_stage"], r["key_message"])
        verdict = editor.run(ContentPiece(channel=r["channel"], text=r["text"]), brief)
        j = "pass" if verdict.status == "approved" else "fail"
        human.append(normalise(r["human_label"]))
        judge.append(j)
        out.append({"id": r["id"], "human_label": human[-1], "judge_label": j,
                    "judge_notes": verdict.revision_notes, "agree": human[-1] == j})

    with RESULTS.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "human_label", "judge_label", "judge_notes", "agree"])
        w.writeheader()
        w.writerows(out)

    m = evaluate(human, judge)
    print(f"\nLLM-as-a-judge vs human labels  ({config.PROVIDER}, n={m['n']})")
    print(f"  Human 'fail' rate      {m['human_fail_rate']:.0%}")
    print(f"  Agreement              {m['agreement']:.0%}")
    print(f"  Precision (fail)       {m['precision_fail']:.0%}   of drafts the judge failed, how many a human also failed")
    print(f"  Recall (fail)          {m['recall_fail']:.0%}   of drafts a human failed, how many the judge caught")
    print(f"  F1 (fail)              {m['f1_fail']:.2f}")
    print(f"  Cohen's kappa          {m['cohen_kappa']:.2f}   agreement beyond chance")
    print(f"  Confusion  TP={m['tp']} FP={m['fp']} FN={m['fn']} TN={m['tn']}")
    print(f"\nPer-row verdicts saved to {RESULTS}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate AdLoop's LLM-as-a-judge against human labels.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate", help="write drafts for you to label")
    g.add_argument("--seed", type=int, default=42)
    sub.add_parser("score", help="score the Editor against your labels")
    args = parser.parse_args()
    generate(args.seed) if args.cmd == "generate" else score()


if __name__ == "__main__":
    main()
