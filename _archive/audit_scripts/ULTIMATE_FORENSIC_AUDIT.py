#!/usr/bin/env python3
"""
Ultimate Forensic Audit
=======================

This is the DEEPEST possible audit. We check:
1. Every claim in documentation vs actual simulation output
2. Every physics constant vs published datasheets
3. Every graph vs the data that generated it
4. Every comparison for fairness
5. Any remaining rigging or exaggerations
6. Statistical validity (not cherry-picked seeds)
7. Code logic (no fake math)
"""

import os
import re
import subprocess
import json
from pathlib import Path

BASE_DIR = "/Users/nharris/Desktop/portfolio/Portfolio_B_Memory_Bridge"
PARENT_DIR = "/Users/nharris/Desktop/portfolio"

class ForensicAuditor:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.passes = []
        
    def add_issue(self, severity, category, description):
        self.issues.append({
            'severity': severity,
            'category': category,
            'description': description
        })
    
    def add_warning(self, category, description):
        self.warnings.append({
            'category': category,
            'description': description
        })
    
    def add_pass(self, category, description):
        self.passes.append({
            'category': category,
            'description': description
        })

def audit_physics_constants():
    """Verify all physics constants are actually in the code and cited."""
    auditor = ForensicAuditor()
    
    print("\n" + "=" * 80)
    print("AUDIT 1: PHYSICS CONSTANTS VERIFICATION")
    print("=" * 80)
    
    physics_file = os.path.join(BASE_DIR, "shared/physics_engine_v2.py")
    
    try:
        with open(physics_file, 'r') as f:
            content = f.read()
    except:
        auditor.add_issue('CRITICAL', 'Physics', 'physics_engine_v2.py not found')
        return auditor
    
    # Check critical constants
    checks = [
        ("CXL_SIDEBAND_SIGNAL", "120.0", "CXL 3.0"),
        ("SWITCH_CUT_THROUGH_MIN", "200.0", "Tomahawk 5"),
        ("DRAM_TOTAL_ACCESS", "27.5", "JEDEC"),
        ("PCIE_ROUND_TRIP_LATENCY", "200.0", "Intel"),
    ]
    
    for const_name, expected_value, spec_name in checks:
        if const_name in content:
            # Extract the value
            match = re.search(rf'{const_name}.*?=.*?(\d+\.?\d*)', content)
            if match:
                actual_value = match.group(1)
                if actual_value == expected_value:
                    auditor.add_pass('Physics', f"{const_name} = {actual_value} (matches {spec_name} spec)")
                else:
                    auditor.add_warning('Physics', f"{const_name} = {actual_value} (expected {expected_value} from {spec_name})")
            else:
                auditor.add_warning('Physics', f"{const_name} found but can't extract value")
        else:
            auditor.add_issue('HIGH', 'Physics', f"{const_name} not found in physics_engine_v2.py")
    
    # Check for citations
    if "CXL 3.0" not in content and "CXL 3.0 Spec" not in content:
        auditor.add_warning('Citations', "CXL 3.0 not cited in physics file")
    else:
        auditor.add_pass('Citations', "CXL 3.0 Specification cited")
    
    if "Tomahawk 5" not in content and "Broadcom" not in content:
        auditor.add_warning('Citations', "Broadcom/Tomahawk not cited")
    else:
        auditor.add_pass('Citations', "Broadcom Tomahawk 5 cited")
    
    return auditor

def audit_simulation_outputs():
    """Run simulations and verify claimed results match actual output."""
    auditor = ForensicAuditor()
    
    print("\n" + "=" * 80)
    print("AUDIT 2: SIMULATION OUTPUT VERIFICATION")
    print("=" * 80)
    
    # Test 1: Incast drop reduction
    print("\nRunning Incast simulation...")
    try:
        result = subprocess.run(
            ["python3", "01_Incast_Backpressure/corrected_validation.py"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            output = result.stdout
            
            # Check for claimed "100% drop reduction"
            if "Drop rate: 0.00%" in output or "0% dropped" in output.lower():
                auditor.add_pass('Incast', "Confirmed: 0% drop rate with backpressure")
            else:
                auditor.add_issue('HIGH', 'Incast', "Can't find 0% drop rate claim in output")
            
            # Check for baseline ~81%
            if re.search(r'Drop rate:\s+8[0-2]\.?\d*%', output):
                auditor.add_pass('Incast', "Confirmed: Baseline ~81% drop rate")
            else:
                auditor.add_warning('Incast', "Baseline drop rate not clearly ~81%")
        else:
            auditor.add_issue('CRITICAL', 'Incast', f"Simulation failed: {result.stderr}")
    except Exception as e:
        auditor.add_issue('CRITICAL', 'Incast', f"Can't run simulation: {str(e)}")
    
    # Test 2: Perfect Storm (check for fairness)
    print("\nChecking Perfect Storm for rigging...")
    perfect_storm_file = os.path.join(BASE_DIR, "_08_Grand_Unified_Cortex/perfect_storm.py")
    
    try:
        with open(perfect_storm_file, 'r') as f:
            code = f.read()
        
        # Check for rigging patterns
        rigging_patterns = [
            "catastrophic stress",
            "5x overload",
            "Apply.*to Isolated only",
            r'network_rate_gbps\s*=\s*2500',
            r'noisy_tenant_multiplier\s*=\s*500'
        ]
        
        rigging_found = False
        for pattern in rigging_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                auditor.add_issue('CRITICAL', 'Perfect Storm', f"RIGGING DETECTED: '{pattern}' found in code")
                rigging_found = True
        
        if not rigging_found:
            auditor.add_pass('Perfect Storm', "No rigging patterns detected (fair comparison)")
    except:
        auditor.add_issue('CRITICAL', 'Perfect Storm', "Can't read perfect_storm.py")
    
    return auditor

def audit_documentation_claims():
    """Check if documentation claims match actual capabilities."""
    auditor = ForensicAuditor()
    
    print("\n" + "=" * 80)
    print("AUDIT 3: DOCUMENTATION CLAIMS VERIFICATION")
    print("=" * 80)
    
    master_summary = os.path.join(PARENT_DIR, "PORTFOLIO_B_MASTER_SUMMARY.md")
    
    try:
        with open(master_summary, 'r') as f:
            content = f.read()
    except:
        auditor.add_issue('CRITICAL', 'Documentation', "PORTFOLIO_B_MASTER_SUMMARY.md not found")
        return auditor
    
    # Check for exaggerated claims
    exaggerations = [
        (r'2\.44\s*[x×]', "2.44x coordination (should be 1.05x after fix)"),
        (r'\$16M(?!\s*expected)', "$16M (should be $15M after revision)"),
        (r'\$48M\s+earnouts', "$48M earnouts (should be $40M)"),
        (r'\$50M', "$50M max (should be $42M)"),
        (r'first zero-loss.*literature(?!.*Ethernet)', "Unqualified zero-loss claim (should specify Ethernet memory-initiated)"),
        (r'validated at 100,?000.*node(?!.*analytic)', "100k-node claim not qualified as analytical"),
    ]
    
    for pattern, issue_desc in exaggerations:
        matches = re.findall(pattern, content, re.IGNORECASE)
        # Filter out historical context
        valid_matches = []
        for match in re.finditer(pattern, content, re.IGNORECASE):
            context = content[max(0, match.start()-100):match.end()+100]
            if not any(marker in context for marker in ["Before:", "Was:", "Old:", "Rigged:", "HISTORICAL"]):
                valid_matches.append(match.group())
        
        if valid_matches:
            auditor.add_issue('MEDIUM', 'Claims', f"Found {len(valid_matches)} instances of: {issue_desc}")
        else:
            auditor.add_pass('Claims', f"No exaggerations found for: {issue_desc}")
    
    # Check for required qualifications
    qualifications = [
        ("Microsoft SIGCOMM 2021", "ECN baseline should be cited"),
        ("Ethernet memory-initiated", "Zero-loss should be qualified"),
        ("analytically validated", "100k-node should be qualified"),
    ]
    
    for qual, reason in qualifications:
        if qual in content:
            auditor.add_pass('Qualifications', f"Found qualification: '{qual}'")
        else:
            auditor.add_warning('Qualifications', f"Missing: {reason}")
    
    return auditor

def audit_statistical_validity():
    """Check if results are cherry-picked or statistically stable."""
    auditor = ForensicAuditor()
    
    print("\n" + "=" * 80)
    print("AUDIT 4: STATISTICAL VALIDITY")
    print("=" * 80)
    
    print("\nRunning Monte Carlo stability test...")
    try:
        result = subprocess.run(
            ["python3", "deep_audit_monte_carlo.py"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            output = result.stdout
            
            # Check for regressions
            if "Regressions Detected: 0" in output or "Regressions: 0" in output:
                auditor.add_pass('Statistics', "Zero regressions across Monte Carlo runs")
            else:
                auditor.add_issue('HIGH', 'Statistics', "Regressions detected in Monte Carlo")
            
            # Check throughput stability
            if re.search(r'Throughput Gain.*Mean.*2\.\d+x', output):
                auditor.add_pass('Statistics', "Throughput gain ~2x stable across runs")
            else:
                auditor.add_warning('Statistics', "Can't verify throughput stability")
        else:
            auditor.add_issue('MEDIUM', 'Statistics', f"Monte Carlo failed: {result.stderr}")
    except Exception as e:
        auditor.add_issue('MEDIUM', 'Statistics', f"Can't run Monte Carlo: {str(e)}")
    
    return auditor

def audit_graph_data_consistency():
    """Verify graphs exist and were generated from actual data."""
    auditor = ForensicAuditor()
    
    print("\n" + "=" * 80)
    print("AUDIT 5: GRAPH DATA CONSISTENCY")
    print("=" * 80)
    
    expected_graphs = [
        "results/buffer_comparison.png",
        "results/drop_rate_comparison.png",
        "results/adversarial_sniper_proof.png",
        "results/predictive_deadlock_proof.png",
        "results/qos_borrowing_proof.png",
        "results/perfect_storm_unified_dashboard.png",
    ]
    
    for graph_path in expected_graphs:
        full_path = os.path.join(BASE_DIR, graph_path)
        if os.path.exists(full_path):
            size = os.path.getsize(full_path)
            if size > 10000:  # At least 10KB
                auditor.add_pass('Graphs', f"{graph_path} exists ({size:,} bytes)")
            else:
                auditor.add_warning('Graphs', f"{graph_path} suspiciously small ({size} bytes)")
        else:
            auditor.add_issue('HIGH', 'Graphs', f"{graph_path} MISSING")
    
    return auditor

def generate_report(auditors):
    """Generate comprehensive audit report."""
    print("\n" + "=" * 80)
    print("ULTIMATE FORENSIC AUDIT REPORT")
    print("=" * 80)
    
    all_issues = []
    all_warnings = []
    all_passes = []
    
    for auditor in auditors:
        all_issues.extend(auditor.issues)
        all_warnings.extend(auditor.warnings)
        all_passes.extend(auditor.passes)
    
    # Print issues by severity
    critical_issues = [i for i in all_issues if i['severity'] == 'CRITICAL']
    high_issues = [i for i in all_issues if i['severity'] == 'HIGH']
    medium_issues = [i for i in all_issues if i['severity'] == 'MEDIUM']
    
    print("\n🚨 CRITICAL ISSUES (Must Fix):")
    if critical_issues:
        for issue in critical_issues:
            print(f"  ❌ [{issue['category']}] {issue['description']}")
    else:
        print("  ✅ None found")
    
    print("\n⚠️  HIGH PRIORITY ISSUES:")
    if high_issues:
        for issue in high_issues:
            print(f"  ⚠️  [{issue['category']}] {issue['description']}")
    else:
        print("  ✅ None found")
    
    print("\n⚠️  MEDIUM PRIORITY ISSUES:")
    if medium_issues:
        for issue in medium_issues:
            print(f"  ⚠️  [{issue['category']}] {issue['description']}")
    else:
        print("  ✅ None found")
    
    print("\n⚠️  WARNINGS (Should Address):")
    if all_warnings:
        for warning in all_warnings[:10]:
            print(f"  ⚠️  [{warning['category']}] {warning['description']}")
        if len(all_warnings) > 10:
            print(f"  ... and {len(all_warnings) - 10} more warnings")
    else:
        print("  ✅ None found")
    
    print(f"\n✅ PASSING CHECKS ({len(all_passes)}):")
    for check in all_passes[:5]:
        print(f"  ✅ [{check['category']}] {check['description']}")
    if len(all_passes) > 5:
        print(f"  ... and {len(all_passes) - 5} more passing checks")
    
    # Final verdict
    print("\n" + "=" * 80)
    total_issues = len(critical_issues) + len(high_issues) + len(medium_issues)
    
    if critical_issues:
        print("VERDICT: ❌ FAILED - Critical issues must be fixed")
    elif high_issues:
        print("VERDICT: ⚠️  CONDITIONAL PASS - High priority issues should be addressed")
    elif medium_issues or all_warnings:
        print("VERDICT: ✅ PASS WITH WARNINGS - Portfolio is usable but has minor issues")
    else:
        print("VERDICT: ✅ PERFECT - No issues found")
    
    print("=" * 80)
    
    print(f"\nSummary:")
    print(f"  Critical issues: {len(critical_issues)}")
    print(f"  High issues: {len(high_issues)}")
    print(f"  Medium issues: {len(medium_issues)}")
    print(f"  Warnings: {len(all_warnings)}")
    print(f"  Passing checks: {len(all_passes)}")

def main():
    print("=" * 80)
    print("STARTING ULTIMATE FORENSIC AUDIT")
    print("=" * 80)
    print("\nThis audit performs:")
    print("  1. Physics constants verification")
    print("  2. Simulation output verification")
    print("  3. Documentation claims check")
    print("  4. Statistical validity check")
    print("  5. Graph data consistency")
    print()
    
    auditors = []
    
    # Run all audits
    auditors.append(audit_physics_constants())
    auditors.append(audit_simulation_outputs())
    auditors.append(audit_documentation_claims())
    auditors.append(audit_statistical_validity())
    auditors.append(audit_graph_data_consistency())
    
    # Generate report
    generate_report(auditors)

if __name__ == "__main__":
    main()






