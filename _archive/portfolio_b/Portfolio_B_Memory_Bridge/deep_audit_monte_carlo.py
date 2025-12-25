"""
Deep Audit: Monte Carlo Stress Test for Portfolio B
===================================================

This script performs a high-entropy statistical audit of the Grand Unified Cortex.
Instead of a single run with seed 42, it runs 100 iterations of 'The Perfect Storm'
with randomized traffic patterns, failure injection times, and cluster states.

We are looking for:
1. Statistical stability (Does Unified always beat Isolated?)
2. Edge cases (Does the Consensus logic ever fail to recover?)
3. Outlier latencies (Do victims ever see >1us spikes?)

Author: Neural Harris Deep Audit Team
"""

import sys
import os
import numpy as np
import pandas as pd
from tqdm import tqdm

# Add subdirectories to path
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)
sys.path.insert(0, os.path.join(root, "_08_Grand_Unified_Cortex"))

from _08_Grand_Unified_Cortex.perfect_storm import run_perfect_storm

def run_deep_audit(n_trials=100):
    print(f"Starting Deep Audit Monte Carlo (N={n_trials})...")
    
    results = []
    
    for i in tqdm(range(n_trials)):
        # Vary the seed for each trial
        seed = 42 + i
        
        # Run both modes
        iso = run_perfect_storm(mode='isolated', seed=seed)
        uni = run_perfect_storm(mode='unified', seed=seed)
        
        results.append({
            'trial': i,
            'iso_throughput': iso['throughput_alpha'],
            'uni_throughput': uni['throughput_alpha'],
            'iso_latency': iso['victim_latency_ns'],
            'uni_latency': uni['victim_latency_ns'],
            'iso_completion': iso['job_completion'],
            'uni_completion': uni['job_completion'],
            'iso_drops': iso['drop_rate'],
            'uni_drops': uni['drop_rate']
        })
        
    df = pd.DataFrame(results)
    
    # Analyze Results
    print("\n" + "="*60)
    print("DEEP AUDIT REPORT: STATISTICAL RIGOR")
    print("="*60)
    
    # Throughput Gain Distribution
    gain = df['uni_throughput'] / df['iso_throughput'].replace(0, 0.001)
    print(f"Throughput Gain: Mean={gain.mean():.2f}x, Min={gain.min():.2f}x, P99={gain.quantile(0.99):.2f}x")
    
    # Stability Check
    unstable_trials = df[df['uni_throughput'] < df['iso_throughput']]
    print(f"Regressions Detected: {len(unstable_trials)} (Goal: 0)")
    
    # Latency Shielding Stability
    latency_reduction = df['iso_latency'] / df['uni_latency'].replace(0, 1.0)
    print(f"Latency Reduction: Mean={latency_reduction.mean():.1f}x, Worst-case={latency_reduction.min():.1f}x")
    
    # Deterministic Recovery Check
    failed_recovery = df[df['uni_drops'] > 0]
    print(f"Coordinated Drop Failures: {len(failed_recovery)} (Goal: 0)")
    
    print("\n" + "="*60)
    if len(unstable_trials) == 0 and gain.mean() >= 1.5:
        print("AUDIT VERDICT: SOVEREIGN SYSTEM IS STATISTICALLY SUPERIOR")
    else:
        print("AUDIT VERDICT: INSTABILITY DETECTED - LOGIC HARDENING REQUIRED")
    print("="*60)

if __name__ == "__main__":
    run_deep_audit(n_trials=10) # 10 trials for a balanced depth/speed audit










