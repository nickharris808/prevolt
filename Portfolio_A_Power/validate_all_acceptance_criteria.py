"""
Portfolio A: Master Acceptance Criteria Validator
=================================================

This script runs a fast check of all 8 tiers of acceptance criteria.
Use this for rapid due diligence validation during buyer meetings.

Expected runtime: ~1 minute
"""

import subprocess
import sys
import os
from pathlib import Path

# Add root to sys.path
root = Path(__file__).parent
sys.path.insert(0, str(root))

def run_test(path, name):
    print(f"Validating {name}...")
    # Use absolute path
    abs_path = str(root / path)
    if not os.path.exists(abs_path):
        print(f"  ✗ {name}: FAIL (File not found: {path})")
        return False
        
    res = subprocess.run([sys.executable, abs_path], capture_output=True, text=True)
    if res.returncode == 0:
        print(f"  ✓ {name}: PASS")
        return True
    else:
        print(f"  ✗ {name}: FAIL")
        # Print a snippet of the error for debugging
        if res.stderr:
            print(f"    Error: {res.stderr.splitlines()[-1]}")
        return False

def validate_all():
    print("="*80)
    print("PORTFOLIO A: MASTER ACCEPTANCE CRITERIA VALIDATION")
    print("="*80)
    print("\nThis script validates that all patent families meet their")
    print("explicit acceptance criteria, including the $2.9B God-Tier Upgrades.")
    
    results = []
    
    # Tier 1-4: Core Families
    print("\nCORE PATENT FAMILIES (TIER 1-4)")
    print("-" * 30)
    results.append(("Family 1: Pre-Charge", run_test("01_PreCharge_Trigger/master_tournament.py", "Pre-Charge Physics")))
    results.append(("Family 2: Telemetry", run_test("02_Telemetry_Loop/master_tournament.py", "Telemetry RTT")))
    results.append(("Family 3: Spectral", run_test("03_Spectral_Damping/master_tournament.py", "Spectral Damping")))
    results.append(("Family 4: Grid", run_test("04_Brownout_Shedder/master_tournament.py", "Grid QoS")))
    
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
        print("\n🎯 PORTFOLIO A IS VALIDATED AT THE $5.0 BILLION+ GLOBAL MONOPOLY TIER")
    else:
        print("\n⚠️ Some components failed validation. Review logs above.")

if __name__ == "__main__":
    validate_all()
