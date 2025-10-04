"""
Test contract metadata completeness.

Validates that all flow fabric contracts have metadata declarations.
Prevents DEF-001 (contract metadata gap).
"""
import yaml
from pathlib import Path
import pytest


def test_all_flow_fabric_contracts_have_metadata():
    """Verify every KNOWN_CONTRACTS entry has produces/consumes in meta.yaml"""
    from orchestrator.flow_fabric_init import KNOWN_CONTRACTS

    # Collect all produces from metadata
    all_produces = set()
    meta_files = list(Path('slots').rglob('*.meta.yaml'))

    for meta_file in meta_files:
        with open(meta_file) as f:
            data = yaml.safe_load(f)
        produces = data.get('produces', [])
        all_produces.update(produces)

    # Verify each contract is documented
    missing = []
    for contract in KNOWN_CONTRACTS:
        if contract not in all_produces:
            missing.append(contract)

    assert not missing, (
        f"Contracts in flow_fabric_init.py missing from metadata: {missing}\n"
        f"Found {len(all_produces)} produces declarations: {sorted(all_produces)}\n"
        f"Expected {len(KNOWN_CONTRACTS)} contracts: {sorted(KNOWN_CONTRACTS)}\n"
        f"Add missing contracts to appropriate slot meta.yaml produces section"
    )


def test_all_metadata_contracts_are_registered():
    """Verify every produces/consumes contract is registered in flow fabric"""
    from orchestrator.flow_fabric_init import KNOWN_CONTRACTS

    # Collect all produces/consumes from metadata
    all_metadata_contracts = set()
    meta_files = list(Path('slots').rglob('*.meta.yaml'))

    for meta_file in meta_files:
        with open(meta_file) as f:
            data = yaml.safe_load(f)
        all_metadata_contracts.update(data.get('produces', []))
        all_metadata_contracts.update(data.get('consumes', []))

    # Verify each metadata contract is registered
    unregistered = all_metadata_contracts - set(KNOWN_CONTRACTS)

    assert not unregistered, (
        f"Contracts in metadata not registered in flow_fabric_init.py: {unregistered}\n"
        f"Add missing contracts to KNOWN_CONTRACTS in orchestrator/flow_fabric_init.py"
    )


def test_all_slots_have_metadata():
    """Verify every slot directory has a meta.yaml file"""
    slot_dirs = [d for d in Path('slots').iterdir() if d.is_dir() and d.name.startswith('slot')]

    missing_metadata = []
    for slot_dir in slot_dirs:
        meta_files = list(slot_dir.glob('*.meta.yaml'))
        if not meta_files:
            missing_metadata.append(slot_dir.name)

    assert not missing_metadata, (
        f"Slots missing meta.yaml: {missing_metadata}\n"
        f"Create <slotname>.meta.yaml for each slot with produces/consumes contracts"
    )


def test_metadata_contract_format():
    """Verify all contract names follow @VERSION format"""
    meta_files = list(Path('slots').rglob('*.meta.yaml'))

    invalid_contracts = []
    for meta_file in meta_files:
        with open(meta_file) as f:
            data = yaml.safe_load(f)

        for contract in data.get('produces', []) + data.get('consumes', []):
            if '@' not in contract:
                invalid_contracts.append((meta_file.name, contract))

    assert not invalid_contracts, (
        f"Contracts not following @VERSION format: {invalid_contracts}\n"
        f"Expected format: CONTRACT_NAME@VERSION (e.g., TRI_REPORT@1)"
    )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
