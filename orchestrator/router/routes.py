"""Slot execution route definitions for Nova ANR."""

from dataclasses import dataclass
from typing import Callable, Dict, Any, List

@dataclass
class Step:
    name: str
    fn: Callable[..., Any]
    kwargs: Dict[str, Any]

@dataclass
class ExecutionPlan:
    route: str
    steps: List[Step]
    conservative: bool = False

# Lazy imports inside builders to avoid cycles
def _tri_eval(strict: bool = False, **kw):
    from orchestrator.adapters.slot4_tri import evaluate as tri_evaluate
    return tri_evaluate(strict=strict, **kw)

def _constellate(**kw):
    from orchestrator.adapters.slot5_constellation import constellate
    return constellate(**kw)

def _synthesize_culture(mode: str = "normal", **kw):
    from orchestrator.adapters.slot6_cultural import synthesize
    return synthesize(mode=mode, **kw)

def _emit_backpressure(level: float, reason: str = "routing", **kw):
    from nova.slots.slot07_production_controls.core.reflex import emit_backpressure
    return emit_backpressure(level=level, reason=reason)

def _deploy_canary(**kw):
    from orchestrator.adapters.slot10_civilizational import run_canary_stage
    return run_canary_stage(**kw)

def build_R1_standard(ctx: Dict[str, Any]) -> ExecutionPlan:
    """Standard route: Full TRI → Constellation → Cultural Synthesis → Deployment."""
    return ExecutionPlan(
        route="R1_STANDARD",
        steps=[
            Step("tri.evaluate", _tri_eval, {"strict": False, "ctx": ctx}),
            Step("constellation.constellate", _constellate, {"ctx": ctx}),
            Step("culture.synthesize", _synthesize_culture, {"mode": "normal", "ctx": ctx}),
            Step("deploy.canary", _deploy_canary, {"ctx": ctx}),
        ],
        conservative=False,
    )

def build_R2_strict(ctx: Dict[str, Any]) -> ExecutionPlan:
    """Strict route: Enhanced TRI validation, conservative cultural synthesis."""
    return ExecutionPlan(
        route="R2_STRICT",
        steps=[
            Step("tri.evaluate", _tri_eval, {"strict": True, "ctx": ctx}),
            Step("culture.synthesize", _synthesize_culture, {"mode": "conservative", "ctx": ctx}),
            Step("deploy.canary", _deploy_canary, {"ctx": ctx}),
        ],
        conservative=True,
    )

def build_R3_fast(ctx: Dict[str, Any]) -> ExecutionPlan:
    """Fast route: Skip constellation, light cultural synthesis."""
    return ExecutionPlan(
        route="R3_FAST",
        steps=[
            Step("tri.evaluate", _tri_eval, {"strict": False, "ctx": ctx}),
            Step("culture.synthesize", _synthesize_culture, {"mode": "light", "ctx": ctx}),
            Step("deploy.canary", _deploy_canary, {"ctx": ctx}),
        ],
        conservative=False,
    )

def build_R4_block(ctx: Dict[str, Any]) -> ExecutionPlan:
    """Guardrail route: Explainable stop with no slot execution."""
    return ExecutionPlan(route="R4_BLOCK", steps=[], conservative=True)

def build_R5_feedback_heavy(ctx: Dict[str, Any]) -> ExecutionPlan:
    """Feedback-heavy route: Enhanced coordination with Slot7 back-pressure."""
    return ExecutionPlan(
        route="R5_FEEDBACK_HEAVY",
        steps=[
            Step("tri.evaluate", _tri_eval, {"strict": True, "ctx": ctx}),
            Step("culture.synthesize", _synthesize_culture, {"mode": "normal", "ctx": ctx}),
            Step("prod.backpressure", _emit_backpressure, {"level": 0.6, "reason": "ANR_R5"}),
            Step("deploy.canary", _deploy_canary, {"ctx": ctx}),
        ],
        conservative=True,
    )

ROUTE_BUILDERS = {
    "R1": build_R1_standard,
    "R2": build_R2_strict,
    "R3": build_R3_fast,
    "R4": build_R4_block,
    "R5": build_R5_feedback_heavy,
}

def build_plan_for_route(route: str, ctx: Dict[str, Any]) -> ExecutionPlan:
    """Return an ExecutionPlan for a given route key ('R1'..'R5'). Defaults to strict."""
    builder = ROUTE_BUILDERS.get(route, build_R2_strict)
    return builder(ctx)

__all__ = [
    "Step",
    "ExecutionPlan",
    "ROUTE_BUILDERS",
    "build_plan_for_route",
    "build_R1_standard",
    "build_R2_strict",
    "build_R3_fast",
    "build_R4_block",
    "build_R5_feedback_heavy",
]
