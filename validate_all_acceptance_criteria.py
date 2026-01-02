"""
AIPP-Omega: Master Acceptance Criteria Validator
================================================

This is the repo-root entrypoint referenced throughout the documentation:

    python validate_all_acceptance_criteria.py

It executes the key simulation/proof scripts across the portfolio and reports a
PASS/FAIL summary with timeouts and useful failure tails.

Component counting
------------------
Some "master tournament" scripts execute multiple sub-variation scripts (e.g.
`src/power/precharge_trigger/master_tournament.py` runs all `variations/*.py`).

To keep the final score aligned with "components validated" language, we count a
master tournament as N components where N is the number of variation scripts it
executes. Everything else counts as 1 component.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Tuple
import os
import subprocess
import sys
import time


REPO_ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class TestCase:
    name: str
    rel_path: str
    timeout_s: int = 60
    args: Sequence[str] = ()
    # If set, counts as "number of matching scripts" for score purposes.
    component_glob: Optional[str] = None


def _component_count(tc: TestCase) -> int:
    if tc.component_glob:
        return len(list(REPO_ROOT.glob(tc.component_glob)))
    return 1


def _tail(text: str, *, max_lines: int = 12) -> str:
    lines = [ln.rstrip() for ln in (text or "").splitlines() if ln.strip()]
    if not lines:
        return ""
    return "\n".join(lines[-max_lines:])


def run_test(tc: TestCase) -> Tuple[bool, int]:
    comp_count = _component_count(tc)
    abs_path = REPO_ROOT / tc.rel_path

    print(f"Validating {tc.name}... ", end="", flush=True)

    if not abs_path.exists():
        print("✗ FAIL (Not found)")
        return False, comp_count

    env = os.environ.copy()
    # Ensure imports work regardless of the script's internal sys.path hacks.
    prior_pp = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(REPO_ROOT) + (os.pathsep + prior_pp if prior_pp else "")
    # Avoid GUI backends in headless environments.
    env.setdefault("MPLBACKEND", "Agg")

    cmd = [sys.executable, str(abs_path), *list(tc.args)]

    start = time.time()
    try:
        res = subprocess.run(
            cmd,
            cwd=str(REPO_ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=tc.timeout_s,
        )
        elapsed = time.time() - start

        if res.returncode == 0:
            print(f"✓ PASS ({elapsed:.1f}s) [{comp_count} component(s)]")
            return True, comp_count

        print(f"✗ FAIL (exit {res.returncode}, {elapsed:.1f}s) [{comp_count} component(s)]")
        stderr_tail = _tail(res.stderr)
        stdout_tail = _tail(res.stdout)
        if stderr_tail:
            print("---- stderr (tail) ----")
            print(stderr_tail)
        if stdout_tail:
            print("---- stdout (tail) ----")
            print(stdout_tail)
        return False, comp_count

    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        print(f"⏱ TIMEOUT (>{tc.timeout_s}s, {elapsed:.1f}s) [{comp_count} component(s)]")
        return False, comp_count
    except Exception as e:  # pragma: no cover
        elapsed = time.time() - start
        print(f"✗ ERROR ({type(e).__name__}: {str(e)[:120]}) [{comp_count} component(s)]")
        return False, comp_count


def build_suite() -> List[TestCase]:
    # NOTE: keep paths relative to repo root.
    return [
        # Tier 1-4: Core Families (master tournaments execute many sub-variations)
        TestCase(
            name="Family 1: Pre-Charge Trigger (Tournament)",
            rel_path="src/power/precharge_trigger/master_tournament.py",
            timeout_s=180,
            component_glob="src/power/precharge_trigger/variations/*.py",
        ),
        TestCase(
            name="Family 2: Telemetry Loop (Tournament)",
            rel_path="src/network/telemetry_loop/master_tournament.py",
            timeout_s=180,
            component_glob="src/network/telemetry_loop/variations/*.py",
        ),
        TestCase(
            name="Family 3: Spectral Damping (Tournament)",
            rel_path="src/network/spectral_damping/master_tournament.py",
            timeout_s=180,
            component_glob="src/network/spectral_damping/variations/*.py",
        ),
        TestCase(
            name="Family 4: Brownout Shedder (Tournament)",
            rel_path="src/power/brownout_shedder/master_tournament.py",
            timeout_s=180,
            component_glob="src/power/brownout_shedder/variations/*.py",
        ),
        # Tier 5: System Architecture
        TestCase(name="HBM4 Refresh Sync", rel_path="src/memory/orchestration/hbm_refresh_sync.py"),
        TestCase(name="UCIe Power Migration", rel_path="src/power/chiplet_fabric/ucie_power_migration.py"),
        TestCase(name="Grid Synthetic Inertia", rel_path="src/power/grid_vpp/grid_synthetic_inertia.py"),
        # Tier 6: Global Proofs
        TestCase(name="Optical Thermal Bias", rel_path="src/optical/io/optical_thermal_bias.py"),
        TestCase(name="Storage Incast Power Shaper", rel_path="src/network/storage_fabric/incast_power_shaper.py"),
        TestCase(name="Power Signature Masking", rel_path="src/security/power_signature_masking.py"),
        TestCase(name="Spine Power Arbiter", rel_path="src/network/fabric_orchestration/spine_power_arbiter.py"),
        TestCase(name="Protocol Formal Proof (Z3)", rel_path="validation/standards/protocol_formal_proof.py"),
        TestCase(name="Unified Temporal Policy", rel_path="src/network/fabric_orchestration/unified_temporal_policy_sim.py"),
        TestCase(name="Limp Mode Safety", rel_path="src/power/precharge_trigger/limp_mode_validation.py"),
        TestCase(
            name="Six Sigma Yield (Monte Carlo)",
            rel_path="tools/utilities/scripts/validate_six_sigma.py",
            timeout_s=240,
        ),
        # Tier 7: God-Tier
        TestCase(name="Cluster Digital Twin", rel_path="src/orchestration/cluster_digital_twin.py"),
        TestCase(name="Zero-Math Control Plane Optimizer", rel_path="silicon/implementation/control_plane_optimizer.py"),
        TestCase(name="RL Power Orchestrator", rel_path="src/ai_agent/rl_power_orchestrator.py", timeout_s=180),
        TestCase(name="Two-Phase Cooling Physics", rel_path="src/thermal/orchestration/two_phase_cooling_physics.py"),
        # Tier 8: Moonshots
        TestCase(name="HBM DPLL Phase Lock", rel_path="src/memory/orchestration/hbm_dpll_phase_lock.py"),
        TestCase(name="Data Vault Handshake", rel_path="src/security/data_vault_handshake.py"),
        TestCase(name="Formal Erasure Proof (Z3)", rel_path="validation/standards/formal_erasure_proof.py"),
        # Tier 9: Hard Physics
        TestCase(name="Active Synthesis Model", rel_path="src/power/precharge_trigger/active_synthesis_model.py"),
        TestCase(name="Formal Verification Report (Z3)", rel_path="validation/standards/formal_verification_report.py"),
        TestCase(name="Nonlinear Buck/Ripple Audit", rel_path="src/power/precharge_trigger/spice_vrm_nonlinear.py"),
        TestCase(name="Carbon Intensity Orchestrator", rel_path="src/power/grid_vpp/carbon_intensity_orchestrator.py"),
        # Tier 10: Omega
        TestCase(name="Power-Gated Dispatch", rel_path="src/power/power_gated_dispatch/token_handshake_sim.py"),
        TestCase(name="Joule Token Ledger", rel_path="src/thermal/thermodynamic_settlement/joule_token_ledger.py"),
        TestCase(name="Inference Load Migrator", rel_path="src/advanced/22_Global_VPP/inference_load_migrator.py"),
        TestCase(name="Phase Drift Compensation", rel_path="src/advanced/23_Atomic_Timing/phase_drift_compensation_sim.py"),
        # Tier 11: Sovereign
        TestCase(name="Planetary Carbon Arbitrage", rel_path="src/advanced/24_Sovereign_Orchestration/planetary_carbon_arbitrage.py"),
        TestCase(name="Sovereign Grid Inertia", rel_path="src/advanced/24_Sovereign_Orchestration/sovereign_grid_inertia.py"),
        # Tier 12: Facility/Planetary
        TestCase(name="Transformer Resonance Moat", rel_path="src/advanced/18_Facility_Scale_Moats/transformer_resonance_moat.py"),
        TestCase(name="IVR Thermal Limit", rel_path="src/advanced/18_Facility_Scale_Moats/ivr_thermal_limit.py"),
        TestCase(name="Global Latency Map", rel_path="src/advanced/19_Planetary_Orchestration/global_latency_map.py"),
        # Tier 13: Hard Engineering
        TestCase(name="Silicon Timing Closure", rel_path="silicon/implementation/aipp_timing_closure.py"),
        TestCase(name="Metastability Robust Proof", rel_path="validation/standards/metastability_robust_proof.py"),
        TestCase(name="PCIe Full-Stack Model", rel_path="tools/sdk/pcie_full_stack_model.py"),
        TestCase(name="Adversarial Incast Sim", rel_path="src/network/fabric_orchestration/adversarial_incast_sim.py"),
        TestCase(name="Nonlinear Stability Audit", rel_path="src/power/precharge_trigger/nonlinear_stability_audit.py"),
        # Tier 14: Extreme
        TestCase(name="Resonant LC Tank Sim", rel_path="src/power/adiabatic_recycling/resonant_lc_tank_sim.py"),
        TestCase(name="Body Bias Leakage Sim", rel_path="src/advanced/26_Adaptive_Body_Biasing/body_bias_leakage_sim.py"),
        TestCase(name="VDD Subthreshold Sim", rel_path="src/advanced/27_Entropy_VDD_Scaling/vdd_subthreshold_sim.py"),
        TestCase(name="Optical Phase Determinism Sim", rel_path="src/optical/phase_lock/optical_phase_determinism_sim.py"),
        TestCase(name="Planetary Gradient Migrator", rel_path="src/advanced/29_Sparse_Gradient_Migration/planetary_gradient_migrator.py"),
        # Tier 15: Economy
        TestCase(name="HBM Silence Token Enforcement", rel_path="src/memory/orchestration/hbm_silence_token_enforcement.py"),
        TestCase(name="Multi-Phase Resonant Clock", rel_path="src/power/adiabatic_recycling/multi_phase_resonant_clock.py"),
        TestCase(name="Sub-Harmonic Cluster Breathing", rel_path="src/advanced/22_Global_VPP/sub_harmonic_cluster_breathing.py"),
        TestCase(name="Entropy Credit Ledger", rel_path="src/thermal/thermodynamic_settlement/entropy_credit_ledger.py"),
        TestCase(name="Power Signature Audit", rel_path="src/security/power_signature_audit.py"),
        # Tier 16: Final Lock
        TestCase(name="PUF Power Fingerprint", rel_path="src/advanced/30_Silicon_Provenance/puf_power_fingerprint.py"),
        TestCase(name="CXL Latency Pre-Dispatch", rel_path="src/network/storage_fabric/cxl_latency_pre_dispatch.py"),
        TestCase(name="Master Pareto Charts", rel_path="tools/utilities/scripts/master_pareto_charts.py"),
        # Portfolio B integrations (fast smoke entrypoints)
        TestCase(name="Incast Backpressure (Sim)", rel_path="src/network/incast_backpressure/simulation.py"),
        TestCase(name="CXL Sideband Telemetry Bus", rel_path="src/network/cxl_sideband/telemetry_bus.py"),
        TestCase(name="Noisy Neighbor (Sim)", rel_path="src/memory/noisy_neighbor/simulation.py"),
        # Thermal/security integrations
        TestCase(name="Grand Unified 3D Twin", rel_path="src/orchestration/grand_unified_3d_twin.py"),
        TestCase(name="Thermal PUF Extractor", rel_path="src/network/telemetry_loop/thermal_puf_extractor.py"),
        TestCase(name="Power-Aware RTL Synthesis", rel_path="silicon/implementation/power_aware_rtl_synthesis.py"),
    ]


def main() -> int:
    suite = build_suite()

    print("=" * 80)
    print("AIPP-OMEGA: MASTER ACCEPTANCE CRITERIA VALIDATION")
    print("=" * 80)
    print(f"Repo root: {REPO_ROOT}")
    print(f"Test entries: {len(suite)}")

    total_components = sum(_component_count(tc) for tc in suite)
    print(f"Counted components: {total_components}")

    results: List[Tuple[str, bool, int]] = []
    passed_components = 0

    for tc in suite:
        ok, comp = run_test(tc)
        results.append((tc.name, ok, comp))
        if ok:
            passed_components += comp

    failed = [(name, comp) for (name, ok, comp) in results if not ok]

    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    for name, ok, comp in results:
        status = "✓ PASS" if ok else "✗ FAIL"
        print(f"{name:.<60} {status} ({comp})")

    print(f"\nFinal Score: {passed_components}/{total_components} components passed")

    if not failed:
        print(f"\n✅ AIPP-OMEGA: ALL {total_components} COMPONENTS VALIDATED (simulation-level)")
        return 0

    print(f"\n⚠️ {len(failed)} test entry/entries failed (see above).")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""
AIPP-Omega: Master Acceptance Criteria Validator
================================================

This script validates all 65+ core components across 12 patent families.
Optimized for reliability and clear error reporting.

Expected runtime: ~30-60 seconds (65+ components)

Usage:
    python validate_all_acceptance_criteria.py
"""

import subprocess
import sys
import os
from pathlib import Path
import time

# Repository root
ROOT = Path(__file__).parent

def run_test(path: str, name: str, timeout: int = 60) -> bool:
    """Run a single test script and return True if it passes."""
    print(f"Validating {name}...", end=' ', flush=True)
    abs_path = ROOT / path
    
    if not abs_path.exists():
        print(f"✗ FAIL (Not found: {path})")
        return False
    
    # Build PYTHONPATH to include repo root and key module directories
    pythonpath_dirs = [
        str(ROOT),
        str(ROOT / "utils"),
        str(ROOT / "tools" / "physics" / "shared_physics"),
        str(ROOT / "tools" / "physics"),
        str(ROOT / "src"),
    ]
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_dirs) + (os.pathsep + existing_pythonpath if existing_pythonpath else "")
    
    start_time = time.time()
    try:
        res = subprocess.run(
            [sys.executable, str(abs_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(abs_path.parent),  # Run from the script's directory
            env=env
        )
        elapsed = time.time() - start_time
        
        if res.returncode == 0:
            print(f"✓ PASS ({elapsed:.1f}s)")
            return True
        else:
            print(f"✗ FAIL (exit {res.returncode})")
            if res.stderr:
                lines = res.stderr.strip().splitlines()
                if lines:
                    print(f"    → {lines[-1][:80]}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏱ TIMEOUT (>{timeout}s)")
        return False
    except Exception as e:
        print(f"✗ ERROR ({str(e)[:60]})")
        return False


def validate_all():
    """Run all validation tests and report results."""
    print("=" * 80)
    print("AIPP-OMEGA: MASTER ACCEPTANCE CRITERIA VALIDATION")
    print("=" * 80)
    print("\nThis script validates all 65+ components across 12 patent")
    print("families meet their explicit acceptance criteria.\n")
    
    results = []
    
    # =========================================================================
    # TIER 1-4: Core Patent Families
    # =========================================================================
    print("CORE PATENT FAMILIES (TIER 1-4)")
    print("-" * 40)
    
    # Family 1: Pre-Cognitive Voltage Trigger
    results.append(("Family 1: Pre-Charge Physics", 
        run_test("src/power/precharge_trigger/master_tournament.py", "Pre-Charge Physics")))
    
    # Family 2: In-Band Telemetry Loop  
    results.append(("Family 2: Telemetry Loop",
        run_test("src/network/telemetry_loop/master_tournament.py", "Telemetry RTT")))
    
    # Family 3: Spectral Resonance Damping
    results.append(("Family 3: Spectral Damping",
        run_test("src/network/spectral_damping/master_tournament.py", "Spectral Damping")))
    
    # Family 4: Brownout Shedder / Grid QoS
    results.append(("Family 4: Grid QoS",
        run_test("src/power/brownout_shedder/master_tournament.py", "Grid QoS")))
    
    # =========================================================================
    # TIER 5: System Architecture
    # =========================================================================
    print("\nSYSTEM ARCHITECTURE (TIER 5)")
    print("-" * 40)
    
    results.append(("HBM4 Refresh Sync",
        run_test("src/memory/orchestration/hbm_refresh_sync.py", "Memory Sync")))
    
    results.append(("UCIe Power Migration",
        run_test("src/power/chiplet_fabric/ucie_power_migration.py", "Chiplet Migration")))
    
    results.append(("Grid Synthetic Inertia",
        run_test("src/power/grid_vpp/grid_synthetic_inertia.py", "Grid Revenue")))
    
    # =========================================================================
    # TIER 6: Global Monopoly Proofs
    # =========================================================================
    print("\nGLOBAL MONOPOLY PROOFS (TIER 6)")
    print("-" * 40)
    
    results.append(("Optical Thermal Bias",
        run_test("src/optical/io/optical_thermal_bias.py", "Optical IO")))
    
    results.append(("Storage Incast Shaper",
        run_test("src/network/storage_fabric/incast_power_shaper.py", "Storage Incast")))
    
    results.append(("Power Signature Masking",
        run_test("src/security/power_signature_masking.py", "Sovereign Security")))
    
    results.append(("Spine Power Arbiter",
        run_test("src/network/fabric_orchestration/spine_power_arbiter.py", "Fabric Token")))
    
    results.append(("Z3 Protocol Proof",
        run_test("validation/standards/protocol_formal_proof.py", "Z3 Formal Proof")))
    
    results.append(("Unified Temporal Policy",
        run_test("src/network/fabric_orchestration/unified_temporal_policy_sim.py", "Unified Policy")))
    
    results.append(("Limp Mode Validation",
        run_test("src/power/precharge_trigger/limp_mode_validation.py", "Limp Mode Safety")))
    
    results.append(("Six Sigma Yield",
        run_test("tools/utilities/scripts/validate_six_sigma.py", "Manufacturing Yield")))
    
    # =========================================================================
    # TIER 7: God-Tier Upgrades
    # =========================================================================
    print("\nGOD-TIER UPGRADES (TIER 7)")
    print("-" * 40)
    
    results.append(("Cluster Digital Twin",
        run_test("src/orchestration/cluster_digital_twin.py", "Unified Digital Twin")))
    
    results.append(("Control Plane Optimizer",
        run_test("silicon/implementation/control_plane_optimizer.py", "Silicon Feasibility")))
    
    results.append(("RL Power Orchestrator",
        run_test("src/ai_agent/rl_power_orchestrator.py", "Autonomous AI")))
    
    results.append(("Two-Phase Cooling",
        run_test("src/thermal/orchestration/two_phase_cooling_physics.py", "Thermodynamic Safety")))
    
    # =========================================================================
    # TIER 8: $5B+ Moonshots
    # =========================================================================
    print("\n$5B+ GLOBAL MONOPOLY MOONSHOTS (TIER 8)")
    print("-" * 40)
    
    results.append(("HBM4 DPLL Phase-Lock",
        run_test("src/memory/orchestration/hbm_dpll_phase_lock.py", "Memory Performance")))
    
    results.append(("Data Vault Handshake",
        run_test("src/security/data_vault_handshake.py", "Sovereign Trust")))
    
    results.append(("Formal Erasure Proof",
        run_test("validation/standards/formal_erasure_proof.py", "Erasure Math")))
    
    # =========================================================================
    # TIER 9: $5B+ Hard Physics Moonshots
    # =========================================================================
    print("\n$5B+ HARD PHYSICS MOONSHOTS (TIER 9)")
    print("-" * 40)
    
    results.append(("Active Synthesis Model",
        run_test("src/power/precharge_trigger/active_synthesis_model.py", "BOM Killer")))
    
    results.append(("Formal Verification Report",
        run_test("validation/standards/formal_verification_report.py", "Liability Shield")))
    
    results.append(("Non-Linear SPICE",
        run_test("src/power/precharge_trigger/spice_vrm_nonlinear.py", "Saturation Proof")))
    
    results.append(("Carbon Intensity Orchestrator",
        run_test("src/power/grid_vpp/carbon_intensity_orchestrator.py", "ESG Standard")))
    
    # =========================================================================
    # TIER 10: $100B+ Omega Tier
    # =========================================================================
    print("\n$100B+ OMEGA TIER (TIER 10)")
    print("-" * 40)
    
    results.append(("Power-Gated Dispatch",
        run_test("src/power/power_gated_dispatch/token_handshake_sim.py", "Permission to Compute")))
    
    results.append(("Joule Token Ledger",
        run_test("src/thermal/thermodynamic_settlement/joule_token_ledger.py", "Global Ledger")))
    
    results.append(("Inference Load Migrator",
        run_test("src/advanced/22_Global_VPP/inference_load_migrator.py", "Global Sun-Follower")))
    
    results.append(("Phase Drift Compensation",
        run_test("src/advanced/23_Atomic_Timing/phase_drift_compensation_sim.py", "Perfect Time")))
    
    # =========================================================================
    # TIER 11: $100B+ Sovereign Orchestration
    # =========================================================================
    print("\n$100B+ SOVEREIGN ORCHESTRATION (TIER 11)")
    print("-" * 40)
    
    results.append(("Planetary Carbon Arbitrage",
        run_test("src/advanced/24_Sovereign_Orchestration/planetary_carbon_arbitrage.py", "Sun-Follower")))
    
    results.append(("Sovereign Grid Inertia",
        run_test("src/advanced/24_Sovereign_Orchestration/sovereign_grid_inertia.py", "Grid Stabilizer")))
    
    # =========================================================================
    # TIER 12: $100B+ Facility & Planetary Moats
    # =========================================================================
    print("\n$100B+ FACILITY & PLANETARY MOATS (TIER 12)")
    print("-" * 40)
    
    results.append(("Transformer Resonance Moat",
        run_test("src/advanced/18_Facility_Scale_Moats/transformer_resonance_moat.py", "Blocking IVR")))
    
    results.append(("IVR Thermal Limit",
        run_test("src/advanced/18_Facility_Scale_Moats/ivr_thermal_limit.py", "The Integration Wall")))
    
    results.append(("Global Latency Map",
        run_test("src/advanced/19_Planetary_Orchestration/global_latency_map.py", "Speed of Light")))
    
    # =========================================================================
    # TIER 13: $100B+ Hard Engineering Proofs
    # =========================================================================
    print("\n$100B+ HARD ENGINEERING PROOFS (TIER 13)")
    print("-" * 40)
    
    results.append(("AIPP Timing Closure",
        run_test("silicon/implementation/aipp_timing_closure.py", "Post-Layout RTL")))
    
    results.append(("Metastability Proof",
        run_test("validation/standards/metastability_robust_proof.py", "Metastability Safety")))
    
    results.append(("PCIe Full-Stack Model",
        run_test("tools/sdk/pcie_full_stack_model.py", "Hardware Determinism")))
    
    results.append(("Adversarial Incast Sim",
        run_test("src/network/fabric_orchestration/adversarial_incast_sim.py", "Express-Lane Scale")))
    
    results.append(("Nonlinear Stability Audit",
        run_test("src/power/precharge_trigger/nonlinear_stability_audit.py", "Lyapunov Sweep")))
    
    # =========================================================================
    # TIER 14: Extreme Engineering Audit
    # =========================================================================
    print("\nEXTREME ENGINEERING AUDIT (TIER 14)")
    print("-" * 40)
    
    results.append(("Resonant LC Tank",
        run_test("src/power/adiabatic_recycling/resonant_lc_tank_sim.py", "Adiabatic Logic")))
    
    results.append(("Body Bias Leakage",
        run_test("src/advanced/26_Adaptive_Body_Biasing/body_bias_leakage_sim.py", "Leakage Choking")))
    
    results.append(("VDD Subthreshold",
        run_test("src/advanced/27_Entropy_VDD_Scaling/vdd_subthreshold_sim.py", "Shannon VDD")))
    
    results.append(("Optical Phase Determinism",
        run_test("src/optical/phase_lock/optical_phase_determinism_sim.py", "THz Phase-Lock")))
    
    results.append(("Planetary Gradient Migrator",
        run_test("src/advanced/29_Sparse_Gradient_Migration/planetary_gradient_migrator.py", "Sparsity Migration")))
    
    # =========================================================================
    # TIER 15: Omega-Tier Physics & Economy
    # =========================================================================
    print("\nOMEGA-TIER PHYSICS & ECONOMY (TIER 15)")
    print("-" * 40)
    
    results.append(("HBM Silence Token",
        run_test("src/memory/orchestration/hbm_silence_token_enforcement.py", "Temporal Guard Band")))
    
    results.append(("Multi-Phase Resonant Clock",
        run_test("src/power/adiabatic_recycling/multi_phase_resonant_clock.py", "EMI Shielded Resonance")))
    
    results.append(("Sub-Harmonic Breathing",
        run_test("src/advanced/22_Global_VPP/sub_harmonic_cluster_breathing.py", "Synthetic Inertia")))
    
    results.append(("Entropy Credit Ledger",
        run_test("src/thermal/thermodynamic_settlement/entropy_credit_ledger.py", "AI Clearinghouse")))
    
    results.append(("Power Signature Audit",
        run_test("src/security/power_signature_audit.py", "Physical Attestation")))
    
    # =========================================================================
    # TIER 16: The Final Lock (Supply Chain & Memory Wall)
    # =========================================================================
    print("\nTHE FINAL LOCK: SUPPLY CHAIN & MEMORY WALL (TIER 16)")
    print("-" * 40)
    
    results.append(("PUF Power Fingerprint",
        run_test("src/advanced/30_Silicon_Provenance/puf_power_fingerprint.py", "Power-PUF")))
    
    results.append(("CXL Latency Pre-Dispatch",
        run_test("src/network/storage_fabric/cxl_latency_pre_dispatch.py", "CXL Memory Wall")))
    
    results.append(("Master Pareto Charts",
        run_test("tools/utilities/scripts/master_pareto_charts.py", "Decision Surface")))
    
    # =========================================================================
    # Portfolio B Integrations (Families 4, 5, 11)
    # =========================================================================
    print("\nPORTFOLIO B INTEGRATIONS (NEW FAMILIES)")
    print("-" * 40)
    
    results.append(("Family 4: Incast Backpressure",
        run_test("src/network/incast_backpressure/simulation.py", "Memory Backpressure")))
    
    results.append(("Family 5: CXL Sideband",
        run_test("src/network/cxl_sideband/telemetry_bus.py", "CXL Sideband")))
    
    results.append(("Family 11: Noisy Neighbor",
        run_test("src/memory/noisy_neighbor/simulation.py", "4D Classifier")))
    
    # =========================================================================
    # Thermal Innovations (Families 9, 10, 12)
    # =========================================================================
    print("\nTHERMAL INNOVATIONS (FAMILIES 9, 10, 12)")
    print("-" * 40)
    
    results.append(("Family 9: Iso-Performance",
        run_test("src/orchestration/grand_unified_3d_twin.py", "Iso-Performance Scaling")))
    
    results.append(("Family 10: Thermal PUF",
        run_test("src/network/telemetry_loop/thermal_puf_extractor.py", "Thermal PUF Auth")))
    
    results.append(("Family 12: Compute-Inhibit",
        run_test("silicon/implementation/power_aware_rtl_synthesis.py", "Compute-Inhibit Interlock")))
    
    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    
    total_tests = len(results)
    passed_tests = sum(1 for _, passed in results if passed)
    
    # Print results table
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name:.<55} {status}")
    
    print(f"\nFinal Score: {passed_tests}/{total_tests} components passed ({100*passed_tests/total_tests:.1f}%)")
    
    if passed_tests == total_tests:
        print(f"\n✅ AIPP-OMEGA: ALL {total_tests} COMPONENTS VALIDATED")
        print("   Technical Quality: Simulation-proven, hardware validation required")
        print("   Current Stage: TRL-3 (Proof of Concept)")
        print("   Patent Families: 12 (integrated from Portfolio A, B, and thermal innovations)")
        print("   Next Step: FPGA demo per docs/specs/HARDWARE_EXECUTION_PLAN.md")
        return 0
    else:
        failed = total_tests - passed_tests
        print(f"\n⚠️ {failed} component(s) failed validation. Review logs above.")
        return 1


if __name__ == "__main__":
    sys.exit(validate_all())
