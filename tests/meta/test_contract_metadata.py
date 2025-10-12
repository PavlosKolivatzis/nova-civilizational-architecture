"""
Test contract metadata completeness.

Validates that all flow fabric contracts have metadata declarations.
Prevents DEF-001 (contract metadata gap).
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import pytest
import yaml


META_PATTERNS: tuple[str, ...] = ("*.meta.yaml", "*.meta.yml", "meta.yaml", "meta.yml")


def _iter_slot_meta_files() -> list[Path]:
    """Return every slot metadata file regardless of naming convention."""
    roots = [Path("slots"), Path("src") / "nova" / "slots"]
    seen: set[Path] = set()
    meta_files: list[Path] = []

    for slot_root in roots:
        if not slot_root.exists():
            continue
        for pattern in META_PATTERNS:
            for meta_path in slot_root.rglob(pattern):
                if not meta_path.is_file():
                    continue
                resolved = meta_path.resolve()
                if resolved in seen:
                    continue
                seen.add(resolved)
                meta_files.append(meta_path)

    if not meta_files:
        pytest.fail("No slot metadata files discovered under 'slots/' or 'src/nova/slots/'")

    meta_files.sort(key=lambda path: str(path))
    return meta_files


def _load_metadata(meta_path: Path) -> dict[str, object]:
    """Load YAML metadata, guaranteeing a mapping result."""
    with meta_path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    if not isinstance(data, dict):
        pytest.fail(f"Metadata file {meta_path} must contain a mapping, got {type(data).__name__}")

    return data


def _contract_list(meta_path: Path, data: dict[str, object], key: str) -> list[str]:
    """Extract a list of contracts for the given key with robust validation."""
    value = data.get(key, [])
    if value in (None, ""):
        return []
    if isinstance(value, str):
        pytest.fail(f"{meta_path} has '{key}' defined as a string; expected a list of contracts")
    if not isinstance(value, list):
        pytest.fail(f"{meta_path} has non-list '{key}' field: {value!r}")

    non_strings = [item for item in value if not isinstance(item, str)]
    if non_strings:
        pytest.fail(f"{meta_path} '{key}' contains non-string entries: {non_strings}")

    return value


def test_all_flow_fabric_contracts_have_metadata():
    """Verify every KNOWN_CONTRACTS entry has produces/consumes in meta.yaml."""
    from orchestrator.flow_fabric_init import KNOWN_CONTRACTS

    meta_files = _iter_slot_meta_files()
    assert meta_files, "No slot metadata files discovered under 'slots/'"

    all_produces: set[str] = set()
    for meta_file in meta_files:
        data = _load_metadata(meta_file)
        all_produces.update(_contract_list(meta_file, data, "produces"))

    missing = [contract for contract in KNOWN_CONTRACTS if contract not in all_produces]
    assert not missing, (
        "Contracts declared in orchestrator/flow_fabric_init.py but missing from slot"
        " metadata: " + ", ".join(sorted(missing)) +
        "\nAdd missing contracts to the appropriate slot meta.yaml 'produces' section."
    )


def test_all_metadata_contracts_are_registered():
    """Verify every produces/consumes contract is registered in flow fabric."""
    from orchestrator.flow_fabric_init import KNOWN_CONTRACTS

    registered = set(KNOWN_CONTRACTS)
    referenced: set[str] = set()

    for meta_file in _iter_slot_meta_files():
        data = _load_metadata(meta_file)
        referenced.update(_contract_list(meta_file, data, "produces"))
        referenced.update(_contract_list(meta_file, data, "consumes"))

    unregistered = sorted(referenced - registered)
    assert not unregistered, (
        "Contracts referenced in slot metadata but missing from KNOWN_CONTRACTS: "
        + ", ".join(unregistered)
    )


def test_flow_fabric_slots_have_metadata():
    """Ensure each flow-fabric contract is linked to at least one slot metadata file."""
    from orchestrator.flow_fabric_init import KNOWN_CONTRACTS

    contract_to_slots: dict[str, set[str]] = defaultdict(set)

    for meta_file in _iter_slot_meta_files():
        slot_name = meta_file.parent.name
        data = _load_metadata(meta_file)
        produces = _contract_list(meta_file, data, "produces")
        consumes = _contract_list(meta_file, data, "consumes")

        for contract in produces + consumes:
            contract_to_slots[contract].add(slot_name)

    missing_contracts = [contract for contract in KNOWN_CONTRACTS if contract not in contract_to_slots]
    assert not missing_contracts, (
        "Flow fabric contracts are missing slot metadata associations: "
        + ", ".join(sorted(missing_contracts))
        + "\nEnsure each contract appears in at least one slot meta.yaml 'produces' or 'consumes'."
    )


def test_metadata_contract_format():
    """Verify all contract names follow CONTRACT@VERSION format."""
    invalid_contracts: list[tuple[str, str]] = []

    for meta_file in _iter_slot_meta_files():
        data = _load_metadata(meta_file)
        contracts = _contract_list(meta_file, data, "produces") + _contract_list(meta_file, data, "consumes")
        for contract in contracts:
            if "@" not in contract:
                invalid_contracts.append((str(meta_file), contract))

    assert not invalid_contracts, (
        "Contracts not following CONTRACT@VERSION format: "
        + "; ".join(f"{path} -> {contract}" for path, contract in invalid_contracts)
    )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
