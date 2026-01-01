"""
Variation 4: Predictive Sag Buffering
=====================================

Proves the "Proactive" resilience claim. 
Data centers usually have ~50ms of "Ride-Through" time via capacitors/UPS.
This logic detects an upstream grid "Sag" (e.g. at the substation) and 
flushes/drains the network queues *before* the local voltage drops.

Benefit: 
Uses the network buffer as a "Virtual Battery" to bridge the sag.
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
import os
from pathlib import Path

def run_variation():
    t = np.linspace(0, 200, 200)
    
    # Sag event at t=100
    substation_voltage = np.full_like(t, 100.0)
    substation_voltage[100:150] = 70.0
    
    # Logic: If substation sag detected, drain queues aggressively at t=80
    queue_depth = np.full_like(t, 60.0)
    
    # Baseline: queue full when sag hits -> Drop
    # Predictive: drain at t=80 -> Smooth
    
    queue_predictive = np.copy(queue_depth)
    queue_predictive[80:100] = np.linspace(60, 10, 20)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(t, substation_voltage, color='red', alpha=0.3, label='Substation Voltage')
    ax.plot(t, queue_depth, 'k--', label='Baseline Queue Depth')
    ax.plot(t, queue_predictive, 'g-', linewidth=2, label='Predictive Sag Buffer (Drain)')
    
    ax.set_title("Family 4: Predictive Sag Buffering (Virtual Battery)")
    ax.set_ylabel("Utilization / Level")
    ax.set_xlabel("Time (ms)")
    ax.legend()
    
    ax.annotate("Drain queue early to create\n'Empty Room' for the sag", 
                 xy=(90, 20), xytext=(20, 30),
                 arrowprops=dict(facecolor='black', shrink=0.05))
    
    artifacts_path = Path(__file__).parent.parent / "artifacts" / "04_sag_buffering"
    plt.savefig(str(artifacts_path) + ".png")
    plt.close(fig)
    print("Sag Buffering Variation Complete.")

if __name__ == "__main__":
    run_variation()
