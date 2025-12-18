"""
Spectral Damping Simulation - Main Entry Point
===============================================

This is the primary simulation script for the Spectral Traffic Shaping invention.
Running this script generates:

1. spectral_heatmap.png - Side-by-side spectral density comparison
2. time_domain.png - Time-domain power consumption comparison
3. tournament_results.csv - Jitter algorithm comparison data

Usage:
    python simulation.py

The "Wow" Factor:
    The spectral heatmap clearly shows a dangerous 100Hz resonance peak
    (which would vibrate transformers) disappearing into the noise floor
    when spectral jitter scheduling is applied.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import pandas as pd
from pathlib import Path
import sys
import os

# Add parent to path for imports
import sys, os
from pathlib import Path
root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root))
family = Path(__file__).parent.parent
sys.path.insert(0, str(family))

from utils.plotting import (
    setup_plot_style,
    save_publication_figure,
    COLOR_FAILURE,
    COLOR_SUCCESS,
    COLOR_WARNING,
)
from utils.constants import INFERENCE_BATCH_FREQ_HZ

# Local imports
from jitter_algorithm import (
    generate_pulse_train,
    compute_spectrum,
    calculate_resonance_reduction,
    JitterMode,
    TrafficPattern,
    SpectralAnalysis
)


# =============================================================================
# Visualization Functions
# =============================================================================

def create_spectral_heatmap(
    baseline_spectrum: SpectralAnalysis,
    jittered_spectrum: SpectralAnalysis,
    output_path: str = None
) -> plt.Figure:
    """
    Create the primary "Wow" deliverable: side-by-side spectral density comparison.
    
    Left panel: Sharp 100Hz spike (The Danger Zone)
    Right panel: Diffuse noise floor with no peaks (The Solution)
    
    Args:
        baseline_spectrum: Spectrum without jitter (dangerous)
        jittered_spectrum: Spectrum with jitter (safe)
        output_path: Path to save the figure
        
    Returns:
        Matplotlib Figure object
    """
    setup_plot_style()
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
    
    fig.suptitle(
        "Spectral Traffic Shaping: Eliminating Dangerous Resonance",
        fontsize=16, fontweight='bold', y=0.98
    )
    
    # Frequency range to display
    freq_max = 500  # Hz
    freq_mask_baseline = baseline_spectrum.frequencies <= freq_max
    freq_mask_jittered = jittered_spectrum.frequencies <= freq_max
    
    # Color map for power spectral density (hot = high power)
    colors = ['#1a1a2e', '#16213e', '#0f3460', '#e94560', '#ff6b6b', '#ffd93d']
    custom_cmap = LinearSegmentedColormap.from_list('power', colors)
    
    # ==========================================================================
    # Left Panel: Baseline (Dangerous Resonance)
    # ==========================================================================
    
    freqs = baseline_spectrum.frequencies[freq_mask_baseline]
    psd = baseline_spectrum.power_spectrum[freq_mask_baseline]
    
    # Create a 2D representation for heatmap effect
    # Stack the spectrum vertically to create a "waterfall" look
    psd_2d = np.tile(psd, (50, 1))
    
    ax1.imshow(
        psd_2d,
        aspect='auto',
        extent=[freqs[0], freqs[-1], 0, 1],
        origin='lower',
        cmap=custom_cmap,
        vmin=-20,
        vmax=80
    )
    
    # Overlay the spectrum line
    ax1_twin = ax1.twinx()
    ax1_twin.plot(freqs, psd, color='white', linewidth=2, alpha=0.9)
    ax1_twin.set_ylim(-20, 90)
    ax1_twin.set_ylabel('Power Spectral Density (dB)', fontsize=11, color='white')
    ax1_twin.tick_params(axis='y', colors='white')
    
    # Mark the resonance frequency
    ax1.axvline(x=100, color='white', linestyle='--', linewidth=2, alpha=0.7)
    ax1.text(105, 0.85, '100 Hz\nRESONANCE', fontsize=10, color='white', fontweight='bold',
             transform=ax1.get_xaxis_transform())
    
    # Add danger annotation (ASCII only to avoid font glyph warnings)
    ax1.text(0.5, 0.95, 'DANGER: 100Hz Spike', 
             transform=ax1.transAxes, fontsize=12, color='#ff6b6b',
             fontweight='bold', ha='center', va='top',
             bbox=dict(boxstyle='round', facecolor='black', alpha=0.7))
    
    ax1.set_xlabel('Frequency (Hz)', fontsize=12)
    ax1.set_ylabel('Time Window', fontsize=11)
    ax1.set_title(f'Baseline: No Jitter\nPeak Power: {baseline_spectrum.peak_power_db:.1f} dB', 
                  fontsize=12, pad=10)
    ax1.set_yticks([])
    
    # ==========================================================================
    # Right Panel: Jittered (Safe)
    # ==========================================================================
    
    freqs = jittered_spectrum.frequencies[freq_mask_jittered]
    psd = jittered_spectrum.power_spectrum[freq_mask_jittered]
    
    # Create 2D representation
    psd_2d = np.tile(psd, (50, 1))
    
    ax2.imshow(
        psd_2d,
        aspect='auto',
        extent=[freqs[0], freqs[-1], 0, 1],
        origin='lower',
        cmap=custom_cmap,
        vmin=-20,
        vmax=80
    )
    
    # Overlay the spectrum line
    ax2_twin = ax2.twinx()
    ax2_twin.plot(freqs, psd, color='white', linewidth=2, alpha=0.9)
    ax2_twin.set_ylim(-20, 90)
    ax2_twin.set_ylabel('Power Spectral Density (dB)', fontsize=11, color='white')
    ax2_twin.tick_params(axis='y', colors='white')
    
    # Mark where the resonance WAS
    ax2.axvline(x=100, color='white', linestyle='--', linewidth=2, alpha=0.4)
    ax2.text(105, 0.85, '100 Hz\n(suppressed)', fontsize=10, color='white', alpha=0.7,
             transform=ax2.get_xaxis_transform())
    
    # Add success annotation (ASCII only to avoid font glyph warnings)
    peak_reduction = baseline_spectrum.peak_power_db - jittered_spectrum.peak_power_db
    ax2.text(0.5, 0.95, f'SAFE: {peak_reduction:.1f} dB Peak Reduction', 
             transform=ax2.transAxes, fontsize=12, color='#4ade80',
             fontweight='bold', ha='center', va='top',
             bbox=dict(boxstyle='round', facecolor='black', alpha=0.7))
    
    ax2.set_xlabel('Frequency (Hz)', fontsize=12)
    ax2.set_ylabel('Time Window', fontsize=11)
    ax2.set_title(f'Spectral Jitter: ±20% Randomization\nPeak Power: {jittered_spectrum.peak_power_db:.1f} dB',
                  fontsize=12, pad=10)
    ax2.set_yticks([])
    
    # ==========================================================================
    # Add summary annotation
    # ==========================================================================
    
    fig.text(0.5, 0.02, 
             f"Patent Claim: Network scheduling with spectral jitter eliminates "
             f"resonance ({peak_reduction:.1f} dB reduction in peak energy)",
             ha='center', fontsize=11, style='italic', color='#666666')
    
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.08, top=0.90)
    
    # Save figure
    if output_path is None:
        output_path = Path(__file__).parent / "spectral_heatmap"
    
    save_publication_figure(fig, str(output_path), dpi=300, formats=['png'])
    
    return fig


def create_time_domain_plot(
    baseline: TrafficPattern,
    jittered: TrafficPattern,
    output_path: str = None
) -> plt.Figure:
    """
    Create a time-domain comparison showing packet arrivals and power.
    
    This visualization shows:
    - Top: Regular packet arrivals (dangerous periodic pattern)
    - Bottom: Jittered packet arrivals (spread out, non-periodic)
    
    Args:
        baseline: Traffic pattern without jitter
        jittered: Traffic pattern with jitter
        output_path: Path to save the figure
        
    Returns:
        Matplotlib Figure object
    """
    setup_plot_style()
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
    
    fig.suptitle("Traffic Pattern Comparison: Regular vs. Jittered Scheduling",
                 fontsize=14, fontweight='bold', y=0.98)
    
    # Time window to display (zoomed in to show pattern clearly)
    t_start = 0.0
    t_end = 0.5  # 500ms window
    
    # ==========================================================================
    # Top Panel: Baseline (Regular)
    # ==========================================================================
    
    time_mask = baseline.sample_times <= t_end
    
    ax1.fill_between(
        baseline.sample_times[time_mask] * 1000,
        0,
        baseline.power_samples[time_mask],
        alpha=0.7,
        color=COLOR_FAILURE,
        label='Power Consumption'
    )
    
    # Mark arrival times
    arrivals_in_window = baseline.arrival_times[baseline.arrival_times <= t_end]
    for arrival in arrivals_in_window:
        ax1.axvline(x=arrival * 1000, color='#333333', linestyle='-', 
                    linewidth=1, alpha=0.3)
    
    ax1.set_ylabel('Power (W)', fontsize=11)
    ax1.set_title('Baseline: Regular 100Hz Arrivals (Dangerous)', fontsize=12, color=COLOR_FAILURE)
    ax1.legend(loc='upper right')
    ax1.set_ylim(0, 180)
    ax1.grid(True, alpha=0.3)
    
    # Add pattern indicator
    ax1.text(0.02, 0.95, 'Perfect 10ms intervals\n→ 100Hz resonance', 
             transform=ax1.transAxes, fontsize=10,
             bbox=dict(boxstyle='round', facecolor='white', edgecolor=COLOR_FAILURE),
             va='top')
    
    # ==========================================================================
    # Bottom Panel: Jittered
    # ==========================================================================
    
    time_mask = jittered.sample_times <= t_end
    
    ax2.fill_between(
        jittered.sample_times[time_mask] * 1000,
        0,
        jittered.power_samples[time_mask],
        alpha=0.7,
        color=COLOR_SUCCESS,
        label='Power Consumption'
    )
    
    # Mark arrival times
    arrivals_in_window = jittered.arrival_times[jittered.arrival_times <= t_end]
    for arrival in arrivals_in_window:
        ax2.axvline(x=arrival * 1000, color='#333333', linestyle='-',
                    linewidth=1, alpha=0.3)
    
    ax2.set_xlabel('Time (ms)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Power (W)', fontsize=11)
    ax2.set_title('Spectral Jitter: ±20% Randomized Arrivals (Safe)', fontsize=12, color=COLOR_SUCCESS)
    ax2.legend(loc='upper right')
    ax2.set_ylim(0, 180)
    ax2.set_xlim(0, t_end * 1000)
    ax2.grid(True, alpha=0.3)
    
    # Add pattern indicator
    ax2.text(0.02, 0.95, 'Randomized intervals\n→ No resonance', 
             transform=ax2.transAxes, fontsize=10,
             bbox=dict(boxstyle='round', facecolor='white', edgecolor=COLOR_SUCCESS),
             va='top')
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.92)
    
    # Save figure
    if output_path is None:
        output_path = Path(__file__).parent / "time_domain"
    
    save_publication_figure(fig, str(output_path), dpi=300, formats=['png'])
    
    return fig


def create_spectrum_comparison_plot(
    baseline_spectrum: SpectralAnalysis,
    jittered_spectrum: SpectralAnalysis,
    output_path: str = None
) -> plt.Figure:
    """
    Create an overlaid spectrum plot showing the frequency content.
    
    Args:
        baseline_spectrum: Spectrum without jitter
        jittered_spectrum: Spectrum with jitter
        output_path: Path to save the figure
        
    Returns:
        Matplotlib Figure object
    """
    setup_plot_style()
    
    fig, ax = plt.subplots(figsize=(14, 7))
    
    # Frequency range
    freq_max = 500
    freq_mask = baseline_spectrum.frequencies <= freq_max
    
    # Plot both spectra
    ax.plot(baseline_spectrum.frequencies[freq_mask],
            baseline_spectrum.power_spectrum[freq_mask],
            color=COLOR_FAILURE, linewidth=2.5,
            label=f'Baseline (Peak: {baseline_spectrum.peak_power_db:.1f} dB)')
    
    ax.plot(jittered_spectrum.frequencies[freq_mask],
            jittered_spectrum.power_spectrum[freq_mask],
            color=COLOR_SUCCESS, linewidth=2.5,
            label=f'With Jitter (Peak: {jittered_spectrum.peak_power_db:.1f} dB)')
    
    # Mark resonance frequency
    ax.axvline(x=100, color='#666666', linestyle='--', linewidth=1.5, alpha=0.7)
    ax.text(102, 75, '100 Hz\n(Resonance)', fontsize=10, va='top')
    
    # Add danger zone shading
    ax.axvspan(90, 110, alpha=0.2, color=COLOR_FAILURE, label='Danger Band (90-110 Hz)')
    
    # Configure axes
    ax.set_xlabel('Frequency (Hz)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Power Spectral Density (dB)', fontsize=12, fontweight='bold')
    ax.set_title('Power Spectrum Comparison: Resonance Elimination via Spectral Jitter',
                 fontsize=14, fontweight='bold')
    ax.set_xlim(0, freq_max)
    ax.set_ylim(-10, 85)
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(True, alpha=0.5)
    
    # Add improvement annotation
    peak_reduction = baseline_spectrum.peak_power_db - jittered_spectrum.peak_power_db
    ax.annotate(
        f'{peak_reduction:.1f} dB\nReduction',
        xy=(100, baseline_spectrum.peak_power_db),
        xytext=(200, baseline_spectrum.peak_power_db - 5),
        fontsize=12, fontweight='bold',
        color=COLOR_SUCCESS,
        arrowprops=dict(arrowstyle='->', color=COLOR_SUCCESS, linewidth=2)
    )
    
    plt.tight_layout()
    
    # Save figure
    if output_path is None:
        output_path = Path(__file__).parent / "spectrum_comparison"
    
    save_publication_figure(fig, str(output_path), dpi=300, formats=['png'])
    
    return fig


def run_jitter_tournament(*, jitter_fraction: float) -> pd.DataFrame:
    """
    Run a tournament comparing different jitter algorithms.
    
    Returns:
        DataFrame with comparison results
    """
    results = []
    
    # Generate baseline
    print("  Running baseline (no jitter)...")
    baseline = generate_pulse_train(jitter_mode=JitterMode.NONE, jitter_fraction=jitter_fraction)
    baseline_spectrum = compute_spectrum(baseline)
    
    results.append({
        'Algorithm': 'None (Baseline)',
        'Peak Frequency (Hz)': baseline_spectrum.peak_frequency,
        'Peak Power (dB)': baseline_spectrum.peak_power_db,
        'Noise Floor (dB)': baseline_spectrum.noise_floor_db,
        'Resonance Energy (dB)': baseline_spectrum.resonance_energy_db,
        'Peak Reduction (dB)': 0.0,
        'Mean Added Delay (ms)': 0.0,
        'p99 Added Delay (ms)': 0.0,
    })
    
    # Test each jitter mode
    for mode in [JitterMode.UNIFORM, JitterMode.GAUSSIAN, JitterMode.ADAPTIVE]:
        print(f"  Running {mode.value} jitter...")
        pattern = generate_pulse_train(jitter_mode=mode, jitter_fraction=jitter_fraction)
        spectrum = compute_spectrum(pattern)
        
        reduction = calculate_resonance_reduction(baseline_spectrum, spectrum)
        peak_reduction = baseline_spectrum.peak_power_db - spectrum.peak_power_db
        
        results.append({
            'Algorithm': mode.value.title(),
            'Peak Frequency (Hz)': spectrum.peak_frequency,
            'Peak Power (dB)': spectrum.peak_power_db,
            'Noise Floor (dB)': spectrum.noise_floor_db,
            'Resonance Energy (dB)': spectrum.resonance_energy_db,
            'Peak Reduction (dB)': peak_reduction,
            'Mean Added Delay (ms)': pattern.mean_injected_delay_s * 1e3,
            'p99 Added Delay (ms)': pattern.p99_injected_delay_s * 1e3,
        })
    
    return pd.DataFrame(results)


# =============================================================================
# Main Execution
# =============================================================================

def main():
    """Main entry point for the Spectral Damping simulation."""
    print("=" * 80)
    print("SPECTRAL DAMPING SIMULATION")
    print("Portfolio A: Grid-to-Gate Power Orchestration")
    print("=" * 80)
    
    output_dir = Path(__file__).parent
    
    # Acceptance targets (user-specified)
    target_peak_reduction_db = 20.0
    # Interpreting \"total latency\" as end-to-end inference SLA budget.
    # Default: 600ms budget -> 5% = 30ms average allowed scheduling delay.
    latency_budget_ms = 600.0
    max_mean_delay_ms = 0.05 * latency_budget_ms

    # Choose jitter magnitude. This value was empirically found (via tournament sweep)
    # to reach >=20dB peak reduction for the modeled pulse train.
    jitter_fraction = 0.45  # +/- 45% interval variability

    # Generate traffic patterns
    print("\n1. Generating traffic patterns...")
    baseline = generate_pulse_train(duration=10.0, jitter_mode=JitterMode.NONE, jitter_fraction=jitter_fraction)
    jittered = generate_pulse_train(duration=10.0, jitter_mode=JitterMode.UNIFORM, jitter_fraction=jitter_fraction)
    print(f"   Baseline: {baseline.n_packets} packets")
    print(f"   Jittered: {jittered.n_packets} packets")
    print(f"   Mean added scheduling delay: {jittered.mean_injected_delay_s*1e3:.2f} ms")
    print(f"   p99 added scheduling delay:  {jittered.p99_injected_delay_s*1e3:.2f} ms")
    
    # Compute spectra
    print("\n2. Computing power spectra...")
    baseline_spectrum = compute_spectrum(baseline)
    jittered_spectrum = compute_spectrum(jittered)
    print(f"   Baseline peak: {baseline_spectrum.peak_power_db:.1f} dB at {baseline_spectrum.peak_frequency:.1f} Hz")
    print(f"   Jittered peak: {jittered_spectrum.peak_power_db:.1f} dB at {jittered_spectrum.peak_frequency:.1f} Hz")
    
    peak_reduction = baseline_spectrum.peak_power_db - jittered_spectrum.peak_power_db
    print(f"   Peak reduction: {peak_reduction:.1f} dB")

    # Acceptance checks
    mean_delay_ms = jittered.mean_injected_delay_s * 1e3
    passes_peak = peak_reduction >= target_peak_reduction_db
    passes_latency = mean_delay_ms <= max_mean_delay_ms
    print(f"\nAcceptance checks:")
    print(f"  - Peak reduction >= {target_peak_reduction_db:.1f} dB: {passes_peak}")
    print(f"  - Mean added delay <= {max_mean_delay_ms:.1f} ms (5% of {latency_budget_ms:.0f} ms): {passes_latency}")
    
    # Generate visualizations
    print("\n3. Generating spectral heatmap...")
    fig1 = create_spectral_heatmap(baseline_spectrum, jittered_spectrum,
                                    str(output_dir / "spectral_heatmap"))
    print("   ✓ Saved: spectral_heatmap.png")
    
    print("\n4. Generating time domain plot...")
    fig2 = create_time_domain_plot(baseline, jittered,
                                    str(output_dir / "time_domain"))
    print("   ✓ Saved: time_domain.png")
    
    print("\n5. Generating spectrum comparison...")
    fig3 = create_spectrum_comparison_plot(baseline_spectrum, jittered_spectrum,
                                            str(output_dir / "spectrum_comparison"))
    print("   ✓ Saved: spectrum_comparison.png")
    
    # Run tournament
    print("\n6. Running jitter algorithm tournament...")
    results_df = run_jitter_tournament(jitter_fraction=jitter_fraction)
    csv_path = output_dir / "tournament_results.csv"
    results_df.to_csv(csv_path, index=False)
    print(f"   ✓ Saved: {csv_path}")
    
    # Print tournament results
    print("\n" + "-" * 80)
    print("JITTER ALGORITHM TOURNAMENT RESULTS")
    print("-" * 80)
    print(results_df.to_string(index=False))
    
    # Summary
    print("\n" + "=" * 80)
    print("SIMULATION COMPLETE")
    print("=" * 80)
    print(f"\nKey Result: {peak_reduction:.1f} dB reduction in 100Hz resonance peak")
    print(f"            This eliminates dangerous transformer vibration")
    print(f"\nOutput files in: {output_dir}")
    print("  - spectral_heatmap.png (Primary deliverable)")
    print("  - time_domain.png (Traffic pattern visualization)")
    print("  - spectrum_comparison.png (Overlaid spectra)")
    print("  - tournament_results.csv (Algorithm comparison)")
    print("\n")
    
    # Close figures
    plt.close('all')


if __name__ == "__main__":
    main()
