# Portfolio B: The Cross-Layer Memory Bridge family Tree
## Strategic Acquisition Briefing for Broadcom / Arista / Hyperscalers

---

### Family 4: Direct-to-Source Backpressure (Incast)
**Mission**: Subordinate the Network (UEC) to the Memory Controller (CXL) to achieve 0.00% drops at 200% load.

1.  **PF4-A: Direct-to-Source (Baseline)**: Pure hardware signal path from MC to NIC.
2.  **PF4-B: Adaptive Hysteresis**: Dual-threshold stability optimizer to prevent control oscillation.
3.  **PF4-C: Predictive HWM**: Online learning fill-rate predictor (dV/dt) for proactive throttling.
4.  **PF4-D: Credit Pacing**: Fractional credit-based deceleration using UEC-native flow control.
5.  **PF4-E: Buffer Partitioning**: Multi-tenant isolation through reserved per-flow memory lanes.
6.  **PF4-F: Hybrid Controller**: Confidence-gated switching between predictive and reactive modes.

---

### Family 5: Cache-Miss "Sniper" Isolation
**Mission**: Identify and silence "Noisy Neighbors" based on cache performance telemetry, protecting victim latency.

1.  **PF5-A: Cache-Miss Sniper**: Core invention using Z-score outliers in miss rates.
2.  **PF5-B: Graduated Sniper**: Multi-stage penalty (ECN Mark → Rate Limit → Selective Drop).
3.  **PF5-C: Aggregated Sniper**: Tenant-level aggregation to defeat QP-spraying attacks.
4.  **PF5-D: UEC Priority Shield**: TC0/Collective traffic whitelisting to protect All-Reduce syncs.
5.  **PF5-E: Velocity Tracker**: First-derivative reaction to rapid miss-rate spikes.
6.  **PF5-F: Fairness/Sniper Hybrid**: Balances individual victim latency against total cluster throughput.

---

### Family 6: Deadlock Release Valve
**Mission**: Guarantee <500μs recovery from credit-locked states in lossless fabrics without false positives.

1.  **PF6-A: Fixed Timeout**: Deterministic residence time trigger (1ms baseline).
2.  **PF6-B: Adaptive TTL**: Congestion-scaling timeout that becomes "patient" during normal peaks.
3.  **PF6-C: Coordinated Valve**: Cross-switch consensus monitor to verify global deadlock state.
4.  **PF6-D: VL Shuffling**: Moving blocked flows to "Recovery Virtual Lanes" before dropping.
5.  **PF6-E: Credit Jittering**: Proactive credit-injection to break potential loops pre-emptively.
6.  **PF6-F: Grand Unified Deadlock Twin**: Real-time fabric monitoring via UEC In-Band Telemetry (INT).

---

### Family 7: Stranded Memory "Borrowing" Protocol
**Mission**: Transparently pool fragmented memory across nodes to reach 100% job completion rate.

1.  **PF7-A: Balanced Borrow**: Headroom-aware allocation from the node with most free memory.
2.  **PF7-B: Latency-Aware Tiering**: Topology-optimized borrowing based on CXL hop count.
3.  **PF7-C: Jitter mitigation**: Software-defined stabilization of remote memory access latency.
4.  **PF7-D: Cooperative Loans**: Duration-negotiated borrowing to prevent stranding future jobs.
5.  **PF7-E: Predictive Pre-Borrowing**: Anticipatory pooling based on job-memory ramp signatures.
6.  **PF7-F: Multi-Tenant Fair Share**: Fair distribution of the remote memory pool across competing tenants.

---
*Proprietary & Confidential. 24 Foundational Patents Pending.*
