"""
FastAPI metrics endpoint router for Prometheus scraping.

NOTE: This router is NOT included in the main app (orchestrator/app.py).
The production /metrics endpoint is defined directly in app.py:308 with
NOVA_ENABLE_PROMETHEUS flag gating and legacy fallback logic.

This router exists for:
- Standalone testing (see tests/metrics/test_build_info.py)
- Optional inclusion in custom FastAPI apps
- Reference implementation without flag gating

Production users should rely on app.py /metrics endpoint.
"""

from fastapi import APIRouter, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from nova.orchestrator.prometheus_metrics import _REGISTRY

router = APIRouter()

@router.get("/metrics")
def metrics():
    """Prometheus metrics endpoint with full Nova telemetry (test/reference only)."""
    return Response(generate_latest(_REGISTRY), media_type=CONTENT_TYPE_LATEST)
