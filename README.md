# Prevolt.io

**Predictive Power Orchestration for AI Infrastructure**

---

## What Is Prevolt?

Prevolt solves the fundamental latency mismatch in AI data center power delivery: GPUs draw 500A in 1µs, but voltage regulators respond in 15µs. The 14µs gap causes voltage collapse, crashes, and GPU damage.

**The Innovation:** Network switches see compute traffic 14µs before it reaches GPUs. Prevolt uses this visibility window to pre-charge voltage regulators, maintaining stable 0.90V instead of crashing at 0.69V.

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run full validation suite (56+ components)
python validation/test_suite.py

# Expected: 56/59 components passing
```

---

## Repository Structure

```
prevolt/
├── src/                        # Core implementations
│   ├── power/                  # Power management
│   │   ├── precharge_trigger/  # Network-driven VRM pre-charge
│   │   ├── power_gated_dispatch/ # Token-based compute gating
│   │   ├── grid_vpp/           # Grid frequency participation
│   │   └── ...
│   ├── network/                # Network orchestration
│   │   ├── telemetry_loop/     # IPv6 health embedding
│   │   ├── spectral_damping/   # Transformer resonance protection
│   │   ├── incast_backpressure/ # Memory flow control
│   │   └── cxl_sideband/       # CXL sideband signaling
│   ├── thermal/                # Thermal management
│   │   ├── orchestration/      # Cooling coordination
│   │   └── ...
│   ├── memory/                 # Memory systems
│   │   ├── orchestration/      # HBM refresh sync
│   │   └── noisy_neighbor/     # Multi-tenant isolation
│   ├── optical/                # Optical synchronization
│   │   └── phase_lock/         # Femtosecond timing sync
│   └── advanced/               # Experimental components
│
├── silicon/                    # Hardware implementations
│   ├── rtl/                    # Synthesizable Verilog (11 modules)
│   └── implementation/         # ASIC integration
│
├── validation/                 # Testing & verification
│   ├── test_suite.py          # Master validation (56+ components)
│   ├── standards/             # UEC protocol specs
│   └── compliance/            # Compliance testing
│
├── tools/                      # Utilities
│   ├── physics/               # Shared physics engines
│   └── utilities/             # Helper scripts
│
├── docs/                       # Documentation
│   ├── technical/             # Technical deep-dives
│   ├── due_diligence/         # Validation reports
│   └── whitepapers/           # Architecture docs
│
└── artifacts/                  # Generated figures & proofs
```

---

## Core Technologies

| Technology | Component | Purpose |
|-----------|-----------|---------|
| **PySpice** | VRM modeling | SPICE circuit simulation with non-linear inductors |
| **SimPy** | Network simulation | Discrete-event modeling of incast traffic |
| **Z3 SMT Solver** | Formal proofs | Deadlock-freedom verification |
| **Verilog RTL** | Hardware | 11 synthesizable modules @ 5nm |
| **Cocotb** | Verification | Hardware testbenches |
| **NumPy/SciPy** | Signal processing | FFT, Kalman filters, control theory |

---

## Key Innovations

### 1. **Pre-Cognitive Voltage Trigger**
- Network switch buffers packets for 14µs
- Pre-charges VRM before compute traffic arrives
- Prevents voltage collapse: 0.90V (safe) vs 0.69V (crash)
- **Status:** Production-ready simulation

### 2. **Spectral Resonance Damping**
- Network jitter spreads power spectrum
- Prevents transformer mechanical resonance
- 20.2 dB peak suppression (100× stress reduction)
- **Status:** Field-tested concept

### 3. **Memory-Initiated Backpressure**
- Memory controller signals NIC directly
- 210ns latency (25× faster than ECN)
- Eliminates packet loss during incast
- **Status:** SimPy validation complete

### 4. **Coherent Phase-Locked Networking**
- Locks to optical carrier frequency (193.4 THz)
- 10 femtosecond jitter (5,000× better than PTP)
- Enables cycle-accurate distributed computing
- **Status:** Physics simulation validated

### 5. **Hardware Compute-Inhibit Interlock**
- Extended Kalman Filter thermal prediction
- Blocks instruction dispatch before thermal crisis
- Z3-proven deadlock-free routing
- ASIL-D safety certification ready
- **Status:** Comprehensive enablement

---

## Validation Status

**56/59 components passing** (95.7%)

Failed components:
- `08_Thermal_Orchestration/two_phase_cooling_physics.py` - Thermodynamic model needs refinement
- `src/thermal/.../iso_performance` - Integration pending
- `src/thermal/.../thermal_puf` - Integration pending

---

## Technology Stack

**Languages:**
- Python 3.11+ (30,000+ lines)
- Verilog (2,000+ lines RTL)
- Markdown (documentation)

**Key Libraries:**
- NumPy, SciPy, Matplotlib (signal processing & visualization)
- SimPy (discrete-event network simulation)
- PySpice (SPICE circuit modeling)
- Z3-solver (formal verification)
- Cocotb (hardware verification)

**Hardware Targets:**
- TSMC 5nm process (timing-closed @ 1GHz)
- Xilinx UltraScale+ FPGA (prototyping)

---

## Documentation

| Audience | Document |
|----------|----------|
| **Quick Start** | [`docs/START_HERE.md`](docs/START_HERE.md) |
| **Technical Deep-Dive** | [`docs/due_diligence/`](docs/due_diligence/) |
| **Whitepapers** | [`whitepapers/`](whitepapers/) |
| **Validation Reports** | [`validation/`](validation/) |

---

## Use Cases

### Data Center Operators
- Prevent GPU voltage collapse in AI clusters
- Reduce transformer fatigue from spectral peaks
- Coordinate power draw with grid frequency

### Cloud Providers
- Multi-tenant memory isolation (noisy neighbor prevention)
- Hardware-enforced power budgets
- Sub-microsecond flow control

### Hardware Vendors
- Network-driven thermal management
- Optical phase-locked synchronization
- ASIL-D certified thermal interlocks

---

## Contributing

This is a research portfolio. Components are provided as-is for evaluation and validation.

For questions or collaboration opportunities:
- GitHub Issues: https://github.com/nickharris808/prevolt/issues
- Repository: https://github.com/nickharris808/prevolt

---

## License

© 2026 Neural Harris IP Holdings. All Rights Reserved.

This repository contains technical implementations supporting patent applications. Patent rights are reserved. Source code is provided for technical evaluation only.

---

## Citation

If you reference this work, please cite:

```
Harris, N. (2026). Prevolt: Network-Causal Power Orchestration for AI Data Centers.
GitHub repository: https://github.com/nickharris808/prevolt
```

---

**Prevolt.io** - Preventing voltage collapse through network orchestration.
