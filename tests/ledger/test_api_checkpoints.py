"""
Tests for checkpoint API endpoints.

Phase 14-2: Merkle Checkpoints & PQC Signer
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from nova.ledger.api_checkpoints import create_checkpoint_router
from nova.ledger.checkpoint_service import CheckpointService


class TestCheckpointAPI:
    """Test checkpoint REST API endpoints."""

    @pytest.fixture
    def mock_service(self):
        """Mock checkpoint service."""
        service = MagicMock(spec=CheckpointService)
        service.roll_once = AsyncMock()
        service.signer = MagicMock()
        service.signer.store = MagicMock()
        service.signer.store.get_latest_checkpoint = AsyncMock()
        service.signer.store.get_checkpoint = AsyncMock()
        service.signer.verify_range = AsyncMock()
        return service

    @pytest.fixture
    def app(self, mock_service):
        """Create FastAPI test app."""
        app = FastAPI()
        router = create_checkpoint_router(mock_service)
        app.include_router(router)
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    @pytest.mark.asyncio
    async def test_roll_checkpoint_success(self, client, mock_service):
        """Test successful checkpoint rolling via API."""
        # Mock successful roll
        mock_checkpoint = MagicMock()
        mock_checkpoint.cid = "test-cid-123"
        mock_checkpoint.merkle_root_hex = "abcd" * 16
        mock_checkpoint.range_start = "2025-01-01T00:00:00Z"
        mock_checkpoint.range_end = "2025-01-02T00:00:00Z"
        mock_checkpoint.records = 100
        mock_checkpoint.algo = "sha3-256"
        mock_checkpoint.version = "cp-1.0"
        mock_checkpoint.sig_b64 = "test_signature"
        mock_checkpoint.pubkey_id = "test_key_id"
        mock_checkpoint.created_at = None

        mock_service.roll_once.return_value = mock_checkpoint

        response = client.post("/ledger/checkpoints/roll", json={
            "start_ts": "2025-01-01T00:00:00Z",
            "end_ts": "2025-01-02T00:00:00Z"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["cid"] == "test-cid-123"
        assert data["records"] == 100
        assert data["sig_b64"] == "test_signature"

        mock_service.roll_once.assert_called_once_with(
            start_ts="2025-01-01T00:00:00Z",
            end_ts="2025-01-02T00:00:00Z"
        )

    @pytest.mark.asyncio
    async def test_roll_checkpoint_defaults(self, client, mock_service):
        """Test checkpoint rolling with default timestamps."""
        mock_checkpoint = MagicMock()
        mock_checkpoint.cid = "test-cid"
        mock_checkpoint.merkle_root_hex = "abcd" * 16
        mock_checkpoint.range_start = "2025-01-01T00:00:00Z"
        mock_checkpoint.range_end = "2025-01-02T00:00:00Z"
        mock_checkpoint.records = 50
        mock_checkpoint.algo = "sha3-256"
        mock_checkpoint.version = "cp-1.0"
        mock_checkpoint.sig_b64 = "test_sig"
        mock_checkpoint.pubkey_id = "test_key"
        mock_checkpoint.created_at = None

        mock_service.roll_once.return_value = mock_checkpoint

        response = client.post("/ledger/checkpoints/roll", json={})

        assert response.status_code == 200
        mock_service.roll_once.assert_called_once_with(start_ts=None, end_ts=None)

    @pytest.mark.asyncio
    async def test_roll_checkpoint_error(self, client, mock_service):
        """Test checkpoint rolling error handling."""
        mock_service.roll_once.side_effect = ValueError("No records found")

        response = client.post("/ledger/checkpoints/roll", json={
            "start_ts": "2025-01-01T00:00:00Z",
            "end_ts": "2025-01-02T00:00:00Z"
        })

        assert response.status_code == 500
        assert "Failed to create checkpoint" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_latest_checkpoint_success(self, client, mock_service):
        """Test getting latest checkpoint."""
        # Mock legacy checkpoint format
        mock_checkpoint = MagicMock()
        mock_checkpoint.cid = "latest-cid"
        mock_checkpoint.merkle_root = "abcd" * 16
        mock_checkpoint.range_start = "2025-01-01T00:00:00Z"
        mock_checkpoint.range_end = "2025-01-02T00:00:00Z"
        mock_checkpoint.record_count = 200
        mock_checkpoint.sig = "legacy_sig".encode()
        mock_checkpoint.created_at = MagicMock()
        mock_checkpoint.created_at.isoformat.return_value = "2025-01-02T12:00:00Z"

        mock_service.signer.store.get_latest_checkpoint.return_value = mock_checkpoint

        response = client.get("/ledger/checkpoints/latest")

        assert response.status_code == 200
        data = response.json()
        assert data["cid"] == "latest-cid"
        assert data["records"] == 200
        assert data["sig_b64"] == "legacy_sig"

    @pytest.mark.asyncio
    async def test_get_latest_checkpoint_not_found(self, client, mock_service):
        """Test getting latest checkpoint when none exists."""
        mock_service.signer.store.get_latest_checkpoint.return_value = None

        response = client.get("/ledger/checkpoints/latest")

        assert response.status_code == 404
        assert "No checkpoints found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_checkpoint_by_id_success(self, client, mock_service):
        """Test getting checkpoint by ID."""
        mock_checkpoint = MagicMock()
        mock_checkpoint.cid = "specific-cid"
        mock_checkpoint.merkle_root = "1234" * 16
        mock_checkpoint.range_start = "2025-01-01T00:00:00Z"
        mock_checkpoint.range_end = "2025-01-02T00:00:00Z"
        mock_checkpoint.record_count = 150
        mock_checkpoint.sig = "specific_sig".encode()
        mock_checkpoint.created_at = MagicMock()
        mock_checkpoint.created_at.isoformat.return_value = "2025-01-02T12:00:00Z"

        mock_service.signer.store.get_checkpoint.return_value = mock_checkpoint

        response = client.get("/ledger/checkpoints/specific-cid")

        assert response.status_code == 200
        data = response.json()
        assert data["cid"] == "specific-cid"
        assert data["records"] == 150

    @pytest.mark.asyncio
    async def test_get_checkpoint_by_id_not_found(self, client, mock_service):
        """Test getting non-existent checkpoint by ID."""
        mock_service.signer.store.get_checkpoint.return_value = None

        response = client.get("/ledger/checkpoints/non-existent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_verify_checkpoint_success(self, client, mock_service):
        """Test successful checkpoint verification."""
        mock_checkpoint = MagicMock()
        mock_checkpoint.cid = "verify-cid"
        mock_checkpoint.merkle_root = "abcd" * 16
        mock_checkpoint.range_start = "2025-01-01T00:00:00Z"
        mock_checkpoint.range_end = "2025-01-02T00:00:00Z"
        mock_checkpoint.record_count = 100
        mock_checkpoint.sig = "verify_sig".encode()
        mock_checkpoint.created_at = MagicMock()

        mock_service.signer.store.get_checkpoint.return_value = mock_checkpoint
        mock_service.signer.verify_range.return_value = (True, "")

        response = client.post("/ledger/checkpoints/verify-cid/verify")

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["error"] == ""
        assert data["checkpoint"]["cid"] == "verify-cid"

    @pytest.mark.asyncio
    async def test_verify_checkpoint_failure(self, client, mock_service):
        """Test checkpoint verification failure."""
        mock_checkpoint = MagicMock()
        mock_checkpoint.cid = "bad-cid"
        mock_checkpoint.merkle_root = "bad" * 16
        mock_checkpoint.range_start = "2025-01-01T00:00:00Z"
        mock_checkpoint.range_end = "2025-01-02T00:00:00Z"
        mock_checkpoint.record_count = 50
        mock_checkpoint.sig = "bad_sig".encode()
        mock_checkpoint.created_at = MagicMock()

        mock_service.signer.store.get_checkpoint.return_value = mock_checkpoint
        mock_service.signer.verify_range.return_value = (False, "Signature invalid")

        response = client.post("/ledger/checkpoints/bad-cid/verify")

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert "Signature invalid" in data["error"]