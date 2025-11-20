"""
Contract auditor and ontology coherence checker.

Usage:
    python scripts/contract_audit.py [--strict-unused]

The script loads all contract definitions from `contracts/*.yaml`,
verifies basic invariants (unique IDs, version alignment, slot metadata),
then cross-checks that every contract referenced in the ontology
(`specs/nova_framework_ontology.v1.yaml`) and `contracts/slot_map.json`
has a corresponding definition.

Warnings are emitted for contracts that are defined but unused; these can be
promoted to hard failures via `--strict-unused`.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set

import yaml

CONTRACT_ID_PATTERN = re.compile(r"[A-Za-z0-9_.-]+@\d+")
ROOT = Path(__file__).resolve().parents[1]
CONTRACTS_DIR = ROOT / "contracts"
ONTOLOGY_PATH = ROOT / "specs" / "nova_framework_ontology.v1.yaml"
SLOT_MAP_PATH = CONTRACTS_DIR / "slot_map.json"
LEGACY_EXTERNAL_CONTRACTS = {
    "CONSTELLATION_STATE@1",
    "CONTENT_ANALYSIS@1",
    "CONTROL_CMDS@1",
    "CULTURAL_PROFILE@1",
    "DELTA_THREAT@1",
    "DISTORTION_DETECTION@1",
    "EMOTION_REPORT@1",
    "EMO_FEEDBACK@1",
    "MEMORY_ETHICS@1",
    "PLAN_WITH_CONSENT@1",
    "PRODUCTION_CONTROL@1",
    "SIGNALS@1",
    "TRI_REPORT@1",
}


@dataclass(frozen=True)
class ContractDefinition:
    contract_id: str
    version: str | None
    path: Path
    slots: List[Dict[str, Any]]


def load_contract_definitions() -> Dict[str, ContractDefinition]:
    contracts: Dict[str, ContractDefinition] = {}
    for path in sorted(CONTRACTS_DIR.glob("*.yaml")):
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        contract_id = str(data.get("contract_id") or path.stem)
        version = str(data.get("version")).strip() if data.get("version") else None
        slots = data.get("slots") or []
        if contract_id in contracts:
            raise RuntimeError(f"Duplicate contract_id detected: {contract_id} ({path})")
        contracts[contract_id] = ContractDefinition(
            contract_id=contract_id,
            version=version,
            path=path,
            slots=slots,
        )
    return contracts


def _collect_contract_refs_from_obj(obj: Any, refs: Set[str]) -> None:
    if isinstance(obj, str):
        if CONTRACT_ID_PATTERN.fullmatch(obj):
            refs.add(obj)
    elif isinstance(obj, dict):
        for value in obj.values():
            _collect_contract_refs_from_obj(value, refs)
    elif isinstance(obj, list):
        for item in obj:
            _collect_contract_refs_from_obj(item, refs)


def load_ontology_contract_refs() -> Set[str]:
    if not ONTOLOGY_PATH.exists():
        return set()
    with ONTOLOGY_PATH.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    refs: Set[str] = set()
    for section in ("frameworks", "coordination_frameworks"):
        _collect_contract_refs_from_obj(data.get(section, []), refs)
    return refs


def load_slot_map_refs() -> Set[str]:
    if not SLOT_MAP_PATH.exists():
        return set()
    with SLOT_MAP_PATH.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    refs: Set[str] = set()
    for slot in data.get("slots", []):
        contracts = slot.get("contracts") or {}
        for direction in ("produces", "consumes"):
            for contract_id in contracts.get(direction, []):
                refs.add(contract_id)
    return refs


def check_version_alignment(contract: ContractDefinition) -> List[str]:
    issues: List[str] = []
    contract_id = contract.contract_id
    if "@" in contract_id and contract.version:
        suffix = contract_id.rsplit("@", 1)[1]
        if suffix.isdigit():
            expected_major = int(suffix)
            declared_major_str = contract.version.split(".", 1)[0]
            if declared_major_str.isdigit():
                declared_major = int(declared_major_str)
                if declared_major != expected_major:
                    issues.append(
                        f"{contract_id}: version '{contract.version}' mismatches '@{expected_major}' suffix "
                        f"(defined at {contract.path})"
                    )
    return issues


def ensure_slots_defined(contract: ContractDefinition) -> List[str]:
    warnings: List[str] = []
    if not contract.slots:
        warnings.append(f"{contract.contract_id}: no slots defined in {contract.path}")
    return warnings


def audit_contracts(strict_unused: bool) -> int:
    exit_code = 0
    contracts = load_contract_definitions()
    ontology_refs = load_ontology_contract_refs()
    slot_map_refs = load_slot_map_refs()
    referenced_contracts = ontology_refs | slot_map_refs

    hard_failures: List[str] = []
    warnings: List[str] = []

    for contract in contracts.values():
        hard_failures.extend(check_version_alignment(contract))
        warnings.extend(ensure_slots_defined(contract))

    missing_defs = sorted(
        refenced
        for refenced in referenced_contracts
        if refenced not in contracts and refenced not in LEGACY_EXTERNAL_CONTRACTS
    )
    if missing_defs:
        hard_failures.append(
            "Contracts referenced in ontology/slot_map without definitions: "
            + ", ".join(missing_defs)
        )

    legacy_gaps = sorted(
        refenced for refenced in referenced_contracts if refenced in LEGACY_EXTERNAL_CONTRACTS and refenced not in contracts
    )
    if legacy_gaps:
        warnings.append(
            "Legacy contracts referenced without local definitions (allowlisted): "
            + ", ".join(legacy_gaps)
        )

    unused_contracts = sorted(cid for cid in contracts if cid not in referenced_contracts)
    if unused_contracts:
        message = "Contracts defined but not referenced in ontology or slot_map: " + ", ".join(unused_contracts)
        if strict_unused:
            hard_failures.append(message)
        else:
            warnings.append(message)

    if hard_failures:
        exit_code = 1
        print("Contract audit failed:")
        for failure in hard_failures:
            print(f"  - {failure}")
    else:
        print(f"Contract audit passed: {len(contracts)} definitions checked.")

    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"  - {warning}")

    return exit_code


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate contract definitions against ontology and slot map.")
    parser.add_argument(
        "--strict-unused",
        action="store_true",
        help="Treat unused contracts as errors instead of warnings.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        return audit_contracts(strict_unused=args.strict_unused)
    except Exception as exc:  # pragma: no cover - defensive
        print(f"Contract audit encountered an error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
