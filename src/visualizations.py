"""Chart functions used by main.py / the notebook to visualize a completed run."""
from typing import List
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from .schemas import PerformanceRecord, ContentPiece


def plot_architecture():
    """Renders the agent workflow as a labeled box-and-arrow diagram."""
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.axis("off")
    boxes = {
        "Manager\n(Orchestrator)": (0.5, 0.88),
        "Researcher": (0.12, 0.62),
        "Strategist": (0.37, 0.62),
        "Writer": (0.62, 0.62),
        "Editor": (0.87, 0.62),
        "Human\nCheckpoint": (0.5, 0.36),
        "Analyst": (0.5, 0.1),
    }
    for label, (x, y) in boxes.items():
        ax.add_patch(mpatches.FancyBboxPatch(
            (x - 0.09, y - 0.05), 0.18, 0.1,
            boxstyle="round,pad=0.01", facecolor="#EAF6F0",
            edgecolor="#1D8F63", linewidth=1.5,
        ))
        ax.text(x, y, label, ha="center", va="center", fontsize=9, color="#12161C")

    arrows = [
        ("Manager\n(Orchestrator)", "Researcher"), ("Manager\n(Orchestrator)", "Strategist"),
        ("Manager\n(Orchestrator)", "Writer"), ("Manager\n(Orchestrator)", "Editor"),
        ("Editor", "Human\nCheckpoint"), ("Human\nCheckpoint", "Analyst"),
        ("Analyst", "Manager\n(Orchestrator)"),
    ]
    for a, b in arrows:
        x1, y1 = boxes[a]
        x2, y2 = boxes[b]
        ax.annotate("", xy=(x2, y2 + 0.055), xytext=(x1, y1 - 0.055),
                    arrowprops=dict(arrowstyle="->", color="#2C6DA0", lw=1.3))

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title("Agent Workflow Architecture", fontsize=13, fontweight="bold")
    plt.tight_layout()
    return fig


def plot_round_comparison(perf_r1: List[PerformanceRecord], perf_r2: List[PerformanceRecord]):
    channels = [p.channel for p in perf_r1]
    x = np.arange(len(channels))
    width = 0.35

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    ctr1 = [p.ctr * 100 for p in perf_r1]
    ctr2 = [p.ctr * 100 for p in perf_r2]
    axes[0].bar(x - width / 2, ctr1, width, label="Round 1", color="#8C97AC")
    axes[0].bar(x + width / 2, ctr2, width, label="Round 2", color="#4ADE9E")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(channels)
    axes[0].set_ylabel("CTR (%)")
    axes[0].set_title("Click-Through Rate: Round 1 vs Round 2")
    axes[0].legend()

    conv1 = [p.conversion_rate * 100 for p in perf_r1]
    conv2 = [p.conversion_rate * 100 for p in perf_r2]
    axes[1].bar(x - width / 2, conv1, width, label="Round 1", color="#8C97AC")
    axes[1].bar(x + width / 2, conv2, width, label="Round 2", color="#5AA9E6")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(channels)
    axes[1].set_ylabel("Conversion Rate (%)")
    axes[1].set_title("Conversion Rate: Round 1 vs Round 2")
    axes[1].legend()

    plt.tight_layout()
    return fig


def plot_roas(perf_r1: List[PerformanceRecord], perf_r2: List[PerformanceRecord]):
    channels = [p.channel for p in perf_r1]
    x = np.arange(len(channels))
    width = 0.35
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(x - width / 2, [p.roas for p in perf_r1], width, label="Round 1", color="#8C97AC")
    ax.bar(x + width / 2, [p.roas for p in perf_r2], width, label="Round 2", color="#E8B84B")
    ax.axhline(1.0, color="gray", linestyle="--", linewidth=1, label="Breakeven (1.0x)")
    ax.set_xticks(x)
    ax.set_xticklabels(channels)
    ax.set_ylabel("ROAS (x)")
    ax.set_title("Return on Ad Spend by Channel")
    ax.legend()
    plt.tight_layout()
    return fig


def plot_revision_loops(round1_content: List[ContentPiece], round2_content: List[ContentPiece]):
    labels = [f"{c.channel} (R1)" for c in round1_content] + [f"{c.channel} (R2)" for c in round2_content]
    loops = [c.revision_loops for c in round1_content] + [c.revision_loops for c in round2_content]
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.barh(labels, loops, color="#5AA9E6")
    ax.set_xlabel("Revision loops needed before Editor approval")
    ax.set_title("Editor Revision Loops per Content Piece")
    plt.tight_layout()
    return fig
