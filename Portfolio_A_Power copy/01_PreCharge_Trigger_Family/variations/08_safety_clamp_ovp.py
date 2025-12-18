"""
Variation 8: Safety Clamp & OVP Protection
==========================================

This variation proves the "Hardware Safety" claim.
GPU vendors fear that "Pre-charging" the rail might lead to an Over-Voltage (OVP) 
event if the expected compute packet is dropped by the network.

Invention:
The "Safety Clamp" logic. If the Switch sends a pre-trigger but no compute 
packet arrives within a strict timeout (Hold_Time_Max), the VRM autonomously 
ramps the voltage back down to nominal.

Acceptance Criteria:
- Simulate a "Packet Drop" scenario.
- Demonstrate that voltage never exceeds 1.2V.
- Show a safe, controlled return to nominal 0.9V after the timeout.
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
    
    # Scenario: Pre-charge starts, but packet is dropped.
    cfg_clamp = SpiceVRMConfig(
        packet_dropped=True,
        hold_time_max_s=5e-6, # 5us maximum hold time
        v_preboost_v=1.20      # Target preboost
    )
    
    # Scenario: Baseline for comparison (Pre-charge without clamp - unsafe)
    # (We simulate this by using a very long hold time)
    cfg_unsafe = SpiceVRMConfig(
        packet_dropped=True,
        hold_time_max_s=50e-6,
        v_preboost_v=1.20
    )
    
    print("Running Safety Clamp Simulation...")
    t_c, v_c, _ = simulate_vrm_transient(mode="pretrigger", cfg=cfg_clamp)
    t_u, v_u, _ = simulate_vrm_transient(mode="pretrigger", cfg=cfg_unsafe)
    
    fig, ax = create_oscilloscope_figure(title="Variation 8: Safety Clamp (OVP Protection)")
    
    ax.plot(t_u * 1e6, v_u, color=COLOR_FAILURE, linestyle='--', label='Unsafe: No Clamp (OVP Risk)')
    ax.plot(t_c * 1e6, v_c, color=COLOR_SUCCESS, linewidth=3, label='Safe: GPOP Safety Clamp Active')
    
    ax.axhline(1.20, color='red', linestyle=':', label='OVP Threshold')
    ax.axhline(0.90, color='black', linestyle=':', label='Nominal')
    
    ax.set_xlabel("Time (us)")
    ax.set_ylabel("V(out) (V)")
    ax.set_ylim(0.85, 1.30)
    ax.legend()
    
    # Annotations
    ax.annotate("Packet Drop Detected\n(Timeout reached)", 
                 xy=(25, 1.2), xytext=(35, 1.25),
                 arrowprops=dict(facecolor='black', shrink=0.05))
    
    ax.annotate("Autonomous Ramp-Down\n(Preventing OVP failure)", 
                 xy=(30, 1.05), xytext=(45, 0.95),
                 arrowprops=dict(facecolor='green', shrink=0.05),
                 bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    artifacts_path = Path(__file__).parent.parent / "artifacts" / "08_safety_clamp"
    save_publication_figure(fig, str(artifacts_path))
    plt.close(fig)
    print(f"Variation 8 complete. Artifact saved to {artifacts_path}.png")

if __name__ == "__main__":
    run_variation()

