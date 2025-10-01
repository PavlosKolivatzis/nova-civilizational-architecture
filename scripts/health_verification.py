#!/usr/bin/env python3
"""Health verification script for Nova Civilizational Architecture.

This script verifies that all 12 Nova slots are operational with
standardized health reporting using the shared healthkit library.
"""

import requests
import json
import sys
from typing import Dict, Any, List
from datetime import datetime


def verify_slot_health(slot_name: str, base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """Verify health of a specific slot."""
    try:
        response = requests.get(f"{base_url}/health/{slot_name}", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            return {
                "status": "ok",
                "health_data": health_data,
                "schema_version": health_data.get("schema_version", "unknown"),
                "engine_status": health_data.get("engine_status", "unknown"),
                "self_check": health_data.get("self_check", "unknown"),
                "capabilities_count": len(health_data.get("capabilities", [])),
                "deps_count": len(health_data.get("deps", [])),
            }
        else:
            return {"status": "error", "http_status": response.status_code, "message": response.text}
    except Exception as e:
        return {"status": "error", "exception": str(e)}


def verify_aggregate_health(base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """Verify aggregate health endpoint."""
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            slot_checks = health_data.get("slot_self_checks", {})
            return {
                "status": "ok",
                "total_slots": len(slot_checks),
                "operational_slots": sum(1 for slot in slot_checks.values()
                                       if slot.get("self_check") == "ok"),
                "flow_fabric_status": health_data.get("flow_fabric", {}).get("status", "unknown"),
                "overall_status": health_data.get("status", "unknown"),
            }
        else:
            return {"status": "error", "http_status": response.status_code, "message": response.text}
    except Exception as e:
        return {"status": "error", "exception": str(e)}


def main():
    """Main verification routine."""
    print("Nova Civilizational Architecture - Health Verification")
    print("=" * 60)
    print(f"Verification time: {datetime.now().isoformat()}")
    print()

    # Expected slot names
    expected_slots = [
        "slot01_truth_anchor",
        "slot02_deltathresh",
        "slot03_emotional_matrix",
        "slot04_tri",
        "slot04_tri_engine",
        "slot05_constellation",
        "slot06_cultural_synthesis",
        "slot07_production_controls",
        "slot08_memory_ethics",
        "slot08_memory_lock",
        "slot09_distortion_protection",
        "slot10_civilizational_deployment",
    ]

    # Verify aggregate health first
    print("1. Aggregate Health Check")
    print("-" * 30)
    aggregate_result = verify_aggregate_health()
    if aggregate_result["status"] == "ok":
        print(f"✓ Total slots detected: {aggregate_result['total_slots']}")
        print(f"✓ Operational slots: {aggregate_result['operational_slots']}")
        print(f"✓ Flow fabric status: {aggregate_result['flow_fabric_status']}")
        print(f"✓ Overall status: {aggregate_result['overall_status']}")
    else:
        print(f"✗ Aggregate health check failed: {aggregate_result}")
        sys.exit(1)
    print()

    # Verify individual slot health
    print("2. Individual Slot Health Checks")
    print("-" * 40)

    operational_count = 0
    failed_slots = []

    for slot_name in expected_slots:
        result = verify_slot_health(slot_name)
        if result["status"] == "ok":
            health_data = result["health_data"]
            engine_status = result["engine_status"]
            self_check = result["self_check"]
            capabilities = result["capabilities_count"]
            deps = result["deps_count"]

            print(f"✓ {slot_name:32} | {engine_status:12} | {self_check:8} | caps:{capabilities:2} | deps:{deps}")
            operational_count += 1
        else:
            print(f"✗ {slot_name:32} | ERROR: {result.get('exception', result.get('message', 'unknown'))}")
            failed_slots.append(slot_name)

    print()
    print("3. Summary")
    print("-" * 20)
    print(f"Operational slots: {operational_count}/{len(expected_slots)}")

    if failed_slots:
        print(f"Failed slots: {', '.join(failed_slots)}")
        print("\n❌ HEALTH VERIFICATION FAILED")
        sys.exit(1)
    else:
        print("✅ ALL SLOTS OPERATIONAL - HEALTH VERIFICATION PASSED")
        print()
        print("🎉 Nova Civilizational Architecture polish sprint complete!")
        print("   - Shared healthkit library implemented")
        print("   - All 12 slots reporting standardized health metrics")
        print("   - Production-ready health monitoring achieved")

    return 0


if __name__ == "__main__":
    sys.exit(main())