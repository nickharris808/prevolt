# Patent Family 2: The "In-Band" Telemetry Loop

## Problem

The switch is **blind**: it will continue blasting packets at a GPU even when the GPU is undervolting or overheating. Without a feedback channel, the network keeps pushing the GPU deeper into failure.

## Invention

**Embed GPU health in-band** inside standard packet headers, so the switch can react in hardware.

This repo implements the specific variant you described:

- **Voltage health** is encoded as a **4-bit integer** (0..15)
- Embedded into the **IPv6 Flow Label** (20 bits)
  - We use the lowest 4 bits as the health code
- The switch parses the Flow Label in hardware and modulates egress rate (meter / token bucket)

## Acceptance Criteria

- **Correlation**: As voltage drops, bandwidth drops within **2 RTTs**.
- **Recovery**: The node returns to safe voltage without a hard reset.
- **Artifact**: Voltage (top) and bandwidth (bottom) look like mirror images.

## What This Repo Does

### `simulation.py` (RTT-delayed closed-loop model)
- Explicitly models RTT and enforces that control actions are delayed by **2 RTTs**
- Quantizes voltage into a 4-bit health code
- Converts health to a rate limit
- Produces `throughput_vs_voltage.png` with two stacked plots

When you run it, it prints:
- RTT
- Control delay (2 RTT)
- Pass/fail for the **within-2-RTT** response check

### P4 reference
- `switch_logic_ipv6_flowlabel.p4`
  - Parses IPv6 flow label
  - Extracts 4-bit voltage health
  - Sketches a dataplane rate-enforcement structure

(We keep the older TCP-option reference in `switch_logic.p4` as an alternative encoding, but the Flow-Label version is the one that matches your spec.)

## Data Room Artifact

- `throughput_vs_voltage.png`
  - Top: Voltage vs time (with and without telemetry)
  - Bottom: Bandwidth vs time + the applied rate limit

## Reproduce

```bash
cd 02_Telemetry_Loop
python simulation.py
```

## Patent Claim (Draft)

> "A network switching apparatus configured to parse an IPv6 header field containing a quantized voltage health value, and to modulate transmission bandwidth to a downstream compute node within a bounded reaction time (≤2 RTTs) in response to decreases in said voltage health value, thereby maintaining a supply voltage above a safety threshold without out-of-band wiring."
