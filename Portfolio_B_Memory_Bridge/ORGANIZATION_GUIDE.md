# 📁 PORTFOLIO B: ORGANIZATION GUIDE
## Clean Folder Structure - Everything in Its Place

**Date:** December 19, 2025  
**Status:** ✅ REORGANIZED - Clean and Professional  
**Structure:** 3-tier (Current / Docs / Archive)  

---

## 🎯 THE CLEAN STRUCTURE

```
Portfolio_B_Memory_Bridge/
│
├── README.md                    ← START HERE (updated, comprehensive)
├── requirements.txt             ← pip install -r requirements.txt
├── RUN_SOVEREIGN_AUDIT.py       ← Main validation (run this!)
│
├── 01_Incast_Backpressure/      ← CURRENT simulations (use these)
├── 02_Deadlock_Release_Valve/
├── 03_Noisy_Neighbor_Sniper/
├── 04_Stranded_Memory_Borrowing/
├── _08_Grand_Unified_Cortex/
│
├── shared/                      ← Common utilities
│   ├── physics_engine_v2.py     ← All timing constants (cited)
│   ├── cache_model_v2.py        ← 4D feature tracking
│   ├── traffic_generator.py     ← Bursty AI workloads
│   └── ...
│
├── results/                     ← Consolidated graphs (8 PNGs)
│   ├── buffer_comparison.png    ← THE MONEY SHOT
│   ├── adversarial_sniper_proof.png
│   └── ...
│
├── docs/                        ← All documentation
│   ├── VALIDATION_RESULTS.md    ← Simulation proof
│   ├── FORENSIC_AUDIT_FINDINGS.md
│   ├── CHAIN_OF_CUSTODY_AUDIT.md
│   └── ...
│
├── _archive/                    ← Legacy code (don't use)
│   ├── legacy_simulations/      ← Old _01, _02, _03, _04
│   └── old_docs/
│
├── data_room/                   ← Supporting materials
│
├── deep_audit_monte_carlo.py    ← Statistical stability checker
├── scaling_and_overhead_validation.py
├── perfect_storm_unified_dashboard.py
└── validate_criteria.py
```

---

## ✅ WHAT CHANGED (Cleanup Actions)

### Before (Messy)

```
❌ Duplicate folders (_01_Incast vs 01_Incast_Backpressure)
❌ 9 markdown files scattered in root
❌ Results in multiple locations
❌ No clear distinction between current and legacy
❌ Hard to navigate
```

### After (Clean)

```
✅ Current simulations: 01, 02, 03, 04 (clear naming)
✅ All docs moved to docs/ folder
✅ Legacy code moved to _archive/
✅ Results consolidated in results/
✅ Clear README with navigation
✅ Easy to find everything
```

---

## 📂 FOLDER DETAILS

### CURRENT SIMULATIONS (Use These)

**01_Incast_Backpressure/**
- `corrected_validation.py` - Streamlined, fast (1.6s runtime)
- `results/` - 4 graphs including THE MONEY SHOT
- **Proves:** 100% drop reduction (81% → 0%)

**02_Deadlock_Release_Valve/**
- `predictive_deadlock_audit.py` - Graph-theoretic detection
- `results/` - 1 graph showing surgical prevention
- **Proves:** 72× faster recovery (can't patent, Broadcom overlap)

**03_Noisy_Neighbor_Sniper/**
- `adversarial_sniper_tournament.py` - 4D vs 1D comparison
- `intent_aware_calibration.py` - Bayesian false-positive prevention
- `results/` - 1 graph showing gaming resistance
- **Proves:** 90× game resistance + <3% false positives

**04_Stranded_Memory_Borrowing/**
- `qos_aware_borrowing_audit.py` - QoS protection validation
- `results/` - 1 graph showing local SLA preservation
- **Proves:** 45% utilization gain without SLA violations

**_08_Grand_Unified_Cortex/**
- `perfect_storm.py` - System-level coordination test
- `coordination_matrix.py` - The "brain"
- `telemetry_bus.py` - Event distribution
- `verify_coordination.py` - Proves brain controls reflexes
- **Proves:** 1.05× coordination benefit (honest, after rigging removal)

---

### SHARED UTILITIES (Common Code)

**shared/**
- `physics_engine_v2.py` (528 lines) - All timing constants cited from datasheets
- `cache_model_v2.py` (118 lines) - 4D feature tracking for Sniper
- `traffic_generator.py` (554 lines) - Bursty AI workload models
- `physics_engine.py` - Legacy (older version, still valid)
- `tournament_harness.py` - Comparison framework
- `visualization.py` - Graphing utilities

**All constants traced to:**
- CXL 3.0 Specification
- PCIe Gen5 Base Spec
- JEDEC JESD79-5 (DRAM)
- Broadcom Tomahawk 5 Datasheet

---

### RESULTS (All Graphs)

**results/**
- All 8 publication-quality graphs (300 DPI)
- Consolidated from individual simulation results/
- Ready for papers, presentations, investor decks

**Key graphs:**
1. `buffer_comparison.png` - Baseline overflow vs controlled (THE MONEY SHOT)
2. `adversarial_sniper_proof.png` - 1D vs 4D detection
3. `perfect_storm_unified_dashboard.png` - System coordination
4. `qos_borrowing_proof.png` - Local SLA protection

---

### DOCS (All Documentation)

**docs/**
- `VALIDATION_RESULTS.md` (20 pages) - All simulation results
- `FORENSIC_AUDIT_FINDINGS.md` (10 pages) - Rigging disclosure
- `CHAIN_OF_CUSTODY_AUDIT.md` (30 pages) - Physics → claims traceability
- `REBUTTAL_TO_CRITIQUE.md` (65 pages) - How we fixed critique issues
- `REBUILD_PLAN.md` (20 pages) - Roadmap of all fixes
- Plus 3 more supporting docs

**All critical docs moved here for clean organization.**

---

### ARCHIVE (Legacy - Don't Use)

**_archive/legacy_simulations/**
- `_01_Incast_Backpressure/` - Old full SimPy version (slower but has proper imports)
- `_02_Deadlock_Release_Valve/` - Old version
- `_03_Noisy_Neighbor_Sniper/` - Old version
- `_04_Stranded_Memory_Borrowing/` - Old version

**Why kept:**
- Historical reference
- Full SimPy implementations (good for patent enablement)
- Tournament comparison framework
- CSV result files

**When to use:**
- Patent filing (show full implementation)
- Deep technical review (more comprehensive)
- Historical comparison

---

## 🎯 NAVIGATION GUIDE

### "I want to run everything"

```bash
python RUN_SOVEREIGN_AUDIT.py
```

**Output:** PASSED/FAILED + summary of all 8 simulations

---

### "I want to understand one innovation"

**Pick your topic:**

**Incast?** → `01_Incast_Backpressure/corrected_validation.py`  
**Gaming?** → `03_Noisy_Neighbor_Sniper/adversarial_sniper_tournament.py`  
**Deadlock?** → `02_Deadlock_Release_Valve/predictive_deadlock_audit.py`  
**Memory?** → `04_Stranded_Memory_Borrowing/qos_aware_borrowing_audit.py`  
**System?** → `_08_Grand_Unified_Cortex/perfect_storm.py`  

**Each file is self-contained and documented.**

---

### "I want to see the proof"

**Go to:** `docs/VALIDATION_RESULTS.md`

**Contains:**
- All 8 simulation results
- All graphs explained
- All claims backed by evidence

---

### "I want to send to buyer"

**Go to parent directory:** `../`

**Key files:**
- `PORTFOLIO_B_MASTER_SUMMARY.md` (all claims)
- `FINAL_HONEST_PACKAGE.md` (email template)
- `FORENSIC_AUDIT_FINDINGS.md` (disclosure)

**Plus graphs from:** `results/` folder (zip them)

---

## ✅ VERIFICATION (Still Works After Cleanup)

### Test 1: Main Audit

```bash
python RUN_SOVEREIGN_AUDIT.py
```

**Status:** ✅ PASSED

**All 8 simulations working:**
- Physics engine (0.05s)
- Incast (1.6s)
- Deadlock (1.3s)
- Sniper (1.2s)
- Intent (0.1s)
- Borrowing (1.3s)
- Scaling (0.7s)
- Perfect Storm (1.7s)

---

### Test 2: Documentation Present

**Check:** All markdown files moved to `docs/`

**Status:** ✅ COMPLETE

**Files in docs/:** 8 markdown documents
- All audit reports
- All validation results
- All forensic findings

---

### Test 3: Graphs Available

**Check:** All graphs in `results/`

**Status:** ✅ COMPLETE

**Count:** 8 publication-quality PNGs
- All 300 DPI
- All regenerated after cleanup
- All ready for use

---

## 🎯 WHAT'S WHERE (Quick Lookup)

### Code

| What | Where |
|------|-------|
| Physics constants | `shared/physics_engine_v2.py` |
| Incast simulation | `01_Incast_Backpressure/corrected_validation.py` |
| Sniper simulation | `03_Noisy_Neighbor_Sniper/adversarial_sniper_tournament.py` |
| Deadlock simulation | `02_Deadlock_Release_Valve/predictive_deadlock_audit.py` |
| Borrowing simulation | `04_Stranded_Memory_Borrowing/qos_aware_borrowing_audit.py` |
| System coordination | `_08_Grand_Unified_Cortex/perfect_storm.py` |
| Main validation | `RUN_SOVEREIGN_AUDIT.py` |

---

### Documentation

| What | Where |
|------|-------|
| All validated claims | `../PORTFOLIO_B_MASTER_SUMMARY.md` (parent dir) |
| Simulation proof | `docs/VALIDATION_RESULTS.md` |
| Forensic disclosure | `docs/FORENSIC_AUDIT_FINDINGS.md` |
| Chain of custody | `docs/CHAIN_OF_CUSTODY_AUDIT.md` |
| Email template | `../FINAL_HONEST_PACKAGE.md` (parent dir) |

---

### Graphs

| What | Where |
|------|-------|
| All graphs | `results/` (consolidated) |
| Incast proof | `results/buffer_comparison.png` |
| Gaming resistance | `results/adversarial_sniper_proof.png` |
| System coordination | `results/perfect_storm_unified_dashboard.png` |

---

## 🎯 RECOMMENDED WORKFLOW

### For Validation

1. Run main audit: `python RUN_SOVEREIGN_AUDIT.py`
2. Check output: Should show "AUDIT STATUS: PASSED"
3. Review graphs: Check `results/` folder
4. Done ✅

---

### For Understanding

1. Read: `README.md` (this file) - Overview
2. Read: `../INNOVATIONS_QUICK_SUMMARY.md` - 5-minute summary
3. Read: `../ALL_INNOVATIONS_AND_PATENTS_EXPLAINED.md` - Complete guide
4. Read: `docs/VALIDATION_RESULTS.md` - Proof

---

### For Sending

1. Read: `../FINAL_HONEST_PACKAGE.md` - Email template
2. Attach: `../PORTFOLIO_B_MASTER_SUMMARY.md`
3. Attach: `docs/VALIDATION_RESULTS.md`
4. Attach: `docs/FORENSIC_AUDIT_FINDINGS.md`
5. Zip: `results/*.png`
6. Send ✅

---

## 🚀 FINAL STATUS

**Organization:** ✅ CLEAN (legacy moved to _archive, docs moved to docs/)  
**README:** ✅ UPDATED (comprehensive navigation guide)  
**Validation:** ✅ PASSING (RUN_SOVEREIGN_AUDIT.py still works)  
**Documentation:** ✅ ORGANIZED (all in docs/ folder)  
**Graphs:** ✅ CONSOLIDATED (all in results/ folder)  

**The codebase is now professional, organized, and ready for acquisition due diligence.**

---

**Next action:** Send the package to Broadcom using template in `../FINAL_HONEST_PACKAGE.md`

**Everything is clean, organized, and validated.** ✅



