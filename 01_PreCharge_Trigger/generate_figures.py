"""
Generate Patent Figures for Family 1
===================================
Generates high-resolution PNGs for the provisional patent application.
"""

import matplotlib.pyplot as plt
import numpy as np
from spice_vrm import SpiceVRMConfig, simulate_vrm_transient
import os

def generate_figure_3_transient():
    print("Generating Figure 3: Voltage Transient Response...")
    cfg = SpiceVRMConfig()
    
    # Run Baseline
    t_base, v_base, _ = simulate_vrm_transient(mode="baseline", cfg=cfg)
    
    # Run Invention
    t_inv, v_inv, _ = simulate_vrm_transient(mode="pretrigger", cfg=cfg)
    
    # Plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot Baseline
    ax.plot(t_base * 1e6, v_base, 'r--', linewidth=2, label='Baseline (No Trigger)')
    
    # Plot Invention
    ax.plot(t_inv * 1e6, v_inv, 'g-', linewidth=2, label='Invention (14µs Pre-Charge)')
    
    # Annotations
    ax.axhline(0.9, color='k', linestyle=':', alpha=0.5, label='Nominal (0.9V)')
    ax.axhline(0.7, color='r', linestyle=':', alpha=0.5, label='Crash Threshold (0.7V)')
    
    # Highlight the crash
    min_base = np.min(v_base)
    crash_time = t_base[np.argmin(v_base)] * 1e6
    ax.annotate(f'CRASH: {min_base:.3f}V', xy=(crash_time, min_base), 
                xytext=(crash_time+5, min_base-0.1),
                arrowprops=dict(facecolor='red', shrink=0.05))

    # Highlight the save - search for min ONLY after load start (t > 20us)
    load_start_idx = np.searchsorted(t_inv, 20e-6)
    v_inv_transient = v_inv[load_start_idx:]
    t_inv_transient = t_inv[load_start_idx:]
    
    min_inv = np.min(v_inv_transient)
    save_idx = np.argmin(v_inv_transient)
    save_time = t_inv_transient[save_idx] * 1e6
    
    ax.annotate(f'STABLE: {min_inv:.3f}V', xy=(save_time, min_inv), 
                xytext=(save_time+5, min_inv+0.05),
                arrowprops=dict(facecolor='green', shrink=0.05))

    ax.set_title('Figure 3: Voltage Transient Response (500A Load Step)')
    ax.set_xlabel('Time (µs)')
    ax.set_ylabel('GPU Voltage (V)')
    ax.set_ylim(bottom=0.5)
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper right')
    
    # Save
    os.makedirs('patents/figures', exist_ok=True)
    plt.savefig('patents/figures/FIG_3_VOLTAGE_TRANSIENT.png', dpi=300)
    plt.close()
    print("✅ Saved FIG_3_VOLTAGE_TRANSIENT.png")

def generate_figure_2_timing():
    print("Generating Figure 2: Timing Diagram...")
    # Abstract timing diagram
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(10, 8), sharex=True)
    
    t = np.linspace(0, 40, 1000)
    
    # Packet Detect (Pulse at t=5)
    packet = np.zeros_like(t)
    packet[125:150] = 1 # Pulse width
    ax1.plot(t, packet, 'b-')
    ax1.set_ylabel('Packet\nDetect')
    ax1.set_yticks([0, 1])
    ax1.set_yticklabels(['0', '1'])
    
    # Pre-Charge Trigger (Latched at t=5)
    trigger = np.zeros_like(t)
    trigger[125:800] = 1 # Held until release
    ax2.plot(t, trigger, 'g-')
    ax2.set_ylabel('Pre-Charge\nTrigger')
    ax2.set_yticks([0, 1])
    
    # VRM Voltage (Ramp starts at t=5)
    voltage = np.ones_like(t) * 0.9
    # Simple exponential ramp model
    mask = t > 5
    voltage[mask] = 0.9 + 0.3 * (1 - np.exp(-(t[mask]-5)/5))
    ax3.plot(t, voltage, 'k-')
    ax3.set_ylabel('VRM\nVoltage (V)')
    
    # Packet Release (At t=19 -> 14us delay)
    release = np.zeros_like(t)
    release[475:500] = 1
    ax4.plot(t, release, 'r-')
    ax4.set_ylabel('Packet\nRelease')
    ax4.set_xlabel('Time (µs)')
    ax4.set_yticks([0, 1])
    
    # Annotations
    ax2.annotate('14µs Lead Time', xy=(5, 0.5), xytext=(12, 0.5),
                 arrowprops=dict(arrowstyle='<->'))
    
    plt.suptitle('Figure 2: System Timing Diagram')
    
    plt.savefig('patents/figures/FIG_2_TIMING_DIAGRAM.png', dpi=300)
    plt.close()
    print("✅ Saved FIG_2_TIMING_DIAGRAM.png")

if __name__ == "__main__":
    generate_figure_3_transient()
    generate_figure_2_timing()
