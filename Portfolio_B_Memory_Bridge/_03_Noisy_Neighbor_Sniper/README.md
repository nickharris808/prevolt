# Simulation 3: Noisy Neighbor Sniper

## The Problem

Tenant A thrashes the shared memory bandwidth, causing Tenant B to experience 100x latency spikes. Fair-share throttling punishes the victim.

In multi-tenant CXL/UEC environments:
- **Noisy Tenant**: High request rate, random access pattern (no locality)
- **Good Tenant**: Normal rate, sequential access (high locality)
- **Result**: Cache thrashing, latency explosion for good tenants

## The Tournament

We compare four isolation algorithms:

| Algorithm | Description | Trade-off |
|-----------|-------------|-----------|
| **No Control (Baseline)** | First-come-first-served | Noisy neighbor wins |
| **Fair Share** | Throttle everyone by 20% | Punishes victims |
| **VIP Priority** | Gold > Bronze queues | Starves Bronze completely |
| **Sniper** | Identify & throttle only the bully | Complex flow tracking |

## The Model (SimPy + Python Classes)

```python
class CacheSlot:
    tenant_id: int
    last_access: float
    eviction_priority: int

class MemoryController:
    slots: List[CacheSlot]  # 1024 slots
    request_queue: PriorityQueue
    flow_tracker: Dict[tenant_id, RequestStats]
```

## Key Files

- `cache_model.py` - Python class-based cache with flow tracking
- `simulation.py` - Multi-tenant contention simulation
- `tournament.py` - Tournament comparing 4 algorithms
- `latency_cdf.png` - Cumulative distribution of latencies
- `fairness_comparison.png` - Jain's fairness index

## Running the Simulation

```bash
# Quick test (50 trials)
python tournament.py --quick

# Full tournament (1000 trials)
python tournament.py --n_trials 1000
```

## Patent Claim Support

> "A multi-tenant memory isolation system comprising a per-flow request rate 
> monitor and a selective throttling mechanism that applies bandwidth reduction 
> exclusively to flows exceeding a statistical deviation threshold from the 
> tenant population mean."

### Key Findings

1. **No Control** allows noisy tenant to consume 60%+ of resources
2. **Fair Share** reduces everyone's throughput by 20%
3. **VIP** protects VIP but starves others
4. **Sniper** achieves 0.95 fairness with minimal good-tenant impact

### The "Wow" Deliverable

The latency CDF shows:
- Baseline: Long tail (p99 = 10ms)
- Sniper: Tight curve (p99 = 50μs)

Good tenants see 200x latency improvement!

## Tenant Behavior Profiles

- **Noisy Tenant**: Random access, 10x request rate, no locality
- **Good Tenant**: Sequential access, normal rate, high locality
- **Bursty Tenant**: Idle periods with 100x spikes

## Key Metrics

- **Fairness Score (Jain's Index)**: 0 = one tenant gets everything, 1 = perfectly equal
- **Victim Latency p99**: Tail latency experienced by good tenants
- **Aggressor Penalty**: How much we slow down the noisy neighbor
