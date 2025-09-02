#!/usr/bin/env python3
"""
Quick sanity check for the NOVA system health and configuration.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from orchestrator.app import monitor, router, SLOT_REGISTRY
    from orchestrator.health import health_payload
    from orchestrator.config import config

    print("✅ Health Payload:")
    payload = health_payload(SLOT_REGISTRY, monitor, router)
    print(f"Slots monitored: {len(payload.get('slots', {}))}")
    print(f"Router thresholds: {payload.get('router_thresholds', {})}")

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
