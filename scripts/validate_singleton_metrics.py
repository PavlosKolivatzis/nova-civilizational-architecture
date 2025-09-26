#!/usr/bin/env python3
"""
Validate Nova semantic mirror singleton metrics end-to-end.

Demonstrates:
- Single-process emitter setup
- Contract emission to JSONL
- Metrics collection on same singleton
- Prometheus export alignment
"""

import os
import json
import asyncio
from types import SimpleNamespace
from orchestrator.semantic_mirror import get_semantic_mirror, ContextScope
from orchestrator.contracts.emitter import set_contract_emitter
from orchestrator.app import _startup


class ValidationEmitter:
    """JSONL emitter for validation."""
    def __init__(self, path="logs/validation_pulses.ndjson"):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        # Clear previous validation data
        if os.path.exists(path):
            os.remove(path)

    def emit(self, contract):
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(contract.model_dump()) + "\n")


async def main():
    print("Nova Singleton Metrics Validation")
    print("=" * 50)

    # Test startup guard
    print("1. Testing startup guard...")
    os.environ["UVICORN_WORKERS"] = "1"
    await _startup()
    print("   [OK] Single worker passed guard")

    # Setup validation emitter
    print("2. Setting up validation emitter...")
    emitter = ValidationEmitter()
    set_contract_emitter(emitter)
    print("   [OK] JsonlEmitter configured")

    # Get production singleton
    print("3. Using production singleton...")
    sm = get_semantic_mirror()

    # Ensure a clean slate when running locally
    if hasattr(sm, "_reset_for_tests"):
        sm._reset_for_tests()
    print(f"   Initial metrics: {dict(sm._metrics)}")

    # Add test contexts (using documented keys for ACL compliance)
    print("4. Adding test contexts...")
    test_contexts = [
        ("slot03.phase_lock", "slot06", 150.0),
        ("slot04.coherence", "slot05", 200.0),
        ("slot04.phase_coherence", "slot07", 300.0)
    ]

    for key, publisher, ttl in test_contexts:
        sm._contexts[key] = SimpleNamespace(
            timestamp=0.0,
            ttl_seconds=ttl,
            access_count=5,  # > threshold
            scope=ContextScope.INTERNAL,
            published_by=publisher,
            is_expired=lambda current_time: True
        )
    print(f"   [OK] Added {len(test_contexts)} test contexts")

    # Trigger cleanup
    print("5. Triggering context cleanup...")
    before_metrics = dict(sm._metrics)
    sm._cleanup_expired_entries(9999.0)
    after_metrics = dict(sm._metrics)

    print(f"   Metrics Before: {before_metrics}")
    print(f"   Metrics After:  {after_metrics}")

    # Validate metrics
    print("6. Validating metrics...")
    actual_pulses = after_metrics.get("unlearn_pulses_sent", 0)

    if actual_pulses > 0:
        print(f"   [OK] Unlearn pulses sent: {actual_pulses}")
    else:
        print(f"   [ERROR] No pulses sent (expected > 0)")
        return

    # Check JSONL output
    print("7. Validating JSONL output...")
    if os.path.exists(emitter.path):
        with open(emitter.path, "r") as f:
            contracts = [json.loads(line) for line in f if line.strip()]

        print(f"   [OK] JSONL contracts written: {len(contracts)}")
        for contract in contracts[:3]:  # Show first 3
            print(f"      -> {contract['schema_id']}@{contract['schema_version']} to {contract['target_slot']}")
    else:
        print(f"   [ERROR] JSONL file not found: {emitter.path}")
        return

    # Test Prometheus alignment
    print("8. Testing Prometheus metrics alignment...")
    from orchestrator.prometheus_metrics import update_semantic_mirror_metrics, unlearn_pulses_sent_gauge

    update_semantic_mirror_metrics()
    prometheus_value = unlearn_pulses_sent_gauge._value._value

    if prometheus_value == actual_pulses:
        print(f"   [OK] Prometheus aligned: {prometheus_value} == {actual_pulses}")
    else:
        print(f"   [ERROR] Prometheus misaligned: {prometheus_value} != {actual_pulses}")
        return

    print("=" * 50)
    print("ALL VALIDATIONS PASSED")
    print("")
    print("Production checklist:")
    print("  [OK] Single-process metrics (UVICORN_WORKERS=1)")
    print("  [OK] Contract emission to JSONL")
    print("  [OK] Metrics collection on singleton")
    print("  [OK] Prometheus export alignment")
    print("  [OK] Nova cognitive metabolism observable")


if __name__ == "__main__":
    asyncio.run(main())