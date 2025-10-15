from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Mapping

from ..models import ProcessingResult

CURRENT_VERSION = "v1"


def adapt_processing_result(payload: Any) -> ProcessingResult:
    """Translate payload into a ProcessingResult of the current version.

    Accepts dictionaries, dataclass instances, or objects with ``__dict__``.
    Missing version fields are assumed to be ``CURRENT_VERSION``.
    """
    if isinstance(payload, ProcessingResult):
        data: Dict[str, Any] = asdict(payload)
    elif is_dataclass(payload) and not isinstance(payload, type):
        data = asdict(payload)
    elif isinstance(payload, Mapping):
        data = dict(payload)
    else:
        data = dict(getattr(payload, "__dict__", {}))
    version = data.get("version")
    if not version:
        version = CURRENT_VERSION
        data["version"] = version
    if version != CURRENT_VERSION:
        raise ValueError(f"Unsupported ProcessingResult version: {version}")
    return ProcessingResult(**data)


def strip_version(result: ProcessingResult) -> Dict[str, Any]:
    """Return a legacy dictionary without version information."""
    data = asdict(result)
    data.pop("version", None)
    return data
