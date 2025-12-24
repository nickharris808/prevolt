"""
Publication-Quality Plotting Utilities
======================================

Consistent styling for all Portfolio A visualizations.
Designed to produce figures suitable for:
- Patent filings
- Technical due diligence presentations
- Engineering validation reports

All figures use:
- 300 DPI resolution for print quality
- Consistent color scheme (Red=Failure, Green=Success, Yellow=Warning)
- Engineering notation for axis labels
- Clean, professional seaborn styling
"""

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import seaborn as sns
from typing import Tuple, Optional, List
from pathlib import Path

# =============================================================================
# Color Scheme
# =============================================================================

# Primary colors for status indication
COLOR_FAILURE = '#DC3545'      # Bootstrap red - for baseline/failure cases
COLOR_WARNING = '#FFC107'      # Bootstrap yellow - for static/warning cases  
COLOR_SUCCESS = '#28A745'      # Bootstrap green - for patented solution success
COLOR_NEUTRAL = '#6C757D'      # Bootstrap gray - for neutral/reference

# Extended palette for multiple traces
COLOR_PALETTE = [
    COLOR_FAILURE,   # First trace is always the failure baseline
    COLOR_WARNING,   # Second trace is often the "safe but slow" approach
    COLOR_SUCCESS,   # Third trace is the patented solution
    '#17A2B8',       # Cyan - for additional traces
    '#6F42C1',       # Purple - for additional traces
    '#FD7E14',       # Orange - for additional traces
]

# Background zones for danger/safe regions
COLOR_DANGER_ZONE = '#FFCCCC'    # Light red - danger zone background
COLOR_SAFE_ZONE = '#CCFFCC'      # Light green - safe zone background

# Traffic class colors (for QoS simulations)
COLOR_GOLD_TRAFFIC = '#FFD700'   # Gold
COLOR_BRONZE_TRAFFIC = '#CD7F32' # Bronze


# =============================================================================
# Plot Style Configuration
# =============================================================================

def setup_plot_style():
    """
    Configure matplotlib/seaborn for publication-quality figures.
    
    Call this at the start of any simulation script to ensure
    consistent styling across all Portfolio A deliverables.
    """
    # Use seaborn's clean whitegrid style
    # Note: seaborn 0.12+ uses 'v0_8' prefix for legacy styles
    try:
        plt.style.use('seaborn-v0_8-whitegrid')
    except OSError:
        # Fallback for older seaborn versions
        plt.style.use('seaborn-whitegrid')
    
    # Override specific settings for engineering figures
    plt.rcParams.update({
        # Font settings
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
        'font.size': 10,
        'axes.titlesize': 12,
        'axes.labelsize': 11,
        'legend.fontsize': 9,
        'xtick.labelsize': 9,
        'ytick.labelsize': 9,
        
        # Line settings
        'lines.linewidth': 1.5,
        'lines.markersize': 6,
        
        # Figure settings
        'figure.figsize': (10, 6),
        'figure.dpi': 100,  # Screen DPI (save uses 300)
        'figure.facecolor': 'white',
        'figure.edgecolor': 'white',
        
        # Axes settings
        'axes.facecolor': 'white',
        'axes.edgecolor': '#333333',
        'axes.linewidth': 1.0,
        'axes.grid': True,
        'axes.axisbelow': True,
        
        # Grid settings
        'grid.color': '#CCCCCC',
        'grid.linewidth': 0.5,
        'grid.alpha': 0.7,
        
        # Legend settings
        'legend.frameon': True,
        'legend.framealpha': 0.9,
        'legend.edgecolor': '#CCCCCC',
        
        # Save settings
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.1,
        'savefig.facecolor': 'white',
        'savefig.edgecolor': 'white',
    })


def create_oscilloscope_figure(
    figsize: Tuple[float, float] = (12, 7),
    title: str = "Voltage Transient Analysis"
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Create a figure styled like a digital oscilloscope display.
    
    Features:
    - Dark grid lines reminiscent of oscilloscope graticule
    - Proper voltage/time axis formatting
    - Space for annotations
    
    Args:
        figsize: Figure dimensions (width, height) in inches
        title: Figure title
        
    Returns:
        Tuple of (figure, axes) objects
    """
    setup_plot_style()
    
    fig, ax = plt.subplots(figsize=figsize)
    
    # Style the axes to look like an oscilloscope
    ax.set_facecolor('#FAFAFA')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
    
    # Configure grid to look like oscilloscope graticule
    ax.grid(True, which='major', linestyle='-', linewidth=0.8, color='#CCCCCC')
    ax.grid(True, which='minor', linestyle=':', linewidth=0.4, color='#DDDDDD')
    ax.minorticks_on()
    
    return fig, ax


def create_stacked_figure(
    n_subplots: int = 2,
    figsize: Tuple[float, float] = (12, 8),
    title: str = "Correlated Analysis",
    share_x: bool = True
) -> Tuple[plt.Figure, List[plt.Axes]]:
    """
    Create a figure with vertically stacked subplots sharing X-axis.
    
    Ideal for showing correlated signals like:
    - Voltage + Throughput (Telemetry Loop)
    - Power + Traffic Classes (Brownout Shedder)
    
    Args:
        n_subplots: Number of vertically stacked plots
        figsize: Figure dimensions
        title: Figure suptitle
        share_x: Whether subplots share X-axis
        
    Returns:
        Tuple of (figure, list of axes)
    """
    setup_plot_style()
    
    fig, axes = plt.subplots(
        n_subplots, 1, 
        figsize=figsize, 
        sharex=share_x,
        gridspec_kw={'hspace': 0.15}
    )
    
    fig.suptitle(title, fontsize=14, fontweight='bold', y=0.98)
    
    # Convert to list if single subplot
    if n_subplots == 1:
        axes = [axes]
    
    return fig, list(axes)


def create_side_by_side_figure(
    figsize: Tuple[float, float] = (14, 6),
    title: str = "Before/After Comparison"
) -> Tuple[plt.Figure, Tuple[plt.Axes, plt.Axes]]:
    """
    Create a figure with two side-by-side subplots.
    
    Ideal for before/after comparisons like:
    - Spectral density with/without jitter
    - Queue depth baseline vs invention
    
    Args:
        figsize: Figure dimensions
        title: Figure suptitle
        
    Returns:
        Tuple of (figure, (left_axes, right_axes))
    """
    setup_plot_style()
    
    fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=figsize)
    fig.suptitle(title, fontsize=14, fontweight='bold', y=0.98)
    
    return fig, (ax_left, ax_right)


# =============================================================================
# Axis Formatting Utilities
# =============================================================================

def format_time_axis(ax: plt.Axes, unit: str = 'µs'):
    """
    Format X-axis for time display with engineering notation.
    
    Args:
        ax: Matplotlib axes object
        unit: Time unit to display (ns, µs, ms, s)
    """
    ax.set_xlabel(f'Time ({unit})', fontsize=11)
    
    # Use engineering formatter for clean tick labels
    ax.xaxis.set_major_formatter(ticker.EngFormatter(unit='s'))


def format_voltage_axis(ax: plt.Axes, 
                         v_min: float = 0.6, 
                         v_max: float = 1.0,
                         danger_threshold: float = 0.8):
    """
    Format Y-axis for voltage display with danger zone shading.
    
    Args:
        ax: Matplotlib axes object
        v_min: Minimum voltage to display
        v_max: Maximum voltage to display
        danger_threshold: Voltage below which is "danger zone"
    """
    ax.set_ylabel('Voltage (V)', fontsize=11)
    ax.set_ylim(v_min, v_max)
    
    # Add danger zone shading
    ax.axhspan(v_min, danger_threshold, alpha=0.2, color=COLOR_FAILURE, 
               label='Danger Zone (<0.8V)')
    
    # Add horizontal line at threshold
    ax.axhline(y=danger_threshold, color=COLOR_FAILURE, linestyle='--', 
               linewidth=1, alpha=0.7)


def format_frequency_axis(ax: plt.Axes, f_max: float = 500.0):
    """
    Format axis for frequency display (for spectral plots).
    
    Args:
        ax: Matplotlib axes object
        f_max: Maximum frequency to display in Hz
    """
    ax.set_xlabel('Frequency (Hz)', fontsize=11)
    ax.set_xlim(0, f_max)


def format_power_axis(ax: plt.Axes, unit: str = 'dB'):
    """
    Format Y-axis for power spectral density display.
    
    Args:
        ax: Matplotlib axes object
        unit: Power unit (dB, W, or normalized)
    """
    if unit == 'dB':
        ax.set_ylabel('Power Spectral Density (dB)', fontsize=11)
    elif unit == 'normalized':
        ax.set_ylabel('Normalized Power', fontsize=11)
    else:
        ax.set_ylabel(f'Power ({unit})', fontsize=11)


# =============================================================================
# Annotation Utilities
# =============================================================================

def add_annotation_box(
    ax: plt.Axes,
    text: str,
    xy: Tuple[float, float],
    xytext: Tuple[float, float],
    color: str = COLOR_SUCCESS
):
    """
    Add a boxed annotation with arrow pointing to a feature.
    
    Args:
        ax: Matplotlib axes object
        text: Annotation text
        xy: Point to annotate (data coordinates)
        xytext: Text position (data coordinates)
        color: Box border color
    """
    ax.annotate(
        text,
        xy=xy,
        xytext=xytext,
        fontsize=10,
        fontweight='bold',
        ha='center',
        va='center',
        bbox=dict(
            boxstyle='round,pad=0.5',
            facecolor='white',
            edgecolor=color,
            linewidth=2
        ),
        arrowprops=dict(
            arrowstyle='->',
            connectionstyle='arc3,rad=0.2',
            color=color,
            linewidth=2
        )
    )


def add_improvement_label(
    ax: plt.Axes,
    baseline_value: float,
    improved_value: float,
    unit: str,
    position: Tuple[float, float],
    metric_name: str = "Improvement"
):
    """
    Add a label showing the improvement percentage.
    
    Args:
        ax: Matplotlib axes object
        baseline_value: Value before improvement
        improved_value: Value after improvement
        unit: Unit of measurement
        position: Position for the label (axes coordinates 0-1)
        metric_name: Name of the metric being improved
    """
    if baseline_value != 0:
        improvement_pct = abs(baseline_value - improved_value) / abs(baseline_value) * 100
        improvement_factor = abs(baseline_value / improved_value) if improved_value != 0 else float('inf')
    else:
        improvement_pct = 100 if improved_value == 0 else float('inf')
        improvement_factor = float('inf')
    
    text = f"{metric_name}:\n{baseline_value:.1f} → {improved_value:.1f} {unit}\n({improvement_factor:.1f}x better)"
    
    ax.text(
        position[0], position[1],
        text,
        transform=ax.transAxes,
        fontsize=10,
        fontweight='bold',
        verticalalignment='top',
        horizontalalignment='left',
        bbox=dict(
            boxstyle='round,pad=0.5',
            facecolor=COLOR_SUCCESS,
            edgecolor='none',
            alpha=0.8
        ),
        color='white'
    )


# =============================================================================
# Save Utilities
# =============================================================================

def save_publication_figure(
    fig: plt.Figure,
    filepath: str,
    dpi: int = 300,
    formats: List[str] = ['png']
):
    """
    Save figure in publication-quality format(s).
    
    Args:
        fig: Matplotlib figure object
        filepath: Base path without extension
        dpi: Resolution in dots per inch
        formats: List of formats to save (png, pdf, svg)
    """
    path = Path(filepath)
    
    for fmt in formats:
        output_path = path.with_suffix(f'.{fmt}')
        fig.savefig(
            output_path,
            dpi=dpi,
            bbox_inches='tight',
            pad_inches=0.1,
            facecolor='white',
            edgecolor='none'
        )
        print(f"Saved: {output_path}")


# =============================================================================
# Demo / Test
# =============================================================================

if __name__ == "__main__":
    # Demonstrate the plotting utilities
    setup_plot_style()
    
    # Create a demo oscilloscope figure
    fig, ax = create_oscilloscope_figure(title="Demo: Voltage Transient Analysis")
    
    # Generate demo data
    t = np.linspace(0, 100e-6, 1000)  # 100µs
    
    # Baseline: voltage crash
    v_baseline = 0.9 - 0.3 * np.exp(-t / 10e-6) * (t > 20e-6)
    
    # With pre-charge: stable
    v_improved = 0.9 - 0.05 * np.exp(-t / 10e-6) * (t > 20e-6)
    
    # Plot
    ax.plot(t * 1e6, v_baseline, color=COLOR_FAILURE, label='Baseline (No Pre-Charge)', linewidth=2)
    ax.plot(t * 1e6, v_improved, color=COLOR_SUCCESS, label='With Pre-Charge', linewidth=2)
    
    # Format
    ax.set_xlabel('Time (µs)')
    ax.set_ylabel('Voltage (V)')
    ax.set_ylim(0.5, 1.0)
    ax.axhspan(0.5, 0.8, alpha=0.2, color=COLOR_FAILURE, label='Danger Zone')
    ax.legend(loc='lower right')
    
    plt.tight_layout()
    plt.show()
    print("Plotting utilities demo complete.")







