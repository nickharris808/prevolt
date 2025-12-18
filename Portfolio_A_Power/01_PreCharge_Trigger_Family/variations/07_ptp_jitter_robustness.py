"""
Variation 7: PTP-Synchronized Timing Robustness
==============================================

This variation proves the "PTP Robustness" claim.
In a real fabric, the Switch and GPU clocks might drift (PTP Sync Error). 
The invention uses future timestamps to coordinate the trigger.

Simulation:
We inject +/- 2.0us of random clock jitter between the Switch and the VRM.
Goal: Show that even with sync error, V_min remains above 0.9V because 
the 14us lead-time provides a sufficient "Timing Margin."

Value Add: 
This moves the claim from "Simple Delay" to "Fabric-wide Synchronization," 
which is a Tier-1 standards requirement.
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
import os
from pathlib import Path

# Add root and family paths to sys.path
root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root))
family = Path(__file__).parent.parent
sys.path.insert(0, str(family))

from spice_vrm import SpiceVRMConfig, simulate_vrm_transient
from utils.plotting import setup_plot_style, create_oscilloscope_figure, save_publication_figure, COLOR_SUCCESS, COLOR_FAILURE, COLOR_WARNING

def run_variation():
    setup_plot_style()
    
    # Range of PTP sync errors to test
    sync_errors_us = [-2.0, -1.0, 0.0, 1.0, 2.0]
    
    fig, ax = create_oscilloscope_figure(title="Variation 7: PTP Sync Jitter Robustness (+/- 2us)")
    
    # Baseline for reference (No Trigger)
    cfg_base = SpiceVRMConfig()
    t_b, v_b, _ = simulate_vrm_transient(mode="baseline", cfg=cfg_base)
    ax.plot(t_b * 1e6, v_b, color=COLOR_FAILURE, alpha=0.3, label='Baseline (Crash)')

    # Iterate through sync errors
    colors = plt.cm.viridis(np.linspace(0, 1, len(sync_errors_us)))
    
    v_mins = []
    for i, err in enumerate(sync_errors_us):
        cfg = SpiceVRMConfig(ptp_sync_error_s=err*1e-6)
        t, v, _ = simulate_vrm_transient(mode="pretrigger", cfg=cfg)
        
        label = f"Sync Error: {err:+.1f}us (Vmin={np.min(v):.2f}V)"
        ax.plot(t * 1e6, v, color=colors[i], label=label)
        v_mins.append(np.min(v))

    ax.axhline(0.9, color='black', linestyle='--')
    ax.set_xlabel("Time (us)")
    ax.set_ylabel("V(out) (V)")
    ax.legend(fontsize=8, loc='lower right')
    
    # Acceptance Annotation
    if all(v >= 0.9 for v in v_mins):
        ax.text(50, 0.65, "✓ ROBUST: All scenarios stay above 0.9V", 
                bbox=dict(facecolor='green', alpha=0.2), fontweight='bold')
    
    artifacts_path = Path(__file__).parent.parent / "artifacts" / "07_ptp_robustness"
    save_publication_figure(fig, str(artifacts_path))
    plt.close(fig)
    print(f"Variation 7 complete. Artifact saved to {artifacts_path}.png")

if __name__ == "__main__":
    run_variation()

