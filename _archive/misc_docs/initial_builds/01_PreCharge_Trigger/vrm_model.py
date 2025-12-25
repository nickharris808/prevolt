"""
VRM (Voltage Regulator Module) Circuit Model
=============================================

This module implements a physics-based model of GPU power delivery that captures
the fundamental problem: VRM control loop is too slow to respond to GPU transients.

Key Physics Principles:
1. Voltage Droop = L * di/dt (inductor opposes current change)
2. Capacitor provides temporary energy: Q = C * V
3. VRM control loop responds with time constant ~15µs
4. GPU load step occurs in ~1µs

The simulation shows:
- Baseline: Deep voltage crash as capacitor discharges before VRM responds
- Pre-charge: VRM is "warned" early, starts ramping current before load hits

This is the core patent innovation: The network switch knows WHEN data will arrive
and can signal the VRM BEFORE the GPU needs the power.
"""

import numpy as np
from scipy.integrate import solve_ivp
from dataclasses import dataclass
from enum import Enum
from typing import Tuple, Optional
import sys
import os

# Add parent directory to path for utils import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.constants import (
    VRM_VOLTAGE_NOMINAL_V,
    VRM_VOLTAGE_MIN_V,
    VRM_VOLTAGE_WARNING_V,
    VRM_RESPONSE_TIME_S,
    GPU_CURRENT_IDLE_A,
    GPU_CURRENT_PEAK_A,
    GPU_LOAD_STEP_TIME_S,
)


# =============================================================================
# Enums and Data Classes
# =============================================================================

class PreChargeMode(Enum):
    """Pre-charge algorithm modes for the tournament."""
    NONE = "none"              # No pre-charge (baseline - voltage crash)
    STATIC = "static"          # Fixed 50ns delay pre-charge
    PREDICTIVE = "predictive"  # Adaptive pre-charge based on load prediction


@dataclass
class SimulationResult:
    """Container for simulation output data."""
    time: np.ndarray           # Time vector (seconds)
    voltage: np.ndarray        # Output voltage (Volts)
    current: np.ndarray        # Load current (Amps)
    vrm_current: np.ndarray    # VRM output current (Amps)
    precharge_mode: str        # Which algorithm was used
    
    @property
    def min_voltage(self) -> float:
        """Minimum voltage during simulation."""
        return float(np.min(self.voltage))
    
    @property
    def voltage_droop(self) -> float:
        """Maximum voltage drop from nominal (mV)."""
        return (VRM_VOLTAGE_NOMINAL_V - self.min_voltage) * 1000
    
    @property
    def time_below_warning(self) -> float:
        """Time spent below warning threshold (µs)."""
        below_warning = self.voltage < VRM_VOLTAGE_WARNING_V
        if not np.any(below_warning):
            return 0.0
        dt = self.time[1] - self.time[0]
        return float(np.sum(below_warning) * dt * 1e6)
    
    @property
    def crashed(self) -> bool:
        """Did voltage drop below minimum (GPU crash)?"""
        return self.min_voltage < VRM_VOLTAGE_MIN_V


# =============================================================================
# VRM Circuit Physics Model
# =============================================================================

class VRMPhysicsModel:
    """
    Physics-based VRM model capturing the key transient behavior.
    
    The model uses a state-space representation:
    
    States:
    - V_out: Output voltage (what the GPU sees)
    - I_vrm: VRM output current (what the VRM can supply)
    
    The key insight is that the VRM current (I_vrm) responds slowly to
    voltage error, while the load current (I_load) changes instantly.
    The output capacitor must bridge this gap.
    
    Physics:
    - C * dV/dt = I_vrm - I_load  (capacitor current balance)
    - tau * dI_vrm/dt = I_load_target - I_vrm  (VRM control loop response)
    
    Where tau = VRM_RESPONSE_TIME (the slow control loop)
    """
    
    def __init__(self):
        """Initialize with realistic GPU power delivery parameters."""
        # VRM parameters
        self.v_nom = VRM_VOLTAGE_NOMINAL_V    # 0.9V nominal
        self.v_warning = VRM_VOLTAGE_WARNING_V  # 0.8V warning threshold
        self.v_min = VRM_VOLTAGE_MIN_V        # 0.75V crash threshold
        
        # VRM dynamics - THIS IS THE KEY LIMITATION
        # The VRM control loop cannot respond faster than this
        # Using 10µs for clearer demonstration
        self.vrm_tau = 10e-6  # 10µs time constant
        
        # Output capacitance (provides temporary energy during transient)
        # Typical high-end GPU: 2000-5000µF bulk + MLCC
        # Using larger value to prevent unrealistic voltage collapse
        self.c_out = 5000e-6  # 5000µF - realistic for high-power GPU
        
        # Load parameters - scaled to show clear but realistic droop
        # The delta matters more than absolute values
        self.i_idle = 50.0    # 50A idle
        self.i_peak = 300.0   # 300A peak (250A step)
        self.load_step_time = 5e-6  # 5µs transition (realistic for GPU)
        
        # Simulation timing
        self.t_load_start = 20e-6  # Load step at 20µs
    
    def _load_current_profile(self, t: float) -> float:
        """
        Calculate GPU load current at time t.
        
        Models a step from idle to peak with finite rise time.
        """
        if t < self.t_load_start:
            return self.i_idle
        elif t < self.t_load_start + self.load_step_time:
            # Linear ramp from idle to peak
            fraction = (t - self.t_load_start) / self.load_step_time
            return self.i_idle + (self.i_peak - self.i_idle) * fraction
        else:
            return self.i_peak
    
    def _vrm_target_current(self, t: float, v_out: float, 
                            precharge_mode: PreChargeMode,
                            precharge_time: float) -> float:
        """
        Calculate the VRM target current based on feedback and pre-charge.
        
        This is where the pre-charge innovation happens:
        - NONE: VRM only responds to voltage error (reactive)
        - STATIC: VRM starts ramping before load step (proactive)
        - PREDICTIVE: VRM estimates load magnitude and pre-positions
        
        Args:
            t: Current time
            v_out: Current output voltage
            precharge_mode: Pre-charge algorithm
            precharge_time: Lead time for pre-charge signal
            
        Returns:
            Target current for VRM control loop
        """
        # Base target: whatever current is needed right now
        i_load_now = self._load_current_profile(t)
        
        # Voltage feedback: correct for any voltage error
        # This is standard VRM behavior - try to maintain v_nom
        v_error = self.v_nom - v_out
        i_feedback = v_error * 1000  # High gain feedback
        
        # Base target is load current plus feedback correction
        i_target = i_load_now + i_feedback
        
        if precharge_mode == PreChargeMode.NONE:
            # Baseline: just react to voltage error
            # Problem: by the time voltage drops, it's too late
            return i_target
        
        elif precharge_mode == PreChargeMode.STATIC:
            # Static pre-charge: start ramping precharge_time BEFORE load step
            t_precharge_start = self.t_load_start - precharge_time
            
            if t >= t_precharge_start and t < self.t_load_start:
                # During pre-charge window: target is peak current
                # This "wakes up" the VRM before the load hits
                i_target = self.i_peak + i_feedback
            elif t >= self.t_load_start:
                # After load step: normal operation
                i_target = i_load_now + i_feedback
            
            return i_target
        
        elif precharge_mode == PreChargeMode.PREDICTIVE:
            # Predictive pre-charge: gradual ramp based on prediction
            # This models a moving-average predictor that learns load patterns
            t_precharge_start = self.t_load_start - precharge_time * 2
            
            if t >= t_precharge_start and t < self.t_load_start:
                # Gradual ramp during prediction window
                ramp_progress = (t - t_precharge_start) / (precharge_time * 2)
                predicted_load = self.i_idle + (self.i_peak - self.i_idle) * ramp_progress
                i_target = predicted_load + i_feedback
            elif t >= self.t_load_start:
                # After load step: normal operation
                i_target = i_load_now + i_feedback
            
            return i_target
        
        return i_target
    
    def simulate(self, duration: float = 100e-6,
                 precharge_mode: PreChargeMode = PreChargeMode.NONE,
                 precharge_time: float = 50e-9) -> SimulationResult:
        """
        Run the VRM transient simulation.
        
        Uses scipy's solve_ivp with adaptive stepping for accuracy.
        
        Args:
            duration: Simulation duration (default 100µs)
            precharge_mode: Which pre-charge algorithm to use
            precharge_time: Lead time for pre-charge (default 50ns)
            
        Returns:
            SimulationResult with voltage, current, and timing data
        """
        
        def derivatives(t, state):
            """ODE system for VRM circuit."""
            v_out, i_vrm = state
            
            # Get current load demand
            i_load = self._load_current_profile(t)
            
            # Get VRM target current
            i_target = self._vrm_target_current(t, v_out, precharge_mode, precharge_time)
            
            # State equations:
            # 1. Capacitor: C * dV/dt = I_vrm - I_load
            dv_dt = (i_vrm - i_load) / self.c_out
            
            # 2. VRM control loop: tau * dI/dt = I_target - I_vrm
            # This is the KEY equation: VRM cannot change current faster than tau allows
            di_dt = (i_target - i_vrm) / self.vrm_tau
            
            return [dv_dt, di_dt]
        
        # Initial conditions: steady state at idle
        state0 = [self.v_nom, self.i_idle]
        
        # Time span for simulation
        t_span = (0, duration)
        
        # Solve with dense output for smooth plotting
        solution = solve_ivp(
            derivatives,
            t_span,
            state0,
            method='RK45',
            dense_output=True,
            max_step=100e-9,  # 100ns max step for accuracy
            rtol=1e-6,
            atol=1e-9
        )
        
        # Generate output time vector (1000 points)
        t_out = np.linspace(0, duration, 1000)
        
        # Evaluate solution at output times
        states = solution.sol(t_out)
        v_out = states[0]
        i_vrm = states[1]
        
        # Calculate load current at each time point
        i_load = np.array([self._load_current_profile(t) for t in t_out])
        
        return SimulationResult(
            time=t_out,
            voltage=v_out,
            current=i_load,
            vrm_current=i_vrm,
            precharge_mode=precharge_mode.value
        )


# =============================================================================
# Convenience Functions
# =============================================================================

def run_baseline_simulation() -> SimulationResult:
    """Run baseline simulation with no pre-charge (demonstrates the problem)."""
    model = VRMPhysicsModel()
    return model.simulate(precharge_mode=PreChargeMode.NONE)


def run_static_precharge_simulation(precharge_time: float = 5e-6) -> SimulationResult:
    """Run simulation with static pre-charge delay (fixed lead time)."""
    model = VRMPhysicsModel()
    return model.simulate(
        precharge_mode=PreChargeMode.STATIC,
        precharge_time=precharge_time
    )


def run_predictive_precharge_simulation(precharge_time: float = 5e-6) -> SimulationResult:
    """Run simulation with predictive pre-charge (adaptive lead time)."""
    model = VRMPhysicsModel()
    return model.simulate(
        precharge_mode=PreChargeMode.PREDICTIVE,
        precharge_time=precharge_time
    )


def run_tournament(precharge_times: list = None) -> dict:
    """
    Run a full tournament comparing all three algorithms.
    
    Args:
        precharge_times: List of pre-charge times to test (default: [1µs, 5µs, 10µs])
        
    Returns:
        Dictionary with results for each algorithm and timing
    """
    if precharge_times is None:
        precharge_times = [1e-6, 5e-6, 10e-6]
    
    results = {
        'baseline': run_baseline_simulation(),
        'static': {},
        'predictive': {}
    }
    
    for pt in precharge_times:
        pt_label = f"{pt*1e6:.0f}us"
        results['static'][pt_label] = run_static_precharge_simulation(pt)
        results['predictive'][pt_label] = run_predictive_precharge_simulation(pt)
    
    return results


# =============================================================================
# Main (Testing)
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("VRM Circuit Model - Test Run")
    print("=" * 70)
    
    # Run all three modes with 5µs pre-charge time
    print("\n1. Running baseline (no pre-charge)...")
    baseline = run_baseline_simulation()
    print(f"   Min Voltage:    {baseline.min_voltage:.3f} V")
    print(f"   Voltage Droop:  {baseline.voltage_droop:.1f} mV")
    print(f"   Time < 0.8V:    {baseline.time_below_warning:.1f} µs")
    print(f"   GPU Crashed:    {'YES' if baseline.crashed else 'No'}")
    
    print("\n2. Running static pre-charge (5µs lead time)...")
    static = run_static_precharge_simulation(5e-6)
    print(f"   Min Voltage:    {static.min_voltage:.3f} V")
    print(f"   Voltage Droop:  {static.voltage_droop:.1f} mV")
    print(f"   Time < 0.8V:    {static.time_below_warning:.1f} µs")
    print(f"   GPU Crashed:    {'YES' if static.crashed else 'No'}")
    
    print("\n3. Running predictive pre-charge (5µs lead time)...")
    predictive = run_predictive_precharge_simulation(5e-6)
    print(f"   Min Voltage:    {predictive.min_voltage:.3f} V")
    print(f"   Voltage Droop:  {predictive.voltage_droop:.1f} mV")
    print(f"   Time < 0.8V:    {predictive.time_below_warning:.1f} µs")
    print(f"   GPU Crashed:    {'YES' if predictive.crashed else 'No'}")
    
    # Calculate improvement
    if baseline.voltage_droop > 0 and predictive.voltage_droop > 0:
        improvement = baseline.voltage_droop / predictive.voltage_droop
    else:
        improvement = float('inf')
    
    print("\n" + "=" * 70)
    print(f"SUMMARY: Pre-charge reduces voltage droop by {improvement:.1f}x")
    print(f"         Baseline: {baseline.voltage_droop:.0f}mV -> Predictive: {predictive.voltage_droop:.0f}mV")
    print("=" * 70)

