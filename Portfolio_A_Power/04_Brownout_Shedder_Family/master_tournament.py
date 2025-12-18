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
    run_all_variations("Brownout Resilience")
    
    summary = [
        {"Family": "4.1", "Mechanism": "Binary Shedding", "Benefit": "Instant Safety", "Valuation": "Low"},
        {"Family": "4.2", "Mechanism": "Graduated QoS", "Benefit": "Soft SLA Landing", "Valuation": "High"},
        {"Family": "4.3", "Mechanism": "Grid Frequency Coupling", "Benefit": "Virtual Battery Revenue", "Valuation": "Very High"},
        {"Family": "4.4", "Mechanism": "Predictive Sag Buffering", "Benefit": "Lossless Resilience", "Valuation": "High"},
        {"Family": "4.5", "Mechanism": "Queue Drain Physics", "Benefit": "Hardware Constraint Proof", "Valuation": "Industrial Tier"}
    ]
    generate_family_summary(4, summary)

