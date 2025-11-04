import inspect

import nova.governor.adaptive_wisdom as module
from nova.governor import AdaptiveWisdomGovernor
from nova.metrics import governor as metrics


def setup_function(function) -> None:
    metrics.reset_for_tests()


def test_controller_bounds_and_modes():
    gov = AdaptiveWisdomGovernor(eta=0.10, eta_min=0.05, eta_max=0.15)

    tele = gov.step(margin=0.005, G=0.40)
    assert tele.eta == 0.05
    assert tele.mode == "CRITICAL"

    tele = gov.step(margin=0.08, G=0.72)
    assert tele.eta == 0.12
    assert tele.mode == "OPTIMAL"

    tele = gov.step(margin=0.50, G=0.10)
    assert 0.05 <= tele.eta <= 0.15


def test_publish_updates_metrics():
    gov = AdaptiveWisdomGovernor()
    tele = gov.step(margin=0.08, G=0.72)
    metrics.publish_telemetry(tele)

    assert metrics.gamma_eta_gauge()._value.get() == tele.eta  # type: ignore[attr-defined]
    assert metrics.gamma_margin_gauge()._value.get() == tele.margin  # type: ignore[attr-defined]
    assert metrics.gamma_generativity_gauge()._value.get() == tele.G  # type: ignore[attr-defined]


def test_public_api_nominal():
    public = {name for name in dir(module) if not name.startswith("_")}
    assert public <= {"AdaptiveWisdomGovernor", "Telemetry", "State", "__all__", "__annotations__", "annotations"}
    exported = set(module.__all__)
    assert exported == {"AdaptiveWisdomGovernor", "Telemetry", "State"}
