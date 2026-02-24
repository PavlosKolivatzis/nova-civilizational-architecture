from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional


@dataclass(frozen=True)
class DecisionContext:
    """Execution context for orchestrator decisions (Phase 1 scaffold)."""

    request_id: str = ""
    source: str = "http"
    trace_id: str = ""
    flags: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ControlPlaneDependencies:
    """Dependency bundle for control plane wiring and easier test injection."""

    router: Any
    governance_engine: Any
    http_context_builder: Optional[Callable[[Any], DecisionContext]] = None
    execution: Optional["ExecutionDependencies"] = None


@dataclass
class ExecutionDependencies:
    """Dependencies for legacy execution-side orchestration."""

    router: Any
    bus: Any
    event_cls: Any
    slot_registry: Dict[str, Any]
    orchestrator_runner: Any = None


@dataclass(frozen=True)
class DecisionRequest:
    """Normalized control-plane request bundle."""

    payload: Dict[str, Any] = field(default_factory=dict)
    context: DecisionContext = field(default_factory=DecisionContext)

    @classmethod
    def normalize(
        cls,
        payload: Optional[Dict[str, Any]] = None,
        context: Optional[DecisionContext] = None,
    ) -> "DecisionRequest":
        normalized_payload = dict(payload or {})
        normalized_context = context or DecisionContext()
        return cls(payload=normalized_payload, context=normalized_context)


@dataclass(frozen=True)
class DecisionResponseEnvelope:
    """Serializer envelope for control-plane decision responses."""

    body: Dict[str, Any]

    @classmethod
    def hold(cls, governance: Dict[str, Any]) -> "DecisionResponseEnvelope":
        return cls(
            body={
                "route": "hold",
                "governance": governance,
                "constraints": {
                    "allowed": False,
                    "reasons": ["governance_precheck"],
                    "snapshot": {},
                },
            }
        )

    @classmethod
    def routed(
        cls,
        decision: Dict[str, Any],
        governance: Dict[str, Any],
    ) -> "DecisionResponseEnvelope":
        body = dict(decision)
        body["governance"] = governance
        return cls(body=body)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.body)


@dataclass(frozen=True)
class DebugResponseEnvelope:
    """Serializer envelope for router/governance debug responses."""

    body: Dict[str, Any]

    @classmethod
    def router(
        cls,
        decision: Dict[str, Any],
        governance: Optional[Dict[str, Any]] = None,
        *,
        mode: str = "deterministic",
    ) -> "DebugResponseEnvelope":
        body = dict(decision)
        metadata = dict(body.get("metadata") or {})
        metadata["mode"] = mode
        body["metadata"] = metadata
        if governance is not None:
            body["governance"] = governance
        return cls(body=body)

    @classmethod
    def governance(cls, result: Dict[str, Any]) -> "DebugResponseEnvelope":
        return cls(body=dict(result))

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.body)


class ControlPlaneDebugAPI:
    """Explicit debug transport API owned by the control plane."""

    def __init__(self, deps: ControlPlaneDependencies) -> None:
        self._deps = deps

    def router(self) -> Dict[str, Any]:
        last_decision = getattr(self._deps.router, "last_decision", None)
        if last_decision is None:
            last_decision = self._deps.router.decide({})
        decision_dict = last_decision.to_dict()

        governance = getattr(self._deps.governance_engine, "last_result", None)
        governance_dict = governance.to_dict() if governance is not None else None
        return DebugResponseEnvelope.router(decision_dict, governance_dict).to_dict()

    def governance(self) -> Dict[str, Any]:
        last = getattr(self._deps.governance_engine, "last_result", None)
        if last is None:
            last = self._deps.governance_engine.evaluate({}, record=False)
        return DebugResponseEnvelope.governance(last.to_dict()).to_dict()


class OrchestratorControlPlane:
    """Thin orchestration layer for routing + governance decisions."""

    def __init__(
        self,
        router: Any = None,
        governance_engine: Any = None,
        http_context_builder: Optional[Callable[[Any], DecisionContext]] = None,
        dependencies: Optional[ControlPlaneDependencies] = None,
    ) -> None:
        if dependencies is None:
            if router is None or governance_engine is None:
                raise ValueError("router and governance_engine are required when dependencies is not provided")
            dependencies = ControlPlaneDependencies(
                router=router,
                governance_engine=governance_engine,
                http_context_builder=http_context_builder,
            )
        elif http_context_builder is not None:
            dependencies.http_context_builder = http_context_builder

        self._deps = dependencies
        self._debug_api = ControlPlaneDebugAPI(self._deps)
        self._last_context: Optional[DecisionContext] = None
        self._last_request: Optional[DecisionRequest] = None

    def decide(
        self,
        payload: Optional[Dict[str, Any]] = None,
        context: Optional[DecisionContext] = None,
    ) -> Dict[str, Any]:
        req = DecisionRequest.normalize(payload=payload, context=context)
        payload = req.payload
        self._last_request = req
        self._last_context = req.context

        precheck = self._deps.governance_engine.evaluate(payload, record=False)
        if not precheck.allowed:
            return DecisionResponseEnvelope.hold(precheck.to_dict()).to_dict()

        decision = self._deps.router.decide(payload)
        decision_dict = decision.to_dict()

        enriched_state = dict(payload)
        enriched_state["routing_decision"] = decision_dict
        final_governance = self._deps.governance_engine.evaluate(
            enriched_state,
            routing_decision=decision_dict,
            record=True,
        )

        return DecisionResponseEnvelope.routed(
            decision=decision_dict,
            governance=final_governance.to_dict(),
        ).to_dict()

    def decide_http(self, payload: Optional[Dict[str, Any]], request: Any) -> Dict[str, Any]:
        builder = self._deps.http_context_builder
        context = builder(request) if builder else DecisionContext(source="http")
        return self.decide(payload=payload, context=context)

    def set_http_context_builder(self, builder: Callable[[Any], DecisionContext]) -> None:
        self._deps.http_context_builder = builder

    def set_execution_dependencies(self, execution: ExecutionDependencies) -> None:
        self._deps.execution = execution

    async def handle_request(self, target_slot: str, payload: Dict[str, Any], request_id: str):
        """Legacy execution path delegated through control plane for Phase 2 prep."""
        execution = self._deps.execution
        if execution is None:
            raise RuntimeError("Execution dependencies not configured")

        slot, timeout = execution.router.get_route(target_slot, original_timeout=2.0)
        evt = execution.event_cls(target_slot=slot, payload=payload)
        await execution.bus.publish("invoke", evt)
        slot_fn = execution.slot_registry.get(slot)
        if execution.orchestrator_runner and slot_fn:
            return await execution.orchestrator_runner.invoke_slot(
                slot_fn,
                slot,
                payload,
                request_id,
                timeout=timeout,
            )
        return None

    def router_debug(self) -> Dict[str, Any]:
        """Return router debug payload with envelope-controlled shape."""
        return self._debug_api.router()

    def governance_debug(self) -> Dict[str, Any]:
        """Return governance debug payload with envelope-controlled shape."""
        return self._debug_api.governance()

    @property
    def last_context(self) -> Optional[DecisionContext]:
        return self._last_context

    @property
    def last_request(self) -> Optional[DecisionRequest]:
        return self._last_request

    @property
    def dependencies(self) -> ControlPlaneDependencies:
        return self._deps

    @property
    def debug_api(self) -> ControlPlaneDebugAPI:
        return self._debug_api
