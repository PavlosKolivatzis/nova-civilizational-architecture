import numpy as np
import pytest

from orchestrator.core.quantization import (
    QuantizedWeight8bit,
    flatten_quantized_weight,
    unflatten_quantized_weight,
)


def test_quantized_weight_dequantize_handles_broadcast():
    weight = np.array([[1, 2], [3, 4]], dtype=np.uint8)
    scales = np.array([0.5], dtype=np.float32)

    qw = QuantizedWeight8bit(weight=weight, scales=scales)
    expected = weight.astype(np.float32) * scales.astype(np.float32)
    np.testing.assert_allclose(qw.dequantize(), expected)
    assert qw.shape == (2, 2)


def test_quantized_weight_rejects_non_integer_weight():
    with pytest.raises(TypeError):
        QuantizedWeight8bit(weight=np.array([1.0], dtype=np.float32), scales=np.array([1.0]))


def test_quantized_weight_round_trip_flatten():
    weight = np.arange(6, dtype=np.uint8).reshape(2, 3)
    scales = np.full((1, 3), 0.25, dtype=np.float32)
    original = QuantizedWeight8bit(weight=weight, scales=scales)

    children, aux = flatten_quantized_weight(original)
    rebuilt = unflatten_quantized_weight(children, aux)

    np.testing.assert_array_equal(rebuilt.weight, weight)
    np.testing.assert_array_equal(rebuilt.scales, scales)
    np.testing.assert_allclose(rebuilt.dequantize(), original.dequantize())
