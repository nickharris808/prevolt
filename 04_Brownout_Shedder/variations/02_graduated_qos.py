"""
Variation 2: Graduated QoS Degradation
======================================

Instead of a binary "On/Off" shed, this variation implements 8 levels 
of QoS degradation.

Mechanism:
The switch maps the "Power Deficit" to a priority depth. 
- Level 1 (90% Power): Shed Backup traffic.
- Level 4 (60% Power): Shed Checkpoint traffic.
- Level 8 (20% Power): Throttle Inference Batching.

Benefit: 
Provides a "Soft Landing" for AI services during grid instability. 
Prevents total cluster blackout by sacrificing low-value bits first.
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
import os
from pathlib import Path

def run_variation():
    t = np.linspace(0, 100, 100)
    
    # Power profile with gradual grid sag
    grid_capacity = np.full_like(t, 100.0)
    grid_capacity[20:80] = np.linspace(100.0, 30.0, 60)
    grid_capacity[80:] = 100.0
    
    # 8-Tier Traffic Profile
    # In a real system these would be 8 distinct DSCP classes
    tiers = [12.5] * 8 # 8 tiers of 12.5 units each
    actual_power = np.zeros_like(t)
    
    tier_usage = []
    for power in grid_capacity:
        usage = []
        remaining = power
        for tier in tiers:
            use = min(tier, remaining)
            usage.append(use)
            remaining -= use
        tier_usage.append(usage)
        
    tier_usage = np.array(tier_usage).T
    
    fig, ax = plt.subplots(figsize=(12, 7))
    colors = plt.cm.RdYlGn(np.linspace(0.1, 0.9, 8))
    ax.stackplot(t, tier_usage, labels=[f'Priority {i}' for i in range(1, 9)], colors=colors[::-1])
    
    ax.plot(t, grid_capacity, 'k--', linewidth=2, label='Grid Capacity')
    ax.set_title("Family 4: Graduated QoS Degradation (8-Level Soft Landing)")
    ax.set_ylabel("Power / Throughput (%)")
    ax.set_xlabel("Time (ms)")
    ax.legend(loc='lower left', ncol=2)
    
    artifacts_path = Path(__file__).parent.parent / "artifacts" / "02_graduated_qos"
    plt.savefig(str(artifacts_path) + ".png")
    plt.close(fig)
    print("Graduated QoS Variation Complete.")

if __name__ == "__main__":
    run_variation()
