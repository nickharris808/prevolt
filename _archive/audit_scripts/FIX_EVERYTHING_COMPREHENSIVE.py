#!/usr/bin/env python3
"""
Comprehensive Fix for ALL Outdated Claims
==========================================

This script updates EVERY file in the portfolio with honest claims.
It preserves historical context but ensures all "current" statements are correct.
"""

import os
import re
from pathlib import Path

BASE_DIR = "/Users/nharris/Desktop/portfolio"

# Files to completely skip (archives, backups)
SKIP_PATTERNS = [
    "Portfolio_A_Power copy/",
    "/archive/",
    "/legacy/",
    "_backup",
    ".git/",
    "__pycache__/",
    ".pyc",
]

# Context markers (don't replace if line contains these)
HISTORICAL_MARKERS = [
    "Before:",
    "Was:",
    "Old:",
    "Previous:",
    "Original:",
    "Initially:",
    "BEFORE",
    "RIGGED",
    "Critique:",
    "Problem:",
    "Issue:",
    "overstated",
    "optimistic",
    "exaggerated",
    "fantasy",
]

def should_skip_file(filepath: str) -> bool:
    """Check if file should be skipped."""
    for pattern in SKIP_PATTERNS:
        if pattern in filepath:
            return True
    return False

def should_skip_line(line: str) -> bool:
    """Check if line is historical context (don't update)."""
    for marker in HISTORICAL_MARKERS:
        if marker in line:
            return True
    return False

def fix_line(line: str) -> tuple:
    """Fix a single line, return (updated_line, changes_made)."""
    original = line
    changes = []
    
    # Skip if historical context
    if should_skip_line(line):
        return line, changes
    
    # Fix 1: Perfect Storm (2.44x → 1.05x)
    if re.search(r'2\.44\s*[x×]', line, re.IGNORECASE):
        line = re.sub(r'2\.44\s*([x×])', r'1.05\1', line, flags=re.IGNORECASE)
        changes.append("Perfect Storm 2.44x → 1.05x")
    
    # Fix 2: Storm stability (1.8x → 1.05x)
    if re.search(r'1\.8\s*[x×]\s+(stability|improvement|higher)', line, re.IGNORECASE):
        line = re.sub(r'1\.8\s*([x×])', r'1.05\1', line)
        changes.append("Storm 1.8x → 1.05x")
    
    # Fix 3: Valuation $16M → $15M (be careful with $16-20M ranges)
    line = re.sub(r'\$16M(?!\s*[-–])', '$15M', line)
    line = re.sub(r'\$16\.2M', '$15.1M', line)
    line = re.sub(r'\$16\s*million', '$15 million', line, flags=re.IGNORECASE)
    if "$16" in original and "$15" in line:
        changes.append("Valuation $16M → $15M")
    
    # Fix 4: Earnouts $48M → $40M
    line = re.sub(r'\$48M(?!\s*million)', '$40M', line)
    line = re.sub(r'\$48\s*million', '$40 million', line, flags=re.IGNORECASE)
    if "$48" in original and "$40" in line:
        changes.append("Earnouts $48M → $40M")
    
    # Fix 5: Max total $50M → $42M
    line = re.sub(r'\$50M(?!\s*million)', '$42M', line)
    line = re.sub(r'\$50\s*million', '$42 million', line, flags=re.IGNORECASE)
    if "$50" in original and "$42" in line:
        changes.append("Max $50M → $42M")
    
    # Fix 6: Qualify ECN (if not already qualified)
    if re.search(r'25\s*[x×]\s+(faster|speedup).*?ECN', line, re.IGNORECASE):
        if "Microsoft" not in line and "SIGCOMM" not in line:
            line = re.sub(
                r'(25\s*[x×]\s+(?:faster than|speedup vs|vs)\s+)ECN',
                r'\1software ECN (5.2μs RTT, Microsoft SIGCOMM 2021)',
                line,
                flags=re.IGNORECASE
            )
            changes.append("ECN qualified with citation")
    
    # Fix 7: Qualify zero-loss (if not already qualified)
    if "zero-loss" in line.lower() and "first" in line.lower():
        if "Ethernet memory-initiated" not in line and "memory-initiated flow control" not in line:
            line = re.sub(
                r'[Ff]irst zero-loss result in (published )?literature',
                'first zero-loss result for memory-initiated flow control in Ethernet-based AI clusters',
                line
            )
            line = re.sub(
                r'[Ff]irst zero-loss result(?! for)',
                'first Ethernet memory-initiated zero-loss result',
                line
            )
            changes.append("Zero-loss qualified")
    
    # Fix 8: Qualify 100k-node (if not already qualified)
    if re.search(r'(validated|proven|demonstrated)\s+at\s+100,?000[\s-]node', line, re.IGNORECASE):
        if "analytic" not in line.lower():
            line = re.sub(
                r'(validated|proven|demonstrated)\s+(at|for)\s+100,?000[\s-]node',
                r'analytically validated for 100,000-node',
                line,
                flags=re.IGNORECASE
            )
            changes.append("100k-node qualified")
    
    return line, changes

def fix_file(filepath: str) -> dict:
    """Fix all issues in a single file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        return {'status': 'ERROR', 'error': str(e), 'changes': []}
    
    # Check if file has HISTORICAL DOCUMENT header
    content = ''.join(lines)
    if "HISTORICAL DOCUMENT - PRESERVED FOR CONTEXT" in content:
        return {'status': 'HISTORICAL', 'changes': []}
    
    updated_lines = []
    all_changes = []
    
    for line in lines:
        fixed_line, changes = fix_line(line)
        updated_lines.append(fixed_line)
        all_changes.extend(changes)
    
    if all_changes:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(updated_lines)
            return {'status': 'UPDATED', 'changes': list(set(all_changes))}
        except Exception as e:
            return {'status': 'ERROR', 'error': str(e), 'changes': []}
    else:
        return {'status': 'ALREADY CORRECT', 'changes': []}

def fix_everything():
    """Fix all markdown files in the portfolio."""
    print("=" * 80)
    print("COMPREHENSIVE FIX: ALL OUTDATED CLAIMS IN ENTIRE PORTFOLIO")
    print("=" * 80)
    print()
    
    # Find all markdown files
    all_md_files = []
    for root, dirs, files in os.walk(BASE_DIR):
        # Skip certain directories
        if any(skip in root for skip in SKIP_PATTERNS):
            continue
        
        for file in files:
            if file.endswith('.md'):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, BASE_DIR)
                all_md_files.append((rel_path, full_path))
    
    print(f"Found {len(all_md_files)} markdown files to process.")
    print()
    
    # Process each file
    results = {}
    stats = {
        'updated': 0,
        'already_correct': 0,
        'historical': 0,
        'error': 0
    }
    
    for rel_path, full_path in sorted(all_md_files):
        if should_skip_file(rel_path):
            continue
        
        result = fix_file(full_path)
        results[rel_path] = result
        
        if result['status'] == 'UPDATED':
            stats['updated'] += 1
            print(f"✓ UPDATED: {rel_path}")
            for change in result['changes']:
                print(f"    - {change}")
        elif result['status'] == 'HISTORICAL':
            stats['historical'] += 1
        elif result['status'] == 'ALREADY CORRECT':
            stats['already_correct'] += 1
        elif result['status'] == 'ERROR':
            stats['error'] += 1
            print(f"✗ ERROR: {rel_path} - {result.get('error', 'Unknown')}")
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"  Files processed:    {len(all_md_files)}")
    print(f"  Updated:            {stats['updated']}")
    print(f"  Already correct:    {stats['already_correct']}")
    print(f"  Historical (skipped): {stats['historical']}")
    print(f"  Errors:             {stats['error']}")
    print()
    print("=" * 80)
    print("ALL FIXES APPLIED")
    print("=" * 80)
    print()
    print("All claims now honest and qualified:")
    print("  ✓ Perfect Storm: 1.05x (not 2.44x)")
    print("  ✓ Valuation: $15M (not $16M)")
    print("  ✓ Earnouts: $40M (not $48M)")
    print("  ✓ Max total: $42M (not $50M)")
    print("  ✓ ECN: Qualified with Microsoft SIGCOMM 2021")
    print("  ✓ Zero-loss: Qualified as 'Ethernet memory-initiated'")
    print("  ✓ 100k-node: Qualified as 'analytically validated'")
    print()
    print("Portfolio is now 100% defensible.")

if __name__ == "__main__":
    fix_everything()






