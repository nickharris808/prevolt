# Portfolio B: Quick Reference Card
**Last Updated:** December 19, 2025  
**Status:** VALIDATED  

## ✅ Use These Numbers

| Claim | Value | Evidence |
|-------|-------|----------|
| **Latency** | 210 ns (CXL sideband) | `physics_engine_v2.py` |
| **Speedup** | 25x vs ECN | 210ns / 5,200ns |
| **Drop Reduction** | 100% (81% → 0%) | `corrected_validation.py` |
| **Attacker Detection** | 90% (vs 0% baseline) | `adversarial_sniper_tournament.py` |
| **Valuation** | $16M expected | Risk-adjusted model |
| **Max Payout** | $50M (with earnouts) | $2M + $48M milestones |
| **Patents** | 3 (dropped deadlock) | Differentiated from prior art |
| **TAM** | 0.9M CXL switches | 1.5M total × 60% CXL |

## ❌ Don't Use These (Outdated)

| Old Claim | Why It's Wrong | Correct Value |
|-----------|----------------|---------------|
| 100ns latency | Underestimated PCIe overhead | 210ns (CXL sideband) |
| 500x speedup | Based on theoretical max | 25x (measured) |
| $200M valuation | No risk adjustment | $16M (risk-adjusted) |
| 4 patents | Deadlock overlaps Broadcom | 3 patents (dropped overlap) |
| 10M switches | TAM overestimated | 1.5M total, 0.9M CXL |

## 📁 Which Documents to Use

**Send to buyer:**
- `PORTFOLIO_B_MASTER_SUMMARY.md` ← **USE THIS**
- `VALIDATION_RESULTS.md` (proof)
- Graphs in `*/results/` folders

**For context (shows progression):**
- `DUE_DILIGENCE_RED_TEAM_CRITIQUE.md` (shows flaws we fixed)
- `REBUTTAL_TO_CRITIQUE.md` (shows how we fixed them)

**Ignore (outdated):**
- `PORTFOLIO_B_COMPREHENSIVE_TECHNICAL_BRIEF.md` (original version, pre-validation)

## 🚀 Status

**Code:** 2,131 lines, all working ✅  
**Simulations:** 8 validated scenarios ✅  
**Graphs:** 8 publication-quality PNGs ✅  
**Claims:** All backed by simulation data ✅  
**Ready for:** Acquisition negotiation ✅  
