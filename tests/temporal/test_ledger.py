import pytest

from nova.orchestrator.temporal.ledger import TemporalLedger, TemporalLedgerError


def test_temporal_ledger_append_and_hash_chain():
    ledger = TemporalLedger()
    ledger.append({"timestamp": 1.0, "tri_coherence": 0.9})
    ledger.append({"timestamp": 2.0, "tri_coherence": 0.85})
    entries = ledger.snapshot()
    assert entries[0]["prev_hash"] == ""
    assert isinstance(entries[0]["hash"], str)
    assert entries[1]["prev_hash"] == entries[0]["hash"]


def test_temporal_ledger_monotonic_enforced():
    ledger = TemporalLedger()
    ledger.append({"timestamp": 10.0})
    with pytest.raises(TemporalLedgerError):
        ledger.append({"timestamp": 5.0})
