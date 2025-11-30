import json
import pathlib
import subprocess
import yaml


def test_schema_exists():
    """Verify Phase 10 ethics schema file exists."""
    assert pathlib.Path("schemas/phase10_ethics.yaml").exists()


def test_fep_contract_policy_threshold():
    """Verify FEP contract enforces FCQ ≥ 0.90 threshold."""
    cfg = yaml.safe_load(
        pathlib.Path("src/nova/orchestrator/contracts/phase10_fep.yaml").read_text()
    )
    assert cfg["policies"]["fcq_threshold"] >= 0.90


def test_fep_contract_dissent_recording():
    """Verify FEP contract preserves dissenting votes."""
    cfg = yaml.safe_load(
        pathlib.Path("src/nova/orchestrator/contracts/phase10_fep.yaml").read_text()
    )
    assert cfg["policies"]["record_dissent"] is True


def test_sim_outputs_fcq():
    """Verify simulation script produces valid FCQ decision."""
    out = subprocess.check_output(["python3", "scripts/simulate_federated_ethics.py"])
    data = json.loads(out)
    assert 0.0 <= data["fcq"] <= 1.0
    assert "provenance" in data and "hash" in data["provenance"]


def test_sim_provenance_chain():
    """Verify simulation includes hash-linked provenance."""
    out = subprocess.check_output(["python3", "scripts/simulate_federated_ethics.py"])
    data = json.loads(out)
    prov = data["provenance"]
    assert "hash" in prov
    assert "parent_hash" in prov
    assert "timestamp" in prov
    # Hash should be SHA-256 hex (64 chars)
    assert len(prov["hash"]) == 64


def test_sim_votes_signed():
    """Verify all votes in simulation include signatures."""
    out = subprocess.check_output(["python3", "scripts/simulate_federated_ethics.py"])
    data = json.loads(out)
    for vote in data["votes"]:
        assert "signature" in vote
        assert len(vote["signature"]) > 0


def test_prometheus_metrics_defined():
    """Verify Phase 10 metrics are defined in Prometheus exporter."""
    metrics_file = pathlib.Path("src/nova/orchestrator/prometheus_metrics.py")
    content = metrics_file.read_text()
    assert "phase10_eai_gauge" in content
    assert "phase10_fcq_gauge" in content
    assert "phase10_cgc_gauge" in content
    assert "phase10_pis_gauge" in content
    assert "phase10_ag_throttle_counter" in content
    assert "phase10_ag_escalation_counter" in content
