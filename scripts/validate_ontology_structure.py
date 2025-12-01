#!/usr/bin/env python3
"""
Structural Validation for Nova Ontology Hierarchy - Phase 11 Step B

Validates:
1. Parent-child refinement rules (children refine, never broaden)
2. Monotonic constraint propagation (invariants flow downward)
3. Semantic preservation (no redefinition of primitives)
4. Lineage metadata consistency (parents, versions, imports)

Usage:
    python scripts/validate_ontology_structure.py
    python scripts/validate_ontology_structure.py --verbose
    python scripts/validate_ontology_structure.py --ontology docs/architecture/ontology/specs/nova.slot03@1.0.yaml
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import yaml


class OntologyValidator:
    """Validates structural properties of Nova ontology hierarchy."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.specs_dir = repo_root / "docs" / "architecture" / "ontology" / "specs"
        self.contracts_dir = repo_root / "contracts"
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.ontologies: Dict[str, Dict] = {}

    def load_ontology(self, path: Path) -> Optional[Dict]:
        """Load YAML ontology file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.errors.append(f"Failed to load {path}: {e}")
            return None

    def discover_ontologies(self) -> None:
        """Discover all ontology files in specs/."""
        for yaml_file in self.specs_dir.glob("nova*.yaml"):
            ontology = self.load_ontology(yaml_file)
            if ontology and "meta" in ontology:
                ontology_id = ontology["meta"].get("id", yaml_file.stem)
                self.ontologies[ontology_id] = {
                    "path": yaml_file,
                    "data": ontology
                }

    def validate_lineage_metadata(self) -> None:
        """Validate lineage metadata (parents, versions, imports)."""
        print("\n=== Validating Lineage Metadata ===")

        for ont_id, ont_info in self.ontologies.items():
            data = ont_info["data"]
            meta = data.get("meta", {})

            # Check required meta fields
            required_fields = ["id", "version", "status"]
            for field in required_fields:
                if field not in meta:
                    self.errors.append(f"{ont_id}: Missing required meta.{field}")

            # Check version format (x.y.z)
            version = meta.get("version", "")
            if version:
                parts = version.split(".")
                if len(parts) != 3 or not all(p.isdigit() for p in parts):
                    self.warnings.append(f"{ont_id}: Version {version} not in semver format (x.y.z)")

            # Check parents exist
            parents = meta.get("parents", [])
            for parent in parents:
                parent_id = parent.split("@")[0]  # Strip version if present
                if parent_id not in self.ontologies:
                    self.warnings.append(f"{ont_id}: Parent {parent_id} not found in ontology set")

            # Check imports match parents
            imports = data.get("imports", [])
            parent_ids = [p.split("@")[0] for p in parents]
            import_ids = [i.split("@")[0] for i in imports]

            if set(parent_ids) != set(import_ids):
                missing_imports = set(parent_ids) - set(import_ids)
                extra_imports = set(import_ids) - set(parent_ids)
                if missing_imports:
                    self.errors.append(f"{ont_id}: Parents {missing_imports} not in imports")
                if extra_imports:
                    self.warnings.append(f"{ont_id}: Imports {extra_imports} not in parents")

    def validate_acyclic_imports(self) -> None:
        """Validate import graph is acyclic (DAG)."""
        print("\n=== Validating Acyclic Import Graph ===")

        # Build import graph
        graph: Dict[str, Set[str]] = {}
        for ont_id, ont_info in self.ontologies.items():
            imports = ont_info["data"].get("imports", [])
            import_ids = {i.split("@")[0] for i in imports}
            graph[ont_id] = import_ids

        # Detect cycles using DFS
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def has_cycle(node: str, path: List[str]) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, set()):
                if neighbor not in visited:
                    if has_cycle(neighbor, path):
                        return True
                elif neighbor in rec_stack:
                    cycle_path = path[path.index(neighbor):] + [neighbor]
                    self.errors.append(f"Cyclic import detected: {' → '.join(cycle_path)}")
                    return True

            path.pop()
            rec_stack.remove(node)
            return False

        for ont_id in graph:
            if ont_id not in visited:
                has_cycle(ont_id, [])

    def validate_monotonic_constraints(self) -> None:
        """Validate constraints propagate monotonically (children don't relax parent constraints)."""
        print("\n=== Validating Monotonic Constraint Propagation ===")

        # Check min_duration_s constraints (Operating Ontology → children)
        operating = self.ontologies.get("nova.operating")
        if not operating:
            self.warnings.append("nova.operating not found - skipping min_duration validation")
            return

        operating_min_durations = operating["data"].get("transitions", {}).get("min_duration_s", {})

        for ont_id, ont_info in self.ontologies.items():
            if ont_id == "nova.operating":
                continue

            data = ont_info["data"]
            parents = data.get("meta", {}).get("parents", [])

            # Check if this ontology imports nova.operating
            if not any("nova.operating" in p for p in parents):
                continue

            # Check regime min_durations if defined
            regimes = data.get("regimes", {})
            for regime_name, regime_data in regimes.items():
                child_min_dur = regime_data.get("min_duration_s")
                parent_min_dur = operating_min_durations.get(regime_name)

                if child_min_dur is not None and parent_min_dur is not None:
                    if child_min_dur < parent_min_dur:
                        self.errors.append(
                            f"{ont_id}: regime '{regime_name}' min_duration_s={child_min_dur} "
                            f"violates parent constraint min_duration_s={parent_min_dur} "
                            f"(children cannot reduce durations)"
                        )

    def validate_amplitude_bounds(self) -> None:
        """Validate amplitude multipliers stay within global safety envelope."""
        print("\n=== Validating Amplitude Bounds ===")

        # Get global bounds from transformation_geometry@1
        tg_path = self.contracts_dir / "transformation_geometry@1.yaml"
        tg_contract = self.load_ontology(tg_path)
        if not tg_contract:
            self.warnings.append("transformation_geometry@1.yaml not found - skipping amplitude validation")
            return

        global_bounds = tg_contract.get("amplitude_bounds", {}).get("global", {})
        eta_bounds = global_bounds.get("eta_scaled", [0.25, 1.0])
        emotion_bounds = global_bounds.get("emotion", [0.5, 1.0])
        sensitivity_bounds = global_bounds.get("sensitivity", [1.0, 1.5])

        # Check all ontologies with amplitude_triad
        for ont_id, ont_info in self.ontologies.items():
            amplitude_triad = ont_info["data"].get("amplitude_triad", {})

            for regime, values in amplitude_triad.items():
                # Check eta
                eta_scale = values.get("governor_eta_scale")
                if isinstance(eta_scale, list) and len(eta_scale) == 2:
                    if eta_scale[0] < eta_bounds[0] or eta_scale[1] > eta_bounds[1]:
                        self.errors.append(
                            f"{ont_id}: regime '{regime}' governor_eta_scale {eta_scale} "
                            f"exceeds global bounds {eta_bounds}"
                        )

                # Check emotion
                emotion = values.get("emotion_constriction")
                if isinstance(emotion, (int, float)):
                    if emotion < emotion_bounds[0] or emotion > emotion_bounds[1]:
                        self.errors.append(
                            f"{ont_id}: regime '{regime}' emotion_constriction {emotion} "
                            f"exceeds global bounds {emotion_bounds}"
                        )
                elif isinstance(emotion, list) and len(emotion) == 2:
                    if emotion[0] < emotion_bounds[0] or emotion[1] > emotion_bounds[1]:
                        self.errors.append(
                            f"{ont_id}: regime '{regime}' emotion_constriction {emotion} "
                            f"exceeds global bounds {emotion_bounds}"
                        )

                # Check sensitivity
                sensitivity = values.get("slot09_sensitivity_multiplier")
                if isinstance(sensitivity, (int, float)):
                    if sensitivity < sensitivity_bounds[0] or sensitivity > sensitivity_bounds[1]:
                        self.errors.append(
                            f"{ont_id}: regime '{regime}' sensitivity {sensitivity} "
                            f"exceeds global bounds {sensitivity_bounds}"
                        )
                elif isinstance(sensitivity, list) and len(sensitivity) == 2:
                    if sensitivity[0] < sensitivity_bounds[0] or sensitivity[1] > sensitivity_bounds[1]:
                        self.errors.append(
                            f"{ont_id}: regime '{regime}' sensitivity {sensitivity} "
                            f"exceeds global bounds {sensitivity_bounds}"
                        )

    def validate_semantic_preservation(self) -> None:
        """Validate children don't redefine parent primitives."""
        print("\n=== Validating Semantic Preservation ===")

        # Get Mother Ontology primitives
        frameworks = self.ontologies.get("nova.frameworks")
        if not frameworks:
            self.warnings.append("nova.frameworks not found - skipping semantic validation")
            return

        # Extract signal names from frameworks
        frameworks_data = frameworks["data"]
        mother_signals = set()

        # Collect signal IDs from coordination_frameworks
        coord_frameworks = frameworks_data.get("coordination_frameworks", [])
        for fw in coord_frameworks:
            mother_signals.add(fw.get("id"))

        # Check children don't redefine these primitives
        for ont_id, ont_info in self.ontologies.items():
            if ont_id == "nova.frameworks":
                continue

            data = ont_info["data"]

            # Check if any frameworks are redefined
            child_frameworks = data.get("coordination_frameworks", [])
            for fw in child_frameworks:
                fw_id = fw.get("id")
                if fw_id in mother_signals:
                    self.warnings.append(
                        f"{ont_id}: Redefines framework '{fw_id}' from parent "
                        f"(children should extend, not redefine)"
                    )

    def validate_all(self) -> bool:
        """Run all validation checks."""
        print("=" * 60)
        print("Nova Ontology Structural Validation - Phase 11 Step B")
        print("=" * 60)

        self.discover_ontologies()
        print(f"\nDiscovered {len(self.ontologies)} ontologies:")
        for ont_id in sorted(self.ontologies.keys()):
            print(f"  - {ont_id}")

        self.validate_lineage_metadata()
        self.validate_acyclic_imports()
        self.validate_monotonic_constraints()
        self.validate_amplitude_bounds()
        self.validate_semantic_preservation()

        # Print results
        print("\n" + "=" * 60)
        print("VALIDATION RESULTS")
        print("=" * 60)

        if self.errors:
            print(f"\n[ERRORS] ({len(self.errors)}):")
            for error in self.errors:
                print(f"  - {error}")

        if self.warnings:
            print(f"\n[WARNINGS] ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  - {warning}")

        if not self.errors and not self.warnings:
            print("\n[PASS] All validation checks passed!")
        elif not self.errors:
            print(f"\n[PASS] No errors (but {len(self.warnings)} warnings)")

        return len(self.errors) == 0


def main():
    parser = argparse.ArgumentParser(
        description="Validate Nova ontology hierarchy structure"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--ontology",
        type=Path,
        help="Validate specific ontology file"
    )

    args = parser.parse_args()

    # Find repo root
    repo_root = Path(__file__).parent.parent

    validator = OntologyValidator(repo_root)
    success = validator.validate_all()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
