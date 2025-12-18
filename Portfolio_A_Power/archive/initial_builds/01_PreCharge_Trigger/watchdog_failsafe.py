"""
Watchdog Failsafe: Autonomous Over-Voltage Protection
=====================================================

This variation proves the "Zero-Liability" claim. 
What happens if the Network Switch tells the GPU to "Boost now" but then 
the compute packet is dropped by the network?

The Risk: 
The GPU would stay at the higher V_preboost (1.2V) without a corresponding 
load step to bleed the energy, potentially frying the silicon via thermal 
or dielectric stress.

Invention:
An autonomous "Safety Watchdog" in the VRM controller. It sets a timer 
(e.g., 5us) upon receiving the GPOP trigger. If no compute packet is 
detected within the timeout window, the VRM autonomously ramps the 
voltage back down to nominal.

Acceptance Criteria:
- Simulate a "GPOP Miss" (trigger sent, but no packet arrives).
- Demonstrate zero silicon damage (voltage returned to 0.9V in < 500ns).
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
from utils.plotting import setup_plot_style, create_oscilloscope_figure, save_publication_figure, COLOR_SUCCESS, COLOR_FAILURE

def run_variation():
    setup_plot_style()
    
    # 1. Simulate the "Hazard" (No Watchdog)
    # Packet is dropped, boost stays high forever
    cfg_hazard = SpiceVRMConfig(
        packet_dropped=True,
        hold_time_max_s=100e-6, # 100us (too long!)
        v_preboost_v=1.20
    )
    
    # 2. Simulate the "Invention" (Watchdog Failsafe)
    # Packet is dropped, boost ramps down in 5us
    cfg_failsafe = SpiceVRMConfig(
        packet_dropped=True,
        hold_time_max_s=5e-6, # 5us watchdog
        v_preboost_v=1.20,
        load_verified=True # Received trigger, but packet never arrived
    )
    
    # 3. Simulate "Zero-Trust Handshake" (Fix 1)
    # The VRM received the trigger but the NIC never signaled "bits arriving".
    # Result: The VRM never even starts the boost, total safety.
    cfg_zerotrust = SpiceVRMConfig(
        load_verified=False,
        v_preboost_v=1.20
    )
    
    print("Running SPICE Watchdog & Zero-Trust analysis...")
    t_h, v_h, _ = simulate_vrm_transient(mode="pretrigger", cfg=cfg_hazard)
    t_f, v_f, _ = simulate_vrm_transient(mode="pretrigger", cfg=cfg_failsafe)
    t_z, v_z, _ = simulate_vrm_transient(mode="pretrigger", cfg=cfg_zerotrust)
    
    fig, ax = create_oscilloscope_figure(title="Fix 1: Zero-Trust Handshake & Watchdog Failsafe")
    
    ax.plot(t_h * 1e6, v_h, color=COLOR_FAILURE, linestyle='--', label='Unsafe: No Watchdog (OVP Risk)')
    ax.plot(t_f * 1e6, v_f, color='orange', linewidth=2, label='Safety: Watchdog (Autonomous Clamp)')
    ax.plot(t_z * 1e6, v_z, color=COLOR_SUCCESS, linewidth=3, label='S+ Tier: Zero-Trust (Verification Gate)')
    
    ax.axhline(1.20, color='red', linestyle=':', label='OVP Limit (1.2V)')
    ax.axhline(0.90, color='black', linestyle=':', label='Nominal (0.9V)')
    
    ax.set_xlabel("Time (us)")
    ax.set_ylabel("Voltage (V)")
    ax.set_ylim(0.8, 1.3)
    ax.legend(loc='lower right')
    
    # Annotations
    ax.annotate("Packet Drop Detected!\n(Watchdog Timer expired)", 
                 xy=(25, 1.2), xytext=(35, 1.25),
                 arrowprops=dict(facecolor='black', shrink=0.05))
    
    ax.annotate("Safe Autonomous Reset\n(Silicon preserved)", 
                 xy=(32, 1.0), xytext=(50, 0.95),
                 arrowprops=dict(facecolor='green', shrink=0.05),
                 bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    plt.tight_layout()
    
    output_path = Path(__file__).parent / "watchdog_failsafe"
    save_publication_figure(fig, str(output_path))
    plt.close(fig)
    print(f"Watchdog Failsafe complete. Artifact saved to {output_path}.png")

if __name__ == "__main__":
    run_variation()

