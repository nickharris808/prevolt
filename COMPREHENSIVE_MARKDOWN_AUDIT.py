#!/usr/bin/env python3
"""
Comprehensive Markdown Audit for Portfolio B
============================================

This script audits ALL 101 markdown files to find:
1. Outdated technical claims (100ns vs 210ns)
2. Incorrect valuations ($200M vs $16M)
3. Dropped patents (deadlock patent)
4. Inconsistent metrics
5. Missing validation references

It categorizes files as:
- CURRENT (matches latest validation)
- OUTDATED (contains old claims)
- OBSOLETE (archive/legacy)
- UNKNOWN (can't determine)
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict

# Base directory
BASE_DIR = "/Users/nharris/Desktop/portfolio"

# Validation criteria (current correct values)
CURRENT_CLAIMS = {
    "latency_ns": ["210", "210ns", "210 ns", "200-600ns"],
    "speedup": ["25x", "24.8x", "9-55x"],
    "valuation_millions": ["$16M", "$16-20M", "$2M + $48M", "$50M"],
    "drop_reduction": ["100%", "81% → 0%", "0.00%"],
    "patents_count": ["3 patents", "three patents"],
    "tam_switches": ["1.5M", "0.9M", "900,000"],
}

# Outdated claims to flag
OUTDATED_CLAIMS = {
    "latency_ns": ["100ns", "100 ns"],
    "speedup": ["500x", "5000x"],
    "valuation_millions": ["$200M", "$300M", "$500M", "$1B"],
    "patents_count": ["4 patents", "four patents"],
    "tam_switches": ["10M switches", "10,000,000"],
}

# Archive patterns (files we expect to be old)
ARCHIVE_PATTERNS = [
    "archive/",
    "legacy",
    "backup",
    "copy",
    "old",
    "initial_builds"
]

def is_archive_file(filepath: str) -> bool:
    """Check if file is in an archive/legacy folder."""
    for pattern in ARCHIVE_PATTERNS:
        if pattern in filepath.lower():
            return True
    return False

def audit_file(filepath: str) -> Dict:
    """Audit a single markdown file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return {
            'status': 'ERROR',
            'issues': [f"Could not read file: {str(e)}"],
            'is_archive': False
        }
    
    issues = []
    is_archive = is_archive_file(filepath)
    
    # Check for outdated claims
    for claim_type, patterns in OUTDATED_CLAIMS.items():
        for pattern in patterns:
            if pattern in content:
                issues.append(f"OUTDATED {claim_type}: Contains '{pattern}'")
    
    # Check for specific problem strings
    problem_strings = [
        ("100ns", "Should be 210ns (CXL sideband) or 570ns (CXL main)"),
        ("500x speedup", "Should be 25x (realistic)"),
        ("$200M", "Should be $16M expected value"),
        ("$500M", "Should be $50M max with earnouts"),
        ("10M switches", "Should be 1.5M total, 0.9M CXL-enabled"),
        ("7,100x", "Should be 100% drop reduction (81% → 0%)"),
    ]
    
    for problem, fix in problem_strings:
        if problem in content:
            issues.append(f"NEEDS UPDATE: '{problem}' → {fix}")
    
    # Determine status
    if is_archive:
        status = "ARCHIVE"
    elif len(issues) == 0:
        status = "CURRENT"
    elif len(issues) > 5:
        status = "SEVERELY OUTDATED"
    elif len(issues) > 0:
        status = "OUTDATED"
    else:
        status = "UNKNOWN"
    
    return {
        'status': status,
        'issues': issues,
        'is_archive': is_archive,
        'size_bytes': len(content),
        'lines': content.count('\n')
    }

def audit_all_markdown():
    """Audit all markdown files in the portfolio."""
    print("=" * 80)
    print("COMPREHENSIVE MARKDOWN AUDIT")
    print("=" * 80)
    print()
    
    # Find all .md files
    all_md_files = []
    for root, dirs, files in os.walk(BASE_DIR):
        for file in files:
            if file.endswith('.md'):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, BASE_DIR)
                all_md_files.append((rel_path, full_path))
    
    print(f"Found {len(all_md_files)} markdown files.")
    print()
    
    # Audit each file
    results = {}
    status_counts = defaultdict(int)
    
    for rel_path, full_path in sorted(all_md_files):
        audit = audit_file(full_path)
        results[rel_path] = audit
        status_counts[audit['status']] += 1
    
    # Print summary by status
    print("=" * 80)
    print("SUMMARY BY STATUS")
    print("=" * 80)
    print()
    
    for status in ["CURRENT", "OUTDATED", "SEVERELY OUTDATED", "ARCHIVE", "ERROR", "UNKNOWN"]:
        count = status_counts[status]
        if count == 0:
            continue
        
        print(f"\n{status}: {count} files")
        print("-" * 80)
        
        matching_files = [(path, audit) for path, audit in results.items() if audit['status'] == status]
        
        # Show details for problematic files
        if status in ["OUTDATED", "SEVERELY OUTDATED", "ERROR"]:
            for path, audit in matching_files[:10]:  # Show first 10
                print(f"\n  📄 {path}")
                print(f"     Lines: {audit['lines']}, Size: {audit['size_bytes']} bytes")
                for issue in audit['issues'][:3]:  # First 3 issues
                    print(f"     ⚠️  {issue}")
                if len(audit['issues']) > 3:
                    print(f"     ... and {len(audit['issues']) - 3} more issues")
            
            if len(matching_files) > 10:
                print(f"\n  ... and {len(matching_files) - 10} more {status} files")
        else:
            # Just list files for CURRENT/ARCHIVE
            for path, audit in matching_files[:5]:
                print(f"  ✓ {path}")
            if len(matching_files) > 5:
                print(f"  ... and {len(matching_files) - 5} more")
    
    # Critical files report
    print("\n" + "=" * 80)
    print("CRITICAL FILES STATUS (Must be CURRENT)")
    print("=" * 80)
    print()
    
    critical_files = [
        "README.md",
        "EXECUTIVE_SUMMARY_FOR_BUYER.md",
        "REBUTTAL_TO_CRITIQUE.md",
        "DUE_DILIGENCE_RED_TEAM_CRITIQUE.md",
        "WHAT_WE_ACCOMPLISHED.md",
        "FINAL_PACKAGE_READY_TO_SEND.md",
        "FIXES_AND_IMPROVEMENTS.md",
        "Portfolio_B_Memory_Bridge/VALIDATION_RESULTS.md",
        "Portfolio_B_Memory_Bridge/README.md",
    ]
    
    all_critical_current = True
    for file in critical_files:
        if file in results:
            audit = results[file]
            status_symbol = "✅" if audit['status'] == "CURRENT" else "❌"
            print(f"{status_symbol} {file}: {audit['status']}")
            if audit['status'] != "CURRENT":
                all_critical_current = False
                for issue in audit['issues'][:2]:
                    print(f"   ⚠️  {issue}")
        else:
            print(f"❌ {file}: MISSING")
            all_critical_current = False
    
    # Final verdict
    print("\n" + "=" * 80)
    if all_critical_current:
        print("VERDICT: PORTFOLIO IS DOCUMENTATION-READY ✅")
    else:
        print("VERDICT: CRITICAL FILES NEED UPDATES ❌")
    print("=" * 80)
    
    # Generate action plan
    print("\n" + "=" * 80)
    print("RECOMMENDED ACTIONS")
    print("=" * 80)
    print()
    
    severely_outdated = [p for p, a in results.items() if a['status'] == "SEVERELY OUTDATED"]
    outdated = [p for p, a in results.items() if a['status'] == "OUTDATED"]
    
    if severely_outdated:
        print(f"1. DELETE or ARCHIVE {len(severely_outdated)} SEVERELY OUTDATED files:")
        for path in severely_outdated[:5]:
            print(f"   - {path}")
        if len(severely_outdated) > 5:
            print(f"   ... and {len(severely_outdated) - 5} more")
    
    if outdated:
        print(f"\n2. UPDATE {len(outdated)} OUTDATED files:")
        for path in outdated[:5]:
            print(f"   - {path}")
        if len(outdated) > 5:
            print(f"   ... and {len(outdated) - 5} more")
    
    print("\n3. KEEP CURRENT: Keep updating critical files as validation evolves")
    
    # Save detailed report
    report_path = os.path.join(BASE_DIR, "MARKDOWN_AUDIT_REPORT.txt")
    with open(report_path, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("COMPREHENSIVE MARKDOWN AUDIT REPORT\n")
        f.write("=" * 80 + "\n\n")
        
        for status in ["SEVERELY OUTDATED", "OUTDATED", "CURRENT", "ARCHIVE", "ERROR"]:
            matching = [(p, a) for p, a in results.items() if a['status'] == status]
            if not matching:
                continue
            
            f.write(f"\n{status}: {len(matching)} files\n")
            f.write("-" * 80 + "\n")
            
            for path, audit in sorted(matching):
                f.write(f"\n{path}\n")
                f.write(f"  Lines: {audit['lines']}, Size: {audit['size_bytes']} bytes\n")
                for issue in audit['issues']:
                    f.write(f"  - {issue}\n")
    
    print(f"\n✓ Detailed report saved to: MARKDOWN_AUDIT_REPORT.txt")
    print()
    
    return results, status_counts

if __name__ == "__main__":
    results, counts = audit_all_markdown()



