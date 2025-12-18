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
    run_all_variations("Telemetry Loop")
    
    summary = [
        {"Family": "2.1", "Mechanism": "Quantized Feedback", "Benefit": "Low-Cost Logic", "Valuation": "Low"},
        {"Family": "2.2", "Mechanism": "PID Rate Control", "Benefit": "Stability/No Jitter", "Valuation": "High"},
        {"Family": "2.3", "Mechanism": "Gradient Preemption", "Benefit": "Crash Prevention", "Valuation": "High"},
        {"Family": "2.4", "Mechanism": "Tenant Flow Sniper", "Benefit": "Multi-Tenant SLA", "Valuation": "Very High"},
        {"Family": "2.5", "Mechanism": "Graduated Penalties", "Benefit": "Soft-Landing Recovery", "Valuation": "High"},
        {"Family": "2.6", "Mechanism": "Collective Guard", "Benefit": "Preserves Training Progress", "Valuation": "S+ Tier"},
        {"Family": "2.7", "Mechanism": "QP-Spray Aggregator", "Benefit": "Evasion-Proof Isolation", "Valuation": "Very High"},
        {"Family": "2.8", "Mechanism": "Stability Analysis", "Benefit": "Phase-Margin Guarantee", "Valuation": "Standard-Ready"},
        {"Family": "2.9", "Mechanism": "Workload Intensity", "Benefit": "Non-Linear Adaptation", "Valuation": "Industrial Tier"},
        {"Family": "2.10", "Mechanism": "Adversarial Guard", "Benefit": "Anti-Spoofing Security", "Valuation": "Cloud-Essential"}
    ]
    generate_family_summary(2, summary)

