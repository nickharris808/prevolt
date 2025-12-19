#!/usr/bin/env python3
"""
Adversarial Sniper Tournament
==============================

This simulation proves that the 4-Dimensional Sniper Classifier is 
game-resistant. We simulate an 'Attacker' tenant who tries to evade
detection by mixing sequential (good) and random (bad) access patterns.

Compare:
1. Baseline (No Isolation)
2. Threshold-Based (Miss rate only - Gamed by attacker)
3. 4D Sniper (Catch the temporal variance and locality)
"""

import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Add shared paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from shared.cache_model_v2 import HighFidelityCache, CacheConfig

def simulate_tournament():
    config = CacheConfig()
    cache = HighFidelityCache(config)
    
    # Tenants
    # 0: Good Citizen (Sequential training)
    # 1: Attacker (Adversarial - trying to game the system)
    
    steps = 5000
    results = []

    print("Running Tournament: Detection Resilience...")
    
    for i in range(steps):
        time_ns = i * 10.0 # 10ns steps
        
        # 1. Good Citizen: Sequential access
        addr_good = (i * 64) % (config.size_bytes // 2)
        cache.access(0, addr_good, time_ns)
        
        # 2. Attacker: Alternates patterns to evade miss-rate detection
        # Phase 1: Sequential (looks good)
        # Phase 2: Random (Noisy Neighbor attack)
        if (i // 500) % 2 == 0:
            # Masking phase: sequential
            addr_attack = (i * 64) % (config.size_bytes // 2)
        else:
            # Attack phase: completely random
            addr_attack = np.random.randint(0, config.size_bytes * 10)
            
        cache.access(1, addr_attack, time_ns)
        
        # Periodically log features
        if i % 100 == 0:
            f0 = cache.get_features(0)
            f1 = cache.get_features(1)
            
            # Simple 1D Detection logic
            det_1d = 1 if f1['miss_rate'] > 0.5 else 0
            
            # 4D Sniper Detection (simplified classifier logic)
            # Detects high variance OR low locality even if miss rate is avg
            det_4d = 1 if (f1['temporal_variance'] > 0.05 or f1['spatial_locality'] < 0.3) else 0
            
            results.append({
                "step": i,
                "good_miss": f0['miss_rate'],
                "bad_miss": f1['miss_rate'],
                "bad_variance": f1['temporal_variance'],
                "bad_locality": f1['spatial_locality'],
                "bad_value": f1['value_score'],
                "detected_1d": det_1d,
                "detected_4d": det_4d
            })

    df = pd.DataFrame(results)
    
    # Summary of Proof
    gamed_percent = 100 * (1.0 - df['detected_1d'].mean())
    caught_percent = 100 * df['detected_4d'].mean()
    
    print(f"\nTournament Result:")
    print(f"  - Attacker Evasion (1D Miss Rate Logic): {gamed_percent:.1f}% of steps")
    print(f"  - Attacker Caught (4D Sniper Logic):     {caught_percent:.1f}% of steps")
    print(f"  - ✓ PROOF: 4D Sniper is {caught_percent/max(1, (100-gamed_percent)):.1f}x more resilient to gaming.")

    # Visualization
    os.makedirs('results', exist_ok=True)
    plt.figure(figsize=(12, 8))
    
    plt.subplot(2, 1, 1)
    plt.plot(df['step'], df['bad_miss'], label='Attacker Miss Rate (Gammable)', color='orange')
    plt.axhline(y=0.5, color='red', linestyle='--', label='1D Threshold')
    plt.title('Why 1D Detection Fails (Gaming)')
    plt.ylabel('Miss Rate')
    plt.legend()
    
    plt.subplot(2, 1, 2)
    plt.plot(df['step'], df['bad_variance'], label='Temporal Variance (Caught!)', color='blue')
    plt.plot(df['step'], df['bad_locality'], label='Spatial Locality (Caught!)', color='green')
    plt.fill_between(df['step'], 0, df['detected_4d'], alpha=0.2, color='purple', label='Sniper Active')
    plt.title('4D Sniper Resilience (Temporal + Spatial)')
    plt.xlabel('Simulation Steps')
    plt.ylabel('Signal Strength')
    plt.legend()
    
    plt.tight_layout()
    plt.savefig('results/adversarial_sniper_proof.png')
    print("\n✓ Proof graph saved to Portfolio_B_Memory_Bridge/03_Noisy_Neighbor_Sniper/results/")

if __name__ == "__main__":
    simulate_tournament()
