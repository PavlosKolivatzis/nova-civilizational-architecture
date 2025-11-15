"""Integration test for UNLEARN_PULSE emitter binding at startup."""

import json
import os
import pytest
from types import SimpleNamespace


@pytest.mark.asyncio
async def test_startup_binds_jsonl_emitter_and_emits(tmp_path, monkeypatch):
    """Test that startup binds JsonlEmitter and emits contracts on context expiry."""
    # Route emissions to a temp file
    out = tmp_path / "pulses.ndjson"
    monkeypatch.setenv("NOVA_UNLEARN_PULSE_PATH", str(out))

    # Import and run startup
    from orchestrator.app import _startup
    from orchestrator.contracts.emitter import get_contract_emitter, NoOpEmitter

    await _startup()
    emitter = get_contract_emitter()
    assert not isinstance(emitter, NoOpEmitter), "Emitter should be bound at startup"
    assert emitter.__class__.__name__ == "JsonlEmitter"

    # Force an expiring context → triggers UNLEARN_PULSE@1
    from orchestrator.semantic_mirror import SemanticMirror, ContextScope
    sm = SemanticMirror()
    sm._contexts["slot03.phase_lock"] = SimpleNamespace(
        timestamp=0.0,
        ttl_seconds=120.0,  # Must be ≥60s to trigger pulse
        access_count=3,
        scope=ContextScope.INTERNAL,
        published_by="slot04",
        is_expired=lambda current_time: True  # Mock expiration
    )

    # Expire
    sm._cleanup_expired_entries(current_time=9999.0)

    # Verify file written with valid JSON lines
    assert out.exists() and out.stat().st_size > 0
    with open(out, "r", encoding="utf-8") as f:
        lines = [json.loads(x) for x in f if x.strip()]

    assert len(lines) >= 1
    rec = lines[0]
    assert rec["schema_id"] == "UNLEARN_PULSE"
    assert rec["schema_version"] == 1
    assert rec["key"] == "slot03.phase_lock"
    assert rec["target_slot"] in ("slot03", "slot04")  # extractor may include both


def test_emitter_configuration_and_emission(tmp_path, monkeypatch):
    """Test emitter configuration and actual emission functionality."""
    import json
    from orchestrator.contracts.emitter import set_contract_emitter
    from orchestrator.contracts.unlearn_pulse import UnlearnPulseV1

    # Create test emitter class (mirrors the one in app.py)
    class TestJsonlEmitter:
        def __init__(self, path=None):
            if path is None:
                path = os.getenv("NOVA_UNLEARN_PULSE_PATH", "logs/unlearn_pulses.ndjson")
            self.path = path
            os.makedirs(os.path.dirname(path), exist_ok=True)
        def emit(self, contract):
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(contract.model_dump()) + "\n")

    # Test with custom path
    custom_path = tmp_path / "custom_pulses.ndjson"
    monkeypatch.setenv("NOVA_UNLEARN_PULSE_PATH", str(custom_path))

    emitter = TestJsonlEmitter()
    assert emitter.path == str(custom_path)
    assert custom_path.parent.exists()

    # Test emission
    set_contract_emitter(emitter)
    contract = UnlearnPulseV1(
        key="slot03.phase_lock",
        target_slot="slot03",
        published_by="slot04"
    )
    emitter.emit(contract)

    # Verify emission
    assert custom_path.exists() and custom_path.stat().st_size > 0
    with open(custom_path, "r", encoding="utf-8") as f:
        lines = [json.loads(x) for x in f if x.strip()]

    assert len(lines) == 1
    rec = lines[0]
    assert rec["schema_id"] == "UNLEARN_PULSE"
    assert rec["schema_version"] == 1
    assert rec["key"] == "slot03.phase_lock"
    assert rec["target_slot"] == "slot03"
