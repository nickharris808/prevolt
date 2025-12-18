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

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from collections import deque
from enum import Enum
import heapq


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
    def avg_latency(self) -> float:
        if self.requests_completed == 0:
            return 0.0
        return self.total_latency / self.requests_completed
    
    @property
    def p99_latency(self) -> float:
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
        window_size_us: float = 100.0,
        history_length: int = 100
    ):
        """
        Initialize the flow tracker.
        
        Args:
            window_size_us: Time window for rate calculation
            history_length: Number of windows to keep in history
        """
        self.window_size_us = window_size_us
        self.history_length = history_length
        
        # Per-tenant counts in current window
        self.current_hits: Dict[int, int] = {}
        self.current_misses: Dict[int, int] = {}
        
        # Per-tenant miss rate history (deques)
        self.miss_rate_history: Dict[int, deque] = {}
        
        # Window timing
        self.window_start_time: float = 0.0
        self.current_time: float = 0.0
    
    def record_access(self, tenant_id: int, was_hit: bool, current_time: float):
        """
        Record a cache access.
        
        Args:
            tenant_id: The tenant making the request
            was_hit: Whether it was a cache hit
            current_time: Current simulation time
        """
        self.current_time = current_time
        
        # Check if we need to roll over to a new window
        if current_time - self.window_start_time >= self.window_size_us:
            self._roll_window()
        
        if was_hit:
            self.current_hits[tenant_id] = self.current_hits.get(tenant_id, 0) + 1
        else:
            self.current_misses[tenant_id] = self.current_misses.get(tenant_id, 0) + 1
    
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
        self.window_start_time = self.current_time
    
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
        n_slots: int = 1024,
        hit_latency_us: float = 1.0,
        miss_latency_us: float = 100.0
    ):
        """
        Initialize the cache.
        
        Args:
            n_slots: Number of cache slots
            hit_latency_us: Latency for cache hit
            miss_latency_us: Latency for cache miss
        """
        self.n_slots = n_slots
        self.hit_latency_us = hit_latency_us
        self.miss_latency_us = miss_latency_us
        
        # Initialize slots
        self.slots: List[CacheSlot] = [
            CacheSlot(slot_id=i) for i in range(n_slots)
        ]
        
        # Key to slot mapping
        self.key_to_slot: Dict[Tuple[int, int], int] = {}  # (tenant, key) -> slot_id
        
        # LRU tracking (min-heap of (access_time, slot_id))
        self.lru_heap: List[Tuple[float, int]] = []
        
        # Flow tracker
        self.flow_tracker = FlowTracker()
        
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
        current_time: float
    ) -> Tuple[bool, float]:
        """
        Access data in the cache.
        
        Args:
            tenant_id: Tenant making the request
            data_key: Key of data to access
            current_time: Current simulation time
            
        Returns:
            Tuple of (was_hit, latency)
        """
        stats = self._get_or_create_stats(tenant_id)
        stats.requests_submitted += 1
        
        # Check for hit
        cache_key = (tenant_id, data_key)
        was_hit = False
        latency = self.miss_latency_us
        
        if cache_key in self.key_to_slot:
            slot_id = self.key_to_slot[cache_key]
            slot = self.slots[slot_id]
            
            # Update LRU
            slot.last_access_time = current_time
            slot.access_count += 1
            heapq.heappush(self.lru_heap, (current_time, slot_id))
            
            stats.cache_hits += 1
            was_hit = True
            latency = self.hit_latency_us
        else:
            # Cache miss - need to allocate slot
            stats.cache_misses += 1
            
            # Find slot to use (empty or LRU eviction)
            slot_id = self._find_or_evict_slot(current_time)
            slot = self.slots[slot_id]
            
            # Evict old entry if necessary
            if not slot.is_empty():
                old_key = (slot.tenant_id, slot.data_key)
                if old_key in self.key_to_slot:
                    del self.key_to_slot[old_key]
            
            # Install new entry
            slot.tenant_id = tenant_id
            slot.data_key = data_key
            slot.last_access_time = current_time
            slot.access_count = 1
            
            self.key_to_slot[cache_key] = slot_id
            heapq.heappush(self.lru_heap, (current_time, slot_id))
            
        # Track access performance
        self.flow_tracker.record_access(tenant_id, was_hit, current_time)
        
        return was_hit, latency
    
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
        print(f"    Avg Latency: {stats.avg_latency:.2f} μs")
    
    print(f"\nSlot Allocation: {cache.get_slot_allocation()}")
    print(f"Is Tenant 1 noisy? {cache.flow_tracker.is_noisy_neighbor(1)}")
    
    print("\nCache model test complete!")


