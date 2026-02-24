from dataclasses import dataclass

import pytest

from nova.orchestrator.control_plane import (
    ControlPlaneDependencies,
    CoreEventBusAdapter,
    CoreEventFactory,
    DecisionContext,
    DecisionRequest,
    ExecutionConfig,
    DictSlotRegistryService,
    DebugResponseEnvelope,
    DecisionResponseEnvelope,
    ExecutionDependencies,
    ExecutionResult,
    ExecutionRoute,
    ExecutionService,
    OrchestratorRunnerAdapter,
    OrchestratorControlPlane,
    PayloadEventFactory,
    PayloadEventBusAdapter,
    RouteDecision,
    RouteDecisionExecutionRoutePolicy,
    RouterExecutionRoutePolicy,
    SlotDescriptor,
)


@dataclass
class _FakeGovResult:
    allowed: bool
    reason: str = "ok"

    def to_dict(self):
        return {"allowed": self.allowed, "reason": self.reason}


class _FakeGovernance:
    def __init__(self, first: _FakeGovResult, second: _FakeGovResult | None = None):
        self._first = first
        self._second = second or first
        self.calls = []

    def evaluate(self, state, routing_decision=None, record=True):
        self.calls.append(
            {
                "state": dict(state),
                "routing_decision": routing_decision,
                "record": record,
            }
        )
        if len(self.calls) == 1:
            return self._first
        return self._second


class _FakeDecision:
    def __init__(self, body):
        self._body = body

    def to_dict(self):
        return dict(self._body)


class _FakeRouter:
    def __init__(self, decision_body=None):
        self.decision_body = decision_body or {"route": "primary", "final_score": 0.9}
        self.calls = []

    def decide(self, payload):
        self.calls.append(dict(payload))
        return _FakeDecision(self.decision_body)


class _FakeExecRouter:
    def __init__(self, route=("slot02_deltathresh", 2.0)):
        self.route = route
        self.calls = []

    def get_route(self, target_slot, original_timeout=2.0):
        self.calls.append((target_slot, original_timeout))
        return self.route


class _FakeRunnerProtocol:
    def __init__(self):
        self.calls = []

    async def invoke(self, slot_fn, slot_name, payload, request_id, timeout):
        self.calls.append((slot_fn, slot_name, dict(payload), request_id, timeout))
        return {"slot": slot_name, "timeout": timeout}


def test_control_plane_returns_hold_on_governance_precheck():
    router = _FakeRouter()
    gov = _FakeGovernance(_FakeGovResult(allowed=False, reason="tri_low"))
    cp = OrchestratorControlPlane(router=router, governance_engine=gov)

    result = cp.decide({"tri_signal": {"tri_coherence": 0.1}})

    assert result["route"] == "hold"
    assert result["governance"]["allowed"] is False
    assert result["constraints"]["reasons"] == ["governance_precheck"]
    assert router.calls == []
    assert len(gov.calls) == 1
    assert gov.calls[0]["record"] is False


def test_control_plane_runs_router_then_final_governance():
    router = _FakeRouter(
        {
            "route": "primary",
            "constraints": {"allowed": True, "reasons": [], "snapshot": {}},
            "policy": {"route": "primary", "score": 0.7, "details": {}},
            "advisors": {},
            "final_score": 0.63,
            "metadata": {"mode": "deterministic"},
        }
    )
    gov = _FakeGovernance(
        _FakeGovResult(allowed=True, reason="ok"),
        _FakeGovResult(allowed=True, reason="ok"),
    )
    cp = OrchestratorControlPlane(router=router, governance_engine=gov)

    payload = {"risk": 0.2, "novelty": 0.6}
    result = cp.decide(payload)

    assert result["route"] == "primary"
    assert result["governance"]["allowed"] is True
    assert len(router.calls) == 1
    assert router.calls[0] == payload
    assert len(gov.calls) == 2
    assert gov.calls[0]["record"] is False
    assert gov.calls[1]["record"] is True
    assert "routing_decision" in gov.calls[1]["state"]
    assert gov.calls[1]["routing_decision"]["route"] == "primary"


def test_control_plane_tracks_last_context():
    router = _FakeRouter()
    gov = _FakeGovernance(_FakeGovResult(allowed=False, reason="tri_low"))
    cp = OrchestratorControlPlane(router=router, governance_engine=gov)
    ctx = DecisionContext(request_id="req-1", source="http:/router/decide", trace_id="tr-1")

    cp.decide({"risk": 0.9}, context=ctx)

    assert cp.last_context == ctx


def test_decision_request_normalize_copies_payload_and_defaults_context():
    raw_payload = {"risk": 0.4}

    req = DecisionRequest.normalize(payload=raw_payload, context=None)

    assert req.payload == {"risk": 0.4}
    assert req.payload is not raw_payload
    assert req.context == DecisionContext()


def test_control_plane_tracks_last_request():
    router = _FakeRouter()
    gov = _FakeGovernance(_FakeGovResult(allowed=False, reason="tri_low"))
    cp = OrchestratorControlPlane(router=router, governance_engine=gov)
    ctx = DecisionContext(request_id="req-2")

    cp.decide({"risk": 0.7}, context=ctx)

    assert cp.last_request is not None
    assert cp.last_request.payload == {"risk": 0.7}
    assert cp.last_request.context == ctx


def test_decision_response_envelope_hold_serializer():
    body = DecisionResponseEnvelope.hold({"allowed": False, "reason": "tri_low"}).to_dict()

    assert body["route"] == "hold"
    assert body["governance"]["reason"] == "tri_low"
    assert body["constraints"]["reasons"] == ["governance_precheck"]


def test_control_plane_decide_http_uses_context_builder():
    router = _FakeRouter()
    gov = _FakeGovernance(
        _FakeGovResult(allowed=True, reason="ok"),
        _FakeGovResult(allowed=True, reason="ok"),
    )

    captured = {}

    def builder(request):
        captured["request"] = request
        return DecisionContext(request_id="r-http", source="http:/router/decide")

    cp = OrchestratorControlPlane(router=router, governance_engine=gov, http_context_builder=builder)

    request = object()
    cp.decide_http({"risk": 0.1}, request)

    assert captured["request"] is request
    assert cp.last_context is not None
    assert cp.last_context.request_id == "r-http"


def test_control_plane_accepts_dependencies_container():
    router = _FakeRouter()
    gov = _FakeGovernance(_FakeGovResult(allowed=False, reason="tri_low"))
    deps = ControlPlaneDependencies(router=router, governance_engine=gov)

    cp = OrchestratorControlPlane(dependencies=deps)
    cp.decide({"risk": 0.8})

    assert cp.dependencies is deps
    assert cp.last_request is not None


def test_debug_response_envelope_router_sets_mode_and_governance():
    body = DebugResponseEnvelope.router(
        {"route": "primary", "metadata": {"predictive": {}}},
        governance={"allowed": True, "reason": "ok"},
    ).to_dict()

    assert body["metadata"]["mode"] == "deterministic"
    assert body["metadata"]["predictive"] == {}
    assert body["governance"]["allowed"] is True


def test_control_plane_router_and_governance_debug_use_serializers():
    class _RouterDebugFake:
        last_decision = None

        def decide(self, payload):
            return _FakeDecision(
                {
                    "route": "primary",
                    "constraints": {"allowed": True, "reasons": [], "snapshot": {}},
                    "policy": {"route": "primary", "score": 0.5, "details": {}},
                    "advisors": {},
                    "final_score": 0.5,
                    "metadata": {},
                }
            )

    gov = _FakeGovernance(
        _FakeGovResult(allowed=True, reason="ok"),
        _FakeGovResult(allowed=True, reason="ok"),
    )
    gov.last_result = _FakeGovResult(allowed=True, reason="ok")
    cp = OrchestratorControlPlane(
        dependencies=ControlPlaneDependencies(router=_RouterDebugFake(), governance_engine=gov)
    )

    router_debug = cp.router_debug()
    gov_debug = cp.governance_debug()

    assert router_debug["metadata"]["mode"] == "deterministic"
    assert router_debug["governance"]["reason"] == "ok"
    assert gov_debug["allowed"] is True


@pytest.mark.asyncio
async def test_core_event_bus_adapter_passthrough():
    captured = {}

    class _Bus:
        async def publish(self, topic, event):
            captured["topic"] = topic
            captured["event"] = event
            return ["ok"]

    adapter = CoreEventBusAdapter(_Bus())
    event = {"payload": 1}
    out = await adapter.publish("invoke", event)

    assert out == ["ok"]
    assert captured == {"topic": "invoke", "event": event}


@pytest.mark.asyncio
async def test_payload_event_bus_adapter_converts_event_object():
    captured = {}

    class _Bus:
        async def publish(self, topic, payload):
            captured["topic"] = topic
            captured["payload"] = payload
            return ["ok"]

    class _Evt:
        target_slot = "slot02_deltathresh"
        payload = {"a": 1}
        trace_id = "t-1"

    adapter = PayloadEventBusAdapter(_Bus())
    out = await adapter.publish("invoke", _Evt())

    assert out == ["ok"]
    assert captured["topic"] == "invoke"
    assert captured["payload"] == {"a": 1}


@pytest.mark.asyncio
async def test_execution_service_success_path():
    class _Bus:
        def __init__(self):
            self.calls = []

        async def publish(self, topic, event):
            self.calls.append((topic, event))
            return []

    bus = _Bus()
    runner = _FakeRunnerProtocol()
    router = _FakeExecRouter(route=("slot02_deltathresh", 3.5))
    slot_fn = object()

    service = ExecutionService(
        ExecutionDependencies(
            route_policy=RouterExecutionRoutePolicy(router, original_timeout=2.0),
            bus=CoreEventBusAdapter(bus),
            event_factory=PayloadEventFactory(),
            slot_registry=DictSlotRegistryService({"slot02_deltathresh": slot_fn}),
            orchestrator_runner=runner,
        )
    )

    out = await service.handle_request("slot02_deltathresh", {"x": 1}, "req-1")

    assert isinstance(out, ExecutionResult)
    assert out.executed is True
    assert out.blocked is False
    assert out.reason == "executed"
    assert out.slot_id == "slot02_deltathresh"
    assert out.timeout == 3.5
    assert out.result == {"slot": "slot02_deltathresh", "timeout": 3.5}
    assert router.calls == [("slot02_deltathresh", 2.0)]
    assert bus.calls == [("invoke", {"target_slot": "slot02_deltathresh", "payload": {"x": 1}})]
    assert runner.calls == [(slot_fn, "slot02_deltathresh", {"x": 1}, "req-1", 3.5)]


@pytest.mark.asyncio
async def test_execution_service_returns_structured_result_without_runner():
    class _Bus:
        async def publish(self, topic, event):
            return []

    service = ExecutionService(
        ExecutionDependencies(
            route_policy=RouterExecutionRoutePolicy(_FakeExecRouter(), original_timeout=2.0),
            bus=CoreEventBusAdapter(_Bus()),
            event_factory=PayloadEventFactory(),
            slot_registry=DictSlotRegistryService({"slot02_deltathresh": object()}),
            orchestrator_runner=None,
        )
    )

    out = await service.handle_request("slot02_deltathresh", {"x": 1}, "req-2")
    assert isinstance(out, ExecutionResult)
    assert out.executed is False
    assert out.blocked is False
    assert out.reason == "no_runner"
    assert out.result is None
    assert out.slot_id == "slot02_deltathresh"
    assert out.timeout == 2.0


def test_core_event_factory_builds_typed_event():
    class _Evt:
        def __init__(self, target_slot, payload):
            self.target_slot = target_slot
            self.payload = payload

    factory = CoreEventFactory(_Evt)
    evt = factory.build("slot02_deltathresh", {"a": 1})

    assert evt.target_slot == "slot02_deltathresh"
    assert evt.payload == {"a": 1}


def test_orchestrator_runner_adapter_bridges_invoke_slot_signature():
    captured = {}

    class _Runner:
        async def invoke_slot(self, slot_fn, slot_name, payload, request_id, timeout=None):
            captured.update(
                {
                    "slot_fn": slot_fn,
                    "slot_name": slot_name,
                    "payload": dict(payload),
                    "request_id": request_id,
                    "timeout": timeout,
                }
            )
            return {"ok": True}

    adapter = OrchestratorRunnerAdapter(_Runner())

    import asyncio

    out = asyncio.run(adapter.invoke(object(), "slotX", {"p": 1}, "reqX", 2.5))

    assert out == {"ok": True}
    assert captured["slot_name"] == "slotX"
    assert captured["timeout"] == 2.5


@pytest.mark.asyncio
async def test_payload_bus_adapter_and_payload_event_factory_end_to_end_execution():
    class _PayloadBus:
        def __init__(self):
            self.calls = []

        async def publish(self, topic, payload):
            self.calls.append((topic, payload))
            return ["published"]

    bus = _PayloadBus()
    router = _FakeExecRouter(route=("slot08_memory_ethics", 4.0))
    slot_fn = object()
    runner = _FakeRunnerProtocol()

    service = ExecutionService(
        ExecutionDependencies(
            route_policy=RouterExecutionRoutePolicy(router, original_timeout=2.0),
            bus=PayloadEventBusAdapter(bus),
            event_factory=PayloadEventFactory(),
            slot_registry=DictSlotRegistryService({"slot08_memory_ethics": slot_fn}),
            orchestrator_runner=runner,
        )
    )

    result = await service.handle_request("slot02_deltathresh", {"z": 9}, "req-payload")

    assert isinstance(result, ExecutionResult)
    assert result.executed is True
    assert result.blocked is False
    assert result.reason == "executed"
    assert result.slot_id == "slot08_memory_ethics"
    assert result.timeout == 4.0
    assert result.result == {"slot": "slot08_memory_ethics", "timeout": 4.0}
    assert bus.calls == [("invoke", {"target_slot": "slot08_memory_ethics", "payload": {"z": 9}})]
    assert runner.calls == [(slot_fn, "slot08_memory_ethics", {"z": 9}, "req-payload", 4.0)]


def test_router_execution_route_policy_normalizes_router_tuple():
    router = _FakeExecRouter(route=("slot10_civilizational_deployment", 5))
    policy = RouterExecutionRoutePolicy(router, original_timeout=3.25)

    route = policy.resolve("slot02_deltathresh")

    assert route == ExecutionRoute(slot_id="slot10_civilizational_deployment", timeout=5.0)
    assert router.calls == [("slot02_deltathresh", 3.25)]


def test_dict_slot_registry_service_returns_slot_descriptor():
    handler = object()
    service = DictSlotRegistryService({"slot02_deltathresh": handler})

    descriptor = service.resolve("slot02_deltathresh")

    assert descriptor == SlotDescriptor(slot_id="slot02_deltathresh", handler=handler)
    assert service.resolve("missing") is None


@pytest.mark.asyncio
async def test_execution_service_uses_configured_event_topic_and_slot_timeout_override():
    class _Bus:
        def __init__(self):
            self.calls = []

        async def publish(self, topic, event):
            self.calls.append((topic, event))
            return []

    class _RoutePolicy:
        def resolve(self, target_slot):
            assert target_slot == "slot02_deltathresh"
            return ExecutionRoute(slot_id="slot02_deltathresh", timeout=2.5)

    bus = _Bus()
    runner = _FakeRunnerProtocol()
    handler = object()
    registry = DictSlotRegistryService(
        {
            "slot02_deltathresh": SlotDescriptor(
                slot_id="slot02_deltathresh",
                handler=handler,
                timeout_override=7.0,
                capability_flags={"critical": True},
            )
        }
    )
    service = ExecutionService(
        ExecutionDependencies(
            route_policy=_RoutePolicy(),
            bus=CoreEventBusAdapter(bus),
            event_factory=PayloadEventFactory(),
            slot_registry=registry,
            config=ExecutionConfig(event_topic="slot.invoke"),
            orchestrator_runner=runner,
        )
    )

    result = await service.handle_request("slot02_deltathresh", {"x": 1}, "req-topic")

    assert isinstance(result, ExecutionResult)
    assert result.executed is True
    assert result.blocked is False
    assert result.reason == "executed"
    assert result.slot_id == "slot02_deltathresh"
    assert result.timeout == 7.0
    assert result.result == {"slot": "slot02_deltathresh", "timeout": 7.0}
    assert bus.calls == [("slot.invoke", {"target_slot": "slot02_deltathresh", "payload": {"x": 1}})]
    assert runner.calls == [(handler, "slot02_deltathresh", {"x": 1}, "req-topic", 7.0)]


def test_route_decision_execution_route_policy_adapts_nonlegacy_router():
    class _DecisionRouter:
        def __init__(self):
            self.calls = []

        def decide(self, payload):
            self.calls.append(dict(payload))
            return _FakeDecision({"route": "slot08_memory_ethics", "metadata": {"timeout": 6}})

    router = _DecisionRouter()
    policy = RouteDecisionExecutionRoutePolicy(router, default_timeout=2.0)

    route = policy.resolve("slot02_deltathresh")

    assert route == ExecutionRoute(slot_id="slot08_memory_ethics", timeout=6.0)
    assert router.calls == [{"target_slot": "slot02_deltathresh"}]


def test_route_decision_execution_route_policy_normalizes_object_without_to_dict():
    class _Decision:
        def __init__(self, route, timeout):
            self.route = route
            self.timeout = timeout

    class _DecisionRouter:
        def decide(self, payload):
            assert payload == {"slot": "slot02_deltathresh"}
            return _Decision(route="slot10_civilizational_deployment", timeout=None)

    policy = RouteDecisionExecutionRoutePolicy(
        _DecisionRouter(),
        default_timeout=3.0,
        decision_request_builder=lambda slot: {"slot": slot},
    )

    route = policy.resolve("slot02_deltathresh")

    assert route == ExecutionRoute(slot_id="slot10_civilizational_deployment", timeout=3.0)


def test_route_decision_dataclass_shape():
    decision = RouteDecision(route="slot02_deltathresh", timeout=1.5)
    assert decision.route == "slot02_deltathresh"
    assert decision.timeout == 1.5


def test_execution_result_to_dict():
    result = ExecutionResult(
        executed=False,
        blocked=True,
        reason="capability_invoke_disabled",
        result=None,
        slot_id="slot02_deltathresh",
        timeout=2.0,
    )

    assert result.to_dict() == {
        "executed": False,
        "blocked": True,
        "reason": "capability_invoke_disabled",
        "result": None,
        "slot_id": "slot02_deltathresh",
        "timeout": 2.0,
    }


@pytest.mark.asyncio
async def test_execution_service_blocks_on_capability_flags_before_publish_and_invoke():
    class _Bus:
        def __init__(self):
            self.calls = []

        async def publish(self, topic, event):
            self.calls.append((topic, event))
            return []

    class _RoutePolicy:
        def resolve(self, target_slot):
            return ExecutionRoute(slot_id=target_slot, timeout=2.0)

    bus = _Bus()
    runner = _FakeRunnerProtocol()
    service = ExecutionService(
        ExecutionDependencies(
            route_policy=_RoutePolicy(),
            bus=CoreEventBusAdapter(bus),
            event_factory=PayloadEventFactory(),
            slot_registry=DictSlotRegistryService(
                {
                    "slot02_deltathresh": SlotDescriptor(
                        slot_id="slot02_deltathresh",
                        handler=object(),
                        capability_flags={"invoke_enabled": False, "required_payload_keys": ["x"]},
                    )
                }
            ),
            orchestrator_runner=runner,
        )
    )

    result = await service.handle_request("slot02_deltathresh", {"x": 1}, "req-gated")

    assert isinstance(result, ExecutionResult)
    assert result.executed is False
    assert result.blocked is True
    assert result.reason == "capability_invoke_disabled"
    assert result.slot_id == "slot02_deltathresh"
    assert result.timeout == 2.0
    assert bus.calls == []
    assert runner.calls == []
