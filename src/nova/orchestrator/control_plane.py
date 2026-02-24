from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, Protocol, runtime_checkable


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
    execution_service: Optional["ExecutionService"] = None


@runtime_checkable
class EventBusProtocol(Protocol):
    """Unified async event bus interface for control-plane execution."""

    async def publish(self, topic: str, event: Any) -> Any:
        ...


@runtime_checkable
class ExecutionEventFactory(Protocol):
    """Build execution events for the selected bus contract."""

    def build(self, target_slot: str, payload: Dict[str, Any]) -> Any:
        ...


@dataclass(frozen=True)
class ExecutionRoute:
    """Resolved execution route with normalized timeout."""

    slot_id: str
    timeout: float


@dataclass(frozen=True)
class RouteDecision:
    """Normalized route-decision shape for non-legacy router adapters."""

    route: str
    timeout: Optional[float] = None


@runtime_checkable
class ExecutionRoutePolicy(Protocol):
    """Resolve execution route + timeout behind a stable contract."""

    def resolve(self, target_slot: str) -> ExecutionRoute:
        ...


@runtime_checkable
class SlotInvocationRunner(Protocol):
    """Invoke a resolved slot callable using a stable control-plane contract."""

    async def invoke(
        self,
        slot_fn: Any,
        slot_name: str,
        payload: Dict[str, Any],
        request_id: str,
        timeout: float,
    ) -> Any:
        ...


@runtime_checkable
class SlotRegistryService(Protocol):
    """Typed slot registry interface for execution resolution."""

    def resolve(self, slot_id: str) -> "SlotDescriptor | None":
        ...


@dataclass(frozen=True)
class SlotDescriptor:
    """Typed slot registry entry used by execution orchestration."""

    slot_id: str
    handler: Any
    timeout_override: Optional[float] = None
    capability_flags: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionConfig:
    """Execution service runtime config (non-behavioral constants)."""

    event_topic: str = "invoke"


@dataclass(frozen=True)
class ExecutionResult:
    """Structured outcome for execution orchestration attempts."""

    executed: bool
    blocked: bool
    reason: str
    result: Any = None
    slot_id: str = ""
    timeout: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "executed": self.executed,
            "blocked": self.blocked,
            "reason": self.reason,
            "result": self.result,
            "slot_id": self.slot_id,
            "timeout": self.timeout,
        }


class RouterExecutionRoutePolicy:
    """Adapter over legacy router.get_route(...) tuple contract."""

    def __init__(self, router: Any, *, original_timeout: float = 2.0) -> None:
        self._router = router
        self._original_timeout = original_timeout

    def resolve(self, target_slot: str) -> ExecutionRoute:
        slot_id, timeout = self._router.get_route(
            target_slot,
            original_timeout=self._original_timeout,
        )
        return ExecutionRoute(slot_id=slot_id, timeout=float(timeout))


class RouteDecisionExecutionRoutePolicy:
    """Adapter for routers exposing decide(...) instead of get_route(...)."""

    def __init__(
        self,
        router: Any,
        *,
        default_timeout: float = 2.0,
        decision_request_builder: Optional[Callable[[str], Dict[str, Any]]] = None,
    ) -> None:
        self._router = router
        self._default_timeout = default_timeout
        self._decision_request_builder = decision_request_builder or self._default_request

    def resolve(self, target_slot: str) -> ExecutionRoute:
        raw = self._router.decide(self._decision_request_builder(target_slot))
        decision = self._normalize_decision(raw)
        timeout = decision.timeout if decision.timeout is not None else self._default_timeout
        return ExecutionRoute(slot_id=decision.route, timeout=float(timeout))

    @staticmethod
    def _default_request(target_slot: str) -> Dict[str, Any]:
        return {"target_slot": target_slot}

    @staticmethod
    def _normalize_decision(raw: Any) -> RouteDecision:
        if hasattr(raw, "to_dict"):
            raw = raw.to_dict()
        if isinstance(raw, dict):
            route = raw.get("route") or raw.get("slot_id")
            timeout = raw.get("timeout")
            if timeout is None:
                metadata = raw.get("metadata") or {}
                if isinstance(metadata, dict):
                    timeout = metadata.get("timeout")
            if route is None:
                raise ValueError("route decision missing 'route'")
            return RouteDecision(route=str(route), timeout=None if timeout is None else float(timeout))

        route = getattr(raw, "route", None) or getattr(raw, "slot_id", None)
        timeout = getattr(raw, "timeout", None)
        if route is None:
            raise ValueError("route decision object missing route/slot_id")
        return RouteDecision(route=str(route), timeout=None if timeout is None else float(timeout))


class CoreEventBusAdapter:
    """Adapter for `nova.orchestrator.core.event_bus.EventBus`."""

    def __init__(self, bus: Any) -> None:
        self._bus = bus

    async def publish(self, topic: str, event: Any) -> Any:
        return await self._bus.publish(topic, event)


class PayloadEventBusAdapter:
    """Adapter for `nova.orchestrator.bus.EventBus` (payload-based)."""

    def __init__(self, bus: Any) -> None:
        self._bus = bus

    async def publish(self, topic: str, event: Any) -> Any:
        if isinstance(event, dict):
            payload = dict(event)
        else:
            payload = getattr(event, "payload", None)
            if not isinstance(payload, dict):
                payload = {
                    "target_slot": getattr(event, "target_slot", None),
                    "payload": getattr(event, "payload", None),
                    "trace_id": getattr(event, "trace_id", None),
                }
        return await self._bus.publish(topic, payload)


class CoreEventFactory:
    """Build typed Event instances for the core event bus path."""

    def __init__(self, event_cls: Any) -> None:
        self._event_cls = event_cls

    def build(self, target_slot: str, payload: Dict[str, Any]) -> Any:
        return self._event_cls(target_slot=target_slot, payload=payload)


class PayloadEventFactory:
    """Build payload dicts for the payload-based event bus path."""

    def build(self, target_slot: str, payload: Dict[str, Any]) -> Any:
        return {
            "target_slot": target_slot,
            "payload": dict(payload),
        }


class DictSlotRegistryService:
    """Adapter exposing a dict registry via SlotRegistryService."""

    def __init__(self, registry: Dict[str, Any]) -> None:
        self._registry = registry

    def resolve(self, slot_id: str) -> SlotDescriptor | None:
        resolved = self._registry.get(slot_id)
        if resolved is None:
            return None
        if isinstance(resolved, SlotDescriptor):
            return resolved
        return SlotDescriptor(slot_id=slot_id, handler=resolved)


class OrchestratorRunnerAdapter:
    """Adapter over legacy runner exposing SlotInvocationRunner protocol."""

    def __init__(self, runner: Any) -> None:
        self._runner = runner

    async def invoke(
        self,
        slot_fn: Any,
        slot_name: str,
        payload: Dict[str, Any],
        request_id: str,
        timeout: float,
    ) -> Any:
        return await self._runner.invoke_slot(
            slot_fn,
            slot_name,
            payload,
            request_id,
            timeout=timeout,
        )


@dataclass
class ExecutionDependencies:
    """Dependencies for legacy execution-side orchestration."""

    route_policy: ExecutionRoutePolicy
    bus: EventBusProtocol
    event_factory: ExecutionEventFactory
    slot_registry: SlotRegistryService
    config: ExecutionConfig = field(default_factory=ExecutionConfig)
    orchestrator_runner: Optional[SlotInvocationRunner] = None


class ExecutionService:
    """Execution orchestration behind a stable control-plane boundary."""

    def __init__(self, deps: ExecutionDependencies) -> None:
        self._deps = deps

    async def handle_request(
        self,
        target_slot: str,
        payload: Dict[str, Any],
        request_id: str,
    ) -> ExecutionResult:
        route = self._deps.route_policy.resolve(target_slot)
        slot_descriptor = self._deps.slot_registry.resolve(route.slot_id)
        capability_reason = None
        if slot_descriptor:
            capability_reason = self._capability_block_reason(slot_descriptor, payload)
        if capability_reason is not None:
            return ExecutionResult(
                executed=False,
                blocked=True,
                reason=capability_reason,
                slot_id=route.slot_id,
                timeout=route.timeout,
            )
        evt = self._deps.event_factory.build(route.slot_id, payload)
        await self._deps.bus.publish(self._deps.config.event_topic, evt)
        if slot_descriptor is None:
            return ExecutionResult(
                executed=False,
                blocked=False,
                reason="slot_not_found",
                slot_id=route.slot_id,
                timeout=route.timeout,
            )
        if self._deps.orchestrator_runner:
            timeout = (
                slot_descriptor.timeout_override
                if slot_descriptor.timeout_override is not None
                else route.timeout
            )
            result = await self._deps.orchestrator_runner.invoke(
                slot_descriptor.handler,
                slot_descriptor.slot_id,
                payload,
                request_id,
                timeout,
            )
            return ExecutionResult(
                executed=True,
                blocked=False,
                reason="executed",
                result=result,
                slot_id=slot_descriptor.slot_id,
                timeout=timeout,
            )
        return ExecutionResult(
            executed=False,
            blocked=False,
            reason="no_runner",
            slot_id=slot_descriptor.slot_id,
            timeout=(
                slot_descriptor.timeout_override
                if slot_descriptor.timeout_override is not None
                else route.timeout
            ),
        )

    @staticmethod
    def _capability_block_reason(
        slot_descriptor: SlotDescriptor,
        payload: Dict[str, Any],
    ) -> Optional[str]:
        flags = slot_descriptor.capability_flags or {}
        if flags.get("invoke_enabled") is False:
            return "capability_invoke_disabled"

        required_payload_keys = flags.get("required_payload_keys") or ()
        try:
            required_keys_iter = tuple(required_payload_keys)
        except TypeError:
            return "capability_invalid_required_payload_keys"

        for key in required_keys_iter:
            if key not in payload:
                return f"capability_missing_payload_key:{key}"
        return None


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
        self._deps.execution_service = ExecutionService(execution)

    def set_execution_service(self, execution_service: ExecutionService) -> None:
        self._deps.execution_service = execution_service

    async def handle_request(self, target_slot: str, payload: Dict[str, Any], request_id: str):
        """Legacy execution path delegated through control plane for Phase 2 prep."""
        execution_service = self._deps.execution_service
        if execution_service is None:
            raise RuntimeError("Execution dependencies not configured")
        return await execution_service.handle_request(target_slot, payload, request_id)

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
