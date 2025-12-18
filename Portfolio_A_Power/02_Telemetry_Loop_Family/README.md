# Patent Family 2: The "In-Band" Telemetry Loop (Standard-Essential)

**The Thesis:** The switch is "blind." By embedding voltage health directly into transport headers (e.g. IPv6 Flow Label or TCP Options), we enable the first nanosecond-scale feedback loop for data center power. This family defines the **In-Band Signaling** requirements for GPOP.

## Family Variations (Patent Claims)

### 2.1 Quantized Feedback (The Baseline)
*   **Mechanism:** 4-bit integer health code. Simple threshold-based throttling.
*   **Proof:** Bandwidth drop within 2 RTTs of voltage crossing 0.8V.
*   **Artifact:** `artifacts/01_quantized_trace.png`

### 2.2 PID Rate Controller
*   **Mechanism:** Closed-loop PID controller implemented in the switch management logic.
*   **Proof:** Smooth, non-oscillatory recovery of bandwidth after a power event.
*   **Artifact:** `artifacts/02_pid_control.png`

### 2.3 Gradient (dv/dt) Preemption
*   **Mechanism:** Detection of the *rate* of change in voltage. Pre-empts the crash by throttling before thresholds are crossed.
*   **Proof:** 30% reduction in peak droop compared to reactive thresholds.
*   **Artifact:** `artifacts/03_gradient_preemption.png`

### 2.4 Per-Tenant Flow Sniper
*   **Mechanism:** Cross-correlation of telemetry error signals with individual flow egress rates. 
*   **Proof:** Surgical throttling of a "power bully" tenant while protecting the SLAs of other tenants.
*   **Artifact:** `artifacts/04_tenant_isolation.png`

### 2.5 Graduated Penalties
*   **Mechanism:** Three-tier escalation: ECN marking → Hardware Rate Limiting → Tail Drop.
*   **Proof:** Soft-landing power curve with zero packet loss during mild stress.
*   **Artifact:** `artifacts/05_graduated_escalation.png`

### 2.6 Collective Guard (S+ Tier)
*   **Mechanism:** Application-aware QoS that protects AllReduce sync traffic while shedding bulk storage flows.
*   **Proof:** Training job progress maintained during power transients.
*   **Artifact:** `artifacts/06_collective_guard.png`

### 2.7 QP-Spray Aggregator
*   **Mechanism:** Tenant-level traffic aggregation to identify power bullies who "spray" load across 1,000s of flows.
*   **Proof:** Evasion-proof tenant isolation.
*   **Artifact:** `artifacts/07_qp_spray_defense.png`

### 2.8 Stability Analysis (Standard-Ready)
*   **Mechanism:** Bode margin analysis to ensure closed-loop stability across the fabric latency envelope (up to 5ms RTT).
*   **Proof:** Phase margin > 45 degrees guaranteed for high-frequency switch schedulers.
*   **Artifact:** `artifacts/08_stability_bode.png`

## How to Run
```bash
python master_tournament.py
```

