"""
Physics Constants for Power Delivery Simulations
=================================================

These constants represent realistic values for modern GPU power delivery systems,
based on publicly available specifications for high-performance computing hardware.

References:
- Nvidia Blackwell Architecture Whitepaper (2024)
- Intel VR13/VR14 VRM Specifications
- Open Compute Project Power Delivery Guidelines
"""

# =============================================================================
# VRM (Voltage Regulator Module) Parameters
# =============================================================================

# VRM Output Voltage Setpoint
# Modern GPUs operate at ~0.9V core voltage for high-performance operation
VRM_VOLTAGE_NOMINAL_V = 0.9  # Volts - Nominal GPU core voltage

# VRM Voltage Tolerance
# The acceptable voltage range before the GPU crashes or throttles
VRM_VOLTAGE_MIN_V = 0.75    # Volts - Below this = GPU crash (undervoltage lockout)
VRM_VOLTAGE_MAX_V = 1.05    # Volts - Above this = damage risk
VRM_VOLTAGE_WARNING_V = 0.80  # Volts - Below this = danger zone (throttle needed)

# VRM Output Stage Impedance
# Models the internal resistance and inductance of the power stage
VRM_R_SOURCE_OHMS = 0.001   # 1 milliohm - Output resistance (very low for high current)
VRM_L_SOURCE_H = 100e-9     # 100 nanohenries - Output inductance (parasitic + intentional)

# VRM Output Capacitance
# Bulk and high-frequency decoupling capacitors
VRM_C_OUTPUT_F = 1000e-6    # 1000 microfarads - Total output capacitance

# VRM Response Time
# The time for the VRM control loop to respond to a load step
# This is the fundamental problem: VRM is too slow for GPU transients
VRM_RESPONSE_TIME_S = 15e-6  # 15 microseconds - Typical multi-phase buck response

# VRM Pre-charge Lead Time Options (for tournament)
VRM_PRECHARGE_NONE_S = 0.0       # No pre-charge (baseline failure)
VRM_PRECHARGE_STATIC_S = 50e-9  # 50 nanoseconds static delay
VRM_PRECHARGE_MIN_S = 10e-9     # 10 nanoseconds minimum (for predictive)
VRM_PRECHARGE_MAX_S = 100e-9    # 100 nanoseconds maximum (for predictive)


# =============================================================================
# GPU Load Parameters
# =============================================================================

# GPU Maximum Current Draw
# Modern HPC GPUs can draw 500+ Amps during peak compute bursts
GPU_CURRENT_IDLE_A = 50.0    # Amps - Idle current (clocks gated, memory refresh)
GPU_CURRENT_PEAK_A = 500.0   # Amps - Peak current during tensor core burst

# GPU Load Step Time
# The time for the GPU to ramp from idle to peak current
# This is much faster than the VRM can respond - the core problem
GPU_LOAD_STEP_TIME_S = 1e-6  # 1 microsecond - Worst-case transient

# GPU di/dt (Current Slew Rate)
# The rate of change of current that causes voltage droop
GPU_DIDT_A_PER_S = (GPU_CURRENT_PEAK_A - GPU_CURRENT_IDLE_A) / GPU_LOAD_STEP_TIME_S


# =============================================================================
# Network and Telemetry Parameters
# =============================================================================

# Network Link Speed
NETWORK_LINK_SPEED_GBPS = 100.0  # Gbps - Typical data center link
NETWORK_LINK_SPEED_BPS = NETWORK_LINK_SPEED_GBPS * 1e9

# Packet Sizes
NETWORK_MTU_BYTES = 1500      # Standard Ethernet MTU
NETWORK_JUMBO_MTU_BYTES = 9000  # Jumbo frames for HPC

# Telemetry TCP Option Code (custom extension)
TELEMETRY_TCP_OPTION_CODE = 0x1A  # Reserved experimental option

# Token Bucket Parameters for Throttling
TOKEN_BUCKET_RATE_FULL_GBPS = 100.0   # Full rate when voltage is healthy
TOKEN_BUCKET_RATE_THROTTLE_GBPS = 25.0  # Reduced rate during voltage dip


# =============================================================================
# Spectral/Frequency Parameters
# =============================================================================

# Inference Batch Frequency
# AI inference batches typically arrive at ~100Hz (10ms intervals)
INFERENCE_BATCH_FREQ_HZ = 100.0
INFERENCE_BATCH_INTERVAL_S = 1.0 / INFERENCE_BATCH_FREQ_HZ  # 10ms

# Dangerous Resonance Frequencies
# These frequencies can excite mechanical resonance in facility transformers
RESONANCE_DANGER_FREQ_HZ = 100.0   # Primary danger frequency
RESONANCE_DANGER_BANDWIDTH_HZ = 20.0  # ±10Hz around center

# Jitter Parameters for Spectral Damping
JITTER_RANGE_FRACTION = 0.2  # ±20% jitter to break resonance
JITTER_MIN_INTERVAL_S = 0.001  # 1ms minimum interval (floor)


# =============================================================================
# Brownout/QoS Parameters
# =============================================================================

# Traffic Class Priorities
QOS_PRIORITY_GOLD = 7      # Highest priority (inference traffic)
QOS_PRIORITY_SILVER = 4    # Medium priority
QOS_PRIORITY_BRONZE = 1    # Lowest priority (checkpoint/backup)

# Traffic Class Power Weights
# How much power each class consumes as fraction of total
QOS_GOLD_POWER_FRACTION = 0.6     # 60% of power is inference
QOS_BRONZE_POWER_FRACTION = 0.4   # 40% of power is checkpoint

# Brownout Thresholds
BROWNOUT_VOLTAGE_THRESHOLD = 0.95  # Grid voltage fraction to trigger brownout
BROWNOUT_SHED_TARGET = 0.4         # Target 40% power reduction


# =============================================================================
# Simulation Parameters
# =============================================================================

# Time Resolution
SIM_TIME_STEP_S = 1e-9      # 1 nanosecond resolution for circuit simulation
SIM_DURATION_SHORT_S = 100e-6  # 100 microseconds for voltage transients
SIM_DURATION_LONG_S = 1.0      # 1 second for network/brownout simulations

# Number of Simulation Points
SIM_POINTS_PER_TRACE = 10000   # Points per voltage trace for smooth plotting

# Random Seed for Reproducibility
SIM_RANDOM_SEED = 42


# =============================================================================
# Derived Constants (Calculated from Above)
# =============================================================================

# Expected Voltage Droop (V = L * di/dt)
# This is the voltage drop due to inductance during load step
EXPECTED_VOLTAGE_DROOP_V = VRM_L_SOURCE_H * GPU_DIDT_A_PER_S

# Time Constant of Output Stage (tau = L/R)
VRM_TIME_CONSTANT_S = VRM_L_SOURCE_H / VRM_R_SOURCE_OHMS

# Resonant Frequency of Output LC Filter
# f = 1 / (2 * pi * sqrt(L * C))
import math
VRM_RESONANT_FREQ_HZ = 1.0 / (2 * math.pi * math.sqrt(VRM_L_SOURCE_H * VRM_C_OUTPUT_F))


if __name__ == "__main__":
    # Print summary of key constants for verification
    print("=" * 60)
    print("Portfolio A: Power Delivery Simulation Constants")
    print("=" * 60)
    print(f"\nVRM Parameters:")
    print(f"  Nominal Voltage:     {VRM_VOLTAGE_NOMINAL_V:.2f} V")
    print(f"  Warning Threshold:   {VRM_VOLTAGE_WARNING_V:.2f} V")
    print(f"  Minimum Voltage:     {VRM_VOLTAGE_MIN_V:.2f} V")
    print(f"  Response Time:       {VRM_RESPONSE_TIME_S * 1e6:.1f} µs")
    print(f"  Output Capacitance:  {VRM_C_OUTPUT_F * 1e6:.0f} µF")
    
    print(f"\nGPU Parameters:")
    print(f"  Peak Current:        {GPU_CURRENT_PEAK_A:.0f} A")
    print(f"  Load Step Time:      {GPU_LOAD_STEP_TIME_S * 1e6:.1f} µs")
    print(f"  di/dt:               {GPU_DIDT_A_PER_S / 1e9:.1f} GA/s")
    
    print(f"\nDerived Values:")
    print(f"  Expected V Droop:    {EXPECTED_VOLTAGE_DROOP_V * 1e3:.1f} mV")
    print(f"  LC Resonant Freq:    {VRM_RESONANT_FREQ_HZ:.1f} Hz")
    print("=" * 60)




