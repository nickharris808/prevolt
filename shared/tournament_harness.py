"""
Tournament Harness - Shared Infrastructure for Algorithm Comparison
====================================================================

This is a lightweight harness used by Portfolio-B-style simulations in this repo
(`src/network/incast_backpressure/`, `src/memory/noisy_neighbor/`, etc).

The goal is *runnability* and *reproducibility*:
- seeded trials
- simple summary stats (mean/std/CI/percentiles)
- optional pairwise comparisons (Welch t-test when SciPy is available)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import math
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

try:
    from scipy import stats as _stats  # type: ignore
except Exception:  # pragma: no cover
    _stats = None


@dataclass(frozen=True)
class SimulationResult:
    algorithm: str
    scenario: str
    trial: int
    metrics: Dict[str, float]
    duration_seconds: float
    seed: int


@dataclass(frozen=True)
class AlgorithmStats:
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


@dataclass(frozen=True)
class PairwiseComparison:
    algorithm_a: str
    algorithm_b: str
    metric: str
    mean_diff: float
    t_statistic: float
    p_value: float
    cohens_d: float
    significant: bool
    practical: bool


@dataclass(frozen=True)
class Scenario:
    name: str
    params: Dict[str, Any]
    description: str = ""


class Algorithm(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def run(self, scenario: Scenario, seed: int) -> Dict[str, float]:
        raise NotImplementedError


def _progress(iterable, *, enabled: bool, total: int, desc: str):
    if not enabled:
        return iterable
    try:
        from tqdm import tqdm  # type: ignore

        return tqdm(iterable, total=total, desc=desc, unit="trial")
    except Exception:  # pragma: no cover
        return iterable


def _welch_ttest(a: np.ndarray, b: np.ndarray) -> Tuple[float, float]:
    if a.size < 2 or b.size < 2:
        return float("nan"), float("nan")

    if _stats is None:
        # Fall back to t-statistic only; p-value requires a t CDF implementation.
        ma = float(np.mean(a))
        mb = float(np.mean(b))
        va = float(np.var(a, ddof=1))
        vb = float(np.var(b, ddof=1))
        denom = math.sqrt(va / a.size + vb / b.size)
        t = (ma - mb) / denom if denom > 0 else float("nan")
        return t, float("nan")

    res = _stats.ttest_ind(a, b, equal_var=False)  # Welch
    return float(res.statistic), float(res.pvalue)


class TournamentRunner:
    def __init__(
        self,
        *,
        algorithms: List[Algorithm],
        scenarios: List[Scenario],
        n_trials: int = 1000,
        base_seed: int = 42,
        metrics_to_track: Optional[List[str]] = None,
        higher_is_better: Optional[Dict[str, bool]] = None,
    ):
        self.algorithms = algorithms
        self.scenarios = scenarios
        self.n_trials = int(n_trials)
        self.base_seed = int(base_seed)
        self.metrics_to_track = metrics_to_track
        self.higher_is_better = higher_is_better or {}

        self.results: List[SimulationResult] = []
        self.results_df: Optional[pd.DataFrame] = None

    def run(self, *, show_progress: bool = True) -> pd.DataFrame:
        self.results = []
        rows: List[Dict[str, Any]] = []

        total_runs = len(self.algorithms) * len(self.scenarios) * self.n_trials
        run_idx = 0

        iterator = _progress(
            range(total_runs),
            enabled=show_progress,
            total=total_runs,
            desc="Running tournament",
        )

        # We don't use the iterator values directly; it's just for progress reporting.
        for _ in iterator:
            algo = self.algorithms[(run_idx // (len(self.scenarios) * self.n_trials)) % len(self.algorithms)]
            scenario = self.scenarios[(run_idx // self.n_trials) % len(self.scenarios)]
            trial = run_idx % self.n_trials
            seed = self.base_seed + run_idx

            start = time.time()
            metrics = algo.run(scenario, seed)
            duration = time.time() - start

            if self.metrics_to_track is not None:
                metrics = {k: float(metrics[k]) for k in self.metrics_to_track if k in metrics}
            else:
                metrics = {k: float(v) for k, v in metrics.items()}

            self.results.append(
                SimulationResult(
                    algorithm=algo.name,
                    scenario=scenario.name,
                    trial=trial,
                    metrics=metrics,
                    duration_seconds=duration,
                    seed=seed,
                )
            )

            rows.append(
                {
                    "algorithm": algo.name,
                    "scenario": scenario.name,
                    "trial": trial,
                    "seed": seed,
                    "duration_seconds": duration,
                    **metrics,
                }
            )

            run_idx += 1

        self.results_df = pd.DataFrame(rows)
        return self.results_df

    def _require_results(self) -> pd.DataFrame:
        if self.results_df is None:
            raise RuntimeError("TournamentRunner has no results yet; call run() first.")
        return self.results_df

    def compute_statistics(self, metric: str) -> List[AlgorithmStats]:
        df = self._require_results()
        if metric not in df.columns:
            # Return empty list rather than throwing; lets callers continue.
            return []

        out: List[AlgorithmStats] = []
        for algo in self.algorithms:
            vals = df[df["algorithm"] == algo.name][metric].astype(float).to_numpy()
            if vals.size == 0:
                continue

            mean = float(np.mean(vals))
            std = float(np.std(vals, ddof=1)) if vals.size >= 2 else 0.0
            n = int(vals.size)

            if n >= 2 and std > 0:
                se = std / math.sqrt(n)
                half = 1.96 * se
                ci_lower = mean - half
                ci_upper = mean + half
            else:
                ci_lower = mean
                ci_upper = mean

            out.append(
                AlgorithmStats(
                    algorithm=algo.name,
                    metric=metric,
                    mean=mean,
                    std=std,
                    ci_lower=float(ci_lower),
                    ci_upper=float(ci_upper),
                    median=float(np.median(vals)),
                    p5=float(np.percentile(vals, 5)),
                    p95=float(np.percentile(vals, 95)),
                    n_samples=n,
                )
            )

        return out

    def compare_algorithms(self, metric: str, baseline_name: str) -> List[PairwiseComparison]:
        df = self._require_results()
        if metric not in df.columns:
            return []

        base = df[df["algorithm"] == baseline_name][metric].astype(float).to_numpy()
        out: List[PairwiseComparison] = []

        for algo in self.algorithms:
            if algo.name == baseline_name:
                continue
            a = df[df["algorithm"] == algo.name][metric].astype(float).to_numpy()
            if a.size == 0 or base.size == 0:
                continue

            mean_a = float(np.mean(a))
            mean_b = float(np.mean(base))
            mean_diff = mean_a - mean_b

            t_stat, p_val = _welch_ttest(a, base)

            std_a = float(np.std(a, ddof=1)) if a.size >= 2 else 0.0
            std_b = float(np.std(base, ddof=1)) if base.size >= 2 else 0.0
            pooled = math.sqrt((std_a**2 + std_b**2) / 2.0) if (std_a > 0 or std_b > 0) else 0.0
            cohens_d = (mean_diff / pooled) if pooled > 0 else 0.0

            significant = (not math.isnan(p_val)) and (p_val < 1e-3)
            practical = abs(cohens_d) > 1.0

            out.append(
                PairwiseComparison(
                    algorithm_a=algo.name,
                    algorithm_b=baseline_name,
                    metric=metric,
                    mean_diff=float(mean_diff),
                    t_statistic=float(t_stat),
                    p_value=float(p_val),
                    cohens_d=float(cohens_d),
                    significant=bool(significant),
                    practical=bool(practical),
                )
            )

        return out

    def determine_winner(self, metric: str) -> Tuple[str, AlgorithmStats]:
        stats = self.compute_statistics(metric)
        if not stats:
            raise RuntimeError(f"No statistics available for metric={metric!r}")

        hib = self.higher_is_better.get(metric, True)
        best = max(stats, key=lambda s: s.mean) if hib else min(stats, key=lambda s: s.mean)
        return best.algorithm, best

