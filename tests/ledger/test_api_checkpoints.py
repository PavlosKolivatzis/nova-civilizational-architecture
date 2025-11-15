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
        service.create = AsyncMock()
        service.get_last = AsyncMock()
        service.verify_range = AsyncMock()
        # Configure default return values to avoid coroutine issues
        service.create.return_value = None
        service.get_last.return_value = None
        service.verify_range.return_value = (True, None)
        return service

    @pytest.fixture
    def app(self, mock_service):
        """Create FastAPI test app."""
        from nova.ledger.api_checkpoints import router, get_service

        app = FastAPI()

        # Override the dependency to return our mock
        app.dependency_overrides[get_service] = lambda: mock_service

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
        mock_checkpoint.id = "test-cid-123"
        mock_checkpoint.merkle_root = "abcd" * 16
        mock_checkpoint.key_id = "test_key_id"

        mock_service.create.return_value = mock_checkpoint

        response = client.post("/ledger/checkpoints/", json={
            "anchor_id": "test-anchor-123",
            "start_rid": "rid-start",
            "end_rid": "rid-end"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-cid-123"
        assert data["merkle_root"] == "abcd" * 16
        assert data["key_id"] == "test_key_id"

        mock_service.create.assert_called_once_with("test-anchor-123", "rid-start", "rid-end")

    @pytest.mark.asyncio
    async def test_create_checkpoint_error(self, client, mock_service):
        """Test checkpoint creation error handling."""
        mock_service.create.side_effect = ValueError("No records found")

        response = client.post("/ledger/checkpoints/", json={
            "anchor_id": "test-anchor-123",
            "start_rid": "rid-start",
            "end_rid": "rid-end"
        })

        assert response.status_code == 400
        assert "No records found" in response.json()["error"]

    @pytest.mark.asyncio
    async def test_get_checkpoint_success(self, client, mock_service):
        """Test getting last checkpoint for an anchor."""
        mock_checkpoint = MagicMock()
        mock_checkpoint.id = "specific-cid"
        mock_checkpoint.merkle_root = "1234" * 16
        mock_checkpoint.key_id = "test_key"

        mock_service.get_last.return_value = mock_checkpoint

        response = client.get("/ledger/checkpoints/test-anchor-123")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "specific-cid"
        assert data["merkle_root"] == "1234" * 16
        assert data["key_id"] == "test_key"
        mock_service.get_last.assert_called_once_with("test-anchor-123")

    @pytest.mark.asyncio
    async def test_get_checkpoint_not_found(self, client, mock_service):
        """Test getting checkpoint for anchor with no checkpoints."""
        mock_service.get_last.return_value = None

        response = client.get("/ledger/checkpoints/non-existent-anchor")

        assert response.status_code == 404
        assert "Not found" in response.json()["detail"]
        mock_service.get_last.assert_called_once_with("non-existent-anchor")

    @pytest.mark.asyncio
    async def test_verify_checkpoint_success(self, client, mock_service):
        """Test successful checkpoint verification."""
        mock_service.verify_range.return_value = (True, None)

        response = client.post("/ledger/checkpoints/verify", json={
            "anchor_id": "test-anchor",
            "start_rid": "rid-start",
            "end_rid": "rid-end",
            "merkle_root": "abcd" * 16
        })

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        mock_service.verify_range.assert_called_once_with("test-anchor", "rid-start", "rid-end", "abcd" * 16)

    @pytest.mark.asyncio
    async def test_verify_checkpoint_failure(self, client, mock_service):
        """Test checkpoint verification failure."""
        mock_service.verify_range.return_value = (False, "Merkle root mismatch")

        response = client.post("/ledger/checkpoints/verify", json={
            "anchor_id": "test-anchor",
            "start_rid": "rid-start",
            "end_rid": "rid-end",
            "merkle_root": "bad" * 16
        })

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is False
        assert data["error"] == "Merkle root mismatch"
        mock_service.verify_range.assert_called_once_with("test-anchor", "rid-start", "rid-end", "bad" * 16)
