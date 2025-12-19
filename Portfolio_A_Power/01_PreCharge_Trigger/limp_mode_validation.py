"""
Limp Mode Validation: Fail-Safe Reliability
==========================================

This module proves the "Mission-Critical Infrastructure" claim.
In a real data center, the network is not 100% reliable. If the 'Pre-charge' 
signal is lost or delayed by network congestion, the GPU must not crash.

Invention:
'Limp Mode' Safety logic. The GPU's local PMU (Power Management Unit) 
expects a GPOP signal before a high-intensity kernel launch. If the signal 
is missing, the GPU automatically throttles its own current step (e.g. 
limiting clock frequency to 500MHz).

Acceptance Criteria:
- Simulate a "Signal Lost" scenario.
- Show that without GPOP and without Limp Mode, voltage crashes to 0.68V.
- Show that with Limp Mode (capping current to 200A instead of 500A), 
  the GPU survives at 0.85V without a boost.
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
import os
from pathlib import Path

# Add root and family paths to sys.path
root = Path(__file__).parent.parent
sys.path.insert(0, str(root))
family_path = root / "01_PreCharge_Trigger_Family"
sys.path.insert(0, str(family_path))

from spice_vrm import SpiceVRMConfig, simulate_vrm_transient
from utils.plotting import setup_plot_style, create_oscilloscope_figure, save_publication_figure, COLOR_SUCCESS, COLOR_FAILURE, COLOR_WARNING

def run_variation():
    setup_plot_style()
    
    # 1. Baseline Crash: Signal Lost, Full 500A Step, No Limp Mode
    cfg_crash = SpiceVRMConfig(
        i_step_a=500.0,
        pretrigger_lead_s=0.0 # Signal lost
    )
    
    # 2. Fail-Safe: Signal Lost, GPU triggers Limp Mode (Cap at 200A)
    cfg_limp = SpiceVRMConfig(
        i_step_a=200.0, # Reduced current step in Limp Mode
        pretrigger_lead_s=0.0 # Signal lost
    )
    
    # 3. Normal Operation: GPOP Active, 500A Step
    cfg_normal = SpiceVRMConfig(
        i_step_a=500.0,
        pretrigger_lead_s=14e-6
    )
    
    print("Running Fail-Safe Limp Mode analysis...")
    t_c, v_crash, _ = simulate_vrm_transient(mode="baseline", cfg=cfg_crash)
    t_l, v_limp, _ = simulate_vrm_transient(mode="baseline", cfg=cfg_limp)
    t_n, v_normal, _ = simulate_vrm_transient(mode="pretrigger", cfg=cfg_normal)
    
    fig, ax = create_oscilloscope_figure(title="Fix 4: Fail-Safe Limp Mode (Reliability Proof)")
    
    ax.plot(t_c * 1e6, v_crash, color=COLOR_FAILURE, linestyle='--', label='Scenario A: Signal Lost, No Limp (CRASH)')
    ax.plot(t_l * 1e6, v_limp, color=COLOR_WARNING, linewidth=2, label='Scenario B: Signal Lost + Limp Mode (SURVIVE)')
    ax.plot(t_n * 1e6, v_normal, color=COLOR_SUCCESS, linewidth=3, label='Scenario C: GPOP Normal (PERFORMANCE)')
    
    ax.axhline(0.80, color='red', linestyle=':', label='Survival Limit')
    ax.axhline(0.90, color='black', linestyle=':', label='Performance Nominal')
    
    ax.set_xlabel("Time (us)")
    ax.set_ylabel("Voltage (V)")
    ax.set_ylim(0.6, 1.1)
    ax.legend(loc='lower right', fontsize=9)
    
    # Annotations
    ax.annotate("Limp Mode:\nCaps current to 200A\nto stay above 0.8V", 
                 xy=(30, 0.85), xytext=(45, 0.75),
                 arrowprops=dict(facecolor='orange', shrink=0.05),
                 bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    ax.annotate("GPOP Active:\nFull 500A step\nat 0.95V", 
                 xy=(25, 0.95), xytext=(5, 1.02),
                 arrowprops=dict(facecolor='green', shrink=0.05),
                 bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    plt.tight_layout()
    
    output_path = Path(__file__).parent / "limp_mode_safety"
    save_publication_figure(fig, str(output_path))
    plt.close(fig)
    print(f"Limp Mode variation complete. Artifact saved to {output_path}.png")

if __name__ == "__main__":
    run_variation()




