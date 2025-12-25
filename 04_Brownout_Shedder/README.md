# Brownout Priority Shedder

## Problem Statement

Grid power events (brownouts, voltage sags) require immediate load reduction:
- Utility signals demand reduction within milliseconds
- Failure to comply can trigger protective breaker trips
- Traditional approach: shed ALL traffic proportionally
- Result: Inference latency spikes, training jobs fail

## The Innovation

**Priority-Based Load Shedding**: Traffic is classified into priority tiers, and only low-priority traffic is shed during brownout events.

| Class | Name | Priority | Sheddable | Example Workloads |
|-------|------|----------|-----------|-------------------|
| Gold | Inference | High | Never | Real-time inference, serving |
| Bronze | Checkpoint | Low | Yes | Model checkpoints, backups |

## Simulation Results

| Metric | Baseline (No QoS) | With QoS | Improvement |
|--------|-------------------|----------|-------------|
| Power Reduction | 33% | 33% | Same |
| Gold Preservation | 60% | **100%** | **+40%** |

### Key Insight

QoS-enabled shedding achieves the **same power reduction** while preserving **100% of inference traffic**. This is the difference between:
- **Baseline**: Customer-facing AI services go down during brownout
- **With QoS**: Customer-facing AI services unaffected

## Shedding Behavior

```
Normal Operation:
  Gold:   ████████████████████████ 60 Gbps
  Bronze: ████████████████         40 Gbps
  Total:  ████████████████████████████████████████ 100 Gbps

Brownout (with QoS):
  Gold:   ████████████████████████ 60 Gbps (100% preserved)
  Bronze: (shed)                    0 Gbps
  Total:  ████████████████████████ 60 Gbps (40% reduction)
```

## Visualizations

### power_shedding.png
Four-panel comparison:
- **Top Left**: Baseline traffic (both reduced during brownout)
- **Bottom Left**: Baseline power consumption
- **Top Right**: QoS traffic (only Bronze shed)
- **Bottom Right**: QoS power consumption

### power_shedding_single.png
Single-panel stacked area chart showing instant Bronze shedding with Gold preservation.

## Patent Claim

> "A network quality-of-service system for power-aware load shedding, comprising:
> 
> (a) a traffic classifier that assigns priority levels to network flows based on workload type;
> (b) a brownout detector that receives grid power signals and triggers shedding events;
> (c) a priority queue manager that instantly drops low-priority queues while preserving high-priority traffic;
> (d) wherein the system achieves target power reduction with zero impact on latency-sensitive workloads."

## Files in This Directory

- `simulation.py` - Main simulation and visualization
- `power_shedding.png` - Four-panel comparison
- `power_shedding_single.png` - Single-panel chart
- `README.md` - This documentation

## Reproduction

```bash
cd 04_Brownout_Shedder
python simulation.py
```

## Target Customers

1. **Cloud Providers**: Participate in demand response programs without SLA violations
2. **Utility Companies**: Get reliable demand reduction from data centers
3. **Data Center Operators**: Avoid breaker trips during grid events







