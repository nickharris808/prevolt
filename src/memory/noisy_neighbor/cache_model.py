"""
Cache Model for Noisy Neighbor Simulation
==========================================

This module provides a detailed cache model with:
- Per-tenant flow tracking
- Request rate monitoring
- Eviction policies
- Fairness measurement

The cache model captures the key dynamics of shared memory bandwidth
contention in multi-tenant CXL/UEC environments.

Author: Portfolio B Research Team
License: Proprietary - Patent Pending
"""

import simpy
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from collections import deque
from enum import Enum
import heapq
import sys
import os

# Add parent directory and shared_physics to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'shared_physics'))

try:
    from physics_engine import Physics
except ImportError:
    # Fallback for standalone testing
    class Physics:
        TIMING = type('obj', (object,), {'CXL_SIDEBAND_SIGNAL': 120.0})()
        BUFFER = type('obj', (object,), {'HBM_CAPACITY_GB': 16})()
        THRESHOLDS = type('obj', (object,), {'BUFFER_HWM': 0.8, 'BUFFER_LWM': 0.2})()
        ARBITRATION = type('obj', (object,), {'VICTIM_QUOTA_PCT': 0.5})()

# PF8: Telemetry Bus Integration (Optional)
try:
    from _08_Grand_Unified_Cortex import (
        TelemetryPublisher,
        MetricType
    )
    PF8_AVAILABLE = True
except ImportError:
    PF8_AVAILABLE = False
    TelemetryPublisher = None
    MetricType = None


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class CacheSlot:
    """
    Represents a single slot in the shared cache.
    
    Attributes:
        slot_id: Unique slot identifier
        tenant_id: Current owner (-1 if empty)
        data_key: Key of cached data
        last_access_time: Time of last access
        access_count: Number of accesses
        eviction_priority: Priority for eviction (lower = evict first)
    """
    slot_id: int
    tenant_id: int = -1
    data_key: int = -1
    last_access_time: float = 0.0
    access_count: int = 0
    eviction_priority: float = 0.0
    
    def is_empty(self) -> bool:
        return self.tenant_id == -1


@dataclass
class MemoryRequest:
    """
    Represents a memory access request.
    
    Attributes:
        request_id: Unique request identifier
        tenant_id: Requesting tenant
        data_key: Key of data being accessed
        arrival_time: When request arrived
        completion_time: When request completed (None if pending)
        was_hit: Whether request was a cache hit
        queue_wait_time: Time spent waiting in queue
    """
    request_id: int
    tenant_id: int
    data_key: int
    arrival_time: float
    completion_time: Optional[float] = None
    was_hit: bool = False
    queue_wait_time: float = 0.0
    
    @property
    def latency(self) -> float:
        """Total latency from arrival to completion."""
        if self.completion_time is None:
            return float('inf')
        return self.completion_time - self.arrival_time


@dataclass
class TenantStats:
    """
    Statistics for a single tenant.
    
    Attributes:
        tenant_id: Tenant identifier
        requests_submitted: Total requests submitted
        requests_completed: Requests completed
        requests_throttled: Requests throttled/delayed
        total_latency: Sum of all latencies
        latencies: List of individual latencies
        cache_hits: Number of cache hits
        cache_misses: Number of cache misses
    """
    tenant_id: int
    requests_submitted: int = 0
    requests_completed: int = 0
    requests_throttled: int = 0
    total_latency: float = 0.0
    latencies: List[float] = field(default_factory=list)
    cache_hits: int = 0
    cache_misses: int = 0
    
    @property
    def avg_latency_ns(self) -> float:
        if self.requests_completed == 0:
            return 0.0
        return self.total_latency / self.requests_completed
    
    @property
    def p99_latency_ns(self) -> float:
        if len(self.latencies) == 0:
            return 0.0
        return np.percentile(self.latencies, 99)
    
    @property
    def hit_rate(self) -> float:
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return self.cache_hits / total
    
    @property
    def throughput(self) -> float:
        """Requests completed per time unit."""
        return float(self.requests_completed)


# =============================================================================
# FLOW TRACKER
# =============================================================================

class FlowTracker:
    """
    Tracks per-tenant cache performance for outlier detection.
    
    This is the key component for the "Sniper" algorithm:
    - Monitors cache miss rates per tenant
    - Identifies tenants thrashing the shared cache
    - Provides throttling recommendations
    """
    
    def __init__(
        self,
        window_size_ns: float = 10_000.0,  # 10us window
        history_length: int = 100,
        telemetry_publisher: Optional['TelemetryPublisher'] = None
    ):
        """
        Initialize the flow tracker.
        """
        self.window_size_ns = window_size_ns
        self.history_length = history_length
        self.telemetry_publisher = telemetry_publisher
        
        # Per-tenant counts
        self.current_hits: Dict[int, int] = {}
        self.current_misses: Dict[int, int] = {}
        
        # Per-QP (flow) counts for aggregation testing
        self.current_qp_misses: Dict[int, int] = {}
        
        # Per-tenant miss rate history
        self.miss_rate_history: Dict[int, deque] = {}
        
        # Window timing
        self.window_start_time: float = 0.0
        self.current_time: float = 0.0
    
    def record_access(self, tenant_id: int, was_hit: bool, current_time: float, qp_id: int = 0):
        """
        Record a cache access.
        """
        self.current_time = current_time
        
        if current_time - self.window_start_time >= self.window_size_ns:
            self._roll_window()
        
        # PF5-C: Aggregated Sniper - track QP but group by Tenant ID
        if was_hit:
            self.current_hits[tenant_id] = self.current_hits.get(tenant_id, 0) + 1
        else:
            self.current_misses[tenant_id] = self.current_misses.get(tenant_id, 0) + 1
            self.current_qp_misses[qp_id] = self.current_qp_misses.get(qp_id, 0) + 1
    
    def _roll_window(self):
        """Roll to a new time window, saving current miss rates to history."""
        # Calculate miss rates for current window
        all_tenants = set(self.current_hits.keys()) | set(self.current_misses.keys())
        
        for tenant_id in all_tenants:
            hits = self.current_hits.get(tenant_id, 0)
            misses = self.current_misses.get(tenant_id, 0)
            total = hits + misses
            
            miss_rate = misses / total if total > 0 else 0.0
            
            if tenant_id not in self.miss_rate_history:
                self.miss_rate_history[tenant_id] = deque(maxlen=self.history_length)
            
            self.miss_rate_history[tenant_id].append(miss_rate)
        
        # Reset for new window
        self.current_hits = {}
        self.current_misses = {}
        self.current_qp_misses = {}
        self.window_start_time = self.current_time
        
        # PF8: Publish aggregate cache miss rate
        if self.telemetry_publisher and PF8_AVAILABLE:
            mean_rate, _ = self.get_population_stats()
            self.telemetry_publisher.publish(
                MetricType.CACHE_MISS_RATE,
                mean_rate
            )
    
    def get_tenant_miss_rate(self, tenant_id: int) -> float:
        """Get the smoothed miss rate for a tenant."""
        if tenant_id not in self.miss_rate_history:
            return 0.0
        
        history = self.miss_rate_history[tenant_id]
        if len(history) == 0:
            return 0.0
        
        return float(np.mean(list(history)))
    
    def get_population_stats(self) -> Tuple[float, float]:
        """Get mean and std of miss rates across all tenants."""
        rates = [self.get_tenant_miss_rate(t) for t in self.miss_rate_history.keys()]
        if len(rates) < 2:
            return 0.0, 1.0  # Avoid division by zero
        return float(np.mean(rates)), float(np.std(rates))
    
    def is_noisy_neighbor(
        self,
        tenant_id: int,
        threshold_std: float = 1.5
    ) -> bool:
        """
        Identify a noisy neighbor based on cache miss rate outlier.
        """
        tenant_rate = self.get_tenant_miss_rate(tenant_id)
        mean_rate, std_rate = self.get_population_stats()
        
        if std_rate == 0:
            return False
            
        z_score = (tenant_rate - mean_rate) / std_rate
        # A noisy neighbor thrashes the cache, meaning they have a high miss rate
        # AND they are likely a large fraction of the misses.
        return z_score > threshold_std
    
    def get_throttle_factor(
        self,
        tenant_id: int,
        base_factor: float = 0.5
    ) -> float:
        """
        Calculate throttle factor for a tenant.
        
        Args:
            tenant_id: Tenant to throttle
            base_factor: Base throttle multiplier
            
        Returns:
            Throttle factor (1.0 = no throttle, 0.0 = complete block)
        """
        if not self.is_noisy_neighbor(tenant_id):
            return 1.0
        
        tenant_rate = self.get_tenant_rate(tenant_id)
        mean_rate, std_rate = self.get_population_stats()
        
        if mean_rate == 0:
            return 1.0
        
        # Throttle proportionally to how much they exceed the mean
        excess = (tenant_rate - mean_rate) / mean_rate
        return max(base_factor, 1.0 / (1.0 + excess))


# =============================================================================
# SHARED CACHE MODEL
# =============================================================================

class SharedCache:
    """
    Model of a shared cache with multi-tenant access.
    
    Features:
    - Configurable number of slots
    - LRU eviction by default
    - Per-tenant slot allocation tracking
    - Flow tracking for noisy neighbor detection
    """
    
    def __init__(
        self,
        env: simpy.Environment,
        n_slots: int = 4096,
        hit_latency_ns: float = Physics.L3_HIT_NS,
        miss_latency_ns: float = Physics.CXL_FABRIC_1HOP_NS,
        telemetry_publisher: Optional['TelemetryPublisher'] = None
    ):
        """
        Initialize the cache.
        """
        self.env = env
        self.n_slots = n_slots
        self.hit_latency_ns = hit_latency_ns
        self.miss_latency_ns = miss_latency_ns
        self.telemetry_publisher = telemetry_publisher
        
        # Memory Controller as a Resource (Physics-Correct: PriorityResource)
        self.controller = simpy.PriorityResource(env, capacity=1)
        
        # Initialize slots
        self.slots: List[CacheSlot] = [
            CacheSlot(slot_id=i) for i in range(n_slots)
        ]
        
        # Key to slot mapping
        self.key_to_slot: Dict[Tuple[int, int], int] = {}  # (tenant, key) -> slot_id
        
        # LRU tracking (min-heap of (access_time, slot_id))
        self.lru_heap: List[Tuple[float, int]] = []
        
        # Flow tracker (Physics-correct window: 1us)
        self.flow_tracker = FlowTracker(
            window_size_ns=1 * Physics.US,
            telemetry_publisher=telemetry_publisher
        )
        
        # Per-tenant statistics
        self.tenant_stats: Dict[int, TenantStats] = {}
    
    def _get_or_create_stats(self, tenant_id: int) -> TenantStats:
        """Get or create statistics for a tenant."""
        if tenant_id not in self.tenant_stats:
            self.tenant_stats[tenant_id] = TenantStats(tenant_id=tenant_id)
        return self.tenant_stats[tenant_id]
    
    def access(
        self,
        tenant_id: int,
        data_key: int,
        current_time: float,
        qp_id: int = 0,
        priority: int = 0,
        rng: Optional[np.random.Generator] = None
    ):
        """
        Access data in the cache with stochastic latency.
        """
        stats = self._get_or_create_stats(tenant_id)
        stats.requests_submitted += 1
        
        # Check for hit
        cache_key = (tenant_id, data_key)
        was_hit = False
        
        if cache_key in self.key_to_slot:
            slot_id = self.key_to_slot[cache_key]
            slot = self.slots[slot_id]
            slot.last_access_time = current_time
            slot.access_count += 1
            heapq.heappush(self.lru_heap, (current_time, slot_id))
            stats.cache_hits += 1
            was_hit = True
            
            # Physics-Correct: Hits also have jitter (e.g. L3 bank conflicts)
            if rng:
                service_time = Physics.get_stochastic_latency(self.hit_latency_ns, rng)
            else:
                service_time = self.hit_latency_ns
        else:
            stats.cache_misses += 1
            slot_id = self._find_or_evict_slot(current_time)
            slot = self.slots[slot_id]
            if not slot.is_empty():
                old_key = (slot.tenant_id, slot.data_key)
                if old_key in self.key_to_slot:
                    del self.key_to_slot[old_key]
            slot.tenant_id = tenant_id
            slot.data_key = data_key
            slot.last_access_time = current_time
            slot.access_count = 1
            self.key_to_slot[cache_key] = slot_id
            heapq.heappush(self.lru_heap, (current_time, slot_id))
            
            # Physics-Correct: Misses have heavy tail
            if rng:
                service_time = Physics.get_stochastic_latency(self.miss_latency_ns, rng)
            else:
                service_time = self.miss_latency_ns
            
        # Track access performance - PF5-C: include qp_id
        self.flow_tracker.record_access(tenant_id, was_hit, current_time, qp_id)
        
        # Request the memory controller resource (Physics-Correct: Multi-Priority)
        # Victims (priority 1) jump ahead of bullies (priority 0)
        with self.controller.request(priority=priority) as req:
            yield req
            yield self.env.timeout(service_time)
            
        return was_hit, service_time
    
    def _find_or_evict_slot(self, current_time: float) -> int:
        """Find an empty slot or evict the LRU entry."""
        # First, look for empty slot
        for slot in self.slots:
            if slot.is_empty():
                return slot.slot_id
        
        # Evict LRU
        while self.lru_heap:
            access_time, slot_id = heapq.heappop(self.lru_heap)
            slot = self.slots[slot_id]
            
            # Check if this is still the current entry (not updated since)
            if slot.last_access_time == access_time:
                return slot_id
        
        # Fallback: evict slot 0
        return 0
    
    def get_slot_allocation(self) -> Dict[int, int]:
        """Get number of slots allocated to each tenant."""
        allocation: Dict[int, int] = {}
        for slot in self.slots:
            if not slot.is_empty():
                allocation[slot.tenant_id] = allocation.get(slot.tenant_id, 0) + 1
        return allocation
    
    def get_utilization(self) -> float:
        """Get cache utilization (fraction of slots in use)."""
        used = sum(1 for s in self.slots if not s.is_empty())
        return used / self.n_slots


# =============================================================================
# FAIRNESS CALCULATION
# =============================================================================

def compute_jains_fairness(allocations: List[float]) -> float:
    """
    Compute Jain's Fairness Index.
    
    J(x) = (sum(x_i))^2 / (n * sum(x_i^2))
    
    Range: 1/n (completely unfair) to 1 (perfectly fair)
    
    Args:
        allocations: List of resource allocations per entity
        
    Returns:
        Fairness index between 0 and 1
    """
    if len(allocations) == 0:
        return 0.0
    
    allocations = np.array(allocations)
    n = len(allocations)
    sum_x = np.sum(allocations)
    sum_x_sq = np.sum(allocations ** 2)
    
    if sum_x_sq == 0:
        return 1.0  # All zeros = perfectly fair
    
    return (sum_x ** 2) / (n * sum_x_sq)


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == '__main__':
    print("Testing Cache Model...")
    
    # Create cache
    cache = SharedCache(n_slots=100)
    
    # Simulate accesses from 2 tenants
    # Tenant 0: sequential access (good locality)
    # Tenant 1: random access (poor locality)
    
    rng = np.random.default_rng(42)
    time = 0.0
    
    for _ in range(1000):
        # Tenant 0: sequential
        key = _ % 50
        hit, lat = cache.access(0, key, time)
        time += 1.0
        
        # Tenant 1: random (10x rate)
        for _ in range(10):
            key = rng.integers(0, 1000)
            hit, lat = cache.access(1, key, time)
            time += 0.1
    
    # Print results
    print("\nTenant Statistics:")
    for tid, stats in cache.tenant_stats.items():
        print(f"  Tenant {tid}:")
        print(f"    Requests: {stats.requests_submitted}")
        print(f"    Hit Rate: {stats.hit_rate:.2%}")
        print(f"    Avg Latency: {stats.avg_latency_ns:.2f} ns")
    
    print(f"\nSlot Allocation: {cache.get_slot_allocation()}")
    print(f"Is Tenant 1 noisy? {cache.flow_tracker.is_noisy_neighbor(1)}")
    
    print("\nCache model test complete!")
