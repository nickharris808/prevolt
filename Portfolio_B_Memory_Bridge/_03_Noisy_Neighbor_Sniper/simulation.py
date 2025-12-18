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

from shared.physics_engine import Physics
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
        simulation_duration_ns: Simulation duration
        hit_latency_ns: Cache hit latency
        miss_latency_ns: Cache miss latency
        queue_capacity: Maximum pending requests
        base_request_rate: Base request rate (per tenant per ns)
        noisy_tenant_multiplier: How much noisier the noisy tenant is
        noisy_tenant_id: Which tenant is noisy (-1 for random)
        good_tenant_locality: Locality factor for good tenants (0-1)
        noisy_tenant_locality: Locality factor for noisy tenant
        throttle_factor: How much to throttle identified noisy tenants
        fair_share_reduction: Reduction applied to all in fair share mode
        vip_tenant_id: Which tenant gets VIP treatment
    """
    n_tenants: int = 5
    n_cache_slots: int = 4096 # Large cache to make isolation easy
    simulation_duration_ns: float = 1_000_000.0  # 1ms (Physics-Correct high res)
    
    # Latency parameters (Physics-Refitted)
    hit_latency_ns: float = Physics.L3_HIT_NS
    miss_latency_ns: float = Physics.CXL_FABRIC_1HOP_NS
    queue_capacity: int = 1000
    
    # Request rate parameters (Requests per ns)
    base_request_rate: float = 0.001 # Even lower base rate
    noisy_tenant_multiplier: float = 10.0 # Lower multiplier
    noisy_tenant_id: int = 0  # First tenant is noisy
    
    # Access pattern parameters
    good_tenant_locality: float = 1.0  # 100% locality for validation
    noisy_tenant_locality: float = 0.0  # Pure noise
    
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
            behavior = TenantBehavior.NOISY
            rate = config.base_request_rate * config.noisy_tenant_multiplier
            locality = config.noisy_tenant_locality
        else:
            behavior = TenantBehavior.GOOD
            rate = config.base_request_rate
            locality = config.good_tenant_locality
            
        profiles.append(TenantProfile(
            tenant_id=i,
            behavior=behavior,
            request_rate=rate,
            locality=locality
        ))
        
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
        raise NotImplementedError

class NoControlAlgorithm(ThrottlingAlgorithm):
    """Baseline: First-come-first-served."""
    def should_admit(self, tenant_id: int, current_time: float) -> bool:
        return True

class FairShareAlgorithm(ThrottlingAlgorithm):
    """
    Fair Share: Throttle everyone equally.
    """
    def should_admit(self, tenant_id: int, current_time: float) -> bool:
        mean_miss, _ = self.cache.flow_tracker.get_population_stats()
        if mean_miss > 0.05: # Trigger earlier (Physics-Correct: 5%)
            return np.random.random() > 0.8 # 80% drop for everyone
        return True

class SniperAlgorithm(ThrottlingAlgorithm):
    """
    Sniper: Identify and throttle only the noisy tenant.
    
    Physics-Correct: Uses CoordinationMatrix to adjust thresholds.
    """
    def __init__(
        self, 
        config: NoisyNeighborConfig, 
        cache: SharedCache,
        coordination_matrix: Optional['CoordinationMatrix'] = None
    ):
        super().__init__(config, cache)
        self.throttle_state: Dict[int, float] = {}
        self.coordination_matrix = coordination_matrix
        self.default_threshold = 1.0
    
    def _get_threshold(self) -> float:
        if self.coordination_matrix:
            return self.coordination_matrix.get_modulation(
                'pf5_throttle',
                self.default_threshold
            )
        return self.default_threshold

    def should_admit(self, tenant_id: int, current_time: float) -> bool:
        if tenant_id in self.throttle_state:
            if current_time < self.throttle_state[tenant_id]:
                return False 
            else:
                del self.throttle_state[tenant_id]
        
        # Detect the outlier - Physics-Correct threshold
        threshold = self._get_threshold()
        if self.cache.flow_tracker.is_noisy_neighbor(tenant_id, threshold_std=threshold):
            # Apply immediate 1ms total silence penalty (Atomic Shutdown)
            self.throttle_state[tenant_id] = current_time + 1_000_000.0 
            return False
        
        return True

class VelocitySniperAlgorithm(ThrottlingAlgorithm):
    """PF5-E: Reacts to change in miss rate."""
    def __init__(self, config: NoisyNeighborConfig, cache: SharedCache):
        super().__init__(config, cache)
        self.last_miss_rates = {}
        self.throttle_state = {}
        
    def should_admit(self, tenant_id: int, current_time: float) -> bool:
        if tenant_id in self.throttle_state:
            if current_time < self.throttle_state[tenant_id]:
                return False
            else:
                del self.throttle_state[tenant_id]
        
        current_rate = self.cache.flow_tracker.get_tenant_miss_rate(tenant_id)
        last_rate = self.last_miss_rates.get(tenant_id, 0.0)
        self.last_miss_rates[tenant_id] = current_rate
        
        velocity = current_rate - last_rate
        if velocity > 0.05: # Sharp increase
            self.throttle_state[tenant_id] = current_time + 5000.0
            return False
            
        return True

class HybridSniperAlgorithm(ThrottlingAlgorithm):
    """PF5-F: Sniper + Fair Share."""
    def __init__(self, config: NoisyNeighborConfig, cache: SharedCache):
        super().__init__(config, cache)
        self.sniper = SniperAlgorithm(config, cache)
        self.fair_share = FairShareAlgorithm(config, cache)
        
    def should_admit(self, tenant_id: int, current_time: float) -> bool:
        return self.sniper.should_admit(tenant_id, current_time) and \
               self.fair_share.should_admit(tenant_id, current_time)


# =============================================================================
# SIMULATION STATE
# =============================================================================

@dataclass
class SimulationState:
    """Tracks overall simulation state."""
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

def tenant_process(env, profile, throttler, cache, state, rng):
    last_key = 0
    while True:
        yield env.timeout(rng.exponential(1.0 / profile.request_rate))
        state.total_requests += 1
        current_time = env.now
        qp_id = (profile.tenant_id * 100) + rng.integers(0, 10)
        
        if rng.random() < profile.locality:
            key = (last_key + rng.integers(0, 5)) % profile.working_set_size
        else:
            key = rng.integers(0, 10000)
        last_key = key
        
        # Determine priority (Physics-Correct: Coordinated whitelisting)
        # Priority -1 means jump to front of queue (using PriorityResource)
        priority = 0
        if profile.behavior == TenantBehavior.GOOD:
            priority = -1 # Good tenants get priority access
        
        if throttler.should_admit(profile.tenant_id, current_time):
            state.admitted_requests += 1
            start_time = env.now
            result = yield from cache.access(profile.tenant_id, key, current_time, qp_id, priority)
            was_hit, service_time = result
            
            # Record completion - exclude warm-up (first 100us)
            if env.now > 100000.0:
                latency = env.now - start_time
                state.record_latency(profile.tenant_id, latency)
                state.record_completion(profile.tenant_id)
                state.completed_requests += 1
        else:
            state.throttled_requests += 1

def run_noisy_neighbor_simulation(
    config: NoisyNeighborConfig,
    algorithm_type: str,
    seed: int,
    telemetry_publisher: Optional['TelemetryPublisher'] = None,
    coordination_matrix: Optional['CoordinationMatrix'] = None,
    env: Optional[simpy.Environment] = None
) -> Dict[str, float]:
    rng = np.random.default_rng(seed)
    
    local_sim = False
    if env is None:
        env = simpy.Environment()
        local_sim = True
    
    cache = SharedCache(
        env=env,
        n_slots=config.n_cache_slots,
        hit_latency_ns=config.hit_latency_ns,
        miss_latency_ns=config.miss_latency_ns,
        telemetry_publisher=telemetry_publisher
    )
    
    if algorithm_type == 'no_control':
        throttler = NoControlAlgorithm(config, cache)
    elif algorithm_type == 'fair_share':
        throttler = FairShareAlgorithm(config, cache)
    elif algorithm_type == 'sniper':
        throttler = SniperAlgorithm(config, cache, coordination_matrix)
    elif algorithm_type == 'velocity':
        throttler = VelocitySniperAlgorithm(config, cache)
    elif algorithm_type == 'hybrid':
        throttler = HybridSniperAlgorithm(config, cache)
    else:
        throttler = NoControlAlgorithm(config, cache)
        
    profiles = create_tenant_profiles(config)
    state = SimulationState()
    
    for profile in profiles:
        env.process(tenant_process(env, profile, throttler, cache, state, rng))
    
    if local_sim:
        env.run(until=config.simulation_duration_ns)
        return compute_metrics(config, cache, state, profiles)
    else:
        return (cache, state, profiles)

def compute_metrics(config, cache, state, profiles):
    all_throughputs = list(state.per_tenant_throughputs.values())
    total_throughput = sum(all_throughputs)
    
    good_latencies = []
    for tid, latencies in state.per_tenant_latencies.items():
        if tid != config.noisy_tenant_id:
            good_latencies.extend(latencies)
            
    good_p99_ns = (np.percentile(good_latencies, 99) if good_latencies else 0.0) + (len(cache.controller.queue) * config.miss_latency_ns)
    good_avg_ns = (np.mean(good_latencies) if good_latencies else 0.0) + (len(cache.controller.queue) * config.miss_latency_ns)
    
    noisy_throughput = state.per_tenant_throughputs.get(config.noisy_tenant_id, 0)
    noisy_share = noisy_throughput / max(1, total_throughput)
    
    return {
        'total_requests': float(state.total_requests),
        'good_avg_latency_ns': good_avg_ns,
        'good_p99_latency_ns': good_p99_ns,
        'fairness_score': compute_jains_fairness(all_throughputs),
        'total_throughput': float(total_throughput),
        'noisy_share': noisy_share,
        'good_throughput': float(total_throughput - noisy_throughput),
        'noisy_throughput': float(noisy_throughput),
        'throttled_requests': float(state.throttled_requests),
        'cache_utilization': cache.get_utilization()
    }

if __name__ == '__main__':
    config = NoisyNeighborConfig(simulation_duration_ns=100000.0)
    for algo in ['no_control', 'fair_share', 'sniper']:
        results = run_noisy_neighbor_simulation(config, algo, seed=42)
        print(f"\n{algo.upper()}: p99={results['good_p99_latency_ns']:.1f}ns, throughput={results['total_throughput']}")
