"""
CXL Cluster Model for Stranded Memory Simulation
=================================================

This module provides a detailed model of a CXL memory cluster with:
- Multiple nodes with local memory
- Memory pooling via CXL.mem
- Remote memory access with latency penalty
- Job allocation and fragmentation tracking

The model captures the key dynamics of memory stranding in
disaggregated memory architectures.

Author: Portfolio B Research Team
License: Proprietary - Patent Pending
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum
import heapq


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class MemoryBlock:
    """
    Represents a contiguous block of memory.
    
    Attributes:
        block_id: Unique identifier
        node_id: Which node owns this memory
        size_gb: Size in gigabytes
        allocated_to_job: Job ID if allocated, None if free
        is_remote: Whether this is borrowed from another node
        source_node: Original node (for borrowed memory)
    """
    block_id: int
    node_id: int
    size_gb: float
    allocated_to_job: Optional[int] = None
    is_remote: bool = False
    source_node: Optional[int] = None
    
    @property
    def is_free(self) -> bool:
        return self.allocated_to_job is None


@dataclass
class ClusterNode:
    """
    Represents a node in the CXL cluster.
    
    Attributes:
        node_id: Unique identifier
        total_memory_gb: Total local memory capacity
        allocated_memory_gb: Memory allocated to local jobs
        borrowed_memory_gb: Memory borrowed from other nodes
        lending_memory_gb: Memory lent to other nodes
        memory_blocks: List of memory blocks on this node
    """
    node_id: int
    total_memory_gb: float = 128.0
    allocated_memory_gb: float = 0.0
    borrowed_memory_gb: float = 0.0
    lending_memory_gb: float = 0.0
    memory_blocks: List[MemoryBlock] = field(default_factory=list)
    
    @property
    def free_memory_gb(self) -> float:
        """Available memory for allocation."""
        return self.total_memory_gb - self.allocated_memory_gb - self.lending_memory_gb
    
    @property
    def utilization(self) -> float:
        """Memory utilization as fraction."""
        return self.allocated_memory_gb / self.total_memory_gb
    
    def can_allocate_locally(self, size_gb: float) -> bool:
        """Check if node can satisfy allocation locally."""
        return self.free_memory_gb >= size_gb
    
    def can_lend(self, size_gb: float) -> bool:
        """Check if node can lend memory to another node."""
        return self.free_memory_gb >= size_gb
    
    def allocate_local(self, job_id: int, size_gb: float) -> Optional[MemoryBlock]:
        """
        Allocate memory locally.
        
        Args:
            job_id: Job to allocate for
            size_gb: Amount to allocate
            
        Returns:
            MemoryBlock if successful, None otherwise
        """
        if not self.can_allocate_locally(size_gb):
            return None
        
        block = MemoryBlock(
            block_id=len(self.memory_blocks),
            node_id=self.node_id,
            size_gb=size_gb,
            allocated_to_job=job_id,
            is_remote=False
        )
        self.memory_blocks.append(block)
        self.allocated_memory_gb += size_gb
        return block
    
    def lend_memory(self, borrower_node_id: int, size_gb: float) -> Optional[MemoryBlock]:
        """
        Lend memory to another node.
        
        Args:
            borrower_node_id: Node requesting the memory
            size_gb: Amount to lend
            
        Returns:
            MemoryBlock representing the loan
        """
        if not self.can_lend(size_gb):
            return None
        
        self.lending_memory_gb += size_gb
        
        # Return block info for borrower
        block = MemoryBlock(
            block_id=len(self.memory_blocks),
            node_id=borrower_node_id,  # Assigned to borrower
            size_gb=size_gb,
            allocated_to_job=None,  # Will be set by borrower
            is_remote=True,
            source_node=self.node_id
        )
        self.memory_blocks.append(block)
        return block
    
    def free_memory_block(self, block: MemoryBlock):
        """Free a memory block."""
        if block.is_remote:
            self.borrowed_memory_gb -= block.size_gb
        else:
            self.allocated_memory_gb -= block.size_gb
        
        block.allocated_to_job = None


# =============================================================================
# JOB MODEL
# =============================================================================

class JobStatus(Enum):
    """Status of a job."""
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    CRASHED = 'crashed'  # OOM


@dataclass
class Job:
    """
    Represents a computational job requiring memory.
    
    Attributes:
        job_id: Unique identifier
        memory_required_gb: Total memory needed
        preferred_node: Preferred node for locality
        duration_us: Expected runtime in microseconds
        status: Current job status
        start_time: When job started
        end_time: When job completed/crashed
        local_memory_gb: Memory allocated locally
        remote_memory_gb: Memory borrowed from other nodes
        memory_blocks: List of allocated blocks
    """
    job_id: int
    memory_required_gb: float
    preferred_node: int
    duration_us: float
    status: JobStatus = JobStatus.PENDING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    local_memory_gb: float = 0.0
    remote_memory_gb: float = 0.0
    memory_blocks: List[MemoryBlock] = field(default_factory=list)
    
    @property
    def allocated_memory_gb(self) -> float:
        """Total memory allocated."""
        return self.local_memory_gb + self.remote_memory_gb
    
    @property
    def is_satisfied(self) -> bool:
        """Whether memory requirement is met."""
        return self.allocated_memory_gb >= self.memory_required_gb
    
    @property
    def remote_fraction(self) -> float:
        """Fraction of memory that is remote."""
        if self.allocated_memory_gb == 0:
            return 0.0
        return self.remote_memory_gb / self.allocated_memory_gb


# =============================================================================
# CXL CLUSTER
# =============================================================================

@dataclass
class ClusterConfig:
    """
    Configuration for the CXL cluster.
    
    Attributes:
        n_nodes: Number of nodes in cluster
        memory_per_node_gb: Memory capacity per node
        local_access_latency_us: Latency for local memory access
        remote_access_latency_us: Latency for remote (CXL) access
        fragmentation_level: Initial fragmentation (0-1)
    """
    n_nodes: int = 8
    memory_per_node_gb: float = 128.0
    local_access_latency_us: float = 0.1  # 100ns local
    remote_access_latency_us: float = 1.0  # 1μs remote (10x penalty)
    fragmentation_level: float = 0.3  # 30% fragmented


class CXLCluster:
    """
    Model of a CXL memory cluster with pooling capabilities.
    
    Features:
    - Multiple nodes with local memory
    - CXL.mem tunneling for remote access
    - Various allocation strategies
    - Fragmentation tracking
    """
    
    def __init__(self, config: ClusterConfig):
        """
        Initialize the cluster.
        
        Args:
            config: Cluster configuration
        """
        self.config = config
        
        # Create nodes
        self.nodes: Dict[int, ClusterNode] = {}
        for i in range(config.n_nodes):
            self.nodes[i] = ClusterNode(
                node_id=i,
                total_memory_gb=config.memory_per_node_gb
            )
        
        # Statistics
        self.jobs_completed: int = 0
        self.jobs_crashed: int = 0
        self.total_memory_allocated: float = 0.0
        self.total_remote_memory: float = 0.0
    
    @property
    def total_memory_gb(self) -> float:
        """Total cluster memory capacity."""
        return self.config.n_nodes * self.config.memory_per_node_gb
    
    @property
    def total_free_memory_gb(self) -> float:
        """Total free memory across cluster."""
        return sum(node.free_memory_gb for node in self.nodes.values())
    
    @property
    def cluster_utilization(self) -> float:
        """Overall cluster memory utilization."""
        total_allocated = sum(node.allocated_memory_gb for node in self.nodes.values())
        return total_allocated / self.total_memory_gb
    
    def apply_fragmentation(self, rng: np.random.Generator):
        """
        Apply initial fragmentation to simulate real-world cluster state.
        
        Args:
            rng: Random number generator
        """
        for node in self.nodes.values():
            # Allocate random-sized blocks to simulate fragmentation
            fragmented_amount = node.total_memory_gb * self.config.fragmentation_level
            allocated = 0.0
            
            while allocated < fragmented_amount:
                # Random block size (8-32 GB)
                block_size = rng.uniform(8, 32)
                block_size = min(block_size, fragmented_amount - allocated)
                
                if node.can_allocate_locally(block_size):
                    block = node.allocate_local(
                        job_id=-1,  # Phantom job for fragmentation
                        size_gb=block_size
                    )
                    allocated += block_size
                else:
                    break
    
    def get_node_free_memory(self) -> Dict[int, float]:
        """Get free memory per node."""
        return {nid: node.free_memory_gb for nid, node in self.nodes.items()}
    
    def find_nodes_with_free_memory(self, min_size_gb: float) -> List[int]:
        """Find nodes that can lend at least min_size_gb."""
        return [
            nid for nid, node in self.nodes.items()
            if node.free_memory_gb >= min_size_gb
        ]
    
    def get_node_with_most_free_memory(self, exclude: Optional[Set[int]] = None) -> Optional[int]:
        """
        Find the node with the most free memory.
        
        Args:
            exclude: Set of node IDs to exclude
            
        Returns:
            Node ID, or None if no nodes available
        """
        exclude = exclude or set()
        best_node = None
        best_free = 0.0
        
        for nid, node in self.nodes.items():
            if nid in exclude:
                continue
            if node.free_memory_gb > best_free:
                best_free = node.free_memory_gb
                best_node = nid
        
        return best_node


# =============================================================================
# ALLOCATION ALGORITHMS
# =============================================================================

class AllocationAlgorithm:
    """Base class for memory allocation algorithms."""
    
    def __init__(self, cluster: CXLCluster):
        self.cluster = cluster
    
    def allocate(self, job: Job) -> bool:
        """
        Attempt to allocate memory for a job.
        
        Args:
            job: Job requiring memory
            
        Returns:
            True if allocation succeeded, False if OOM
        """
        raise NotImplementedError


class LocalOnlyAlgorithm(AllocationAlgorithm):
    """
    Baseline: Only allocate from preferred node.
    
    If the preferred node doesn't have enough memory, the job crashes.
    This is the current behavior in most systems.
    """
    
    def allocate(self, job: Job) -> bool:
        node = self.cluster.nodes[job.preferred_node]
        
        if node.can_allocate_locally(job.memory_required_gb):
            block = node.allocate_local(job.job_id, job.memory_required_gb)
            job.local_memory_gb = job.memory_required_gb
            job.memory_blocks.append(block)
            return True
        
        # OOM - crash
        return False


class GreedyBorrowAlgorithm(AllocationAlgorithm):
    """
    Greedy Borrow: Take memory from first available node.
    
    If preferred node doesn't have enough, borrow from the first
    node that has any free memory. May strand other jobs.
    """
    
    def allocate(self, job: Job) -> bool:
        node = self.cluster.nodes[job.preferred_node]
        remaining = job.memory_required_gb
        
        # First, allocate locally as much as possible
        local_available = min(node.free_memory_gb, remaining)
        if local_available > 0:
            block = node.allocate_local(job.job_id, local_available)
            job.local_memory_gb = local_available
            job.memory_blocks.append(block)
            remaining -= local_available
        
        if remaining <= 0:
            return True
        
        # Borrow from other nodes (greedy: first available)
        for other_id, other_node in self.cluster.nodes.items():
            if other_id == job.preferred_node:
                continue
            
            if other_node.can_lend(remaining):
                block = other_node.lend_memory(job.preferred_node, remaining)
                block.allocated_to_job = job.job_id
                job.remote_memory_gb += remaining
                job.memory_blocks.append(block)
                self.cluster.nodes[job.preferred_node].borrowed_memory_gb += remaining
                remaining = 0
                break
            elif other_node.free_memory_gb > 0:
                # Take what's available
                available = other_node.free_memory_gb
                block = other_node.lend_memory(job.preferred_node, available)
                block.allocated_to_job = job.job_id
                job.remote_memory_gb += available
                job.memory_blocks.append(block)
                self.cluster.nodes[job.preferred_node].borrowed_memory_gb += available
                remaining -= available
        
        if remaining > 0:
            # Couldn't satisfy - but partial allocation happened
            # In real system, would need to roll back
            return False
        
        return True


class BalancedBorrowAlgorithm(AllocationAlgorithm):
    """
    Balanced Borrow: Borrow from node with most free memory (THE INVENTION).
    
    Optimizes cluster utilization by spreading borrowed memory
    across nodes with the most headroom. This prevents stranding
    other jobs while maximizing completion rate.
    """
    
    def allocate(self, job: Job) -> bool:
        node = self.cluster.nodes[job.preferred_node]
        remaining = job.memory_required_gb
        
        # First, allocate locally
        local_available = min(node.free_memory_gb, remaining)
        if local_available > 0:
            block = node.allocate_local(job.job_id, local_available)
            job.local_memory_gb = local_available
            job.memory_blocks.append(block)
            remaining -= local_available
        
        if remaining <= 0:
            return True
        
        # Borrow from nodes with most free memory (balanced)
        used_nodes = {job.preferred_node}
        
        while remaining > 0:
            # Find node with most free memory
            best_node_id = self.cluster.get_node_with_most_free_memory(exclude=used_nodes)
            
            if best_node_id is None:
                # No more nodes available
                break
            
            best_node = self.cluster.nodes[best_node_id]
            
            if best_node.free_memory_gb <= 0:
                break
            
            # Borrow what we need (or what's available)
            borrow_amount = min(best_node.free_memory_gb, remaining)
            
            block = best_node.lend_memory(job.preferred_node, borrow_amount)
            block.allocated_to_job = job.job_id
            job.remote_memory_gb += borrow_amount
            job.memory_blocks.append(block)
            self.cluster.nodes[job.preferred_node].borrowed_memory_gb += borrow_amount
            
            remaining -= borrow_amount
            used_nodes.add(best_node_id)
        
        return remaining <= 0


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == '__main__':
    print("Testing CXL Cluster Model...")
    
    config = ClusterConfig(n_nodes=4, memory_per_node_gb=128.0)
    cluster = CXLCluster(config)
    
    # Apply fragmentation
    rng = np.random.default_rng(42)
    cluster.apply_fragmentation(rng)
    
    print(f"\nCluster State After Fragmentation:")
    print(f"  Total Memory: {cluster.total_memory_gb} GB")
    print(f"  Free Memory: {cluster.total_free_memory_gb:.1f} GB")
    print(f"  Utilization: {cluster.cluster_utilization:.1%}")
    print(f"\n  Per-Node Free Memory: {cluster.get_node_free_memory()}")
    
    # Test job allocation
    job = Job(job_id=1, memory_required_gb=64, preferred_node=0, duration_us=1000)
    
    print(f"\nAllocating job requiring {job.memory_required_gb} GB on node 0...")
    
    for algo_name, algo_class in [
        ("Local Only", LocalOnlyAlgorithm),
        ("Greedy Borrow", GreedyBorrowAlgorithm),
        ("Balanced Borrow", BalancedBorrowAlgorithm)
    ]:
        # Reset cluster
        cluster = CXLCluster(config)
        cluster.apply_fragmentation(rng)
        
        job = Job(job_id=1, memory_required_gb=64, preferred_node=0, duration_us=1000)
        algo = algo_class(cluster)
        success = algo.allocate(job)
        
        print(f"\n  {algo_name}:")
        print(f"    Success: {success}")
        if success:
            print(f"    Local: {job.local_memory_gb:.1f} GB")
            print(f"    Remote: {job.remote_memory_gb:.1f} GB")
    
    print("\nCluster model test complete!")
