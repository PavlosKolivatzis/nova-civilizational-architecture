"""
Ontology loader - parses docs/architecture/ontology/specs/nova_framework_ontology.v1.yaml.

Validates:
- YAML structure
- Required sections (meta, signals, frameworks, ledgers, validation)
- Signal type definitions
- Framework transformation contracts
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class Signal:
    """Signal definition from ontology."""
    name: str
    type: str
    desc: str
    range: Optional[List] = None
    shape: Optional[List] = None
    formula: Optional[str] = None
    validation: Optional[Dict[str, Any]] = None


@dataclass
class Transformation:
    """Transformation within a framework."""
    name: str
    inputs: List[str]
    outputs: List[str]
    rule: str
    impl_ref: Optional[str] = None
    validation: Optional[Dict[str, Any]] = None


@dataclass
class Framework:
    """Framework definition from ontology."""
    id: str
    name: str
    purpose: str
    slot_id: Optional[int]
    inputs: List[str]
    outputs: List[str]
    transformations: List[Transformation]
    state_variables: Optional[List[str]] = None
    interfaces: Optional[Dict[str, List[str]]] = None


class OntologyLoader:
    """Loads and parses Nova Framework Ontology YAML."""

    def __init__(self, ontology_path: Optional[Path] = None):
        """
        Initialize loader.

        Args:
            ontology_path: Path to ontology YAML. Defaults to docs/architecture/ontology/specs/nova_framework_ontology.v1.yaml
        """
        if ontology_path is None:
            repo_root = Path(__file__).parent.parent.parent.parent
            ontology_path = repo_root / "docs" / "architecture" / "ontology" / "specs" / "nova_framework_ontology.v1.yaml"

        self.ontology_path = ontology_path
        self._raw: Optional[Dict[str, Any]] = None
        self._signals: Optional[Dict[str, Signal]] = None
        self._frameworks: Optional[Dict[str, Framework]] = None

    def load(self) -> Dict[str, Any]:
        """
        Load and parse ontology YAML.

        Returns:
            Parsed ontology dictionary

        Raises:
            FileNotFoundError: If ontology file doesn't exist
            yaml.YAMLError: If YAML is malformed
            ValueError: If required sections missing
        """
        if not self.ontology_path.exists():
            raise FileNotFoundError(f"Ontology not found: {self.ontology_path}")

        with open(self.ontology_path, 'r', encoding='utf-8') as f:
            self._raw = yaml.safe_load(f)

        self._validate_structure()
        self._parse_signals()
        self._parse_frameworks()

        return self._raw

    def _validate_structure(self) -> None:
        """Validate ontology has required top-level sections."""
        required = ["meta", "signals", "ledgers", "frameworks", "validation"]
        missing = [s for s in required if s not in self._raw]

        if missing:
            raise ValueError(f"Ontology missing required sections: {missing}")

        # Validate meta
        meta = self._raw["meta"]
        required_meta = ["name", "version", "scientific_foundation"]
        missing_meta = [m for m in required_meta if m not in meta]
        if missing_meta:
            raise ValueError(f"Ontology meta missing fields: {missing_meta}")

    def _parse_signals(self) -> None:
        """Parse signal definitions into Signal objects."""
        self._signals = {}
        signals_raw = self._raw.get("signals", {})

        for sig_name, sig_def in signals_raw.items():
            if isinstance(sig_def, dict):
                self._signals[sig_name] = Signal(
                    name=sig_name,
                    type=sig_def.get("type", "Unknown"),
                    desc=sig_def.get("desc", ""),
                    range=sig_def.get("range"),
                    shape=sig_def.get("shape"),
                    formula=sig_def.get("formula") or sig_def.get("formula_raw"),
                    validation=sig_def.get("validation")
                )

    def _parse_frameworks(self) -> None:
        """Parse framework definitions into Framework objects."""
        self._frameworks = {}
        frameworks_raw = self._raw.get("frameworks", [])

        for fw_raw in frameworks_raw:
            transformations = []
            for trans_raw in fw_raw.get("transformations", []):
                transformations.append(Transformation(
                    name=trans_raw["name"],
                    inputs=trans_raw.get("in", []),
                    outputs=trans_raw.get("out", []),
                    rule=trans_raw.get("rule", ""),
                    impl_ref=trans_raw.get("impl_ref"),
                    validation=trans_raw.get("validation")
                ))

            framework = Framework(
                id=fw_raw["id"],
                name=fw_raw["name"],
                purpose=fw_raw["purpose"],
                slot_id=fw_raw.get("slot_id"),
                inputs=fw_raw.get("inputs", []),
                outputs=fw_raw.get("outputs", []),
                transformations=transformations,
                state_variables=fw_raw.get("state_variables"),
                interfaces=fw_raw.get("interfaces")
            )

            self._frameworks[framework.id] = framework

    @property
    def signals(self) -> Dict[str, Signal]:
        """Get parsed signal definitions."""
        if self._signals is None:
            raise RuntimeError("Must call load() before accessing signals")
        return self._signals

    @property
    def frameworks(self) -> Dict[str, Framework]:
        """Get parsed framework definitions."""
        if self._frameworks is None:
            raise RuntimeError("Must call load() before accessing frameworks")
        return self._frameworks

    def get_framework(self, framework_id: str) -> Optional[Framework]:
        """Get framework by ID."""
        return self.frameworks.get(framework_id)

    def get_signal(self, signal_name: str) -> Optional[Signal]:
        """Get signal by name."""
        return self.signals.get(signal_name)
