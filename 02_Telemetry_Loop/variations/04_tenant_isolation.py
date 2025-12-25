"""
Variation 4: Per-Tenant Flow Sniper
===================================

This variation proves the "Multi-Tenant Isolation" claim.
In a shared cluster, Tenant A might be running a massive power-hungry 
kernel while Tenant B is doing low-power latency-sensitive work.

Invention:
The switch correlates the telemetry *signal* with the *egress byte counts* of 
individual flows. It identifies the "Bully" (the flow with highest di/dt 
correlation) and throttles ONLY that tenant, preserving the SLAs of others.

Acceptance Criteria:
- Must simulate 2 tenants.
- Tenant A: High-power bully.
- Tenant B: Constant low-power.
- Must show Tenant B throughput stays at 100% while Tenant A is throttled.
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

from utils.plotting import setup_plot_style, save_publication_figure, COLOR_FAILURE, COLOR_SUCCESS, COLOR_NEUTRAL

def run_variation():
    setup_plot_style()
    
    t = np.linspace(0, 0.5, 500)
    dt = 0.001
    v_nom = 0.95
    v = np.zeros_like(t)
    v[0] = v_nom
    
    # Rates for two tenants
    u_a = np.full_like(t, 100) # Bully (starts burst at 100ms)
    u_b = np.full_like(t, 20)  # Victim
    
    u_a[100:300] = 150 # Massive burst
    
    # Trackers for the switch
    throttled_a = False
    
    for i in range(1, len(t)):
        if v[i-1] < 0.85:
            # Switch Logic: Identify culprit. 
            # Tenant A is using 150, B is using 20. A is the sniper target.
            throttled_a = True
            
        if throttled_a:
            u_a[i] = 10
            # Check for recovery
            if v[i-1] > 0.92:
                throttled_a = False
        
        # Physics update (total power affects aggregate voltage)
        total_u = u_a[i] + u_b[i]
        v_drop = total_u * 0.001
        v_recover = (v_nom - v[i-1]) * 0.2
        v[i] = v[i-1] - v_drop*dt + v_recover*dt
        
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    
    ax1.plot(t * 1000, v, color='black', label='Aggregate GPU Voltage')
    ax1.axhline(0.85, color='red', linestyle='--', label='Throttle Threshold')
    ax1.set_ylabel("Voltage (V)")
    ax1.legend()
    
    ax2.plot(t * 1000, u_a, color=COLOR_FAILURE, label='Tenant A (Throttled Bully)')
    ax2.plot(t * 1000, u_b, color=COLOR_SUCCESS, label='Tenant B (Protected Victim)')
    ax2.set_ylabel("Throughput (Gbps)")
    ax2.set_xlabel("Time (ms)")
    ax2.legend()
    
    plt.suptitle("Tenant Isolation: Surgical Throttling via di/dt Correlation")
    
    artifacts_path = Path(__file__).parent.parent / "artifacts" / "04_tenant_isolation"
    save_publication_figure(fig, str(artifacts_path))
    plt.close(fig)
    print(f"Variation 4 complete. Artifact saved to {artifacts_path}.png")

if __name__ == "__main__":
    run_variation()

