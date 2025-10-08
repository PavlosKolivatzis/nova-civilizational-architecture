"""Quantization utilities derived from Grok-1 reference implementation.

Provides a thin wrapper to represent 8-bit quantized weights alongside their
scale factors in a way that plugs into NOVA checkpoint tooling.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Tuple

import numpy as np


@dataclass(frozen=True)
class QuantizedWeight8bit:
    """Container for 8-bit quantised weights and their scale factors.

    Args:
        weight: Integer tensor holding the quantised values.
        scales: Floating point scale factors for de-quantisation. The tensor is
            broadcast against ``weight``.
    """

    weight: np.ndarray
    scales: np.ndarray

    def __post_init__(self) -> None:
        weight = np.asarray(self.weight)
        scales = np.asarray(self.scales)
        if weight.dtype not in (np.uint8, np.int8):
            raise TypeError(
                "QuantizedWeight8bit.weight must be uint8 or int8, got"
                f" {weight.dtype}"
            )
        if scales.dtype.kind not in {"f", "i"}:
            raise TypeError(
                "QuantizedWeight8bit.scales must be numeric, got"
                f" {scales.dtype}"
            )
        # Normalise to contiguous arrays to avoid surprises during broadcasting.
        object.__setattr__(self, "weight", np.ascontiguousarray(weight))
        object.__setattr__(self, "scales", np.ascontiguousarray(scales))

    @property
    def shape(self) -> Tuple[int, ...]:
        """Expose the shape of the underlying quantised tensor."""

        return tuple(self.weight.shape)

    def dequantize(self, dtype: np.dtype = np.float32) -> np.ndarray:
        """Convert quantised weights back to floating point array."""

        return self.weight.astype(dtype) * self.scales.astype(dtype)


def flatten_quantized_weight(qw: QuantizedWeight8bit) -> Tuple[Sequence[np.ndarray], Tuple[()]]:
    """Return pytree-compatible flattening for :class:`QuantizedWeight8bit`."""

    return (qw.weight, qw.scales), ()


def unflatten_quantized_weight(children: Sequence[np.ndarray], aux_data: Tuple[()]) -> QuantizedWeight8bit:
    """Inverse operation for :func:`flatten_quantized_weight`."""

    del aux_data
    weight, scales = children
    return QuantizedWeight8bit(weight=weight, scales=scales)
