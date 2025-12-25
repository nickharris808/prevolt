# AIPP Hardware Interface Specification (v1.0)
## Formal Definition of GPU-to-Switch & Switch-to-VRM Signaling

**Status:** ✅ RESOLVED (Technical Gap 2)
**Objective:** Define physical and logical interfaces to remove "Integration Assumptions."

---

## 1. Physical Layer (PHY)

### 1.1 Switch-to-GPU (Egress)
- **Primary Channel:** Standard Ethernet (800G/1.6T)
- **AIPP Signal Channel:** 
  - **In-Band:** IPv6 Flow Label (20-bit) or TCP Option (0x1A)
  - **Side-Band (Optional):** LVDS pairs on specialized backplanes for <50ns jitter.

### 1.2 GPU-to-VRM (Local)
- **Interface:** PCIe VDM (Vendor Defined Messages) or 1.8V GPIO.
- **Latency:** Must be <10ns from GPU pin to VRM controller interrupt.

---

## 2. Protocol Frame Format

| Bit Range | Field | Description |
|-----------|-------|-------------|
| 0:7       | Intensity | 8-bit quantized load prediction (0-255) |
| 8:23      | Delay_ns | 16-bit requested buffer time in nanoseconds |
| 24:31     | Token_ID | Unique identifier for cryptographic billing |

---

## 3. Timing Requirements

1. **Detection Latency:** Switch must parse AIPP header in <15ns.
2. **Buffer Jitter:** Packet release jitter must be <1ns (FPGA-enforced).
3. **VRM Ramp-up:** Trigger must precede load by at least $T_{ramp} - T_{prop}$.

---

## 4. Compliance Matrix

| Vendor | Component | Requirement |
|--------|-----------|-------------|
| Nvidia | GPU CP | Must emit AIPP header 20us before GEMM launch |
| Broadcom | Tomahawk | Must implement AIPP Priority Queue (14us deep) |
| Vicor | VRM | Must support Feed-Forward Setpoint Adjustment |

---

**© 2025 Neural Harris IP Holdings. Proprietary Specification.**



