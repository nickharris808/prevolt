# TTH-to-UCIe Mapping Specification
**Version:** 1.0  
**Status:** Draft Standard for Chiplet Interoperability  
**Date:** December 2025  

---

## 1. Executive Summary

This document defines the mapping of the **Temporal Thermal Handshake (TTH)** protocol onto the **Universal Chiplet Interconnect Express (UCIe)** physical and link layers. This specification enables heterogeneous chiplets (e.g., Logic, Memory, Analog) from different vendors to negotiate thermal budgets in real-time, preventing cascading failures in 3D-stacked packages (CoWoS, SoIC).

---

## 2. Protocol Mapping (Stack Layer)

TTH packets are mapped to the UCIe **Link Layer (FDI)** using specific **Message Classes** within the UCIe Sideband or Mainband flits.

### 2.1 Sideband Mapping (Low Latency / High Priority)
For critical **Compute-Inhibit (CI)** and **Thermal-Deflection (TD)** signals, TTH utilizes the UCIe Sideband Message Interface.

| TTH Signal | UCIe Sideband OpCode | Payload (Bits) | Priority |
| :--- | :--- | :--- | :--- |
| **CI_ASSERT** | 0x80 (Custom Vendor) | [31:0] Core_ID, [63:32] Duration | 0 (Emergency) |
| **TC_GRANT** | 0x81 (Custom Vendor) | [31:0] Credit_Value | 1 (Real-time) |
| **T_TELEMETRY**| 0x82 (Custom Vendor) | [15:0] Temp_mC, [31:16] TTV_us | 2 (Monitoring) |

### 2.2 Mainband Flit Mapping (High Bandwidth / Orchestration)
For non-critical thermal budget negotiation and "Market-Aware" metadata, TTH utilizes **Standard flit headers** in the UCIe streaming mode.

---

## 3. Heterogeneous Negotiation (HBM Shield)

### 3.1 Logic-to-Memory (HBM3e) Handshake
The Logic die (Master) must request a **Thermal Clearance Token** from the HBM die (Slave) before initiating a high-current GEMM burst that would laterally heat the memory cells.

**Constraint:** HBM dies exhibit bit-flip errors if junction temperature exceeds **85°C**. AIPP-T maintains this "Thermal Shield" by inhibiting Logic cycles if HBM telemetry predicts a violation.

---

## 4. Hardware Requirements (The UCIe Adapter)

Implementations must include a **TTH-to-UCIe Bridge (Bus Adapter)** that performs:
1.  **Serialization:** Converting TTH registers to UCIe flits.
2.  **Priority Arbitration:** Ensuring CI_ASSERT packets bypass standard data traffic.
3.  **Clock-Domain Synchronization:** Crossing between the AIPP-T controller clock and the UCIe high-speed SerDes clock.

---

## 5. Monopoly Claim: The Inter-Vendor Lock-In

By standardizing TTH onto UCIe, AIPP-T becomes the **mandatory safety layer for all multi-vendor chiplet systems**. 

- **Vendor A (Nvidia GPU)** cannot communicate with **Vendor B (Micron HBM)** without the TTH Bus Adapter.
- Any chiplet lacking the TTH-UCIe bridge is excluded from the high-performance 3D-IC ecosystem due to thermal liability.

**Status:** This specification is the "Constitutional Authority" for the Chiplet Era.
