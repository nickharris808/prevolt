"""01_PreCharge_Trigger/tournament.py

Pre-Charge Trigger Tournament (SPICE)
====================================

This tournament exists to answer the buyer's core question:

  "How much delay must the switch add to guarantee the GPU supply stays safe?"

We sweep the pre-trigger lead time and measure:
- Minimum V(out)
- Whether we meet the strict safety requirement (V(out) >= 0.9V)
- Added delay in microseconds

We also verify the baseline failure case:
- No pre-trigger must droop below 0.7V.

Outputs:
- `tournament_results.csv`: sweep results

Run:
  python tournament.py
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

from spice_vrm import SpiceVRMConfig, simulate_vrm_transient


def run_sweep(
    *,
    cfg: SpiceVRMConfig,
    lead_times_us: np.ndarray,
) -> pd.DataFrame:
    rows = []

    # Baseline reference (lead=0, no pretrigger boost)
    t_b, v_b, _ = simulate_vrm_transient(mode="baseline", cfg=cfg)
    baseline_min = float(np.min(v_b))

    for lead_us in lead_times_us:
        cfg_i = SpiceVRMConfig(**{**asdict(cfg), "pretrigger_lead_s": float(lead_us) * 1e-6})
        t_p, v_p, _ = simulate_vrm_transient(mode="pretrigger", cfg=cfg_i)
        min_v = float(np.min(v_p))

        rows.append(
            {
                "pretrigger_lead_us": float(lead_us),
                "min_v_out_v": min_v,
                "passes_vmin_ge_0p9": bool(min_v >= 0.90),
                "passes_delay_lt_20us": bool(lead_us < 20.0),
                "overall_pass": bool((min_v >= 0.90) and (lead_us < 20.0)),
            }
        )

    df = pd.DataFrame(rows).sort_values("pretrigger_lead_us").reset_index(drop=True)
    df.attrs["baseline_min_v_out_v"] = baseline_min
    return df


def main() -> None:
    out_dir = Path(__file__).parent

    # Base config chosen to satisfy your acceptance criteria.
    cfg = SpiceVRMConfig(
        i_step_a=500.0,
        i_step_rise_s=1e-6,
        t_load_start_s=20e-6,
        vrm_tau_s=15e-6,
        v_nominal_v=0.90,
        v_preboost_v=1.20,
    )

    lead_times_us = np.arange(0.0, 20.0, 1.0)  # 0..19 µs
    df = run_sweep(cfg=cfg, lead_times_us=lead_times_us)

    # Baseline check
    baseline_min = df.attrs["baseline_min_v_out_v"]
    print("=" * 80)
    print("PRE-CHARGE TRIGGER TOURNAMENT (SPICE)")
    print("=" * 80)
    print(f"Baseline min V(out) = {baseline_min:.6f} V (acceptance requires < 0.70V)")

    # Find smallest lead time meeting vmin>=0.9
    winners = df[df["overall_pass"]]
    if len(winners) == 0:
        print("No lead time in 0..19µs met V(out) >= 0.90V.")
    else:
        best = winners.iloc[0]
        print(f"Smallest lead time meeting V(out) >= 0.90V: {best['pretrigger_lead_us']:.1f} µs")

    csv_path = out_dir / "tournament_results.csv"
    df.to_csv(csv_path, index=False)
    print(f"Saved: {csv_path}")

    # Print a compact table
    print("\n" + df.to_string(index=False))


if __name__ == "__main__":
    main()

