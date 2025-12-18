"""
Family Master Tournament Runner
==============================
"""

import subprocess
import os
import sys
from pathlib import Path
import pandas as pd

def run_all_variations(family_name):
    variations_dir = Path(__file__).parent / "variations"
    variation_scripts = sorted(list(variations_dir.glob("*.py")))
    
    print("=" * 80)
    print(f"{family_name.upper()} FAMILY: EXECUTING FULL TOURNAMENT")
    print("=" * 80)
    
    for script in variation_scripts:
        print(f"\n[RUNNING] {script.name}...")
        try:
            subprocess.check_call([sys.executable, str(script)])
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Variation {script.name} failed: {e}")

def generate_family_summary(family_num, summary_data):
    df = pd.DataFrame(summary_data)
    print("\n" + "=" * 80)
    print(f"FAMILY {family_num} PATENT ARCHITECTURE")
    print("=" * 80)
    print(df.to_string(index=False))
    df.to_csv(Path(__file__).parent / "family_summary.csv", index=False)

if __name__ == "__main__":
    run_all_variations("Spectral Damping")
    
    summary = [
        {"Family": "3.1", "Mechanism": "Uniform Jitter", "Benefit": "Proven Peak Smearing", "Valuation": "Low"},
        {"Family": "3.2", "Mechanism": "Surgical Notch", "Benefit": "Lower Latency Penalty", "Valuation": "High"},
        {"Family": "3.3", "Mechanism": "Phase Interleaving", "Benefit": "Zero-Jitter Hardware", "Valuation": "Very High"},
        {"Family": "3.4", "Mechanism": "Harmonic Damping", "Benefit": "Total Facility Safety", "Valuation": "High"},
        {"Family": "3.5", "Mechanism": "Pink Noise SNR", "Benefit": "Dirty-Rail Robustness", "Valuation": "Industrial Tier"}
    ]
    generate_family_summary(3, summary)

