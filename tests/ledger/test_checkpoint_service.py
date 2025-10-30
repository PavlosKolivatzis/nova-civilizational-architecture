"""
Tests for checkpoint service.

Phase 14-2: Merkle Checkpoints & PQC Signer
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from nova.ledger.checkpoint_service import CheckpointService


class TestCheckpointService:
    """Test checkpoint service functionality."""

    @pytest.fixture
    def mock_store(self):
        """Mock ledger store."""
        store = AsyncMock()
        return store

    @pytest.fixture
    def mock_signer(self):
        """Mock checkpoint signer."""
        signer = MagicMock()
        signer.store = AsyncMock()
        return signer

    @pytest.fixture
    def service(self, mock_store, mock_signer):
        """Create checkpoint service."""
        return CheckpointService(
            store=mock_store,
            signer=mock_signer,
            every_seconds=300,
            min_records=1000,
            enabled=True
        )

    def test_initialization(self, service):
        """Test service initialization."""
        assert service.every_seconds == 300
        assert service.min_records == 1000
        assert service.enabled is True
        assert service.state.last_roll_ts is None


    @pytest.mark.asyncio
    async def test_run_forever_disabled(self):
        """Test service doesn't run when disabled."""
        service = CheckpointService(
            store=AsyncMock(),
            signer=MagicMock(),
            enabled=False
        )

        # Should return immediately without error
        await service.run_forever()

    @pytest.mark.asyncio
    async def test_disabled_service_roll_fails(self):
        """Test disabled service rejects roll operations."""
        service = CheckpointService(
            store=AsyncMock(),
            signer=MagicMock(),
            enabled=False
        )

        with pytest.raises(ValueError, match="Checkpoint service is disabled"):
            await service.roll_once()