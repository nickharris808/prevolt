"""
Variation 3: Phase-Cancellation Interleaving
============================================

This is a "Zero Jitter" solution. 
The switch detects two different 100Hz traffic flows (Flow A and Flow B). 
Instead of jittering them, it perfectly interleaves them with a 5ms 
(180 degree) phase shift.

Result: 
Flow A's peak aligns with Flow B's trough. The 100Hz harmonic cancels 
out at the aggregate power consumption level (PDU/Transformer).

Deliverable:
Time-domain and FFT plot showing "Harmonic Cancellation."
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
import os
from pathlib import Path
from scipy.fft import rfft, rfftfreq

# Add root and family paths to sys.path
root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root))
family = Path(__file__).parent.parent
sys.path.insert(0, str(family))

from utils.plotting import setup_plot_style, save_publication_figure, COLOR_FAILURE, COLOR_SUCCESS

def run_variation():
    duration = 2.0
    fs = 1000.0
    t = np.linspace(0, duration, int(fs*duration))
    
    # Two flows at 100Hz
    flow_a = np.sin(2 * np.pi * 100 * t)
    
    # 180 degree shift (5ms for 100Hz)
    flow_b_shifted = np.sin(2 * np.pi * 100 * t + np.pi) 
    
    # Flow B unshifted (Periodic Baseline)
    flow_b_base = np.sin(2 * np.pi * 100 * t)
    
    # Aggregate
    aggregate_base = flow_a + flow_b_base
    aggregate_cancelled = flow_a + flow_b_shifted
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Time Domain
    ax1.plot(t[:100], flow_a[:100], 'b--', alpha=0.5, label='Flow A')
    ax1.plot(t[:100], flow_b_shifted[:100], 'r--', alpha=0.5, label='Flow B (Shifted)')
    ax1.plot(t[:100], aggregate_cancelled[:100], 'g-', linewidth=2, label='Aggregate (Cancelled)')
    ax1.set_title("Time Domain: Phase Interleaving")
    ax1.legend()
    
    # Frequency Domain
    xf = rfftfreq(len(t), 1/fs)
    yf_base = 20 * np.log10(np.abs(rfft(aggregate_base)) + 1e-6)
    yf_cancel = 20 * np.log10(np.abs(rfft(aggregate_cancelled)) + 1e-6)
    
    ax2.plot(xf, yf_base, 'r--', label='Un-aligned (Peak)')
    ax2.plot(xf, yf_cancel, 'g-', label='Phase Cancelled (Clean)')
    ax2.set_xlim(0, 200)
    ax2.set_title("Frequency Domain: 100Hz Cancellation")
    ax2.set_ylabel("dB")
    ax2.legend()
    
    artifacts_path = Path(__file__).parent.parent / "artifacts" / "03_phase_cancellation"
    plt.savefig(str(artifacts_path) + ".png")
    plt.close(fig)
    print("Phase Cancellation Variation Complete.")

if __name__ == "__main__":
    run_variation()

