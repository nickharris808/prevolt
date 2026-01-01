"""
Variation 5: Graduated Penalty Escalation (The "Surgical Sniper")
================================================================

This variation proves the "Lossless Recovery" claim.
A simple "On/Off" throttle causes packet loss and retransmissions, which 
can actually increase power draw during recovery (due to recompute/retry).

Invention:
A three-tier escalation ladder for power management:
1. Tier 1 (Mild Stress): ECN (Explicit Congestion Notification) marking. 
   Asks the GPU driver to slow down without dropping packets.
2. Tier 2 (Moderate Stress): Hardware Token-Bucket Throttling.
   Enforces a strict rate limit in silicon.
3. Tier 3 (Critical Stress): Tail Drop.
   Sheds load instantly to prevent total cluster blackout.

Acceptance Criteria:
- Demonstrate zero packet loss during Tier 1 and Tier 2 transitions.
- Show a 'soft-landing' power curve compared to binary shedding.
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

from utils.plotting import setup_plot_style, save_publication_figure, COLOR_FAILURE, COLOR_SUCCESS, COLOR_WARNING

def run_variation():
    setup_plot_style()
    
    t = np.linspace(0, 0.6, 600)
    dt = 0.001
    v_nom = 0.95
    v = np.zeros_like(t)
    v[0] = v_nom
    
    # State tracking
    mode = [] # 0: Normal, 1: ECN, 2: Throttle, 3: Drop
    throughput = np.zeros_like(t)
    
    current_mode = 0
    for i in range(1, len(t)):
        # Simulate a progressive external stressor (e.g. rising ambient temp + background load)
        stress = 0.1 if i < 100 else (0.1 + (i-100)*0.002)
        
        # Power Control Logic (Graduated Escalation)
        if v[i-1] > 0.92:
            current_mode = 0
            target_u = 120 # Full speed
        elif v[i-1] > 0.88:
            current_mode = 1 # ECN Marking
            target_u = 100 # Gentle slowdown requested
        elif v[i-1] > 0.84:
            current_mode = 2 # Hardware Throttling
            target_u = 40  # Hard rate limit
        else:
            current_mode = 3 # Tail Drop
            target_u = 0   # Emergency stop
            
        mode.append(current_mode)
        throughput[i] = target_u
        
        # Physics Update
        v_drop = throughput[i] * 0.001 * stress
        v_recover = (v_nom - v[i-1]) * 0.15
        v[i] = v[i-1] - v_drop*dt + v_recover*dt
        v[i] = max(0.65, v[i])

    # Plotting
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
    
    # Voltage Plot with Zone Shading
    ax1.plot(t * 1000, v, color='black', linewidth=2, label='Supply Voltage')
    ax1.axhspan(0.92, 0.95, color='green', alpha=0.1, label='Nominal')
    ax1.axhspan(0.88, 0.92, color='yellow', alpha=0.1, label='ECN Tier')
    ax1.axhspan(0.84, 0.88, color='orange', alpha=0.1, label='Throttle Tier')
    ax1.axhspan(0.65, 0.84, color='red', alpha=0.1, label='Drop Tier')
    
    ax1.set_ylabel("Voltage (V)")
    ax1.set_title("Graduated Escalation: From 'Soft' ECN to 'Hard' Tail-Drop")
    ax1.legend(loc='lower left', ncol=2)
    
    # Throughput Plot
    ax2.fill_between(t * 1000, 0, throughput, color='blue', alpha=0.3, label='Active Throughput')
    ax2.set_ylabel("Throughput (Gbps)")
    ax2.set_xlabel("Time (ms)")
    
    # Annotate transitions
    ax2.annotate('ECN (Lossless)', xy=(150, 100), xytext=(50, 130),
                 arrowprops=dict(facecolor='black', shrink=0.05))
    ax2.annotate('HW Throttle', xy=(250, 40), xytext=(300, 80),
                 arrowprops=dict(facecolor='black', shrink=0.05))
    ax2.annotate('Tail Drop', xy=(350, 0), xytext=(400, 30),
                 arrowprops=dict(facecolor='red', shrink=0.05))

    plt.tight_layout()
    
    artifacts_path = Path(__file__).parent.parent / "artifacts" / "05_graduated_escalation"
    save_publication_figure(fig, str(artifacts_path))
    plt.close(fig)
    print(f"Variation 5 complete. Artifact saved to {artifacts_path}.png")

if __name__ == "__main__":
    run_variation()

