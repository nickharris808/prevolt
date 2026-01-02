"""
Shared utilities used by multiple simulation families.

This package primarily exists to keep "Portfolio B"-style tournament code runnable
from the repo root by providing stable imports like:

  - `from shared.tournament_harness import TournamentRunner`
  - `from shared.visualization import plot_metric_comparison_bar`
  - `from shared.physics_engine import Physics`
"""

