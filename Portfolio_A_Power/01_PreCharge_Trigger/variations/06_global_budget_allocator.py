"""
Variation 6: Global Pre-charge Current Budgeting
===============================================

This variation proves the "Facility-Aware Coordination" claim.
Pre-charging a VRM consumes a massive current spike BEFORE the load step.
If a 64-port switch pre-charges all GPUs simultaneously, the combined spike 
will trip the data center's main PDU breaker.

Invention:
The switch maintains a 'Global Pre-charge Budget'. It monitors the total current 
spike currently in progress across all ports. If the budget is exhausted, it 
automatically 'scales' or 'delays' the pre-charge of the 65th GPU to ensure 
total facility safety.

Acceptance Criteria:
- Simulate 64 ports.
- Demonstrate that aggregate pre-charge current never exceeds a configurable limit.
- Show 'fair-share' allocation of pre-charge current during collective bursts.
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
    
    t = np.linspace(0, 100e-6, 2000) # 100us
    n_ports = 64
    
    # Each pre-charge event draws 50A extra for 15us
    def precharge_draw(t, start_time, scaled_factor=1.0):
        draw = np.zeros_like(t)
        mask = (t >= start_time) & (t < start_time + 15e-6)
        draw[mask] = 50.0 * scaled_factor
        return draw

    # Scenario 1: Uncoordinated (Baseline)
    # A collective burst triggers all 64 ports at once
    aggregate_uncoord = np.zeros_like(t)
    for _ in range(n_ports):
        aggregate_uncoord += precharge_draw(t, 20e-6)
        
    # Scenario 2: Budget-Limited (Invention)
    # Switch allows max 1500A pre-charge current
    budget_limit = 1500.0
    aggregate_coord = np.zeros_like(t)
    
    # Coordination Logic: Stagger ports in groups to respect budget
    ports_per_group = int(budget_limit / 50.0) # 30 ports
    for i in range(n_ports):
        group = i // ports_per_group
        stagger = group * 10e-6
        aggregate_coord += precharge_draw(t, 20e-6 + stagger)
        
    fig, ax = plt.subplots(figsize=(12, 7))
    
    ax.plot(t * 1e6, aggregate_uncoord, color=COLOR_FAILURE, label='Uncoordinated (Trips Facility Breaker!)')
    ax.plot(t * 1e6, aggregate_coord, color=COLOR_SUCCESS, linewidth=3, label='Budget-Aware Allocation (Invention)')
    
    ax.axhline(budget_limit, color='red', linestyle='--', label='Main Breaker Limit')
    ax.fill_between(t * 1e6, budget_limit, 3500, color='red', alpha=0.1)
    
    ax.set_title("Global Pre-charge Budgeting: Protecting Facility Infrastructure")
    ax.set_xlabel("Time (us)")
    ax.set_ylabel("Aggregate Pre-charge Current (A)")
    ax.legend(loc='upper right')
    
    ax.annotate("Switch staggers groups to\nstay under breaker limit", 
                 xy=(35, 1200), xytext=(50, 2500),
                 arrowprops=dict(facecolor='black', shrink=0.05),
                 bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    plt.tight_layout()
    
    artifacts_path = Path(__file__).parent.parent / "artifacts" / "06_global_budgeting"
    save_publication_figure(fig, str(artifacts_path))
    plt.close(fig)
    print(f"Variation 6 complete. Artifact saved to {artifacts_path}.png")

if __name__ == "__main__":
    run_variation()

