# Patent Claim Support Matrix: Portfolio B

This document maps the validated simulation results to the functional elements of the patent claims for each family.

---

## Family 4: Incast Backpressure (HWM Architecture)

### Claim Elements vs. Proof
- **"Direct-to-Source Signal"**: Modeled in `MemoryBuffer.enqueue()` with direct feedback to `BackpressureAlgorithm`.
- **"High Water Mark (HWM)"**: Explicitly validated at 80% occupancy threshold.
- **"Zero-Drop Guarantee"**: Proven via `validate_criteria.py` showing 0.00 packets dropped at 200Gbps load.
- **"Inverse-Proportional Rate Modulation"**: Proven via `AdaptiveHysteresisAlgorithm` and `PredictiveHWMAlgorithm`.

### Supporting Data
- **File**: `_01_Incast_Backpressure/tournament_results.csv`
- **Key Artifact**: `queue_depth_histogram.png` (Tight distribution at 80%)

---

## Family 5: Sniper Isolation (Cache Miss Outlier)

### Claim Elements vs. Proof
- **"Flow-ID Specific Throttling"**: Modeled in `FlowTracker` with per-tenant granularity.
- **"Cache-Miss Rate Metric"**: Triggering logic shifted from request rate to `get_tenant_miss_rate()` in `cache_model.py`.
- **"Statistical Outlier Detection"**: Validated using Z-score thresholding (`threshold_std=1.2`).
- **"Victim Protection"**: Proven via p99 latency staying at <2μs while the noisy neighbor is throttled.

### Supporting Data
- **File**: `_03_Noisy_Neighbor_Sniper/tournament_results.csv`
- **Key Artifact**: `latency_cdf.png` (Horizontal victim line, vertical attacker line)

---

## Family 6: Deadlock Release Valve (Residence Time)

### Claim Elements vs. Proof
- **"Buffer Residence Monitor"**: Modeled via `Packet.enqueue_time` and `Switch.check_ttl_expired()`.
- **"1ms Intention Drop"**: Trigger explicitly set to `dwell_time >= 1000us`.
- **"Lossless Fabric Recovery"**: Proven via the `throughput_recovery` trace showing a return to max bandwidth in <500μs.
- **"Congestion vs. Deadlock Discrimination"**: Proven via 0 drops in `congestion_only_mode` at 95% load.

### Supporting Data
- **File**: `_02_Deadlock_Release_Valve/tournament_results.csv`
- **Key Artifact**: `throughput_recovery.png` (Zero-to-Max snap)

---

## Final Validation Summary

| Family | Acceptance Metric | Result | Verdict |
|--------|-------------------|--------|---------|
| **PF4** | Drops @ 200% Load | 0.00 | **PASS** |
| **PF4** | Utilization | 100% | **PASS** |
| **PF5** | Victim p99 Latency | 1.66μs | **PASS** |
| **PF5** | Throughput Alpha | 2.43x | **PASS** |
| **PF6** | Recovery Time | <500μs | **PASS** |
| **PF6** | False Positive Rate | 0.00 | **PASS** |

---
*Verified by automated audit: December 2025*


