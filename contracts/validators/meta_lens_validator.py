"""Fast JSON schema validator for META_LENS_REPORT@1."""

import json
from pathlib import Path
from typing import Dict, Any, Optional
import fastjsonschema


class MetaLensValidator:
    """Fast validator for META_LENS_REPORT@1 schema."""

    def __init__(self):
        """Initialize validator with compiled schema."""
        schema_path = Path(__file__).parent.parent / "meta_lens_report@1.json"
        with open(schema_path) as f:
            schema = json.load(f)

        self._validate_func = fastjsonschema.compile(schema)
        self._schema = schema

    def validate(self, report: Dict[str, Any]) -> bool:
        """
        Validate META_LENS_REPORT@1 instance.

        Args:
            report: Report instance to validate

        Returns:
            True if valid

        Raises:
            fastjsonschema.JsonSchemaException: If validation fails
        """
        self._validate_func(report)
        return True

    def validate_safe(self, report: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Safe validation that returns error message instead of raising.

        Args:
            report: Report instance to validate

        Returns:
            (is_valid, error_message)
        """
        try:
            self._validate_func(report)
            return True, None
        except Exception as e:
            return False, str(e)

    def validate_state_vector(self, state_vector: list) -> bool:
        """
        Validate state vector specifically.

        Args:
            state_vector: 6-element array [independence_score, cross_family_resonance,
                         narrative_invisibility, cultural_synthesis_confidence,
                         risk_overall, emotional_volatility]

        Returns:
            True if valid

        Raises:
            ValueError: If invalid
        """
        if not isinstance(state_vector, list):
            raise ValueError("State vector must be a list")

        if len(state_vector) != 6:
            raise ValueError("State vector must have exactly 6 elements")

        for i, value in enumerate(state_vector):
            if not isinstance(value, (int, float)):
                raise ValueError(f"State vector element {i} must be numeric")

            if not (0.0 <= value <= 1.0):
                raise ValueError(f"State vector element {i} must be in range [0.0, 1.0]")

        return True

    def validate_convergence(self, iteration: Dict[str, Any]) -> bool:
        """
        Validate iteration/convergence parameters.

        Args:
            iteration: Iteration object from report

        Returns:
            True if valid

        Raises:
            ValueError: If invalid
        """
        required_fields = ["epoch", "max_iters", "alpha", "epsilon", "converged", "residual"]
        for field in required_fields:
            if field not in iteration:
                raise ValueError(f"Missing required iteration field: {field}")

        # Validate ranges
        if not (0 <= iteration["epoch"] <= iteration["max_iters"]):
            raise ValueError("Epoch must be <= max_iters")

        if not (0.0 < iteration["alpha"] <= 1.0):
            raise ValueError("Alpha must be in range (0.0, 1.0]")

        if not (0.0 <= iteration["epsilon"] <= 0.1):
            raise ValueError("Epsilon must be in range [0.0, 0.1]")

        if not (0.0 <= iteration["residual"] <= 1.0):
            raise ValueError("Residual must be in range [0.0, 1.0]")

        # Logical consistency
        if iteration["converged"] and iteration["residual"] > iteration["epsilon"]:
            raise ValueError("Cannot be converged with residual > epsilon")

        return True

    @property
    def schema(self) -> Dict[str, Any]:
        """Get the raw schema."""
        return self._schema


# Convenience functions
_validator_instance = None

def get_validator() -> MetaLensValidator:
    """Get singleton validator instance."""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = MetaLensValidator()
    return _validator_instance


def validate_meta_lens_report(report: Dict[str, Any]) -> bool:
    """Validate META_LENS_REPORT@1 instance (convenience function)."""
    return get_validator().validate(report)


def validate_meta_lens_report_safe(report: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Safe validation with error message (convenience function)."""
    return get_validator().validate_safe(report)