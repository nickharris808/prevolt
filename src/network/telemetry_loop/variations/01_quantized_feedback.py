"""02_Telemetry_Loop/simulation.py

Portfolio A — Patent Family 2: The "In-Band" Telemetry Loop
===========================================================

Goal
----
Demonstrate a closed-loop where *voltage health* reported in-band causes the
switch to throttle bandwidth quickly enough to prevent prolonged undervoltage.

This script generates the data-room artifact:
- `throughput_vs_voltage.png`: two stacked plots (Voltage on top, Bandwidth on bottom)
  that show tight (mirrored) closed-loop behavior.

Acceptance Criteria (as provided)
---------------------------------
1) Correlation: As voltage drops, bandwidth must drop within **2 RTTs**.
2) Recovery: Node returns to safe voltage without a hard reset.
3) Artifact: Voltage and bandwidth should look like mirror images.

How we model "in-band" telemetry
--------------------------------
In real deployment:
- GPU encodes a 4-bit voltage-health code in an IPv6 header field (e.g. Flow Label)
  on outgoing ACKs.
- Switch parses it in hardware (P4) and adjusts a rate limiter.

In this *simulation*:
- We explicitly model the RTT and enforce that switch control actions are delayed
  by exactly 2 RTTs relative to voltage changes.
- We model the 4-bit health encoding (0..15) as a quantizer of voltage.

This code is deterministic and reproducible. It does not generate synthetic
"perfect mirror" curves; the mirroring emerges from the control law + RTT delay.

Run:
  python simulation.py
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

import sys, os
from pathlib import Path
root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root))
family = Path(__file__).parent.parent
sys.path.insert(0, str(family))

from utils.plotting import (
    setup_plot_style,
    save_publication_figure,
    COLOR_FAILURE,
    COLOR_SUCCESS,
)


@dataclass(frozen=True)
class TelemetryConfig:
    # Time base
    duration_ms: float = 500.0
    dt_ms: float = 0.1

    # RTT (round-trip time)
    rtt_ms: float = 0.25

    # Traffic demand (Gbps)
    base_rate_gbps: float = 40.0
    burst_rate_gbps: float = 140.0
    burst_period_ms: float = 100.0
    burst_duration_ms: float = 30.0
    warmup_ms: float = 10.0

    # Voltage dynamics (simple but causal)
    v_nominal: float = 0.95
    v_safe: float = 0.90
    v_warning: float = 0.88

    # Voltage droop model:
    # droop is proportional to *excess* bandwidth above the steady-state baseline.
    # Units: Volts per (Gbps * ms). The update multiplies by dt_ms.
    drop_gain_v_per_gbps: float = 0.00010

    # VRM recovery (first-order)
    vrm_tau_ms: float = 12.0

    # Rate limiter bounds
    max_rate_gbps: float = 150.0
    min_rate_gbps: float = 10.0


def voltage_to_health_4bit(v: float, v_min: float, v_max: float) -> int:
    """Quantize voltage into a 4-bit health code (0..15).

    v <= v_min  -> 0 (worst)
    v >= v_max  -> 15 (best)

    This matches the acceptance spec "a 4-bit integer".
    """
    if v <= v_min:
        return 0
    if v >= v_max:
        return 15
    x = (v - v_min) / (v_max - v_min)
    return int(np.round(x * 15.0))


def health_to_rate_limit(health: int, cfg: TelemetryConfig) -> float:
    """Map health (0..15) to a switch rate limit.

    This is the hardware-friendly rule you would implement as a P4 table.
    """
    # Linear mapping: health=15 -> max, health=0 -> min
    return cfg.min_rate_gbps + (cfg.max_rate_gbps - cfg.min_rate_gbps) * (health / 15.0)


def generate_demand(cfg: TelemetryConfig, t_ms: np.ndarray) -> np.ndarray:
    """Generate a bursty demand waveform."""
    demand = np.full_like(t_ms, cfg.base_rate_gbps, dtype=float)
    # Warm-up so the system starts from a steady operating point.
    active_t = np.maximum(0.0, t_ms - cfg.warmup_ms)
    phase = np.mod(active_t, cfg.burst_period_ms)
    in_burst = (t_ms >= cfg.warmup_ms) & (phase < cfg.burst_duration_ms)
    demand[in_burst] = cfg.burst_rate_gbps
    return demand


def run_closed_loop(cfg: TelemetryConfig, telemetry_enabled: bool) -> dict:
    """Run the RTT-delayed closed loop."""

    n = int(cfg.duration_ms / cfg.dt_ms) + 1
    t_ms = np.linspace(0.0, cfg.duration_ms, n)

    demand = generate_demand(cfg, t_ms)

    v = np.zeros_like(t_ms)
    v[0] = cfg.v_nominal

    # Telemetry / control pipeline
    rtt_steps = max(1, int(np.round(cfg.rtt_ms / cfg.dt_ms)))
    control_delay_steps = 2 * rtt_steps

    health = np.zeros_like(t_ms, dtype=int)
    health[0] = voltage_to_health_4bit(v[0], cfg.v_warning, cfg.v_nominal)

    rate_limit = np.zeros_like(t_ms)
    rate_limit[0] = cfg.max_rate_gbps

    throughput = np.zeros_like(t_ms)

    # Initialize a buffer of past health codes (models 2 RTT delay)
    health_history = [health[0]] * (control_delay_steps + 1)

    for k in range(1, n):
        # Switch applies control based on delayed telemetry
        if telemetry_enabled:
            delayed_health = health_history[-(control_delay_steps + 1)]
            rate_limit[k] = health_to_rate_limit(delayed_health, cfg)
        else:
            rate_limit[k] = cfg.max_rate_gbps

        # Throughput is demand limited by switch
        throughput[k] = min(demand[k], rate_limit[k])

        # Voltage drops with *excess* throughput and recovers with VRM time constant.
        # dv = -(k_drop * max(0, throughput - base) * dt_ms) + ((v_nom - v)/tau * dt_ms)
        excess = max(0.0, throughput[k] - cfg.base_rate_gbps)
        drop = cfg.drop_gain_v_per_gbps * excess * cfg.dt_ms
        recover = ((cfg.v_nominal - v[k - 1]) / cfg.vrm_tau_ms) * cfg.dt_ms
        v[k] = v[k - 1] - drop + recover

        # Update telemetry health code based on current voltage
        health[k] = voltage_to_health_4bit(v[k], cfg.v_warning, cfg.v_nominal)
        health_history.append(health[k])

    # Acceptance metric: response within 2 RTTs
    # We define "voltage drop event" as crossing below v_warning.
    events = np.where((v[:-1] >= cfg.v_warning) & (v[1:] < cfg.v_warning))[0]
    
    response_ok = True
    response_lags_ms: list[float] = []

    if telemetry_enabled and len(events) > 0:
        for idx in events:
            t_event = t_ms[idx + 1]
            # Find the first time after event where throughput drops by at least 10%.
            # Use actual throughput at the event time to avoid dependence on demand shape.
            baseline_tp = float(throughput[idx + 1])
            target_tp = 0.9 * baseline_tp
            window_end = t_event + 2.0 * cfg.rtt_ms

            window_mask = (t_ms >= t_event) & (t_ms <= window_end)
            if not np.any(window_mask):
                continue
            k_window = np.where(window_mask)[0]
            k_hit = k_window[np.where(throughput[k_window] <= target_tp)[0]]
            if len(k_hit) == 0:
                response_ok = False
            else:
                response_lags_ms.append(float(t_ms[k_hit[0]] - t_event))

    return {
        "t_ms": t_ms,
        "demand_gbps": demand,
        "throughput_gbps": throughput,
        "rate_limit_gbps": rate_limit,
        "voltage_v": v,
        "health": health,
        "rtt_ms": cfg.rtt_ms,
        "control_delay_ms": 2.0 * cfg.rtt_ms,
        "response_within_2rtt": response_ok if telemetry_enabled else None,
        "response_lags_ms": response_lags_ms,
    }


def plot_closed_loop(baseline: dict, telemetry: dict, cfg: TelemetryConfig, out_basepath: Path) -> None:
    setup_plot_style()

    fig, (ax_v, ax_bw) = plt.subplots(2, 1, figsize=(14, 8), sharex=True, gridspec_kw={"hspace": 0.12})

    t = baseline["t_ms"]

    # Voltage (top)
    ax_v.plot(t, baseline["voltage_v"], color=COLOR_FAILURE, linewidth=2.0, label="Voltage (no telemetry)")
    ax_v.plot(t, telemetry["voltage_v"], color=COLOR_SUCCESS, linewidth=2.0, label="Voltage (with telemetry)")
    ax_v.axhline(cfg.v_warning, color="#AA6600", linestyle="--", linewidth=1.2, alpha=0.9, label=f"Warning {cfg.v_warning:.2f}V")
    ax_v.axhline(cfg.v_safe, color="#333333", linestyle=":", linewidth=1.2, alpha=0.9, label=f"Safe {cfg.v_safe:.2f}V")
    ax_v.set_ylabel("Voltage (V)")
    ax_v.set_title("In-Band Telemetry Loop: Voltage and Bandwidth Coupled (2 RTT control delay)")
    ax_v.grid(True, alpha=0.3)
    ax_v.legend(loc="lower left", fontsize=9)

    # Bandwidth (bottom)
    ax_bw.plot(t, baseline["throughput_gbps"], color=COLOR_FAILURE, linewidth=2.0, label="Bandwidth (no telemetry)")
    ax_bw.plot(t, telemetry["throughput_gbps"], color=COLOR_SUCCESS, linewidth=2.0, label="Bandwidth (with telemetry)")
    ax_bw.plot(t, telemetry["rate_limit_gbps"], color="#6F42C1", linewidth=1.5, linestyle="--", alpha=0.8, label="Rate limit")
    ax_bw.set_xlabel("Time (ms)")
    ax_bw.set_ylabel("Bandwidth (Gbps)")
    ax_bw.grid(True, alpha=0.3)
    ax_bw.legend(loc="upper right", fontsize=9)

    # Caption with acceptance check
    lags = telemetry["response_lags_ms"]
    if len(lags):
        worst = max(lags)
        lag_text = f"worst_response={worst:.3f}ms"
    else:
        lag_text = "no_crossing_events"

    caption = (
        f"Acceptance: bandwidth reacts within 2 RTTs (RTT={cfg.rtt_ms:.2f}ms, 2RTT={2*cfg.rtt_ms:.2f}ms) | "
        f"response_within_2rtt={telemetry['response_within_2rtt']} | {lag_text}"
    )
    fig.text(0.5, 0.02, caption, ha="center", fontsize=10, style="italic", color="#444444")

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.09)

    save_publication_figure(fig, str(out_basepath), dpi=300, formats=["png"])
    plt.close(fig)


def main() -> None:
    cfg = TelemetryConfig()

    baseline = run_closed_loop(cfg, telemetry_enabled=False)
    telemetry = run_closed_loop(cfg, telemetry_enabled=True)

    print("=" * 80)
    print("IN-BAND TELEMETRY LOOP")
    print("=" * 80)
    print(f"RTT: {cfg.rtt_ms:.3f} ms | Control delay: {2*cfg.rtt_ms:.3f} ms")
    print(f"Response within 2 RTTs: {telemetry['response_within_2rtt']}")
    if telemetry["response_lags_ms"]:
        print(f"Worst response lag: {max(telemetry['response_lags_ms']):.4f} ms")

    out_dir = Path(__file__).parent
    plot_closed_loop(baseline, telemetry, cfg, out_dir / "throughput_vs_voltage")
    print(f"Saved: {out_dir / 'throughput_vs_voltage.png'}")


if __name__ == "__main__":
    main()
