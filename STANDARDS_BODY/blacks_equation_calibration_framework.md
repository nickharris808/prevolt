# Black's Equation Calibration Framework
**Purpose:** Per-Foundry MTTF Parameter Calibration  
**Status:** Methodology Defined  

---

## 1. The Parameter Uncertainty Problem

**Black's Equation:** MTTF = A / J^n × exp(Ea / kT)

**Uncertain Parameters:**
- **Ea (Activation Energy):** Varies 0.8-1.2 eV based on:
  - Copper purity
  - Barrier layer material (TaN, Ti, Ta)
  - Grain structure
- **n (Current Density Exponent):** Typically 2.0, but ranges 1.5-2.5
- **A (Material Constant):** Foundry-specific pre-factor

**Impact:** ±250,000x difference in MTTF prediction

---

## 2. Calibration Procedure

### Step 1: Accelerated Aging Tests
**Setup:**
1. Obtain 100 TSV test structures from target foundry
2. Subject to elevated temperature (150°C) and current (2× normal)
3. Monitor resistance over time until failure

**Analysis:**
- Plot: ln(MTTF) vs. 1/T (Arrhenius plot)
- Extract: Ea from slope
- Validate: n from current density dependence

**Timeline:** 6-8 weeks (accelerated)  
**Cost:** $80-120k

---

### Step 2: Foundry-Specific Parameter Database
**Create:**
```yaml
foundry_parameters:
  TSMC_N5:
    Ea_eV: 0.95
    n: 2.1
    A: 1.2e-6
  Samsung_5nm:
    Ea_eV: 0.88
    n: 1.9
    A: 1.5e-6
```

**Integration:** Update `advanced_tsv_reliability_model.py` to read from this config

---

### Step 3: Sensitivity-Bounded Claims
**Current Claim:** "19.5x MTTF extension"  
**Calibrated Claim:** "10-30x MTTF extension depending on Ea (0.8-1.0 eV range)"

**Impact:** More honest, more defensible

---

## 3. Interim Solution (Pre-Calibration)

**Use Conservative Bounds:**
```python
Ea_min = 0.8 * 1.602e-19  # eV to Joules
Ea_max = 1.0 * 1.602e-19

mttf_min = calculate_mttf(Ea_min, ...)
mttf_max = calculate_mttf(Ea_max, ...)

# Report range
print(f"MTTF Extension: {mttf_min:.1f}x - {mttf_max:.1f}x")
```

**Advantage:** Acknowledges uncertainty while providing bounds

---

**Status:** Framework defined, execution pending foundry partnership.

**End of Calibration Framework**








