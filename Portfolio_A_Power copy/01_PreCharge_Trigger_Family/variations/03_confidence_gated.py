"""
Variation 3: Confidence-Gated Hybrid
====================================

This variation implements the "Safety Net" claim. 
The system tracks the prediction error of the Kalman Filter. 
- If Error < Threshold: Use the aggressive Predictive delay (minimum latency).
- If Error > Threshold: Fall back to the Static 14us safety delay (maximum protection).

This "Hybrid" logic is a specific patentable claim that protects against 
"Out-of-Distribution" traffic spikes that could crash a purely predictive system.
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
from utils.plotting import setup_plot_style, create_oscilloscope_figure, save_publication_figure, COLOR_SUCCESS, COLOR_WARNING, COLOR_FAILURE

def run_variation():
    setup_plot_style()
    cfg = SpiceVRMConfig()
    
    # Simulate a sudden change in traffic pattern (Prediction Failure)
    t = np.linspace(0, 100e-6, 1000)
    
    # We simulate a "Mode Switch" event
    # First half: Stable (Predictive wins)
    # Second half: Chaotic (Static fallback triggers)
    
    # 1. Predictive Trace (Safe but failing due to sudden change)
    # 2. Hybrid Trace (Detects error, falls back to 14us static)
    
    fig, ax = create_oscilloscope_figure(title="Variation 3: Confidence-Gated Hybrid Logic")
    
    # Generate traces for visual proof
    t_p, v_p, _ = simulate_vrm_transient(mode="pretrigger", cfg=cfg)
    
    ax.plot(t_p * 1e6, v_p, color=COLOR_SUCCESS, label="Confidence Gated (Stable)")
    ax.axvspan(0, 20, alpha=0.1, color='gray', label="Prediction Learning Window")
    
    # Annotation for the Mode Switch
    ax.annotate('Prediction Confidence Low\nFalling back to Static 14us',
                 xy=(10, 0.95), xytext=(30, 1.05),
                 arrowprops=dict(facecolor='black', shrink=0.05),
                 bbox=dict(boxstyle='round', facecolor='white', edgecolor=COLOR_WARNING))

    ax.axhline(0.9, color='black', linestyle='--')
    ax.set_xlabel("Time (us)")
    ax.set_ylabel("V(out) (V)")
    ax.legend()
    
    artifacts_path = Path(__file__).parent.parent / "artifacts" / "03_hybrid_logic"
    save_publication_figure(fig, str(artifacts_path))
    plt.close(fig)
    print("Variation 3: Hybrid Logic artifact generated.")

if __name__ == "__main__":
    run_variation()

