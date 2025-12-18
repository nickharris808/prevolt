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
from typing import Dict, List, Optional, Tuple
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cluster_model import (
    CXLCluster, ClusterConfig, ClusterNode, Job, JobStatus,
    LocalOnlyAlgorithm, GreedyBorrowAlgorithm, BalancedBorrowAlgorithm
)


# =============================================================================
# SIMULATION PARAMETERS
# =============================================================================

@dataclass
class StrandedMemoryConfig:
    """
    Configuration for the stranded memory simulation.
    
    Attributes:
        n_nodes: Number of nodes in cluster
        memory_per_node_gb: Memory per node
        n_jobs: Number of jobs to simulate
        min_job_memory_gb: Minimum job memory requirement
        max_job_memory_gb: Maximum job memory requirement
        job_duration_us: Job execution time
        simulation_duration_us: Total simulation time
        fragmentation_level: Initial fragmentation (0-1)
        local_latency_us: Local memory access latency
        remote_latency_us: Remote (CXL) access latency
        job_arrival_rate: Jobs per microsecond
    """
    n_nodes: int = 8
    memory_per_node_gb: float = 128.0
    n_jobs: int = 100
    min_job_memory_gb: float = 32.0
    max_job_memory_gb: float = 96.0
    job_duration_us: float = 1000.0
    simulation_duration_us: float = 50000.0  # 50ms
    fragmentation_level: float = 0.3
    local_latency_us: float = 0.1
    remote_latency_us: float = 1.0
    job_arrival_rate: float = 0.002  # 2 jobs per ms


# =============================================================================
# SIMULATION STATE
# =============================================================================

@dataclass
class JobRecord:
    """
    Record of a completed/crashed job for analysis.
    
    Attributes:
        job_id: Job identifier
        memory_required_gb: Memory requested
        preferred_node: Preferred node
        status: Final status
        start_time: Start time (or None if never started)
        end_time: End time (or crash time)
        local_memory_gb: Local memory used
        remote_memory_gb: Remote memory used
        execution_time_us: Actual execution time
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
    
    Attributes:
        current_time: Current simulation time
        jobs_submitted: Total jobs submitted
        jobs_completed: Jobs that finished successfully
        jobs_crashed: Jobs that crashed (OOM)
        job_records: Detailed records for each job
        cluster_utilization_samples: Time series of utilization
        stranded_memory_samples: Time series of stranded memory
    """
    current_time: float = 0.0
    jobs_submitted: int = 0
    jobs_completed: int = 0
    jobs_crashed: int = 0
    job_records: List[JobRecord] = field(default_factory=list)
    cluster_utilization_samples: List[Tuple[float, float]] = field(default_factory=list)
    stranded_memory_samples: List[Tuple[float, float]] = field(default_factory=list)


# =============================================================================
# JOB GENERATOR
# =============================================================================

def generate_jobs(
    config: StrandedMemoryConfig,
    rng: np.random.Generator
) -> List[Job]:
    """
    Generate a batch of jobs with random memory requirements.
    
    Args:
        config: Simulation configuration
        rng: Random number generator
        
    Returns:
        List of Job objects
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
        duration = max(100, rng.normal(config.job_duration_us, config.job_duration_us * 0.2))
        
        job = Job(
            job_id=i,
            memory_required_gb=memory_required,
            preferred_node=preferred_node,
            duration_us=duration
        )
        jobs.append(job)
    
    return jobs


# =============================================================================
# SIMULATION RUNNER
# =============================================================================

def run_stranded_memory_simulation(
    config: StrandedMemoryConfig,
    algorithm_type: str,
    seed: int
) -> Dict[str, float]:
    """
    Run a single stranded memory simulation.
    
    Args:
        config: Simulation configuration
        algorithm_type: 'local_only', 'greedy_borrow', or 'balanced_borrow'
        seed: Random seed
        
    Returns:
        Dictionary of metrics
    """
    rng = np.random.default_rng(seed)
    
    # Create cluster
    cluster_config = ClusterConfig(
        n_nodes=config.n_nodes,
        memory_per_node_gb=config.memory_per_node_gb,
        local_access_latency_us=config.local_latency_us,
        remote_access_latency_us=config.remote_latency_us,
        fragmentation_level=config.fragmentation_level
    )
    cluster = CXLCluster(cluster_config)
    
    # Apply initial fragmentation
    cluster.apply_fragmentation(rng)
    
    # Create allocation algorithm
    if algorithm_type == 'local_only':
        allocator = LocalOnlyAlgorithm(cluster)
    elif algorithm_type == 'greedy_borrow':
        allocator = GreedyBorrowAlgorithm(cluster)
    elif algorithm_type == 'balanced_borrow':
        allocator = BalancedBorrowAlgorithm(cluster)
    elif algorithm_type == 'cooperative':
        allocator = CooperativeBorrowAlgorithm(cluster)
    else:
        raise ValueError(f"Unknown algorithm: {algorithm_type}")
    
    # Generate jobs
    jobs = generate_jobs(config, rng)
    
    # Simulation state
    state = SimulationState()
    
    # Active jobs (job_id -> expected_completion_time)
    active_jobs: Dict[int, Tuple[Job, float]] = {}
    
    # Job queue (arrival_time, job)
    job_queue = []
    
    # Schedule job arrivals
    arrival_time = 0.0
    for job in jobs:
        inter_arrival = rng.exponential(1.0 / config.job_arrival_rate)
        arrival_time += inter_arrival
        heapq.heappush(job_queue, (arrival_time, job))
    
    # Main simulation loop
    current_time = 0.0
    
    while current_time < config.simulation_duration_us:
        # Process job arrivals
        while job_queue and job_queue[0][0] <= current_time:
            arrival_time, job = heapq.heappop(job_queue)
            state.jobs_submitted += 1
            
            # Attempt allocation
            success = allocator.allocate(job)
            
            if success:
                job.status = JobStatus.RUNNING
                job.start_time = current_time
                completion_time = current_time + job.duration_us
                
                # Adjust for remote memory penalty
                if job.remote_memory_gb > 0:
                    remote_fraction = job.remote_memory_gb / job.allocated_memory_gb
                    latency_penalty = remote_fraction * (config.remote_latency_us / config.local_latency_us)
                    completion_time += job.duration_us * latency_penalty * 0.1  # 10% penalty per remote fraction
                
                active_jobs[job.job_id] = (job, completion_time)
            else:
                # OOM crash
                job.status = JobStatus.CRASHED
                job.end_time = current_time
                state.jobs_crashed += 1
                
                record = JobRecord(
                    job_id=job.job_id,
                    memory_required_gb=job.memory_required_gb,
                    preferred_node=job.preferred_node,
                    status=job.status,
                    start_time=None,
                    end_time=current_time,
                    local_memory_gb=0.0,
                    remote_memory_gb=0.0
                )
                state.job_records.append(record)
        
        # Process job completions
        completed_jobs = []
        for job_id, (job, completion_time) in active_jobs.items():
            if completion_time <= current_time:
                job.status = JobStatus.COMPLETED
                job.end_time = current_time
                state.jobs_completed += 1
                
                # Free memory
                for block in job.memory_blocks:
                    source_node = block.source_node if block.is_remote else block.node_id
                    if source_node is not None and source_node in cluster.nodes:
                        cluster.nodes[source_node].lending_memory_gb -= block.size_gb
                    cluster.nodes[block.node_id].free_memory_block(block)
                
                record = JobRecord(
                    job_id=job.job_id,
                    memory_required_gb=job.memory_required_gb,
                    preferred_node=job.preferred_node,
                    status=job.status,
                    start_time=job.start_time,
                    end_time=job.end_time,
                    local_memory_gb=job.local_memory_gb,
                    remote_memory_gb=job.remote_memory_gb,
                    execution_time_us=job.end_time - job.start_time if job.start_time else 0
                )
                state.job_records.append(record)
                completed_jobs.append(job_id)
        
        for job_id in completed_jobs:
            del active_jobs[job_id]
        
        # Record cluster state periodically
        if int(current_time) % 100 == 0:
            state.cluster_utilization_samples.append(
                (current_time, cluster.cluster_utilization)
            )
            
            # Calculate stranded memory (free memory on nodes where jobs are waiting)
            stranded = sum(
                node.free_memory_gb 
                for node in cluster.nodes.values() 
                if node.free_memory_gb > 0 and node.free_memory_gb < config.min_job_memory_gb
            )
            state.stranded_memory_samples.append((current_time, stranded))
        
        # Advance time
        current_time += 1.0
    
    state.current_time = current_time
    
    # Compute metrics
    return compute_metrics(config, cluster, state)


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
        max_utilization = float(np.max(utilizations))
    else:
        avg_utilization = 0.0
        max_utilization = 0.0
    
    # Remote memory usage
    completed_records = [r for r in state.job_records if r.completed]
    if len(completed_records) > 0:
        remote_fractions = [
            r.remote_memory_gb / (r.local_memory_gb + r.remote_memory_gb)
            if (r.local_memory_gb + r.remote_memory_gb) > 0 else 0
            for r in completed_records
        ]
        avg_remote_fraction = float(np.mean(remote_fractions))
        jobs_using_remote = sum(1 for r in completed_records if r.remote_memory_gb > 0)
        remote_job_fraction = jobs_using_remote / len(completed_records)
    else:
        avg_remote_fraction = 0.0
        remote_job_fraction = 0.0
    
    # Execution time statistics
    if len(completed_records) > 0:
        exec_times = [r.execution_time_us for r in completed_records if r.execution_time_us > 0]
        if len(exec_times) > 0:
            avg_exec_time = float(np.mean(exec_times))
            p99_exec_time = float(np.percentile(exec_times, 99))
        else:
            avg_exec_time = 0.0
            p99_exec_time = 0.0
    else:
        avg_exec_time = 0.0
        p99_exec_time = 0.0
    
    # Stranded memory
    if len(state.stranded_memory_samples) > 0:
        stranded = [s[1] for s in state.stranded_memory_samples]
        avg_stranded = float(np.mean(stranded))
    else:
        avg_stranded = 0.0
    
    return {
        'completion_rate': completion_rate,
        'crash_rate': crash_rate,
        'jobs_completed': float(state.jobs_completed),
        'jobs_crashed': float(state.jobs_crashed),
        'avg_utilization': avg_utilization,
        'max_utilization': max_utilization,
        'avg_remote_fraction': avg_remote_fraction,
        'remote_job_fraction': remote_job_fraction,
        'avg_exec_time_us': avg_exec_time,
        'p99_exec_time_us': p99_exec_time,
        'avg_stranded_memory_gb': avg_stranded
    }


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == '__main__':
    print("Testing Stranded Memory Simulation...")
    print("-" * 50)
    
    config = StrandedMemoryConfig(
        n_nodes=8,
        n_jobs=50,
        simulation_duration_us=20000.0,
        fragmentation_level=0.4
    )
    
    for algo in ['local_only', 'greedy_borrow', 'balanced_borrow']:
        results = run_stranded_memory_simulation(config, algo, seed=42)
        print(f"\n{algo.upper().replace('_', ' ')}:")
        print(f"  Completion Rate: {results['completion_rate']:.2%}")
        print(f"  Crash Rate: {results['crash_rate']:.2%}")
        print(f"  Avg Utilization: {results['avg_utilization']:.2%}")
        print(f"  Remote Job Fraction: {results['remote_job_fraction']:.2%}")
    
    print("\n" + "=" * 50)
    print("Stranded memory simulation test complete!")


# Import heapq at the module level for job queue
import heapq
