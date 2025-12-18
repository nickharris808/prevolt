# Patent Family 3: The "Spectral" Resonance Damping

**The Thesis:** AI inference requests arrive in rhythmic batches, creating 100Hz current pulses that destroy transformers. We move traffic from the Time Domain to the Frequency Domain to kill the resonance.

## Family Variations (Patent Claims)

### 3.1 Uniform Spectrum Smearing (The Baseline)
*   **Mechanism:** Large-magnitude timing jitter (±45%) applied to all departures.
*   **Proof:** FFT showing >20dB reduction in 100Hz energy peak.
*   **Artifact:** `artifacts/01_uniform_heatmap.png`

### 3.2 Surgical Notch Scheduling
*   **Mechanism:** Narrow-band jitter targeted specifically at the mechanical resonance of the facility.
*   **Proof:** 20dB damping achieved with 50% less average latency penalty than baseline jitter.
*   **Artifact:** `artifacts/02_surgical_notch.png`

### 3.3 Phase-Cancellation Interleaving
*   **Mechanism:** Port-to-port phase offset. Switch schedules adjacent GPUs with a 180-degree phase shift (5ms).
*   **Proof:** Aggregate 100Hz power reduction > 25dB with *zero jitter* added to individual flows.
*   **Artifact:** `artifacts/03_phase_cancellation.png`

### 3.4 Multi-Harmonic Attenuator
*   **Mechanism:** Gaussian Mixture jitter distribution to suppress higher-order harmonics (200Hz, 300Hz, etc.).
*   **Proof:** Suppression of the entire harmonic ladder below the facility noise floor.
*   **Artifact:** `artifacts/04_broadband_damping.png`

## How to Run
```bash
python master_tournament.py
```

