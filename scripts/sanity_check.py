#!/usr/bin/env python3
"""
Quick sanity check for the NOVA system health and configuration.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from orchestrator.app import monitor, router, SLOT_REGISTRY
    from orchestrator.health import health_payload, collect_slot_selfchecks
    from orchestrator.config import config
    from orchestrator.core import DEFAULT_FALLBACK_MAP

    print("✅ Health Payload:")
    payload = health_payload(SLOT_REGISTRY, monitor, router)
    print(f"Slots monitored: {len(payload.get('slots', {}))}")
    print(f"Router thresholds: {payload.get('router_thresholds', {})}")

    print("\n✅ Fallback Configuration:")
    print(f"Default fallback map: {DEFAULT_FALLBACK_MAP}")
    print(f"Router fallback map: {getattr(router, 'fallback_map', {})}")

    print("\n✅ Slot Self-Checks:")
    self_checks = collect_slot_selfchecks(SLOT_REGISTRY)
    for slot_id, check in self_checks.items():
        status = check.get('self_check', 'unknown')
        print(f"  {slot_id}: {status}")

    print("\n✅ Circuit Breaker Status:")
    cb_metrics = payload.get('circuit_breaker', {})
    trip_count = cb_metrics.get('trip_count', 0)
    print(f"Trip count: {trip_count} {'✅' if trip_count == 0 else '⚠️'}")

    print("\n✅ Configuration:")
    print(f"TRUTH_THRESHOLD: {config.TRUTH_THRESHOLD}")
    print(f"ROUTER_LATENCY_MS: {config.ROUTER_LATENCY_MS}")
    print(f"ROUTER_ERROR_THRESHOLD: {config.ROUTER_ERROR_THRESHOLD}")

    print("\n✅ Sanity check passed!")

except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error during sanity check: {e}")
    sys.exit(1)
