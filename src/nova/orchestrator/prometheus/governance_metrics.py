from __future__ import annotations

from typing import Any

from prometheus_client import Gauge, Counter, Info

from nova.orchestrator.prometheus.public_registry import nova_public_registry
from nova.orchestrator.prometheus.internal_registry import nova_internal_registry

governance_allowed_gauge_public = Gauge(
    "nova_governance_allowed",
    "Whether governance allowed the last action",
    registry=nova_public_registry,
)

governance_block_reason_info = Info(
    "nova_governance_block_reason",
    "Reason for the last governance block",
    registry=nova_public_registry,
)

governance_policy_score_gauge = Gauge(
    "nova_governance_policy_score",
    "Policy score observed by governance",
    registry=nova_internal_registry,
)

governance_ethics_violation_counter = Counter(
    "nova_governance_ethics_violations_total",
    "Total governance ethics violations",
    registry=nova_internal_registry,
)

governance_state_stability_gauge = Gauge(
    "nova_governance_state_stability",
    "Recent state stability score",
    registry=nova_internal_registry,
)


def record_governance_result(result: Any) -> None:
    allowed_value = 1 if result.allowed else 0
    governance_allowed_gauge_public.set(allowed_value)

    if not result.allowed:
        governance_block_reason_info.info({"reason": result.reason})

    policy_score = float(result.metadata.get("policy_score", 0.0))
    governance_policy_score_gauge.set(policy_score)

    stability = float(result.metadata.get("stability_score", 1.0))
    governance_state_stability_gauge.set(stability)

    violations = sum(1 for check in result.ethics if not check.passed)
    if violations:
        governance_ethics_violation_counter.inc(violations)
