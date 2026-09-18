"""
Synthetic performance data + the human-in-the-loop approval gate.

Upgrade path: replace generate_synthetic_performance with a real connector
to the Meta Marketing API or Google Ads API — every downstream consumer
(the Analyst agent, the charts) only depends on the PerformanceRecord shape,
not on where the numbers came from.
"""
import random
from typing import List, Optional
from .schemas import ContentPiece, PerformanceRecord


def generate_synthetic_performance(
    content_pieces: List[ContentPiece], seed: Optional[int] = None
) -> List[PerformanceRecord]:
    """
    Produces believable, clearly-synthetic performance numbers per content piece.
    Channel-specific baselines keep the numbers plausible (email typically has
    much higher CTR than paid social/display, for instance).
    """
    rng = random.Random(seed)
    baseline = {"social_post": (0.02, 0.08), "email": (0.15, 0.25), "ad_copy": (0.01, 0.04)}
    records = []
    for piece in content_pieces:
        ctr_range = baseline.get(piece.channel, (0.01, 0.05))
        ctr = rng.uniform(*ctr_range)
        conversion_rate = ctr * rng.uniform(0.05, 0.2)
        cac = rng.uniform(8, 45)
        roas = rng.uniform(0.5, 4.5)
        records.append(PerformanceRecord(
            channel=piece.channel, ctr=ctr, conversion_rate=conversion_rate, cac=cac, roas=roas
        ))
    return records


def human_checkpoint(content_pieces: List[ContentPiece], auto_approve: bool = False) -> bool:
    """
    The governance gate: nothing is treated as 'published' without explicit approval.
    auto_approve=True lets a run finish non-interactively (e.g. in CI or 'Run All');
    set it to False to actually pause for real input().
    """
    print("\n--- HUMAN APPROVAL CHECKPOINT ---")
    for piece in content_pieces:
        print(f"\n[{piece.channel.upper()}] ({piece.status})\n{piece.text}\n")

    if auto_approve:
        print("Auto-approve mode ON — treating all content as approved.")
        return True

    answer = input("Approve this content for 'publishing'? (y/n): ").strip().lower()
    return answer == "y"
