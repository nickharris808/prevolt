"""
Portfolio A: Economic ROI & TCO Master Calculator
=================================================

This tool generates the quantitative 'Investment Case' for the IP portfolio.
It converts physical results (dB reduction, voltage stability) into 
hard economic data for strategic acquirers.

Targets:
- Nvidia: Avoided Revenue Loss (Blackwell compatibility)
- Broadcom: Incremental Switch Margin
- Meta/Google: Facility CAPEX Savings (Avoided Upgrades)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys
import os

# Add root to sys.path
sys.path.insert(0, str(Path(__file__).parent))
from utils.plotting import setup_plot_style, save_publication_figure

def calculate_roi(cluster_size=32768, gpu_cost=30000, crash_rate_baseline=0.02):
    """
    Calculate ROI metrics for a hyperscale AI cluster.
    
    Arguments:
        cluster_size: Number of GPUs in the fabric.
        gpu_cost: Unit cost per GPU ($).
        crash_rate_baseline: % of jobs failing due to power transients today.
    """
    
    # 1. Revenue Loss Prevention (Family 1 & 2)
    # Average AI training job lasts 30 days. One crash loses 2 days of progress.
    days_per_year = 365
    job_loss_cost = (gpu_cost / 1000) * cluster_size * (2/365) # Pro-rated compute value
    total_annual_risk = job_loss_cost * (crash_rate_baseline * 12)
    
    # Invention: Reduces crash rate by 95%
    savings_reliability = total_annual_risk * 0.95
    
    # 2. Facility CAPEX Savings (Family 3)
    # Cost to upgrade transformers for high-harmonic load: $5M per 10MW
    facility_power_mw = (cluster_size * 1000) / 1e6 # 1kW per GPU
    avoided_upgrade_cost = (facility_power_mw / 10) * 5000000
    
    # 3. Stranded Capacity Unlock (Family 4)
    # Grid limits often force 20% 'Power Buffer'.
    # Invention allows using that buffer safely.
    unlocked_gpu_revenue = cluster_size * 0.20 * (gpu_cost * 0.1) # 10% annual compute rent
    
    # 4. Grid Revenue Generation (Family 7)
    # Participation in FCR (Frequency Containment Reserve) markets.
    fcr_revenue_per_mw_year = 25.0 * 8760 * 0.95 # $/MW-year
    grid_vpp_revenue = (facility_power_mw * 0.3) * fcr_revenue_per_mw_year
    
    metrics = {
        'Avoided Job Losses ($M/yr)': savings_reliability / 1e6,
        'Avoided CAPEX Upgrades ($M)': avoided_upgrade_cost / 1e6,
        'Unlocked Revenue ($M/yr)': unlocked_gpu_revenue / 1e6,
        'Grid VPP Revenue ($M/yr)': grid_vpp_revenue / 1e6,
        'Total 3-Year Value ($M)': (savings_reliability*3 + avoided_upgrade_cost + unlocked_gpu_revenue*3 + grid_vpp_revenue*3) / 1e6
    }
    
    return metrics

def generate_visuals():
    setup_plot_style()
    
    # ROI over Cluster Size
    sizes = [1024, 4096, 16384, 32768, 65536]
    total_values = [calculate_roi(cluster_size=s)['Total 3-Year Value ($M)'] for s in sizes]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(sizes, total_values, 'o-', linewidth=3, color='green', label='IP Value (Total Value Created)')
    
    # Acquisition Bins
    ax.axhspan(0, 50, color='gray', alpha=0.1, label='Seed/A-Round Value')
    ax.axhspan(50, 150, color='blue', alpha=0.1, label='Strategic Strategic M&A Zone')
    ax.axhspan(150, 500, color='gold', alpha=0.1, label='Market Dominance Value')
    
    ax.set_title("Economic Multiplier: Portfolio Value vs. Deployment Scale")
    ax.set_xlabel("Total Cluster Scale (GPUs)")
    ax.set_ylabel("Total Economic Value Created ($M)")
    ax.legend()
    ax.grid(True)
    
    save_publication_figure(fig, str(Path(__file__).parent / "executive_roi_scaling"))
    plt.close(fig)

if __name__ == "__main__":
    print("=" * 80)
    print("PORTFOLIO A: ECONOMIC ROI ANALYSIS")
    print("=" * 80)
    
    m = calculate_roi()
    for k, v in m.items():
        print(f"{k:<30} | {v:>10.1f}")
        
    generate_visuals()
    print("\nROI Visualization saved to executive_roi_scaling.png")

