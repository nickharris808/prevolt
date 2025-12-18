"""
Noisy Neighbor Sniper Simulation
================================

This module simulates multi-tenant memory contention and isolation mechanisms.
The key innovation is the "Sniper" algorithm that identifies and throttles
only the noisy tenants, leaving well-behaved tenants unaffected.

Patent Claim Support:
"A multi-tenant memory isolation system comprising a per-flow request rate 
monitor and a selective throttling mechanism that applies bandwidth reduction 
exclusively to flows exceeding a statistical deviation threshold from the 
tenant population mean."

Author: Portfolio B Research Team
License: Proprietary - Patent Pending
"""

import simpy
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable
from enum import Enum
from queue import PriorityQueue
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cache_model import SharedCache, MemoryRequest, TenantStats, compute_jains_fairness


# =============================================================================
# SIMULATION PARAMETERS
# =============================================================================

@dataclass
class NoisyNeighborConfig:
    """
    Configuration for the noisy neighbor simulation.
    
    Attributes:
        n_tenants: Number of tenants in the system
        n_cache_slots: Number of cache slots
        simulation_duration_us: Simulation duration
        hit_latency_us: Cache hit latency
        miss_latency_us: Cache miss latency
        queue_capacity: Maximum pending requests
        base_request_rate: Base request rate (per tenant per us)
        noisy_tenant_multiplier: How much noisier the noisy tenant is
        noisy_tenant_id: Which tenant is noisy (-1 for random)
        good_tenant_locality: Locality factor for good tenants (0-1)
        noisy_tenant_locality: Locality factor for noisy tenant
        throttle_factor: How much to throttle identified noisy tenants
        fair_share_reduction: Reduction applied to all in fair share mode
        vip_tenant_id: Which tenant gets VIP treatment
    """
    n_tenants: int = 5
    n_cache_slots: int = 1024
    simulation_duration_us: float = 20000.0  # 20ms for better stability
    
    # Latency parameters
    hit_latency_us: float = 1.0
    miss_latency_us: float = 200.0  # Higher miss penalty to emphasize SNR
    queue_capacity: int = 1000
    
    # Request rate parameters
    base_request_rate: float = 0.02  # higher base load
    noisy_tenant_multiplier: float = 15.0  # Noisy is much noisier
    noisy_tenant_id: int = 0  # First tenant is noisy
    
    # Access pattern parameters
    good_tenant_locality: float = 0.8  # 80% locality
    noisy_tenant_locality: float = 0.1  # 10% locality (random access)
    
    # Throttling parameters
    throttle_factor: float = 0.2  # Throttle to 20% of rate
    fair_share_reduction: float = 0.2  # Reduce everyone by 20%
    vip_tenant_id: int = 1  # Second tenant is VIP


# =============================================================================
# TENANT BEHAVIOR PROFILES
# =============================================================================

class TenantBehavior(Enum):
    """Types of tenant behavior."""
    GOOD = 'good'       # Normal rate, high locality
    NOISY = 'noisy'     # High rate, low locality
    BURSTY = 'bursty'   # Periodic bursts


@dataclass
class TenantProfile:
    """
    Profile defining a tenant's behavior.
    
    Attributes:
        tenant_id: Unique identifier
        behavior: Type of behavior
        request_rate: Requests per microsecond
        locality: Probability of accessing recent data
        working_set_size: Number of unique keys in working set
        burst_probability: Probability of entering burst mode
        burst_multiplier: Rate multiplier during burst
    """
    tenant_id: int
    behavior: TenantBehavior
    request_rate: float
    locality: float
    working_set_size: int = 100
    burst_probability: float = 0.0
    burst_multiplier: float = 1.0


def create_tenant_profiles(config: NoisyNeighborConfig) -> List[TenantProfile]:
    """Create tenant profiles based on configuration."""
    profiles = []
    
    for i in range(config.n_tenants):
        if i == config.noisy_tenant_id:
            # Noisy tenant: high rate, low locality
            profile = TenantProfile(
                tenant_id=i,
                behavior=TenantBehavior.NOISY,
                request_rate=config.base_request_rate * config.noisy_tenant_multiplier,
                locality=config.noisy_tenant_locality,
                working_set_size=config.n_cache_slots * 10 # Thrash the cache
            )
        else:
            # Good tenant: normal rate, high locality
            profile = TenantProfile(
                tenant_id=i,
                behavior=TenantBehavior.GOOD,
                request_rate=config.base_request_rate,
                locality=config.good_tenant_locality,
                working_set_size=20 # Small working set fits in cache
            )
        
        profiles.append(profile)
    
    return profiles


# =============================================================================
# THROTTLING ALGORITHMS
# =============================================================================

class ThrottlingAlgorithm:
    """Base class for throttling algorithms."""
    
    def __init__(self, config: NoisyNeighborConfig, cache: SharedCache):
        self.config = config
        self.cache = cache
    
    def should_admit(self, tenant_id: int, current_time: float) -> bool:
        """Return True if request should be admitted."""
        raise NotImplementedError
    
    def get_delay(self, tenant_id: int) -> float:
        """Return additional delay to apply."""
        return 0.0


class NoControlAlgorithm(ThrottlingAlgorithm):
    """
    Baseline: No throttling control.
    
    All requests are admitted immediately. The noisy tenant
    dominates the cache and degrades everyone's performance.
    """
    
    def should_admit(self, tenant_id: int, current_time: float) -> bool:
        return True


class FairShareAlgorithm(ThrottlingAlgorithm):
    """
    Fair Share: Throttle everyone equally.
    
    When congestion is detected (based on aggregate miss rate), 
    all tenants are throttled by the same factor.
    """
    
    def should_admit(self, tenant_id: int, current_time: float) -> bool:
        # Check aggregate cache miss rate
        mean_miss, _ = self.cache.flow_tracker.get_population_stats()
        if mean_miss > 0.5: # 50% aggregate miss rate
            # Probabilistically drop for EVERYONE
            return np.random.random() > 0.4 # 40% drop for all
        return True


class VIPAlgorithm(ThrottlingAlgorithm):
    """
    VIP Priority: Prioritize designated VIP tenant.
    
    The VIP tenant always gets full access. Others are throttled
    when the VIP needs resources. Simple but can starve others.
    """
    
    def should_admit(self, tenant_id: int, current_time: float) -> bool:
        if tenant_id == self.config.vip_tenant_id:
            return True  # VIP always admitted
        
        # Check VIP's queue depth
        vip_stats = self.cache.tenant_stats.get(self.config.vip_tenant_id)
        if vip_stats and self.cache.get_utilization() > 0.8:
            # Throttle non-VIP by 50%
            return np.random.random() > 0.5
        
        return True


class SniperAlgorithm(ThrottlingAlgorithm):
    """
    Sniper: Identify and throttle only the noisy tenant (THE INVENTION).
    
    Uses the flow tracker to detect statistical outliers in CACHE MISS RATES
    and applies throttling only to those tenants. Good tenants are unaffected.
    
    This is the patentable innovation.
    """
    
    def __init__(self, config: NoisyNeighborConfig, cache: SharedCache):
        super().__init__(config, cache)
        self.throttle_state: Dict[int, float] = {}  # tenant -> throttle until time
    
    def should_admit(self, tenant_id: int, current_time: float) -> bool:
        # Check if tenant is in throttle state
        if tenant_id in self.throttle_state:
            if current_time < self.throttle_state[tenant_id]:
                # Still throttled - strict drop for noisy neighbor
                return np.random.random() > 0.9  # 90% drop rate for sniper
            else:
                # Throttle period expired - check again
                del self.throttle_state[tenant_id]
        
        # Check if this tenant has an outlier cache miss rate
        if self.cache.flow_tracker.is_noisy_neighbor(tenant_id, threshold_std=1.5):
            # Apply throttle for next 200us
            self.throttle_state[tenant_id] = current_time + 200.0
            return False # Drop first packet to trigger fast reaction
        
        return True
    
    def get_delay(self, tenant_id: int) -> float:
        return 0.0


# =============================================================================
# SIMULATION STATE
# =============================================================================

@dataclass
class SimulationState:
    """
    Tracks overall simulation state.
    
    Attributes:
        current_time: Current simulation time
        total_requests: Total requests submitted
        admitted_requests: Requests admitted
        throttled_requests: Requests throttled
        completed_requests: Requests completed
        per_tenant_latencies: Dict of tenant_id -> list of latencies
    """
    current_time: float = 0.0
    total_requests: int = 0
    admitted_requests: int = 0
    throttled_requests: int = 0
    completed_requests: int = 0
    per_tenant_latencies: Dict[int, List[float]] = field(default_factory=dict)
    per_tenant_throughputs: Dict[int, int] = field(default_factory=dict)
    
    def record_latency(self, tenant_id: int, latency: float):
        if tenant_id not in self.per_tenant_latencies:
            self.per_tenant_latencies[tenant_id] = []
        self.per_tenant_latencies[tenant_id].append(latency)
    
    def record_completion(self, tenant_id: int):
        self.per_tenant_throughputs[tenant_id] = \
            self.per_tenant_throughputs.get(tenant_id, 0) + 1


# =============================================================================
# SIMULATION RUNNER
# =============================================================================

def run_noisy_neighbor_simulation(
    config: NoisyNeighborConfig,
    algorithm_type: str,
    seed: int
) -> Dict[str, float]:
    """
    Run a single noisy neighbor simulation.
    
    Args:
        config: Simulation configuration
        algorithm_type: 'no_control', 'fair_share', 'vip', or 'sniper'
        seed: Random seed
        
    Returns:
        Dictionary of metrics
    """
    rng = np.random.default_rng(seed)
    
    # Create cache
    cache = SharedCache(
        n_slots=config.n_cache_slots,
        hit_latency_us=config.hit_latency_us,
        miss_latency_us=config.miss_latency_us
    )
    
    # Create throttling algorithm
    if algorithm_type == 'no_control':
        throttler = NoControlAlgorithm(config, cache)
    elif algorithm_type == 'fair_share':
        throttler = FairShareAlgorithm(config, cache)
    elif algorithm_type == 'vip':
        throttler = VIPAlgorithm(config, cache)
    elif algorithm_type == 'sniper':
        throttler = SniperAlgorithm(config, cache)
    else:
        raise ValueError(f"Unknown algorithm: {algorithm_type}")
    
    # Create tenant profiles
    profiles = create_tenant_profiles(config)
    
    # Simulation state
    state = SimulationState()
    
    # Per-tenant state
    last_keys: Dict[int, int] = {p.tenant_id: 0 for p in profiles}  # For locality
    
    # Main simulation loop
    current_time = 0.0
    
    while current_time < config.simulation_duration_us:
        # Generate requests from each tenant
        for profile in profiles:
            # Determine if this tenant makes a request this timestep
            # Using Poisson process approximation
            if rng.random() < profile.request_rate:
                state.total_requests += 1
                
                # Determine data key based on locality
                if rng.random() < profile.locality:
                    # Access within working set (locality)
                    key = last_keys[profile.tenant_id]
                    key = (key + rng.integers(0, 5)) % profile.working_set_size
                else:
                    # Random access
                    key = rng.integers(0, 10000)
                
                last_keys[profile.tenant_id] = key
                
                # Check if request is admitted
                if throttler.should_admit(profile.tenant_id, current_time):
                    state.admitted_requests += 1
                    
                    # Access cache
                    was_hit, base_latency = cache.access(
                        profile.tenant_id, key, current_time
                    )
                    
                    # Add throttling delay
                    extra_delay = throttler.get_delay(profile.tenant_id)
                    total_latency = base_latency + extra_delay
                    
                    # Record completion
                    state.record_latency(profile.tenant_id, total_latency)
                    state.record_completion(profile.tenant_id)
                    state.completed_requests += 1
                else:
                    state.throttled_requests += 1
        
        # Advance time
        current_time += 1.0  # 1us timestep
    
    state.current_time = current_time
    
    # Compute metrics
    metrics = compute_metrics(config, cache, state, profiles)
    
    return metrics


def compute_metrics(
    config: NoisyNeighborConfig,
    cache: SharedCache,
    state: SimulationState,
    profiles: List[TenantProfile]
) -> Dict[str, float]:
    """Compute all output metrics."""
    
    # Overall metrics
    admission_rate = state.admitted_requests / max(1, state.total_requests)
    
    # Per-tenant metrics
    good_tenant_latencies = []
    noisy_tenant_latencies = []
    all_throughputs = []
    
    for profile in profiles:
        tid = profile.tenant_id
        latencies = state.per_tenant_latencies.get(tid, [0.0])
        throughput = state.per_tenant_throughputs.get(tid, 0)
        
        if profile.behavior == TenantBehavior.NOISY:
            noisy_tenant_latencies.extend(latencies)
        else:
            good_tenant_latencies.extend(latencies)
        
        all_throughputs.append(throughput)
    
    # Latency statistics
    if len(good_tenant_latencies) > 0:
        good_avg_latency = float(np.mean(good_tenant_latencies))
        good_p99_latency = float(np.percentile(good_tenant_latencies, 99))
        good_p50_latency = float(np.percentile(good_tenant_latencies, 50))
    else:
        good_avg_latency = 0.0
        good_p99_latency = 0.0
        good_p50_latency = 0.0
    
    if len(noisy_tenant_latencies) > 0:
        noisy_avg_latency = float(np.mean(noisy_tenant_latencies))
        noisy_p99_latency = float(np.percentile(noisy_tenant_latencies, 99))
    else:
        noisy_avg_latency = 0.0
        noisy_p99_latency = 0.0
    
    # Fairness
    fairness_score = compute_jains_fairness(all_throughputs)
    
    # Total throughput
    total_throughput = sum(all_throughputs)
    
    # Noisy tenant's share (should be low if isolation works)
    noisy_throughput = state.per_tenant_throughputs.get(config.noisy_tenant_id, 0)
    noisy_share = noisy_throughput / max(1, total_throughput)
    
    # Good tenants' combined throughput
    good_throughput = total_throughput - noisy_throughput
    
    return {
        'admission_rate': admission_rate,
        'good_avg_latency_us': good_avg_latency,
        'good_p99_latency_us': good_p99_latency,
        'good_p50_latency_us': good_p50_latency,
        'noisy_avg_latency_us': noisy_avg_latency,
        'noisy_p99_latency_us': noisy_p99_latency,
        'fairness_score': fairness_score,
        'total_throughput': float(total_throughput),
        'noisy_share': noisy_share,
        'good_throughput': float(good_throughput),
        'noisy_throughput': float(noisy_throughput),
        'throttled_requests': float(state.throttled_requests),
        'cache_utilization': cache.get_utilization()
    }


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == '__main__':
    print("Testing Noisy Neighbor Simulation...")
    print("-" * 50)
    
    config = NoisyNeighborConfig(
        n_tenants=5,
        simulation_duration_us=5000.0,
        noisy_tenant_multiplier=10.0
    )
    
    for algo in ['no_control', 'fair_share', 'vip', 'sniper']:
        results = run_noisy_neighbor_simulation(config, algo, seed=42)
        print(f"\n{algo.upper()}:")
        print(f"  Good Tenant p99 Latency: {results['good_p99_latency_us']:.2f} μs")
        print(f"  Fairness Score: {results['fairness_score']:.3f}")
        print(f"  Good Throughput: {results['good_throughput']:.0f}")
        print(f"  Noisy Share: {results['noisy_share']:.2%}")
    
    print("\n" + "=" * 50)
    print("Noisy neighbor simulation test complete!")

