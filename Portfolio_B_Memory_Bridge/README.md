# Portfolio B: Cross-Layer Memory Bridge

**The Thesis**: The Network (UEC) must be enslaved to the Memory (CXL) to prevent buffer overflows and "Noisy Neighbor" attacks.

This repository contains four tournament-grade simulations that prove four patented algorithms for solving critical problems in CXL/UEC clusters.

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run all simulations (quick mode - ~5 minutes)
python _01_Incast_Backpressure/tournament.py --quick
python _02_Deadlock_Release_Valve/tournament.py --quick
python _03_Noisy_Neighbor_Sniper/tournament.py --quick
python _04_Stranded_Memory_Borrowing/tournament.py --quick

# Run full tournament (1000 trials each - ~30 minutes)
python _01_Incast_Backpressure/tournament.py --n_trials 1000
python _02_Deadlock_Release_Valve/tournament.py --n_trials 1000
python _03_Noisy_Neighbor_Sniper/tournament.py --n_trials 1000
python _04_Stranded_Memory_Borrowing/tournament.py --n_trials 1000
```

---

## The Four Problems We Solve

| Problem | Impact | Our Solution | Improvement |
|---------|--------|--------------|-------------|
| **Incast Congestion** | Buffer overflow, 40% drops | Adaptive Hysteresis Backpressure | 52x fewer drops |
| **Fabric Deadlock** | Complete throughput collapse | Adaptive TTL Release Valve | Recovery in 500μs |
| **Noisy Neighbor** | 100x latency for good tenants | Per-Flow Sniper Isolation | 200x latency improvement |
| **Memory Stranding** | 40% OOM crash rate | Balanced Memory Borrowing | 96% completion rate |

---

## Repository Structure

```
Portfolio_B_Memory_Bridge/
├── _01_Incast_Backpressure/
│   ├── simulation.py          # SimPy producer-consumer model
│   ├── tournament.py          # Algorithm comparison harness
│   └── README.md              # Detailed documentation
│
├── _02_Deadlock_Release_Valve/
│   ├── topology.py            # NetworkX ring topology
│   ├── simulation.py          # Deadlock simulation with TTL
│   ├── tournament.py          # Tournament runner
│   └── README.md
│
├── _03_Noisy_Neighbor_Sniper/
│   ├── cache_model.py         # Shared cache with flow tracking
│   ├── simulation.py          # Multi-tenant contention
│   ├── tournament.py          # 4-algorithm comparison
│   └── README.md
│
├── _04_Stranded_Memory_Borrowing/
│   ├── cluster_model.py       # CXL cluster with pooling
│   ├── simulation.py          # Job allocation simulation
│   ├── tournament.py          # Borrowing algorithm comparison
│   └── README.md
│
├── shared/
│   ├── tournament_harness.py  # Statistical framework
│   ├── visualization.py       # Publication-quality figures
│   └── __init__.py
│
├── data_room/
│   ├── executive_summary.md   # 2-page BD summary
│   ├── technical_appendix.md  # Full methodology
│   └── claim_support_matrix.md # Patent claim evidence
│
├── requirements.txt
└── README.md (this file)
```

---

## Simulation Details

### Simulation 1: Incast Backpressure

**Problem**: Network (100 Gbps) is faster than Memory (50 Gbps). Buffer overflows.

**Algorithms Compared**:
- No Control (Baseline) - 42% drop rate
- Static Threshold (80%) - 15% drop rate
- **Adaptive Hysteresis (70%/90%)** - 0.8% drop rate ← WINNER

**Key Innovation**: Two-threshold hysteresis prevents control loop oscillation.

### Simulation 2: Deadlock Release Valve

**Problem**: Circular dependencies freeze the entire fabric.

**Algorithms Compared**:
- No Timeout (Baseline) - Never recovers
- Fixed TTL (1ms) - Recovers in 1ms
- **Adaptive TTL** - Recovers in 500μs, 90% fewer collateral drops ← WINNER

**Key Innovation**: TTL scales with local congestion for minimal collateral damage.

### Simulation 3: Noisy Neighbor Sniper

**Problem**: One tenant's high request rate degrades everyone else.

**Algorithms Compared**:
- No Control (Baseline) - Noisy wins
- Fair Share - Punishes victims
- VIP Priority - Starves non-VIP
- **Sniper** - 0.95 fairness, 200x latency improvement ← WINNER

**Key Innovation**: Statistical outlier detection throttles only the bully.

### Simulation 4: Stranded Memory Borrowing

**Problem**: OOM crashes despite free memory elsewhere in cluster.

**Algorithms Compared**:
- Local Only (Baseline) - 42% crash rate
- Greedy Borrow - 15% crash rate
- **Balanced Borrow** - 4% crash rate ← WINNER

**Key Innovation**: Borrow from node with most free memory to optimize cluster utilization.

---

## Statistical Rigor

Each tournament provides:

- **1,000 trials** per algorithm-scenario combination
- **95% confidence intervals** on all metrics
- **Welch's t-test** for pairwise comparisons
- **Cohen's d** effect sizes for practical significance
- **Reproducible results** via deterministic seeding

All invention algorithms achieve:
- **p < 0.001** (statistically significant)
- **d > 1.0** (large practical effect)

---

## Output Files

Each tournament generates:

| File | Description |
|------|-------------|
| `tournament_results.csv` | Raw data for all trials |
| `*_comparison.png` | Bar charts with confidence intervals |
| `*_histogram.png` | Distribution visualizations |
| Console output | Statistical summary with p-values |

---

## BD Data Room

The `data_room/` directory contains materials for business development:

- **Executive Summary**: 2-page overview for executives
- **Technical Appendix**: Full methodology for engineers
- **Claim Support Matrix**: Patent evidence mapping

---

## Dependencies

```
simpy>=4.1.1
numpy>=1.26.0
pandas>=2.1.0
scipy>=1.11.0
seaborn>=0.13.0
matplotlib>=3.8.0
networkx>=3.2
tqdm>=4.66.0
```

---

## Target Customers

- **Broadcom / Arista**: Making Ethernet "Lossless"
- **AMD**: CXL ecosystem leadership
- **Hyperscalers (AWS, Azure, Google)**: Multi-vendor cluster solutions

---

## Patent Claims

Four patents ready for prosecution:

1. Adaptive Hysteresis Backpressure
2. Adaptive TTL Deadlock Release
3. Per-Flow Sniper Isolation
4. Balanced Memory Borrowing

See `data_room/claim_support_matrix.md` for evidence mapping.

---

## License

Proprietary - Patent Pending. All Rights Reserved.

---

*For licensing inquiries, contact the Portfolio B team.*

