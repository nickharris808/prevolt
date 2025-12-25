"""
Coordination Logic Verification Script
======================================

This script verifies that the PF8 Telemetry Bus and Coordination Matrix
are actually being applied during unified simulations.

We check:
1. Telemetry events are being published
2. Coordination rules are triggering
3. Thresholds are being modulated correctly

Author: Portfolio B Quality Assurance
"""

import sys
import os
import simpy

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.physics_engine import Physics
from _08_Grand_Unified_Cortex.telemetry_bus import EventBroker, DistributedStateStore, TelemetryPublisher, MetricType
from _08_Grand_Unified_Cortex.coordination_matrix import CoordinationMatrix

def test_telemetry_bus():
    """Test that telemetry bus publishes and delivers events."""
    print("Testing Telemetry Bus...")
    
    env = simpy.Environment()
    broker = EventBroker(env)
    state_store = DistributedStateStore(env, broker)
    
    # Create publisher
    publisher = TelemetryPublisher(env, broker, "TEST_Component")
    
    # Publish some events
    publisher.publish(MetricType.BUFFER_DEPTH, 0.75)
    publisher.publish(MetricType.CACHE_MISS_RATE, 0.12)
    
    # Run for a bit to allow async delivery
    env.run(until=1000.0)
    
    # Check state store
    buffer_depth = state_store.get_current("TEST_Component", MetricType.BUFFER_DEPTH)
    miss_rate = state_store.get_current("TEST_Component", MetricType.CACHE_MISS_RATE)
    
    assert buffer_depth is not None, "Buffer depth not published"
    assert miss_rate is not None, "Miss rate not published"
    assert abs(buffer_depth - 0.75) < 0.01, f"Buffer depth mismatch: {buffer_depth}"
    assert abs(miss_rate - 0.12) < 0.01, f"Miss rate mismatch: {miss_rate}"
    
    print(f"  ✓ Telemetry Bus: {broker.events_published} events published, {broker.events_delivered} delivered")
    return True

def test_coordination_matrix():
    """Test that coordination rules trigger correctly."""
    print("\nTesting Coordination Matrix...")
    
    env = simpy.Environment()
    broker = EventBroker(env)
    state_store = DistributedStateStore(env, broker)
    matrix = CoordinationMatrix(state_store)
    
    # Create publisher
    publisher = TelemetryPublisher(env, broker, "PF5_Cache_0")
    
    # Publish high cache miss rate to trigger Rule 1
    publisher.publish(MetricType.CACHE_MISS_RATE, 0.15)
    
    # Run to allow delivery
    env.run(until=1000.0)
    
    # Check if PF4 backpressure threshold gets modulated
    default_hwm = 0.80
    coordinated_hwm = matrix.get_modulation('pf4_backpressure', default_hwm)
    
    print(f"  Default HWM: {default_hwm}")
    print(f"  Coordinated HWM: {coordinated_hwm}")
    
    # Rule should have triggered (cache miss > 12%)
    assert coordinated_hwm < default_hwm, f"Coordination rule did not trigger: {coordinated_hwm} >= {default_hwm}"
    
    print(f"  ✓ Coordination Matrix: Rule triggered, HWM reduced from {default_hwm} to {coordinated_hwm}")
    
    # Check statistics
    stats = matrix.get_statistics()
    total_activations = sum(
        sum(r['activations'] for r in rules)
        for rules in stats.values()
    )
    
    print(f"  ✓ Total rule activations: {total_activations}")
    return True

def test_integrated_flow():
    """Test full integrated telemetry flow."""
    print("\nTesting Integrated Flow...")
    
    env = simpy.Environment()
    broker = EventBroker(env)
    state_store = DistributedStateStore(env, broker)
    matrix = CoordinationMatrix(state_store)
    
    # Simulate PF4 and PF5 publishing telemetry
    pf4_pub = TelemetryPublisher(env, broker, "PF4_Incast")
    pf5_pub = TelemetryPublisher(env, broker, "PF5_Sniper")
    
    # PF5 publishes high cache miss rate
    pf5_pub.publish(MetricType.CACHE_MISS_RATE, 0.18)
    
    # PF4 publishes buffer depth
    pf4_pub.publish(MetricType.BUFFER_DEPTH, 0.65)
    
    # Run
    env.run(until=1000.0)
    
    # PF4 should now see modulated threshold
    coordinated_hwm = matrix.get_modulation('pf4_backpressure', 0.80)
    
    # PF5 should now see modulated sniper threshold
    coordinated_sniper = matrix.get_modulation('pf5_throttle', 1.0)
    
    print(f"  ✓ PF4 HWM modulated: 0.80 → {coordinated_hwm}")
    print(f"  ✓ PF5 Sniper modulated: 1.0 → {coordinated_sniper}")
    
    # Both should be modulated
    assert coordinated_hwm < 0.80, "PF4 not modulated"
    assert coordinated_sniper < 1.0, "PF5 not modulated"
    
    return True

def main():
    print("="*60)
    print("PF8 COORDINATION LOGIC VERIFICATION")
    print("="*60)
    
    try:
        test_telemetry_bus()
        test_coordination_matrix()
        test_integrated_flow()
        
        print("\n" + "="*60)
        print("VERDICT: ALL COORDINATION LOGIC VERIFIED")
        print("="*60)
        return True
    except AssertionError as e:
        print(f"\n❌ VERIFICATION FAILED: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)










