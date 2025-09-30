"""
FastAPI metrics endpoint for Prometheus scraping.
Exports all Nova metrics including build provenance and runtime stats.
"""

from fastapi import APIRouter, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from orchestrator.prometheus_metrics import _REGISTRY

router = APIRouter()

@router.get("/metrics")
def metrics():
    """Prometheus metrics endpoint with full Nova telemetry."""
    return Response(generate_latest(_REGISTRY), media_type=CONTENT_TYPE_LATEST)