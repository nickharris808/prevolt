"""
Variation 2: PID Rate Controller
================================

This variation moves beyond simple "step" thresholds. 
The switch implements a Proportional-Integral-Derivative (PID) controller 
to calculate the egress rate limit.

Key Benefit: 
Prevents "Bang-Bang" oscillations. Simple thresholds cause the switch to 
slam the brakes, then slam the gas, causing network jitter. PID provides 
a smooth, asymptotic recovery to nominal voltage.

Acceptance Criteria:
- Show zero oscillations during recovery.
- Demonstrate 30% higher average throughput than Step-Thresholds.
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

from utils.plotting import setup_plot_style, save_publication_figure, COLOR_FAILURE, COLOR_SUCCESS

class PIDController:
    def __init__(self, kp=200, ki=10, kd=5, target=0.9):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.target = target
        self.integral = 0
        self.prev_error = 0
        
    def compute(self, current_v, dt):
        error = current_v - self.target
        self.integral += error * dt
        derivative = (error - self.prev_error) / dt
        self.prev_error = error
        return self.kp * error + self.ki * self.integral + self.kd * derivative

def run_variation():
    setup_plot_style()
    
    t = np.linspace(0, 0.5, 500)
    dt = 0.001
    v_nom = 0.95
    v = np.zeros_like(t)
    u = np.zeros_like(t)
    v[0] = v_nom
    
    pid = PIDController(kp=500, ki=50, kd=5, target=0.90)
    
    for i in range(1, len(t)):
        # Compute control signal
        control = pid.compute(v[i-1], dt)
        u[i] = np.clip(100 + control, 10, 150)
        
        # Physics update
        v_drop = u[i] * 0.0015
        v_recover = (v_nom - v[i-1]) * 0.2
        v[i] = v[i-1] - v_drop*dt + v_recover*dt
        
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    
    ax1.plot(t * 1000, v, color=COLOR_SUCCESS, label='GPU Voltage (PID Controlled)')
    ax1.axhline(0.90, color='black', linestyle='--', label='Setpoint')
    ax1.set_ylabel("Voltage (V)")
    ax1.legend()
    
    ax2.plot(t * 1000, u, color='purple', label='Switch Rate Limit (PID)')
    ax2.set_ylabel("Throughput (Gbps)")
    ax2.set_xlabel("Time (ms)")
    ax2.legend()
    
    plt.suptitle("Variation 2: PID Rate Control for Smooth Recovery")
    
    artifacts_path = Path(__file__).parent.parent / "artifacts" / "02_pid_control"
    save_publication_figure(fig, str(artifacts_path))
    plt.close(fig)
    print(f"Variation 2 complete. Artifact saved to {artifacts_path}.png")

if __name__ == "__main__":
    run_variation()

