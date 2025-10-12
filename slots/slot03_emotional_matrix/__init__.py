# ruff: noqa: E402
"""Compatibility shim for nova.slots.slot03_emotional_matrix."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
import sys

from src_bootstrap import ensure_src_on_path

ensure_src_on_path()

_target = "nova.slots.slot03_emotional_matrix"
_module = import_module(_target)

# Re-export everything from the nova package
globals().update({k: getattr(_module, k) for k in getattr(_module, '__all__', dir(_module)) if not k.startswith('__')})
__all__ = getattr(_module, '__all__', [name for name in globals() if not name.startswith('_')])
__path__ = [str(Path(__file__).resolve().parents[2] / 'src' / 'nova' / 'slots' / 'slot03_emotional_matrix')]
__spec__ = getattr(_module, '__spec__', None)
__package__ = getattr(_module, '__package__', _target)

sys.modules.setdefault(_target, _module)
sys.modules[__name__] = _module
