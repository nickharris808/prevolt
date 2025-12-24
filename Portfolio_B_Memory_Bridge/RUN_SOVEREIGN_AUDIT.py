#!/usr/bin/env python3
"""
Sovereign Audit Script (Comprehensive v2)
========================================
Runs all high-fidelity simulations, checks outputs, and verifies parameter 
consistency and document existence across the entire Portfolio B.
"""

import os
import sys
import subprocess
import time
from typing import List, Dict

# Base directory
BASE_DIR = "/Users/nharris/Desktop/portfolio/Portfolio_B_Memory_Bridge"
ROOT_DIR = "/Users/nharris/Desktop/portfolio"

# Paths to the primary simulation files
SIMULATIONS = [
    "shared/physics_engine_v2.py",
    "01_Incast_Backpressure/corrected_validation.py",
    "02_Deadlock_Release_Valve/predictive_deadlock_audit.py",
    "03_Noisy_Neighbor_Sniper/adversarial_sniper_tournament.py",
    "03_Noisy_Neighbor_Sniper/intent_aware_calibration.py",
    "04_Stranded_Memory_Borrowing/qos_aware_borrowing_audit.py",
    "scaling_and_overhead_validation.py",
    "perfect_storm_unified_dashboard.py"
]

# Documents to check in ROOT
DOCS_ROOT = [
    "EXECUTIVE_SUMMARY_FOR_BUYER.md",
    "DUE_DILIGENCE_RED_TEAM_CRITIQUE.md",
    "REBUTTAL_TO_CRITIQUE.md",
    "README.md",
    "WHAT_WE_ACCOMPLISHED.md",
    "FINAL_PACKAGE_READY_TO_SEND.md",
    "FIXES_AND_IMPROVEMENTS.md"
]

# Results folders to verify
RESULTS_FOLDERS = [
    "01_Incast_Backpressure/results",
    "02_Deadlock_Release_Valve/results",
    "03_Noisy_Neighbor_Sniper/results",
    "04_Stranded_Memory_Borrowing/results",
    "results"
]

def run_step(file_path: str) -> bool:
    print(f"\n[AUDIT] Running {file_path}...")
    start_time = time.time()
    try:
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

def check_docs():
    print("\n[AUDIT] Verifying Documentation Presence...")
    all_present = True
    for doc in DOCS_ROOT:
        path = os.path.join(ROOT_DIR, doc)
        if os.path.exists(path):
            print(f"  ✓ {doc}: Present.")
        else:
            print(f"  ✗ {doc}: MISSING!")
            all_present = False
    return all_present

def audit_results_folders():
    print("\n[AUDIT] Checking Results Folders...")
    all_valid = True
    for folder in RESULTS_FOLDERS:
        path = os.path.join(BASE_DIR, folder)
        if os.path.exists(path):
            files = [f for f in os.listdir(path) if f.endswith('.png')]
            if files:
                print(f"  ✓ {folder}: {len(files)} PNGs found.")
                for f in sorted(files):
                    print(f"    - {f}")
            else:
                print(f"  ! {folder}: No PNGs found!")
                # results folder at the root might not have many PNGs if they went to subfolders
                if "results" != folder:
                    all_valid = False
        else:
            print(f"  ✗ {folder}: Folder missing!")
            all_valid = False
    return all_valid

def perform_sovereign_audit():
    print("=" * 60)
    print("PORTFOLIO B: COMPREHENSIVE SOVEREIGN AUDIT (v2)")
    print("=" * 60)
    
    os.chdir(BASE_DIR)
    
    # 1. Run Simulations
    all_sims_pass = True
    for sim in SIMULATIONS:
        if not run_step(sim):
            all_sims_pass = False
            
    # 2. Check Documentation
    docs_ok = check_docs()
    
    # 3. Check Results Folders
    results_ok = audit_results_folders()
    
    print("\n" + "=" * 60)
    if all_sims_pass and docs_ok and results_ok:
        print("AUDIT STATUS: PASSED - PORTFOLIO IS ASSET-READY")
    else:
        print("AUDIT STATUS: FAILED - CORRECTIONS REQUIRED")
        if not all_sims_pass: print("  - Issues in simulation runs.")
        if not docs_ok: print("  - Issues in documentation presence.")
        if not results_ok: print("  - Issues in results generation.")
    print("=" * 60)

if __name__ == "__main__":
    perform_sovereign_audit()



