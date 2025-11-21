import pytest

from orchestrator.predictive.ledger import PredictiveLedger, PredictiveLedgerError


def test_predictive_ledger_appends_entries():
    ledger = PredictiveLedger()
    ledger.append({"timestamp": 1.0, "tri_coherence": 0.9})
    ledger.append({"timestamp": 2.0, "tri_coherence": 0.85})
    entries = ledger.snapshot()
    assert len(entries) == 2
    assert entries[-1]["entry"]["tri_coherence"] == 0.85


def test_predictive_ledger_enforces_monotonic_time():
    ledger = PredictiveLedger()
    ledger.append({"timestamp": 10.0})
    with pytest.raises(PredictiveLedgerError):
        ledger.append({"timestamp": 9.0})


def test_predictive_ledger_head_returns_copy():
    ledger = PredictiveLedger()
    ledger.append({"timestamp": 5.0, "value": 42})
    head = ledger.head()
    assert head["entry"]["value"] == 42
    head["entry"]["value"] = 0
    assert ledger.head()["entry"]["value"] == 42
