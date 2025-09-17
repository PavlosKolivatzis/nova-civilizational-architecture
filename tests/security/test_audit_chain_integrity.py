from slots.common.hashutils import compute_audit_hash


def test_hash_changes_when_nested_fields_change():
    base = {
        "id": "a1",
        "slot": 2,
        "type": "event",
        "timestamp": 123.4,
        "api_version": "1.0",
        "router_state": {"mode": "stable", "tri_enabled": True},
        "circuit_breaker_state": {"open": False},
        "ids_traits_state": {"risk": 0.1},
        "ids_content_state": {"delta": 0.2},
        "data": {"payload": "x"},
        "confidence": 0.99,
        "previous_hash": "",
    }
    h1 = compute_audit_hash(base)
    tampered = dict(base)
    tampered["ids_traits_state"] = {"risk": 0.5}
    h2 = compute_audit_hash(tampered)
    assert h1 != h2


def test_hash_chain_links_previous():
    rec = {"id": "a2", "slot": 2, "type": "event", "timestamp": 1.0, "previous_hash": ""}
    h1 = compute_audit_hash(rec)
    rec2 = {
        "id": "a3",
        "slot": 2,
        "type": "event",
        "timestamp": 2.0,
        "previous_hash": h1,
    }
    h2 = compute_audit_hash(rec2)
    assert h1 != h2 and isinstance(h1, str) and isinstance(h2, str)
