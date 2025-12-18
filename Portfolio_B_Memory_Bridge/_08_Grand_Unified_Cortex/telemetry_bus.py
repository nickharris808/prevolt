"""
Distributed Telemetry Bus for Cross-Layer Coordination
=======================================================

This module implements the core telemetry infrastructure for Patent Family 8.
It provides a publish-subscribe event system that allows independent subsystems
(PF4-PF7) to share operational state and coordinate their control actions.

Key Innovation:
"A distributed telemetry and coordination system for memory-fabric interfaces,
wherein independent subsystems publish operational state to a shared event broker,
and wherein actuators subscribe to cross-layer telemetry to modulate control
thresholds based on aggregate system state."

Author: Portfolio B Research Team
License: Proprietary - Patent Pending (PF8)
"""

import simpy
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Set
from collections import deque
from enum import Enum
import time


# =============================================================================
# TELEMETRY EVENT MODEL
# =============================================================================

class MetricType(Enum):
    """Types of telemetry metrics."""
    # PF4: Incast Backpressure metrics
    BUFFER_DEPTH = 'buffer_depth'
    BUFFER_VELOCITY = 'buffer_velocity'  # dV/dt
    BACKPRESSURE_ACTIVE = 'backpressure_active'
    
    # PF5: Cache Sniper metrics
    CACHE_MISS_RATE = 'cache_miss_rate'
    TENANT_THROTTLED = 'tenant_throttled'
    CACHE_PRESSURE = 'cache_pressure'
    
    # PF6: Deadlock Valve metrics
    DEADLOCK_RISK = 'deadlock_risk'
    TTL_DROPS = 'ttl_drops'
    FABRIC_BLOCKED = 'fabric_blocked'
    
    # PF7: Memory Borrowing metrics
    PATH_HEALTH = 'path_health'
    FRAGMENTATION_LEVEL = 'fragmentation_level'
    REMOTE_MEMORY_FRACTION = 'remote_memory_fraction'


@dataclass
class TelemetryEvent:
    """
    A single telemetry event published to the bus.
    
    Attributes:
        timestamp: Simulation time when event was created
        source: Identifier of the publishing subsystem
        metric_type: Type of metric being reported
        value: Metric value (float or bool)
        metadata: Optional additional context
    """
    timestamp: float
    source: str
    metric_type: MetricType
    value: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __repr__(self) -> str:
        return f"TelemetryEvent({self.source}:{self.metric_type.value}={self.value:.3f} @ t={self.timestamp:.1f})"


# =============================================================================
# EVENT BROKER (PUB/SUB CORE)
# =============================================================================

class EventBroker:
    """
    Central publish-subscribe event broker.
    
    Subsystems publish TelemetryEvents to the broker.
    Subscribers receive events matching their filter criteria.
    
    This is the "nervous system" connecting PF4-PF7.
    """
    
    def __init__(self, env: simpy.Environment):
        """
        Initialize the event broker.
        
        Args:
            env: SimPy environment for time synchronization
        """
        self.env = env
        
        # Subscription registry: {metric_type: [callback functions]}
        self.subscriptions: Dict[MetricType, List[Callable]] = {}
        
        # Event log for debugging/analysis
        self.event_log: List[TelemetryEvent] = []
        
        # Statistics
        self.events_published = 0
        self.events_delivered = 0
    
    def subscribe(
        self,
        metric_type: MetricType,
        callback: Callable[[TelemetryEvent], None]
    ):
        """
        Subscribe to a metric type.
        
        Args:
            metric_type: The type of metric to subscribe to
            callback: Function to call when event is published
        """
        if metric_type not in self.subscriptions:
            self.subscriptions[metric_type] = []
        
        self.subscriptions[metric_type].append(callback)
    
    def publish(self, event: TelemetryEvent):
        """
        Publish a telemetry event to all subscribers.
        
        Args:
            event: The event to publish
        """
        self.events_published += 1
        self.event_log.append(event)
        
        # Deliver to all subscribers
        if event.metric_type in self.subscriptions:
            for callback in self.subscriptions[event.metric_type]:
                callback(event)
                self.events_delivered += 1
    
    def get_recent_events(
        self,
        metric_type: Optional[MetricType] = None,
        since: float = 0.0
    ) -> List[TelemetryEvent]:
        """
        Retrieve recent events from the log.
        
        Args:
            metric_type: Filter by metric type (None = all types)
            since: Return events since this timestamp
            
        Returns:
            List of matching events
        """
        events = [e for e in self.event_log if e.timestamp >= since]
        
        if metric_type is not None:
            events = [e for e in events if e.metric_type == metric_type]
        
        return events


# =============================================================================
# DISTRIBUTED STATE STORE
# =============================================================================

@dataclass
class TimeSeriesWindow:
    """
    A time-windowed buffer of metric values.
    
    Maintains a sliding window of recent values for aggregation.
    """
    window_size_us: float = 100.0  # 100us window
    max_samples: int = 1000
    
    values: deque = field(default_factory=deque)
    timestamps: deque = field(default_factory=deque)
    
    def add_sample(self, timestamp: float, value: float):
        """Add a sample to the window."""
        self.values.append(value)
        self.timestamps.append(timestamp)
        
        # Trim to max samples
        if len(self.values) > self.max_samples:
            self.values.popleft()
            self.timestamps.popleft()
    
    def get_current_value(self) -> Optional[float]:
        """Get the most recent value."""
        return self.values[-1] if len(self.values) > 0 else None
    
    def get_average(self, since: Optional[float] = None) -> float:
        """Get average value in window."""
        if len(self.values) == 0:
            return 0.0
        
        if since is None:
            return float(np.mean(list(self.values)))
        
        # Filter by timestamp
        filtered = [v for v, t in zip(self.values, self.timestamps) if t >= since]
        return float(np.mean(filtered)) if len(filtered) > 0 else 0.0
    
    def get_derivative(self) -> float:
        """
        Calculate rate of change (dV/dt).
        
        Returns:
            Rate of change per microsecond
        """
        if len(self.values) < 2:
            return 0.0
        
        # Use last N samples for derivative
        n = min(10, len(self.values))
        recent_values = list(self.values)[-n:]
        recent_times = list(self.timestamps)[-n:]
        
        if len(recent_values) < 2:
            return 0.0
        
        # Linear regression for slope
        dt = recent_times[-1] - recent_times[0]
        if dt == 0:
            return 0.0
        
        dv = recent_values[-1] - recent_values[0]
        return dv / dt


class DistributedStateStore:
    """
    Shared state repository for cross-layer coordination.
    
    Each subsystem publishes its state here.
    Actuators query this store to make coordinated decisions.
    
    Think of this as the "shared memory" of the distributed brain.
    """
    
    def __init__(self, env: simpy.Environment, broker: EventBroker):
        """
        Initialize the state store.
        
        Args:
            env: SimPy environment
            broker: Event broker to subscribe to
        """
        self.env = env
        self.broker = broker
        
        # Time-series data for each metric type
        self.timeseries: Dict[str, TimeSeriesWindow] = {}
        
        # Current state snapshot (latest values)
        self.current_state: Dict[str, float] = {}
        
        # Subscribe to ALL metric types
        for metric_type in MetricType:
            self.broker.subscribe(metric_type, self._on_event)
    
    def _on_event(self, event: TelemetryEvent):
        """
        Handle incoming telemetry event.
        
        Args:
            event: The telemetry event
        """
        key = f"{event.source}:{event.metric_type.value}"
        
        # Update current state
        self.current_state[key] = event.value
        
        # Update time series
        if key not in self.timeseries:
            self.timeseries[key] = TimeSeriesWindow()
        
        self.timeseries[key].add_sample(event.timestamp, event.value)
    
    def get_current(self, source: str, metric_type: MetricType) -> Optional[float]:
        """
        Get current value for a metric.
        
        Args:
            source: Source identifier
            metric_type: Metric type
            
        Returns:
            Current value or None if not available
        """
        key = f"{source}:{metric_type.value}"
        return self.current_state.get(key)
    
    def get_average(
        self,
        source: str,
        metric_type: MetricType,
        since: Optional[float] = None
    ) -> float:
        """
        Get time-averaged value for a metric.
        
        Args:
            source: Source identifier
            metric_type: Metric type
            since: Calculate average since this time
            
        Returns:
            Average value
        """
        key = f"{source}:{metric_type.value}"
        if key not in self.timeseries:
            return 0.0
        
        return self.timeseries[key].get_average(since)
    
    def get_derivative(self, source: str, metric_type: MetricType) -> float:
        """
        Get rate of change for a metric.
        
        Args:
            source: Source identifier
            metric_type: Metric type
            
        Returns:
            Rate of change (dV/dt)
        """
        key = f"{source}:{metric_type.value}"
        if key not in self.timeseries:
            return 0.0
        
        return self.timeseries[key].get_derivative()
    
    def get_all_sources(self, metric_type: MetricType) -> List[str]:
        """
        Get all sources publishing a given metric type.
        
        Args:
            metric_type: Metric type to search for
            
        Returns:
            List of source identifiers
        """
        suffix = f":{metric_type.value}"
        return [
            key.replace(suffix, "")
            for key in self.current_state.keys()
            if key.endswith(suffix)
        ]


# =============================================================================
# TELEMETRY PUBLISHER (HELPER CLASS)
# =============================================================================

class TelemetryPublisher:
    """
    Helper class for subsystems to publish telemetry.
    
    Wraps the EventBroker with a simpler interface.
    """
    
    def __init__(
        self,
        env: simpy.Environment,
        broker: EventBroker,
        source: str
    ):
        """
        Initialize publisher.
        
        Args:
            env: SimPy environment
            broker: Event broker to publish to
            source: Identifier for this publisher
        """
        self.env = env
        self.broker = broker
        self.source = source
    
    def publish(self, metric_type: MetricType, value: float, **metadata):
        """
        Publish a telemetry event.
        
        Args:
            metric_type: Type of metric
            value: Metric value
            **metadata: Additional context
        """
        event = TelemetryEvent(
            timestamp=self.env.now,
            source=self.source,
            metric_type=metric_type,
            value=value,
            metadata=metadata
        )
        self.broker.publish(event)


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == '__main__':
    print("Testing Telemetry Bus...")
    print("-" * 50)
    
    # Create environment and broker
    env = simpy.Environment()
    broker = EventBroker(env)
    state_store = DistributedStateStore(env, broker)
    
    # Create publishers
    pf4_publisher = TelemetryPublisher(env, broker, "PF4_Buffer_0")
    pf5_publisher = TelemetryPublisher(env, broker, "PF5_Cache_0")
    
    # Simulate some telemetry
    def simulation_process(env):
        for t in range(100):
            # PF4 publishes buffer depth
            buffer_depth = 0.5 + 0.3 * np.sin(t / 10.0)
            pf4_publisher.publish(MetricType.BUFFER_DEPTH, buffer_depth)
            
            # PF5 publishes cache miss rate
            miss_rate = 0.2 + 0.1 * np.random.random()
            pf5_publisher.publish(MetricType.CACHE_MISS_RATE, miss_rate)
            
            yield env.timeout(1.0)
    
    env.process(simulation_process(env))
    env.run(until=100.0)
    
    # Check results
    print(f"\nEvents Published: {broker.events_published}")
    print(f"Events Delivered: {broker.events_delivered}")
    print(f"\nCurrent Buffer Depth: {state_store.get_current('PF4_Buffer_0', MetricType.BUFFER_DEPTH):.3f}")
    print(f"Avg Cache Miss Rate: {state_store.get_average('PF5_Cache_0', MetricType.CACHE_MISS_RATE):.3f}")
    print(f"Buffer Velocity: {state_store.get_derivative('PF4_Buffer_0', MetricType.BUFFER_DEPTH):.6f}")
    
    print("\n" + "=" * 50)
    print("Telemetry Bus test complete!")
