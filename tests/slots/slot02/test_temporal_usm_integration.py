import os
from typing import Any, Dict

import pytest

from src.nova.slots.slot02_deltathresh.core import DeltaThreshProcessor


def _set_env(**kwargs: str) -> None:
    for key, value in kwargs.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def test_temporal_usm_disabled_without_flags():
    """Temporal USM does not emit payload when flag is off."""
    _set_env(NOVA_ENABLE_BIAS_DETECTION=None, NOVA_ENABLE_USM_TEMPORAL=None)

    processor = DeltaThreshProcessor()
    result = processor.process_content("Temporal test content.", session_id="s1")

    assert result.temporal_usm is None


def test_temporal_usm_requires_bias_detection():
    """Temporal USM only runs when both temporal and bias flags are enabled."""
    # Temporal flag ON, bias flag OFF -> no temporal_usm
    _set_env(NOVA_ENABLE_USM_TEMPORAL="1", NOVA_ENABLE_BIAS_DETECTION=None)
    processor = DeltaThreshProcessor()

    result = processor.process_content("Content without bias detection.", session_id="s2")
    assert result.temporal_usm is None


def test_temporal_usm_emitted_with_bias_and_temporal_flags(monkeypatch: Any):
    """Temporal USM emits temporal_usm@1-compatible payload when both flags are enabled."""
    _set_env(NOVA_ENABLE_USM_TEMPORAL="1", NOVA_ENABLE_BIAS_DETECTION="1")

    processor = DeltaThreshProcessor()

    # Patch _analyze_bias to return a controlled BIAS_REPORT@1-like dict
    def fake_analyze_bias(content: str) -> Dict[str, Any]:
        return {
            "bias_vector": {
                "b_local": 0.3,
                "b_global": 0.7,
                "b_risk": 0.6,
                "b_completion": 0.4,
                "b_structural": 0.5,
                "b_semantic": 0.3,
                "b_refusal": 0.2,
            },
            "collapse_score": 0.15,
            "usm_metrics": {
                "spectral_entropy": 1.8,
                "equilibrium_ratio": 0.65,
                "shield_factor": 0.3,
                "refusal_delta": 0.2,
            },
            "metadata": {"graph_state": "normal"},
            "confidence": 0.9,
        }

    monkeypatch.setattr(processor, "_analyze_bias", fake_analyze_bias)

    session_id = "stream-123"
    result = processor.process_content("Temporal USM enabled.", session_id=session_id)

    temporal = result.temporal_usm
    assert temporal is not None
    assert temporal["stream_id"] == session_id
    assert temporal["graph_state"] == "normal"
    # First non-VOID update uses instantaneous metrics
    assert temporal["H_temporal"] == pytest.approx(1.8)
    assert temporal["rho_temporal"] == pytest.approx(0.65)
    assert temporal["C_temporal"] == pytest.approx(0.15)
    assert 0.0 < temporal["lambda_used"] < 1.0
    assert temporal["mode"] in {"soft", "reset", "freeze"}
    assert 0.0 <= temporal["rho_equilibrium"] <= 1.0


def test_temporal_usm_void_decay(monkeypatch: Any):
    """VOID updates apply soft decay to temporal state when mode=soft."""
    _set_env(NOVA_ENABLE_USM_TEMPORAL="1", NOVA_ENABLE_BIAS_DETECTION="1", NOVA_TEMPORAL_MODE="soft")

    processor = DeltaThreshProcessor()

    # Two-step sequence: normal -> void
    calls = {"count": 0}

    def fake_analyze_bias(content: str) -> Dict[str, Any]:
        calls["count"] += 1
        if calls["count"] == 1:
            return {
                "bias_vector": {},
                "collapse_score": 0.4,
                "usm_metrics": {
                    "spectral_entropy": 2.0,
                    "equilibrium_ratio": 0.4,
                    "shield_factor": 0.0,
                    "refusal_delta": 0.0,
                },
                "metadata": {"graph_state": "normal"},
                "confidence": 0.9,
            }
        else:
            return {
                "bias_vector": {},
                "collapse_score": -0.5,
                "usm_metrics": {
                    "spectral_entropy": 0.0,
                    "equilibrium_ratio": None,
                    "shield_factor": 0.0,
                    "refusal_delta": 0.0,
                },
                "metadata": {"graph_state": "void"},
                "confidence": 1.0,
            }

    monkeypatch.setattr(processor, "_analyze_bias", fake_analyze_bias)

    session_id = "stream-void"

    first = processor.process_content("First (normal).", session_id=session_id)
    second = processor.process_content("Second (void).", session_id=session_id)

    t1 = first.temporal_usm
    t2 = second.temporal_usm

    assert t1 is not None and t2 is not None
    assert t1["graph_state"] == "normal"
    assert t2["graph_state"] == "void"
    # C_temporal decays toward 0 in VOID
    assert t2["C_temporal"] == pytest.approx(t1["C_temporal"] * processor._temporal_lambda)
    # rho_temporal moves toward rho_eq
    assert t2["rho_temporal"] > t1["rho_temporal"]


def test_temporal_usm_per_stream_isolated(monkeypatch: Any):
    """Temporal state is tracked per stream_id (session_id) independently."""
    _set_env(NOVA_ENABLE_USM_TEMPORAL="1", NOVA_ENABLE_BIAS_DETECTION="1")

    processor = DeltaThreshProcessor()

    def fake_analyze_bias(content: str) -> Dict[str, Any]:
        return {
            "bias_vector": {},
            "collapse_score": 0.2,
            "usm_metrics": {
                "spectral_entropy": 1.0,
                "equilibrium_ratio": 0.5,
                "shield_factor": 0.0,
                "refusal_delta": 0.0,
            },
            "metadata": {"graph_state": "normal"},
            "confidence": 0.9,
        }

    monkeypatch.setattr(processor, "_analyze_bias", fake_analyze_bias)

    # Two different streams
    processor.process_content("Stream A - first", session_id="A")
    processor.process_content("Stream B - first", session_id="B")

    assert "A" in processor._temporal_state
    assert "B" in processor._temporal_state
    assert processor._temporal_state["A"] is not processor._temporal_state["B"]


# ---------------------------------------------------------------------------
# Temporal extraction annotation (extraction_present)
# ---------------------------------------------------------------------------

def _make_processor_with_fake_bias(
    monkeypatch: Any,
    equilibrium_ratio: float,
    graph_state: str = "normal",
) -> DeltaThreshProcessor:
    """Helper to construct a processor with deterministic USM metrics."""
    _set_env(NOVA_ENABLE_USM_TEMPORAL="1", NOVA_ENABLE_BIAS_DETECTION="1")

    processor = DeltaThreshProcessor()

    def fake_analyze_bias(content: str) -> Dict[str, Any]:
        return {
            "bias_vector": {},
            "collapse_score": 0.2,
            "usm_metrics": {
                "spectral_entropy": 1.0,
                "equilibrium_ratio": equilibrium_ratio,
                "shield_factor": 0.0,
                "refusal_delta": 0.0,
            },
            "metadata": {"graph_state": graph_state},
            "confidence": 0.9,
        }

    monkeypatch.setattr(processor, "_analyze_bias", fake_analyze_bias)
    return processor


def test_extraction_present_none_during_warmup(monkeypatch: Any) -> None:
    """First 1-2 non-VOID turns keep extraction_present=None (min_turns guardrail)."""
    processor = _make_processor_with_fake_bias(
        monkeypatch, equilibrium_ratio=0.1, graph_state="normal"
    )

    session_id = "warmup-session"

    # Turn 1 (count=1 < min_turns)
    r1 = processor.process_content("First turn.", session_id=session_id)
    assert r1.bias_report is not None
    assert r1.bias_report.get("extraction_present") is None

    # Turn 2 (count=2 < min_turns)
    r2 = processor.process_content("Second turn.", session_id=session_id)
    assert r2.bias_report is not None
    assert r2.bias_report.get("extraction_present") is None


def test_extraction_present_true_for_low_rho_after_warmup(monkeypatch: Any) -> None:
    """Low rho_t band (<= extractive_rho) yields extraction_present=True after warmup."""
    processor = _make_processor_with_fake_bias(
        monkeypatch, equilibrium_ratio=0.1, graph_state="normal"
    )
    session_id = "low-rho"

    # Advance to and past warm-up (min_turns=3)
    for i in range(3):
        result = processor.process_content(f"turn-{i}", session_id=session_id)

    assert result.bias_report is not None
    assert result.bias_report.get("extraction_present") is True


def test_extraction_present_false_for_high_rho_after_warmup(monkeypatch: Any) -> None:
    """High rho_t band (>= protective_rho) yields extraction_present=False after warmup."""
    processor = _make_processor_with_fake_bias(
        monkeypatch, equilibrium_ratio=0.8, graph_state="normal"
    )
    session_id = "high-rho"

    for i in range(3):
        result = processor.process_content(f"turn-{i}", session_id=session_id)

    assert result.bias_report is not None
    assert result.bias_report.get("extraction_present") is False


def test_extraction_present_none_for_mid_rho_after_warmup(monkeypatch: Any) -> None:
    """Mid-band rho_t produces extraction_present=None after warmup (ambiguous)."""
    processor = _make_processor_with_fake_bias(
        monkeypatch, equilibrium_ratio=0.4, graph_state="normal"
    )
    session_id = "mid-rho"

    for i in range(3):
        result = processor.process_content(f"turn-{i}", session_id=session_id)

    assert result.bias_report is not None
    assert result.bias_report.get("extraction_present") is None


def test_extraction_present_none_for_void_state(monkeypatch: Any) -> None:
    """VOID graph_state always yields extraction_present=None, regardless of rho_t."""
    # equilibrium_ratio is unused in VOID updates but provided for completeness.
    processor = _make_processor_with_fake_bias(
        monkeypatch, equilibrium_ratio=None, graph_state="void"  # type: ignore[arg-type]
    )

    result = processor.process_content("Void-only turn.", session_id="void-session")
    assert result.bias_report is not None
    assert result.bias_report.get("extraction_present") is None
