"""
AdLoop — run a full two-round marketing campaign end to end.

Usage:
    python main.py "A plant-based protein bar aimed at gym-goers"

Runs in MOCK_MODE automatically if no ANTHROPIC_API_KEY is set (see src/config.py).
"""
import sys
import pandas as pd

from src.orchestrator import MarketingTeamOrchestrator
from src.visualizations import plot_round_comparison, plot_roas, plot_revision_loops
import matplotlib.pyplot as plt


def pipeline_metrics_summary(result: dict) -> pd.DataFrame:
    import numpy as np
    r1_content = result["round1"]["content"]
    r2_content = result["round2"]["content"]
    all_content = r1_content + r2_content

    avg_loops = sum(c.revision_loops for c in all_content) / len(all_content)
    ctr1 = np.mean([p.ctr for p in result["round1_performance"]])
    ctr2 = np.mean([p.ctr for p in result["round2_performance"]])
    conv1 = np.mean([p.conversion_rate for p in result["round1_performance"]])
    conv2 = np.mean([p.conversion_rate for p in result["round2_performance"]])

    return pd.DataFrame([{
        "avg_revision_loops_per_piece": round(avg_loops, 2),
        "round1_avg_ctr": f"{ctr1:.2%}",
        "round2_avg_ctr": f"{ctr2:.2%}",
        "ctr_change": f"{(ctr2 - ctr1) / ctr1 * 100:+.1f}%",
        "round1_avg_conversion": f"{conv1:.2%}",
        "round2_avg_conversion": f"{conv2:.2%}",
        "conversion_change": f"{(conv2 - conv1) / conv1 * 100:+.1f}%",
        "total_logged_agent_steps": len(result["history"]),
    }])


def main():
    product = sys.argv[1] if len(sys.argv) > 1 else "A plant-based protein bar aimed at gym-goers"

    orchestrator = MarketingTeamOrchestrator(max_revision_loops=2)
    result = orchestrator.run_full_campaign(product, auto_approve_human=True)

    if "round2_performance" not in result:
        print("Campaign stopped at the human checkpoint — nothing further to report.")
        return

    metrics_df = pipeline_metrics_summary(result)
    audit_df = pd.DataFrame(result["history"])

    audit_df.to_csv("agent_audit_trail.csv", index=False)
    metrics_df.to_csv("pipeline_metrics.csv", index=False)
    print(f"\nExported {len(audit_df)} audit-trail rows to agent_audit_trail.csv")
    print("Exported pipeline_metrics.csv")
    print("\n" + metrics_df.T.to_string())

    plot_round_comparison(result["round1_performance"], result["round2_performance"])
    plot_roas(result["round1_performance"], result["round2_performance"])
    plot_revision_loops(result["round1"]["content"], result["round2"]["content"])
    plt.show()


if __name__ == "__main__":
    main()
