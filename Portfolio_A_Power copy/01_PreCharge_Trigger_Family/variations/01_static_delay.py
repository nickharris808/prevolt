"""01_PreCharge_Trigger/simulation.py

Portfolio A — Patent Family 1: The "Pre-Cognitive" Voltage Trigger
==================================================================

This script produces the *data room artifact* for the Pre-Charge Trigger patent:

- `voltage_trace.png`: transient response plot showing baseline crash (red)
  vs. pre-trigger stable (green).

It is built to satisfy the user-specified, explicit acceptance criteria:

Acceptance Criteria (Pass/Fail)
-------------------------------
1) Baseline:
   - Simulate a 500A load step
   - Voltage must drop below 0.7V (FAIL case)

2) Invention:
   - Same 500A load step
   - With a 14µs pre-trigger
   - Voltage must never drop below 0.9V (PASS case)

3) Efficiency:
   - Added delay must be < 20µs

Implementation Notes
--------------------
- Uses **PySpice + ngspice** for circuit-physics simulation.
- The VRM control-loop response is modeled as a first-order system (15µs tau)
  that ramps the VRM setpoint upward when the switch pre-triggers.

Run:
  python simulation.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

import sys
from pathlib import Path
# Add parent to path for SPICE model and utils
sys.path.insert(0, str(Path(__file__).parent.parent))
from spice_vrm import SpiceVRMConfig, simulate_vrm_transient, check_acceptance_criteria

# Use shared plotting utilities
import sys, os
from pathlib import Path
root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root))
family = Path(__file__).parent.parent
sys.path.insert(0, str(family))
from spice_vrm import SpiceVRMConfig, simulate_vrm_transient, check_acceptance_criteria
from utils.plotting import (
    setup_plot_style,
    create_oscilloscope_figure,
    save_publication_figure,
    COLOR_FAILURE,
    COLOR_SUCCESS,
)


def generate_transient_response_plot(*, cfg: SpiceVRMConfig, out_basepath: Path) -> None:
    """Generate the red vs green transient response figure."""

    t_b, v_b, _ = simulate_vrm_transient(mode="baseline", cfg=cfg)
    t_p, v_p, _ = simulate_vrm_transient(mode="pretrigger", cfg=cfg)

    # Ngspice may return slightly different time grids depending on step control.
    # Plot each trace against its own time vector.
    t_us_b = t_b * 1e6
    t_us_p = t_p * 1e6

    setup_plot_style()
    fig, ax = create_oscilloscope_figure(
        figsize=(14, 8),
        title="Pre-Cognitive Voltage Trigger: Transient Response (500A Load Step)",
    )

    # Threshold lines
    ax.axhline(0.90, color="#333333", linestyle=":", linewidth=1.2, alpha=0.8)
    ax.axhline(0.70, color="#AA0000", linestyle="--", linewidth=1.2, alpha=0.8)

    # Traces
    ax.plot(t_us_b, v_b, color=COLOR_FAILURE, linewidth=2.8,
            label=f"Baseline: min={np.min(v_b):.3f}V (must be <0.70V)")
    ax.plot(t_us_p, v_p, color=COLOR_SUCCESS, linewidth=2.8,
            label=f"Pre-trigger (14µs): min={np.min(v_p):.3f}V (must be ≥0.90V)")

    # Load step marker
    ax.axvline(cfg.t_load_start_s * 1e6, color="#666666", linestyle=":", linewidth=1.5, alpha=0.7)
    ax.text(cfg.t_load_start_s * 1e6 + 0.5, 0.995,
            "Load step start",
            fontsize=9, va="top", ha="left", color="#666666")

    ax.set_xlabel("Time (µs)")
    ax.set_ylabel("V(out) (V)")
    ax.set_xlim(0, cfg.t_stop_s * 1e6)
    ax.set_ylim(0.60, 1.10)
    ax.legend(loc="upper right", framealpha=0.95)

    # Acceptance summary
    checks = check_acceptance_criteria(cfg)
    summary = (
        f"Acceptance: baseline_min={checks['baseline_min_v']:.3f}V (<0.70) | "
        f"pretrigger_min={checks['pretrigger_min_v']:.3f}V (≥0.90) | "
        f"delay={checks['added_delay_us']:.1f}µs (<20) | overall={checks['overall_pass']}"
    )
    fig.text(0.5, 0.02, summary, ha="center", fontsize=10, style="italic", color="#444444")

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.09)

    save_publication_figure(fig, str(out_basepath), dpi=300, formats=["png"])
    plt.close(fig)


def main() -> None:
    out_dir = Path(__file__).parent

    cfg = SpiceVRMConfig(
        # These are the exact acceptance-criteria numbers.
        i_step_a=500.0,
        t_load_start_s=20e-6,
        pretrigger_lead_s=14e-6,
        vrm_tau_s=15e-6,
    )

    checks = check_acceptance_criteria(cfg)

    print("=" * 80)
    print("PRE-COGNITIVE VOLTAGE TRIGGER (SPICE)")
    print("=" * 80)
    print(f"Baseline min V(out):   {checks['baseline_min_v']:.6f} V")
    print(f"Pretrigger min V(out): {checks['pretrigger_min_v']:.6f} V")
    print(f"Added delay:           {checks['added_delay_us']:.2f} µs")
    print(f"Overall pass:          {checks['overall_pass']}")

    generate_transient_response_plot(cfg=cfg, out_basepath=out_dir / "voltage_trace")
    print(f"Saved: {out_dir / 'voltage_trace.png'}")


if __name__ == "__main__":
    main()
