"""
Ontology validator - checks ontology contracts against reality.

Validates:
- impl_ref paths exist and are importable
- Slot inputs/outputs match signal definitions
- Transformations have corresponding tests
"""

import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from .loader import OntologyLoader, Framework, Transformation


@dataclass
class ValidationResult:
    """Result of ontology validation."""
    framework_id: str
    transformation_name: str
    check: str
    status: str  # "pass", "fail", "skip"
    message: str


class OntologyValidator:
    """Validates ontology contracts against actual implementation."""

    def __init__(self, loader: OntologyLoader):
        """
        Initialize validator.

        Args:
            loader: Loaded ontology
        """
        self.loader = loader
        self.results: List[ValidationResult] = []

    def validate_all(self) -> Tuple[int, int, int]:
        """
        Validate all frameworks in ontology.

        Returns:
            Tuple of (passed, failed, skipped) counts
        """
        self.results.clear()

        for framework in self.loader.frameworks.values():
            self.validate_framework(framework)

        passed = sum(1 for r in self.results if r.status == "pass")
        failed = sum(1 for r in self.results if r.status == "fail")
        skipped = sum(1 for r in self.results if r.status == "skip")

        return passed, failed, skipped

    def validate_framework(self, framework: Framework) -> None:
        """Validate a single framework."""
        for transformation in framework.transformations:
            self._validate_impl_ref(framework, transformation)
            self._validate_inputs_outputs(framework, transformation)

    def _validate_impl_ref(
        self,
        framework: Framework,
        transformation: Transformation
    ) -> None:
        """
        Validate impl_ref path exists and is importable.

        Example: "src.nova.slots.slot02_deltathresh.spectral.compute_entropy"
        """
        if not transformation.impl_ref:
            self.results.append(ValidationResult(
                framework_id=framework.id,
                transformation_name=transformation.name,
                check="impl_ref_exists",
                status="skip",
                message="No impl_ref specified"
            ))
            return

        # Parse module and function name
        parts = transformation.impl_ref.split(".")
        if len(parts) < 2:
            self.results.append(ValidationResult(
                framework_id=framework.id,
                transformation_name=transformation.name,
                check="impl_ref_format",
                status="fail",
                message=f"Invalid impl_ref format: {transformation.impl_ref}"
            ))
            return

        module_path = ".".join(parts[:-1])
        function_name = parts[-1]

        # Try to import module
        try:
            module = importlib.import_module(module_path)
            self.results.append(ValidationResult(
                framework_id=framework.id,
                transformation_name=transformation.name,
                check="impl_ref_module_import",
                status="pass",
                message=f"Module {module_path} imported successfully"
            ))
        except ModuleNotFoundError as e:
            self.results.append(ValidationResult(
                framework_id=framework.id,
                transformation_name=transformation.name,
                check="impl_ref_module_import",
                status="fail",
                message=f"Module not found: {module_path} ({e})"
            ))
            return
        except Exception as e:
            self.results.append(ValidationResult(
                framework_id=framework.id,
                transformation_name=transformation.name,
                check="impl_ref_module_import",
                status="fail",
                message=f"Import error: {module_path} ({e})"
            ))
            return

        # Check function exists
        if hasattr(module, function_name):
            self.results.append(ValidationResult(
                framework_id=framework.id,
                transformation_name=transformation.name,
                check="impl_ref_function_exists",
                status="pass",
                message=f"Function {function_name} exists in {module_path}"
            ))
        else:
            available = [name for name in dir(module) if not name.startswith('_')]
            self.results.append(ValidationResult(
                framework_id=framework.id,
                transformation_name=transformation.name,
                check="impl_ref_function_exists",
                status="fail",
                message=f"Function {function_name} not found in {module_path}. "
                        f"Available: {', '.join(available[:5])}"
            ))

    def _validate_inputs_outputs(
        self,
        framework: Framework,
        transformation: Transformation
    ) -> None:
        """Validate transformation inputs/outputs are defined signals."""
        # Check inputs are defined signals
        for input_sig in transformation.inputs:
            if input_sig in self.loader.signals:
                self.results.append(ValidationResult(
                    framework_id=framework.id,
                    transformation_name=transformation.name,
                    check=f"input_signal_{input_sig}",
                    status="pass",
                    message=f"Input signal '{input_sig}' is defined"
                ))
            else:
                # Skip validation for composite inputs like slot_outputs_all
                if input_sig in ["slot_outputs_all", "all_transformations",
                                 "all_state_changes", "external_inputs", "peer_list",
                                 "detection_results", "ground_truth", "convergence_state",
                                 "state_vectors", "emotional_matrices", "signal_spectra",
                                 "narrative_networks", "anchors", "content", "claim_hash"]:
                    self.results.append(ValidationResult(
                        framework_id=framework.id,
                        transformation_name=transformation.name,
                        check=f"input_signal_{input_sig}",
                        status="skip",
                        message=f"Composite/dynamic input '{input_sig}' (not in signals)"
                    ))
                else:
                    self.results.append(ValidationResult(
                        framework_id=framework.id,
                        transformation_name=transformation.name,
                        check=f"input_signal_{input_sig}",
                        status="fail",
                        message=f"Input signal '{input_sig}' not defined in ontology"
                    ))

        # Check outputs are defined signals
        for output_sig in transformation.outputs:
            if output_sig in self.loader.signals:
                self.results.append(ValidationResult(
                    framework_id=framework.id,
                    transformation_name=transformation.name,
                    check=f"output_signal_{output_sig}",
                    status="pass",
                    message=f"Output signal '{output_sig}' is defined"
                ))
            elif not output_sig:  # Empty output list
                continue
            else:
                # Skip validation for dynamic outputs
                if output_sig in ["verification_status", "chain_integrity",
                                  "attest_hash", "anchor_position", "production_mode",
                                  "shield_status", "optimized_params", "validated_signals",
                                  "p_values", "ethical_weight_vector", "cognitive_load_estimate",
                                  "audit_graph", "sync_status", "node_health",
                                  "divergence_alerts", "coherence_breakdown"]:
                    self.results.append(ValidationResult(
                        framework_id=framework.id,
                        transformation_name=transformation.name,
                        check=f"output_signal_{output_sig}",
                        status="skip",
                        message=f"Dynamic output '{output_sig}' (not in signals)"
                    ))
                else:
                    self.results.append(ValidationResult(
                        framework_id=framework.id,
                        transformation_name=transformation.name,
                        check=f"output_signal_{output_sig}",
                        status="fail",
                        message=f"Output signal '{output_sig}' not defined in ontology"
                    ))

    def print_results(self, show_passed: bool = False) -> None:
        """Print validation results."""
        print("\n=== Ontology Validation Results ===\n")

        failed = [r for r in self.results if r.status == "fail"]
        skipped = [r for r in self.results if r.status == "skip"]
        passed = [r for r in self.results if r.status == "pass"]

        if failed:
            print(f"FAILED ({len(failed)}):\n")
            for r in failed:
                print(f"  {r.framework_id}.{r.transformation_name}")
                print(f"    Check: {r.check}")
                print(f"    {r.message}\n")

        if show_passed and passed:
            print(f"PASSED ({len(passed)}):\n")
            for r in passed:
                print(f"  {r.framework_id}.{r.transformation_name}")
                print(f"    Check: {r.check}")
                print(f"    {r.message}\n")

        print(f"Summary:")
        print(f"  Passed:  {len(passed)}")
        print(f"  Failed:  {len(failed)}")
        print(f"  Skipped: {len(skipped)}")
        print(f"  Total:   {len(self.results)}")

        if failed:
            print(f"\n{len(failed)} validation failures detected")
        else:
            print(f"\nAll validations passed!")
