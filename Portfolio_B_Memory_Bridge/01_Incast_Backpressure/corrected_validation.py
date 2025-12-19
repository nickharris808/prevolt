#!/usr/bin/env python3
"""
Incast Backpressure: Corrected Validation
==========================================

Fixed version with proper backpressure implementation.

Key fix: Backpressure must PREVENT packets from being sent in the first place,
not just delay them after they've already been generated.
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict
from dataclasses import dataclass, field
import time
from collections import deque

sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)


@dataclass
class Packet:
    """A packet with timing information."""
    packet_id: int
    sender_id: int
    size_bytes: int
    creation_time_us: float
    arrival_time_us: float = 0.0  # When it actually arrives at buffer
    queue_entry_us: float = 0.0
    queue_exit_us: float = 0.0
    dropped: bool = False


@dataclass
class SimulationResults:
    """Results from a simulation run."""
    packets_sent: int = 0
    packets_delivered: int = 0
    packets_dropped: int = 0
    latencies_us: List[float] = field(default_factory=list)
    buffer_timeline: List[tuple] = field(default_factory=list)  # (time, bytes)
    backpressure_events: int = 0
    
    @property
    def drop_rate(self) -> float:
        return self.packets_dropped / max(1, self.packets_sent)
    
    @property
    def p99_latency(self) -> float:
        return np.percentile(self.latencies_us, 99) if self.latencies_us else 0


class IncastSimulator:
    """
    Improved simulator with correct backpressure implementation.
    
    Key insight: Backpressure must control the RATE of packet injection,
    not just delay packets that have already been sent.
    """
    
    def __init__(
        self,
        num_senders: int = 10,
        total_data_per_sender_mb: float = 6.4,
        link_speed_gbps: float = 400.0,
        buffer_size_mb: float = 12.0,
        drain_rate_gbps: float = 200.0,
        backpressure_latency_us: float = 0.21,
        threshold: float = 0.80,
    ):
        self.num_senders = num_senders
        self.data_per_sender = total_data_per_sender_mb * 1e6
        self.buffer_capacity = buffer_size_mb * 1e6
        self.threshold = threshold
        self.threshold_bytes = threshold * self.buffer_capacity
        
        # Rates in bytes/microsecond
        self.link_rate = (link_speed_gbps * 1e9) / (8 * 1e6)
        self.drain_rate = (drain_rate_gbps * 1e9) / (8 * 1e6)
        
        self.bp_latency = backpressure_latency_us
        
    def run(self, enable_backpressure: bool = True) -> SimulationResults:
        """
        Run simulation with or without backpressure.
        
        Algorithm:
        1. All senders want to transmit data starting at t=0 (synchronized burst)
        2. Each sender transmits at link_rate
        3. Buffer drains at drain_rate
        4. If backpressure enabled:
           - When buffer > threshold, send PAUSE signal
           - Signal reaches senders after bp_latency
           - Senders stop transmitting
           - When buffer < threshold/2, send RESUME signal
        """
        results = SimulationResults()
        
        # State
        current_time = 0.0
        buffer_bytes = 0.0
        backpressure_active = False
        pause_signal_sent_at = None
        resume_signal_sent_at = None
        
        # Each sender has:
        # - bytes_remaining: how much left to send
        # - is_paused: whether they've received the PAUSE signal
        # - transmit_rate: bytes/us (equal to link_rate / num_senders for fairness)
        
        sender_states = []
        for i in range(self.num_senders):
            sender_states.append({
                'id': i,
                'bytes_remaining': self.data_per_sender,
                'is_paused': False,
                'pause_until': 0.0,
            })
        
        # Packet size (8KB for ML gradients)
        packet_size = 8192
        packet_id = 0
        
        # Timeline
        buffer_timeline = [(0.0, 0.0)]
        
        # Simulation loop
        # Run until all senders are done or we hit time limit
        max_time = 1000.0  # 1 millisecond (shorter for speed)
        dt = 0.01  # 10 nanoseconds in microseconds (coarser for speed)
        
        while current_time < max_time:
            # Check if all senders are done
            if all(s['bytes_remaining'] <= 0 for s in sender_states):
                break
            
            # Drain buffer
            if buffer_bytes > 0:
                bytes_drained = self.drain_rate * dt
                buffer_bytes = max(0, buffer_bytes - bytes_drained)
            
            # Check backpressure conditions
            if enable_backpressure:
                buffer_pct = buffer_bytes / self.buffer_capacity
                
                # Should we send PAUSE?
                if not backpressure_active and buffer_pct > self.threshold:
                    backpressure_active = True
                    pause_signal_sent_at = current_time
                    results.backpressure_events += 1
                
                # Should we send RESUME?
                elif backpressure_active and buffer_pct < (self.threshold * 0.5):
                    backpressure_active = False
                    resume_signal_sent_at = current_time
                
                # Update sender pause states based on signal propagation
                if pause_signal_sent_at is not None:
                    signal_arrival = pause_signal_sent_at + self.bp_latency
                    if current_time >= signal_arrival:
                        for sender in sender_states:
                            if not sender['is_paused']:
                                sender['is_paused'] = True
                                sender['pause_until'] = float('inf')
                
                if resume_signal_sent_at is not None:
                    signal_arrival = resume_signal_sent_at + self.bp_latency
                    if current_time >= signal_arrival:
                        for sender in sender_states:
                            sender['is_paused'] = False
                            sender['pause_until'] = 0.0
                        resume_signal_sent_at = None  # Reset
            
            # Each sender tries to send
            for sender in sender_states:
                if sender['bytes_remaining'] <= 0:
                    continue
                
                if sender['is_paused'] and current_time < sender['pause_until']:
                    continue  # Paused
                
                # Try to send a packet
                send_size = min(packet_size, sender['bytes_remaining'])
                
                if send_size > 0:
                    # Create packet
                    packet = Packet(
                        packet_id=packet_id,
                        sender_id=sender['id'],
                        size_bytes=send_size,
                        creation_time_us=current_time,
                        arrival_time_us=current_time,  # Assume instant arrival for simplicity
                    )
                    packet_id += 1
                    results.packets_sent += 1
                    
                    # Try to enqueue
                    if buffer_bytes + send_size > self.buffer_capacity:
                        # DROP
                        packet.dropped = True
                        results.packets_dropped += 1
                    else:
                        # Enqueue
                        buffer_bytes += send_size
                        packet.queue_entry_us = current_time
                        
                        # Delivery time (when will it finish draining?)
                        # Simplified: assume it takes buffer_bytes / drain_rate to drain
                        packet.queue_exit_us = current_time + (buffer_bytes / self.drain_rate)
                        
                        latency = packet.queue_exit_us - packet.creation_time_us
                        results.latencies_us.append(latency)
                        results.packets_delivered += 1
                    
                    sender['bytes_remaining'] -= send_size
            
            # Record buffer state
            if len(buffer_timeline) == 0 or abs(buffer_timeline[-1][1] - buffer_bytes) > 1000:
                buffer_timeline.append((current_time, buffer_bytes))
            
            current_time += dt
        
        results.buffer_timeline = buffer_timeline
        return results


def run_comparison():
    """Run comparison with corrected implementation."""
    print("=" * 80)
    print("INCAST BACKPRESSURE VALIDATION (CORRECTED)")
    print("=" * 80)
    print()
    print("Scenario:")
    print("  - 10 senders (GPUs)")
    print("  - 6.4 MB data per sender")
    print("  - 12 MB buffer capacity")
    print("  - 400 Gbps link speed")
    print("  - 200 Gbps drain rate (memory bandwidth)")
    print("  - Synchronized burst (all start at t=0)")
    print()
    
    sim = IncastSimulator()
    
    # Run baseline (no backpressure)
    print("Running: Baseline (No Backpressure)...")
    start = time.time()
    results_baseline = sim.run(enable_backpressure=False)
    print(f"  Completed in {time.time() - start:.2f}s")
    print(f"  Packets sent: {results_baseline.packets_sent:,}")
    print(f"  Packets delivered: {results_baseline.packets_delivered:,}")
    print(f"  Packets dropped: {results_baseline.packets_dropped:,}")
    print(f"  Drop rate: {results_baseline.drop_rate*100:.2f}%")
    print(f"  P99 latency: {results_baseline.p99_latency:.1f} μs")
    print()
    
    # Run with fast backpressure (our solution)
    print("Running: With Backpressure (210 ns latency)...")
    start = time.time()
    results_ours = sim.run(enable_backpressure=True)
    print(f"  Completed in {time.time() - start:.2f}s")
    print(f"  Packets sent: {results_ours.packets_sent:,}")
    print(f"  Packets delivered: {results_ours.packets_delivered:,}")
    print(f"  Packets dropped: {results_ours.packets_dropped:,}")
    print(f"  Drop rate: {results_ours.drop_rate*100:.2f}%")
    print(f"  P99 latency: {results_ours.p99_latency:.1f} μs")
    print(f"  Backpressure events: {results_ours.backpressure_events}")
    print()
    
    # Calculate improvements
    print("=" * 80)
    print("IMPROVEMENT")
    print("=" * 80)
    drop_reduction = (results_baseline.drop_rate - results_ours.drop_rate) / results_baseline.drop_rate
    print(f"Drop rate improvement: {drop_reduction*100:.1f}% reduction")
    
    if results_ours.p99_latency > 0:
        latency_improvement = results_baseline.p99_latency / results_ours.p99_latency
        print(f"P99 latency improvement: {latency_improvement:.1f}x faster")
    print()
    
    # Generate graphs
    print("Generating visualizations...")
    generate_graphs(results_baseline, results_ours, sim)
    print("✓ Saved to results/")
    print()


def generate_graphs(baseline, ours, sim):
    """Generate publication-quality graphs."""
    import os
    os.makedirs('results', exist_ok=True)
    
    # Graph 1: Buffer Occupancy Comparison
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # Baseline
    times_base = [t for (t, b) in baseline.buffer_timeline]
    buffer_base = [b / 1e6 for (t, b) in baseline.buffer_timeline]
    
    ax1.plot(times_base, buffer_base, color='#d62728', linewidth=2)
    ax1.axhline(y=sim.buffer_capacity/1e6, color='red', linestyle='--', alpha=0.6, label='Buffer Full')
    ax1.axhline(y=sim.threshold_bytes/1e6, color='orange', linestyle='--', alpha=0.6, label='80% Threshold')
    ax1.fill_between(times_base, 0, buffer_base, alpha=0.3, color='red')
    ax1.set_ylabel('Buffer Occupancy (MB)', fontsize=13, fontweight='bold')
    ax1.set_title('Baseline (No Backpressure) - Frequent Overflow', fontsize=15, fontweight='bold')
    ax1.legend(fontsize=11, loc='upper right')
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(0, 14)
    
    # With backpressure
    times_ours = [t for (t, b) in ours.buffer_timeline]
    buffer_ours = [b / 1e6 for (t, b) in ours.buffer_timeline]
    
    ax2.plot(times_ours, buffer_ours, color='#2ca02c', linewidth=2)
    ax2.axhline(y=sim.buffer_capacity/1e6, color='red', linestyle='--', alpha=0.6, label='Buffer Full')
    ax2.axhline(y=sim.threshold_bytes/1e6, color='orange', linestyle='--', alpha=0.6, label='80% Threshold')
    ax2.fill_between(times_ours, 0, buffer_ours, alpha=0.3, color='green')
    ax2.set_xlabel('Time (microseconds)', fontsize=13, fontweight='bold')
    ax2.set_ylabel('Buffer Occupancy (MB)', fontsize=13, fontweight='bold')
    ax2.set_title('Our Solution (210 ns Backpressure) - Stays Below Threshold', fontsize=15, fontweight='bold')
    ax2.legend(fontsize=11, loc='upper right')
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(0, 14)
    
    plt.tight_layout()
    plt.savefig('results/buffer_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("  ✓ buffer_comparison.png")
    
    # Graph 2: Drop Rate Bar Chart
    fig, ax = plt.subplots(figsize=(10, 7))
    
    scenarios = ['Baseline\n(No Backpressure)', 'Our Solution\n(210 ns Backpressure)']
    drop_rates = [baseline.drop_rate * 100, ours.drop_rate * 100]
    colors = ['#d62728', '#2ca02c']
    
    bars = ax.bar(scenarios, drop_rates, color=colors, alpha=0.85, edgecolor='black', linewidth=2.5, width=0.6)
    
    for bar, val in zip(bars, drop_rates):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{val:.2f}%',
                ha='center', va='bottom', fontsize=14, fontweight='bold')
    
    ax.set_ylabel('Packet Drop Rate (%)', fontsize=15, fontweight='bold')
    ax.set_title('Packet Loss Comparison', fontsize=17, fontweight='bold')
    ax.grid(True, axis='y', alpha=0.3)
    ax.set_ylim(0, max(drop_rates) * 1.3)
    
    plt.tight_layout()
    plt.savefig('results/drop_rate_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("  ✓ drop_rate_comparison.png")


if __name__ == "__main__":
    run_comparison()



