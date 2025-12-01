"""Tests for UNLEARN_PULSE@1 contract emission from semantic mirror."""

from types import SimpleNamespace
from nova.orchestrator.semantic_mirror import SemanticMirror, ContextScope
from nova.orchestrator.contracts.emitter import set_contract_emitter, NoOpEmitter


class StubEmitter:
    """Test emitter that captures emitted contracts."""
    def __init__(self):
        self.events = []

    def emit(self, contract):
        self.events.append(contract)


def mk_entry(**kw):
    """Create a mock context entry for testing."""
    d = dict(
        timestamp=0.0,
        ttl_seconds=120.0,
        access_count=3,
        scope=ContextScope.INTERNAL,
        published_by="slot04",
    )
    d.update(kw)
    entry = SimpleNamespace(**d)

    # Add is_expired method to mock
    def is_expired(current_time):
        return (current_time - entry.timestamp) > entry.ttl_seconds
    entry.is_expired = is_expired

    return entry


def test_contract_emitted_to_all_destinations():
    """Test that UNLEARN_PULSE@1 contracts are emitted to all source slots."""
    sm = SemanticMirror()
    sm._contexts["slot03.phase_lock"] = mk_entry(published_by="slot04")

    # Normal extraction: key=slot03.*, plus published_by=slot04 → 2 destinations
    emitter = StubEmitter()
    set_contract_emitter(emitter)

    sm._cleanup_expired_entries(9999.0)

    assert sm._metrics["entries_expired"] == 1
    # Two contracts emitted: to slot03 and slot04
    assert len(emitter.events) == 2
    targets = sorted([e.target_slot for e in emitter.events])
    assert targets == ["slot03", "slot04"]

    # Contract basics
    for ev in emitter.events:
        assert ev.schema_id == "UNLEARN_PULSE"
        assert ev.schema_version == 1
        assert ev.key == "slot03.phase_lock"
        assert ev.reason == "ttl_expired"
        assert ev.published_by == "slot04"
        assert ev.ttl_seconds == 120.0
        assert ev.access_count == 3

    # Restore
    set_contract_emitter(NoOpEmitter())


def test_immune_recipients_block_emission():
    """Test that immune slots (slot01, slot07) don't receive contracts."""
    sm = SemanticMirror()
    sm._contexts["slot03.phase_lock"] = mk_entry(published_by="slot01")  # immune publisher

    emitter = StubEmitter()
    set_contract_emitter(emitter)
    sm._cleanup_expired_entries(9999.0)

    assert sm._metrics["entries_expired"] == 1
    # Only slot03 receives contract (from key), slot01 is immune
    assert len(emitter.events) == 1
    assert emitter.events[0].target_slot == "slot03"

    set_contract_emitter(NoOpEmitter())


def test_no_contract_emission_for_low_access_entries():
    """Test that entries with low access count don't emit contracts."""
    sm = SemanticMirror()
    sm._contexts["slot03.phase_lock"] = mk_entry(access_count=1)  # Below threshold

    emitter = StubEmitter()
    set_contract_emitter(emitter)
    sm._cleanup_expired_entries(9999.0)

    assert sm._metrics["entries_expired"] == 1
    # No contracts emitted due to low access count
    assert len(emitter.events) == 0

    set_contract_emitter(NoOpEmitter())


def test_contract_emission_error_handling():
    """Test that contract emission errors don't break cleanup."""
    class BrokenEmitter:
        def emit(self, contract):
            raise RuntimeError("Emission failed")

    sm = SemanticMirror()
    sm._contexts["slot03.phase_lock"] = mk_entry()

    set_contract_emitter(BrokenEmitter())

    # Should not raise exception
    sm._cleanup_expired_entries(9999.0)

    # Entry should still be cleaned up
    assert "slot03.phase_lock" not in sm._contexts
    assert sm._metrics["entries_expired"] == 1

    set_contract_emitter(NoOpEmitter())


def test_contract_contains_metadata():
    """Test that emitted contracts contain complete metadata."""
    sm = SemanticMirror()
    sm._contexts["slot04.coherence"] = mk_entry(
        published_by="slot06",
        ttl_seconds=300.0,
        access_count=5,
        scope=ContextScope.PUBLIC,
        timestamp=1000.0
    )

    emitter = StubEmitter()
    set_contract_emitter(emitter)
    sm._cleanup_expired_entries(9999.0)

    assert len(emitter.events) == 2  # slot04 + slot06

    for contract in emitter.events:
        assert contract.key == "slot04.coherence"
        assert contract.published_by == "slot06"
        assert contract.ttl_seconds == 300.0
        assert contract.access_count == 5
        assert contract.scope == "public"
        assert contract.age_seconds > 8000.0  # (9999 - 1000)
        assert contract.ts > 0  # timestamp set

    set_contract_emitter(NoOpEmitter())
