# Patent Family 3: The "Spectral" Resonance Damping

## Problem

AI inference traffic often arrives in rhythmic batches (e.g., every 10ms → **100Hz**). That periodicity becomes a periodic **power draw**, which can couple into facility electrical infrastructure.

When the traffic creates a strong spectral line near a mechanical resonance of transformers, you can get:
- vibration
- breaker trips
- equipment damage

## Invention

**Frequency-domain scheduling in the switch**:

1. Switch observes outgoing traffic as a time series.
2. Switch computes/maintains an FFT (or an equivalent line-detection statistic).
3. If it detects a strong peak at 100Hz, it injects controlled jitter into packet release timing.
4. The energy spreads across the spectrum and the dangerous line collapses.

## Acceptance Criteria

- **Peak reduction**: 100Hz peak reduces by **≥ 20 dB**.
- **Latency impact**: mean added scheduling delay is **< 5%** of end-to-end latency budget.

This repo makes the latency budget explicit (default: 600ms) and reports the measured mean and p99 added delay.

## What This Repo Does

- `jitter_algorithm.py`
  - Generates a periodic arrival process (100Hz)
  - Applies a queue-aware jitter scheduler (causality-preserving)
  - Computes FFT/PSD and reports peak reduction
  - Computes added delay distribution (mean, p99)

- `simulation.py`
  - Runs the baseline vs jittered comparison
  - Prints acceptance checks
  - Writes the artifact figures + a tournament CSV

## Results (Default Run)

- Peak reduction: **~20.2 dB**
- Mean added delay: **~25.4 ms**
- p99 added delay: **~91.3 ms**

Under a 600ms latency budget, 5% = 30ms, so the mean delay passes.

## Data Room Artifacts

- `spectral_heatmap.png`: left = baseline line at 100Hz, right = smeared noise floor
- `spectrum_comparison.png`: overlaid PSD lines with the measured dB reduction
- `time_domain.png`: time-domain power signal showing periodic vs jittered

## Reproduce

```bash
cd 03_Spectral_Damping
python simulation.py
```

## Patent Claim (Draft)

> "A network scheduling apparatus configured to detect a periodic spectral component in an outgoing traffic stream and to inject controlled timing jitter into packet release decisions such that a target spectral line (e.g., 100Hz) is reduced by at least a threshold (≥20dB), while maintaining an average added scheduling delay below a defined fraction of an end-to-end latency budget."



