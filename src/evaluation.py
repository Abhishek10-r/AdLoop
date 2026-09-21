"""
Metrics for checking the Editor (the LLM-as-a-judge) against human labels.

Labels are "pass" or "fail". "fail" is treated as the positive class: the
point of a judge is to catch the drafts that should not ship, and those are
the rare, costly cases, so precision and recall are reported for them.

Pure Python on purpose, so the metrics are unit-testable without an LLM.
"""
from typing import Dict, List

LABELS = ("pass", "fail")


def normalise(label: str) -> str:
    """Accepts pass/fail plus common spellings; raises on anything else."""
    value = str(label).strip().lower()
    if value in ("pass", "p", "approved", "approve", "yes", "y", "1", "true"):
        return "pass"
    if value in ("fail", "f", "rejected", "reject", "no", "n", "0", "false"):
        return "fail"
    raise ValueError(f"Unrecognised label {label!r}: use 'pass' or 'fail'")


def confusion(human: List[str], judge: List[str]) -> Dict[str, int]:
    """Counts with 'fail' as the positive class."""
    if len(human) != len(judge):
        raise ValueError("human and judge label lists must be the same length")
    counts = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
    for h, j in zip(human, judge):
        if j == "fail" and h == "fail":
            counts["tp"] += 1
        elif j == "fail" and h == "pass":
            counts["fp"] += 1
        elif j == "pass" and h == "fail":
            counts["fn"] += 1
        else:
            counts["tn"] += 1
    return counts


def _ratio(num: float, den: float) -> float:
    return num / den if den else 0.0


def cohen_kappa(human: List[str], judge: List[str]) -> float:
    """Agreement corrected for the agreement expected by chance."""
    n = len(human)
    if n == 0:
        return 0.0
    observed = sum(h == j for h, j in zip(human, judge)) / n
    expected = sum(
        (human.count(label) / n) * (judge.count(label) / n) for label in LABELS
    )
    if expected == 1.0:  # both raters used a single label throughout
        return 1.0 if observed == 1.0 else 0.0
    return (observed - expected) / (1 - expected)


def evaluate(human: List[str], judge: List[str]) -> Dict[str, float]:
    human = [normalise(x) for x in human]
    judge = [normalise(x) for x in judge]
    c = confusion(human, judge)
    precision = _ratio(c["tp"], c["tp"] + c["fp"])
    recall = _ratio(c["tp"], c["tp"] + c["fn"])
    return {
        "n": len(human),
        "human_fail_rate": _ratio(human.count("fail"), len(human)),
        "agreement": _ratio(c["tp"] + c["tn"], len(human)),
        "precision_fail": precision,
        "recall_fail": recall,
        "f1_fail": _ratio(2 * precision * recall, precision + recall),
        "cohen_kappa": cohen_kappa(human, judge),
        **c,
    }
