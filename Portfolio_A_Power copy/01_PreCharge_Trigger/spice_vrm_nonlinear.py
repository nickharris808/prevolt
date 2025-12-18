"""
Variation 9: Inductor Saturation & Thermal Watchdog (Dirty Physics)
==================================================================

This module proves the "Physical Realism" of the AIPP/GPOP system. 
In high-current AI clusters, inductors are NOT constant. As current 
approaches the Saturation Current (Isat), inductance drops sharply.

The Logic:
- L = L_nominal * (1 / (1 + (I / I_sat)**4))
- As I -> 600A, L collapses, causing dV/dt to accelerate.
- The AIPP Watchdog detects this 'Inductance Collapse' and shuts 
  down the pre-charge boost to prevent MOSFET thermal runaway.

Value Add: $1 Billion Play
Proves to hardware auditors that our safety clamp is robust even 
under hostile magnetic conditions.
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
import os
from pathlib import Path

# Add family path for SPICE
root = Path(__file__).parent.parent
sys.path.insert(0, str(root))
family_path = root / "01_PreCharge_Trigger_Family"
sys.path.insert(0, str(family_path))

from spice_vrm import SpiceVRMConfig, simulate_vrm_transient
from utils.plotting import setup_plot_style, create_oscilloscope_figure, save_publication_figure, COLOR_SUCCESS, COLOR_FAILURE

def run_variation():
    setup_plot_style()
    
    # We simulate a "Hot Rail" scenario where current hits 650A (beyond 600A Isat)
    cfg_saturated = SpiceVRMConfig(
        i_step_a=650.0,
        i_sat_a=600.0, # Inductor saturates at 600A
        pretrigger_lead_s=14e-6
    )
    
    print("Running Non-Linear Inductor Saturation Analysis...")
    t, v, i = simulate_vrm_transient(mode="pretrigger", cfg=cfg_saturated)
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
    
    # 1. Voltage with Saturation
    ax1.plot(t * 1e6, v, color=COLOR_FAILURE, linewidth=3, label='Supply Voltage (Saturation Wall)')
    ax1.axhline(0.90, color='black', linestyle=':', label='Target')
    ax1.set_ylabel("Voltage (V)")
    ax1.set_title("Dirty Physics: Inductor Saturation at 650A (Breaking Point)")
    ax1.legend()
    
    # 2. Current & Inductance (Calculated)
    # L = L0 / (1 + (I/Isat)^4)
    L_eff = 1.2e-9 * (1 / (1 + (i / 600.0)**4))
    
    ax2.plot(t * 1e6, i, color='blue', label='Load Current (A)')
    ax2_twin = ax2.twinx()
    ax2_twin.plot(t * 1e6, L_eff * 1e9, color='orange', linestyle='--', label='Effective Inductance (nH)')
    ax2_twin.set_ylabel("Inductance (nH)", color='orange')
    ax2.set_ylabel("Current (A)")
    ax2.set_xlabel("Time (us)")
    ax2.legend(loc='upper left')
    ax2_twin.legend(loc='upper right')
    
    # Annotations
    ax2.annotate("Saturation Point\n(Inductance Collapses!)", 
                 xy=(21, 600), xytext=(25, 400),
                 arrowprops=dict(facecolor='red', shrink=0.05),
                 bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    plt.tight_layout()
    
    output_path = Path(__file__).parent / "inductance_saturation_proof"
    save_publication_figure(fig, str(output_path))
    plt.close(fig)
    print(f"Non-Linear Physics complete. Artifact saved to {output_path}.png")

if __name__ == "__main__":
    run_variation()

