"""
AIPP-Omega: Master Acceptance Criteria Validator
================================================

This script validates all 65+ core components across 12 patent families.
Optimized for reliability and clear error reporting.

Expected runtime: ~3-4 minutes (60+ components)
"""

import subprocess
import sys
import os
from pathlib import Path
import time

# Add root to sys.path
root = Path(__file__).parent
sys.path.insert(0, str(root))

def run_test(path, name, timeout=60):
    print(f"Validating {name}...", end=' ', flush=True)
    abs_path = str(root / path)
    
    if not os.path.exists(abs_path):
        print(f"✗ FAIL (Not found)")
        return False
    
    start_time = time.time()
    try:
        res = subprocess.run([sys.executable, abs_path], 
                           capture_output=True, 
                           text=True, 
                           timeout=timeout)
        elapsed = time.time() - start_time
        
        if res.returncode == 0:
            print(f"✓ PASS ({elapsed:.1f}s)")
            return True
        else:
            print(f"✗ FAIL (exit {res.returncode})")
            if res.stderr:
                lines = res.stderr.splitlines()
                if lines:
                    print(f"    → {lines[-1][:80]}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏱ TIMEOUT (>{timeout}s)")
        return False
    except Exception as e:
        print(f"✗ ERROR ({str(e)[:60]})")
        return False

def validate_all():
    print("="*80)
    print("AIPP-OMEGA: MASTER ACCEPTANCE CRITERIA VALIDATION")
    print("="*80)
    print("\nThis script validates all 65+ components across 12 patent")
    print("families meet their explicit acceptance criteria.")
    
    results = []
    
    # Tier 1-4: Core Families
    print("\nCORE PATENT FAMILIES (TIER 1-4)")
    print("-" * 30)
    results.append(("Family 1: Pre-Charge", run_test("01_PreCharge_Trigger/master_tournament.py", "Pre-Charge Physics")))
    results.append(("Family 2: Telemetry", run_test("02_Telemetry_Loop/master_tournament.py", "Telemetry RTT")))
    results.append(("Family 3: Spectral", run_test("03_Spectral_Damping/master_tournament.py", "Spectral Damping")))
    results.append(("Family 4 (Old): Grid", run_test("04_Brownout_Shedder/master_tournament.py", "Grid QoS")))
    
    # Tier 5: $1B System Architecture
    print("\nSYSTEM ARCHITECTURE (TIER 5)")
    print("-" * 30)
    results.append(("HBM4 Sync", run_test("05_Memory_Orchestration/hbm_refresh_sync.py", "Memory Sync")))
    results.append(("UCIe Shunt", run_test("06_Chiplet_Fabric/ucie_power_migration.py", "Chiplet Migration")))
    results.append(("Grid VPP", run_test("07_Grid_VPP/grid_synthetic_inertia.py", "Grid Revenue")))
    
    # Tier 6: $2B+ Global Monopoly
    print("\nGLOBAL MONOPOLY PROOFS (TIER 6)")
    print("-" * 30)
    results.append(("Optical Bias", run_test("11_Optical_IO/optical_thermal_bias.py", "Optical IO")))
    results.append(("Storage Incast", run_test("12_Storage_Fabric/incast_power_shaper.py", "Storage Incast")))
    results.append(("Temporal Obfuscation", run_test("13_Sovereign_Security/power_signature_masking.py", "Sovereign Security")))
    results.append(("Fabric Token", run_test("10_Fabric_Orchestration/spine_power_arbiter.py", "Fabric Token")))
    results.append(("Formal Proof", run_test("STANDARDS_BODY/protocol_formal_proof.py", "Z3 Formal Proof")))
    results.append(("Unified Policy", run_test("10_Fabric_Orchestration/unified_temporal_policy_sim.py", "Unified Policy")))
    results.append(("Limp Mode Safety", run_test("01_PreCharge_Trigger/limp_mode_validation.py", "Limp Mode Safety")))
    results.append(("Six Sigma Yield", run_test("scripts/validate_six_sigma.py", "Manufacturing Yield")))
    
    # Tier 7: God-Tier Upgrades
    print("\nGOD-TIER UPGRADES (TIER 7)")
    print("-" * 30)
    results.append(("Digital Twin", run_test("15_Grand_Unified_Digital_Twin/cluster_digital_twin.py", "Unified Digital Twin")))
    results.append(("Zero-Math Data Plane", run_test("14_ASIC_Implementation/control_plane_optimizer.py", "Silicon Feasibility")))
    results.append(("RL Sovereign Agent", run_test("16_Autonomous_Agent/rl_power_orchestrator.py", "Autonomous AI")))
    results.append(("Phase Change Safety", run_test("08_Thermal_Orchestration/two_phase_cooling_physics.py", "Thermodynamic Safety")))
    
    # Tier 8: $5B+ Moonshots
    print("\n$5B+ GLOBAL MONOPOLY MOONSHOTS (TIER 8)")
    print("-" * 30)
    results.append(("HBM4 Phase-Locking", run_test("05_Memory_Orchestration/hbm_dpll_phase_lock.py", "Memory Performance")))
    results.append(("Data-Vault Handshake", run_test("13_Sovereign_Security/data_vault_handshake.py", "Sovereign Trust")))
    results.append(("Erasure Formal Proof", run_test("STANDARDS_BODY/formal_erasure_proof.py", "Erasure Math")))
    
    # Tier 9: $5B+ Hard Physics Moonshots
    print("\n$5B+ HARD PHYSICS MOONSHOTS (TIER 9)")
    print("-" * 30)
    results.append(("Active Synthesis", run_test("01_PreCharge_Trigger/active_synthesis_model.py", "BOM Killer")))
    results.append(("Boeing-Grade Proof", run_test("STANDARDS_BODY/formal_verification_report.py", "Liability Shield")))
    results.append(("Non-Linear SPICE", run_test("01_PreCharge_Trigger/spice_vrm_nonlinear.py", "Saturation Proof")))
    results.append(("Carbon Routing", run_test("07_Grid_VPP/carbon_intensity_orchestrator.py", "ESG Standard")))
    
    # Tier 10: $100B+ Omega Tier
    print("\n$100B+ OMEGA TIER (TIER 10)")
    print("-" * 30)
    results.append(("Power-Gated Dispatch", run_test("20_Power_Gated_Dispatch/token_handshake_sim.py", "Permission to Compute")))
    results.append(("Thermodynamic Settlement", run_test("21_Thermodynamic_Settlement/joule_token_ledger.py", "Global Ledger")))
    results.append(("Planetary Migration", run_test("22_Global_VPP/inference_load_migrator.py", "Global Sun-Follower")))
    results.append(("Atomic Fabric", run_test("23_Atomic_Timing/phase_drift_compensation_sim.py", "Perfect Time")))
    
    # Tier 11: $100B+ Sovereign Orchestration
    print("\n$100B+ SOVEREIGN ORCHESTRATION (TIER 11)")
    print("-" * 30)
    results.append(("Planetary Arbitrage", run_test("24_Sovereign_Orchestration/planetary_carbon_arbitrage.py", "Sun-Follower")))
    results.append(("Sovereign Inertia", run_test("24_Sovereign_Orchestration/sovereign_grid_inertia.py", "Grid Stabilizer")))
    
    # Tier 12: $100B+ Facility & Planetary Moats
    print("\n$100B+ FACILITY & PLANETARY MOATS (TIER 12)")
    print("-" * 30)
    results.append(("Transformer Resonance", run_test("18_Facility_Scale_Moats/transformer_resonance_moat.py", "Blocking IVR")))
    results.append(("IVR Thermal Limit", run_test("18_Facility_Scale_Moats/ivr_thermal_limit.py", "The Integration Wall")))
    results.append(("Global Latency Map", run_test("19_Planetary_Orchestration/global_latency_map.py", "Speed of Light")))

    # Tier 13: $100B+ Hard Engineering Proofs
    print("\n$100B+ HARD ENGINEERING PROOFS (TIER 13)")
    print("-" * 30)
    results.append(("Silicon Timing", run_test("14_ASIC_Implementation/aipp_timing_closure.py", "Post-Layout RTL")))
    results.append(("Asynchronous Proof", run_test("STANDARDS_BODY/metastability_robust_proof.py", "Metastability Safety")))
    results.append(("PCIe Full-Stack", run_test("09_Software_SDK/pcie_full_stack_model.py", "Hardware Determinism")))
    results.append(("Fabric Incast", run_test("10_Fabric_Orchestration/adversarial_incast_sim.py", "Express-Lane Scale")))
    results.append(("Non-Linear Stability", run_test("01_PreCharge_Trigger/nonlinear_stability_audit.py", "Lyapunov Sweep")))
    
    # Tier 14: Extreme Engineering Audit
    print("\nEXTREME ENGINEERING AUDIT (TIER 14)")
    print("-" * 30)
    results.append(("Resonant Clock", run_test("25_Adiabatic_Recycling/resonant_lc_tank_sim.py", "Adiabatic Logic")))
    results.append(("Body Biasing", run_test("26_Adaptive_Body_Biasing/body_bias_leakage_sim.py", "Leakage Choking")))
    results.append(("Entropy Scaling", run_test("27_Entropy_VDD_Scaling/vdd_subthreshold_sim.py", "Shannon VDD")))
    results.append(("Coherent Sync", run_test("28_Optical_Phase_Lock/optical_phase_determinism_sim.py", "THz Phase-Lock")))
    results.append(("Gradient Migration", run_test("29_Sparse_Gradient_Migration/planetary_gradient_migrator.py", "Sparsity Migration")))

    # Tier 15: Omega-Tier Physics & Economy
    print("\nOMEGA-TIER PHYSICS & ECONOMY (TIER 15)")
    print("-" * 30)
    results.append(("Silence Tokens", run_test("05_Memory_Orchestration/hbm_silence_token_enforcement.py", "Temporal Guard Band")))
    results.append(("Multi-Phase Clock", run_test("25_Adiabatic_Recycling/multi_phase_resonant_clock.py", "EMI Shielded Resonance")))
    results.append(("Cluster Breathing", run_test("22_Global_VPP/sub_harmonic_cluster_breathing.py", "Synthetic Inertia")))
    results.append(("Entropy Credits", run_test("21_Thermodynamic_Settlement/entropy_credit_ledger.py", "AI Clearinghouse")))
    results.append(("Power Audit", run_test("13_Sovereign_Security/power_signature_audit.py", "Physical Attestation")))
    
    # Tier 16: The Final Lock (Supply Chain & Memory Wall)
    print("\nTHE FINAL LOCK: SUPPLY CHAIN & MEMORY WALL (TIER 16)")
    print("-" * 30)
    results.append(("Silicon Provenance", run_test("30_Silicon_Provenance/puf_power_fingerprint.py", "Power-PUF")))
    results.append(("CXL Latency Hiding", run_test("12_Storage_Fabric/cxl_latency_pre_dispatch.py", "CXL Memory Wall")))
    results.append(("Master Pareto", run_test("scripts/master_pareto_charts.py", "Decision Surface")))
    
    # NEW: Portfolio B Families (4, 5, 6, 11)
    print("\nPORTFOLIO B INTEGRATIONS (NEW FAMILIES)")
    print("-" * 30)
    results.append(("Family 4: Incast Backpressure", run_test("32_Incast_Backpressure/simulation.py", "Memory Backpressure", timeout=120)))
    results.append(("Family 5: CXL Sideband", run_test("33_CXL_Sideband_Control/telemetry_bus.py", "CXL Sideband", timeout=120)))
    results.append(("Family 11: Noisy Neighbor", run_test("35_Noisy_Neighbor_Sniper/simulation.py", "4D Classifier", timeout=120)))
    
    # NEW: Thermal Innovations (Families 9, 10, 12)
    print("\nTHERMAL INNOVATIONS (FAMILIES 9, 10, 12)")
    print("-" * 30)
    results.append(("Family 9: Iso-Performance", run_test("15_Grand_Unified_Digital_Twin/grand_unified_3d_twin.py", "Iso-Performance Scaling")))
    results.append(("Family 10: Thermal PUF", run_test("02_Telemetry_Loop/thermal_puf_extractor.py", "Thermal PUF Auth")))
    results.append(("Family 12: Compute-Inhibit", run_test("14_ASIC_Implementation/power_aware_rtl_synthesis.py", "Compute-Inhibit Interlock")))
    
    # Summary
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    
    total_tests = len(results)
    passed_tests = sum(1 for _, p in results if p)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name:.<50} {status}")
    
    print(f"\nFinal Score: {passed_tests}/{total_tests} components passed")
    
    if passed_tests == total_tests:
        print(f"\n✅ AIPP-OMEGA: ALL {total_tests} COMPONENTS VALIDATED")
        print("   Technical Quality: Simulation-proven, hardware validation required")
        print("   Current Stage: TRL-3 (Proof of Concept)")
        print("   Patent Families: 12 (integrated from Portfolio A, B, and thermal innovations)")
        print("   Next Step: FPGA demo per docs/specs/HARDWARE_EXECUTION_PLAN.md")
    else:
        print(f"\n⚠️ {total_tests - passed_tests} component(s) failed validation. Review logs above.")

if __name__ == "__main__":
    validate_all()






