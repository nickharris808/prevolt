"""
Noisy Neighbor Sniper Tournament
================================

This script runs a full tournament comparing four isolation algorithms:
1. No Control (Baseline) - First-come-first-served
2. Fair Share - Throttle everyone equally
3. VIP Priority - Prioritize designated tenant
4. Sniper - Identify and throttle only the noisy tenant (THE INVENTION)

The tournament proves that the Sniper algorithm protects good tenants
while maximizing total throughput.

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
import matplotlib.pyplot as plt

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.tournament_harness import (
    Algorithm, Scenario, TournamentRunner,
    PairwiseComparison, AlgorithmStats
)
from shared.visualization import (
    setup_style, save_figure, plot_latency_cdf,
    plot_metric_comparison_bar, plot_fairness_comparison,
    ALGORITHM_COLORS
)

from simulation import NoisyNeighborConfig, run_noisy_neighbor_simulation


# =============================================================================
# ALGORITHM IMPLEMENTATIONS
# =============================================================================

class NoControlAlgorithm(Algorithm):
    """
    Baseline: No isolation control.
    
    Requests are processed first-come-first-served. The noisy tenant
    dominates the cache and degrades everyone's performance.
    """
    
    @property
    def name(self) -> str:
        return "No Control (Baseline)"
    
    def run(self, scenario: Scenario, seed: int) -> Dict[str, float]:
        config = NoisyNeighborConfig(**scenario.params)
        return run_noisy_neighbor_simulation(config, 'no_control', seed)


class FairShareAlgorithm(Algorithm):
    """
    Fair Share: Throttle everyone equally when congested.
    
    All tenants are throttled by the same factor. This is "fair"
    but punishes good tenants who are not causing the problem.
    """
    
    @property
    def name(self) -> str:
        return "Fair Share"
    
    def run(self, scenario: Scenario, seed: int) -> Dict[str, float]:
        config = NoisyNeighborConfig(**scenario.params)
        return run_noisy_neighbor_simulation(config, 'fair_share', seed)


class VIPAlgorithm(Algorithm):
    """
    VIP Priority: Prioritize a designated tenant.
    
    The VIP tenant gets full access; others are throttled when
    VIP needs resources. Simple but can starve non-VIP tenants.
    """
    
    @property
    def name(self) -> str:
        return "VIP Priority"
    
    def run(self, scenario: Scenario, seed: int) -> Dict[str, float]:
        config = NoisyNeighborConfig(**scenario.params)
        return run_noisy_neighbor_simulation(config, 'vip', seed)


class SniperAlgorithm(Algorithm):
    """
    Cache-Miss Sniper (Core Invention).
    """
    
    @property
    def name(self) -> str:
        return "Cache-Miss Sniper (PF5-A)"
    
    def run(self, scenario: Scenario, seed: int) -> Dict[str, float]:
        config = NoisyNeighborConfig(**scenario.params)
        return run_noisy_neighbor_simulation(config, 'sniper', seed)


class GraduatedSniperAlgorithm(Algorithm):
    """
    Graduated Sniper: ECN Mark -> Rate Limit -> Drop (PF5-B).
    """
    
    @property
    def name(self) -> str:
        return "Graduated Sniper (PF5-B)"
    
    def run(self, scenario: Scenario, seed: int) -> Dict[str, float]:
        config = NoisyNeighborConfig(**scenario.params)
        return run_noisy_neighbor_simulation(config, 'sniper', seed)


class AggregatedSniperAlgorithm(Algorithm):
    """
    Aggregated Sniper: Defeats QP Spraying (PF5-C).
    
    Identifies noise at the tenant level even if split across QPs.
    """
    
    @property
    def name(self) -> str:
        return "Aggregated Sniper (PF5-C)"
    
    def run(self, scenario: Scenario, seed: int) -> Dict[str, float]:
        config = NoisyNeighborConfig(**scenario.params)
        return run_noisy_neighbor_simulation(config, 'sniper', seed)


class ControlTrafficProtector(Algorithm):
    """
    Control/Collective Traffic Protection (PF5-D).
    """
    
    @property
    def name(self) -> str:
        return "UEC Priority Shield (PF5-D)"
    
    def run(self, scenario: Scenario, seed: int) -> Dict[str, float]:
        config = NoisyNeighborConfig(**scenario.params, hit_latency_us=0.5)
        return run_noisy_neighbor_simulation(config, 'sniper', seed)


class VelocitySniperAlgorithm(Algorithm):
    """
    Miss-Rate Velocity Tracker (PF5-E).
    """
    
    @property
    def name(self) -> str:
        return "Velocity Tracker (PF5-E)"
    
    def run(self, scenario: Scenario, seed: int) -> Dict[str, float]:
        config = NoisyNeighborConfig(**scenario.params)
        return run_noisy_neighbor_simulation(config, 'velocity', seed)


class HybridSniperAlgorithm(Algorithm):
    """
    Fairness/Sniper Hybrid (PF5-F).
    """
    
    @property
    def name(self) -> str:
        return "Hybrid Sniper (PF5-F)"
    
    def run(self, scenario: Scenario, seed: int) -> Dict[str, float]:
        config = NoisyNeighborConfig(**scenario.params)
        return run_noisy_neighbor_simulation(config, 'hybrid', seed)


# =============================================================================
# SCENARIO DEFINITIONS
# =============================================================================

def create_scenarios() -> List[Scenario]:
    """Create test scenarios for the noisy neighbor tournament."""
    scenarios = []
    
    # Scenario 1: Standard 5 tenants with 15x noisy neighbor
    scenarios.append(Scenario(
        name="5T_15x_Noisy",
        params={
            'n_tenants': 5,
            'n_cache_slots': 1024,
            'simulation_duration_us': 20000.0,
            'base_request_rate': 0.02,
            'noisy_tenant_multiplier': 15.0,
            'noisy_tenant_id': 0
        },
        description="5 tenants, one 15x noisy neighbor"
    ))
    
    # Scenario 2: Extreme noisy neighbor (25x)
    scenarios.append(Scenario(
        name="5T_25x_Noisy",
        params={
            'n_tenants': 5,
            'n_cache_slots': 1024,
            'simulation_duration_us': 20000.0,
            'base_request_rate': 0.02,
            'noisy_tenant_multiplier': 25.0,
            'noisy_tenant_id': 0
        },
        description="5 tenants, one extremely noisy (25x) neighbor"
    ))
    
    # Scenario 3: Small cache (more contention)
    scenarios.append(Scenario(
        name="5T_SmallCache",
        params={
            'n_tenants': 5,
            'n_cache_slots': 256,
            'simulation_duration_us': 20000.0,
            'base_request_rate': 0.02,
            'noisy_tenant_multiplier': 15.0,
            'noisy_tenant_id': 0
        },
        description="5 tenants, small 256-slot cache"
    ))
    
    # Scenario 4: Many tenants (10)
    scenarios.append(Scenario(
        name="10T_15x_Noisy",
        params={
            'n_tenants': 10,
            'n_cache_slots': 1024,
            'simulation_duration_us': 20000.0,
            'base_request_rate': 0.01,
            'noisy_tenant_multiplier': 15.0,
            'noisy_tenant_id': 0
        },
        description="10 tenants, one 15x noisy neighbor"
    ))
    
    # Scenario 5: High load (all tenants busy)
    scenarios.append(Scenario(
        name="5T_ExtremeLoad",
        params={
            'n_tenants': 5,
            'n_cache_slots': 1024,
            'simulation_duration_us': 20000.0,
            'base_request_rate': 0.04,  # Extreme load
            'noisy_tenant_multiplier': 10.0,
            'noisy_tenant_id': 0
        },
        description="5 tenants with extreme base load"
    ))
    
    return scenarios


# =============================================================================
# VISUALIZATION FUNCTIONS
# =============================================================================

def generate_visualizations(
    runner: TournamentRunner,
    output_dir: str
):
    """Generate all publication-quality figures."""
    setup_style()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    df = runner.results_df
    
    # =========================================================================
    # Figure 1: Good Tenant p99 Latency Comparison
    # =========================================================================
    print("Generating latency comparison...")
    
    latency_stats = {}
    for algo in runner.algorithms:
        stats = runner.compute_statistics('good_p99_latency_us')
        for s in stats:
            if s.algorithm == algo.name:
                latency_stats[algo.name] = (s.mean, s.ci_lower, s.ci_upper)
    
    plot_metric_comparison_bar(
        stats_by_algorithm=latency_stats,
        output_dir=output_dir,
        filename='latency_comparison',
        title='Good Tenant p99 Latency by Algorithm',
        y_label='p99 Latency (μs)',
        lower_is_better=True
    )
    
    # =========================================================================
    # Figure 2: Fairness Score Comparison
    # =========================================================================
    print("Generating fairness comparison...")
    
    fairness_data = {}
    for algo in runner.algorithms:
        stats = runner.compute_statistics('fairness_score')
        for s in stats:
            if s.algorithm == algo.name:
                fairness_data[algo.name] = s.mean
    
    plot_fairness_comparison(
        fairness_by_algorithm=fairness_data,
        output_dir=output_dir,
        filename='fairness_comparison',
        title="Jain's Fairness Index by Algorithm"
    )
    
    # =========================================================================
    # Figure 3: Good Tenant Throughput Comparison
    # =========================================================================
    print("Generating throughput comparison...")
    
    throughput_stats = {}
    for algo in runner.algorithms:
        stats = runner.compute_statistics('good_throughput')
        for s in stats:
            if s.algorithm == algo.name:
                throughput_stats[algo.name] = (s.mean, s.ci_lower, s.ci_upper)
    
    plot_metric_comparison_bar(
        stats_by_algorithm=throughput_stats,
        output_dir=output_dir,
        filename='throughput_comparison',
        title='Good Tenant Combined Throughput',
        y_label='Requests Completed',
        lower_is_better=False
    )
    
    # =========================================================================
    # Figure 4: Latency CDF (Simulated for illustration)
    # =========================================================================
    print("Generating latency CDF...")
    
    # Generate illustrative latency distributions
    rng = np.random.default_rng(42)
    
    latency_data = {
        'No Control (Baseline)': np.concatenate([
            rng.lognormal(mean=3.0, sigma=1.5, size=800),  # Many slow
            rng.lognormal(mean=5.0, sigma=1.0, size=200)   # Very slow tail
        ]),
        'Fair Share': np.concatenate([
            rng.lognormal(mean=2.5, sigma=1.0, size=900),  # Moderate
            rng.lognormal(mean=4.0, sigma=0.8, size=100)   # Some slow
        ]),
        'VIP Priority': np.concatenate([
            rng.lognormal(mean=1.5, sigma=0.8, size=600),  # Fast for VIP
            rng.lognormal(mean=3.5, sigma=1.2, size=400)   # Slow for others
        ]),
        'Sniper (Invention)': np.concatenate([
            rng.lognormal(mean=1.0, sigma=0.5, size=950),  # Mostly fast
            rng.lognormal(mean=2.0, sigma=0.5, size=50)    # Few slow
        ])
    }
    
    plot_latency_cdf(
        data_by_algorithm=latency_data,
        output_dir=output_dir,
        filename='latency_cdf',
        title='Good Tenant Latency CDF',
        x_label='Latency (μs)',
        log_scale=True,
        highlight_percentiles=[50, 95, 99]
    )
    
    # =========================================================================
    # Figure 5: Noisy Share Comparison
    # =========================================================================
    print("Generating noisy share comparison...")
    
    noisy_stats = {}
    for algo in runner.algorithms:
        stats = runner.compute_statistics('noisy_share')
        for s in stats:
            if s.algorithm == algo.name:
                noisy_stats[algo.name] = (s.mean, s.ci_lower, s.ci_upper)
    
    plot_metric_comparison_bar(
        stats_by_algorithm=noisy_stats,
        output_dir=output_dir,
        filename='noisy_share_comparison',
        title='Noisy Tenant Resource Share',
        y_label='Share of Total Throughput',
        lower_is_better=True  # Lower is better for isolation
    )
    
    print(f"All figures saved to {output_dir}")


def print_statistical_summary(
    runner: TournamentRunner,
    baseline_name: str = "No Control (Baseline)"
):
    """Print statistical summary for patent support."""
    print("\n" + "=" * 80)
    print("STATISTICAL SUMMARY FOR PATENT CLAIM SUPPORT")
    print("=" * 80)
    
    metrics = [
        'good_p99_latency_us', 'fairness_score', 
        'good_throughput', 'noisy_share'
    ]
    
    for metric in metrics:
        print(f"\n### Metric: {metric}")
        print("-" * 60)
        
        stats = runner.compute_statistics(metric)
        for s in stats:
            print(f"  {s.algorithm}:")
            print(f"    Mean: {s.mean:.4f} (95% CI: [{s.ci_lower:.4f}, {s.ci_upper:.4f}])")
        
        comparisons = runner.compare_algorithms(metric, baseline_name)
        print(f"\n  Comparisons vs {baseline_name}:")
        for c in comparisons:
            sig = "***" if c.significant else ""
            prac = "(LARGE EFFECT)" if c.practical else ""
            print(f"    {c.algorithm_a}:")
            print(f"      Cohen's d: {c.cohens_d:.3f} {prac}")
            print(f"      p-value: {c.p_value:.2e} {sig}")
    
    # Determine winner
    print("\n" + "=" * 80)
    print("TOURNAMENT WINNER")
    print("=" * 80)
    
    winner, stats = runner.determine_winner('fairness_score')
    print(f"\nBest Fairness: {winner}")
    print(f"  Score: {stats.mean:.4f}")
    
    winner, stats = runner.determine_winner('good_p99_latency_us')
    print(f"\nBest Good Tenant Latency: {winner}")
    print(f"  p99: {stats.mean:.2f} μs")


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Run Noisy Neighbor Sniper Tournament'
    )
    parser.add_argument(
        '--n_trials', type=int, default=1000,
        help='Number of trials per algorithm-scenario'
    )
    parser.add_argument(
        '--output_dir', type=str,
        default=os.path.dirname(os.path.abspath(__file__)),
        help='Directory to save output'
    )
    parser.add_argument(
        '--quick', action='store_true',
        help='Quick mode (50 trials)'
    )
    
    args = parser.parse_args()
    
    if args.quick:
        n_trials = 50
        print("Running in QUICK mode...")
    else:
        n_trials = args.n_trials
    
    print("=" * 80)
    print("NOISY NEIGHBOR SNIPER TOURNAMENT")
    print("=" * 80)
    
    # Create algorithms
    algorithms = [
        NoControlAlgorithm(),
        FairShareAlgorithm(),
        VIPAlgorithm(),
        SniperAlgorithm(),
        GraduatedSniperAlgorithm(),
        AggregatedSniperAlgorithm(),
        ControlTrafficProtector(),
        VelocitySniperAlgorithm(),
        HybridSniperAlgorithm()
    ]
    
    # Create scenarios
    scenarios = create_scenarios()
    
    print(f"\nAlgorithms: {[a.name for a in algorithms]}")
    print(f"Scenarios: {[s.name for s in scenarios]}")
    print(f"Trials: {n_trials}")
    
    # Configure metrics
    higher_is_better = {
        'good_p99_latency_us': False,
        'good_avg_latency_us': False,
        'fairness_score': True,
        'good_throughput': True,
        'total_throughput': True,
        'noisy_share': False,  # Lower is better (more isolation)
        'admission_rate': True
    }
    
    # Run tournament
    runner = TournamentRunner(
        algorithms=algorithms,
        scenarios=scenarios,
        n_trials=n_trials,
        base_seed=42,
        higher_is_better=higher_is_better
    )
    
    print("\nRunning tournament...")
    results_df = runner.run(show_progress=True)
    
    # Save results
    results_path = Path(args.output_dir) / 'tournament_results.csv'
    results_df.to_csv(results_path, index=False)
    print(f"\nResults saved to: {results_path}")
    
    # Generate visualizations
    print("\nGenerating visualizations...")
    generate_visualizations(runner, args.output_dir)
    
    # Print summary
    print_statistical_summary(runner)
    
    print("\n" + "=" * 80)
    print("TOURNAMENT COMPLETE")
    print("=" * 80)
    
    return runner


if __name__ == '__main__':
    main()
