"""
Visualization Standards - Publication-Quality Figures
======================================================

This module provides standardized visualization functions for all
Portfolio B simulations. All figures follow these standards:

- Color Palette: Baseline=Red, Invention=Green, Alternatives=Blue/Orange
- Figure Size: 10x6 for histograms, 12x8 for multi-panel
- Font: 12pt labels, 14pt titles
- Export: PNG (300dpi) + SVG (vector) + PDF

Author: Portfolio B Research Team
License: Proprietary - Patent Pending
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
import warnings

# =============================================================================
# STYLE CONFIGURATION
# =============================================================================

# Color palette for algorithms
COLORS = {
    'baseline': '#E74C3C',      # Red - Baseline/No Control
    'invention': '#27AE60',      # Green - Our invention (best)
    'alternative1': '#3498DB',   # Blue - Alternative approach
    'alternative2': '#F39C12',   # Orange - Another alternative
    'alternative3': '#9B59B6',   # Purple - Third alternative
}

# Algorithm-specific colors (mapped by position in tournament)
ALGORITHM_COLORS = [
    '#E74C3C',  # First algo (usually baseline) - Red
    '#3498DB',  # Second algo - Blue
    '#F39C12',  # Third algo - Orange
    '#27AE60',  # Fourth algo (usually invention) - Green
    '#9B59B6',  # Fifth algo - Purple
    '#34495E',  # Sixth algo - Dark Blue
    '#1ABC9C',  # Seventh algo - Turquoise
]

# Seaborn style settings
STYLE_SETTINGS = {
    'font.size': 12,
    'axes.titlesize': 14,
    'axes.labelsize': 12,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.titlesize': 16,
    'axes.spines.top': False,
    'axes.spines.right': False,
}


def setup_style():
    """Configure matplotlib and seaborn for publication-quality output."""
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.rcParams.update(STYLE_SETTINGS)
    sns.set_palette(ALGORITHM_COLORS)

def format_time_ns(ns_val: float) -> str:
    """Format nanoseconds to most readable units (ns/us/ms)."""
    if ns_val < 1000.0:
        return f"{ns_val:.1f} ns"
    elif ns_val < 1_000_000.0:
        return f"{ns_val/1000.0:.1f} μs"
    else:
        return f"{ns_val/1_000_000.0:.1f} ms"


def save_figure(
    fig: plt.Figure,
    output_dir: str,
    filename: str,
    formats: List[str] = ['png', 'svg', 'pdf']
):
    """
    Save figure in multiple formats for maximum compatibility.
    
    Args:
        fig: Matplotlib figure object
        output_dir: Directory to save files
        filename: Base filename (without extension)
        formats: List of formats to export
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    for fmt in formats:
        filepath = output_path / f"{filename}.{fmt}"
        dpi = 300 if fmt == 'png' else None
        fig.savefig(filepath, format=fmt, dpi=dpi, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        print(f"Saved: {filepath}")


# =============================================================================
# HISTOGRAM VISUALIZATIONS
# =============================================================================

def plot_queue_depth_histogram(
    data_by_algorithm: Dict[str, np.ndarray],
    buffer_capacity: float,
    output_dir: str,
    filename: str = 'queue_depth_histogram',
    title: str = 'Buffer Occupancy Distribution by Algorithm'
) -> plt.Figure:
    """
    Create a histogram comparing queue depth distributions.
    """
    setup_style()
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Normalize to percentage of capacity
    for i, (algo_name, data) in enumerate(data_by_algorithm.items()):
        normalized = (data / buffer_capacity) * 100
        color = ALGORITHM_COLORS[i % len(ALGORITHM_COLORS)]
        
        ax.hist(normalized, bins=50, alpha=0.6, label=algo_name,
               color=color, edgecolor='white', linewidth=0.5)
    
    # Add vertical lines for key thresholds
    ax.axvline(x=80, color='green', linestyle='--', linewidth=2, 
              label='Optimal Threshold (80%)')
    ax.axvline(x=100, color='red', linestyle='--', linewidth=2,
              label='Buffer Full (100%)')
    
    ax.set_xlabel('Buffer Occupancy (%)')
    ax.set_ylabel('Frequency')
    ax.set_title(title)
    ax.legend(loc='upper left')
    ax.set_xlim(0, 110)
    
    # Add annotation
    ax.annotate(
        'DROP ZONE',
        xy=(105, ax.get_ylim()[1] * 0.8),
        fontsize=10,
        color='red',
        fontweight='bold',
        ha='center'
    )
    
    save_figure(fig, output_dir, filename)
    return fig


def plot_latency_cdf(
    data_by_algorithm: Dict[str, np.ndarray],
    output_dir: str,
    filename: str = 'latency_cdf',
    title: str = 'Request Latency CDF by Algorithm',
    x_label: str = 'Latency (μs)',
    log_scale: bool = True,
    highlight_percentiles: List[float] = [50, 95, 99]
) -> plt.Figure:
    """
    Create a Cumulative Distribution Function plot for latency comparison.
    """
    setup_style()
    fig, ax = plt.subplots(figsize=(10, 6))
    
    for i, (algo_name, data) in enumerate(data_by_algorithm.items()):
        sorted_data = np.sort(data)
        cdf = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
        color = ALGORITHM_COLORS[i % len(ALGORITHM_COLORS)]
        
        ax.plot(sorted_data, cdf, label=algo_name, color=color, linewidth=2)
        
        # Annotate key percentiles
        for pct in highlight_percentiles:
            idx = int(pct / 100 * len(sorted_data)) - 1
            if idx >= 0 and idx < len(sorted_data):
                val = sorted_data[idx]
                ax.scatter([val], [pct/100], color=color, s=50, zorder=5)
    
    if log_scale:
        ax.set_xscale('log')
    
    # Add horizontal lines for key percentiles
    for pct in highlight_percentiles:
        ax.axhline(y=pct/100, color='gray', linestyle=':', alpha=0.5)
        ax.text(ax.get_xlim()[0], pct/100 + 0.02, f'p{pct}', fontsize=9, color='gray')
    
    ax.set_xlabel(x_label)
    ax.set_ylabel('Cumulative Probability')
    ax.set_title(title)
    ax.legend(loc='lower right')
    ax.set_ylim(0, 1.05)
    
    save_figure(fig, output_dir, filename)
    return fig


def plot_sniper_cdf(
    data_by_algorithm: Dict[str, np.ndarray],
    output_dir: str,
    filename: str = 'sniper_latency_cdf',
    title: str = 'Sniper Isolation: Good Tenant vs Noisy Neighbor'
) -> plt.Figure:
    """
    Specifically contrasts Good Tenant vs Noisy Neighbor latency.
    Acceptance Criteria: Good Tenant stays < 50us.
    """
    setup_style()
    fig, ax = plt.subplots(figsize=(10, 6))
    
    for i, (label, data) in enumerate(data_by_algorithm.items()):
        sorted_data = np.sort(data)
        cdf = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
        color = ALGORITHM_COLORS[i % len(ALGORITHM_COLORS)]
        
        ax.plot(sorted_data, cdf, label=label, color=color, linewidth=3)

    ax.axvline(x=50, color='green', linestyle='--', alpha=0.5, label='Target Latency (50μs)')
    ax.set_xscale('log')
    ax.set_xlabel('Latency (μs)')
    ax.set_ylabel('CDF')
    ax.set_title(title)
    ax.legend(loc='lower right')
    
    save_figure(fig, output_dir, filename)
    return fig


def plot_throughput_recovery(
    time_series_by_algorithm: Dict[str, Tuple[np.ndarray, np.ndarray]],
    output_dir: str,
    filename: str = 'throughput_recovery',
    title: str = 'Throughput Recovery After Deadlock',
    deadlock_time: Optional[float] = None,
    recovery_time: Optional[float] = None
) -> plt.Figure:
    """
    Create a time series plot showing throughput before/during/after deadlock.
    """
    setup_style()
    fig, ax = plt.subplots(figsize=(12, 6))
    
    for i, (algo_name, (times, throughputs)) in enumerate(time_series_by_algorithm.items()):
        color = ALGORITHM_COLORS[i % len(ALGORITHM_COLORS)]
        ax.plot(times * 1000, throughputs, label=algo_name, color=color, linewidth=2)
    
    # Add shaded regions for deadlock and recovery
    if deadlock_time is not None:
        ax.axvline(x=deadlock_time * 1000, color='red', linestyle='--', 
                  linewidth=2, label='Deadlock Onset')
        ax.axvspan(deadlock_time * 1000, ax.get_xlim()[1], alpha=0.1, color='red')
    
    if recovery_time is not None:
        ax.axvline(x=recovery_time * 1000, color='green', linestyle='--',
                  linewidth=2, label='Recovery')
    
    ax.set_xlabel('Time (ms)')
    ax.set_ylabel('Throughput (Gbps)')
    ax.set_title(title)
    ax.legend(loc='lower right')
    ax.set_ylim(bottom=0)
    
    save_figure(fig, output_dir, filename)
    return fig


def plot_gantt_chart(
    jobs: List[Dict[str, Any]],
    output_dir: str,
    filename: str = 'gantt_chart',
    title: str = 'Job Execution Timeline'
) -> plt.Figure:
    """
    Create a Gantt chart showing job execution with local vs remote memory.
    """
    setup_style()
    fig, ax = plt.subplots(figsize=(12, max(6, len(jobs) * 0.5)))
    
    y_positions = list(range(len(jobs)))
    
    for i, job in enumerate(jobs):
        if job['status'] == 'crashed':
            duration = job.get('crash_time', job['start'] + 1) - job['start']
            ax.barh(i, duration, left=job['start'], height=0.6,
                   color='#E74C3C', edgecolor='black', linewidth=1)
            ax.text(job['start'] + duration/2, i, 'CRASH',
                   ha='center', va='center', color='white', fontweight='bold')
        else:
            total_duration = job['end'] - job['start']
            local_fraction = job['local_memory'] / (job['local_memory'] + job.get('remote_memory', 1))
            local_duration = total_duration * local_fraction
            ax.barh(i, local_duration, left=job['start'], height=0.6,
                   color='#27AE60', edgecolor='black', linewidth=1, label='Local' if i == 0 else '')
            if job.get('remote_memory', 0) > 0:
                ax.barh(i, total_duration - local_duration, 
                       left=job['start'] + local_duration, height=0.6,
                       color='#F1C40F', edgecolor='black', linewidth=1, 
                       label='Remote' if i == 0 else '')
    
    ax.set_yticks(y_positions)
    ax.set_yticklabels([job['name'] for job in jobs])
    ax.set_xlabel('Time (s)')
    ax.set_title(title)
    ax.legend(loc='upper right')
    ax.invert_yaxis()
    
    save_figure(fig, output_dir, filename)
    return fig


def plot_metric_comparison_bar(
    stats_by_algorithm: Dict[str, Tuple[float, float, float]],
    output_dir: str,
    filename: str = 'metric_comparison',
    title: str = 'Algorithm Comparison',
    y_label: str = 'Metric Value',
    highlight_best: bool = True,
    lower_is_better: bool = False
) -> plt.Figure:
    """
    Create a bar chart comparing algorithms with confidence intervals.
    """
    setup_style()
    fig, ax = plt.subplots(figsize=(10, 6))
    
    names = list(stats_by_algorithm.keys())
    means = [stats_by_algorithm[n][0] for n in names]
    ci_lowers = [stats_by_algorithm[n][1] for n in names]
    ci_uppers = [stats_by_algorithm[n][2] for n in names]
    
    errors = [[m - l for m, l in zip(means, ci_lowers)],
              [u - m for m, u in zip(means, ci_uppers)]]
    
    if lower_is_better:
        best_idx = means.index(min(means))
    else:
        best_idx = means.index(max(means))
    
    colors = []
    for i in range(len(names)):
        if highlight_best and i == best_idx:
            colors.append('#27AE60')
        else:
            colors.append(ALGORITHM_COLORS[i % len(ALGORITHM_COLORS)])
    
    x_pos = np.arange(len(names))
    bars = ax.bar(x_pos, means, yerr=errors, capsize=5, color=colors,
                 edgecolor='black', linewidth=1, alpha=0.8)
    
    ax.set_xticks(x_pos)
    ax.set_xticklabels(names, rotation=15, ha='right')
    ax.set_ylabel(y_label)
    ax.set_title(title)
    
    save_figure(fig, output_dir, filename)
    return fig


def plot_fairness_comparison(
    fairness_by_algorithm: Dict[str, float],
    output_dir: str,
    filename: str = 'fairness_comparison',
    title: str = "Jain's Fairness Index by Algorithm"
) -> plt.Figure:
    """
    Create a bar chart comparing fairness scores.
    """
    setup_style()
    fig, ax = plt.subplots(figsize=(10, 6))
    
    names = list(fairness_by_algorithm.keys())
    scores = [fairness_by_algorithm[n] for n in names]
    
    colors = []
    for score in scores:
        if score >= 0.9: colors.append('#27AE60')
        elif score >= 0.7: colors.append('#F39C12')
        else: colors.append('#E74C3C')
    
    x_pos = np.arange(len(names))
    bars = ax.bar(x_pos, scores, color=colors, edgecolor='black', linewidth=1)
    
    ax.set_xticks(x_pos)
    ax.set_xticklabels(names, rotation=15, ha='right')
    ax.set_ylabel("Jain's Fairness Index")
    ax.set_title(title)
    ax.set_ylim(0, 1.15)
    
    save_figure(fig, output_dir, filename)
    return fig


def plot_heatmap(
    data: np.ndarray,
    x_labels: List[str],
    y_labels: List[str],
    output_dir: str,
    filename: str = 'heatmap',
    title: str = 'Heatmap',
    x_label: str = 'X',
    y_label: str = 'Y',
    cmap: str = 'RdYlGn',
    annotate: bool = True
) -> plt.Figure:
    """
    Create a heatmap for 2D parameter exploration.
    """
    setup_style()
    fig, ax = plt.subplots(figsize=(10, 8))
    
    sns.heatmap(data, ax=ax, cmap=cmap, annot=annotate, fmt='.2f',
               xticklabels=x_labels, yticklabels=y_labels,
               cbar_kws={'label': 'Value'}, linewidths=0.5)
    
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)
    
    save_figure(fig, output_dir, filename)
    return fig


def plot_drop_rate_comparison(
    thresholds: List[float],
    drop_rates_by_algorithm: Dict[str, List[float]],
    output_dir: str,
    filename: str = 'drop_rate_comparison',
    title: str = 'Drop Rate vs Backpressure Threshold'
) -> plt.Figure:
    """
    Create a line plot showing drop rate across threshold values.
    """
    setup_style()
    fig, ax = plt.subplots(figsize=(10, 6))
    
    for i, (algo_name, drop_rates) in enumerate(drop_rates_by_algorithm.items()):
        color = ALGORITHM_COLORS[i % len(ALGORITHM_COLORS)]
        ax.plot(thresholds, drop_rates, marker='o', label=algo_name, 
               color=color, linewidth=2, markersize=8)
    
    ax.set_xlabel('Backpressure Threshold (%)')
    ax.set_ylabel('Drop Rate (%)')
    ax.set_title(title)
    ax.legend(loc='upper right')
    ax.set_ylim(bottom=0)
    
    save_figure(fig, output_dir, filename)
    return fig


def plot_family_sextet(
    stats_by_algorithm: Dict[str, Dict[str, Tuple[float, float, float]]],
    output_dir: str,
    filename: str,
    title: str
) -> plt.Figure:
    """
    Creates a 2x3 grid of bar charts for a patent family (The Sextet).
    Each subplot shows a different variation against the baseline.
    """
    setup_style()
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    axes = axes.flatten()
    
    algo_names = list(stats_by_algorithm.keys())
    # Baseline is assumed to be the first one
    baseline_name = algo_names[0]
    
    # Variations are 1 to N
    plot_idx = 0
    for i in range(1, len(algo_names)):
        if plot_idx >= 6: break
        
        ax = axes[plot_idx]
        name = algo_names[i]
        
        metrics = list(stats_by_algorithm[name].keys())
        if not metrics: continue
        primary_metric = metrics[0]
        
        b_stats = stats_by_algorithm[baseline_name].get(primary_metric)
        v_stats = stats_by_algorithm[name].get(primary_metric)
        
        if not b_stats or not v_stats:
            continue
            
        b_mean, b_low, b_high = b_stats
        v_mean, v_low, v_high = v_stats
        
        # Shorten name for plot
        short_name = name.split('(')[-1].replace(')', '')
        if len(short_name) > 15: short_name = short_name[:12] + "..."
        
        labels = ['Baseline', short_name]
        means = [b_mean, v_mean]
        errors = [[max(0, b_mean-b_low), max(0, v_mean-v_low)], 
                  [max(0, b_high-b_mean), max(0, v_high-v_mean)]]
        
        ax.bar(labels, means, yerr=errors, capsize=5, 
               color=[ALGORITHM_COLORS[0], ALGORITHM_COLORS[3]], alpha=0.8)
        ax.set_title(f"Var {plot_idx+1}: {name.split('(')[-1].replace(')', '')}")
        ax.set_ylabel(primary_metric.replace('_', ' ').title())
        
        plot_idx += 1
        
    for j in range(plot_idx, 6):
        axes[j].axis('off')
        
    fig.suptitle(title, fontsize=22, fontweight='bold')
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    save_figure(fig, output_dir, filename)
    return fig


def plot_family_sextet(
    stats_by_algorithm: Dict[str, Dict[str, Tuple[float, float, float]]],
    output_dir: str,
    filename: str,
    title: str
) -> plt.Figure:
    """
    Creates a 2x3 grid of bar charts for a patent family (The Sextet).
    Each subplot shows a different variation against the baseline.
    """
    setup_style()
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    axes = axes.flatten()
    
    algo_names = list(stats_by_algorithm.keys())
    baseline_name = algo_names[0]
    
    plot_idx = 0
    for i in range(1, len(algo_names)):
        if plot_idx >= 6: break
        
        ax = axes[plot_idx]
        name = algo_names[i]
        
        metrics = list(stats_by_algorithm[name].keys())
        primary_metric = metrics[0]
        
        b_stats = stats_by_algorithm[baseline_name].get(primary_metric)
        v_stats = stats_by_algorithm[name].get(primary_metric)
        
        if not b_stats or not v_stats:
            continue
            
        b_mean, b_low, b_high = b_stats
        v_mean, v_low, v_high = v_stats
        
        labels = ['Baseline', name.split('(')[-1].replace(')', '')]
        means = [b_mean, v_mean]
        errors = [[max(0, b_mean-b_low), max(0, v_mean-v_low)], [max(0, b_high-b_mean), max(0, v_high-v_mean)]]
        
        ax.bar(labels, means, yerr=errors, capsize=5, color=[ALGORITHM_COLORS[0], ALGORITHM_COLORS[3]], alpha=0.8)
        ax.set_title(f"Variation {plot_idx+1}: {name.split('(')[-1].replace(')', '')}")
        ax.set_ylabel(primary_metric.replace('_', ' ').title())
        
        plot_idx += 1
        
    for j in range(plot_idx, 6):
        axes[j].axis('off')
        
    fig.suptitle(title, fontsize=20, fontweight='bold')
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    save_figure(fig, output_dir, filename)
    return fig


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    'COLORS',
    'ALGORITHM_COLORS',
    'setup_style',
    'save_figure',
    'plot_queue_depth_histogram',
    'plot_latency_cdf',
    'plot_sniper_cdf',
    'plot_throughput_recovery',
    'plot_gantt_chart',
    'plot_metric_comparison_bar',
    'plot_fairness_comparison',
    'plot_heatmap',
    'plot_drop_rate_comparison',
    'plot_family_sextet'
]

