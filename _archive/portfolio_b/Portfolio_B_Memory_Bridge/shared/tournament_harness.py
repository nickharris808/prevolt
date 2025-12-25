"""
Tournament Harness - Shared Infrastructure for Algorithm Comparison
====================================================================

This module provides the statistical framework for running algorithm tournaments
across all Portfolio B simulations. It ensures:
- Reproducible results via seeded random number generation
- Statistical rigor via confidence intervals and effect size calculations
- Publication-quality output via standardized visualization

Author: Portfolio B Research Team
License: Proprietary - Patent Pending
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import List, Dict, Callable, Any, Optional, Tuple
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import time
from tqdm import tqdm
import warnings

# =============================================================================
# CORE DATA STRUCTURES
# =============================================================================

@dataclass
class SimulationResult:
    """
    Captures the outcome of a single simulation run.
    
    Attributes:
        algorithm: Name of the algorithm being tested
        scenario: Name of the scenario configuration
        trial: Trial number (0 to n_trials-1)
        metrics: Dictionary of metric_name -> value pairs
        duration_seconds: Wall-clock time for this simulation
        seed: Random seed used for reproducibility
    """
    algorithm: str
    scenario: str
    trial: int
    metrics: Dict[str, float]
    duration_seconds: float
    seed: int


@dataclass
class AlgorithmStats:
    """
    Statistical summary for one algorithm across all trials.
    
    Attributes:
        algorithm: Name of the algorithm
        metric: Name of the metric being summarized
        mean: Sample mean
        std: Sample standard deviation
        ci_lower: Lower bound of 95% confidence interval
        ci_upper: Upper bound of 95% confidence interval
        median: Sample median
        p5: 5th percentile
        p95: 95th percentile
        n_samples: Number of trials
    """
    algorithm: str
    metric: str
    mean: float
    std: float
    ci_lower: float
    ci_upper: float
    median: float
    p5: float
    p95: float
    n_samples: int


@dataclass
class PairwiseComparison:
    """
    Statistical comparison between two algorithms.
    
    Attributes:
        algorithm_a: First algorithm (typically the invention)
        algorithm_b: Second algorithm (typically baseline)
        metric: Metric being compared
        mean_diff: Difference in means (A - B)
        t_statistic: Welch's t-test statistic
        p_value: Two-tailed p-value
        cohens_d: Effect size (Cohen's d)
        significant: Whether p < 0.001
        practical: Whether |d| > 1.0 (large effect)
    """
    algorithm_a: str
    algorithm_b: str
    metric: str
    mean_diff: float
    t_statistic: float
    p_value: float
    cohens_d: float
    significant: bool
    practical: bool


@dataclass
class Scenario:
    """
    Configuration for a simulation scenario.
    
    Attributes:
        name: Human-readable scenario name
        params: Dictionary of parameter_name -> value
        description: Optional description for documentation
    """
    name: str
    params: Dict[str, Any]
    description: str = ""


# =============================================================================
# ABSTRACT BASE CLASS FOR ALGORITHMS
# =============================================================================

class Algorithm(ABC):
    """
    Abstract base class that all tournament algorithms must implement.
    
    Subclasses must implement:
        - name: Property returning the algorithm name
        - run(): Method that executes the simulation and returns metrics
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the algorithm's display name."""
        pass
    
    @abstractmethod
    def run(self, scenario: Scenario, seed: int) -> Dict[str, float]:
        """
        Execute the algorithm simulation.
        
        Args:
            scenario: The scenario configuration to use
            seed: Random seed for reproducibility
            
        Returns:
            Dictionary mapping metric names to their values
        """
        pass


# =============================================================================
# TOURNAMENT RUNNER
# =============================================================================

class TournamentRunner:
    """
    Orchestrates algorithm comparison tournaments with statistical rigor.
    
    This class manages:
    1. Running all algorithm x scenario x trial combinations
    2. Collecting and organizing results
    3. Computing statistical summaries
    4. Performing pairwise comparisons
    5. Determining winners
    
    Example usage:
        runner = TournamentRunner(
            algorithms=[NoControl(), StaticThreshold(), AdaptiveHysteresis()],
            scenarios=[uniform_scenario, bursty_scenario],
            n_trials=1000
        )
        results_df = runner.run()
        stats = runner.compute_statistics()
        comparisons = runner.compare_algorithms(baseline="NoControl")
    """
    
    def __init__(
        self,
        algorithms: List[Algorithm],
        scenarios: List[Scenario],
        n_trials: int = 1000,
        base_seed: int = 42,
        metrics_to_track: Optional[List[str]] = None,
        higher_is_better: Optional[Dict[str, bool]] = None
    ):
        """
        Initialize the tournament runner.
        
        Args:
            algorithms: List of Algorithm instances to compete
            scenarios: List of Scenario configurations to test
            n_trials: Number of independent trials per algorithm-scenario pair
            base_seed: Starting seed for reproducibility
            metrics_to_track: List of metric names to extract (None = all)
            higher_is_better: Dict mapping metric -> True if higher is better
        """
        self.algorithms = algorithms
        self.scenarios = scenarios
        self.n_trials = n_trials
        self.base_seed = base_seed
        self.metrics_to_track = metrics_to_track
        self.higher_is_better = higher_is_better or {}
        
        # Results storage
        self.results: List[SimulationResult] = []
        self.results_df: Optional[pd.DataFrame] = None
        self._stats_cache: Dict[str, AlgorithmStats] = {}
        
    def run(self, show_progress: bool = True) -> pd.DataFrame:
        """
        Execute all tournament simulations.
        
        Args:
            show_progress: Whether to show a progress bar
            
        Returns:
            DataFrame with all results (one row per trial)
        """
        self.results = []
        total_runs = len(self.algorithms) * len(self.scenarios) * self.n_trials
        
        # Create progress bar if requested
        iterator = range(total_runs)
        if show_progress:
            iterator = tqdm(iterator, desc="Running tournament", unit="trial")
        
        run_idx = 0
        for algo in self.algorithms:
            for scenario in self.scenarios:
                for trial in range(self.n_trials):
                    # Compute unique seed for this run
                    seed = self.base_seed + run_idx
                    
                    # Time the simulation
                    start_time = time.time()
                    metrics = algo.run(scenario, seed)
                    duration = time.time() - start_time
                    
                    # Store result
                    result = SimulationResult(
                        algorithm=algo.name,
                        scenario=scenario.name,
                        trial=trial,
                        metrics=metrics,
                        duration_seconds=duration,
                        seed=seed
                    )
                    self.results.append(result)
                    
                    if show_progress:
                        iterator.update(1)  # type: ignore
                    run_idx += 1
        
        if show_progress:
            iterator.close()  # type: ignore
        
        # Convert to DataFrame for analysis
        self.results_df = self._results_to_dataframe()
        return self.results_df
    
    def _results_to_dataframe(self) -> pd.DataFrame:
        """Convert results list to a flat DataFrame."""
        rows = []
        for r in self.results:
            row = {
                'algorithm': r.algorithm,
                'scenario': r.scenario,
                'trial': r.trial,
                'duration_seconds': r.duration_seconds,
                'seed': r.seed
            }
            # Flatten metrics into columns
            for metric_name, value in r.metrics.items():
                if self.metrics_to_track is None or metric_name in self.metrics_to_track:
                    row[metric_name] = value
            rows.append(row)
        
        return pd.DataFrame(rows)
    
    def compute_statistics(self, metric: str, scenario: Optional[str] = None) -> List[AlgorithmStats]:
        """
        Compute summary statistics for each algorithm on a given metric.
        
        Args:
            metric: Name of the metric to analyze
            scenario: Optional scenario filter (None = aggregate all)
            
        Returns:
            List of AlgorithmStats, one per algorithm
        """
        if self.results_df is None:
            raise ValueError("Must call run() before computing statistics")
        
        df = self.results_df
        if scenario is not None:
            df = df[df['scenario'] == scenario]
        
        stats_list = []
        for algo_name in df['algorithm'].unique():
            algo_data = df[df['algorithm'] == algo_name][metric].dropna()
            
            if len(algo_data) == 0:
                continue
                
            # Compute confidence interval using t-distribution
            n = len(algo_data)
            mean = algo_data.mean()
            std = algo_data.std(ddof=1)
            se = std / np.sqrt(n)
            
            # 95% CI using t-distribution
            t_crit = stats.t.ppf(0.975, df=n-1)
            ci_lower = mean - t_crit * se
            ci_upper = mean + t_crit * se
            
            stat = AlgorithmStats(
                algorithm=algo_name,
                metric=metric,
                mean=mean,
                std=std,
                ci_lower=ci_lower,
                ci_upper=ci_upper,
                median=algo_data.median(),
                p5=algo_data.quantile(0.05),
                p95=algo_data.quantile(0.95),
                n_samples=n
            )
            stats_list.append(stat)
        
        return stats_list
    
    def compare_algorithms(
        self,
        metric: str,
        baseline: str,
        scenario: Optional[str] = None
    ) -> List[PairwiseComparison]:
        """
        Perform pairwise statistical comparisons against a baseline.
        
        Args:
            metric: Metric to compare
            baseline: Name of the baseline algorithm
            scenario: Optional scenario filter
            
        Returns:
            List of PairwiseComparison results
        """
        if self.results_df is None:
            raise ValueError("Must call run() before comparing algorithms")
        
        df = self.results_df
        if scenario is not None:
            df = df[df['scenario'] == scenario]
        
        baseline_data = df[df['algorithm'] == baseline][metric].dropna().values
        comparisons = []
        
        for algo_name in df['algorithm'].unique():
            if algo_name == baseline:
                continue
                
            algo_data = df[df['algorithm'] == algo_name][metric].dropna().values
            
            if len(algo_data) == 0 or len(baseline_data) == 0:
                continue
            
            # Welch's t-test (unequal variances)
            t_stat, p_value = stats.ttest_ind(algo_data, baseline_data, equal_var=False)
            
            # Cohen's d effect size
            pooled_std = np.sqrt(
                ((len(algo_data) - 1) * np.var(algo_data, ddof=1) +
                 (len(baseline_data) - 1) * np.var(baseline_data, ddof=1)) /
                (len(algo_data) + len(baseline_data) - 2)
            )
            
            if pooled_std > 0:
                cohens_d = (np.mean(algo_data) - np.mean(baseline_data)) / pooled_std
            else:
                cohens_d = 0.0
            
            comparison = PairwiseComparison(
                algorithm_a=algo_name,
                algorithm_b=baseline,
                metric=metric,
                mean_diff=np.mean(algo_data) - np.mean(baseline_data),
                t_statistic=t_stat,
                p_value=p_value,
                cohens_d=cohens_d,
                significant=p_value < 0.001,
                practical=abs(cohens_d) > 1.0
            )
            comparisons.append(comparison)
        
        return comparisons
    
    def determine_winner(
        self,
        metric: str,
        scenario: Optional[str] = None
    ) -> Tuple[str, AlgorithmStats]:
        """
        Determine the winning algorithm for a given metric.
        
        Args:
            metric: Metric to evaluate
            scenario: Optional scenario filter
            
        Returns:
            Tuple of (winner_name, winner_stats)
        """
        stats_list = self.compute_statistics(metric, scenario)
        
        # Determine if higher or lower is better
        higher_better = self.higher_is_better.get(metric, True)
        
        if higher_better:
            winner = max(stats_list, key=lambda s: s.mean)
        else:
            winner = min(stats_list, key=lambda s: s.mean)
        
        return winner.algorithm, winner
    
    def get_metric_data(
        self,
        metric: str,
        algorithm: Optional[str] = None,
        scenario: Optional[str] = None
    ) -> np.ndarray:
        """
        Extract raw metric values for visualization.
        
        Args:
            metric: Metric name
            algorithm: Optional algorithm filter
            scenario: Optional scenario filter
            
        Returns:
            NumPy array of metric values
        """
        if self.results_df is None:
            raise ValueError("Must call run() before extracting data")
        
        df = self.results_df
        if algorithm is not None:
            df = df[df['algorithm'] == algorithm]
        if scenario is not None:
            df = df[df['scenario'] == scenario]
        
        return df[metric].dropna().values
    
    def summary_table(self, metrics: List[str]) -> pd.DataFrame:
        """
        Generate a summary table of all algorithms across metrics.
        
        Args:
            metrics: List of metrics to include
            
        Returns:
            DataFrame with algorithms as rows, metrics as columns
        """
        rows = []
        for algo in self.algorithms:
            row = {'Algorithm': algo.name}
            for metric in metrics:
                stats_list = self.compute_statistics(metric)
                for s in stats_list:
                    if s.algorithm == algo.name:
                        row[f'{metric}_mean'] = s.mean
                        row[f'{metric}_std'] = s.std
                        row[f'{metric}_ci'] = f"[{s.ci_lower:.3f}, {s.ci_upper:.3f}]"
            rows.append(row)
        
        return pd.DataFrame(rows)


# =============================================================================
# STATISTICAL UTILITIES
# =============================================================================

def compute_cohens_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Compute Cohen's d effect size between two groups.
    
    Interpretation:
        |d| < 0.2: Negligible
        0.2 <= |d| < 0.5: Small
        0.5 <= |d| < 0.8: Medium
        |d| >= 0.8: Large
        |d| >= 1.0: Very Large (our threshold for "practical significance")
    
    Args:
        group1: First group's values
        group2: Second group's values
        
    Returns:
        Cohen's d effect size
    """
    n1, n2 = len(group1), len(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    
    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return 0.0
    
    return (np.mean(group1) - np.mean(group2)) / pooled_std


def compute_jains_fairness(allocations: np.ndarray) -> float:
    """
    Compute Jain's Fairness Index for resource allocation.
    
    The index ranges from 1/n (completely unfair) to 1 (perfectly fair).
    
    Formula: J(x) = (sum(x_i))^2 / (n * sum(x_i^2))
    
    Args:
        allocations: Array of resource allocations per entity
        
    Returns:
        Fairness index between 0 and 1
    """
    n = len(allocations)
    if n == 0:
        return 0.0
    
    sum_x = np.sum(allocations)
    sum_x_sq = np.sum(allocations ** 2)
    
    if sum_x_sq == 0:
        return 1.0  # All zeros = perfectly fair (everyone gets nothing)
    
    return (sum_x ** 2) / (n * sum_x_sq)


def bootstrap_ci(
    data: np.ndarray,
    statistic: Callable[[np.ndarray], float] = np.mean,
    n_bootstrap: int = 10000,
    confidence: float = 0.95
) -> Tuple[float, float]:
    """
    Compute bootstrap confidence interval for any statistic.
    
    Args:
        data: Sample data
        statistic: Function to compute (default: mean)
        n_bootstrap: Number of bootstrap samples
        confidence: Confidence level (default: 0.95)
        
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    n = len(data)
    bootstrap_stats = np.zeros(n_bootstrap)
    
    for i in range(n_bootstrap):
        sample = np.random.choice(data, size=n, replace=True)
        bootstrap_stats[i] = statistic(sample)
    
    alpha = 1 - confidence
    lower = np.percentile(bootstrap_stats, 100 * alpha / 2)
    upper = np.percentile(bootstrap_stats, 100 * (1 - alpha / 2))
    
    return lower, upper


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    'SimulationResult',
    'AlgorithmStats', 
    'PairwiseComparison',
    'Scenario',
    'Algorithm',
    'TournamentRunner',
    'compute_cohens_d',
    'compute_jains_fairness',
    'bootstrap_ci'
]











