"""spice_vrm.py

PySpice/Ngspice VRM + GPU Load-Step Model
========================================

This module exists because the *acceptance criteria* for Patent Family 1 are
explicitly circuit-physics based and must be demonstrated with SPICE:

Acceptance Criteria (Pass/Fail):
- Baseline: 500A load step -> Vout must drop below 0.7V.
- Invention: same load step with 14µs pre-trigger -> Vout must never drop below 0.9V.
- Efficiency: total added delay < 20µs.

Modeling approach:
- We model the VRM output as a controlled Thevenin source with a finite response time.
- The switch "pre-trigger" causes the VRM reference/setpoint to ramp *up* early,
  pre-charging the output capacitor so that when the GPU load step hits, Vout
  stays >= 0.9V.

This is intentionally a *minimal* but auditable circuit:
- Series R models DC droop (I * R).
- Series L models fast transient droop (L * di/dt).
- Cout models energy buffering.

Notes on realism:
- Board/package inductance seen by the die can be in the single-nH range.
- 500A/1µs is an extreme step; the point here is demonstrating the timing mismatch.

This module does not draw plots; it produces time-series suitable for the
"Transient Response" data room artifact.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Tuple

import numpy as np

from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import u_Ohm, u_H, u_F, u_s, u_V


@dataclass(frozen=True)
class SpiceVRMConfig:
    """All parameters are explicit so reviewers can audit them."""

    # Nominal operating voltage (GPU core)
    v_nominal_v: float = 0.90

    # Load step (GPU)
    i_step_a: float = 500.0
    i_step_rise_s: float = 1e-6
    t_load_start_s: float = 20e-6

    # Output network (VRM + board + decaps)
    r_series_ohm: float = 0.0004     # 0.4 mΩ
    l_series_h: float = 1.2e-9       # 1.2 nH
    i_sat_a: float = 600.0           # Fix 3: Inductor saturation current
    c_out_f: float = 0.015           # 15 mF (15,000 µF)

    # VRM control response (first-order)
    vrm_tau_s: float = 15e-6         # 15 µs
    vrm_di_dt_limit_a_per_s: float = 100e6 # 100A/us VRM ramp limit (S+ requirement)

    # PTP Synchronization Error
    ptp_sync_error_s: float = 0.0    # Jitter/Drift between switch and VRM

    # Pre-trigger behavior
    pretrigger_lead_s: float = 14e-6
    # Pre-charge setpoint.
    v_preboost_v: float = 1.20

    # Safety Clamp Logic (OVP Protection)
    packet_dropped: bool = False     # Simulate missing compute packet
    hold_time_max_s: float = 5e-6    # Max time to hold boost before clamp
    
    # Fix 1: Load Verification Gate (Zero-Trust Handshake)
    # The VRM only boosts if the local NIC confirms packet arrival.
    # This prevents OVP if the 'Pre-charge' signal was spoofed or the link died.
    load_verified: bool = True       # Does the NIC confirm packet start?

    # Transient analysis
    t_stop_s: float = 80e-6
    t_step_s: float = 50e-9          # 50 ns output sample step


def _build_step_pwl(
    mode: Literal["baseline", "pretrigger"],
    cfg: SpiceVRMConfig,
) -> list[tuple[float, float]]:
    """Return a PWL stimulus for the VRM reference generator.

    Updated for $1B Tier:
    - Includes PTP Sync Jitter (shift in trigger time)
    - Includes Safety Clamp (ramp down if packet_dropped=True)
    - Includes Fix 1: Load Verification Gate (only boost if verified)
    """

    v0 = cfg.v_nominal_v
    t_trigger = cfg.t_load_start_s - cfg.pretrigger_lead_s + cfg.ptp_sync_error_s
    t_eps = 1e-9  # 1 ns
    t_ramp = 1e-6 # 1us ramp speed for pre-charge

    if mode == "baseline":
        return [
            (0.0, v0),
            (cfg.t_stop_s, v0),
        ]

    # Pre-trigger mode: First, determine if we even start a boost
    if not cfg.load_verified:
        # Zero-Trust: No verification from NIC, stay at nominal
        return [(0.0, v0), (cfg.t_stop_s, v0)]

    # Pre-trigger mode with verification
    pwl = [
        (0.0, v0),
        (t_trigger, v0),
        (t_trigger + t_ramp, cfg.v_preboost_v),
    ]

    if cfg.packet_dropped:
        # SAFETY CLAMP: No packet arrives.
        # Hold for hold_time_max, then ramp down to prevent OVP.
        t_clamp_start = cfg.t_load_start_s + cfg.hold_time_max_s
        pwl.extend([
            (t_clamp_start, cfg.v_preboost_v),
            (t_clamp_start + t_ramp, v0),
            (cfg.t_stop_s, v0)
        ])
    else:
        # Normal burst handling
        pwl.append((cfg.t_stop_s, cfg.v_preboost_v))

    # print(f"DEBUG PWL: {pwl}")
    return pwl


def simulate_vrm_transient(
    *,
    mode: Literal["baseline", "pretrigger"],
    cfg: SpiceVRMConfig,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Run ngspice transient simulation.

    Returns:
      t_s: time vector in seconds
      v_out_v: V(out) in volts
      i_load_a: I(load) in amps (positive = sink)
    """

    circuit = Circuit(f"VRM_GPU_LoadStep_{mode}")

    # Nodes
    # n_step: raw reference step stimulus
    # n_ctrl: filtered control voltage (VRM control-loop response)
    # n_vrm: ideal low-impedance VRM output setpoint (controlled by n_ctrl)
    # n_mid: between R and L
    # out: GPU supply node

    # Reference step + control-loop RC filter (tau = R*C)
    #
    # IMPORTANT: PySpice formats PWL source values with unit suffixes (e.g. \"500A\").
    # Ngspice PWL syntax does NOT treat \"A\"/\"V\" as units (it treats letters as
    # scale suffixes like m/u/n/p). This silently destroys amplitudes (e.g. \"500A\"
    # can be interpreted as 500 atto = 5e-16).
    #
    # To keep the simulation physically correct and reproducible, we emit the two
    # PWL sources as *raw SPICE lines* with plain numeric values.
    pwl_v_raw = _build_step_pwl(mode=mode, cfg=cfg)
    pwl_v_tokens = " ".join([f"{t:.12e} {v:.12f}" for (t, v) in pwl_v_raw])
    circuit.raw_spice += f"VSTEP n_step 0 PWL({pwl_v_tokens})\n"

    # Choose Rctrl so Cctrl is in a reasonable range; tau = R*C
    r_ctrl = 1_000.0  # Ohms
    c_ctrl = cfg.vrm_tau_s / r_ctrl  # Farads
    circuit.R('CTRL', 'n_step', 'n_ctrl', r_ctrl @ u_Ohm)
    circuit.C('CTRL', 'n_ctrl', circuit.gnd, c_ctrl @ u_F)

    # Ideal VRM output setpoint driven by control-loop voltage.
    # This decouples the *control* dynamics from the *power* delivery impedance.
    circuit.VCVS('VRM', 'n_vrm', circuit.gnd, 'n_ctrl', circuit.gnd, 1.0)

    circuit.R('SER', 'n_vrm', 'n_mid', cfg.r_series_ohm @ u_Ohm)
    
    # ideal voltage source for current measurement
    circuit.V('MEAS', 'n_mid', 'n_l_in', 0 @ u_V)
    
    # Fix 3: Non-Linear Saturation Inductor (Numerical Stability Fix)
    # Inductance L(I) = L0 / (1 + (I/Isat)^2). 
    # This is a smoother transition that avoids the 'zero inductance' crash.
    l_expr = f"{cfg.l_series_h} / (1 + (abs(I(VMEAS)) / {cfg.i_sat_a})**2)"
    circuit.raw_spice += f"LSER n_l_in out L={{ {l_expr} }}\n"

    circuit.C('OUT', 'out', circuit.gnd, cfg.c_out_f @ u_F)

    # Load current: PWL sink from out -> gnd
    t0 = cfg.t_load_start_s
    t1 = cfg.t_load_start_s + cfg.i_step_rise_s

    if cfg.packet_dropped:
        # No packet arrives, load stays idle (0A)
        pwl_i_raw = [
            (0.0, 0.0),
            (cfg.t_stop_s, 0.0),
        ]
    else:
        # Standard load step
        pwl_i_raw = [
            (0.0, 0.0),
            (t0, 0.0),
            (t1, cfg.i_step_a),
            (cfg.t_stop_s, cfg.i_step_a),
        ]
    
    pwl_i_tokens = " ".join([f"{t:.12e} {i:.12f}" for (t, i) in pwl_i_raw])
    circuit.raw_spice += f"ILOAD out 0 PWL({pwl_i_tokens})\n"

    simulator = circuit.simulator(temperature=25, nominal_temperature=25)
    analysis = simulator.transient(step_time=cfg.t_step_s @ u_s, end_time=cfg.t_stop_s @ u_s)

    t_s = np.array(analysis.time)
    v_out_v = np.array(analysis.out)

    # Reconstruct i_load from the PWL definition (for plotting/annotation)
    # This is deterministic and not "fake"; it's the exact load waveform.
    i_load = np.zeros_like(t_s)
    ramp_mask = (t_s >= t0) & (t_s < t1)
    hold_mask = t_s >= t1
    i_load[ramp_mask] = cfg.i_step_a * (t_s[ramp_mask] - t0) / (t1 - t0)
    i_load[hold_mask] = cfg.i_step_a

    return t_s, v_out_v, i_load


def check_acceptance_criteria(cfg: SpiceVRMConfig) -> dict:
    """Run both modes and evaluate the explicit pass/fail criteria."""

    t_b, v_b, _ = simulate_vrm_transient(mode="baseline", cfg=cfg)
    t_p, v_p, _ = simulate_vrm_transient(mode="pretrigger", cfg=cfg)

    min_baseline = float(np.min(v_b))
    min_pretrigger = float(np.min(v_p))

    baseline_pass = min_baseline < 0.70
    invention_pass = min_pretrigger >= 0.90

    delay_us = cfg.pretrigger_lead_s * 1e6
    efficiency_pass = delay_us < 20.0

    return {
        "baseline_min_v": min_baseline,
        "pretrigger_min_v": min_pretrigger,
        "baseline_pass": baseline_pass,
        "invention_pass": invention_pass,
        "efficiency_pass": efficiency_pass,
        "added_delay_us": delay_us,
        "overall_pass": baseline_pass and invention_pass and efficiency_pass,
    }






