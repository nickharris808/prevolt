"""
Patent Family 8: The Grand Unified Cortex
==========================================

Cross-Layer Telemetry and Coordination Bus for Portfolio B.

This package implements the distributed "brain" that coordinates
PF4 (Incast), PF5 (Sniper), PF6 (Deadlock), and PF7 (Borrowing)
into a unified sovereign architecture.

Key Innovation:
"A distributed telemetry and coordination system for memory-fabric interfaces,
wherein independent subsystems publish operational state to a shared event broker,
and wherein actuators subscribe to cross-layer telemetry to modulate control
thresholds based on aggregate system state."

Author: Portfolio B Research Team
License: Proprietary - Patent Pending (PF8)
"""

from .telemetry_bus import (
    MetricType,
    TelemetryEvent,
    EventBroker,
    DistributedStateStore,
    TelemetryPublisher,
    TimeSeriesWindow
)

from .coordination_matrix import (
    RulePriority,
    CoordinationRule,
    CoordinationMatrix,
    PriorityWeightedMatrix,
    PredictiveMatrix,
    AdaptiveMatrix
)

__all__ = [
    # Telemetry Bus
    'MetricType',
    'TelemetryEvent',
    'EventBroker',
    'DistributedStateStore',
    'TelemetryPublisher',
    'TimeSeriesWindow',
    
    # Coordination Matrix
    'RulePriority',
    'CoordinationRule',
    'CoordinationMatrix',
    'PriorityWeightedMatrix',
    'PredictiveMatrix',
    'AdaptiveMatrix',
]




