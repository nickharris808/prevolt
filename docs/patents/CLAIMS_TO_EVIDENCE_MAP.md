# CLAIMS-TO-EVIDENCE MAPPING MATRIX
## Patent Claims Cross-Referenced to Validation Data

**Date:** December 27, 2025  
**Purpose:** Direct traceability between patent claims and technical proof  
**Classification:** CONFIDENTIAL - Patent Prosecution Work Product

---

## How to Use This Document

For each patent claim, this matrix provides:
1. **Claim Text** — The exact functional claim language
2. **Evidence File** — The specific Python/Verilog file proving the claim
3. **Key Metric** — The quantitative result validating the claim
4. **Line Reference** — Exact code location (where applicable)
5. **Artifact** — Visual proof (PNG figure)

**Purpose for Legal Team:** When an examiner asks "Where is the enablement for Claim 14?", you point to this map → Row 14 → `spice_vrm.py:124`.

---

## FAMILY 1: PRE-COGNITIVE VOLTAGE TRIGGER (47 Claims)

### Independent Claims (1-4)

| Claim # | Claim Element | Evidence File | Key Metric | Code Line | Artifact |
|---------|---------------|---------------|------------|-----------|----------|
| **1** | Method for coordinated power delivery via network-layer packet scheduling coupled to VRM dynamics | `01_PreCharge_Trigger/spice_vrm.py` | 0.687V→0.900V | Lines 140-234 | `voltage_trace.png` |
| **1(a)** | Packet classification via RDMA opcode/payload/DSCP | `02_Telemetry_Loop/variations/reference.p4` | IPv6 Flow Label parsing | Lines 95-99 | N/A |
| **1(b)** | Lead time = f(characteristic response time) | `01_PreCharge_Trigger/spice_vrm.py` | τ = 15µs → lead = 14µs | Line 70 | N/A |
| **1(c)** | Simultaneous trigger + hold | `14_ASIC_Implementation/aipp_fpga_trigger.v` | <1ns trigger assertion | Lines 20-28 | N/A |
| **1(d)** | Release after handshake OR timer | `01_PreCharge_Trigger/spice_vrm.py` | Both modes implemented | Lines 88-137 | N/A |
| **1(f)** | Packet-absent clamp (OVP prevention) | `01_PreCharge_Trigger/limp_mode_validation.py` | 1.18V safe (vs 1.35V trip) | Lines 60-85 | `safety_clamp.png` |
| **1(g)** | Trigger-absent limp mode | `01_PreCharge_Trigger/limp_mode_validation.py` | 0.85V limp vs 0.68V crash | Lines 30-55 | `limp_mode_safety.png` |
| **2** | System with network node, VRM, bidirectional signaling, fail-safe logic | `14_ASIC_Implementation/aipp_omega_top.v` | Full system integration | Lines 1-87 | N/A |
| **3** | Closed-loop handshake method | `01_PreCharge_Trigger/variations/03_confidence_gated.py` | VRM confirms before release | Lines 45-78 | N/A |
| **4** | Reduced-capacitance system (≥20% reduction) | `01_PreCharge_Trigger/active_synthesis_model.py` | 15mF→1.5mF (90% reduction) | Lines 40-90 | `active_synthesis_proof.png` |

### Dependent Claims (5-47)

| Claim # | Claim Element | Evidence File | Key Metric | Code Line | Artifact |
|---------|---------------|---------------|------------|-----------|----------|
| **5** | Network node = ToR/leaf/spine switch | `10_Fabric_Orchestration/spine_power_arbiter.py` | Hierarchical coordination | Lines 20-50 | N/A |
| **6** | Network node = SmartNIC/DPU | `09_Software_SDK/pcie_full_stack_model.py` | PCIe VDM signaling | Lines 30-80 | N/A |
| **7** | Network node = Optical transceiver | `11_Optical_IO/optical_thermal_bias.py` | Optical trigger modulation | Lines 25-60 | N/A |
| **8** | Network node = FPGA in data path | `14_ASIC_Implementation/aipp_fpga_trigger.v` | 1GHz FPGA logic | Lines 1-45 | N/A |
| **9-12** | Packet classification (RDMA/Flow Label/NCCL) | `02_Telemetry_Loop/variations/reference.p4` | Header parsing | Lines 95-110 | N/A |
| **13** | Lead time = τ × (1 + k) | `01_PreCharge_Trigger/variations/02_kalman_predictor.py` | 14µs→22.4µs aging | Lines 60-120 | `02_kalman_trace.png` |
| **14** | Characteristic response time = settling time | `01_PreCharge_Trigger/spice_vrm.py` | 15µs settling to 95% | Lines 175-180 | N/A |
| **15** | Characteristic response time = LC time constant | `01_PreCharge_Trigger/spice_vrm_nonlinear.py` | τ_LC = 2π√(LC) | Line 193 | N/A |
| **16** | Periodic calibration & storage | `01_PreCharge_Trigger/variations/02_kalman_predictor.py` | Kalman state update | Lines 90-115 | N/A |
| **17** | Lead time range 5-100µs | `01_PreCharge_Trigger/master_tournament.py` | Sweep results | Lines 40-80 | `tournament_results.csv` |
| **18-21** | Release conditions (timeout/handshake/LVDS/VDM) | `01_PreCharge_Trigger/variations/03_confidence_gated.py` | Hybrid logic | Lines 50-90 | N/A |
| **22-26** | Fail-safe timing (hold time, slew, guard) | `01_PreCharge_Trigger/limp_mode_validation.py` | 200mV/µs slew rate | Lines 70-95 | N/A |
| **27-31** | Signaling paths (in-band/LVDS/VDM/optical) | `02_Telemetry_Loop/variations/reference.p4` | IPv6 Hop-by-Hop | Lines 95-99 | N/A |
| **32-35** | Capacitance reduction (30%, 50%, area, BOM) | `01_PreCharge_Trigger/active_synthesis_model.py` | $450/GPU savings | Lines 110-145 | N/A |
| **36-39** | Adaptive calibration (Kalman, aging) | `01_PreCharge_Trigger/variations/02_kalman_predictor.py` | 5-year stability | Lines 60-140 | `02_aging_adaptation.png` |
| **40-42** | System implementation (P4, VRM, GPU) | `02_Telemetry_Loop/variations/reference.p4` | Full P4 program | Lines 1-207 | N/A |
| **43-45** | Scale coordination (rack, facility) | `10_Fabric_Orchestration/spine_power_arbiter.py` | 100-GPU stagger | Lines 30-90 | N/A |
| **46-47** | Implementation media (software, ASIC) | `14_ASIC_Implementation/aipp_omega_top.v` | Top-level RTL | Lines 1-87 | N/A |

---

## FAMILY 2: IN-BAND TELEMETRY LOOP (15+ Claims)

### Core Claims

| Claim # | Claim Element | Evidence File | Key Metric | Code Line | Artifact |
|---------|---------------|---------------|------------|-----------|----------|
| **1** | Method for embedding GPU voltage health in IPv6 Flow Label | `02_Telemetry_Loop/variations/reference.p4` | 4-bit health (0-15) | Lines 95-99 | N/A |
| **2** | Closed-loop bandwidth throttling based on health | `02_Telemetry_Loop/master_tournament.py` | 0.75V→0.88V recovery | Lines 50-120 | `02_pid_control.png` |
| **3** | PID stability (phase margin >45°) | `02_Telemetry_Loop/variations/08_stability_bode_analysis.py` | 52.3° phase margin | Lines 80-110 | `08_stability_bode.png` |
| **4** | Collective guard (AllReduce protection) | `02_Telemetry_Loop/variations/06_collective_guard.py` | 100% gold preserved | Lines 40-90 | `06_collective_guard.png` |

---

## FAMILY 3: SPECTRAL RESONANCE DAMPING (20+ Claims)

### Core Claims

| Claim # | Claim Element | Evidence File | Key Metric | Code Line | Artifact |
|---------|---------------|---------------|------------|-----------|----------|
| **1** | Method for protecting transformers via FFT-driven jitter | `03_Spectral_Damping/master_tournament.py` | 20.2dB @ 100Hz | Lines 60-130 | `master_tournament_results.png` |
| **2** | Gaussian smearing algorithm | `03_Spectral_Damping/jitter_algorithm.py` | σ = 10ms spread | Lines 30-70 | N/A |
| **3** | Transformer fatigue model (Palmgren-Miner) | `31_Actuarial_Loss_Models/transformer_fatigue_accelerator.py` | 20yr→2.4yr MTTF | Lines 15-40 | N/A |
| **4** | Resonance frequency detection | `03_Spectral_Damping/master_tournament.py` | 100Hz peak detected | Lines 80-100 | N/A |
| **5-10** | Variations (uniform/surgical/phase/multi/pink) | `03_Spectral_Damping/variations/` | Multiple embodiments | Various | 5 PNG artifacts |

---

## FAMILY 4: HBM4 PHASE-LOCKING (12+ Claims)

### Core Claims

| Claim # | Claim Element | Evidence File | Key Metric | Code Line | Artifact |
|---------|---------------|---------------|------------|-----------|----------|
| **1** | Method for synchronizing HBM refresh to network heartbeat | `05_Memory_Orchestration/hbm_dpll_phase_lock.py` | 87.5% efficiency | Lines 40-110 | `hbm_phase_lock.png` |
| **2** | DPLL implementation for phase tracking | `05_Memory_Orchestration/hbm_dpll_phase_lock.py` | Phase error <2ns | Lines 60-90 | N/A |
| **3** | Bandwidth reclamation (5% recovery) | `05_Memory_Orchestration/temporal_credits_dpll.py` | 5.1% TFLOPS gain | Lines 50-100 | N/A |

---

## FAMILY 5: TEMPORAL WHITENING SECURITY (10+ Claims)

### Core Claims

| Claim # | Claim Element | Evidence File | Key Metric | Code Line | Artifact |
|---------|---------------|---------------|------------|-----------|----------|
| **1** | Method for defeating power side-channel attacks via tile shuffling | `scripts/SECURITY_SIDE_CHANNEL_AUDIT.py` | SNR 4.0→1.0 | Lines 80-130 | `signature_whitening_proof.png` |
| **2** | Bubble injection for temporal decorrelation | `scripts/SECURITY_SIDE_CHANNEL_AUDIT.py` | Attack correlation broken | Lines 110-125 | N/A |
| **3** | Power signature masking | `13_Sovereign_Security/power_signature_masking.py` | Weight leakage prevented | Lines 40-90 | N/A |

---

## FAMILY 6: THERMODYNAMIC PREDICTIVE PUMP (10+ Claims)

### Core Claims

| Claim # | Claim Element | Evidence File | Key Metric | Code Line | Artifact |
|---------|---------------|---------------|------------|-----------|----------|
| **1** | Method for pre-cooling liquid loop based on network visibility | `08_Thermal_Orchestration/cdu_predictive_pump.py` | 200ms lead time | Lines 48-84 | N/A |
| **2** | Phase-change physics (latent heat modeling) | `08_Thermal_Orchestration/two_phase_cooling_physics.py` | 2.26 MJ/kg ΔH_vap | Lines 30-40 | `thermodynamic_safety_proof.png` |
| **3** | Leidenfrost prevention | `08_Thermal_Orchestration/two_phase_cooling_physics.py` | 0% vapor formation | Lines 70-85 | N/A |
| **4** | Thermal headroom creation (+5°C) | `08_Thermal_Orchestration/cdu_predictive_pump.py` | Predictive vs reactive | Lines 60-80 | N/A |

---

## FAMILY 7: POWER-GATED DISPATCH (30+ Claims)

### Core Claims (from Provisional)

| Claim # | Claim Element | Evidence File | Key Metric | Code Line | Artifact |
|---------|---------------|---------------|------------|-----------|----------|
| **1** | Method for token-gated instruction retirement | `20_Power_Gated_Dispatch/token_handshake_sim.py` | 100% unauthorized blocked | Lines 40-90 | N/A |
| **2** | Hardware gate between Command Processor and ALU | `20_Power_Gated_Dispatch/gate_logic_spec.v` | Physical enforcement | Lines 15-40 | N/A |
| **3** | Cryptographic token verification | `20_Power_Gated_Dispatch/token_handshake_sim.py` | <10ns verification | Lines 60-85 | N/A |
| **4-10** | Token format, timeout, revocation, hierarchy | `14_ASIC_Implementation/aipp_omega_top.v` | System integration | Lines 67-77 | N/A |

**Full Claims:** See `patents/PROVISIONAL_PATENT_FAMILY_7_POWER_GATED_DISPATCH.md`

---

## FAMILY 8: COHERENT PHASE-LOCKED NETWORKING (15+ Claims)

### Core Claims

| Claim # | Claim Element | Evidence File | Key Metric | Code Line | Artifact |
|---------|---------------|---------------|------------|-----------|----------|
| **1** | System for femtosecond timing via optical carrier phase | `28_Optical_Phase_Lock/optical_phase_determinism_sim.py` | 5000× improvement | Lines 40-75 | `optical_phase_proof.png` |
| **2** | OPLL implementation (Phase-Locked Loop) | `14_ASIC_Implementation/aipp_coherent_phase_recovery.v` | Lock acquisition | Lines 1-90 | N/A |
| **3** | Carrier frequency = 193.4 THz | `28_Optical_Phase_Lock/optical_phase_determinism_sim.py` | c/λ for 1550nm | Lines 28-32 | N/A |
| **4** | Jitter reduction (50ps→10fs) | `28_Optical_Phase_Lock/optical_phase_determinism_sim.py` | 5000× factor | Lines 38-45 | N/A |

---

## CROSS-CUTTING VALIDATION COMPONENTS

### Formal Methods

| Component | Claims Supported | Evidence File | Result |
|-----------|------------------|---------------|--------|
| **TLA+ Protocol Verification** | All handshake claims (Families 1, 7) | `STANDARDS_BODY/aipp_formal_spec.tla` | Safety invariant proven |
| **Z3 Erasure Proof** | Family 5 (Security) | `STANDARDS_BODY/formal_erasure_proof.py` | UNSAT (no breach) |
| **Metastability Analysis** | Family 8 (Coherent) | `STANDARDS_BODY/metastability_robust_proof.py` | ±5ns async-safe |

### Multi-Physics Integration

| Component | Claims Supported | Evidence File | Key Metric |
|-----------|------------------|---------------|------------|
| **Grand Unified Digital Twin** | All families (coupling proof) | `15_Grand_Unified_Digital_Twin/cluster_digital_twin.py` | 0 cascading failures |
| **Counter-Factual Integrity** | All families (authenticity) | `scripts/COUNTER_FACTUAL_INTEGRITY_TEST.py` | 5/5 tests pass |
| **Physics Audit** | All families (constants) | `scripts/OMEGA_PHYSICS_AUDIT.py` | Landauer/Maxwell verified |

### Silicon Feasibility

| Component | Claims Supported | Evidence File | Key Metric |
|-----------|------------------|---------------|------------|
| **FPGA Trigger Logic** | Family 1 (timing accuracy) | `14_ASIC_Implementation/aipp_fpga_trigger.v` | 1ns resolution @ 1GHz |
| **Top-Level Integration** | All families (system claim) | `14_ASIC_Implementation/aipp_omega_top.v` | 45K gates, 0.04mm² |
| **AXI4-Stream Parser** | Families 1, 2 (packet parsing) | `14_ASIC_Implementation/aipp_parser_axi4.v` | Hardware parser |
| **Timing Closure** | All silicon claims | `14_ASIC_Implementation/aipp_timing_closure.py` | 680ps @ 5nm |

---

## ECONOMIC/TCO CLAIMS MAPPING

| Economic Claim | Evidence File | Key Metric |
|----------------|---------------|------------|
| **BOM Savings ($450/GPU)** | `01_PreCharge_Trigger/active_synthesis_model.py` | 90% capacitor reduction |
| **Energy Recovery (70%)** | `25_Adiabatic_Recycling/multi_phase_resonant_clock.py` | Q-factor measurement |
| **Performance Unlock (5.1%)** | `05_Memory_Orchestration/hbm_dpll_phase_lock.py` | HBM bandwidth reclaim |
| **Grid Revenue ($1.2M/yr)** | `07_Grid_VPP/grid_synthetic_inertia.py` | FCR market pricing |
| **Transformer MTTF (20yr)** | `31_Actuarial_Loss_Models/transformer_fatigue_accelerator.py` | Palmgren-Miner rule |

---

## HOW TO USE IN PATENT PROSECUTION

### Scenario 1: Examiner Requests Enablement for Claim X
1. Look up Claim X in this matrix
2. Navigate to the Evidence File
3. Extract the specific code/result at the Line Reference
4. Include the Artifact (PNG) in your response

### Scenario 2: Building Response to 102/103 Rejection
1. Identify which claim element is challenged
2. Find all supporting evidence files in this matrix
3. Cross-reference with `DESIGN_AROUNDS_AND_ALTERNATIVE_EMBODIMENTS.md`
4. Build argument using measured data + blocked workarounds

### Scenario 3: Investor Due Diligence
1. Investor asks: "Prove Claim 4 (capacitance reduction)"
2. Matrix shows: `active_synthesis_model.py` + `active_synthesis_proof.png`
3. Run the file, show the artifact, quote the metric (90% reduction)

---

## VALIDATION SHORTCUTS

### Quick Validation (Single Claim)
```bash
# Example: Validate Family 1, Claim 1
cd 01_PreCharge_Trigger
python -c "from spice_vrm import check_acceptance_criteria, SpiceVRMConfig; \
           cfg = SpiceVRMConfig(); \
           results = check_acceptance_criteria(cfg); \
           print(results)"
```

**Expected Output:**
```
{
  'baseline_min_v': 0.687,
  'pretrigger_min_v': 0.900,
  'overall_pass': True
}
```

### Full Portfolio Validation (All Claims)
```bash
python validate_all_acceptance_criteria.py
```

**Expected Output:** `53/53 PASS`

---

## NOTES FOR LEGAL TEAM

1. **Definiteness (112b):** All vague terms ("power-intensive packet", "characteristic response time") are defined in the DEFINITIONS section of each provisional patent.

2. **Enablement (112a):** Every claim has at least one evidence file with executable code. No "prophetic examples."

3. **Best Mode:** The best mode is disclosed in the provisional patents (e.g., Kalman adaptive aging for Family 1).

4. **Priority Dates:** 
   - Family 1: Filed Dec 25, 2025 (provisional)
   - Family 3: Filed Dec 25, 2025 (provisional)
   - Family 7: Filed Dec 25, 2025 (provisional)
   - Families 2, 4, 5, 6, 8: Ready to file (enablement complete)

---

**Prepared By:** Neural Harris IP Holdings  
**Last Updated:** December 27, 2025  
**Status:** PROSECUTION-READY

*This mapping matrix provides direct traceability between legal claims and technical proof, accelerating patent prosecution and due diligence.*

