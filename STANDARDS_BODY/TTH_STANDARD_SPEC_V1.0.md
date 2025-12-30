# Temporal Thermal Handshake (TTH) Protocol Specification
**Version:** 1.0  
**Status:** Draft Standard  
**Date:** December 2025  
**Authors:** AIPP-T Technical Working Group

---

## 1. Introduction

### 1.1 Purpose
This specification defines the **Temporal Thermal Handshake (TTH) Protocol**, a standardized interface between Operating System schedulers and 3D-IC thermal controllers. The protocol enables predictive thermal management by establishing a common language for thermal constraint negotiation.

### 1.2 Scope
The TTH protocol applies to:
- 3D-Integrated Circuits (3D-ICs) with ≥2 stacked dies
- Multi-core processors with heterogeneous thermal profiles
- AI accelerators operating near thermal design power (TDP)
- Any system requiring deterministic thermal guarantees

### 1.3 Definitions

- **Thermal Window (TW)**: A time interval during which a compute core is guaranteed to remain below a specified temperature threshold.
- **Time-to-Violation (TTV)**: The predicted time until a core reaches its critical temperature at current power trajectory.
- **Thermal Credit (TC)**: A quantized unit of "heat budget" allocated to a task.
- **Compute-Inhibit (CI)**: A hardware-enforced pause signal that prevents instruction dispatch when thermal safety is violated.

---

## 2. Protocol Architecture

### 2.1 System Model

```
┌─────────────────────────────────────────────────┐
│          Operating System Scheduler             │
│  (Linux CFS, Windows, RTOS, Hypervisor)         │
└─────────────────┬───────────────────────────────┘
                  │ TTH API (Section 3)
                  ▼
┌─────────────────────────────────────────────────┐
│       AIPP-T Thermal Controller (Hardware)      │
│  ┌──────────────┐  ┌──────────────┐            │
│  │ Virtual      │  │ Predictive   │            │
│  │ Current      │  │ Governor     │            │
│  │ Sensor       │  │ (TTV Calc)   │            │
│  └──────────────┘  └──────────────┘            │
└─────────────────┬───────────────────────────────┘
                  │ Hardware Interlocks
                  ▼
┌─────────────────────────────────────────────────┐
│       3D-IC Silicon (Cores, NoC, TSVs)          │
└─────────────────────────────────────────────────┘
```

### 2.2 Communication Flow

1. **Request Phase**: OS requests a Thermal Window for a task.
2. **Prediction Phase**: Controller calculates TTV based on current thermal state.
3. **Grant/Deny Phase**: Controller returns a Thermal Credit or Inhibit signal.
4. **Execution Phase**: Task executes within granted thermal constraints.
5. **Feedback Phase**: Controller updates thermal state and broadcasts to OS.

---

## 3. API Specification

### 3.1 Core Data Structures

```c
typedef struct {
    uint32_t core_id;          // Physical core identifier
    uint32_t task_id;          // OS task/thread identifier
    uint64_t power_signature;  // Expected power profile (mW)
    uint32_t duration_us;      // Requested execution time (μs)
    uint8_t  priority;         // Thermal priority (0-255)
} tth_request_t;

typedef struct {
    uint32_t core_id;
    int32_t  temperature_mC;   // Current junction temp (milliCelsius)
    uint32_t ttv_us;           // Time-to-Violation (μs)
    uint32_t thermal_credit;   // Granted heat budget
    uint8_t  inhibit_flag;     // 1 = Compute-Inhibit active
} tth_response_t;

typedef struct {
    uint32_t core_id;
    int32_t  predicted_temp_mC; // Predicted peak temperature
    uint32_t confidence_pct;    // Prediction confidence (0-100)
    uint64_t timestamp_ns;      // Nanosecond timestamp
} tth_telemetry_t;
```

### 3.2 API Functions

#### 3.2.1 Request Thermal Window
```c
int tth_request_window(const tth_request_t *req, tth_response_t *resp);
```
**Description:** OS requests permission to execute a task with specified power profile.  
**Returns:** 
- `0` on success (thermal credit granted)
- `-EAGAIN` if core is currently inhibited
- `-EINVAL` if request parameters are invalid

#### 3.2.2 Query Thermal State
```c
int tth_query_state(uint32_t core_id, tth_telemetry_t *telemetry);
```
**Description:** Polls the current and predicted thermal state of a core.  
**Returns:** `0` on success, `-ENODEV` if core_id is invalid.

#### 3.2.3 Register Callback (Asynchronous)
```c
int tth_register_callback(void (*callback)(const tth_telemetry_t *));
```
**Description:** Register a function to receive thermal event notifications (e.g., approaching TTV).

---

## 4. Thermal Credit Allocation Algorithm

### 4.1 Velocity-Adjusted Credit

The Thermal Credit is calculated as:

```
TC = min(TC_max, (T_limit - T_current) / (dT/dt * latency_migration))
```

Where:
- `TC_max`: Maximum credit (platform-dependent)
- `T_limit`: Critical temperature threshold (typically 105°C)
- `T_current`: Current junction temperature
- `dT/dt`: Thermal velocity (°C/s)
- `latency_migration`: OS task migration latency (typically 2ms)

### 4.2 Credit Depletion

Each instruction consumes credit proportional to its power signature:
```
Credit_remaining -= (Power_instruction * Time_execution) / Thermal_Capacitance
```

When `Credit_remaining ≤ 0`, the Compute-Inhibit signal is asserted.

---

## 5. Hardware Requirements

### 5.1 Mandatory Features
1. **Virtual Current Sensor**: Predict temperature from current within 1ms.
2. **Compute-Inhibit Gate**: Hardware-enforced instruction pause.
3. **Thermal Deflection Router**: NoC routing that avoids hot cores.

### 5.2 Optional Features
1. **Precision-for-Frequency Scaling**: Iso-Performance mode.
2. **Atomic Stress Tracking**: TSV electromigration monitoring.

---

## 6. Formal Guarantees

The TTH protocol provides the following mathematically proven invariants:

### 6.1 Safety
```
∀ t, cores[c].temperature(t) < T_critical
```
**Proof:** Hardware Compute-Inhibit prevents execution when predicted temperature exceeds limit (See Section 5, Week 5 formal verification).

### 6.2 Liveness
```
∀ task, ∃ t_exec : task.execute(t_exec)
```
**Proof:** Finite cooling cycles ensure every task receives a thermal window (See formal_proof.py).

### 6.3 Deadlock-Freedom
```
¬∃ state : NoC.blocked ∧ ∀ ports, thermal_inhibit[port] = true
```
**Proof:** Global orchestrator guarantees ≥2 cold buffer ports (See aipp_t_noc_router.v).

---

## 7. Implementation Guidelines

### 7.1 OS Integration & Safety Core Pool
- **Linux:** Integrate with CFS scheduler via `sched_class` hooks.
- **Windows:** Implement as kernel-mode driver (KMDF).
- **RTOS:** Use priority-based thermal credits in rate-monotonic scheduling.
- **Livelock Prevention:** The Global Orchestrator must maintain a **"Safety Core Pool"**—at least one core that is guaranteed to be both thermally cold (not inhibited) and ready (available buffer space) to ensure NoC progress even under extreme backpressure.

### 7.2 Power Model Calibration
Each platform must calibrate the `power_signature` mapping:
1. Run microbenchmarks for each instruction class (ALU, SIMD, Memory).
2. Measure steady-state power using on-die current sensors.
3. Store in platform-specific lookup table (LUT).

---

## 8. Compliance & Certification

### 8.1 Conformance Levels
- **Level 1 (Basic)**: Implements tth_request_window() and tth_query_state().
- **Level 2 (Advanced)**: Adds asynchronous callbacks and predictive telemetry.
- **Level 3 (Full)**: Includes formal verification and multi-die orchestration.

### 8.2 Testing Requirements
Implementations must pass:
1. **Unit Tests**: API correctness (100 test cases minimum).
2. **Integration Tests**: Multi-core thermal stress (1000-core scale).
3. **Formal Verification**: Z3 proof of safety invariants.

---

## 9. Security Considerations

### 9.1 Thermal Side-Channels
The TTH protocol does NOT expose raw temperature data to unprivileged processes. All telemetry is quantized to prevent thermal side-channel attacks (e.g., inferring cryptographic keys from power traces).

### 9.2 Denial-of-Service
Malicious tasks cannot exhaust thermal credits of other cores due to per-task credit accounting and hardware priority enforcement.

### 9.3 Thermal PUF Protocol
The hardware extracts a unique digital signature from manufacturing-specific thermal decay characteristics (Physical Unclonable Function). This signature serves as the root-of-trust for:
- Secure Boot verification.
- Remote Attestation for cloud workloads.
- Anti-counterfeiting verification.

---

## 10. Deployment Vector: Shadow Mode
AIPP-T implementations should support a non-invasive **"Shadow Mode"** for zero-risk adoption:
- The controller monitors and logs thermal events without overriding legacy control signals.
- Discrepancy logs (near-miss events) provide quantified proof of value before full activation.

---

## 11. Economic Vector: Market-Aware Scheduling
The protocol supports priority-based metadata enabling "Market-Aware" compute arbitrage:
- **Premium SLA:** Guaranteed thermal windows on "Excellent" silicon cores.
- **Spot SLA:** Discounted compute on "Marginal" cores rescued by AIPP-T predictive gating.

---

## 12. Future Extensions

### 12.1 Multi-Die Coordination (TTH v2.0)
Extend the protocol to negotiate thermal budgets across multiple 3D-stacked chiplets in a heterogeneous package.

### 12.2 AI-Driven Prediction
Replace the Kalman Filter with a lightweight neural network for workload-specific thermal prediction.

---

## Appendix A: Packet Format

### A.1 Request Packet (64 bytes)
```
Offset  | Size | Field
--------|------|------------------
0x00    | 4    | Magic (0x54544801)
0x04    | 4    | core_id
0x08    | 4    | task_id
0x0C    | 8    | power_signature
0x14    | 4    | duration_us
0x18    | 1    | priority (Market Metadata)
0x19    | 7    | Reserved
0x20    | 32   | Extension (future)
0x40    | 4    | CRC32
```

### A.2 Response Packet (64 bytes)
```
Offset  | Size | Field
--------|------|------------------
0x00    | 4    | Magic (0x54544802)
0x04    | 4    | core_id
0x08    | 4    | temperature_mC
0x0C    | 4    | ttv_us
0x10    | 4    | thermal_credit
0x14    | 1    | inhibit_flag
0x15    | 3    | Reserved
0x18    | 8    | timestamp_ns
0x20    | 32   | Extension (future)
0x40    | 4    | CRC32
```

---

## Appendix B: References

1. Black, J.R. "Electromigration Failure Modes in Aluminum Metallization for Semiconductor Devices," Proceedings of the IEEE, 1969.
2. Borkar, S., Karnik, T., "The Future of Microprocessors," IEEE, 2011.
3. Kandlikar, S.G., "Fundamental Issues Related to Flow Boiling in Minichannels and Microchannels," Experimental Thermal and Fluid Science, 2002.
4. Rabaey, J.M., "Low Power Design Essentials," Springer, 2009.

---

**End of TTH Protocol Specification v1.0**

