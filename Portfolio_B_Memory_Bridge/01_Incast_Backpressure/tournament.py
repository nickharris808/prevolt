"""
Incast Backpressure Tournament
==============================

This script runs a full tournament comparing three backpressure algorithms:
1. No Control (Baseline) - Packets drop when buffer fills
2. Static Threshold - Pause at fixed threshold (80%)
3. Adaptive Hysteresis - Pause at 90%, resume at 70% (THE INVENTION)

The tournament runs 1000 trials per algorithm across multiple scenarios,
computing statistical significance and effect sizes to support patent claims.

Usage:
    python tournament.py [--n_trials 1000] [--output_dir ./output]

Author: Portfolio B Research Team
License: Proprietary - Patent Pending
"""

import sys
import os
import argparse
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.tournament_harness import (
    Algorithm, Scenario, TournamentRunner, 
    PairwiseComparison, AlgorithmStats
)
from shared.visualization import (
    setup_style, plot_queue_depth_histogram, 
    plot_metric_comparison_bar, plot_drop_rate_comparison
)

from simulation import IncastConfig, run_incast_simulation


# =============================================================================
# ALGORITHM IMPLEMENTATIONS (Adapter Pattern)
# =============================================================================

class NoControlAlgorithm(Algorithm):
    """
    Baseline algorithm: No backpressure control whatsoever.
    
    This represents the current state of most network-memory interfaces
    where the network blindly sends data without considering memory state.
    """
    
    @property
    def name(self) -> str:
        return "No Control (Baseline)"
    
    def run(self, scenario: Scenario, seed: int) -> Dict[str, float]:
        config = IncastConfig(**scenario.params)
        return run_incast_simulation(config, 'no_control', seed)


class StaticThresholdAlgorithm(Algorithm):
    """
    Static threshold backpressure at 80% buffer occupancy.
    
    This is a naive improvement that pauses sending when the buffer
    exceeds a fixed threshold. It suffers from oscillation.
    """
    
    @property
    def name(self) -> str:
        return "Static Threshold (80%)"
    
    def run(self, scenario: Scenario, seed: int) -> Dict[str, float]:
        config = IncastConfig(**scenario.params, backpressure_threshold=0.80)
        return run_incast_simulation(config, 'static', seed)


class AdaptiveHysteresisAlgorithm(Algorithm):
    """
    Adaptive hysteresis backpressure (THE PATENTED INVENTION).
    
    Uses two thresholds to prevent oscillation:
    - Pause when buffer exceeds 90%
    - Resume when buffer drops to 70%
    
    This is the core innovation that maximizes throughput while
    preventing buffer overflow and avoiding control loop oscillation.
    """
    
    @property
    def name(self) -> str:
        return "Adaptive Hysteresis (Invention)"
    
    def run(self, scenario: Scenario, seed: int) -> Dict[str, float]:
        config = IncastConfig(
            **scenario.params,
            hysteresis_low=0.70,
            hysteresis_high=0.90
        )
        return run_incast_simulation(config, 'hysteresis', seed)


# =============================================================================
# SCENARIO DEFINITIONS
# =============================================================================

def create_scenarios() -> List[Scenario]:
    """
    Create the set of scenarios to test.
    
    We test across:
    - Traffic patterns: uniform, bursty, incast
    - Buffer sizes: 1MB, 10MB, 100MB
    - Load levels: normal, heavy
    """
    scenarios = []
    
    # Scenario 1: Uniform traffic, standard buffer
    scenarios.append(Scenario(
        name="Uniform_10MB",
        params={
            'traffic_pattern': 'uniform',
            'buffer_capacity_bytes': 10_000_000,
            'simulation_duration_us': 500.0,
            'network_rate_gbps': 200.0,
            'memory_rate_gbps': 100.0,
            'n_senders': 1
        },
        description="Steady-state uniform traffic with 10MB buffer"
    ))
    
    # Scenario 2: Bursty traffic (AI inference pattern)
    scenarios.append(Scenario(
        name="Bursty_10MB",
        params={
            'traffic_pattern': 'bursty',
            'buffer_capacity_bytes': 10_000_000,
            'simulation_duration_us': 500.0,
            'network_rate_gbps': 200.0,
            'memory_rate_gbps': 100.0,
            'burst_factor': 5.0,
            'n_senders': 1
        },
        description="Bursty traffic simulating AI inference batches"
    ))
    
    # Scenario 3: Incast - The worst case (many-to-one)
    scenarios.append(Scenario(
        name="Incast_50_senders",
        params={
            'traffic_pattern': 'incast',
            'buffer_capacity_bytes': 10_000_000,
            'simulation_duration_us': 500.0,
            'network_rate_gbps': 200.0,
            'memory_rate_gbps': 100.0,
            'n_senders': 50
        },
        description="Incast congestion with 50 simultaneous senders"
    ))
    
    # Scenario 4: Incast with small buffer (stress test)
    scenarios.append(Scenario(
        name="Incast_Small_Buffer",
        params={
            'traffic_pattern': 'incast',
            'buffer_capacity_bytes': 1_000_000,  # 1MB only
            'simulation_duration_us': 500.0,
            'network_rate_gbps': 200.0,
            'memory_rate_gbps': 100.0,
            'n_senders': 50
        },
        description="Incast with undersized 1MB buffer - stress test"
    ))
    
    # Scenario 5: Incast with large buffer (best case for baseline)
    scenarios.append(Scenario(
        name="Incast_Large_Buffer",
        params={
            'traffic_pattern': 'incast',
            'buffer_capacity_bytes': 100_000_000,  # 100MB
            'simulation_duration_us': 500.0,
            'network_rate_gbps': 200.0,
            'memory_rate_gbps': 100.0,
            'n_senders': 50
        },
        description="Incast with large 100MB buffer"
    ))
    
    return scenarios


# =============================================================================
# VISUALIZATION FUNCTIONS
# =============================================================================

def generate_visualizations(
    runner: TournamentRunner,
    output_dir: str
):
    """
    Generate all publication-quality figures for the data room.
    
    Args:
        runner: Completed tournament runner with results
        output_dir: Directory to save figures
    """
    setup_style()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    df = runner.results_df
    
    # =========================================================================
    # Figure 1: Queue Depth Histogram
    # =========================================================================
    print("Generating queue depth histogram...")
    
    # Extract queue depth data for the worst-case incast scenario
    queue_data = {}
    for algo in runner.algorithms:
        algo_data = df[
            (df['algorithm'] == algo.name) & 
            (df['scenario'] == 'Incast_50_senders')
        ]['avg_occupancy'].values
        queue_data[algo.name] = algo_data
    
    plot_queue_depth_histogram(
        data_by_algorithm=queue_data,
        buffer_capacity=1.0,  # Already normalized to fraction
        output_dir=output_dir,
        filename='queue_depth_histogram',
        title='Buffer Occupancy Distribution (Incast, 50 Senders)'
    )
    
    # =========================================================================
    # Figure 2: Drop Rate Comparison
    # =========================================================================
    print("Generating drop rate comparison...")
    
    drop_stats = {}
    for algo in runner.algorithms:
        stats = runner.compute_statistics('drop_rate')
        for s in stats:
            if s.algorithm == algo.name:
                drop_stats[algo.name] = (s.mean, s.ci_lower, s.ci_upper)
    
    plot_metric_comparison_bar(
        stats_by_algorithm=drop_stats,
        output_dir=output_dir,
        filename='drop_rate_comparison',
        title='Packet Drop Rate by Algorithm',
        y_label='Drop Rate (fraction)',
        lower_is_better=True
    )
    
    # =========================================================================
    # Figure 3: Throughput Comparison
    # =========================================================================
    print("Generating throughput comparison...")
    
    throughput_stats = {}
    for algo in runner.algorithms:
        stats = runner.compute_statistics('throughput_fraction')
        for s in stats:
            if s.algorithm == algo.name:
                throughput_stats[algo.name] = (s.mean, s.ci_lower, s.ci_upper)
    
    plot_metric_comparison_bar(
        stats_by_algorithm=throughput_stats,
        output_dir=output_dir,
        filename='throughput_comparison',
        title='Effective Throughput by Algorithm',
        y_label='Throughput (fraction of maximum)',
        lower_is_better=False
    )
    
    # =========================================================================
    # Figure 4: Latency Comparison
    # =========================================================================
    print("Generating latency comparison...")
    
    latency_stats = {}
    for algo in runner.algorithms:
        stats = runner.compute_statistics('avg_latency_us')
        for s in stats:
            if s.algorithm == algo.name:
                latency_stats[algo.name] = (s.mean, s.ci_lower, s.ci_upper)
    
    plot_metric_comparison_bar(
        stats_by_algorithm=latency_stats,
        output_dir=output_dir,
        filename='latency_comparison',
        title='Average Latency by Algorithm',
        y_label='Latency (μs)',
        lower_is_better=True
    )
    
    # =========================================================================
    # Figure 5: Utilization Comparison
    # =========================================================================
    print("Generating utilization comparison...")
    
    util_stats = {}
    for algo in runner.algorithms:
        stats = runner.compute_statistics('utilization')
        for s in stats:
            if s.algorithm == algo.name:
                util_stats[algo.name] = (s.mean, s.ci_lower, s.ci_upper)
    
    plot_metric_comparison_bar(
        stats_by_algorithm=util_stats,
        output_dir=output_dir,
        filename='utilization_comparison',
        title='Link Utilization by Algorithm',
        y_label='Utilization (fraction)',
        lower_is_better=False
    )
    
    print(f"All figures saved to {output_dir}")


def print_statistical_summary(
    runner: TournamentRunner,
    baseline_name: str = "No Control (Baseline)"
):
    """
    Print a summary of statistical results for patent support.
    
    Args:
        runner: Completed tournament runner
        baseline_name: Name of the baseline algorithm for comparison
    """
    print("\n" + "=" * 80)
    print("STATISTICAL SUMMARY FOR PATENT CLAIM SUPPORT")
    print("=" * 80)
    
    metrics = ['drop_rate', 'throughput_fraction', 'avg_latency_us', 'avg_occupancy', 'utilization']
    
    for metric in metrics:
        print(f"\n### Metric: {metric}")
        print("-" * 60)
        
        # Print statistics for each algorithm
        stats = runner.compute_statistics(metric)
        for s in stats:
            print(f"  {s.algorithm}:")
            print(f"    Mean: {s.mean:.6f} (95% CI: [{s.ci_lower:.6f}, {s.ci_upper:.6f}])")
            print(f"    Std:  {s.std:.6f}")
        
        # Print pairwise comparisons against baseline
        comparisons = runner.compare_algorithms(metric, baseline_name)
        print(f"\n  Comparisons vs {baseline_name}:")
        for c in comparisons:
            sig = "***" if c.significant else ""
            prac = "(LARGE EFFECT)" if c.practical else ""
            print(f"    {c.algorithm_a}:")
            print(f"      Mean Diff: {c.mean_diff:+.6f}")
            print(f"      t-stat: {c.t_statistic:.3f}, p-value: {c.p_value:.2e} {sig}")
            print(f"      Cohen's d: {c.cohens_d:.3f} {prac}")
    
    # Determine overall winner
    print("\n" + "=" * 80)
    print("TOURNAMENT WINNER")
    print("=" * 80)
    
    # Winner is algorithm with lowest drop rate AND highest throughput
    winner, winner_stats = runner.determine_winner('drop_rate')
    print(f"\nBest Drop Rate: {winner}")
    print(f"  Mean: {winner_stats.mean:.6f}")
    
    winner, winner_stats = runner.determine_winner('throughput_fraction')
    print(f"\nBest Throughput: {winner}")
    print(f"  Mean: {winner_stats.mean:.6f}")


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Run Incast Backpressure Tournament'
    )
    parser.add_argument(
        '--n_trials', type=int, default=1000,
        help='Number of trials per algorithm-scenario combination'
    )
    parser.add_argument(
        '--output_dir', type=str, 
        default=os.path.dirname(os.path.abspath(__file__)),
        help='Directory to save output files'
    )
    parser.add_argument(
        '--quick', action='store_true',
        help='Quick mode with fewer trials for testing'
    )
    
    args = parser.parse_args()
    
    if args.quick:
        n_trials = 50
        print("Running in QUICK mode (50 trials)...")
    else:
        n_trials = args.n_trials
    
    print("=" * 80)
    print("INCAST BACKPRESSURE TOURNAMENT")
    print("=" * 80)
    print(f"Trials per algorithm-scenario: {n_trials}")
    print(f"Output directory: {args.output_dir}")
    
    # Create algorithms
    algorithms = [
        NoControlAlgorithm(),
        StaticThresholdAlgorithm(),
        AdaptiveHysteresisAlgorithm()
    ]
    
    # Create scenarios
    scenarios = create_scenarios()
    
    print(f"\nAlgorithms: {[a.name for a in algorithms]}")
    print(f"Scenarios: {[s.name for s in scenarios]}")
    print(f"Total simulations: {len(algorithms) * len(scenarios) * n_trials}")
    
    # Configure higher_is_better for each metric
    higher_is_better = {
        'drop_rate': False,  # Lower is better
        'throughput_fraction': True,  # Higher is better
        'avg_latency_us': False,  # Lower is better
        'p99_latency_us': False,  # Lower is better
        'avg_occupancy': False,  # Lower is better (want headroom)
        'max_occupancy': False,  # Lower is better
        'backpressure_events': False,  # Lower is better (less oscillation)
        'utilization': True  # Higher is better
    }
    
    # Create and run tournament
    runner = TournamentRunner(
        algorithms=algorithms,
        scenarios=scenarios,
        n_trials=n_trials,
        base_seed=42,
        higher_is_better=higher_is_better
    )
    
    print("\nRunning tournament...")
    results_df = runner.run(show_progress=True)
    
    # Save raw results
    results_path = Path(args.output_dir) / 'tournament_results.csv'
    results_df.to_csv(results_path, index=False)
    print(f"\nRaw results saved to: {results_path}")
    
    # Generate visualizations
    print("\nGenerating visualizations...")
    generate_visualizations(runner, args.output_dir)
    
    # Print statistical summary
    print_statistical_summary(runner)
    
    print("\n" + "=" * 80)
    print("TOURNAMENT COMPLETE")
    print("=" * 80)
    
    return runner


if __name__ == '__main__':
    main()


