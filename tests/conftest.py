"""
Pytest configuration and fixtures.

Phase 14-2: Merkle Checkpoints & PQC Signer
"""

import pytest
import prometheus_client
from prometheus_client import CollectorRegistry

# Fresh registry for the entire test session to avoid cross-test pollution
prometheus_client.REGISTRY = CollectorRegistry()
