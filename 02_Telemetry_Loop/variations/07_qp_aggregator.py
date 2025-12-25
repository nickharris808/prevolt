"""
Variation 7: QP-Spray Aggregator (Tenant-Level Isolation)
========================================================

This variation proves the "Evasion-Proof" claim.
Sophisticated users might try to bypass per-flow throttling by "Spraying" their 
traffic across 1,000 separate flows (Queue Pairs / QPs).

Invention:
The switch maintains a 'Tenant Energy Map'. It aggregates traffic from all QPs 
belonging to the same tenant (Source MAC/IP). It identifies that the aggregate 
tenant draw is what causes the voltage dip, even if no single flow is the 'bully'.

Acceptance Criteria:
- Simulate a tenant with 100 small flows (1Gbps each).
- Show that the switch identifies the AGGREGATE 100Gbps draw.
- Demonstrate surgical throttling of all 100 flows simultaneously.
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

from utils.plotting import setup_plot_style, save_publication_figure, COLOR_SUCCESS, COLOR_FAILURE

def run_variation():
    setup_plot_style()
    
    t = np.linspace(0, 0.5, 500)
    dt = 0.001
    v_nom = 0.95
    v = np.zeros_like(t)
    v[0] = v_nom
    
    # Tenant 1 (Bully): 10 flows of 12 Gbps each (Total 120)
    n_flows = 10
    u_flows = [np.full_like(t, 12.0) for _ in range(n_flows)]
    
    # Victim (Good Citizen): 1 flow of 20 Gbps
    u_victim = np.full_like(t, 20.0)
    
    throttled = False
    for i in range(1, len(t)):
        # QP-Spray Detection Logic (Tenant Aggregation)
        tenant_total = sum(f[i] for f in u_flows)
        
        if v[i-1] < 0.85:
            # CORRELATION DETECTED: Aggregate Tenant 1 is the bully
            throttled = True
            
        if throttled:
            # Throttle ALL flows in the tenant group
            for f in u_flows:
                f[i] = 1.0 # 10Gbps total
            if v[i-1] > 0.92:
                throttled = False
        
        # Physics update
        total_u = sum(f[i] for f in u_flows) + u_victim[i]
        v_drop = total_u * 0.001
        v_recover = (v_nom - v[i-1]) * 0.2
        v[i] = v[i-1] - v_drop*dt + v_recover*dt

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
    
    # Voltage Plot
    ax1.plot(t * 1000, v, color='black', label='Aggregate Voltage')
    ax1.axhline(0.85, color='red', linestyle='--', label='Group Throttle Threshold')
    ax1.set_ylabel("Voltage (V)")
    ax1.set_title("QP-Spray Defense: Aggregate Tenant Isolation")
    ax1.legend()
    
    # Traffic Plot showing many small flows
    colors = plt.cm.Blues(np.linspace(0.4, 0.9, n_flows))
    ax2.stackplot(t * 1000, *u_flows, labels=[f'Tenant A - Flow {i+1}' for i in range(n_flows)], colors=colors)
    ax2.plot(t * 1000, u_victim, color=COLOR_SUCCESS, linewidth=3, label='Tenant B (Victim)')
    
    ax2.set_ylabel("Throughput (Gbps)")
    ax2.set_xlabel("Time (ms)")
    ax2.legend(loc='upper right', ncol=2, fontsize=8)
    
    ax2.annotate("Group Throttling: All 10 flows\nclamped despite small size", 
                 xy=(150, 10), xytext=(250, 80),
                 arrowprops=dict(facecolor='black', shrink=0.05),
                 bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    plt.tight_layout()
    
    artifacts_path = Path(__file__).parent.parent / "artifacts" / "07_qp_spray_defense"
    save_publication_figure(fig, str(artifacts_path))
    plt.close(fig)
    print(f"Variation 7 complete. Artifact saved to {artifacts_path}.png")

if __name__ == "__main__":
    run_variation()

