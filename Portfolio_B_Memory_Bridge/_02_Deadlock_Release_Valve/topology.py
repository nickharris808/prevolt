"""
Deadlock Topology Model
=======================

This module defines the network topology for deadlock simulation.
We use a 3-switch ring topology that can create circular dependencies:

    Switch A → Switch B → Switch C → Switch A

When all buffers are full and each switch is waiting on the next,
a deadlock occurs and no packets can move.

Author: Portfolio B Research Team
License: Proprietary - Patent Pending
"""

import networkx as nx
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum


# =============================================================================
# TOPOLOGY CONFIGURATION
# =============================================================================

@dataclass
class SwitchConfig:
    """
    Configuration for a single switch in the network.
    
    Attributes:
        name: Human-readable switch identifier
        buffer_capacity_packets: Maximum packets in output buffer
        link_rate_gbps: Link speed in Gbps
        processing_delay_us: Per-packet processing delay
    """
    name: str
    buffer_capacity_packets: int = 100
    link_rate_gbps: float = 100.0
    processing_delay_us: float = 0.1


@dataclass
class LinkConfig:
    """
    Configuration for a link between switches.
    
    Attributes:
        source: Source switch name
        destination: Destination switch name
        propagation_delay_us: Link propagation delay
        bandwidth_gbps: Link bandwidth
    """
    source: str
    destination: str
    propagation_delay_us: float = 1.0
    bandwidth_gbps: float = 100.0


class TopologyType(Enum):
    """Supported topology types."""
    RING_3 = 'ring_3'      # 3-switch ring (minimum for deadlock)
    RING_4 = 'ring_4'      # 4-switch ring
    RING_8 = 'ring_8'      # 8-switch ring
    CUSTOM = 'custom'      # User-defined


# =============================================================================
# TOPOLOGY BUILDER
# =============================================================================

class RingTopology:
    """
    Builds and manages a ring topology for deadlock simulation.
    
    A ring topology is the minimal structure that can exhibit
    circular dependency deadlock in lossless networks.
    """
    
    def __init__(
        self,
        n_switches: int = 3,
        buffer_capacity: int = 100,
        link_rate_gbps: float = 100.0
    ):
        """
        Initialize a ring topology.
        
        Args:
            n_switches: Number of switches in the ring
            buffer_capacity: Buffer capacity per switch (packets)
            link_rate_gbps: Link speed
        """
        self.n_switches = n_switches
        self.buffer_capacity = buffer_capacity
        self.link_rate_gbps = link_rate_gbps
        
        # Build NetworkX graph
        self.graph = nx.DiGraph()
        self.switches: Dict[str, SwitchConfig] = {}
        self.links: List[LinkConfig] = []
        
        self._build_topology()
    
    def _build_topology(self):
        """Construct the ring topology."""
        # Create switches
        for i in range(self.n_switches):
            name = f"Switch_{chr(65 + i)}"  # A, B, C, ...
            config = SwitchConfig(
                name=name,
                buffer_capacity_packets=self.buffer_capacity,
                link_rate_gbps=self.link_rate_gbps
            )
            self.switches[name] = config
            self.graph.add_node(name, config=config)
        
        # Create ring links (A→B→C→A)
        switch_names = list(self.switches.keys())
        for i in range(self.n_switches):
            source = switch_names[i]
            destination = switch_names[(i + 1) % self.n_switches]
            
            link = LinkConfig(
                source=source,
                destination=destination,
                propagation_delay_us=1.0,
                bandwidth_gbps=self.link_rate_gbps
            )
            self.links.append(link)
            self.graph.add_edge(source, destination, config=link)
    
    def get_switch_names(self) -> List[str]:
        """Return ordered list of switch names."""
        return list(self.switches.keys())
    
    def get_next_hop(self, switch_name: str) -> str:
        """Get the next switch in the ring."""
        successors = list(self.graph.successors(switch_name))
        if successors:
            return successors[0]
        raise ValueError(f"No successor for {switch_name}")
    
    def get_prev_hop(self, switch_name: str) -> str:
        """Get the previous switch in the ring."""
        predecessors = list(self.graph.predecessors(switch_name))
        if predecessors:
            return predecessors[0]
        raise ValueError(f"No predecessor for {switch_name}")
    
    def is_ring(self) -> bool:
        """Verify the topology is a valid ring."""
        if not nx.is_strongly_connected(self.graph):
            return False
        
        # Each node should have exactly one in-edge and one out-edge
        for node in self.graph.nodes():
            if self.graph.in_degree(node) != 1:
                return False
            if self.graph.out_degree(node) != 1:
                return False
        
        return True
    
    def visualize(self, output_path: Optional[str] = None):
        """
        Generate a visualization of the topology.
        
        Args:
            output_path: Optional path to save the figure
        """
        import matplotlib.pyplot as plt
        
        fig, ax = plt.subplots(figsize=(8, 8))
        
        # Circular layout for ring
        pos = nx.circular_layout(self.graph)
        
        # Draw nodes
        nx.draw_networkx_nodes(
            self.graph, pos, ax=ax,
            node_color='lightblue',
            node_size=3000,
            edgecolors='black',
            linewidths=2
        )
        
        # Draw edges with arrows
        nx.draw_networkx_edges(
            self.graph, pos, ax=ax,
            edge_color='gray',
            arrows=True,
            arrowsize=20,
            arrowstyle='-|>',
            connectionstyle='arc3,rad=0.1',
            width=2
        )
        
        # Draw labels
        nx.draw_networkx_labels(
            self.graph, pos, ax=ax,
            font_size=12,
            font_weight='bold'
        )
        
        ax.set_title(f'{self.n_switches}-Switch Ring Topology')
        ax.axis('off')
        
        if output_path:
            fig.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"Saved topology visualization to {output_path}")
        
        return fig


# =============================================================================
# DEADLOCK DETECTION UTILITIES
# =============================================================================

def detect_circular_dependency(
    buffer_states: Dict[str, int],
    topology: RingTopology
) -> bool:
    """
    Detect if a circular dependency (deadlock) exists.
    
    A deadlock occurs when:
    1. All buffers are full (or above threshold)
    2. Each switch is waiting to send to the next
    3. No switch can make progress
    
    Args:
        buffer_states: Dict mapping switch name to current buffer fill
        topology: The ring topology
        
    Returns:
        True if deadlock detected
    """
    # All buffers must be at or near capacity
    threshold = 0.9 * topology.buffer_capacity
    
    for switch_name, fill in buffer_states.items():
        if fill < threshold:
            return False  # This switch has room, no deadlock
    
    return True


def find_deadlock_cycle(
    wait_for_graph: nx.DiGraph
) -> Optional[List[str]]:
    """
    Find a cycle in the wait-for graph.
    
    In lossless networks, switches "wait" for downstream buffers
    to drain before they can send. A cycle means deadlock.
    
    Args:
        wait_for_graph: DiGraph where edge A→B means A waits for B
        
    Returns:
        List of nodes in the cycle, or None if no cycle
    """
    try:
        cycle = nx.find_cycle(wait_for_graph)
        return [edge[0] for edge in cycle]
    except nx.NetworkXNoCycle:
        return None


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == '__main__':
    print("Testing Ring Topology...")
    
    # Create 3-switch ring
    topo = RingTopology(n_switches=3, buffer_capacity=100)
    
    print(f"Switches: {topo.get_switch_names()}")
    print(f"Is valid ring: {topo.is_ring()}")
    
    for switch in topo.get_switch_names():
        next_hop = topo.get_next_hop(switch)
        prev_hop = topo.get_prev_hop(switch)
        print(f"  {switch}: prev={prev_hop}, next={next_hop}")
    
    print("\nTopology test complete!")
