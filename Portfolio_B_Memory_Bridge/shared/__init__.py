"""
Shared Infrastructure for Portfolio B Simulations
==================================================

This package provides common utilities for all 4 tournament simulations:
- Tournament harness for algorithm comparison
- Statistical analysis functions
- Publication-quality visualization

Usage:
    from shared.tournament_harness import TournamentRunner, Algorithm, Scenario
    from shared.visualization import plot_queue_depth_histogram, plot_latency_cdf
"""

from .tournament_harness import (
    SimulationResult,
    AlgorithmStats,
    PairwiseComparison,
    Scenario,
    Algorithm,
    TournamentRunner,
    compute_cohens_d,
    compute_jains_fairness,
    bootstrap_ci
)

from .visualization import (
    COLORS,
    ALGORITHM_COLORS,
    setup_style,
    save_figure,
    plot_queue_depth_histogram,
    plot_latency_cdf,
    plot_throughput_recovery,
    plot_gantt_chart,
    plot_metric_comparison_bar,
    plot_fairness_comparison,
    plot_heatmap,
    plot_drop_rate_comparison
)

__all__ = [
    # Tournament harness
    'SimulationResult',
    'AlgorithmStats',
    'PairwiseComparison',
    'Scenario',
    'Algorithm',
    'TournamentRunner',
    'compute_cohens_d',
    'compute_jains_fairness',
    'bootstrap_ci',
    # Visualization
    'COLORS',
    'ALGORITHM_COLORS',
    'setup_style',
    'save_figure',
    'plot_queue_depth_histogram',
    'plot_latency_cdf',
    'plot_throughput_recovery',
    'plot_gantt_chart',
    'plot_metric_comparison_bar',
    'plot_fairness_comparison',
    'plot_heatmap',
    'plot_drop_rate_comparison'
]


