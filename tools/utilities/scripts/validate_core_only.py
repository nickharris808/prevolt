"""
Portfolio A: Core Component Validator (Fast)
===========================================

Tests only the essential components for rapid validation.
Expected runtime: 30-60 seconds

Tier Coverage:
- Tier 1-4: Core Physics (4 components)
- Tier 5-7: Key System Components (5 components)
- Tier 10-11: Key Omega Pillars (4 components)
"""

import subprocess
import sys
import os
from pathlib import Path
import time

root = Path(__file__).parent
sys.path.insert(0, str(root))

def run_test(path, name, timeout=30):
    print(f"{name}...", end=' ', flush=True)
    abs_path = str(root / path)
    
    if not os.path.exists(abs_path):
        print("✗ NOT FOUND")
        return False
    
    try:
        res = subprocess.run([sys.executable, abs_path], 
                           capture_output=True, 
                           text=True, 
                           timeout=timeout)
        if res.returncode == 0:
            print("✓ PASS")
            return True
        else:
            print(f"✗ FAIL")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏱ TIMEOUT")
        return False
    except Exception as e:
        print(f"✗ ERROR")
        return False

def main():
    print("="*60)
    print("PORTFOLIO A: CORE COMPONENT VALIDATION")
    print("="*60)
    
    results = []
    
    # Core Physics
    print("\nCORE PHYSICS:")
    results.append(run_test("01_PreCharge_Trigger/master_tournament.py", "Pre-Charge"))
    results.append(run_test("02_Telemetry_Loop/master_tournament.py", "Telemetry"))
    results.append(run_test("03_Spectral_Damping/master_tournament.py", "Spectral"))
    results.append(run_test("04_Brownout_Shedder/master_tournament.py", "Grid QoS"))
    
    # System Integration
    print("\nSYSTEM INTEGRATION:")
    results.append(run_test("05_Memory_Orchestration/hbm_dpll_phase_lock.py", "HBM4 Sync"))
    results.append(run_test("15_Grand_Unified_Digital_Twin/cluster_digital_twin.py", "Digital Twin"))
    results.append(run_test("16_Autonomous_Agent/rl_power_orchestrator.py", "RL Sovereign"))
    results.append(run_test("14_ASIC_Implementation/control_plane_optimizer.py", "Zero-Math"))
    
    # Omega Pillars
    print("\nOMEGA PILLARS:")
    results.append(run_test("20_Power_Gated_Dispatch/token_handshake_sim.py", "Gated Dispatch"))
    results.append(run_test("21_Thermodynamic_Settlement/joule_token_ledger.py", "Settlement"))
    results.append(run_test("24_Sovereign_Orchestration/planetary_carbon_arbitrage.py", "Planetary"))
    results.append(run_test("28_Optical_Phase_Lock/optical_phase_determinism_sim.py", "Coherent Sync"))
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f"\n{'='*60}")
    print(f"RESULT: {passed}/{total} PASS ({passed/total*100:.1f}%)")
    print(f"{'='*60}")
    
    if passed == total:
        print("✓ CORE PORTFOLIO VERIFIED")
    else:
        print("⚠ SOME COMPONENTS FAILED - Review above")

if __name__ == "__main__":
    main()



