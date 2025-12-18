"""
Incast Backpressure Simulation
==============================

This module simulates the fundamental problem of network-memory speed mismatch:
- Network can deliver 100 Gbps
- Memory controller can only drain 50 Gbps
- Result: Buffer overflow and packet drops

The simulation uses SimPy to model a producer-consumer queue with configurable
backpressure mechanisms.

Patent Claim Support:
"A memory flow control apparatus wherein a network interface modulates 
transmission rate in inverse proportion to memory buffer occupancy, 
utilizing hysteresis thresholds to prevent oscillation."

Author: Portfolio B Research Team
License: Proprietary - Patent Pending
"""

import simpy
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable
from enum import Enum
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =============================================================================
# SIMULATION PARAMETERS
# =============================================================================

@dataclass
class IncastConfig:
    """
    Configuration parameters for the Incast simulation.
    
    Attributes:
        buffer_capacity_bytes: Maximum buffer size in bytes
        network_rate_gbps: Network ingress rate in Gbps
        memory_rate_gbps: Memory controller drain rate in Gbps
        simulation_duration_us: Total simulation time in microseconds
        packet_size_bytes: Size of each packet
        traffic_pattern: 'uniform', 'bursty', or 'incast'
        n_senders: Number of concurrent senders (for incast pattern)
        burst_factor: Multiplier for burst intensity
        backpressure_threshold: Threshold (0-1) to activate backpressure
        hysteresis_low: Lower threshold for hysteresis (resume sending)
        hysteresis_high: Upper threshold for hysteresis (pause sending)
    """
    # Buffer and rate parameters (realistic for CXL/UEC systems)
    buffer_capacity_bytes: int = 10_000_000  # 10 MB buffer
    network_rate_gbps: float = 200.0         # 200 Gbps network (200% Load)
    memory_rate_gbps: float = 100.0          # 100 Gbps memory drain
    
    # Simulation parameters
    simulation_duration_us: float = 1000.0   # 1ms simulation
    packet_size_bytes: int = 1500            # Standard MTU
    
    # Traffic pattern parameters
    traffic_pattern: str = 'uniform'         # 'uniform', 'bursty', 'incast'
    n_senders: int = 100                     # Number of senders for incast
    burst_factor: float = 5.0                # Burst intensity multiplier
    
    # Backpressure parameters
    backpressure_threshold: float = 0.80     # 80% threshold
    hysteresis_low: float = 0.70             # Resume at 70%
    hysteresis_high: float = 0.90            # Pause at 90%
    
    @property
    def network_rate_bytes_per_us(self) -> float:
        """Convert network rate to bytes per microsecond."""
        return (self.network_rate_gbps * 1e9 / 8) / 1e6
    
    @property
    def memory_rate_bytes_per_us(self) -> float:
        """Convert memory drain rate to bytes per microsecond."""
        return (self.memory_rate_gbps * 1e9 / 8) / 1e6
    
    @property
    def packet_inter_arrival_us(self) -> float:
        """Average time between packet arrivals in microseconds."""
        return self.packet_size_bytes / self.network_rate_bytes_per_us
    
    @property
    def packet_drain_time_us(self) -> float:
        """Time to drain one packet in microseconds."""
        return self.packet_size_bytes / self.memory_rate_bytes_per_us


class TrafficPattern(Enum):
    """Enumeration of supported traffic patterns."""
    UNIFORM = 'uniform'
    BURSTY = 'bursty'
    INCAST = 'incast'


# =============================================================================
# SIMULATION STATE
# =============================================================================

@dataclass
class SimulationState:
    """
    Tracks the state of the simulation for metrics collection.
    
    Attributes:
        queue_depth_samples: List of (time, depth) tuples
        packets_arrived: Total packets that arrived at the buffer
        packets_dropped: Packets dropped due to buffer overflow
        packets_drained: Packets successfully processed by memory
        backpressure_events: Number of times backpressure was activated
        total_latency_us: Sum of all packet latencies
        latencies: List of individual packet latencies
    """
    queue_depth_samples: List[Tuple[float, int]] = field(default_factory=list)
    packets_arrived: int = 0
    packets_dropped: int = 0
    packets_drained: int = 0
    backpressure_events: int = 0
    total_latency_us: float = 0.0
    latencies: List[float] = field(default_factory=list)
    total_drain_time_us: float = 0.0  # Time memory controller was busy
    
    @property
    def drop_rate(self) -> float:
        """Calculate packet drop rate as a fraction."""
        if self.packets_arrived == 0:
            return 0.0
        return self.packets_dropped / self.packets_arrived

    @property
    def utilization(self) -> float:
        """Calculate memory link utilization."""
        if self.packets_drained == 0:
            return 0.0
        # This will be calculated at the end based on total_drain_time_us vs simulation duration
        return 0.0 # Placeholder
        """Calculate packet drop rate as a fraction."""
        if self.packets_arrived == 0:
            return 0.0
        return self.packets_dropped / self.packets_arrived
    
    @property
    def throughput_fraction(self) -> float:
        """Calculate effective throughput as fraction of maximum."""
        if self.packets_arrived == 0:
            return 0.0
        return self.packets_drained / self.packets_arrived
    
    @property
    def avg_latency_us(self) -> float:
        """Calculate average packet latency."""
        if self.packets_drained == 0:
            return 0.0
        return self.total_latency_us / self.packets_drained
    
    @property
    def p99_latency_us(self) -> float:
        """Calculate 99th percentile latency."""
        if len(self.latencies) == 0:
            return 0.0
        return np.percentile(self.latencies, 99)


# =============================================================================
# PACKET MODEL
# =============================================================================

@dataclass
class Packet:
    """
    Represents a network packet in the simulation.
    
    Attributes:
        packet_id: Unique identifier
        size_bytes: Packet size
        arrival_time: Time packet arrived at buffer
        sender_id: ID of the sending node (for incast)
    """
    packet_id: int
    size_bytes: int
    arrival_time: float
    sender_id: int = 0


# =============================================================================
# CORE SIMULATION COMPONENTS
# =============================================================================

class MemoryBuffer:
    """
    Simulates a memory buffer with configurable capacity and backpressure.
    
    This is the core component that receives packets from the network
    and drains them to the memory controller. It tracks queue depth
    and can signal backpressure to upstream senders.
    """
    
    def __init__(self, env: simpy.Environment, config: IncastConfig):
        """
        Initialize the memory buffer.
        
        Args:
            env: SimPy environment
            config: Simulation configuration
        """
        self.env = env
        self.config = config
        
        # Queue represented as a list of packets
        self.queue: List[Packet] = []
        self.current_size_bytes: int = 0
        
        # Backpressure state
        self.backpressure_active: bool = False
        
        # Statistics
        self.state = SimulationState()
        
    @property
    def occupancy_fraction(self) -> float:
        """Current buffer occupancy as a fraction (0 to 1)."""
        return self.current_size_bytes / self.config.buffer_capacity_bytes
    
    def can_accept_packet(self, packet: Packet) -> bool:
        """Check if buffer has room for the packet."""
        return (self.current_size_bytes + packet.size_bytes) <= self.config.buffer_capacity_bytes
    
    def enqueue(self, packet: Packet) -> bool:
        """
        Attempt to enqueue a packet.
        
        Args:
            packet: The packet to enqueue
            
        Returns:
            True if packet was accepted, False if dropped
        """
        self.state.packets_arrived += 1
        
        if self.can_accept_packet(packet):
            self.queue.append(packet)
            self.current_size_bytes += packet.size_bytes
            self._record_queue_depth()
            return True
        else:
            self.state.packets_dropped += 1
            return False
    
    def dequeue(self) -> Optional[Packet]:
        """
        Remove and return the next packet from the queue.
        
        Returns:
            The dequeued packet, or None if queue is empty
        """
        if len(self.queue) == 0:
            return None
        
        packet = self.queue.pop(0)
        self.current_size_bytes -= packet.size_bytes
        self.state.packets_drained += 1
        
        # Calculate latency
        latency = self.env.now - packet.arrival_time
        self.state.total_latency_us += latency
        self.state.latencies.append(latency)
        
        self._record_queue_depth()
        return packet
    
    def _record_queue_depth(self):
        """Record current queue depth for analysis."""
        self.state.queue_depth_samples.append(
            (self.env.now, self.current_size_bytes)
        )


# =============================================================================
# BACKPRESSURE ALGORITHMS
# =============================================================================

class BackpressureAlgorithm:
    """Base class for backpressure algorithms."""
    
    def __init__(self, buffer: MemoryBuffer, config: IncastConfig):
        self.buffer = buffer
        self.config = config
    
    def should_pause(self) -> bool:
        """Return True if sender should pause."""
        raise NotImplementedError
    
    def should_resume(self) -> bool:
        """Return True if sender can resume after pausing."""
        raise NotImplementedError


class NoControlAlgorithm(BackpressureAlgorithm):
    """
    Baseline: No backpressure control.
    
    Packets are sent at full rate regardless of buffer state.
    This leads to catastrophic drops when buffer fills.
    """
    
    def should_pause(self) -> bool:
        return False
    
    def should_resume(self) -> bool:
        return True


class StaticThresholdAlgorithm(BackpressureAlgorithm):
    """
    Direct-to-Source Backpressure (Hardware Signal Path).
    
    The CXL Memory Controller sends a "Pause" frame directly to the 
    UEC Network Interface (NIC) when the memory buffer hits a 
    High Water Mark (HWM) of 80%.
    """
    
    def should_pause(self) -> bool:
        # Strict HWM at 80%
        return self.buffer.occupancy_fraction >= 0.80
    
    def should_resume(self) -> bool:
        return self.buffer.occupancy_fraction < 0.80


class AdaptiveHysteresisAlgorithm(BackpressureAlgorithm):
    """
    Adaptive hysteresis backpressure (THE INVENTION).
    
    Uses two thresholds to prevent oscillation:
    - Pause when buffer exceeds HIGH threshold (90%)
    - Resume when buffer drops below LOW threshold (70%)
    
    This is the patentable innovation that maximizes throughput
    while preventing oscillation and drops.
    """
    
    def __init__(self, buffer: MemoryBuffer, config: IncastConfig):
        super().__init__(buffer, config)
        self.paused = False
    
    def should_pause(self) -> bool:
        if not self.paused and self.buffer.occupancy_fraction >= self.config.hysteresis_high:
            self.paused = True
            self.buffer.state.backpressure_events += 1
            return True
        return self.paused
    
    def should_resume(self) -> bool:
        if self.paused and self.buffer.occupancy_fraction <= self.config.hysteresis_low:
            self.paused = False
            return True
        return not self.paused


# =============================================================================
# TRAFFIC GENERATORS
# =============================================================================

def uniform_traffic_generator(
    env: simpy.Environment,
    buffer: MemoryBuffer,
    backpressure: BackpressureAlgorithm,
    config: IncastConfig,
    rng: np.random.Generator
):
    """
    Generate uniform traffic with exponential inter-arrival times.
    
    This simulates steady-state network load.
    """
    packet_id = 0
    
    while env.now < config.simulation_duration_us:
        # Check backpressure
        if backpressure.should_pause():
            # Wait for resume signal (check every 0.1us)
            while not backpressure.should_resume():
                yield env.timeout(0.1)
        
        # Generate packet
        packet = Packet(
            packet_id=packet_id,
            size_bytes=config.packet_size_bytes,
            arrival_time=env.now,
            sender_id=0
        )
        buffer.enqueue(packet)
        packet_id += 1
        
        # Wait for next packet (exponential inter-arrival)
        inter_arrival = rng.exponential(config.packet_inter_arrival_us)
        yield env.timeout(inter_arrival)


def bursty_traffic_generator(
    env: simpy.Environment,
    buffer: MemoryBuffer,
    backpressure: BackpressureAlgorithm,
    config: IncastConfig,
    rng: np.random.Generator
):
    """
    Generate bursty traffic using a Pareto distribution.
    
    This simulates AI inference workloads with periodic bursts.
    """
    packet_id = 0
    
    while env.now < config.simulation_duration_us:
        # Determine if this is a burst period (20% of time)
        is_burst = rng.random() < 0.2
        
        if is_burst:
            # Send a burst of packets rapidly
            burst_size = int(rng.pareto(2.0) * 10) + 5
            for _ in range(burst_size):
                if backpressure.should_pause():
                    while not backpressure.should_resume():
                        yield env.timeout(0.1)
                
                packet = Packet(
                    packet_id=packet_id,
                    size_bytes=config.packet_size_bytes,
                    arrival_time=env.now,
                    sender_id=0
                )
                buffer.enqueue(packet)
                packet_id += 1
                
                # Minimal delay within burst
                yield env.timeout(config.packet_inter_arrival_us / config.burst_factor)
        else:
            # Normal packet
            if not backpressure.should_pause():
                packet = Packet(
                    packet_id=packet_id,
                    size_bytes=config.packet_size_bytes,
                    arrival_time=env.now,
                    sender_id=0
                )
                buffer.enqueue(packet)
                packet_id += 1
            
            # Normal inter-arrival
            yield env.timeout(rng.exponential(config.packet_inter_arrival_us * 2))


def incast_traffic_generator(
    env: simpy.Environment,
    buffer: MemoryBuffer,
    backpressure: BackpressureAlgorithm,
    config: IncastConfig,
    rng: np.random.Generator
):
    """
    Generate incast traffic from multiple synchronized senders.
    
    This simulates the worst-case scenario where many nodes
    simultaneously send to one destination.
    """
    packet_id = 0
    
    # All senders start at slightly offset times
    sender_offsets = rng.uniform(0, 1.0, size=config.n_senders)
    
    while env.now < config.simulation_duration_us:
        # Each sender sends one packet in this round
        for sender_id in range(config.n_senders):
            if backpressure.should_pause():
                while not backpressure.should_resume():
                    yield env.timeout(0.1)
            
            # Slight jitter per sender
            yield env.timeout(sender_offsets[sender_id] * 0.1)
            
            packet = Packet(
                packet_id=packet_id,
                size_bytes=config.packet_size_bytes,
                arrival_time=env.now,
                sender_id=sender_id
            )
            buffer.enqueue(packet)
            packet_id += 1
        
        # Wait for next round
        round_interval = (config.packet_inter_arrival_us * config.n_senders) / 2
        yield env.timeout(round_interval)


def memory_drain_process(
    env: simpy.Environment,
    buffer: MemoryBuffer,
    config: IncastConfig
):
    """
    Simulates the memory controller draining packets from the buffer.
    
    Runs continuously, draining packets at the configured rate.
    """
    while True:
        if len(buffer.queue) > 0:
            packet = buffer.dequeue()
            if packet:
                # Simulate drain time
                drain_time = config.packet_drain_time_us
                buffer.state.total_drain_time_us += drain_time
                yield env.timeout(drain_time)
        else:
            # No packets to drain, wait briefly
            yield env.timeout(0.1)


# =============================================================================
# SIMULATION RUNNER
# =============================================================================

def run_incast_simulation(
    config: IncastConfig,
    algorithm_type: str,
    seed: int
) -> Dict[str, float]:
    """
    Run a single incast simulation with the specified algorithm.
    
    Args:
        config: Simulation configuration
        algorithm_type: 'no_control', 'static', or 'hysteresis'
        seed: Random seed for reproducibility
        
    Returns:
        Dictionary of metric name -> value
    """
    # Initialize random number generator
    rng = np.random.default_rng(seed)
    
    # Create SimPy environment
    env = simpy.Environment()
    
    # Create buffer
    buffer = MemoryBuffer(env, config)
    
    # Create backpressure algorithm
    if algorithm_type == 'no_control':
        backpressure = NoControlAlgorithm(buffer, config)
    elif algorithm_type == 'static':
        backpressure = StaticThresholdAlgorithm(buffer, config)
    elif algorithm_type == 'hysteresis':
        backpressure = AdaptiveHysteresisAlgorithm(buffer, config)
    else:
        raise ValueError(f"Unknown algorithm type: {algorithm_type}")
    
    # Select traffic generator
    if config.traffic_pattern == 'uniform':
        generator = uniform_traffic_generator
    elif config.traffic_pattern == 'bursty':
        generator = bursty_traffic_generator
    elif config.traffic_pattern == 'incast':
        generator = incast_traffic_generator
    else:
        raise ValueError(f"Unknown traffic pattern: {config.traffic_pattern}")
    
    # Start processes
    env.process(generator(env, buffer, backpressure, config, rng))
    env.process(memory_drain_process(env, buffer, config))
    
    # Run simulation
    env.run(until=config.simulation_duration_us)
    
    # Collect metrics
    state = buffer.state
    
    # Calculate utilization
    utilization = state.total_drain_time_us / config.simulation_duration_us
    
    # Calculate queue depth statistics
    if len(state.queue_depth_samples) > 0:
        queue_depths = [d[1] for d in state.queue_depth_samples]
        avg_queue_depth = np.mean(queue_depths)
        max_queue_depth = np.max(queue_depths)
        queue_depth_std = np.std(queue_depths)
        
        # Occupancy as fraction of capacity
        avg_occupancy = avg_queue_depth / config.buffer_capacity_bytes
        max_occupancy = max_queue_depth / config.buffer_capacity_bytes
    else:
        avg_queue_depth = 0.0
        max_queue_depth = 0.0
        queue_depth_std = 0.0
        avg_occupancy = 0.0
        max_occupancy = 0.0
    
    return {
        'drop_rate': state.drop_rate,
        'throughput_fraction': state.throughput_fraction,
        'avg_latency_us': state.avg_latency_us,
        'p99_latency_us': state.p99_latency_us,
        'avg_occupancy': avg_occupancy,
        'max_occupancy': max_occupancy,
        'avg_queue_depth_bytes': avg_queue_depth,
        'queue_depth_std': queue_depth_std,
        'packets_arrived': float(state.packets_arrived),
        'packets_dropped': float(state.packets_dropped),
        'packets_drained': float(state.packets_drained),
        'backpressure_events': float(state.backpressure_events),
        'utilization': utilization
    }


# =============================================================================
# STANDALONE EXECUTION FOR TESTING
# =============================================================================

if __name__ == '__main__':
    # Quick test run
    config = IncastConfig(
        traffic_pattern='incast',
        simulation_duration_us=100.0,
        n_senders=50
    )
    
    print("Testing Incast Simulation...")
    print("-" * 50)
    
    for algo in ['no_control', 'static', 'hysteresis']:
        results = run_incast_simulation(config, algo, seed=42)
        print(f"\n{algo.upper()}:")
        print(f"  Drop Rate: {results['drop_rate']:.4f}")
        print(f"  Throughput: {results['throughput_fraction']:.4f}")
        print(f"  Avg Latency: {results['avg_latency_us']:.2f} μs")
        print(f"  Avg Occupancy: {results['avg_occupancy']:.2%}")
        print(f"  Link Utilization: {results['utilization']:.2%}")
    
    print("\n" + "=" * 50)
    print("Simulation test complete!")


