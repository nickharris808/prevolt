"""
Stranded Memory Borrowing Simulation
====================================

This module simulates memory stranding in CXL clusters and the borrowing
mechanisms that prevent OOM crashes.

The key innovation is the "Balanced Borrow" algorithm that optimizes
cluster-wide utilization by borrowing from nodes with the most headroom.

Patent Claim Support:
"A distributed memory allocation system wherein a memory request exceeding 
local node capacity triggers a network-transparent borrowing protocol that 
maps a contiguous virtual address space across multiple physical nodes 
via CXL.mem tunneling."

Author: Portfolio B Research Team
License: Proprietary - Patent Pending
"""

import simpy
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.physics_engine import Physics
from cluster_model import (
    CXLCluster, ClusterConfig, ClusterNode, Job, JobStatus,
    LocalOnlyAlgorithm, GreedyBorrowAlgorithm, BalancedBorrowAlgorithm,
    CooperativeBorrowAlgorithm, PredictivePreBorrowAlgorithm, FairShareBorrowAlgorithm
)


# =============================================================================
# SIMULATION PARAMETERS
# =============================================================================

@dataclass
class StrandedMemoryConfig:
    """
    Configuration for the stranded memory simulation (Physics-Correct).
    
    Attributes:
        n_nodes: Number of nodes in cluster
        memory_per_node_gb: Memory per node
        n_jobs: Number of jobs to simulate
        min_job_memory_gb: Minimum job memory requirement
        max_job_memory_gb: Maximum job memory requirement
        job_duration_ns: Job execution time
        simulation_duration_ns: Total simulation time
        fragmentation_level: Initial fragmentation (0-1)
        local_latency_ns: Local memory access latency
        remote_latency_ns: Remote (CXL) access latency
        job_arrival_rate: Jobs per nanosecond
    """
    n_nodes: int = 8
    memory_per_node_gb: float = 128.0
    n_jobs: int = 100
    min_job_memory_gb: float = 32.0
    max_job_memory_gb: float = 96.0
    job_duration_ns: float = 1_000_000.0 # 1ms
    simulation_duration_ns: float = 50_000_000.0 # 50ms
    fragmentation_level: float = 0.3
    local_latency_ns: float = Physics.CXL_LOCAL_NS
    remote_latency_ns: float = Physics.CXL_FABRIC_1HOP_NS
    job_arrival_rate: float = 0.000002  # 2 jobs per ms


# =============================================================================
# SIMULATION STATE
# =============================================================================

@dataclass
class JobRecord:
    """
    Record of a completed/crashed job for analysis.
    """
    job_id: int
    memory_required_gb: float
    preferred_node: int
    status: JobStatus
    start_time: Optional[float]
    end_time: Optional[float]
    local_memory_gb: float
    remote_memory_gb: float
    execution_time_us: float = 0.0
    
    @property
    def completed(self) -> bool:
        return self.status == JobStatus.COMPLETED
    
    @property
    def crashed(self) -> bool:
        return self.status == JobStatus.CRASHED


@dataclass
class SimulationState:
    """
    Tracks simulation state and statistics.
    """
    current_time: float = 0.0
    jobs_submitted: int = 0
    jobs_completed: int = 0
    jobs_crashed: int = 0
    job_records: List[JobRecord] = field(default_factory=list)
    cluster_utilization_samples: List[Tuple[float, float]] = field(default_factory=list)
    stranded_memory_samples: List[Tuple[float, float]] = field(default_factory=list)


# =============================================================================
# TRAFFIC GENERATOR
# =============================================================================

def generate_jobs(config: StrandedMemoryConfig, rng: np.random.Generator) -> List[Job]:
    """
    Generate a set of jobs based on configuration.
    """
    jobs = []
    
    for i in range(config.n_jobs):
        # Random memory requirement (uniform distribution)
        memory_required = rng.uniform(
            config.min_job_memory_gb,
            config.max_job_memory_gb
        )
        
        # Random preferred node
        preferred_node = rng.integers(0, config.n_nodes)
        
        # Random duration (normal distribution around base)
        duration = max(100, rng.normal(config.job_duration_ns, config.job_duration_ns * 0.2))
        
        job = Job(
            job_id=i,
            memory_required_gb=memory_required,
            preferred_node=preferred_node,
            duration_ns=duration
        )
        jobs.append(job)
    
    return jobs


# =============================================================================
# SIMULATION RUNNER
# =============================================================================

def run_stranded_memory_simulation(
    config: StrandedMemoryConfig,
    algorithm_type: str,
    seed: int,
    telemetry_publisher: Optional[Any] = None,
    coordination_matrix: Optional[Any] = None,
    env: Optional[simpy.Environment] = None
) -> Dict[str, float]:
    """
    Run a single stranded memory simulation.
    """
    rng = np.random.default_rng(seed)
    
    local_sim = False
    if env is None:
        env = simpy.Environment()
        local_sim = True
    
    # Create cluster
    cluster_config = ClusterConfig(
        n_nodes=config.n_nodes,
        memory_per_node_gb=config.memory_per_node_gb,
        local_access_latency_ns=config.local_latency_ns,
        remote_access_latency_ns=config.remote_latency_ns,
        fragmentation_level=config.fragmentation_level
    )
    cluster = CXLCluster(cluster_config, telemetry_publisher)
    
    # Apply initial fragmentation
    cluster.apply_fragmentation(rng)
    
    # Create allocation algorithm
    if algorithm_type == 'local_only':
        allocator = LocalOnlyAlgorithm(cluster)
    elif algorithm_type == 'greedy_borrow':
        allocator = GreedyBorrowAlgorithm(cluster)
    elif algorithm_type == 'balanced_borrow':
        allocator = BalancedBorrowAlgorithm(cluster, coordination_matrix)
    elif algorithm_type == 'cooperative':
        allocator = CooperativeBorrowAlgorithm(cluster)
    elif algorithm_type == 'predictive':
        allocator = PredictivePreBorrowAlgorithm(cluster)
    elif algorithm_type == 'fair_share':
        allocator = FairShareBorrowAlgorithm(cluster)
    else:
        raise ValueError(f"Unknown algorithm: {algorithm_type}")
    
    # Generate jobs
    jobs = generate_jobs(config, rng)
    
    # Simulation state
    state = SimulationState()
    
    # Simulation process (since PF7 doesn't have a natural background process)
    def pf7_process():
        # Active jobs (job_id -> expected_completion_time)
        active_jobs: Dict[int, Tuple[Job, float]] = {}
        
        # Job queue (arrival_time, job)
        job_queue = []
        
        # Schedule job arrivals
        arrival_time = 0.0
        for job in jobs:
            inter_arrival = rng.exponential(1.0 / config.job_arrival_rate)
            arrival_time += inter_arrival
            import heapq
            heapq.heappush(job_queue, (arrival_time, job))
            
        while env.now < config.simulation_duration_ns:
            # Process job arrivals
            import heapq
            while job_queue and job_queue[0][0] <= env.now:
                arrival_time, job = heapq.heappop(job_queue)
                state.jobs_submitted += 1
                
                success = allocator.allocate(job)
                
                if success:
                    job.status = JobStatus.RUNNING
                    job.start_time = env.now
                    completion_time = env.now + job.duration_ns
                    
                    if job.remote_memory_gb > 0:
                        remote_fraction = job.remote_memory_gb / job.allocated_memory_gb
                        latency_penalty = remote_fraction * (config.remote_latency_ns / config.local_latency_ns)
                        completion_time += job.duration_ns * latency_penalty * 0.1
                    
                    active_jobs[job.job_id] = (job, completion_time)
                else:
                    job.status = JobStatus.CRASHED
                    job.end_time = env.now
                    state.jobs_crashed += 1
                    state.job_records.append(JobRecord(job.job_id, job.memory_required_gb, job.preferred_node, job.status, None, env.now, 0.0, 0.0))
            
            # Process completions
            completed_jobs = []
            for job_id, (job, completion_time) in active_jobs.items():
                if completion_time <= env.now:
                    job.status = JobStatus.COMPLETED
                    job.end_time = env.now
                    state.jobs_completed += 1
                    for block in job.memory_blocks:
                        source_node = block.source_node if block.is_remote else block.node_id
                        if source_node is not None and source_node in cluster.nodes:
                            cluster.nodes[source_node].lending_memory_gb -= block.size_gb
                        cluster.nodes[block.node_id].free_memory_block(block)
                    state.job_records.append(JobRecord(job.job_id, job.memory_required_gb, job.preferred_node, job.status, job.start_time, job.end_time, job.local_memory_gb, job.remote_memory_gb, (job.end_time-job.start_time)/1000.0))
                    completed_jobs.append(job_id)
            
            for job_id in completed_jobs: del active_jobs[job_id]
            
            # Telemetry
            if int(env.now) % 10000 == 0:
                state.cluster_utilization_samples.append((env.now, cluster.cluster_utilization))
                cluster.publish_telemetry()
                
            yield env.timeout(100.0) # 100ns tick for allocation

    env.process(pf7_process())
    
    if local_sim:
        env.run(until=config.simulation_duration_ns)
        return compute_metrics(config, cluster, state)
    else:
        return (cluster, state)


def compute_metrics(
    config: StrandedMemoryConfig,
    cluster: CXLCluster,
    state: SimulationState
) -> Dict[str, float]:
    """Compute output metrics from simulation state."""
    
    # Job completion rate
    total_jobs = state.jobs_submitted
    if total_jobs == 0:
        completion_rate = 0.0
        crash_rate = 0.0
    else:
        completion_rate = state.jobs_completed / total_jobs
        crash_rate = state.jobs_crashed / total_jobs
    
    # Memory utilization
    if len(state.cluster_utilization_samples) > 0:
        utilizations = [u[1] for u in state.cluster_utilization_samples]
        avg_utilization = float(np.mean(utilizations))
    else:
        avg_utilization = 0.0
    
    # Remote memory usage
    completed_records = [r for r in state.job_records if r.completed]
    if len(completed_records) > 0:
        remote_fractions = [
            r.remote_memory_gb / (r.local_memory_gb + r.remote_memory_gb)
            if (r.local_memory_gb + r.remote_memory_gb) > 0 else 0
            for r in completed_records
        ]
        avg_remote_fraction = float(np.mean(remote_fractions))
    else:
        avg_remote_fraction = 0.0
    
    return {
        'completion_rate': completion_rate,
        'crash_rate': crash_rate,
        'avg_utilization': avg_utilization,
        'avg_remote_fraction': avg_remote_fraction,
        'jobs_submitted': float(total_jobs),
        'jobs_completed': float(state.jobs_completed),
        'jobs_crashed': float(state.jobs_crashed)
    }


if __name__ == '__main__':
    config = StrandedMemoryConfig(n_jobs=50)
    for algo in ['local_only', 'balanced_borrow']:
        results = run_stranded_memory_simulation(config, algo, seed=42)
        print(f"\n{algo.upper()}: completion={results['completion_rate']:.1%}, utilization={results['avg_utilization']:.1%}")
