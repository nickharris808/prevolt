# Patent Family 1: The "Pre-Cognitive" Voltage Trigger

## Thesis

**The network switch can predict power demand** because it controls when data is released to the GPU. That makes it the only upstream component fast enough to "warn" the VRM before a compute-triggering packet arrives.

## Problem (Latency Mismatch)

- **VRM current ramp**: ~15 µs control-loop response
- **Compute-triggered load step**: ~1 µs

Result: A heavy packet arrives, GPU starts compute, current demand spikes, and the supply droops before the VRM can react.

## Invention (Look-Ahead Signaling)

1. Switch classifies an incoming packet as a **"Heavy Job"**.
2. Switch sends a **Wake-Up control frame** to the VRM.
3. Switch **buffers** the packet for a calculated delay (e.g. 14 µs).
4. VRM setpoint rises preemptively, **pre-charging decoupling capacitors**.
5. Packet is released; GPU load step occurs; voltage stays in the safe band.

## Acceptance Criteria (Pass/Fail)

### Baseline (must fail)
- Load step: **500 A** (ramp time 1 µs)
- Requirement: **V(out) must dip below 0.7 V**

### Invention (must pass)
- Same 500 A load step
- Pre-trigger lead time: **14 µs**
- Requirement: **V(out) must never dip below 0.9 V**

### Efficiency (must pass)
- Added delay: **< 20 µs**

## What This Repo Actually Does

This directory uses **PySpice + ngspice** to run an auditable R–L–C + VRM-control transient.

- Baseline: V(out) min ≈ **0.6866 V** (fails as required)
- With 14 µs pre-trigger: V(out) min ≈ **0.9000 V** (passes as required)
- Added delay: **14 µs** (< 20 µs)

## Data Room Artifact

- `voltage_trace.png`: **Transient Response** showing the red crash trace vs the green stable trace.

## Files

- `spice_vrm.py`
  - Builds and runs the SPICE model
  - Includes `check_acceptance_criteria()` which returns explicit pass/fail booleans
- `simulation.py`
  - Generates `voltage_trace.png` (the buyer-facing artifact)
- `tournament.py`
  - Sweeps pre-trigger lead times and writes `tournament_results.csv`
- `tournament_results.csv`
  - Lead time vs minimum V(out)

## Reproduce

```bash
# From repository root
pip install -r requirements.txt

# Install ngspice
brew install ngspice      # macOS
apt install ngspice       # Linux

cd 01_PreCharge_Trigger
python spice_vrm.py
python master_tournament.py
```

## Patent Claim (Draft)

> "A network switching apparatus configured to detect a compute-heavy packet and to delay transmission of said packet for a delay interval, while transmitting a pre-trigger control frame to a downstream voltage regulator module prior to releasing the packet, such that a downstream supply voltage remains above a safety threshold during a resulting load transient, wherein the delay interval is less than a performance limit."






