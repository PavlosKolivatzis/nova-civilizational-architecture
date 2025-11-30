"""Test Continuity Stability Index (CSI) computation."""

import tempfile
from pathlib import Path

import pytest

import nova.ledger.factory as ledger_factory
from nova.continuity.csi_calculator import compute_csi, get_csi_breakdown


@pytest.fixture(autouse=True)
def csi_test_env(monkeypatch, tmp_path):
    """Isolate ledger/keyring for CSI tests to avoid ~/.nova writes."""
    # Force in-memory ledger and reset singleton to avoid cross-test pollution
    monkeypatch.setenv("LEDGER_BACKEND", "memory")
    ledger_factory.reset_memory_store_singleton()

    # Use a temp keyring to avoid ~/.nova access during tests
    key_dir = tmp_path / "keyring"
    key_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("NOVA_KEYRING_DIR", str(key_dir))
    monkeypatch.setenv("NOVA_PQC_KEYFILE", str(key_dir / "pqc_key_01.json"))

    yield


def test_compute_csi_empty_chain():
    """CSI returns 0.0 for empty chain."""
    csi = compute_csi("nonexistent-phase")
    assert csi == 0.0


def test_compute_csi_with_attestations():
    """CSI computes correctly from RC attestation history."""
    import sys
    repo_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(repo_root / "scripts"))

    from generate_rc_attestation import generate_attestation

    # Generate 3 RC attestations
    for i in range(3):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = Path(f.name)

        try:
            generate_attestation(
                output_path=output_path,
                memory_stability=0.85 + (i * 0.01),
                ris_score=0.90 + (i * 0.01),
                stress_recovery=0.92 + (i * 0.01),
                append_to_ledger=True
            )
        finally:
            output_path.unlink(missing_ok=True)

    # Compute CSI
    csi = compute_csi("7.0-rc", window_size=3)

    # CSI should be > 0 since we have attestations
    assert csi > 0.0
    # CSI should be <= 1.0 (clamped)
    assert csi <= 1.0


def test_csi_formula_components():
    """Verify CSI formula: 0.3*P6 + 0.3*P7 + 0.4*correlation."""
    import sys
    repo_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(repo_root / "scripts"))

    from generate_rc_attestation import generate_attestation

    # Generate single attestation with known stability
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        output_path = Path(f.name)

    try:
        generate_attestation(
            output_path=output_path,
            memory_stability=0.90,
            ris_score=0.85,
            stress_recovery=0.95,
            append_to_ledger=True
        )
    finally:
        output_path.unlink(missing_ok=True)

    # Get CSI breakdown
    breakdown = get_csi_breakdown("7.0-rc", window_size=1)

    # Verify components
    assert "csi" in breakdown
    assert "p6_stability" in breakdown
    assert "p7_stability" in breakdown
    assert "correlation" in breakdown

    # P6 is placeholder (0.85)
    assert breakdown["p6_stability"] == 0.85

    # P7 should match attestation memory stability
    assert 0.89 <= breakdown["p7_stability"] <= 0.91  # Allow small variance from window

    # Correlation is min(P6, P7)
    expected_corr = min(breakdown["p6_stability"], breakdown["p7_stability"])
    assert abs(breakdown["correlation"] - expected_corr) < 0.01

    # Verify CSI formula
    expected_csi = (
        0.3 * breakdown["p6_stability"] +
        0.3 * breakdown["p7_stability"] +
        0.4 * breakdown["correlation"]
    )
    assert abs(breakdown["csi"] - expected_csi) < 0.01


def test_csi_window_size():
    """CSI uses only window_size most recent attestations."""
    import sys
    repo_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(repo_root / "scripts"))

    from generate_rc_attestation import generate_attestation

    # Generate 5 attestations with varying stability
    stabilities = [0.70, 0.75, 0.80, 0.85, 0.90]

    for stability in stabilities:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = Path(f.name)

        try:
            generate_attestation(
                output_path=output_path,
                memory_stability=stability,
                ris_score=0.85,
                stress_recovery=0.90,
                append_to_ledger=True
            )
        finally:
            output_path.unlink(missing_ok=True)

    # Compute CSI with window_size=2 (should use last 2: 0.85, 0.90)
    breakdown = get_csi_breakdown("7.0-rc", window_size=2)

    # P7 should be average of last 2 attestations
    expected_p7 = (0.85 + 0.90) / 2
    assert abs(breakdown["p7_stability"] - expected_p7) < 0.01


def test_csi_breakdown_structure():
    """get_csi_breakdown returns all expected fields."""
    import sys
    repo_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(repo_root / "scripts"))

    from generate_rc_attestation import generate_attestation

    # Generate single attestation
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        output_path = Path(f.name)

    try:
        generate_attestation(
            output_path=output_path,
            memory_stability=0.88,
            ris_score=0.90,
            stress_recovery=0.92,
            append_to_ledger=True
        )
    finally:
        output_path.unlink(missing_ok=True)

    breakdown = get_csi_breakdown("7.0-rc")

    # Verify all expected fields
    expected_fields = {
        "csi",
        "p6_stability",
        "p7_stability",
        "p7_ris",
        "correlation",
        "attestation_count",
        "window_size",
        "weights",
    }

    assert set(breakdown.keys()) == expected_fields

    # Verify weights
    assert breakdown["weights"] == {
        "p6": 0.3,
        "p7": 0.3,
        "correlation": 0.4,
    }

    # Verify attestation_count > 0
    assert breakdown["attestation_count"] > 0

    # Verify window_size default is 7
    assert breakdown["window_size"] == 7
