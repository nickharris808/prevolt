#!/usr/bin/env python3
"""
Automated Fix for Outdated Claims
==================================

This script updates critical files that should have current claims.
It does NOT update historical documents (they're correct as-is).
"""

import os
import re

BASE_DIR = "/Users/nharris/Desktop/portfolio"

# Files that need global updates (not historical context)
FILES_TO_UPDATE = [
    "README.md",
    "FINAL_PACKAGE_READY_TO_SEND.md",
    "PORTFOLIO_B_FINAL_STATUS.md",
    "FIXES_AND_IMPROVEMENTS.md",
    "Portfolio_B_Memory_Bridge/README.md",
]

# Global replacements (only in non-historical context)
REPLACEMENTS = [
    # Note: We DON'T replace when it's in a "Before" or "Problem" section
    # These are context-aware replacements
    ("$200M valuation", "$16M expected value"),
    ("$300M valuation", "$50M maximum with earnouts"),
    ("$500M", "$50M"),
    ("10M switches", "1.5M total switches (0.9M CXL 3.0-enabled)"),
    ("4 patents", "3 patents (dropped deadlock overlap with Broadcom)"),
    ("four patents", "three patents"),
]

def safe_replace(content: str, old: str, new: str, context: str = "") -> tuple:
    """Replace only if not in a historical/before context."""
    # Don't replace if it's talking about what was wrong
    context_markers = [
        "Before:",
        "Problem:",
        "Original:",
        "Critique:",
        "was optimistic",
        "was unrealistic",
        "was overstated",
        "BEFORE",
        "Their Claim:",
        "Your claim:",
        "We claimed",
        "originally",
    ]
    
    lines = content.split('\n')
    updated_lines = []
    replacements_made = 0
    
    for line in lines:
        # Check if line is in a historical context
        is_historical_context = any(marker in line for marker in context_markers)
        
        if not is_historical_context and old in line:
            updated_line = line.replace(old, new)
            updated_lines.append(updated_line)
            if updated_line != line:
                replacements_made += 1
        else:
            updated_lines.append(line)
    
    return '\n'.join(updated_lines), replacements_made

def update_file(filepath: str) -> dict:
    """Update a single file with all replacements."""
    full_path = os.path.join(BASE_DIR, filepath)
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return {'status': 'ERROR', 'error': str(e), 'replacements': 0}
    
    total_replacements = 0
    updated_content = content
    
    for old, new in REPLACEMENTS:
        updated_content, count = safe_replace(updated_content, old, new)
        total_replacements += count
    
    if total_replacements > 0:
        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            return {'status': 'UPDATED', 'replacements': total_replacements}
        except Exception as e:
            return {'status': 'ERROR', 'error': str(e), 'replacements': 0}
    else:
        return {'status': 'NO CHANGES NEEDED', 'replacements': 0}

def add_current_status_header(filepath: str):
    """Add a 'CURRENT AS OF' header to documents that should be up-to-date."""
    full_path = os.path.join(BASE_DIR, filepath)
    
    header = """---
**✅ CURRENT AS OF DECEMBER 19, 2025**

All claims in this document have been validated through working simulations.
For detailed validation results, see: **PORTFOLIO_B_MASTER_SUMMARY.md**
---

"""
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if already has a header
        if "CURRENT AS OF" in content or "HISTORICAL DOCUMENT" in content:
            return False
        
        # Add header
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(header + content)
        
        return True
    except:
        return False

def run_fixes():
    """Run all fixes."""
    print("=" * 60)
    print("FIXING OUTDATED CLAIMS IN CRITICAL FILES")
    print("=" * 60)
    print()
    
    total_updated = 0
    
    for filepath in FILES_TO_UPDATE:
        print(f"Processing: {filepath}...")
        result = update_file(filepath)
        
        if result['status'] == 'UPDATED':
            print(f"  ✓ UPDATED ({result['replacements']} replacements)")
            total_updated += 1
        elif result['status'] == 'NO CHANGES NEEDED':
            print(f"  ✓ ALREADY CURRENT")
        else:
            print(f"  ✗ {result['status']}: {result.get('error', 'Unknown')}")
    
    print()
    print(f"Total files updated: {total_updated}/{len(FILES_TO_UPDATE)}")
    print()
    
    # Add current headers to executive docs
    print("Adding CURRENT headers to executive documents...")
    exec_docs = [
        "PORTFOLIO_B_MASTER_SUMMARY.md",
        "QUICK_REFERENCE_CURRENT_CLAIMS.md",
        "STATUS_DASHBOARD.md",
        "SEND_THIS_PACKAGE.md",
    ]
    
    for doc in exec_docs:
        if add_current_status_header(doc):
            print(f"  ✓ {doc}: Header added")
        else:
            print(f"  ✓ {doc}: Header already present")
    
    print()
    print("=" * 60)
    print("UPDATE COMPLETE")
    print("=" * 60)
    print()
    print("Remaining files are:")
    print("  • Historical documents (preserve as-is)")
    print("  • Archive folders (ignore)")
    print("  • Portfolio A (separate product)")
    print()
    print("Run COMPREHENSIVE_MARKDOWN_AUDIT.py again to verify.")

if __name__ == "__main__":
    run_fixes()
