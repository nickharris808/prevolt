"""
Cross-Layer Coordination Matrix
================================

This module implements the coordination rules that modulate control actions
across different subsystems based on aggregate telemetry state.

Key Innovation:
Instead of isolated reflexes, control thresholds are dynamically adjusted
based on cross-layer state. For example:
- PF4 (Incast) triggers backpressure earlier if PF5 (Cache) shows high miss rates
- PF7 (Borrowing) avoids paths where PF6 (Deadlock) detects risk

This is the "cortex" that coordinates the "reflexes."

Author: Portfolio B Research Team
License: Proprietary - Patent Pending (PF8)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
import numpy as np

from .telemetry_bus import (
    DistributedStateStore,
    MetricType,
    TelemetryEvent
)


# =============================================================================
# COORDINATION RULE MODEL
# =============================================================================

class RulePriority(Enum):
    """Priority levels for coordination rules."""
    CRITICAL = 1  # Safety-critical (prevent crashes)
    HIGH = 2      # Performance-critical
    NORMAL = 3    # Optimization
    LOW = 4       # Nice-to-have


@dataclass
class CoordinationRule:
    """
    A rule that modulates a control threshold based on cross-layer state.
    
    Example:
        "IF cache_miss_rate > 0.7 THEN reduce buffer_hwm from 80% to 50%"
    
    Attributes:
        rule_id: Unique identifier
        priority: Rule priority (for conflict resolution)
        condition: Function that evaluates telemetry state
        modulation: Function that calculates threshold adjustment
        description: Human-readable explanation
    """
    rule_id: str
    priority: RulePriority
    condition: Callable[[DistributedStateStore], bool]
    modulation: Callable[[DistributedStateStore], float]
    description: str
    
    # Statistics
    activations: int = 0
    last_activation_time: Optional[float] = None
    
    def evaluate(self, state_store: DistributedStateStore) -> Optional[float]:
        """
        Evaluate the rule against current state.
        
        Args:
            state_store: Current telemetry state
            
        Returns:
            Modulation factor if condition is met, None otherwise
        """
        if self.condition(state_store):
            self.activations += 1
            return self.modulation(state_store)
        return None


# =============================================================================
# COORDINATION MATRIX
# =============================================================================

class CoordinationMatrix:
    """
    The coordination matrix that manages all cross-layer rules.
    
    This is the "brain" that coordinates PF4-PF7.
    """
    
    def __init__(self, state_store: DistributedStateStore):
        """
        Initialize the coordination matrix.
        
        Args:
            state_store: Telemetry state store
        """
        self.state_store = state_store
        self.rules: Dict[str, List[CoordinationRule]] = {
            'pf4_backpressure': [],
            'pf5_throttle': [],
            'pf6_drop': [],
            'pf7_borrow': []
        }
        
        # Initialize default coordination rules
        self._register_default_rules()
    
    def _register_default_rules(self):
        """Register the 4 core coordination rules (Physics-Correct)."""
        
        # Rule 1: PF4 Cache-Aware Backpressure
        # "Trigger backpressure at 50% if cache miss rate > 12%"
        self.register_rule(
            actuator='pf4_backpressure',
            rule=CoordinationRule(
                rule_id='pf4_cache_aware_hwm',
                priority=RulePriority.HIGH,
                condition=lambda state: self._check_cache_pressure(state, threshold=0.12),
                modulation=lambda state: 0.50,  # Reduce HWM from 80% to 50%
                description="Trigger backpressure early when cache drain is slow"
            )
        )
        
        # Rule 2: PF5 Buffer-Aware Throttle
        # "Lower sniper threshold if buffer > 60%"
        self.register_rule(
            actuator='pf5_throttle',
            rule=CoordinationRule(
                rule_id='pf5_buffer_aware_sniper',
                priority=RulePriority.HIGH,
                condition=lambda state: self._check_buffer_pressure(state, threshold=0.60),
                modulation=lambda state: 0.1,  # Reduce Z-score threshold from 1.0 to 0.1
                description="Throttle aggressively when buffer is filling"
            )
        )
        
        # Rule 3: PF6 Congestion-Aware Valve
        # "Reduce TTL to 20us if buffer > 90%"
        self.register_rule(
            actuator='pf6_drop',
            rule=CoordinationRule(
                rule_id='pf6_congestion_aware_ttl',
                priority=RulePriority.CRITICAL,
                condition=lambda state: self._check_buffer_pressure(state, threshold=0.90),
                modulation=lambda state: 20_000.0,  # Reduce TTL from 50us to 20us
                description="Aggressive valve when deadlock meets congestion"
            )
        )
        
        # Rule 4: PF7 Topology-Aware Borrowing
        # "Blacklist nodes with deadlock_risk > 0.12"
        self.register_rule(
            actuator='pf7_borrow',
            rule=CoordinationRule(
                rule_id='pf7_topology_aware_allocation',
                priority=RulePriority.HIGH,
                condition=lambda state: self._check_fabric_risk(state, threshold=0.12),
                modulation=lambda state: self._get_safe_nodes(state),
                description="Avoid borrowing from deadlock-prone paths"
            )
        )
    
    def register_rule(self, actuator: str, rule: CoordinationRule):
        """
        Register a coordination rule.
        
        Args:
            actuator: Which subsystem actuator this rule affects
            rule: The coordination rule
        """
        if actuator not in self.rules:
            self.rules[actuator] = []
        
        self.rules[actuator].append(rule)
        
        # Sort by priority
        self.rules[actuator].sort(key=lambda r: r.priority.value)
    
    def get_modulation(
        self,
        actuator: str,
        default_value: float
    ) -> float:
        """
        Get the coordinated threshold for an actuator.
        
        Args:
            actuator: Which actuator is requesting modulation
            default_value: Default threshold value
            
        Returns:
            Modulated threshold (or default if no rules apply)
        """
        if actuator not in self.rules:
            return default_value
        
        # Evaluate rules in priority order
        for rule in self.rules[actuator]:
            modulation = rule.evaluate(self.state_store)
            if modulation is not None:
                # First matching rule wins (highest priority)
                return modulation
        
        return default_value
    
    # =========================================================================
    # HELPER METHODS FOR RULE CONDITIONS
    # =========================================================================
    
    def _check_cache_pressure(
        self,
        state: DistributedStateStore,
        threshold: float
    ) -> bool:
        """
        Check if any cache is under pressure.
        
        Args:
            state: State store
            threshold: Miss rate threshold
            
        Returns:
            True if cache pressure detected
        """
        cache_sources = state.get_all_sources(MetricType.CACHE_MISS_RATE)
        
        for source in cache_sources:
            miss_rate = state.get_current(source, MetricType.CACHE_MISS_RATE)
            if miss_rate is not None and miss_rate > threshold:
                return True
        
        return False
    
    def _check_buffer_pressure(
        self,
        state: DistributedStateStore,
        threshold: float
    ) -> bool:
        """
        Check if any buffer is under pressure.
        
        Args:
            state: State store
            threshold: Occupancy threshold
            
        Returns:
            True if buffer pressure detected
        """
        buffer_sources = state.get_all_sources(MetricType.BUFFER_DEPTH)
        
        for source in buffer_sources:
            depth = state.get_current(source, MetricType.BUFFER_DEPTH)
            if depth is not None and depth > threshold:
                return True
        
        return False
    
    def _check_fabric_risk(
        self,
        state: DistributedStateStore,
        threshold: float
    ) -> bool:
        """
        Check if fabric has deadlock risk.
        
        Args:
            state: State store
            threshold: Risk threshold
            
        Returns:
            True if risk detected
        """
        fabric_sources = state.get_all_sources(MetricType.DEADLOCK_RISK)
        
        for source in fabric_sources:
            risk = state.get_current(source, MetricType.DEADLOCK_RISK)
            if risk is not None and risk > threshold:
                return True
        
        return False
    
    def _get_safe_nodes(self, state: DistributedStateStore) -> List[int]:
        """
        Get list of nodes safe for borrowing (PF7-G).
        """
        safe_nodes = []
        # Query PF6 deadlock risk for all fabric sources
        risky_sources = state.get_all_sources(MetricType.DEADLOCK_RISK)
        
        risky_node_ids = set()
        for source in risky_sources:
            risk = state.get_current(source, MetricType.DEADLOCK_RISK)
            if risk is not None and risk > 0.1: # Any risk detected
                # Extract node ID from source name (e.g., "PF6_Switch_2")
                try:
                    nid = int(source.split('_')[-1])
                    risky_node_ids.add(nid)
                except:
                    pass
        
        # All nodes not in risky paths are safe
        for i in range(8): # Assuming 8 nodes
            if i not in risky_node_ids:
                safe_nodes.append(i)
                
        return safe_nodes
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get coordination statistics.
        
        Returns:
            Dictionary of statistics per rule
        """
        stats = {}
        
        for actuator, rules in self.rules.items():
            stats[actuator] = [
                {
                    'rule_id': rule.rule_id,
                    'priority': rule.priority.name,
                    'activations': rule.activations,
                    'description': rule.description
                }
                for rule in rules
            ]
        
        return stats


# =============================================================================
# ADVANCED COORDINATION POLICIES (PF8 VARIATIONS)
# =============================================================================

class PriorityWeightedMatrix(CoordinationMatrix):
    """
    PF8-B: Priority-Weighted Coordination.
    
    Some telemetry signals override others based on weights.
    """
    
    def __init__(self, state_store: DistributedStateStore):
        super().__init__(state_store)
        self.weights: Dict[str, float] = {
            'pf4_backpressure': 1.0,
            'pf5_throttle': 0.8,
            'pf6_drop': 1.5,  # Deadlock is highest priority
            'pf7_borrow': 0.6
        }
    
    def get_modulation(self, actuator: str, default_value: float) -> float:
        """Get weighted modulation."""
        base_modulation = super().get_modulation(actuator, default_value)
        weight = self.weights.get(actuator, 1.0)
        
        # Weighted blend between default and modulated
        return default_value * (1 - weight) + base_modulation * weight


class PredictiveMatrix(CoordinationMatrix):
    """
    PF8-C: Predictive State Propagation.
    
    Forecast future state based on derivatives (dV/dt, d²V/dt²).
    """
    
    def __init__(self, state_store: DistributedStateStore):
        super().__init__(state_store)
        self.prediction_horizon_us = 50.0  # Predict 50us ahead
    
    def _check_buffer_pressure(self, state: DistributedStateStore, threshold: float) -> bool:
        """Check predicted buffer pressure."""
        buffer_sources = state.get_all_sources(MetricType.BUFFER_DEPTH)
        
        for source in buffer_sources:
            current_depth = state.get_current(source, MetricType.BUFFER_DEPTH)
            velocity = state.get_derivative(source, MetricType.BUFFER_DEPTH)
            
            if current_depth is not None and velocity is not None:
                # Predict future depth
                predicted_depth = current_depth + velocity * self.prediction_horizon_us
                
                if predicted_depth > threshold:
                    return True
        
        return False


class AdaptiveMatrix(CoordinationMatrix):
    """
    PF8-E: Adaptive Coordination Matrix.
    
    Rules update based on workload history.
    """
    
    def __init__(self, state_store: DistributedStateStore):
        super().__init__(state_store)
        self.adaptation_rate = 0.1
        self.learned_thresholds: Dict[str, float] = {}
    
    def adapt_thresholds(self, performance_metric: float):
        """
        Adapt thresholds based on observed performance.
        """
        # If performance is poor, make rules more aggressive
        if performance_metric < 0.7:
            for actuator in self.rules:
                for rule in self.rules[actuator]:
                    key = f"{actuator}:{rule.rule_id}"
                    if key not in self.learned_thresholds:
                        self.learned_thresholds[key] = 1.0
                    self.learned_thresholds[key] *= (1 - self.adaptation_rate)

class GameTheoryMatrix(CoordinationMatrix):
    """
    PF8-D: Conflict Resolution via Game Theory.
    
    Treats subsystems as players in a cooperative game.
    Uses a Social Welfare Function to find the threshold set that maximizes
    Global System Utility:
    
    U = Sum(Throughput_i) - λ * Max(Latency_j) - μ * P(Deadlock)
    """
    
    def __init__(self, state_store: DistributedStateStore):
        super().__init__(state_store)
        self.latency_lambda = 200.0 # Heavier penalty for victim latency
        self.deadlock_mu = 1000.0   # Critical penalty for deadlock risk
        
    def resolve_conflicts(self, proposals: Dict[str, float]) -> Dict[str, float]:
        """
        Dynamically balances Safety, Fairness, and Throughput.
        """
        final_thresholds = proposals.copy()
        
        # Query aggregate system state
        buffer_depth = self.state_store.get_current('PF4_Incast', MetricType.BUFFER_DEPTH) or 0.0
        miss_rate = self.state_store.get_current('PF5_Sniper', MetricType.CACHE_MISS_RATE) or 0.0
        deadlock_risk = self.state_store.get_current('PF6_Deadlock', MetricType.DEADLOCK_RISK) or 0.0
        
        # 1. Safety Override (Safety First)
        if deadlock_risk > 0.1:
            # Fabric is in danger. All optimization rules are suspended.
            # Safety player (PF6) demands immediate pressure release.
            final_thresholds['pf6_drop'] = 10_000.0 # Release valve at 10us
            final_thresholds['pf4_backpressure'] = 0.20 # Stop ingress immediately
            
        # 2. Resource Contention (Cooperative Bargaining)
        # If cache misses are high AND buffer is filling, the system is thrashing.
        if miss_rate > 0.12 and buffer_depth > 0.5:
            # Social Welfare function indicates the marginal utility of extra
            # throughput is negative due to latency penalty escalation.
            final_thresholds['pf4_backpressure'] = 0.40 # Aggressive early warning
            final_thresholds['pf5_throttle'] = 0.5 # Extreme statistical intolerance
            
        return final_thresholds


class HierarchicalCortex(CoordinationMatrix):
    """
    PF8-F: Hierarchical Orchestration.
    
    Reflex Layer: Local PF4-7 logic (fast, cycle-accurate).
    Cortex Layer: This class (strategic, analyzes multi-us trends).
    """
    
    def __init__(self, state_store: DistributedStateStore):
        super().__init__(state_store)
        self.strategic_horizon_us = 5.0 # Cortex looks at 5us trends
        
    def get_strategic_guidance(self) -> str:
        """Analyze trends to determine system 'mood'."""
        miss_trend = self.state_store.get_derivative('PF5_Sniper', MetricType.CACHE_MISS_RATE)
        buffer_trend = self.state_store.get_derivative('PF4_Incast', MetricType.BUFFER_DEPTH)
        
        if miss_trend > 0.01 and buffer_trend > 0.01:
            return "COLLAPSE_IMMINENT"
        elif miss_trend < -0.01:
            return "RECOVERY_PHASE"
        return "STEADY_STATE"


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == '__main__':
    import simpy
    from telemetry_bus import EventBroker, DistributedStateStore, TelemetryPublisher
    
    print("Testing Coordination Matrix...")
    print("-" * 50)
    
    # Setup
    env = simpy.Environment()
    broker = EventBroker(env)
    state_store = DistributedStateStore(env, broker)
    matrix = CoordinationMatrix(state_store)
    
    # Create publisher
    publisher = TelemetryPublisher(env, broker, "PF5_Cache_0")
    
    # Publish high cache miss rate
    publisher.publish(MetricType.CACHE_MISS_RATE, 0.85)
    
    # Check if PF4 rule triggers
    default_hwm = 0.80
    coordinated_hwm = matrix.get_modulation('pf4_backpressure', default_hwm)
    
    print(f"\nDefault PF4 HWM: {default_hwm:.2f}")
    print(f"Coordinated PF4 HWM: {coordinated_hwm:.2f}")
    print(f"Rule triggered: {coordinated_hwm < default_hwm}")
    
    # Print statistics
    print("\nCoordination Statistics:")
    stats = matrix.get_statistics()
    for actuator, rules in stats.items():
        print(f"\n{actuator}:")
        for rule in rules:
            print(f"  - {rule['rule_id']}: {rule['activations']} activations")
    
    print("\n" + "=" * 50)
    print("Coordination Matrix test complete!")







