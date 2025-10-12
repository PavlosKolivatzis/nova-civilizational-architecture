
from nova.slots.slot08_memory_ethics import ids_protection as ip
from services.ids.core import IDSState


def test_protected_memory_write_allows(monkeypatch):
    ip.memory_store.clear()

    def mock_analyze_vector(vector, trace_id="", scope="memory", previous_vector=None):
        return {"stability": 0.9, "drift": 0.0, "state": IDSState.STABLE.value}

    monkeypatch.setattr(ip.ids_service, "analyze_vector", mock_analyze_vector)

    embedding = [0.1, 0.2, 0.3]
    metadata = {"actor": "tester"}
    trace_id = "allowed_trace"

    result = ip.protected_memory_write(embedding, metadata, trace_id)

    assert result["success"] is True
    assert result["ids_protection"] == "passed"
    assert trace_id in ip.memory_store
    lock = ip.memory_store[trace_id]
    assert lock.verify()
    assert lock.data["embedding"] == embedding
    assert lock.data["metadata"] == metadata


def test_protected_memory_write_blocked(monkeypatch):
    ip.memory_store.clear()

    def mock_analyze_vector(vector, trace_id="", scope="memory", previous_vector=None):
        return {"stability": 0.2, "drift": 0.3, "state": IDSState.DIVERGING.value}

    monkeypatch.setattr(ip.ids_service, "analyze_vector", mock_analyze_vector)

    embedding = [0.1, 0.2, 0.3]
    metadata = {"actor": "tester"}
    trace_id = "blocked_trace"

    result = ip.protected_memory_write(embedding, metadata, trace_id)

    assert result["success"] is False
    assert result["blocked_by"] == "ids_protection"
    assert trace_id not in ip.memory_store
