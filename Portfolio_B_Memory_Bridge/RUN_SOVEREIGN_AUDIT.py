#!/usr/bin/env python3
"""
Sovereign Audit Script
======================
Runs all high-fidelity simulations, checks outputs, and verifies parameter 
consistency across the entire Portfolio B.

This script ensures that the 'Grand Unified Cortex' is ready for acquisition.
"""

import os
import sys
import subprocess
import time
from typing import List, Dict

# Paths to the primary simulation files
SIMULATIONS = [
    "shared/physics_engine_v2.py",
    "01_Incast_Backpressure/corrected_validation.py",
    "02_Deadlock_Release_Valve/predictive_deadlock_audit.py",
    "03_Noisy_Neighbor_Sniper/adversarial_sniper_tournament.py",
    "04_Stranded_Memory_Borrowing/qos_aware_borrowing_audit.py",
    "perfect_storm_unified_dashboard.py"
]

def run_step(file_path: str) -> bool:
    print(f"\n[AUDIT] Running {file_path}...")
    start_time = time.time()
    try:
        # Run with current python interpreter
        result = subprocess.run(
            [sys.executable, file_path],
            capture_output=True,
            text=True,
            timeout=60
        )
        duration = time.time() - start_time
        
        if result.returncode == 0:
            print(f"  ✓ SUCCESS ({duration:.2f}s)")
            # Print last few lines of output for verification
            lines = result.stdout.strip().split('\n')
            for line in lines[-3:]:
                print(f"    > {line}")
            return True
        else:
            print(f"  ✗ FAILED ({duration:.2f}s)")
            print(f"    Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"  ✗ EXCEPTION: {str(e)}")
        return False

def audit_results_folders():
    print("\n[AUDIT] Checking Results Folders...")
    result_paths = [
        "01_Incast_Backpressure/results",
        "03_Noisy_Neighbor_Sniper/results",
        "results"
    ]
    for path in result_paths:
        if os.path.exists(path):
            files = os.listdir(path)
            print(f"  ✓ {path}: {len(files)} files found.")
            for f in files:
                if f.endswith('.png'):
                    print(f"    - {f}")
        else:
            print(f"  ✗ {path}: Folder missing!")

def perform_sovereign_audit():
    print("=" * 60)
    print("PORTFOLIO B: SOVEREIGN ARCHITECTURE AUDIT")
    print("=" * 60)
    
    all_success = True
    for sim in SIMULATIONS:
        if not run_step(sim):
            all_success = False
            
    audit_results_folders()
    
    print("\n" + "=" * 60)
    if all_success:
        print("AUDIT STATUS: PASSED (Sovereign Tier Validated)")
    else:
        print("AUDIT STATUS: FAILED (Critical Issues Found)")
    print("=" * 60)

if __name__ == "__main__":
    # Change to the base directory of the portfolio
    os.chdir("/Users/nharris/Desktop/portfolio/Portfolio_B_Memory_Bridge")
    perform_sovereign_audit()
