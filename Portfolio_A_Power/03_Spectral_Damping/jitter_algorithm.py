"""
Spectral Jitter Algorithm for Traffic Damping
==============================================

This module implements the "Spectral Traffic Shaping" invention that prevents
dangerous resonance in data center power infrastructure.

The Problem:
- AI inference batches arrive at regular intervals (~100Hz = 10ms)
- This creates a 100Hz harmonic in the power draw
- Facility transformers have mechanical resonance at low frequencies
- The 100Hz spike can cause transformer vibration, breaker trips, and power failures

The Solution:
- Introduce controlled "jitter" (randomization) in packet scheduling
- This spreads the energy across the frequency spectrum
- The resonant peak disappears into the noise floor

Key Insight:
Even small jitter (±20% of interval) eliminates dangerous resonance while
having negligible impact on overall throughput and latency.

References:
- IEEE Power Delivery: Transformer Resonance in Data Centers
- ASHRAE: Electrical Harmonics from IT Equipment
"""

import numpy as np
from dataclasses import dataclass
from enum import Enum
from typing import Tuple, List
import sys
import os

# Add parent to path for utils import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.constants import (
    INFERENCE_BATCH_FREQ_HZ,
    INFERENCE_BATCH_INTERVAL_S,
    JITTER_RANGE_FRACTION,
    JITTER_MIN_INTERVAL_S,
    SIM_RANDOM_SEED,
)


# =============================================================================
# Jitter Algorithm Modes
# =============================================================================

class JitterMode(Enum):
    """Jitter algorithm modes for spectral damping."""
    NONE = "none"           # No jitter (baseline - dangerous resonance)
    UNIFORM = "uniform"     # Uniform random jitter
    GAUSSIAN = "gaussian"   # Gaussian (normal) random jitter
    ADAPTIVE = "adaptive"   # Adaptive jitter based on frequency analysis


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class TrafficPattern:
    """Container for traffic arrival times and power consumption."""
    arrival_times: np.ndarray    # Packet arrival times (seconds)
    nominal_times: np.ndarray    # Ideal (unjittered) times (seconds)
    injected_delays: np.ndarray  # Per-packet nonnegative delays (seconds)
    power_samples: np.ndarray    # Power consumption over time
    sample_times: np.ndarray     # Time points for power samples
    jitter_mode: str            # Which jitter algorithm was used
    
    @property
    def n_packets(self) -> int:
        return len(self.arrival_times)
    
    @property
    def duration(self) -> float:
        return self.sample_times[-1] if len(self.sample_times) > 0 else 0.0

    @property
    def mean_injected_delay_s(self) -> float:
        """Average added delay per packet (seconds)."""
        return float(np.mean(self.injected_delays)) if len(self.injected_delays) else 0.0

    @property
    def p99_injected_delay_s(self) -> float:
        """p99 of added delay per packet (seconds)."""
        return float(np.quantile(self.injected_delays, 0.99)) if len(self.injected_delays) else 0.0


@dataclass
class SpectralAnalysis:
    """Container for FFT analysis results."""
    frequencies: np.ndarray      # Frequency bins (Hz)
    power_spectrum: np.ndarray   # Power spectral density (dB)
    peak_frequency: float        # Dominant frequency (Hz)
    peak_power_db: float         # Peak power level (dB)
    noise_floor_db: float        # Average noise floor (dB)
    resonance_energy_db: float   # Energy in the resonance band (dB)


# =============================================================================
# Pulse Train Generator
# =============================================================================

def generate_pulse_train(
    duration: float = 10.0,
    base_interval: float = INFERENCE_BATCH_INTERVAL_S,
    jitter_mode: JitterMode = JitterMode.NONE,
    jitter_fraction: float = JITTER_RANGE_FRACTION,
    max_added_delay_s: float | None = None,
    sample_rate: float = 10000.0,
    seed: int = SIM_RANDOM_SEED
) -> TrafficPattern:
    """
    Generate a pulse train representing inference batch arrivals.
    
    Each "pulse" represents an inference batch that causes a power spike.
    The inter-arrival times can be jittered to break up spectral peaks.
    
    Args:
        duration: Total simulation duration (seconds)
        base_interval: Mean interval between batches (seconds)
        jitter_mode: Type of jitter to apply
        jitter_fraction: Jitter range as fraction of base interval
        sample_rate: Samples per second for power signal
        seed: Random seed for reproducibility
        
    Returns:
        TrafficPattern with arrival times and power samples
    """
    np.random.seed(seed)
    
    # Queue-aware scheduler model (causality-preserving)
    # -----------------------------------------------
    # Packets/jobs arrive periodically at base_interval.
    # The switch may *delay* their release. It cannot transmit a packet before it arrives.
    #
    # We generate a *target* inter-departure interval with jitter (can be +/-),
    # but then enforce causality with:
    #   depart[k] = max(arrival[k], depart[k-1] + target_interval[k])
    #
    # This naturally yields nonnegative waiting times (added latency).
    jitter_range = base_interval * jitter_fraction

    n_packets = int(duration / base_interval) + 1
    nominal_times = (np.arange(n_packets) * base_interval).astype(float)
    nominal_times = nominal_times[nominal_times < duration]

    # Draw target interval jitter
    if jitter_mode == JitterMode.NONE:
        jitter = np.zeros(len(nominal_times))
    elif jitter_mode == JitterMode.UNIFORM:
        jitter = np.random.uniform(-jitter_range, jitter_range, size=len(nominal_times))
    elif jitter_mode == JitterMode.GAUSSIAN:
        jitter = np.random.normal(0.0, jitter_range / 2.0, size=len(nominal_times))
        jitter = np.clip(jitter, -jitter_range, jitter_range)
    elif jitter_mode == JitterMode.ADAPTIVE:
        phase = np.linspace(0.0, 2 * np.pi, len(nominal_times), endpoint=False)
        congestion = 0.5 * (1.0 + np.sin(phase))  # 0..1
        adaptive_range = jitter_range * (0.2 + 0.8 * congestion)
        jitter = np.random.uniform(-adaptive_range, adaptive_range)
    else:
        jitter = np.zeros(len(nominal_times))

    target_intervals = np.maximum(JITTER_MIN_INTERVAL_S, base_interval + jitter)

    # Build departure schedule (these are the actual transmission times)
    # Optionally enforce a hard cap on added delay (latency impact constraint).
    departure_times = np.zeros_like(nominal_times)
    departure_times[0] = nominal_times[0]
    for k in range(1, len(nominal_times)):
        desired_departure = departure_times[k - 1] + target_intervals[k]
        lower_bound = max(nominal_times[k], departure_times[k - 1])  # causality + monotonicity

        if max_added_delay_s is None:
            departure_times[k] = max(lower_bound, desired_departure)
        else:
            upper_bound = nominal_times[k] + max_added_delay_s
            # Clamp desired departure into [lower_bound, upper_bound]
            departure_times[k] = min(max(lower_bound, desired_departure), max(lower_bound, upper_bound))

    injected_delays = departure_times - nominal_times
    arrival_times = departure_times
    
    # Generate power consumption signal
    # Each arrival causes a power spike (modeled as Gaussian pulse)
    sample_times = np.arange(0, duration, 1.0 / sample_rate)
    power_samples = np.zeros_like(sample_times)
    
    # Parameters for power pulse shape
    pulse_width = 0.001  # 1ms pulse duration
    pulse_amplitude = 100.0  # Arbitrary units (represents power in Watts)
    baseline_power = 50.0  # Idle power consumption
    
    for arrival in arrival_times:
        # Add Gaussian pulse at each arrival
        pulse = pulse_amplitude * np.exp(-0.5 * ((sample_times - arrival) / pulse_width) ** 2)
        power_samples += pulse
    
    # Add baseline power and noise
    power_samples += baseline_power
    power_samples += np.random.normal(0, 2, len(power_samples))  # Small noise
    
    return TrafficPattern(
        arrival_times=arrival_times,
        nominal_times=nominal_times,
        injected_delays=injected_delays,
        power_samples=power_samples,
        sample_times=sample_times,
        jitter_mode=jitter_mode.value if hasattr(jitter_mode, 'value') else jitter_mode
    )


# =============================================================================
# Spectral Analysis
# =============================================================================

def compute_spectrum(
    pattern: TrafficPattern,
    resonance_freq: float = INFERENCE_BATCH_FREQ_HZ,
    resonance_bandwidth: float = 20.0
) -> SpectralAnalysis:
    """
    Compute the power spectral density of a traffic pattern.
    
    Uses FFT to analyze the frequency content of the power consumption signal.
    Identifies the resonance peak and measures energy in the danger band.
    
    Args:
        pattern: TrafficPattern from generate_pulse_train()
        resonance_freq: Center frequency of danger band (Hz)
        resonance_bandwidth: Width of danger band (Hz)
        
    Returns:
        SpectralAnalysis with frequency content and metrics
    """
    # Compute FFT
    n_samples = len(pattern.power_samples)
    dt = pattern.sample_times[1] - pattern.sample_times[0]
    sample_rate = 1.0 / dt
    
    # Window the signal to reduce spectral leakage
    window = np.hanning(n_samples)
    windowed_signal = pattern.power_samples * window
    
    # Compute one-sided FFT
    fft_result = np.fft.rfft(windowed_signal)
    frequencies = np.fft.rfftfreq(n_samples, dt)
    
    # Compute power spectral density
    # Normalize by window energy and convert to dB
    window_energy = np.sum(window ** 2)
    psd = np.abs(fft_result) ** 2 / window_energy
    psd_db = 10 * np.log10(psd + 1e-12)  # Add small value to avoid log(0)
    
    # Find peak frequency (excluding DC component)
    dc_cutoff_idx = np.searchsorted(frequencies, 5.0)  # Ignore below 5Hz
    peak_idx = dc_cutoff_idx + np.argmax(psd_db[dc_cutoff_idx:])
    peak_frequency = frequencies[peak_idx]
    peak_power_db = psd_db[peak_idx]
    
    # Calculate noise floor (average of non-peak regions)
    # Use frequencies outside the resonance band
    low_freq_mask = (frequencies > 5) & (frequencies < resonance_freq - resonance_bandwidth)
    high_freq_mask = (frequencies > resonance_freq + resonance_bandwidth) & (frequencies < sample_rate / 4)
    noise_mask = low_freq_mask | high_freq_mask
    noise_floor_db = np.mean(psd_db[noise_mask]) if np.any(noise_mask) else -40.0
    
    # Calculate energy in resonance band
    resonance_mask = (frequencies >= resonance_freq - resonance_bandwidth / 2) & \
                     (frequencies <= resonance_freq + resonance_bandwidth / 2)
    if np.any(resonance_mask):
        resonance_energy = np.sum(psd[resonance_mask])
        resonance_energy_db = 10 * np.log10(resonance_energy + 1e-12)
    else:
        resonance_energy_db = noise_floor_db
    
    return SpectralAnalysis(
        frequencies=frequencies,
        power_spectrum=psd_db,
        peak_frequency=peak_frequency,
        peak_power_db=peak_power_db,
        noise_floor_db=noise_floor_db,
        resonance_energy_db=resonance_energy_db
    )


def calculate_resonance_reduction(
    baseline_spectrum: SpectralAnalysis,
    jittered_spectrum: SpectralAnalysis
) -> float:
    """
    Calculate the dB reduction in resonance energy.
    
    Args:
        baseline_spectrum: Spectrum without jitter
        jittered_spectrum: Spectrum with jitter
        
    Returns:
        Reduction in dB (positive = improvement)
    """
    return baseline_spectrum.resonance_energy_db - jittered_spectrum.resonance_energy_db


# =============================================================================
# Demo / Test
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Spectral Jitter Algorithm - Test Run")
    print("=" * 70)
    
    # Generate baseline (no jitter)
    print("\n1. Generating baseline traffic (no jitter)...")
    baseline = generate_pulse_train(jitter_mode=JitterMode.NONE)
    baseline_spectrum = compute_spectrum(baseline)
    print(f"   Peak Frequency: {baseline_spectrum.peak_frequency:.1f} Hz")
    print(f"   Peak Power: {baseline_spectrum.peak_power_db:.1f} dB")
    print(f"   Noise Floor: {baseline_spectrum.noise_floor_db:.1f} dB")
    print(f"   Resonance Energy: {baseline_spectrum.resonance_energy_db:.1f} dB")
    
    # Generate jittered traffic
    print("\n2. Generating jittered traffic (uniform ±20%)...")
    jittered = generate_pulse_train(jitter_mode=JitterMode.UNIFORM)
    jittered_spectrum = compute_spectrum(jittered)
    print(f"   Peak Frequency: {jittered_spectrum.peak_frequency:.1f} Hz")
    print(f"   Peak Power: {jittered_spectrum.peak_power_db:.1f} dB")
    print(f"   Noise Floor: {jittered_spectrum.noise_floor_db:.1f} dB")
    print(f"   Resonance Energy: {jittered_spectrum.resonance_energy_db:.1f} dB")
    
    # Calculate improvement
    reduction_db = calculate_resonance_reduction(baseline_spectrum, jittered_spectrum)
    print(f"\n3. Resonance Reduction: {reduction_db:.1f} dB")
    print("   (20dB reduction = 100x less energy in danger band)")
    
    print("\n" + "=" * 70)
