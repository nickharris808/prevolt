#!/usr/bin/env python3
"""
Cache Model V2: Multi-Dimensional Locality Tracking
===================================================

This module implements the high-fidelity cache model required for the 
"Sniper" Flow Isolation logic. It tracks more than just miss rates;
it measures the 'Value of Work' and 'Spatial Locality' to detect 
adversarial gaming.

Addresses Critique 1.3: "Sniper logic can be gamed"
"""

import numpy as np
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

@dataclass
class CacheConfig:
    size_bytes: int = 33_554_432  # 32 MiB L3 (Xeon Sapphire Rapids)
    line_size: int = 64            # 64-byte lines
    associativity: int = 16        # 16-way set associative
    latency_hit_ns: float = 13.75  # From physics_engine_v2
    latency_miss_ns: float = 100.0 # DRAM access

class MultiDimensionalTracker:
    """
    Tracks workload characteristics across 4 dimensions:
    1. Cache Miss Rate
    2. Temporal Variance (Detects alternating sequential/random)
    3. Spatial Locality (Address clustering)
    4. Value Score (Useful fetches vs wasted cycles)
    """
    def __init__(self, window_size: int = 1000):
        self.history = deque(maxlen=window_size)
        self.addresses = deque(maxlen=window_size)
        self.window_size = window_size

    def record(self, is_miss: bool, address: int):
        self.history.append(1 if is_miss else 0)
        self.addresses.append(address)

    @property
    def miss_rate(self) -> float:
        if not self.history: return 0.0
        return sum(self.history) / len(self.history)

    @property
    def temporal_variance(self) -> float:
        """Detects if the workload is rapidly switching patterns (gaming attempt)."""
        if len(self.history) < 20: return 0.0
        # Compute rolling variance of the miss rate
        parts = np.array_split(list(self.history), 10)
        means = [np.mean(p) for p in parts]
        return float(np.var(means))

    @property
    def spatial_locality(self) -> float:
        """Measures how clustered the addresses are (0 = random, 1 = perfectly sequential)."""
        if len(self.addresses) < 2: return 0.0
        addr_list = list(self.addresses)
        # Calculate stride distances
        strides = np.abs(np.diff(addr_list))
        # Stride of 'line_size' is perfect locality
        sequential_hits = np.sum(strides <= 64)
        return sequential_hits / len(strides)

    @property
    def value_score(self) -> float:
        """Computes a 'utility' score for the bandwidth consumed."""
        # High value = low miss rate + high spatial locality
        # Low value = high miss rate + low locality (The Sniper's Target)
        return (1.0 - self.miss_rate) * (0.5 + 0.5 * self.spatial_locality)

class HighFidelityCache:
    def __init__(self, config: CacheConfig):
        self.config = config
        self.num_lines = config.size_bytes // config.line_size
        self.num_sets = self.num_lines // config.associativity
        
        # Simple set-associative cache (address -> timestamp)
        self.sets = [{} for _ in range(self.num_sets)]
        self.trackers: Dict[int, MultiDimensionalTracker] = {}

    def access(self, tenant_id: int, address: int, time_ns: float) -> Tuple[bool, float]:
        if tenant_id not in self.trackers:
            self.trackers[tenant_id] = MultiDimensionalTracker()
        
        line_addr = address // self.config.line_size
        set_idx = line_addr % self.num_sets
        cache_set = self.sets[set_idx]
        
        is_miss = False
        latency = self.config.latency_hit_ns
        
        if line_addr in cache_set:
            # HIT
            cache_set[line_addr] = time_ns
        else:
            # MISS
            is_miss = True
            latency = self.config.latency_miss_ns
            if len(cache_set) >= self.config.associativity:
                # LRU Eviction
                lru_line = min(cache_set, key=cache_set.get)
                del cache_set[lru_line]
            cache_set[line_addr] = time_ns
            
        self.trackers[tenant_id].record(is_miss, address)
        return is_miss, latency

    def get_features(self, tenant_id: int) -> Dict[str, float]:
        t = self.trackers.get(tenant_id)
        if not t: return {}
        return {
            "miss_rate": t.miss_rate,
            "temporal_variance": t.temporal_variance,
            "spatial_locality": t.spatial_locality,
            "value_score": t.value_score
        }
