# Portfolio B: The Cross-Layer Memory Bridge family Tree
## Strategic Acquisition Briefing for Broadcom / Arista / Hyperscalers

---

### Family 4: Direct-to-Source Backpressure (Incast Protection)
**The Mission:** Subordinate the Network (UEC) to the Memory Controller (CXL) to achieve 0.00% drops at 200% load with >99% link utilization.

*   **PF4-A: Direct-to-Source (Baseline)** - Pure hardware signal path from Memory Controller (MC) to NIC for binary pause.
*   **PF4-B: Adaptive Hysteresis** - Dual-threshold stability optimizer (80/70) to prevent "control oscillation" and link jitter.
*   **PF4-C: Predictive dV/dt Controller** - **[Key Invention]** Calculates buffer fill velocity (first derivative); triggers backpressure proactive to overflow.
*   **PF4-D: Credit Pacing (Fractional)** - Modulates the rate of UEC-native credit return to smoothly decelerate senders instead of hard stopping.
*   **PF4-E: Buffer Partitioning** - Guaranteed minimum buffer slots per Flow-ID to prevent "incast bullying" from starving independent flows.
*   **PF4-F: Jitter-Aware Hybrid** - Confidence-gated switching between dV/dt prediction and HWM safety nets based on traffic entropy.

---

### Family 5: Cache-Miss "Sniper" (Multi-Tenant Isolation)
**The Mission:** Protect "Victim" p99 latency (<50us) by silencing memory-bandwidth bullies using hardware-level cache performance telemetry.

*   **PF5-A: Cache-Miss Sniper (Core)** - Outlier detection using Z-score deviations in per-flow cache miss rates.
*   **PF5-B: Graduated Sniper** - Multi-stage penalty escalation (UEC ECN Mark → Credit Reduction → Intention Drop).
*   **PF5-C: Aggregated Tenant Sniper** - **[Key Invention]** Hardware grouping of Flow-IDs by Tenant-ID to defeat "QP-Spraying" (where a bully hides across 1000 flows).
*   **PF5-D: Collective Traffic Shield** - Whitelists UEC TC0/TC1 (Collective sync/Control) traffic to ensure system stability during bulk-data attacks.
*   **PF5-E: Miss-Rate Velocity Tracker** - First-derivative reaction to rapid miss-rate spikes, catching "Burst Bullies" before they hit the cache.
*   **PF5-F: VIP Guard Hybrid** - Combines sniper isolation with strict priority queues for "Gold Tier" workload protection.

---

### Family 6: Deadlock Release Valve (Intention Drop)
**The Mission:** Guarantee <2ms recovery from credit-locked states in lossless fabrics with **Zero False Positives** during normal congestion.

*   **PF6-A: Fixed TTL Timeout** - Deterministic residence time trigger (1ms baseline) for safety drops.
*   **PF6-B: Adaptive TTL** - Scales timeout duration based on local queue depth to allow "legal" congestion to pass.
*   **PF6-C: Coordinated Valve (Consensus)** - **[Key Invention]** Switch queries upstream/downstream neighbors; only drops if circular dependency is confirmed fabric-wide.
*   **PF6-D: VL Shuffling (Lane Swap)** - Moves "stuck" packets to dedicated recovery Virtual Lanes (VLs) instead of discarding data.
*   **PF6-E: Credit Jittering** - Proactively injects intentional jitter into credit returns to break synchronization-based deadlock loops.
*   **PF6-F: Fast Retransmit Valve** - Couples the Intention-Drop with a sub-microsecond Hardware-NACK to the sender for instant recovery.

---

### Family 7: Stranded Memory Borrowing (CXL Pooling)
**The Mission:** Eliminate OOM crashes by enabling zero-copy, network-transparent memory borrowing across the CXL.mem fabric.

*   **PF7-A: Balanced Borrowing** - Global allocation policy that pulls from nodes with highest free capacity.
*   **PF7-B: Latency-Tiered Allocation** - Allocator awareness of "Hot" (Local), "Warm" (CXL Bridge), and "Cold" (Multi-hop) memory pools.
*   **PF7-C: CXL.mem Tunneling** - Protocol for mapping remote physical memory directly into local virtual address space via UEC-CXL bridge.
*   **PF7-D: Duration-Negotiated Loans** - **[Key Invention]** Borrowing thresholds scale inversely with job duration; prevents long-running "memory hogs" from stranding peers.
*   **PF7-E: Predictive Pre-Borrowing** - Uses page-fault telemetry to pre-allocate remote pages *before* the local limit is reached.
*   **PF7-F: Fair-Share Cluster Pool** - Enforces cluster-wide memory fairness (Jain's Index) while maximizing total cluster utilization (>95%).

---
*Proprietary & Confidential. 24 Foundational Patents Pending.*
