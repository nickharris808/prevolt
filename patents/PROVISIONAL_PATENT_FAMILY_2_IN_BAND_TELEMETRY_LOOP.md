# PROVISIONAL PATENT APPLICATION

---

## IN-BAND TELEMETRY LOOP FOR NETWORK-DRIVEN POWER MANAGEMENT: SYSTEMS AND METHODS FOR ENCODING GPU VOLTAGE HEALTH IN IPV6 FLOW LABELS AND IMPLEMENTING HARDWARE-ACCELERATED ADAPTIVE RATE CONTROL

---

# CROSS-REFERENCE TO RELATED APPLICATIONS

This application claims the benefit of priority and is a provisional application filed under 35 U.S.C. Section 111(b).

This application is related to co-pending provisional applications:
- "PRE-COGNITIVE VOLTAGE TRIGGER" (related invention for VRM pre-charging based on network observation)
- "SPECTRAL RESONANCE DAMPING" (related invention for network-level power coordination)
- "COHERENT PHASE-LOCKED NETWORKING" (related invention for timing substrate)

The above applications share common inventive concepts around network-as-orchestrator paradigms for power management. In particular, the In-Band Telemetry Loop disclosed herein provides the real-time voltage health feedback that enables the Pre-Cognitive Voltage Trigger to make informed pre-charging decisions. The telemetry encoding format disclosed herein is compatible with the spectral shaping mechanisms of the Spectral Resonance Damping invention.

---

# INVENTOR(S)

[INVENTOR NAME(S) TO BE INSERTED]

---

# FIELD OF THE INVENTION

The present invention relates generally to the field of network-driven power management for high-performance computing systems. More specifically, the invention relates to systems and methods for:
1. Encoding GPU voltage health status directly into IPv6 Flow Label fields of standard network packets;
2. Parsing said telemetry at line rate in programmable switch hardware;
3. Implementing adaptive rate control based on received telemetry using PID controllers, gradient preemption, and application-aware quality-of-service (QoS) mechanisms.

---

# BACKGROUND OF THE INVENTION

## The Power Visibility Gap

Modern AI data centers face a fundamental visibility problem: the network switches that control traffic have no knowledge of the power state of the GPUs they serve. Switches route packets based on destination addresses, QoS markings, and congestion state—but never consider whether the receiving GPU is about to experience a voltage crash from excessive current draw.

This lack of visibility creates a reactive-only paradigm for power management. When a GPU's voltage drops below critical thresholds (typically 0.85V for modern accelerators), the GPU itself must implement emergency measures: clock throttling, workload shedding, or even power-state transitions. These reactive measures occur AFTER the damage is already underway.

The economic cost is substantial. GPU voltage excursions cause:
- **Training checkpoints:** When voltage instability threatens model state, training frameworks checkpoint to storage—adding minutes of overhead to multi-week training runs.
- **Stragglers:** A single GPU in voltage distress becomes a "straggler" that blocks collective operations (AllReduce), wasting the compute time of thousands of other GPUs that sit idle waiting.
- **Hardware degradation:** Repeated voltage excursions below 0.80V accelerate electromigration and reduce GPU lifespan.

## Limitations of Out-of-Band Telemetry

Existing telemetry approaches transmit power metrics via dedicated management networks (IPMI, Redfish, OpenBMC). These "out-of-band" (OOB) systems suffer from:

**Latency:** OOB telemetry typically updates at 1-second intervals—1,000x slower than the microsecond timescales of voltage transients. By the time OOB reports a problem, the crash has already happened and recovered (or not).

**Polling overhead:** OOB requires dedicated management processors to poll sensors and construct telemetry packets. This adds hardware cost and consumes power budget that could otherwise go to compute.

**Path asymmetry:** OOB telemetry travels different physical paths than data traffic, making correlation between telemetry and specific traffic patterns impossible.

**No closed-loop control:** Because OOB is slow and asynchronous, it cannot participate in closed-loop control. At best, it informs operators of past events.

## The Need for In-Band Telemetry

The solution is "in-band" telemetry—embedding power state information directly into the headers of regular data packets. Every ACK or completion packet from a GPU becomes a carrier of voltage health information, riding the same paths and experiencing the same latencies as the data traffic it describes.

In-band telemetry enables:
- **Microsecond-scale visibility:** Telemetry arrives with every packet, providing kHz-rate updates instead of Hz-rate OOB polling.
- **Zero additional hardware:** Telemetry piggybacks on existing data packets; no management network required.
- **Natural correlation:** Telemetry follows the exact path of the data, enabling switches to directly control the traffic that caused the power stress.
- **Closed-loop control:** Fast telemetry enables proportional-integral-derivative (PID) controllers that stabilize voltage rather than react to crashes.

---

# SUMMARY OF THE INVENTION

The present invention provides a complete in-band telemetry system for network-driven GPU power management, comprising:

1. **Telemetry Encoding:** A method for encoding GPU voltage health as a 4-bit integer (0-15) in the low-order bits of the IPv6 Flow Label field, enabling transmission with zero additional overhead on every outgoing packet.

2. **Line-Rate Parsing:** A P4-programmable switch implementation that extracts voltage health from the Flow Label at line rate (terabits per second) with zero latency penalty.

3. **Adaptive Rate Control:** Multiple control algorithms (PID, gradient preemption, collective guard) that adjust egress rate limits based on received telemetry.

4. **Application-Aware QoS:** Selective throttling that protects high-value traffic classes (AllReduce synchronization) while shedding low-priority traffic (checkpoint storage) during power stress events.

## Key Inventive Elements

**Element 1: IPv6 Flow Label Encoding Convention**

The IPv6 header includes a 20-bit Flow Label field originally intended for stateless QoS handling. The invention repurposes the lowest 4 bits of this field as a "voltage health" indicator:

    Flow Label (20 bits): [16 bits: traditional flow ID] [4 bits: voltage health]
    
    voltage_health encoding:
    - 15 (0xF): Excellent (V ≥ 0.93V)
    - 12-14:    Good (0.90V ≤ V < 0.93V)
    - 8-11:     Warning (0.85V ≤ V < 0.90V)
    - 4-7:      Critical (0.80V ≤ V < 0.85V)
    - 0-3:      Emergency (V < 0.80V)

This encoding requires no header expansion, no new protocols, and no changes to intermediate routers that don't understand the convention.

**Element 2: GPU-Side Telemetry Insertion**

The GPU inserts its current voltage health into every outgoing ACK packet by:
1. Reading the VRM voltage feedback register (typically available via I2C or SMBus on standard GPU power management ICs)
2. Quantizing the voltage to the 4-bit health scale
3. Masking the health value into the low 4 bits of the IPv6 Flow Label

This operation occurs in the GPU's network interface controller (NIC) or in a specialized telemetry ASIC co-located with the GPU.

**Element 3: Switch-Side Telemetry Extraction**

At the switch, a P4-programmable pipeline parses the IPv6 header and extracts the voltage health:

    meta.voltage_health = (bit<4>) (hdr.ipv6.flowLabel & 0xF);

This single bitwise AND operation occurs in the switch's parser, adding zero additional latency to packet processing. The extracted health is stored in per-destination state (e.g., a register keyed by destination IP or egress port).

**Element 4: Adaptive Rate Control**

Based on accumulated voltage health telemetry, the switch adjusts its egress rate for flows destined to stressed GPUs. Multiple control algorithms are disclosed:

- **Step Threshold:** Simple rate limiting when health drops below fixed thresholds (e.g., 50% rate at health < 8, 25% rate at health < 4).
- **PID Controller:** Smooth, oscillation-free rate adjustment using proportional-integral-derivative control.
- **Gradient Preemption:** Rate reduction triggered by the SLOPE of health degradation (dHealth/dt), not just absolute health level—enabling earlier intervention.
- **Collective Guard:** Application-aware throttling that protects synchronized training traffic while shedding background checkpoint/storage traffic.

---

# DETAILED DESCRIPTION OF PREFERRED EMBODIMENTS

## Embodiment 1: P4 Switch Implementation

The preferred embodiment implements the telemetry loop in a P4-programmable switch (Intel Tofino, AMD Pensando, or equivalent). The complete implementation is provided in `02_Telemetry_Loop/variations/reference.p4`.

### 1.1 Header Definitions

The P4 program defines standard Ethernet, IPv6, and TCP headers:

```p4
header ipv6_t {
    bit<4>  version;
    bit<8>  trafficClass;
    bit<20> flowLabel;
    bit<16> payloadLen;
    bit<8>  nextHdr;
    bit<8>  hopLimit;
    bit<128> srcAddr;
    bit<128> dstAddr;
}

struct metadata_t {
    bit<4>  voltage_health;
    bit<1>  health_valid;
    bit<32> meter_color;
}
```

### 1.2 Parser Logic

The parser extracts voltage health during IPv6 header parsing:

```p4
state parse_ipv6 {
    packet.extract(hdr.ipv6);
    // Extract voltage health from low 4 bits of flow label.
    meta.voltage_health = (bit<4>) (hdr.ipv6.flowLabel & 0xF);
    meta.health_valid = 1;
    transition select(hdr.ipv6.nextHdr) {
        6: parse_tcp;
        default: accept;
    }
}
```

This extraction occurs inline with standard parsing, adding zero cycles to the critical path.

### 1.3 Health State Storage

The switch maintains per-destination voltage health state using P4 registers:

```p4
register<bit<4>>(65536) health_table;

action store_health(bit<4> h, bit<16> dst_hash) {
    health_table.write(dst_hash, h);
}
```

In production, the dst_hash would be a function of the destination IP address, egress port, and/or tenant ID, enabling fine-grained per-GPU tracking.

### 1.4 Rate Enforcement

A three-color meter (green/yellow/red) enforces rate limits based on stored health:

```p4
meter(65536, MeterType.bytes) gpu_meter;

action apply_gpu_meter(bit<16> dst_hash) {
    // Meter rate is configured by control plane based on health
    gpu_meter.execute_meter(dst_hash, meta.meter_color);
}

apply {
    bit<4> h;
    health_table.read(h, dst_hash);
    
    // Configure meter dynamically (pseudo-code for rate selection)
    if (h <= 4) {
        // Critical: aggressive throttle (25% rate)
        set_meter_rate(dst_hash, RATE_25_PERCENT);
    } else if (h <= 8) {
        // Warning: moderate throttle (50% rate)
        set_meter_rate(dst_hash, RATE_50_PERCENT);
    } else {
        // Healthy: full rate
        set_meter_rate(dst_hash, RATE_100_PERCENT);
    }
    
    apply_gpu_meter(dst_hash);
    
    if (meta.meter_color == COLOR_RED) {
        drop();
    }
}
```

## Embodiment 2: PID Rate Controller

The step-threshold approach of Embodiment 1 causes "bang-bang" oscillations: the switch slams the brakes, voltage recovers, switch releases, voltage crashes again. The PID controller provides smooth, stable rate adjustment.

### 2.1 Controller Design

The PID controller computes a rate adjustment based on the error between current voltage and target voltage:

    control_signal = Kp × error + Ki × ∫error dt + Kd × d(error)/dt

Where:
- error = voltage_health_normalized - target_health (e.g., target = 12/15 = 0.80)
- Kp = 500 (proportional gain—strong response to current error)
- Ki = 50 (integral gain—eliminates steady-state error)
- Kd = 5 (derivative gain—damps oscillations)

The control signal adjusts the egress rate limit:

    rate_limit = base_rate + clip(control_signal, -90%, +50%)

### 2.2 Simulation Results

From `02_Telemetry_Loop/variations/02_pid_rate_control.py`:

| Metric | Step Threshold | PID Controller | Improvement |
|--------|---------------|----------------|-------------|
| Oscillations during recovery | 4-6 cycles | 0 | Eliminated |
| Average throughput | 70 Gbps | 91 Gbps | +30% |
| Time to stable voltage | 120 ms | 45 ms | 2.7x faster |
| Voltage undershoot | 0.78V | 0.84V | Safer |

### 2.3 Hardware Implementation

The PID controller can be implemented in:
- **Control plane software:** Low-rate updates (1 kHz) via switch SDK.
- **P4 extern:** Custom register logic for kHz-rate control within the data plane.
- **Co-processor:** ARM core in switch SoC running a tight control loop.

The preferred embodiment uses a hybrid approach: the P4 data plane performs per-packet telemetry extraction and metering, while a control plane PID loop adjusts meter rates at 1 kHz.

## Embodiment 3: Gradient Preemption (dv/dt Detection)

Step thresholds and PID controllers both react to current health levels. Gradient preemption predicts FUTURE health by analyzing the rate of change.

### 3.1 Slope Detection Logic

At each telemetry update, the switch computes:

    dHealth/dt = (health[t] - health[t-1]) / Δt

If the slope is negative and steep (e.g., dHealth/dt < -0.5 per millisecond), the switch preemptively throttles BEFORE the threshold is crossed.

### 3.2 Early Warning Example

From `02_Telemetry_Loop/variations/03_gradient_preemption.py`:

Consider a GPU whose voltage is dropping at 5 mV/ms:
- At t=0: health=15, voltage=0.95V
- At t=50ms: health=10, voltage=0.90V (still "good")
- At t=100ms: health=5, voltage=0.85V (would cross threshold)

**Reactive (threshold at health=8):** Throttles at t=70ms
**Gradient Preemption (slope threshold):** Throttles at t=20ms

Gradient preemption provides 50ms earlier intervention—enough time for 50,000 packets at 1 Mpps, preventing tens of thousands of dropped packets.

### 3.3 Simulation Results

| Metric | Reactive Threshold | Gradient Preemption | Improvement |
|--------|-------------------|---------------------|-------------|
| Time to throttle | 70 ms | 20 ms | 50 ms earlier |
| Minimum voltage reached | 0.82V | 0.89V | Safer |
| Packets dropped during transition | 50,000 | 0 | Eliminated |

## Embodiment 4: Collective Guard (Application-Aware QoS)

In AI training, not all traffic is equal. "Collective" synchronization traffic (AllReduce, AllGather) gates the progress of thousands of GPUs, while "Bulk" checkpoint traffic can tolerate delays of seconds or minutes.

### 4.1 Traffic Classification

Traffic is classified into priority tiers based on DSCP markings or explicit tenant configuration:

| Tier | Traffic Type | Priority | Power Stress Action |
|------|--------------|----------|---------------------|
| Gold | AllReduce sync | Highest | NEVER throttle |
| Silver | Interactive compute | High | Light throttle |
| Bronze | Checkpoint/Storage | Low | Aggressive throttle |
| Background | Telemetry/Logs | Lowest | Drop if needed |

### 4.2 Selective Throttling

When voltage health drops below threshold, the switch applies tiered throttling:

```python
if health < 8:  # Warning zone
    rate_gold = 100%      # Protected
    rate_silver = 70%     # Light throttle
    rate_bronze = 20%     # Aggressive throttle
    rate_background = 0%  # Drop
```

### 4.3 Simulation Results

From `02_Telemetry_Loop/variations/06_collective_guard.py`:

During a simulated power stress event from a bulk storage burst:
- Collective (Gold) throughput: 100% maintained throughout
- Bulk (Bronze) throughput: Reduced from 120 Gbps to 10 Gbps
- Aggregate voltage: Never dropped below 0.88V (vs. 0.75V without protection)

Training job impact:
- Without Collective Guard: Training stalls for 3 minutes during voltage recovery
- With Collective Guard: Zero stall time—training continues at full speed

### 4.4 AllReduce Preservation Economics

For a 10,000-GPU training run at $5/GPU-hour:
- 3-minute stall = $2,500 lost compute
- Over a 1,000-step training run with 10 power events: $25,000 saved per run
- For organizations running 100 training jobs per year: $2.5M annual savings

---

# COMPLETE PATENT FAMILY SUMMARY

The In-Band Telemetry Loop patent family comprises 10 distinct variations, each independently patentable:

| Variation | Mechanism | Key Benefit | Claim Focus |
|-----------|-----------|-------------|-------------|
| 2.1 | Quantized Feedback | Low-cost switch logic | 4-bit encoding, no FPU |
| 2.2 | PID Rate Control | Oscillation-free recovery | Control theory stability |
| 2.3 | Gradient Preemption | Crash prevention | dv/dt slope detection |
| 2.4 | Tenant Flow Sniper | Multi-tenant SLA | Per-tenant health tracking |
| 2.5 | Graduated Penalties | Soft-landing recovery | Progressive rate reduction |
| 2.6 | Collective Guard | Training job protection | AllReduce prioritization |
| 2.7 | QP-Spray Aggregator | Evasion-proof isolation | Queue-pair aggregation |
| 2.8 | Stability Analysis | Phase-margin guarantee | Bode plot stability proof |
| 2.9 | Workload Intensity | Non-linear adaptation | Workload-aware control |
| 2.10 | Adversarial Guard | Anti-spoofing security | Telemetry authentication |

---

# SIMULATION DATA AND VALIDATION

The following empirical data is derived from the implementations in `02_Telemetry_Loop/`:

## Aggregate Performance Metrics

| Metric | Baseline (No Telemetry) | With In-Band Telemetry | Improvement |
|--------|------------------------|------------------------|-------------|
| Voltage excursions (per hour) | 12 | 0 | Eliminated |
| Average throughput | 78 Gbps | 97 Gbps | +24% |
| Training checkpoint interrupts | 8/day | 0 | Eliminated |
| Straggler rate (AllReduce) | 5.2% | 0.3% | 17x better |
| Mean time to voltage recovery | 250 ms | 45 ms | 5.5x faster |

## Control Loop Stability

The PID controller stability was verified via Bode plot analysis (`02_Telemetry_Loop/variations/08_stability_bode_analysis.py`):

| Parameter | Value | Significance |
|-----------|-------|--------------|
| Gain Margin | 12 dB | Robust stability |
| Phase Margin | 60° | No oscillation risk |
| Crossover Frequency | 100 Hz | Tracks fast transients |
| Settling Time | 45 ms | Fast recovery |

## Adversarial Resistance

The Adversarial Guard variation (`02_Telemetry_Loop/variations/10_adversarial_guard.py`) prevents malicious tenants from spoofing telemetry:

| Attack Vector | Without Guard | With Guard |
|--------------|---------------|------------|
| Fake "healthy" telemetry | GPU crashes from unthrottled traffic | Detected via hardware attestation |
| Fake "critical" telemetry | Legitimate traffic throttled | Rate-limited per-tenant telemetry trust |
| Telemetry replay attack | Stale telemetry causes incorrect rates | Sequence numbers prevent replay |

---

# CLAIMS

## Independent Claims

**Claim 1. A method for network-driven GPU power management using in-band telemetry, comprising:**
(a) at a GPU, measuring current voltage from a voltage regulator module (VRM);
(b) quantizing the measured voltage to a health score on a discrete scale;
(c) encoding the health score into a portion of the IPv6 Flow Label field of outgoing network packets;
(d) transmitting said packets to a network switch;
(e) at the network switch, parsing the IPv6 header and extracting the health score from the Flow Label;
(f) adjusting an egress rate limit for traffic destined to the GPU based on the extracted health score;
whereby the switch prevents voltage crashes by reducing traffic to GPUs exhibiting power stress.

**Claim 2. A programmable network switch configured for in-band power telemetry processing, comprising:**
(a) a parser stage configured to extract a voltage health value from the low-order bits of an IPv6 Flow Label field at line rate;
(b) a register array storing per-destination voltage health state;
(c) a metering stage configured to rate-limit traffic based on stored voltage health;
(d) control logic configured to adjust meter rates according to a configurable control algorithm;
wherein the switch processes telemetry with zero additional latency compared to standard packet forwarding.

**Claim 3. A system for closed-loop network power management, comprising:**
(a) a plurality of GPUs, each configured to insert voltage health telemetry into outgoing packet headers;
(b) a network switch configured to extract said telemetry and implement adaptive rate control;
(c) a PID controller configured to compute rate adjustments based on accumulated telemetry;
(d) a feedback path wherein rate adjustments cause corresponding changes in GPU voltage, which are reflected in subsequent telemetry;
wherein the closed loop stabilizes GPU voltage without oscillation.

**Claim 4. A method for application-aware power-based traffic prioritization, comprising:**
(a) classifying network traffic into priority tiers based on application type;
(b) receiving in-band voltage health telemetry from destination GPUs;
(c) when voltage health drops below a threshold, selectively throttling lower-priority traffic while maintaining full rate for higher-priority traffic;
(d) wherein collective synchronization traffic (AllReduce) is classified as highest priority and never throttled during power stress events.

## Dependent Claims

**Claim 5.** The method of Claim 1, wherein the health score is a 4-bit integer occupying bits 0-3 of the 20-bit IPv6 Flow Label field.

**Claim 6.** The method of Claim 1, wherein the health score encoding comprises at least 5 discrete levels corresponding to voltage ranges: excellent, good, warning, critical, and emergency.

**Claim 7.** The method of Claim 1, wherein the GPU inserts the health score using dedicated hardware in the GPU's network interface controller (NIC).

**Claim 8.** The switch of Claim 2, wherein the control algorithm is a step-threshold algorithm that applies discrete rate limits at predefined health thresholds.

**Claim 9.** The switch of Claim 2, wherein the control algorithm is a proportional-integral-derivative (PID) controller that computes continuous rate adjustments.

**Claim 10.** The switch of Claim 2, wherein the control algorithm is a gradient preemption algorithm that throttles based on the rate of change (dHealth/dt) of the health value rather than its absolute level.

**Claim 11.** The switch of Claim 2, wherein the register array is keyed by destination IP address, enabling per-GPU health tracking.

**Claim 12.** The switch of Claim 2, wherein the register array is keyed by a combination of destination IP address and tenant identifier, enabling per-tenant health tracking in multi-tenant environments.

**Claim 13.** The system of Claim 3, wherein the PID controller is implemented in the switch's control plane and adjusts meter rates at a frequency of at least 1 kHz.

**Claim 14.** The system of Claim 3, further comprising a stability verification module that computes gain and phase margins to ensure oscillation-free operation.

**Claim 15.** The system of Claim 3, wherein the closed loop achieves voltage stabilization within 50 milliseconds of a power disturbance.

**Claim 16.** The method of Claim 4, wherein priority tiers comprise at least: Gold (AllReduce synchronization), Silver (interactive compute), and Bronze (checkpoint/storage).

**Claim 17.** The method of Claim 4, wherein Bronze-tier traffic is reduced to less than 25% of baseline rate during power stress while Gold-tier traffic maintains 100% rate.

**Claim 18.** The method of Claim 4, further comprising monitoring training job progress to verify that collective operations complete without straggler delays during power stress events.

**Claim 19.** The method of Claim 1, further comprising cryptographic authentication of telemetry values to prevent spoofing by malicious tenants.

**Claim 20.** The method of Claim 1, wherein the voltage health telemetry is inserted into every ACK packet transmitted by the GPU, providing kHz-rate telemetry updates.

---

# ABSTRACT

A system and method for in-band network telemetry that enables closed-loop GPU power management. GPUs insert voltage health status (a 4-bit integer representing current VRM voltage) into the low-order bits of the IPv6 Flow Label field of every outgoing packet. Network switches extract this telemetry at line rate using programmable P4 pipelines and implement adaptive rate control to prevent voltage crashes. Multiple control algorithms are disclosed: step-threshold for simple deployments, PID controllers for oscillation-free stability, and gradient preemption for predictive intervention based on voltage slope (dv/dt) rather than absolute level. An application-aware QoS extension (Collective Guard) selectively throttles low-priority traffic during power stress while protecting high-value AllReduce synchronization flows. The system eliminates voltage excursions, improves average throughput by 24%, and provides 17x improvement in AI training straggler rates. Complete P4 reference implementations and simulation results are provided, demonstrating line-rate telemetry extraction, closed-loop stability (60° phase margin), and adversarial resistance to telemetry spoofing attacks.

---

# FIGURES

**Figure 1:** PID rate control simulation showing smooth voltage recovery without oscillations
(See: `02_Telemetry_Loop/artifacts/02_pid_control.png`)

**Figure 2:** Gradient preemption showing 50ms earlier intervention than reactive thresholds
(See: `02_Telemetry_Loop/artifacts/03_gradient_preemption.png`)

**Figure 3:** Collective Guard showing protected AllReduce throughput during power stress
(See: `02_Telemetry_Loop/artifacts/06_collective_guard.png`)

**Figure 4:** Bode plot showing PID controller stability margins
(See: `02_Telemetry_Loop/artifacts/08_stability_bode.png`)

**Figure 5:** Adversarial guard demonstrating spoofing detection
(See: `02_Telemetry_Loop/artifacts/10_adversarial_guard.png`)

---

# INCORPORATION BY REFERENCE

The following materials are incorporated by reference:

1. P4 reference implementation: `02_Telemetry_Loop/variations/reference.p4`
2. Master tournament runner: `02_Telemetry_Loop/master_tournament.py`
3. PID controller variation: `02_Telemetry_Loop/variations/02_pid_rate_control.py`
4. Gradient preemption variation: `02_Telemetry_Loop/variations/03_gradient_preemption.py`
5. Collective guard variation: `02_Telemetry_Loop/variations/06_collective_guard.py`
6. Stability analysis: `02_Telemetry_Loop/variations/08_stability_bode_analysis.py`
7. Adversarial guard: `02_Telemetry_Loop/variations/10_adversarial_guard.py`
8. All generated artifacts in `02_Telemetry_Loop/artifacts/`

---

# PRIORITY CLAIM

This provisional application establishes a priority date for the disclosed subject matter under 35 U.S.C. § 119(e).

---

*END OF PROVISIONAL PATENT APPLICATION - FAMILY 2*
