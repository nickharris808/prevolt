# Patent Family 4: The "Grid-Aware" Resilience Family

**The Thesis:** The data center is now an active participant in the electrical grid. By coupling the network directly to utility signals, we can prevent cluster-wide outages and monetize flexibility.

## Family Variations (Patent Claims)

### 4.1 Binary Priority Shedding (The Baseline)
*   **Mechanism:** Two-tier QoS (Gold/Bronze). Instantly drops low-priority traffic on grid events.
*   **Proof:** Instant 33% power reduction while 100% of Gold (Inference) traffic is preserved.
*   **Artifact:** `artifacts/01_binary_shedder.png`

### 4.2 Graduated QoS Degradation
*   **Mechanism:** 8-level priority queues allowing for "Soft Landings" during deepening sags.
*   **Proof:** Staircase power reduction curve showing zero high-priority impact until critical thresholds.
*   **Artifact:** `artifacts/02_graduated_qos.png`

### 4.3 Grid Frequency Coupling (FCR)
*   **Mechanism:** Real-time proportional response to grid frequency deviations (60Hz nominal).
*   **Proof:** Virtual Battery behavior with < 100ms response time to grid transients.
*   **Artifact:** `artifacts/03_grid_coupling.png`

### 4.4 Predictive Sag Buffering
*   **Mechanism:** Proactive queue drainage using "Pre-Sag" utility alerts (50ms lead).
*   **Proof:** Elimination of congestion-related packet drops during the transition to battery/throttle mode.
*   **Artifact:** `artifacts/04_sag_buffering.png`

## How to Run
```bash
python master_tournament.py
```

