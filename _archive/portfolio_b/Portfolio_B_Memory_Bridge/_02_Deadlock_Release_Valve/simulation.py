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

from shared.physics_engine import Physics
from topology import RingTopology, SwitchConfig

# PF8: Telemetry Bus Integration (Optional)
try:
    from _08_Grand_Unified_Cortex import (
        TelemetryPublisher,
        MetricType
    )
    PF8_AVAILABLE = True
except ImportError:
    PF8_AVAILABLE = False
    TelemetryPublisher = None
    MetricType = None


# =============================================================================
# SIMULATION PARAMETERS
# =============================================================================

@dataclass
class DeadlockConfig:
    """
    Configuration for the deadlock simulation (Physics-Correct).
    """
    n_switches: int = 3
    buffer_capacity_packets: int = 100
    link_rate_gbps: float = 100.0
    packet_size_bytes: int = 1500
    simulation_duration_ns: float = 500_000.0  # 500us
    
    # Traffic parameters
    injection_rate: float = 0.9  # 90% of link rate
    
    # TTL parameters (Physics-Correct for fabric residence)
    ttl_timeout_ns: float = 50_000.0  # 50us residence time trigger
    adaptive_ttl_base_ns: float = 25_000.0  
    adaptive_ttl_multiplier: float = 2.0  
    
    # Validation scenarios
    congestion_only_mode: bool = False  # If True, heavy traffic but no deadlock
    virtual_lanes_enabled: bool = False # PF6-D support
    coordination_mode: bool = False    # PF6-C support
    
    # Deadlock injection timing (ns)
    deadlock_injection_time_ns: float = 100_000.0  # Start at 100us
    deadlock_duration_ns: float = 200_000.0  # Sustain for 200us
    
    @property
    def packet_transmission_time_ns(self) -> float:
        """Time to transmit one packet in nanoseconds."""
        return Physics.bytes_to_ns(self.packet_size_bytes, self.link_rate_gbps)
    
    @property
    def max_packets_per_ns(self) -> float:
        """Maximum packets per nanosecond."""
        return 1.0 / self.packet_transmission_time_ns


# =============================================================================
# PACKET MODEL WITH TTL
# =============================================================================

@dataclass
class Packet:
    """
    Network packet with TTL tracking.
    """
    packet_id: int
    source: str
    destination: str
    size_bytes: int
    creation_time: float
    enqueue_time: float = 0.0
    ttl_remaining_ns: float = float('inf')
    hops: int = 0


# =============================================================================
# SWITCH MODEL
# =============================================================================

class Switch:
    """
    Model of a network switch with output buffer.
    """
    
    def __init__(
        self,
        env: simpy.Environment,
        name: str,
        config: DeadlockConfig,
        ttl_algorithm: str = 'none',
        telemetry_publisher: Optional['TelemetryPublisher'] = None
    ):
        self.env = env
        self.name = name
        self.config = config
        self.ttl_algorithm = ttl_algorithm
        self.telemetry_publisher = telemetry_publisher
        
        # Output buffer
        self.buffer: List[Packet] = []
        self.buffer_capacity = config.buffer_capacity_packets
        
        # Flow control
        self.credits_available = config.buffer_capacity_packets
        self.downstream_switch: Optional['Switch'] = None
        self.upstream_switch: Optional['Switch'] = None
        
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
        return len(self.buffer) / self.buffer_capacity
    
    @property
    def is_blocked(self) -> bool:
        return self.credits_available <= 0
    
    def can_accept(self) -> bool:
        return len(self.buffer) < self.buffer_capacity
    
    def receive_packet(self, packet: Packet) -> bool:
        self.packets_received += 1
        if not self.can_accept():
            self.packets_dropped_overflow += 1
            return False
        
        packet.enqueue_time = self.env.now
        
        if self.ttl_algorithm == 'fixed':
            packet.ttl_remaining_ns = self.config.ttl_timeout_ns
        elif self.ttl_algorithm == 'adaptive':
            congestion_factor = 1.0 + self.buffer_occupancy * self.config.adaptive_ttl_multiplier
            packet.ttl_remaining_ns = self.config.adaptive_ttl_base_ns * congestion_factor
            
        self.buffer.append(packet)
        return True
    
    def check_ttl_expired(self, coordination_matrix: Optional['CoordinationMatrix'] = None) -> List[Packet]:
        if self.ttl_algorithm == 'none':
            return []
        
        # Get coordinated TTL threshold
        ttl_limit = self.config.ttl_timeout_ns
        if coordination_matrix:
            ttl_limit = coordination_matrix.get_modulation('pf6_drop', ttl_limit)

        if self.config.coordination_mode:
            consensus = True
            if self.downstream_switch and not self.downstream_switch.deadlock_detected:
                consensus = False
            if self.upstream_switch and not self.upstream_switch.deadlock_detected:
                consensus = False
            if not consensus:
                return []

        expired = []
        remaining = []
        for packet in self.buffer:
            dwell_time = self.env.now - packet.enqueue_time
            if dwell_time >= ttl_limit:
                if self.config.virtual_lanes_enabled and packet.hops < 5:
                    packet.enqueue_time = self.env.now
                    packet.ttl_remaining_ns *= 1.5
                    remaining.append(packet)
                else:
                    expired.append(packet)
                    self.packets_dropped_ttl += 1
            else:
                remaining.append(packet)
        
        self.buffer = remaining
        return expired
    
    def forward_packet(self) -> Optional[Packet]:
        if len(self.buffer) == 0:
            return None
        if self.downstream_switch is None:
            return None
        
        if not self.downstream_switch.can_accept():
            self.time_since_last_forward += self.config.packet_transmission_time_ns
            if self.time_since_last_forward > 100:
                self.deadlock_detected = True
            return None
        
        packet = self.buffer.pop(0)
        packet.hops += 1
        self.downstream_switch.receive_packet(packet)
        self.packets_forwarded += 1
        self._packets_this_interval += 1
        self.time_since_last_forward = 0.0
        self.deadlock_detected = False
        return packet
    
    def record_throughput(self, interval_ns: float = 100.0):
        if self.env.now - self._last_sample_time >= interval_ns:
            rate = self._packets_this_interval / (interval_ns / 1e9)
            gbps = (rate * self.config.packet_size_bytes * 8) / 1e9
            self.throughput_samples.append((self.env.now, gbps))
            self._packets_this_interval = 0
            self._last_sample_time = self.env.now
            
            # PF8: Publish deadlock risk
            if self.telemetry_publisher and PF8_AVAILABLE:
                risk = 1.0 if self.deadlock_detected else 0.0
                self.telemetry_publisher.publish(
                    MetricType.DEADLOCK_RISK,
                    risk
                )


# =============================================================================
# NETWORK MODEL
# =============================================================================

class DeadlockNetwork:
    def __init__(self, env, config, ttl_algorithm):
        self.env = env
        self.config = config
        self.topology = RingTopology(config.n_switches, config.buffer_capacity_packets, config.link_rate_gbps)
        self.switches = {}
        for name in self.topology.get_switch_names():
            self.switches[name] = Switch(env, name, config, ttl_algorithm)
        
        for name in self.topology.get_switch_names():
            self.switches[name].downstream_switch = self.switches[self.topology.get_next_hop(name)]
            self.switches[name].upstream_switch = self.switches[self.topology.get_prev_hop(name)]

        self.deadlock_active = False
        self.deadlock_start_time = None
        self.recovery_time = None
        self.total_throughput_samples = []
    
    def is_deadlocked(self) -> bool:
        for switch in self.switches.values():
            if switch.buffer_occupancy < 0.95 or not switch.is_blocked:
                return False
        return True
    
    def record_aggregate_throughput(self):
        total_gbps = sum(s.throughput_samples[-1][1] for s in self.switches.values() if s.throughput_samples)
        self.total_throughput_samples.append((self.env.now, total_gbps))


# =============================================================================
# PROCESSES & RUNNER
# =============================================================================

def traffic_generator(env, network, config, rng):
    packet_id = 0
    switch_names = list(network.switches.keys())
    while env.now < config.simulation_duration_ns:
        in_deadlock_window = config.deadlock_injection_time_ns <= env.now < (config.deadlock_injection_time_ns + config.deadlock_duration_ns)
        if in_deadlock_window and not config.congestion_only_mode:
            for i, name in enumerate(switch_names):
                dest = switch_names[(i+1)%len(switch_names)]
                p = Packet(packet_id, name, dest, config.packet_size_bytes, env.now)
                network.switches[name].receive_packet(p)
                packet_id += 1
            yield env.timeout(config.packet_transmission_time_ns * 0.5)
        else:
            src = rng.choice(switch_names)
            dest = rng.choice([n for n in switch_names if n != src])
            p = Packet(packet_id, src, dest, config.packet_size_bytes, env.now)
            network.switches[src].receive_packet(p)
            packet_id += 1
            yield env.timeout(rng.exponential(config.packet_transmission_time_ns / config.injection_rate))

def switch_forwarder(env, switch, config, coordination_matrix=None):
    while True:
        switch.check_ttl_expired(coordination_matrix)
        switch.forward_packet()
        switch.record_throughput()
        yield env.timeout(config.packet_transmission_time_ns * 0.1)

def deadlock_monitor(env, network, config):
    while env.now < config.simulation_duration_ns:
        network.record_aggregate_throughput()
        if network.is_deadlocked():
            if not network.deadlock_active:
                network.deadlock_active, network.deadlock_start_time = True, env.now
        elif network.deadlock_active:
            network.deadlock_active, network.recovery_time = False, env.now
        yield env.timeout(10.0)

def run_deadlock_simulation(
    config: DeadlockConfig,
    algorithm_type: str,
    seed: int,
    telemetry_publisher: Optional['TelemetryPublisher'] = None,
    coordination_matrix: Optional['CoordinationMatrix'] = None,
    env: Optional[simpy.Environment] = None
) -> Dict[str, float]:
    rng = np.random.default_rng(seed)
    
    local_sim = False
    if env is None:
        env = simpy.Environment()
        local_sim = True
        
    ttl_map = {'no_timeout': 'none', 'fixed_ttl': 'fixed', 'adaptive_ttl': 'adaptive', 'coordinated': 'fixed', 'shuffling': 'adaptive'}
    ttl_algorithm = ttl_map.get(algorithm_type, 'none')
    if algorithm_type == 'coordinated': config.coordination_mode = True
    if algorithm_type == 'shuffling': config.virtual_lanes_enabled = True
    network = DeadlockNetwork(env, config, ttl_algorithm)
    
    # Pass publisher to switches
    for s in network.switches.values():
        s.telemetry_publisher = telemetry_publisher
        
    env.process(traffic_generator(env, network, config, rng))
    env.process(deadlock_monitor(env, network, config))
    for s in network.switches.values(): env.process(switch_forwarder(env, s, config, coordination_matrix))
    
    if local_sim:
        env.run(until=config.simulation_duration_ns)
        return _collect_deadlock_metrics(config, network)
    else:
        return network

def _collect_deadlock_metrics(config: DeadlockConfig, network: DeadlockNetwork) -> Dict[str, float]:
    total_forwarded = sum(s.packets_forwarded for s in network.switches.values())
    total_dropped_ttl = sum(s.packets_dropped_ttl for s in network.switches.values())
    throughputs = [t[1] for t in network.total_throughput_samples]
    
    if network.deadlock_start_time is not None and network.recovery_time is not None:
        recovery_time_ns = network.recovery_time - network.deadlock_start_time
    elif network.deadlock_start_time is not None:
        recovery_time_ns = config.simulation_duration_ns - network.deadlock_start_time
    else:
        recovery_time_ns = 0.0
        
    return {
        'avg_throughput_gbps': np.mean(throughputs) if throughputs else 0.0,
        'recovery_time_ns': recovery_time_ns,
        'packets_dropped_ttl': float(total_dropped_ttl),
        'deadlock_occurred': 1.0 if network.deadlock_start_time is not None else 0.0
    }

if __name__ == '__main__':
    config = DeadlockConfig()
    for algo in ['no_timeout', 'fixed_ttl', 'adaptive_ttl']:
        res = run_deadlock_simulation(config, algo, 42)
        print(f"{algo.upper()}: recovery={res['recovery_time_ns']:.1f}ns, drops={res['packets_dropped_ttl']}")
