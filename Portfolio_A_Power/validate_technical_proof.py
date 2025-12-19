"""
Portfolio A: Technical Proof Validator
=====================================
Validates the 15 highest-value technical proofs.
Runtime: <60 seconds
"""

import subprocess
import sys
from pathlib import Path

root = Path(__file__).parent

tests = [
    ("01_PreCharge_Trigger/spice_vrm.py", "SPICE Physics"),
    ("15_Grand_Unified_Digital_Twin/cluster_digital_twin.py", "Digital Twin"),
    ("16_Autonomous_Agent/rl_power_orchestrator.py", "RL Sovereign"),
    ("14_ASIC_Implementation/control_plane_optimizer.py", "Zero-Math"),
    ("14_ASIC_Implementation/aipp_timing_closure.py", "Silicon Timing"),
    ("STANDARDS_BODY/metastability_robust_proof.py", "Metastability"),
    ("STANDARDS_BODY/formal_verification_report.py", "Formal Safety"),
    ("05_Memory_Orchestration/hbm_dpll_phase_lock.py", "HBM4 Sync"),
    ("20_Power_Gated_Dispatch/token_handshake_sim.py", "Gated Dispatch"),
    ("21_Thermodynamic_Settlement/joule_token_ledger.py", "Settlement"),
    ("24_Sovereign_Orchestration/planetary_carbon_arbitrage.py", "Planetary"),
    ("25_Adiabatic_Recycling/resonant_lc_tank_sim.py", "Resonant Clock"),
    ("28_Optical_Phase_Lock/optical_phase_determinism_sim.py", "Optical Sync"),
    ("31_Actuarial_Loss_Models/transformer_fatigue_accelerator.py", "Fatigue Model"),
    ("18_Facility_Scale_Moats/transformer_resonance_moat.py", "Resonance Moat"),
]

print("="*60)
print("TECHNICAL PROOF VALIDATION")
print("="*60)

passed = 0
for path, name in tests:
    abs_path = root / path
    if not abs_path.exists():
        print(f"✗ {name}: NOT FOUND")
        continue
    
    try:
        res = subprocess.run([sys.executable, str(abs_path)], 
                           capture_output=True, 
                           text=True, 
                           timeout=30)
        if res.returncode == 0:
            print(f"✓ {name}")
            passed += 1
        else:
            print(f"✗ {name}: FAILED")
    except:
        print(f"⏱ {name}: TIMEOUT")

print(f"\n{'='*60}")
print(f"RESULT: {passed}/{len(tests)} PASS ({passed/len(tests)*100:.0f}%)")
print(f"{'='*60}")
