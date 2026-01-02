"""
Visualization Standards - Publication-Quality Figures (Lightweight)
===================================================================

This module provides a small set of plotting helpers used by tournament scripts
under `src/network/*/tournament.py` and `src/memory/*/tournament.py`.

The emphasis is on:
- deterministic output (Agg backend recommended)
- avoiding hard dependencies on a specific plotting stack
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import matplotlib.pyplot as plt

try:  # optional
    import seaborn as sns  # type: ignore
except Exception:  # pragma: no cover
    sns = None


# Algorithm color palette (stable across runs)
ALGORITHM_COLORS: List[str] = [
    "#E74C3C",  # red
    "#3498DB",  # blue
    "#F39C12",  # orange
    "#27AE60",  # green
    "#9B59B6",  # purple
    "#34495E",  # dark
    "#1ABC9C",  # turquoise
    "#7F8C8D",  # gray
]


def setup_style() -> None:
    """Configure matplotlib (and seaborn if available) for clean output."""
    try:
        plt.style.use("seaborn-v0_8-whitegrid")
    except OSError:
        try:
            plt.style.use("seaborn-whitegrid")
        except OSError:
            pass

    if sns is not None:
        try:
            sns.set_palette(ALGORITHM_COLORS)
        except Exception:
            pass

    plt.rcParams.update(
        {
            "figure.dpi": 100,
            "savefig.dpi": 300,
            "axes.titlesize": 14,
            "axes.labelsize": 12,
            "legend.fontsize": 9,
        }
    )


def save_figure(
    fig: plt.Figure,
    output_dir: str,
    filename: str,
    formats: Sequence[str] = ("png",),
) -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    for fmt in formats:
        path = out / f"{filename}.{fmt}"
        dpi = 300 if fmt == "png" else None
        fig.savefig(path, format=fmt, dpi=dpi, bbox_inches="tight", facecolor="white", edgecolor="none")
        print(f"Saved: {path}")


def plot_queue_depth_histogram(
    *,
    data_by_algorithm: Dict[str, np.ndarray],
    buffer_capacity: float,
    output_dir: str,
    filename: str = "queue_depth_histogram",
    title: str = "Buffer Occupancy Distribution by Algorithm",
) -> plt.Figure:
    setup_style()
    fig, ax = plt.subplots(figsize=(10, 6))

    for i, (name, data) in enumerate(data_by_algorithm.items()):
        color = ALGORITHM_COLORS[i % len(ALGORITHM_COLORS)]
        ax.hist(np.asarray(data), bins=30, alpha=0.45, label=name, color=color)

    ax.axvline(buffer_capacity, color="black", linestyle="--", linewidth=1.2, alpha=0.8, label="Capacity")
    ax.set_title(title)
    ax.set_xlabel("Average Occupancy (fraction)")
    ax.set_ylabel("Count")
    ax.legend(loc="best", framealpha=0.9)
    fig.tight_layout()

    save_figure(fig, output_dir, filename)
    plt.close(fig)
    return fig


def plot_metric_comparison_bar(
    *,
    stats_by_algorithm: Dict[str, Tuple[float, float, float]],
    output_dir: str,
    filename: str,
    title: str,
    y_label: str,
    lower_is_better: bool = False,
) -> plt.Figure:
    setup_style()
    fig, ax = plt.subplots(figsize=(12, 6))

    items = list(stats_by_algorithm.items())
    # Sort by mean for readability
    items.sort(key=lambda kv: kv[1][0], reverse=not lower_is_better)

    names = [k for k, _ in items]
    means = np.array([v[0] for _, v in items], dtype=float)
    lows = np.array([v[1] for _, v in items], dtype=float)
    highs = np.array([v[2] for _, v in items], dtype=float)
    yerr = np.vstack([means - lows, highs - means])

    x = np.arange(len(names))
    colors = [ALGORITHM_COLORS[i % len(ALGORITHM_COLORS)] for i in range(len(names))]
    ax.bar(x, means, yerr=yerr, capsize=4, color=colors, alpha=0.85)

    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=25, ha="right")
    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.grid(True, axis="y", alpha=0.25)
    fig.tight_layout()

    save_figure(fig, output_dir, filename)
    plt.close(fig)
    return fig


def plot_drop_rate_comparison(**kwargs) -> plt.Figure:
    """Alias maintained for older scripts."""
    return plot_metric_comparison_bar(lower_is_better=True, **kwargs)


def plot_fairness_comparison(
    *,
    fairness_by_algorithm: Dict[str, float],
    output_dir: str,
    filename: str,
    title: str,
) -> plt.Figure:
    setup_style()
    fig, ax = plt.subplots(figsize=(10, 6))

    items = list(fairness_by_algorithm.items())
    items.sort(key=lambda kv: kv[1], reverse=True)

    names = [k for k, _ in items]
    vals = np.array([v for _, v in items], dtype=float)
    x = np.arange(len(names))
    colors = [ALGORITHM_COLORS[i % len(ALGORITHM_COLORS)] for i in range(len(names))]

    ax.bar(x, vals, color=colors, alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=25, ha="right")
    ax.set_ylim(0.0, 1.05)
    ax.set_ylabel("Jain's Fairness Index")
    ax.set_title(title)
    ax.grid(True, axis="y", alpha=0.25)
    fig.tight_layout()

    save_figure(fig, output_dir, filename)
    plt.close(fig)
    return fig


def plot_latency_cdf(
    *,
    data_by_algorithm: Dict[str, np.ndarray],
    output_dir: str,
    filename: str,
    title: str,
    x_label: str = "Latency",
    log_scale: bool = False,
    highlight_percentiles: Optional[Sequence[int]] = None,
) -> plt.Figure:
    setup_style()
    fig, ax = plt.subplots(figsize=(10, 6))

    for i, (name, data) in enumerate(data_by_algorithm.items()):
        arr = np.sort(np.asarray(data, dtype=float).ravel())
        if arr.size == 0:
            continue
        y = np.linspace(0.0, 1.0, arr.size, endpoint=True)
        ax.plot(arr, y, label=name, color=ALGORITHM_COLORS[i % len(ALGORITHM_COLORS)], linewidth=2)

    if log_scale:
        ax.set_xscale("log")

    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel("CDF")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best", framealpha=0.9)

    if highlight_percentiles:
        # Add horizontal lines at selected percentiles for reference
        for p in highlight_percentiles:
            ax.axhline(p / 100.0, color="#444444", linestyle=":", linewidth=0.8, alpha=0.6)

    fig.tight_layout()
    save_figure(fig, output_dir, filename)
    plt.close(fig)
    return fig


def plot_family_sextet(
    *,
    stats_by_algorithm: Dict[str, Dict[str, Tuple[float, float, float]]],
    output_dir: str,
    filename: str,
    title: str,
) -> plt.Figure:
    """
    Multi-metric summary plot.

    Callers typically pass 3 metrics (e.g. drop_rate/throughput/utilization).
    """
    setup_style()

    # Preserve metric order from first algorithm (if any)
    metrics: List[str] = []
    for _, per_metric in stats_by_algorithm.items():
        metrics = list(per_metric.keys())
        break

    if not metrics:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.set_title(title)
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
        save_figure(fig, output_dir, filename)
        plt.close(fig)
        return fig

    n = len(metrics)
    fig, axes = plt.subplots(1, n, figsize=(6 * n, 5))
    if n == 1:
        axes = [axes]

    algos = list(stats_by_algorithm.keys())
    colors = [ALGORITHM_COLORS[i % len(ALGORITHM_COLORS)] for i in range(len(algos))]

    for mi, metric in enumerate(metrics):
        ax = axes[mi]
        means = []
        yerr_lo = []
        yerr_hi = []
        for algo in algos:
            m, lo, hi = stats_by_algorithm[algo][metric]
            means.append(m)
            yerr_lo.append(m - lo)
            yerr_hi.append(hi - m)

        x = np.arange(len(algos))
        ax.bar(x, means, yerr=np.vstack([yerr_lo, yerr_hi]), capsize=4, color=colors, alpha=0.85)
        ax.set_xticks(x)
        ax.set_xticklabels(algos, rotation=25, ha="right")
        ax.set_title(metric)
        ax.grid(True, axis="y", alpha=0.25)

    fig.suptitle(title, fontsize=14)
    fig.tight_layout()
    save_figure(fig, output_dir, filename)
    plt.close(fig)
    return fig

