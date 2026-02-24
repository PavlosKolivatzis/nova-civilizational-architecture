from dataclasses import dataclass

from nova.orchestrator.control_plane import (
    ControlPlaneDependencies,
    DecisionContext,
    DecisionRequest,
    DebugResponseEnvelope,
    DecisionResponseEnvelope,
    OrchestratorControlPlane,
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
