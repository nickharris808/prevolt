# Simulation 4: Stranded Memory Borrowing

## The Problem

Job crashes with OOM despite 500GB free memory in the cluster—it's just on the wrong node. CXL promises memory pooling, but the network doesn't know how to "borrow."

Memory stranding occurs when:
- **Fragmentation**: Each node has 20-40GB free, but no single node has 64GB
- **Locality preference**: Jobs prefer local memory for performance
- **Result**: OOM crashes despite available cluster capacity

## The Tournament

We compare three allocation algorithms:

| Algorithm | Description | Trade-off |
|-----------|-------------|-----------|
| **Local Only (Baseline)** | OOM crash if local memory insufficient | Fast but wastes cluster capacity |
| **Greedy Borrow** | Grab remote memory from first available node | May strand other jobs |
| **Balanced Borrow** | Borrow from node with most free memory | Optimal utilization, complex routing |

## The Model (SimPy + Pandas)

```python
class ClusterNode:
    total_memory: int      # 128GB per node
    allocated: int
    remote_borrowed: int   # Memory lent to other nodes
    remote_lending: int    # Memory borrowed from other nodes

class Job:
    memory_required: int   # e.g., 64GB
    preferred_node: int
    remote_allocation: Dict[node_id, int]  # Distributed memory map
```

## Key Files

- `cluster_model.py` - CXL cluster with memory pooling
- `simulation.py` - Job allocation with borrowing
- `tournament.py` - Tournament comparing 3 algorithms
- `gantt_chart.png` - Job execution timeline
- `utilization_heatmap.png` - Cluster utilization by scenario

## Running the Simulation

```bash
# Quick test (50 trials)
python tournament.py --quick

# Full tournament (1000 trials)
python tournament.py --n_trials 1000
```

## Patent Claim Support

> "A distributed memory allocation system wherein a memory request exceeding 
> local node capacity triggers a network-transparent borrowing protocol that 
> maps a contiguous virtual address space across multiple physical nodes 
> via CXL.mem tunneling."

### Key Findings

1. **Local Only** crashes 40%+ of jobs in fragmented clusters
2. **Greedy Borrow** reduces crashes but may strand subsequent jobs
3. **Balanced Borrow** achieves 95%+ completion rate

### The "Wow" Deliverable

The Gantt chart shows:
- Baseline: Red bars (OOM crashes)
- Invention: All green/yellow bars (completed with remote memory)

## Cluster Configuration

- 8 nodes, 128GB each = 1TB total
- Jobs require 32GB-96GB (variable)
- Fragmentation: Each node 30-50% pre-allocated

## Key Metrics

- **Job Completion Rate**: % of jobs that finish vs OOM crash
- **Memory Utilization**: Actual used / Total available
- **Remote Access Penalty**: Added latency for remote memory (10x local)

## Scenarios Tested

1. **8N_30pct_Frag**: 8 nodes, 30% fragmented
2. **8N_50pct_Frag**: 8 nodes, 50% fragmented (stress test)
3. **8N_LargeJobs**: Large 64-120GB jobs
4. **4N_30pct_Frag**: Small cluster, limited options
5. **16N_30pct_Frag**: Large cluster, many options
