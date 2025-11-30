from nova.orchestrator.router.constraints import evaluate_constraints


def test_constraints_allow_when_all_signals_good():
    request = {
        "tri_signal": {"tri_coherence": 0.9, "tri_drift_z": 0.1, "tri_jitter": 0.1},
        "slot07": {"mode": "BASELINE"},
        "slot10": {"passed": True},
    }
    result = evaluate_constraints(request)
    assert result.allowed is True
    assert result.reasons == []


def test_constraints_block_on_low_coherence():
    request = {
        "tri_signal": {"tri_coherence": 0.2, "tri_drift_z": 0.1, "tri_jitter": 0.0},
        "slot07": {"mode": "BASELINE"},
        "slot10": {"passed": True},
    }
    result = evaluate_constraints(request)
    assert result.allowed is False
    assert any("tri_coherence" in reason for reason in result.reasons)


def test_constraints_block_when_slot07_frozen():
    request = {
        "tri_signal": {"tri_coherence": 0.9},
        "slot07": {"mode": "FROZEN"},
    }
    result = evaluate_constraints(request)
    assert result.allowed is False
    assert "slot07_frozen" in result.reasons


def test_constraints_block_when_slot10_gate_closed():
    request = {
        "tri_signal": {"tri_coherence": 0.9},
        "slot07": {"mode": "BASELINE"},
        "slot10": {"passed": False, "reason": "gate_closed"},
    }
    result = evaluate_constraints(request)
    assert result.allowed is False
    assert any("gate_closed" in reason for reason in result.reasons)
