"""Fixed-point meta-lens processor for structured epistemological analysis."""

import os
import math
from datetime import datetime, timezone
from hashlib import sha256
from typing import Dict, Any, List, Tuple, Callable, Optional


# Configuration constants - parametrized for production tuning
MAX_ITERS = max(1, min(10, int(os.getenv("META_LENS_MAX_ITERS", os.getenv("NOVA_META_LENS_MAX_ITERS", "3")))))
ALPHA = max(0.1, min(1.0, float(os.getenv("META_LENS_ALPHA", os.getenv("NOVA_META_LENS_ALPHA", "0.5")))))
EPSILON = max(0.001, min(0.1, float(os.getenv("META_LENS_EPSILON", os.getenv("NOVA_META_LENS_EPSILON", "0.02")))))


def _param(name, default, cast, lo=None, hi=None):
    """Load runtime parameter with type casting and bounds checking."""
    val = os.getenv(name, None)
    try:
        x = cast(val) if val is not None else default
    except Exception:
        x = default
    if lo is not None:
        x = max(lo, x)
    if hi is not None:
        x = min(hi, x)
    return x


def _load_iter_params():
    """Load iteration parameters at runtime for test flexibility."""
    return {
        "MAX_ITERS": _param("META_LENS_MAX_ITERS", 3, int, 1, 10),
        "ALPHA": _param("META_LENS_ALPHA", 0.5, float, 0.1, 1.0),
        "EPSILON": _param("META_LENS_EPSILON", 0.02, float, 0.001, 0.1),
    }


def vectorize(R: Dict[str, Any]) -> List[float]:
    """Extract state vector from report for convergence testing."""
    return R["meta_lens_analysis"]["state_vector"]


def l1_norm(a: List[float], b: List[float], ndigits: int = 12) -> float:
    """Stable L1 norm with deterministic rounding for tests."""
    s = math.fsum(abs(x - y) for x, y in zip(a, b))
    return round(s, ndigits)


def hash_report(R: Dict[str, Any]) -> str:
    """Generate SHA-256 hash of report for integrity."""
    # Remove integrity field to avoid circular hashing
    clean_report = {k: v for k, v in R.items() if k != "integrity"}
    report_str = str(sorted(clean_report.items()))
    return "sha256:" + sha256(report_str.encode("utf-8")).hexdigest()


def compute_once(
    state: Dict[str, Any],
    anchors: Optional[Dict[str, Any]],
    tri: Dict[str, Any],
    constellation: Dict[str, Any],
    culture: Dict[str, Any],
    distortion: Dict[str, Any],
    emotion: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Apply one iteration of the fixed-point operator F.

    State vector indices:
    0: independence_score
    1: cross_family_resonance
    2: narrative_invisibility
    3: cultural_synthesis_confidence
    4: risk_overall (monotone)
    5: emotional_volatility
    """
    v = state["meta_lens_analysis"]["state_vector"][:]
    v_new = v[:]

    # Update state vector components from slot outputs
    v_new[1] = tri.get("resonance_cross", v[1])                    # TRI cross-family
    v_new[2] = distortion.get("overall_score", v[2])               # INF-o-INITY
    v_new[3] = culture.get("synthesis_confidence", v[3])           # Slot-6
    v_new[4] = max(v[4], culture.get("risk_overall", 0.0))         # Monotone risk
    v_new[5] = emotion.get("volatility", v[5])                     # P.a.d.el/Slot-3

    # Apply damped update: R^(k+1) = (1-α)·R^(k) + α·F(R^(k))
    v_out = [(1 - ALPHA) * old + ALPHA * new for old, new in zip(v, v_new)]

    # Ensure bounds [0.0, 1.0]
    state["meta_lens_analysis"]["state_vector"] = [max(0.0, min(1.0, x)) for x in v_out]

    # Update associated fields
    state["meta_lens_analysis"]["manipulative_patterns"] = {
        "detected": distortion.get("patterns", []),
        "confidence": distortion.get("confidence", 0.0),
        "cross_validation_source": "INF-o-INITY"
    }

    state["meta_lens_analysis"]["cultural_overlay"] = {
        "historical_context": culture.get("historical_context", ""),
        "cultural_bias_markers": culture.get("bias_markers", []),
        "synthesis_confidence": culture.get("synthesis_confidence", 0.0)
    }

    state["risk_assessment"] = {
        "level": _risk_level_from_score(v_out[4]),
        "vectors": culture.get("risk_vectors", []),
        "mitigation_suggestions": culture.get("mitigation_suggestions", [])
    }

    return state


def _risk_level_from_score(risk_score: float) -> str:
    """Convert numeric risk score to categorical level."""
    if risk_score < 0.25:
        return "low"
    elif risk_score < 0.5:
        return "medium"
    elif risk_score < 0.75:
        return "high"
    else:
        return "critical"


def run_fixed_point(
    input_ref: str,
    base_state: Dict[str, Any],
    tri_fn: Callable,
    const_fn: Callable,
    culture_fn: Callable,
    distort_fn: Callable,
    emo_fn: Callable,
    lightclock_tick: int
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Run fixed-point iteration until convergence or budget exhaustion.

    Args:
        input_ref: Hash/ID of analyzed input
        base_state: Initial report state
        tri_fn: TRI computation function (Slot4)
        const_fn: Constellation mapping function (Slot5)
        culture_fn: Cultural synthesis function (Slot6)
        distort_fn: Distortion detection function (INF-o-INITY)
        emo_fn: Emotional analysis function (P.a.d.el)
        lightclock_tick: Current Light-Clock tick

    Returns:
        (final_report, epoch_snapshots)
    """
    # Load runtime parameters for test flexibility
    params = _load_iter_params()
    MAX_ITERS = params["MAX_ITERS"]
    ALPHA = params["ALPHA"]
    EPSILON = params["EPSILON"]

    R = dict(base_state)
    snapshots = []

    for k in range(1, MAX_ITERS + 1):
        # DAG flow: S2 → S4/S5 → S6 → integration
        tri = tri_fn(R)
        const = const_fn(R)
        culture = culture_fn(R, tri, const)
        distortion = distort_fn(R)
        emotion = emo_fn(R)

        # Watchdog: abort on high distortion or volatility
        distortion_score = distortion.get("overall_score", 0.0)
        emotion_volatility = emotion.get("volatility", 0.0)

        if distortion_score > 0.75 or emotion_volatility > 0.8:
            R["iteration"].update({
                "epoch": k,
                "converged": False,
                "residual": 1.0,
                "watchdog": {
                    "distortion_overall": distortion_score,
                    "emotional_volatility": emotion_volatility,
                    "abort_triggered": True
                }
            })
            break

        # Apply fixed-point operator
        prev_vector = vectorize(R)
        R = compute_once(R, None, tri, const, culture, distortion, emotion)
        residual = l1_norm(prev_vector, vectorize(R))

        # Update iteration state
        R["iteration"].update({
            "epoch": k,
            "residual": round(residual, 6),
            "alpha": ALPHA,
            "epsilon": EPSILON,
            "watchdog": {
                "distortion_overall": distortion_score,
                "emotional_volatility": emotion_volatility,
                "abort_triggered": False
            }
        })

        # Create epoch snapshot
        epoch_hash = hash_report(R)
        snapshots.append({
            "epoch": k,
            "hash": epoch_hash,
            "residual": round(residual, 6),
            "state_vector": vectorize(R)[:]
        })

        # Convergence test
        if residual < EPSILON:
            R["iteration"]["converged"] = True
            break
    else:
        # Max iterations reached without convergence
        R["iteration"]["converged"] = False

    # Finalize report with timestamps and integrity
    R["timestamp"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    R["lightclock_tick"] = lightclock_tick
    R["input_reference"] = input_ref

    # Integrity hash (will be signed by Slot1)
    R["integrity"]["hash"] = hash_report(R)
    R["integrity"]["timestamp"] = R["timestamp"]

    return R, snapshots


def create_base_state(
    input_hash: str,
    padel_req_id: str,
    infinity_req_id: str,
    cognitive_level: str = "synthesis"
) -> Dict[str, Any]:
    """
    Create initial meta-lens report state.

    Args:
        input_hash: SHA-256 hash of input content
        padel_req_id: P.a.d.el request ID for frozen inputs
        infinity_req_id: INF-o-INITY request ID for frozen inputs
        cognitive_level: Bloom's taxonomy level

    Returns:
        Initial report state dictionary
    """
    return {
        "schema_version": "1.0.0",
        "source_slot": "S2",
        "input_reference": input_hash,
        "meta_lens_analysis": {
            "cognitive_level": cognitive_level,
            "lenses_applied": [
                "Bloom_Critical",
                "DeltaC_Systemic",
                "Cultural_Historical",
                "Manipulation_Audit",
                "Evidence_Independence"
            ],
            "state_vector": [0.5, 0.5, 0.5, 0.5, 0.0, 0.5],  # Safe priors
            "manipulative_patterns": {
                "detected": [],
                "confidence": 0.0,
                "cross_validation_source": "INF-o-INITY"
            },
            "cultural_overlay": {
                "historical_context": "",
                "cultural_bias_markers": [],
                "synthesis_confidence": 0.0
            }
        },
        "iteration": {
            "epoch": 0,
            "max_iters": MAX_ITERS,
            "alpha": ALPHA,
            "epsilon": EPSILON,
            "converged": False,
            "residual": 1.0,
            "frozen_inputs": {
                "padel_ref": padel_req_id,
                "infinity_ref": infinity_req_id
            }
        },
        "risk_assessment": {
            "level": "low",
            "vectors": [],
            "mitigation_suggestions": []
        },
        "notes": [],
        "integrity": {
            "hash": "sha256:",  # Will be computed
            "signed_by": "slot01_truth_anchor",
            "timestamp": ""  # Will be set
        }
    }