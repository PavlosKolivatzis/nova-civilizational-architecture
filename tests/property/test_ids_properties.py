import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from services.ids.core import InterpretiveDriftSynthesizer


@pytest.mark.property
@given(st.lists(st.floats(min_value=-10, max_value=10), min_size=2, max_size=100))
@settings(suppress_health_check=[HealthCheck.too_slow])
def test_stability_range(vector):
    """Test stability always returns values between 0 and 1"""
    ids = InterpretiveDriftSynthesizer()
    stability = ids.calculate_stability(vector)
    assert 0 <= stability <= 1


@pytest.mark.property
@given(
    st.lists(st.floats(min_value=-10, max_value=10), min_size=2, max_size=100),
    st.lists(st.floats(min_value=-10, max_value=10), min_size=2, max_size=100),
)
def test_drift_range(vector1, vector2):
    """Test drift always returns values between -1 and 1"""
    ids = InterpretiveDriftSynthesizer()
    if len(vector1) == len(vector2):
        drift = ids.calculate_drift(vector1, vector2)
        assert -1 <= drift <= 1


@pytest.mark.property
def test_symmetry_properties():
    """Test certain symmetry properties of the IDS calculations"""
    ids = InterpretiveDriftSynthesizer()
    vector = [1.0, 0.5, 0.3]
    drift = ids.calculate_drift(vector, vector)
    assert abs(drift) < 0.1
    reversed_vector = list(reversed(vector))
    drift = ids.calculate_drift(vector, reversed_vector)
    assert abs(drift) > 0.5
