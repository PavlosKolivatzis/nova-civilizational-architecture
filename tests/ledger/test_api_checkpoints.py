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
        service.create_and_sign = AsyncMock()
        service.verify = AsyncMock()
        service.store = MagicMock()
        service.store.fetch_checkpoint = AsyncMock()
        # Configure default return values to avoid coroutine issues
        service.create_and_sign.return_value = None
        service.verify.return_value = True
        service.store.fetch_checkpoint.return_value = None
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
    async def test_create_checkpoint_success(self, client, mock_service):
        """Test successful checkpoint creation via API."""
        # Mock successful creation
        mock_checkpoint = MagicMock()
        mock_checkpoint.cid = "test-cid-123"
        mock_checkpoint.merkle_root = "abcd" * 16
        mock_checkpoint.range_start = "2025-01-01T00:00:00Z"
        mock_checkpoint.range_end = "2025-01-02T00:00:00Z"
        mock_checkpoint.record_count = 100
        mock_checkpoint.sig = b"test_signature"
        mock_checkpoint.key_id = "test_key_id"
        mock_checkpoint.created_at = None
        mock_checkpoint.to_dict.return_value = {
            "id": "test-cid-123",
            "merkle_root": "abcd" * 16,
            "start_rid": "2025-01-01T00:00:00Z",
            "end_rid": "2025-01-02T00:00:00Z",
            "record_count": 100,
            "sig": "test_signature",
            "key_id": "test_key_id"
        }

        mock_service.create_and_sign.return_value = mock_checkpoint

        response = client.post("/ledger/checkpoints/test-anchor-123")

        assert response.status_code == 200
        data = response.json()
        assert data["checkpoint"]["id"] == "test-cid-123"
        assert data["checkpoint"]["record_count"] == 100
        assert data["checkpoint"]["sig"] == "test_signature"

        mock_service.create_and_sign.assert_called_once_with("test-anchor-123")

    @pytest.mark.asyncio
    async def test_create_checkpoint_error(self, client, mock_service):
        """Test checkpoint creation error handling."""
        mock_service.create_and_sign.side_effect = ValueError("No records found")

        response = client.post("/ledger/checkpoints/test-anchor-123")

        assert response.status_code == 400
        assert "No records found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_checkpoint_success(self, client, mock_service):
        """Test getting checkpoint by ID."""
        mock_checkpoint = MagicMock()
        mock_checkpoint.cid = "specific-cid"
        mock_checkpoint.merkle_root = "1234" * 16
        mock_checkpoint.range_start = "2025-01-01T00:00:00Z"
        mock_checkpoint.range_end = "2025-01-02T00:00:00Z"
        mock_checkpoint.record_count = 150
        mock_checkpoint.sig = b"specific_sig"
        mock_checkpoint.key_id = "test_key"
        mock_checkpoint.created_at = None
        mock_checkpoint.to_dict.return_value = {
            "id": "specific-cid",
            "merkle_root": "1234" * 16,
            "start_rid": "2025-01-01T00:00:00Z",
            "end_rid": "2025-01-02T00:00:00Z",
            "record_count": 150,
            "sig": "specific_sig",
            "key_id": "test_key"
        }

        mock_service.store.fetch_checkpoint.return_value = mock_checkpoint

        response = client.get("/ledger/checkpoints/specific-cid")

        assert response.status_code == 200
        data = response.json()
        assert data["checkpoint"]["id"] == "specific-cid"
        assert data["checkpoint"]["record_count"] == 150

    @pytest.mark.asyncio
    async def test_get_checkpoint_not_found(self, client, mock_service):
        """Test getting non-existent checkpoint by ID."""
        mock_service.store.fetch_checkpoint.return_value = None

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
        mock_checkpoint.sig = b"verify_sig"
        mock_checkpoint.key_id = "test_key"
        mock_checkpoint.created_at = None

        mock_service.store.fetch_checkpoint.return_value = mock_checkpoint
        mock_service.verify.return_value = True

        response = client.get("/ledger/checkpoints/verify-cid/verify")

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True

    @pytest.mark.asyncio
    async def test_verify_checkpoint_failure(self, client, mock_service):
        """Test checkpoint verification failure."""
        mock_checkpoint = MagicMock()
        mock_checkpoint.cid = "bad-cid"
        mock_checkpoint.merkle_root = "bad" * 16
        mock_checkpoint.range_start = "2025-01-01T00:00:00Z"
        mock_checkpoint.range_end = "2025-01-02T00:00:00Z"
        mock_checkpoint.record_count = 50
        mock_checkpoint.sig = b"bad_sig"
        mock_checkpoint.key_id = "bad_key"
        mock_checkpoint.created_at = None

        mock_service.store.fetch_checkpoint.return_value = mock_checkpoint
        mock_service.verify.return_value = False

        response = client.get("/ledger/checkpoints/bad-cid/verify")

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False

    @pytest.mark.asyncio
    async def test_get_checkpoint_by_id_not_found(self, client, mock_service):
        """Test getting non-existent checkpoint by ID."""
        mock_service.store.fetch_checkpoint.return_value = None

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
        mock_checkpoint.sig = b"verify_sig"
        mock_checkpoint.key_id = "test_key"
        mock_checkpoint.created_at = None

        mock_service.store.fetch_checkpoint.return_value = mock_checkpoint
        mock_service.verify.return_value = True

        response = client.get("/ledger/checkpoints/verify-cid/verify")

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
        mock_checkpoint.sig = b"bad_sig"
        mock_checkpoint.key_id = "bad_key"
        mock_checkpoint.created_at = None

        mock_service.store.fetch_checkpoint.return_value = mock_checkpoint
        mock_service.verify.return_value = False

        response = client.get("/ledger/checkpoints/bad-cid/verify")

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert "Signature invalid" in data["error"]