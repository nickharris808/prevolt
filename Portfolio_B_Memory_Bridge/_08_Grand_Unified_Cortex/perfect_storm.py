"""
PF8: The Perfect Storm Simulation
=================================

This simulation unifies all 4 patent families (PF4-PF7) and subjects them to
a simultaneous failure scenario:
1. Incast Congestion (PF4)
2. Noisy Neighbor Cache Attack (PF5)
3. Fabric Deadlock Risk (PF6)
4. Memory Fragmentation (PF7)

We compare the 'Isolated' architecture (independent reflexes) against the
'Unified Cortex' architecture (coordinated via PF8 Telemetry Bus).

Key Acceptance Criteria:
- Unified system achieves ≥1.5x throughput improvement vs isolated
- Unified system achieves 10x reduction in victim p99 latency

Author: Portfolio B Research Team
License: Proprietary - Patent Pending (PF8)
"""

import sys
import os
import numpy as np
import pandas as pd
import simpy
from typing import Dict, List, Tuple

# Add subdirectories to path
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)
sys.path.insert(0, os.path.join(root, "_01_Incast_Backpressure"))
sys.path.insert(0, os.path.join(root, "_02_Deadlock_Release_Valve"))
sys.path.insert(0, os.path.join(root, "_03_Noisy_Neighbor_Sniper"))
sys.path.insert(0, os.path.join(root, "_04_Stranded_Memory_Borrowing"))

from shared.physics_engine import Physics
from _01_Incast_Backpressure.simulation import IncastConfig, run_incast_simulation
from _02_Deadlock_Release_Valve.simulation import DeadlockConfig, run_deadlock_simulation
from _03_Noisy_Neighbor_Sniper.simulation import NoisyNeighborConfig, run_noisy_neighbor_simulation
from _04_Stranded_Memory_Borrowing.simulation import StrandedMemoryConfig, run_stranded_memory_simulation

from _08_Grand_Unified_Cortex.telemetry_bus import EventBroker, DistributedStateStore, TelemetryPublisher
from _08_Grand_Unified_Cortex.coordination_matrix import CoordinationMatrix


def run_perfect_storm(mode: str = 'unified', seed: int = 42) -> Dict[str, float]:
    """
    Run the Perfect Storm simulation with SOVEREIGN BRAIN refactor.
    """
    env = simpy.Environment()
    duration = 100_000.0 # 100μs (reduced for performance)
    
    # Initialize PF8 Infrastructure
    broker = EventBroker(env)
    state_store = DistributedStateStore(env, broker)
    matrix = CoordinationMatrix(state_store)
    
    # Create Publishers
    pf4_pub = TelemetryPublisher(env, broker, "PF4_Incast")
    pf5_pub = TelemetryPublisher(env, broker, "PF5_Sniper")
    pf6_pub = TelemetryPublisher(env, broker, "PF6_Deadlock")
    pf7_pub = TelemetryPublisher(env, broker, "PF7_Memory")
    
    # Configurations (Physics-Correct Keyword Args)
    pf4_config = IncastConfig(
        buffer_capacity_bytes=Physics.NIC_BUFFER_BYTES,
        network_rate_gbps=600.0,
        memory_rate_gbps=512.0,
        simulation_duration_ns=duration,
        traffic_pattern='incast',
        n_senders=100
    )
    pf5_config = NoisyNeighborConfig(
        n_tenants=5,
        n_cache_slots=4096,
        simulation_duration_ns=duration,
        hit_latency_ns=Physics.L3_HIT_NS,
        miss_latency_ns=Physics.CXL_FABRIC_1HOP_NS,
        queue_capacity=1000,
        base_request_rate=0.005,
        noisy_tenant_multiplier=20.0,
        noisy_tenant_id=0,
        good_tenant_locality=1.0,
        noisy_tenant_locality=0.0
    )
    pf6_config = DeadlockConfig(
        n_switches=3,
        buffer_capacity_packets=100,
        link_rate_gbps=100.0,
        packet_size_bytes=1500,
        simulation_duration_ns=duration,
        injection_rate=0.9,
        ttl_timeout_ns=50000.0,
        adaptive_ttl_base_ns=25000.0,
        adaptive_ttl_multiplier=2.0,
        congestion_only_mode=False,
        virtual_lanes_enabled=False,
        coordination_mode=False,
        deadlock_injection_time_ns=20000.0,
        deadlock_duration_ns=50000.0
    )
    pf7_config = StrandedMemoryConfig(
        n_nodes=8,
        memory_per_node_gb=128.0,
        n_jobs=20,
        min_job_memory_gb=32.0,
        max_job_memory_gb=96.0,
        job_duration_ns=10000.0,
        simulation_duration_ns=duration,
        fragmentation_level=0.4,
        local_latency_ns=Physics.CXL_LOCAL_NS,
        remote_latency_ns=Physics.CXL_FABRIC_1HOP_NS,
        job_arrival_rate=0.0002
    )

    # Selection of algorithms based on mode
    if mode == 'unified':
        pf4_algo, pf5_algo, pf6_algo, pf7_algo = 'cache_aware', 'sniper', 'adaptive_ttl', 'balanced_borrow'
        matrix_arg, pub4, pub5, pub6, pub7 = matrix, pf4_pub, pf5_pub, pf6_pub, pf7_pub
    else:
        # Isolated System (FAIR COMPARISON - Same load as Unified)
        pf4_algo, pf5_algo, pf6_algo, pf7_algo = 'no_control', 'no_control', 'no_timeout', 'local_only'
        matrix_arg, pub4, pub5, pub6, pub7 = None, None, None, None, None
        
        # FAIR COMPARISON: Both systems face IDENTICAL conditions
        # (Removed artificial handicap - both systems get same load)

    # Start all simulations SIMULTANEOUSLY in the same environment
    buffer = run_incast_simulation(pf4_config, pf4_algo, seed, pub4, state_store, matrix_arg, env)
    cache_objs = run_noisy_neighbor_simulation(pf5_config, pf5_algo, seed, pub5, matrix_arg, env)
    network = run_deadlock_simulation(pf6_config, pf6_algo, seed, pub6, matrix_arg, env)
    cluster_objs = run_stranded_memory_simulation(pf7_config, pf7_algo, seed, pub7, matrix_arg, env)
    
    # Run the unified brain
    env.run(until=duration)
    
    # Collect metrics from handles
    from _01_Incast_Backpressure.simulation import _collect_incast_metrics
    res4 = _collect_incast_metrics(pf4_config, buffer)
    
    from _03_Noisy_Neighbor_Sniper.simulation import compute_metrics as cm_pf5
    res5 = cm_pf5(pf5_config, cache_objs[0], cache_objs[1], cache_objs[2])
    
    from _02_Deadlock_Release_Valve.simulation import _collect_deadlock_metrics
    res6 = _collect_deadlock_metrics(pf6_config, network)
    
    from _04_Stranded_Memory_Borrowing.simulation import compute_metrics as cm_pf7
    res7 = cm_pf7(pf7_config, cluster_objs[0], cluster_objs[1])
    
    # Debug: Print component scores
    if False: # Set to True for debugging
        print(f"DEBUG [{mode}]:")
        print(f"  s4 (Incast): {res4['throughput_fraction']:.3f} * (1 - {res4['drop_rate']:.3f})")
        print(f"  s5 (Cache): {res5['total_throughput']:.0f} / {duration:.0f}")
        print(f"  s6 (Deadlock): occurred={res6['deadlock_occurred']}, recovery={res6['recovery_time_ns']:.0f}")
        print(f"  s7 (Memory): {res7['completion_rate']:.2%}")
    
    # Unified Performance Score (Physics-Correct Normalization)
    # 1. Incast Efficiency: Delivered throughput after accounting for drops
    s4 = res4['throughput_fraction'] * (1.0 - res4['drop_rate'])
    
    # 2. Cache Throughput: Normalize by simulation duration, not expected requests
    #    This avoids the normalization bug where changing base_request_rate breaks comparison
    s5 = res5['total_throughput'] / duration if duration > 0 else 0
    
    # 3. Deadlock Avoidance: Did we avoid/recover from deadlock?
    if res6['deadlock_occurred'] == 0:
        s6 = 1.0 # Perfect
    elif res6['recovery_time_ns'] > 0:
        s6 = max(0, 1.0 - res6['recovery_time_ns'] / 100_000.0) # Penalize slow recovery
    else:
        s6 = 0.0 # Never recovered
    
    # 4. Memory Completion Efficiency
    s7 = res7['completion_rate']
    
    # Weighted aggregate (emphasize safety-critical metrics)
    total_throughput = (s4 * 0.3 + s5 * 0.2 + s6 * 0.2 + s7 * 0.3)
    
    return {
        'throughput_alpha': total_throughput,
        'victim_latency_ns': res5['good_p99_latency_ns'],
        'drop_rate': res4['drop_rate'],
        'recovery_time_ns': res6['recovery_time_ns'],
        'job_completion': res7['completion_rate']
    }


def main():
    print("="*60)
    print("PF8: THE PERFECT STORM TOURNAMENT")
    print("="*60)
    
    print("\nRunning Isolated Reflexes (Baseline)...")
    iso = run_perfect_storm(mode='isolated', seed=42)
    
    print("\nRunning Unified Cortex (Sovereign Architecture)...")
    uni = run_perfect_storm(mode='unified', seed=42)
    
    print("\n" + "-"*60)
    print(f"{'Metric':<20} | {'Isolated':<12} | {'Unified':<12} | {'Improvement'}")
    print("-"*60)
    
    t_gain = uni['throughput_alpha'] / iso['throughput_alpha']
    print(f"{'Throughput Score':<20} | {iso['throughput_alpha']:<12.3f} | {uni['throughput_alpha']:<12.3f} | {t_gain:.2f}x")
    
    l_gain = iso['victim_latency_ns'] / max(1, uni['victim_latency_ns'])
    print(f"{'Victim Latency':<20} | {iso['victim_latency_ns']:<12.1f} | {uni['victim_latency_ns']:<12.1f} | {l_gain:.1f}x")
    
    print(f"{'Drop Rate':<20} | {iso['drop_rate']:<12.4f} | {uni['drop_rate']:<12.4f} | {'DEFEATED' if uni['drop_rate']==0 else 'REDUCED'}")
    print(f"{'Job Completion':<20} | {iso['job_completion']:<12.2%} | {uni['job_completion']:<12.2%} | {uni['job_completion']/max(0.01, iso['job_completion']):.1f}x")
    
    print("\n" + "="*60)
    if t_gain >= 1.5 and l_gain >= 10:
        print("PF8 STATUS: BILLION DOLLAR STANDARD MET")
    else:
        print("PF8 STATUS: PERFORMANCE ALPHA PENDING")
    print("="*60)

if __name__ == "__main__":
    main()




