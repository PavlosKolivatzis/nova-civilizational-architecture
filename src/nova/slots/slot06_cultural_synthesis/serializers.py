from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict

from .engine import SynthesisResult


def synthesis_result_to_dict(res: SynthesisResult) -> Dict[str, Any]:
    try:
        return {
            "simulation_status": res.simulation_status.value,
            "cultural_profile": asdict(res.cultural_profile),
            "compliance_score": res.compliance_score,
            "violations": res.violations,
            "recommendations": res.recommendations,
        }
    except Exception:
        return {"error": "Serialization failed"}
