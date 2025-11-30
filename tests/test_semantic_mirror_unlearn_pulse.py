"""Tests for Observable Pulse prototype in semantic mirror contextual unlearning."""

from types import SimpleNamespace
from nova.orchestrator.semantic_mirror import SemanticMirror, ContextScope


def mk_entry(**kw):
    """Create a mock context entry for testing."""
    d = dict(
        timestamp=0.0,
        ttl_seconds=120.0,
        access_count=2,
        scope=ContextScope.INTERNAL,
        published_by="slot03",
    )
    d.update(kw)
    entry = SimpleNamespace(**d)

    # Add is_expired method to mock
    def is_expired(current_time):
        return (current_time - entry.timestamp) > entry.ttl_seconds
    entry.is_expired = is_expired

    return entry


def test_expired_entry_emits_pulse_and_increments_metrics():
    """Test that expired entries emit unlearn pulses and update metrics."""
    sm = SemanticMirror()
    sm._contexts["slot03.phase_lock"] = mk_entry()

    # Force expiry by setting future time
    now = 9999.0
    sm._cleanup_expired_entries(now)

    # Verify metrics
    assert sm._metrics["entries_expired"] == 1
    assert sm._metrics["unlearn_pulses_sent"] == 1
    assert sm._metrics["unlearn_pulse_total_contexts"] == 1
    assert sm._metrics["unlearn_pulse_to_slot03"] == 1

    # Verify entry was deleted
    assert "slot03.phase_lock" not in sm._contexts


def test_immune_slots_do_not_receive_pulses():
    """Foundational slots (slot01, slot07) are immune to unlearn pulses."""
    sm = SemanticMirror()

    # Use documented keys as literals (ACL-safe)
    # Publishers are immune (slot01, slot07) so they won't receive pulses
    sm._contexts["slot03.phase_lock"] = mk_entry(published_by="slot01")
    sm._contexts["slot04.coherence"] = mk_entry(published_by="slot07")

    sm._cleanup_expired_entries(9999.0)

    # Entries expired and pulses sent to the key slots (slot03, slot04),
    # but immune publishers (slot01, slot07) are filtered out
    assert sm._metrics["entries_expired"] == 2
    assert sm._metrics.get("unlearn_pulses_sent", 0) == 2  # pulses to slot03, slot04
    # Key-derived slots get pulses (not immune)
    assert sm._metrics["unlearn_pulse_to_slot03"] == 1
    assert sm._metrics["unlearn_pulse_to_slot04"] == 1
    # Immune publishers don't get pulses
    assert "unlearn_pulse_to_slot01" not in sm._metrics
    assert "unlearn_pulse_to_slot07" not in sm._metrics


def test_should_emit_unlearn_pulse_conditions():
    """Test the conditions for emitting unlearn pulses."""
    sm = SemanticMirror()

    # Should emit: accessed > 1, internal scope, long TTL
    entry_should_emit = mk_entry(
        access_count=3,
        scope=ContextScope.INTERNAL,
        ttl_seconds=120.0
    )
    assert sm._should_emit_unlearn_pulse(entry_should_emit) is True

    # Should not emit: access_count <= 1
    entry_low_access = mk_entry(access_count=1)
    assert sm._should_emit_unlearn_pulse(entry_low_access) is False

    # Should not emit: private scope
    entry_private = mk_entry(
        access_count=3,
        scope=ContextScope.PRIVATE
    )
    assert sm._should_emit_unlearn_pulse(entry_private) is False

    # Should not emit: short TTL (transient)
    entry_short_ttl = mk_entry(
        access_count=3,
        ttl_seconds=30.0
    )
    assert sm._should_emit_unlearn_pulse(entry_short_ttl) is False


def test_extract_source_slots():
    """Test extraction of source slots from context keys."""
    sm = SemanticMirror()

    # Test slot key extraction - both slot from key and publisher included
    entry = mk_entry(published_by="slot03")
    slots = sm._extract_source_slots("slot04.coherence", entry)
    assert "slot04" in slots  # from key
    assert "slot03" in slots  # from publisher

    # Test immunity filtering - slot03 from key should be included, slot01 publisher filtered out
    entry_immune = mk_entry(published_by="slot01")
    slots_immune = sm._extract_source_slots("slot03.phase_lock", entry_immune)
    assert "slot03" in slots_immune  # from key (not immune)
    assert "slot01" not in slots_immune  # publisher filtered out (immune)
    assert len(slots_immune) == 1

    # Test non-slot key with non-immune publisher
    entry_other = mk_entry(published_by="prometheus_metrics")
    slots_other = sm._extract_source_slots("slot04.coherence", entry_other)
    assert "slot04" in slots_other  # from key
    assert "prometheus_metrics" in slots_other  # from publisher


def test_slot_immunity():
    """Test that foundational slots are immune to unlearn pulses."""
    sm = SemanticMirror()

    # Immune slots
    immune_slots = [
        "slot01", "slot07",
        "slot1_truth_anchor", "slot7_production_controls"
    ]
    for slot in immune_slots:
        assert sm._slot_should_receive_unlearn_pulse(slot) is False

    # Non-immune slots
    non_immune_slots = ["slot03", "slot04", "slot05", "slot06", "slot08", "slot10"]
    for slot in non_immune_slots:
        assert sm._slot_should_receive_unlearn_pulse(slot) is True


def test_multiple_expired_entries_pulse_counting():
    """Test pulse counting with multiple expired entries."""
    sm = SemanticMirror()

    # Add multiple entries that should emit pulses (use documented keys)
    sm._contexts["slot03.phase_lock"] = mk_entry(published_by="slot03")
    sm._contexts["slot04.coherence"] = mk_entry(published_by="slot04")
    sm._contexts["slot06.cultural_profile"] = mk_entry(published_by="slot06")

    # Add entry that shouldn't emit (low access) - use documented key
    sm._contexts["slot04.phase_coherence"] = mk_entry(access_count=1, published_by="slot05")

    sm._cleanup_expired_entries(9999.0)

    # Verify metrics
    assert sm._metrics["entries_expired"] == 4
    assert sm._metrics["unlearn_pulses_sent"] == 3  # 3 should emit, 1 shouldn't
    assert sm._metrics["unlearn_pulse_total_contexts"] == 3
    assert sm._metrics["unlearn_pulse_to_slot03"] == 1
    assert sm._metrics["unlearn_pulse_to_slot04"] == 1
    assert sm._metrics["unlearn_pulse_to_slot06"] == 1
    assert "unlearn_pulse_to_slot05" not in sm._metrics  # low access count


def test_unlearn_pulse_logging_can_be_disabled(monkeypatch, caplog):
    """Test that unlearn pulse logging can be disabled via environment variable."""
    # Disable logging
    monkeypatch.setenv("NOVA_UNLEARN_PULSE_LOG", "0")

    sm = SemanticMirror()
    sm._contexts["slot03.phase_lock"] = mk_entry()

    sm._cleanup_expired_entries(9999.0)

    # Should still emit pulse (metrics updated) but no log message
    assert sm._metrics["unlearn_pulses_sent"] == 1
    assert "UNLEARN_PULSE" not in caplog.text


def test_graceful_error_handling_in_pulse_emission():
    """Test that errors in pulse emission don't break cleanup."""
    sm = SemanticMirror()

    # Create entry with malformed timestamp - use documented key
    bad_entry = mk_entry()
    bad_entry.timestamp = "not_a_number"  # This will cause age calculation to fail

    sm._contexts["slot03.phase_lock"] = bad_entry

    # Should not raise exception
    sm._cleanup_expired_entries(9999.0)

    # Entry should still be cleaned up
    assert "slot03.phase_lock" not in sm._contexts
    assert sm._metrics["entries_expired"] == 1


def test_public_scope_entries_emit_pulses():
    """Test that PUBLIC scope entries also emit unlearn pulses."""
    sm = SemanticMirror()
    sm._contexts["slot03.phase_lock"] = mk_entry(
        scope=ContextScope.PUBLIC,
        access_count=5
    )

    sm._cleanup_expired_entries(9999.0)

    assert sm._metrics["unlearn_pulses_sent"] == 1
    assert sm._metrics["unlearn_pulse_to_slot03"] == 1
