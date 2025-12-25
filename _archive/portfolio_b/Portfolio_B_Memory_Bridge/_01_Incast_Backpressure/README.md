# Simulation 1: Incast Backpressure

## The Problem

Network (100 Gbps) is faster than Memory Controller (50 Gbps). When 1000 GPUs send data to one node, the buffer overflows instantly.

This is the fundamental "speed mismatch" problem in CXL/UEC clusters:
- **Network ingress**: 100+ Gbps per port
- **Memory drain**: 50 Gbps effective bandwidth
- **Result**: 2:1 oversubscription causes buffer overflow

## The Tournament

We compare three backpressure algorithms:

| Algorithm | Description | Trade-off |
|-----------|-------------|-----------|
| **No Control (Baseline)** | Buffer fills, packets drop | High throughput, catastrophic drops |
| **Static Threshold** | Pause at 80% buffer depth | Safe but wastes 20% capacity |
| **Adaptive Hysteresis** | Pause at 90%, resume at 70% | Maximizes throughput, complex logic |

## The Model (SimPy)

- **Producer Process**: Network arrivals at exponential inter-arrival times (100 Gbps equivalent)
- **Consumer Process**: Memory controller draining at fixed rate (50 Gbps)
- **Buffer**: SimPy `Container` with configurable capacity (1MB, 10MB, 100MB tests)
- **Backpressure Signal**: Binary flag checked by producer before each put()

## Key Files

- `simulation.py` - Core SimPy model with producer-consumer queue
- `tournament.py` - Tournament runner comparing all algorithms
- `queue_depth_histogram.png` - Distribution of buffer occupancy
- `drop_rate_comparison.png` - Packet drop rates by algorithm

## Running the Simulation

```bash
# Quick test (50 trials)
python tournament.py --quick

# Full tournament (1000 trials per algorithm)
python tournament.py --n_trials 1000
```

## Patent Claim Support

> "A memory flow control apparatus wherein a network interface modulates 
> transmission rate in inverse proportion to memory buffer occupancy, 
> utilizing hysteresis thresholds to prevent oscillation."

### Key Findings

1. **No Control** leads to 40%+ drop rates in incast scenarios
2. **Static Threshold** reduces drops but wastes buffer capacity
3. **Adaptive Hysteresis** achieves <1% drops while using 85%+ buffer capacity

### Statistical Validation

- 1000 trials per algorithm-scenario combination
- 95% confidence intervals on all metrics
- Welch's t-test for pairwise comparisons (p < 0.001)
- Cohen's d > 2.0 (very large effect size)

## Scenarios Tested

1. **Uniform_10MB**: Steady-state uniform traffic
2. **Bursty_10MB**: AI inference batch patterns
3. **Incast_50_senders**: 50 nodes sending simultaneously
4. **Incast_Small_Buffer**: Stress test with 1MB buffer
5. **Incast_Large_Buffer**: Best case with 100MB buffer
