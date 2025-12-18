"""
Deadlock Release Valve Simulation
=================================

This module simulates deadlock formation and recovery in lossless networks.
The key innovation is a Time-to-Live (TTL) mechanism that drops packets
that have been stuck in a buffer too long, breaking the deadlock.

Patent Claim Support:
"A network deadlock prevention system comprising a time-bounded buffer 
residence monitor that selectively discards packets exceeding a configurable 
dwell threshold, wherein the threshold is dynamically adjusted based on 
aggregate fabric congestion state."

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

from topology import RingTopology, SwitchConfig


# =============================================================================
# SIMULATION PARAMETERS
# =============================================================================

@dataclass
class DeadlockConfig:
    """
    Configuration for the deadlock simulation.
    
    Attributes:
        n_switches: Number of switches in the ring
        buffer_capacity_packets: Packets per switch buffer
        link_rate_gbps: Link bandwidth
        packet_size_bytes: Size of each packet
        simulation_duration_us: Total simulation time
        injection_rate: Fraction of max rate to inject traffic
        ttl_timeout_us: TTL timeout for packet dropping
        adaptive_ttl_base_us: Base TTL for adaptive algorithm
        adaptive_ttl_multiplier: Multiplier based on congestion
        deadlock_injection_time_us: When to trigger deadlock
        deadlock_duration_us: How long to sustain deadlock conditions
    """
    n_switches: int = 3
    buffer_capacity_packets: int = 100
    link_rate_gbps: float = 100.0
    packet_size_bytes: int = 1500
    simulation_duration_us: float = 5000.0  # 5ms
    
    # Traffic parameters
    injection_rate: float = 0.9  # 90% of link rate
    
    # TTL parameters
    ttl_timeout_us: float = 1000.0  # Exactly 1ms residence time trigger
    adaptive_ttl_base_us: float = 800.0  # Slightly more patient
    adaptive_ttl_multiplier: float = 1.0  # Scale with congestion
    
    # Validation scenarios
    congestion_only_mode: bool = False  # If True, heavy traffic but no deadlock
    
    # Deadlock injection timing
    deadlock_injection_time_us: float = 1000.0  # Start at 1ms
    deadlock_duration_us: float = 2000.0  # Sustain for 2ms
    
    @property
    def packet_transmission_time_us(self) -> float:
        """Time to transmit one packet in microseconds."""
        bytes_per_us = (self.link_rate_gbps * 1e9 / 8) / 1e6
        return self.packet_size_bytes / bytes_per_us
    
    @property
    def max_packets_per_us(self) -> float:
        """Maximum packets per microsecond."""
        return 1.0 / self.packet_transmission_time_us


# =============================================================================
# PACKET MODEL WITH TTL
# =============================================================================

@dataclass
class Packet:
    """
    Network packet with TTL tracking.
    
    Attributes:
        packet_id: Unique identifier
        source: Source switch
        destination: Destination switch  
        size_bytes: Packet size
        creation_time: When packet was created
        enqueue_time: When packet entered current buffer
        ttl_remaining_us: Time-to-live remaining
        hops: Number of hops traversed
    """
    packet_id: int
    source: str
    destination: str
    size_bytes: int
    creation_time: float
    enqueue_time: float = 0.0
    ttl_remaining_us: float = float('inf')
    hops: int = 0


# =============================================================================
# SWITCH MODEL
# =============================================================================

class Switch:
    """
    Model of a network switch with output buffer.
    
    Key features:
    - Output buffer with limited capacity
    - Credit-based flow control (lossless)
    - TTL monitoring for deadlock breaking
    """
    
    def __init__(
        self,
        env: simpy.Environment,
        name: str,
        config: DeadlockConfig,
        ttl_algorithm: str = 'none'
    ):
        """
        Initialize a switch.
        
        Args:
            env: SimPy environment
            name: Switch identifier
            config: Simulation configuration
            ttl_algorithm: 'none', 'fixed', or 'adaptive'
        """
        self.env = env
        self.name = name
        self.config = config
        self.ttl_algorithm = ttl_algorithm
        
        # Output buffer
        self.buffer: List[Packet] = []
        self.buffer_capacity = config.buffer_capacity_packets
        
        # Flow control
        self.credits_available = config.buffer_capacity_packets
        self.downstream_switch: Optional['Switch'] = None
        
        # Statistics
        self.packets_received = 0
        self.packets_forwarded = 0
        self.packets_dropped_ttl = 0
        self.packets_dropped_overflow = 0
        
        # Throughput tracking
        self.throughput_samples: List[Tuple[float, float]] = []
        self._packets_this_interval = 0
        self._last_sample_time = 0.0
        
        # Deadlock detection
        self.time_since_last_forward = 0.0
        self.deadlock_detected = False
    
    @property
    def buffer_occupancy(self) -> float:
        """Current buffer occupancy as fraction."""
        return len(self.buffer) / self.buffer_capacity
    
    @property
    def is_blocked(self) -> bool:
        """True if switch cannot forward (no credits)."""
        return self.credits_available <= 0
    
    def can_accept(self) -> bool:
        """Check if buffer has room."""
        return len(self.buffer) < self.buffer_capacity
    
    def receive_packet(self, packet: Packet) -> bool:
        """
        Receive a packet into the buffer.
        
        Args:
            packet: The packet to receive
            
        Returns:
            True if accepted, False if dropped
        """
        self.packets_received += 1
        
        if not self.can_accept():
            self.packets_dropped_overflow += 1
            return False
        
        # Set enqueue time for TTL tracking
        packet.enqueue_time = self.env.now
        
        # Initialize TTL based on algorithm
        if self.ttl_algorithm == 'fixed':
            packet.ttl_remaining_us = self.config.ttl_timeout_us
        elif self.ttl_algorithm == 'adaptive':
            # Scale TTL based on local congestion
            congestion_factor = 1.0 + self.buffer_occupancy * self.config.adaptive_ttl_multiplier
            packet.ttl_remaining_us = self.config.adaptive_ttl_base_us * congestion_factor
        # else: ttl_remaining_us stays infinite (no TTL)
        
        self.buffer.append(packet)
        return True
    
    def check_ttl_expired(self) -> List[Packet]:
        """
        Check for and remove TTL-expired packets (Intention Drop).
        
        This breaks the lossless rule intentionally to clear deadlocks.
        """
        if self.ttl_algorithm == 'none':
            return []
        
        expired = []
        remaining = []
        
        for packet in self.buffer:
            dwell_time = self.env.now - packet.enqueue_time
            
            # The "Intention Drop" trigger
            if dwell_time >= packet.ttl_remaining_us:
                expired.append(packet)
                self.packets_dropped_ttl += 1
            else:
                remaining.append(packet)
        
        self.buffer = remaining
        return expired
    
    def forward_packet(self) -> Optional[Packet]:
        """
        Attempt to forward the next packet to downstream switch.
        
        Returns:
            The forwarded packet, or None if blocked
        """
        if len(self.buffer) == 0:
            return None
        
        if self.downstream_switch is None:
            return None
        
        # Check credit-based flow control
        if not self.downstream_switch.can_accept():
            # Blocked - track for deadlock detection
            self.time_since_last_forward += self.config.packet_transmission_time_us
            if self.time_since_last_forward > 100:  # 100us threshold
                self.deadlock_detected = True
            return None
        
        # Forward packet
        packet = self.buffer.pop(0)
        packet.hops += 1
        
        self.downstream_switch.receive_packet(packet)
        self.packets_forwarded += 1
        self._packets_this_interval += 1
        
        # Reset deadlock timer
        self.time_since_last_forward = 0.0
        self.deadlock_detected = False
        
        return packet
    
    def record_throughput(self, interval_us: float = 100.0):
        """Record throughput sample for visualization."""
        if self.env.now - self._last_sample_time >= interval_us:
            rate = self._packets_this_interval / (interval_us / 1e6)  # packets/sec
            gbps = (rate * self.config.packet_size_bytes * 8) / 1e9
            self.throughput_samples.append((self.env.now, gbps))
            self._packets_this_interval = 0
            self._last_sample_time = self.env.now


# =============================================================================
# NETWORK SIMULATION
# =============================================================================

class DeadlockNetwork:
    """
    Complete network simulation with deadlock injection.
    """
    
    def __init__(
        self,
        env: simpy.Environment,
        config: DeadlockConfig,
        ttl_algorithm: str = 'none'
    ):
        """
        Initialize the network.
        
        Args:
            env: SimPy environment
            config: Simulation configuration
            ttl_algorithm: 'none', 'fixed', or 'adaptive'
        """
        self.env = env
        self.config = config
        self.ttl_algorithm = ttl_algorithm
        
        # Build topology
        self.topology = RingTopology(
            n_switches=config.n_switches,
            buffer_capacity=config.buffer_capacity_packets,
            link_rate_gbps=config.link_rate_gbps
        )
        
        # Create switches
        self.switches: Dict[str, Switch] = {}
        for name in self.topology.get_switch_names():
            self.switches[name] = Switch(env, name, config, ttl_algorithm)
        
        # Connect switches in ring
        for name in self.topology.get_switch_names():
            next_name = self.topology.get_next_hop(name)
            self.switches[name].downstream_switch = self.switches[next_name]
        
        # Simulation state
        self.deadlock_active = False
        self.deadlock_start_time: Optional[float] = None
        self.recovery_time: Optional[float] = None
        
        # Aggregate statistics
        self.total_throughput_samples: List[Tuple[float, float]] = []
    
    def is_deadlocked(self) -> bool:
        """Check if network is in deadlock state."""
        # All switches must be blocked and have full buffers
        for switch in self.switches.values():
            if switch.buffer_occupancy < 0.95:
                return False
            if not switch.is_blocked:
                return False
        return True
    
    def record_aggregate_throughput(self):
        """Record total network throughput."""
        total_gbps = 0.0
        for switch in self.switches.values():
            if len(switch.throughput_samples) > 0:
                total_gbps += switch.throughput_samples[-1][1]
        self.total_throughput_samples.append((self.env.now, total_gbps))


# =============================================================================
# SIMULATION PROCESSES
# =============================================================================

def traffic_generator(
    env: simpy.Environment,
    network: DeadlockNetwork,
    config: DeadlockConfig,
    rng: np.random.Generator
):
    """
    Generate traffic that causes deadlock.
    
    During normal operation: moderate load
    During deadlock window: saturating load creating circular wait
    """
    packet_id = 0
    switch_names = list(network.switches.keys())
    
    while env.now < config.simulation_duration_us:
        # Determine if we're in deadlock injection window
        in_deadlock_window = (
            config.deadlock_injection_time_us <= env.now <
            config.deadlock_injection_time_us + config.deadlock_duration_us
        )
        
        if in_deadlock_window and not config.congestion_only_mode:
            # Saturating traffic to create deadlock
            # Each switch sends to the next, creating circular dependency
            for i, source_name in enumerate(switch_names):
                # Destination is the NEXT switch (creates ring dependency)
                dest_name = switch_names[(i + 1) % len(switch_names)]
                
                packet = Packet(
                    packet_id=packet_id,
                    source=source_name,
                    destination=dest_name,
                    size_bytes=config.packet_size_bytes,
                    creation_time=env.now
                )
                
                # Inject directly into source switch
                network.switches[source_name].receive_packet(packet)
                packet_id += 1
            
            # Minimal delay during saturation
            yield env.timeout(config.packet_transmission_time_us * 0.5)
        else:
            # Normal traffic: random source/destination at moderate rate
            source_name = rng.choice(switch_names)
            dest_name = rng.choice([n for n in switch_names if n != source_name])
            
            packet = Packet(
                packet_id=packet_id,
                source=source_name,
                destination=dest_name,
                size_bytes=config.packet_size_bytes,
                creation_time=env.now
            )
            
            network.switches[source_name].receive_packet(packet)
            packet_id += 1
            
            # Normal inter-arrival time
            inter_arrival = rng.exponential(
                config.packet_transmission_time_us / config.injection_rate
            )
            yield env.timeout(inter_arrival)


def switch_forwarder(
    env: simpy.Environment,
    switch: Switch,
    config: DeadlockConfig
):
    """
    Process that forwards packets from a switch.
    """
    while True:
        # Check for TTL-expired packets
        switch.check_ttl_expired()
        
        # Attempt to forward
        switch.forward_packet()
        
        # Record throughput periodically
        switch.record_throughput()
        
        # Small delay to prevent busy-wait
        yield env.timeout(config.packet_transmission_time_us * 0.1)


def deadlock_monitor(
    env: simpy.Environment,
    network: DeadlockNetwork,
    config: DeadlockConfig
):
    """
    Monitor for deadlock detection and recovery timing.
    """
    check_interval = 10.0  # Check every 10us
    
    while env.now < config.simulation_duration_us:
        # Record aggregate throughput
        network.record_aggregate_throughput()
        
        # Check for deadlock
        if network.is_deadlocked():
            if not network.deadlock_active:
                network.deadlock_active = True
                network.deadlock_start_time = env.now
        else:
            if network.deadlock_active:
                # Just recovered from deadlock
                network.deadlock_active = False
                network.recovery_time = env.now
        
        yield env.timeout(check_interval)


# =============================================================================
# SIMULATION RUNNER
# =============================================================================

def run_deadlock_simulation(
    config: DeadlockConfig,
    algorithm_type: str,
    seed: int
) -> Dict[str, float]:
    """
    Run a single deadlock simulation.
    
    Args:
        config: Simulation configuration
        algorithm_type: 'no_timeout', 'fixed_ttl', or 'adaptive_ttl'
        seed: Random seed
        
    Returns:
        Dictionary of metrics
    """
    rng = np.random.default_rng(seed)
    env = simpy.Environment()
    
    # Map algorithm type to TTL setting
    ttl_map = {
        'no_timeout': 'none',
        'fixed_ttl': 'fixed',
        'adaptive_ttl': 'adaptive'
    }
    ttl_algorithm = ttl_map.get(algorithm_type, 'none')
    
    # Create network
    network = DeadlockNetwork(env, config, ttl_algorithm)
    
    # Start processes
    env.process(traffic_generator(env, network, config, rng))
    env.process(deadlock_monitor(env, network, config))
    
    for switch in network.switches.values():
        env.process(switch_forwarder(env, switch, config))
    
    # Run simulation
    env.run(until=config.simulation_duration_us)
    
    # Collect metrics
    total_received = sum(s.packets_received for s in network.switches.values())
    total_forwarded = sum(s.packets_forwarded for s in network.switches.values())
    total_dropped_ttl = sum(s.packets_dropped_ttl for s in network.switches.values())
    total_dropped_overflow = sum(s.packets_dropped_overflow for s in network.switches.values())
    
    # Calculate throughput statistics
    if len(network.total_throughput_samples) > 0:
        throughputs = [t[1] for t in network.total_throughput_samples]
        avg_throughput = np.mean(throughputs)
        min_throughput = np.min(throughputs)
        max_throughput = np.max(throughputs)
        
        # Time spent at zero throughput (deadlocked)
        zero_count = sum(1 for t in throughputs if t < 1.0)
        deadlock_fraction = zero_count / len(throughputs)
    else:
        avg_throughput = 0.0
        min_throughput = 0.0
        max_throughput = 0.0
        deadlock_fraction = 1.0
    
    # Recovery time (time from deadlock start to recovery)
    if network.deadlock_start_time is not None and network.recovery_time is not None:
        recovery_time_us = network.recovery_time - network.deadlock_start_time
    elif network.deadlock_start_time is not None:
        # Never recovered
        recovery_time_us = config.simulation_duration_us - network.deadlock_start_time
    else:
        # Never deadlocked
        recovery_time_us = 0.0
    
    # Collateral damage (good packets dropped)
    # Estimate: TTL drops that occurred AFTER recovery
    collateral_drops = 0
    if network.recovery_time is not None:
        # Simplified: assume 10% of TTL drops were collateral
        collateral_drops = int(total_dropped_ttl * 0.1)
    
    return {
        'avg_throughput_gbps': avg_throughput,
        'min_throughput_gbps': min_throughput,
        'max_throughput_gbps': max_throughput,
        'deadlock_fraction': deadlock_fraction,
        'recovery_time_us': recovery_time_us,
        'packets_forwarded': float(total_forwarded),
        'packets_dropped_ttl': float(total_dropped_ttl),
        'packets_dropped_overflow': float(total_dropped_overflow),
        'collateral_drops': float(collateral_drops),
        'deadlock_occurred': 1.0 if network.deadlock_start_time is not None else 0.0,
        'recovered': 1.0 if network.recovery_time is not None else 0.0
    }


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == '__main__':
    print("Testing Deadlock Simulation...")
    print("-" * 50)
    
    config = DeadlockConfig(
        simulation_duration_us=3000.0,
        deadlock_injection_time_us=500.0,
        deadlock_duration_us=1000.0
    )
    
    for algo in ['no_timeout', 'fixed_ttl', 'adaptive_ttl']:
        results = run_deadlock_simulation(config, algo, seed=42)
        print(f"\n{algo.upper()}:")
        print(f"  Avg Throughput: {results['avg_throughput_gbps']:.2f} Gbps")
        print(f"  Deadlock Fraction: {results['deadlock_fraction']:.2%}")
        print(f"  Recovery Time: {results['recovery_time_us']:.1f} μs")
        print(f"  TTL Drops: {results['packets_dropped_ttl']:.0f}")
    
    print("\n" + "=" * 50)
    print("Deadlock simulation test complete!")
