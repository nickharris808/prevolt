# Patent Family 1: The "Pre-Cognitive" Voltage Trigger (Standard-Essential)

**The Thesis:** The physical power grid is too slow for AI. We use the Network Switch (which operates in nanoseconds) to act as the "Brain" for the Power Supply. This family forms the core of the **GPOP v1.0 Standard**.

This family proves that the Network Switch is the only upstream component capable of predicting GPU power transients with high enough temporal resolution to prevent voltage collapse.

## Family Variations (Patent Claims)

### 1.1 Static Lead Time (The Baseline)
*   **Mechanism:** Fixed-delay buffer for all compute-triggering packets.
*   **Proof:** SPICE simulation showing 14us delay keeps V_min >= 0.9V.
*   **Artifact:** `artifacts/01_static_trace.png`

### 1.2 Online Kalman Predictor
*   **Mechanism:** Online learning of inter-packet intervals to narrow the uncertainty window.
*   **Proof:** Convergence on jittered arrival patterns with < 1us error.
*   **Artifact:** `artifacts/02_kalman_convergence.png`

### 1.3 Confidence-Gated Hybrid
*   **Mechanism:** Real-time variance monitoring. Automatically falls back to Static mode if traffic entropy increases.
*   **Proof:** State-transition map showing zero safety violations during traffic phase shifts.
*   **Artifact:** `artifacts/03_gating_logic.png`

### 1.4 Amplitude/Lead-Time Co-Optimizer
*   **Mechanism:** Mathematical co-optimization of pre-charge voltage boost and delay.
*   **Proof:** Pareto front showing the minimum "energy overhead" to satisfy safety constraints.
*   **Artifact:** `artifacts/04_pareto_front.png`

### 1.5 Multi-GPU Collective Sync
*   **Mechanism:** Orchestrated stagger across switch ports for collective operations (AllReduce).
*   **Proof:** 30% reduction in rack-level current spikes (di/dt).
*   **Artifact:** `artifacts/05_rack_smoothing.png`

## How to Run
```bash
# Execute the full family tournament
python master_tournament.py
```

