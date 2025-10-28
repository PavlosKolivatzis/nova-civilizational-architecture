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
    def mock_signer(self):
        """Mock checkpoint signer."""
        signer = MagicMock()
        signer.store = AsyncMock()
        return signer

    @pytest.fixture
    def service(self, mock_signer):
        """Create checkpoint service."""
        return CheckpointService(
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
        assert service._running is False
        assert service._last_checkpoint_ts is None

    @pytest.mark.asyncio
    async def test_roll_once_success(self, service, mock_signer):
        """Test successful checkpoint rolling."""
        # Mock successful signing
        mock_checkpoint = MagicMock()
        mock_checkpoint.cid = "test-cid"
        mock_signer.build_and_sign = AsyncMock(return_value=mock_checkpoint)
        mock_signer.verify_range = AsyncMock(return_value=(True, ""))

        checkpoint = await service.roll_once("2025-01-01T00:00:00Z", "2025-01-02T00:00:00Z")

        assert checkpoint == mock_checkpoint
        mock_signer.build_and_sign.assert_called_once_with("2025-01-01T00:00:00Z", "2025-01-02T00:00:00Z")
        mock_signer.verify_range.assert_called_once_with(mock_checkpoint)

    @pytest.mark.asyncio
    async def test_roll_once_defaults(self, service, mock_signer):
        """Test roll_once uses defaults when no timestamps provided."""
        mock_checkpoint = MagicMock()
        mock_signer.build_and_sign = AsyncMock(return_value=mock_checkpoint)
        mock_signer.verify_range = AsyncMock(return_value=(True, ""))

        # Mock the helper methods
        service._get_last_checkpoint_end_ts = AsyncMock(return_value="2025-01-01T00:00:00Z")
        service._current_iso_timestamp = MagicMock(return_value="2025-01-02T00:00:00Z")

        checkpoint = await service.roll_once()

        mock_signer.build_and_sign.assert_called_once_with("2025-01-01T00:00:00Z", "2025-01-02T00:00:00Z")

    @pytest.mark.asyncio
    async def test_roll_once_verification_failure(self, service, mock_signer):
        """Test roll_once fails when verification fails."""
        mock_checkpoint = MagicMock()
        mock_signer.build_and_sign = AsyncMock(return_value=mock_checkpoint)
        mock_signer.verify_range = AsyncMock(return_value=(False, "Verification failed"))

        with pytest.raises(ValueError, match="Checkpoint verification failed"):
            await service.roll_once()

    @pytest.mark.asyncio
    async def test_get_last_checkpoint_end_ts_with_checkpoint(self, service, mock_signer):
        """Test getting end timestamp from existing checkpoint."""
        mock_checkpoint = MagicMock()
        mock_checkpoint.range_end = "2025-01-01T12:00:00Z"
        mock_signer.store.get_latest_checkpoint = AsyncMock(return_value=mock_checkpoint)

        end_ts = await service._get_last_checkpoint_end_ts()
        assert end_ts == "2025-01-01T12:00:00Z"

    @pytest.mark.asyncio
    async def test_get_last_checkpoint_end_ts_no_checkpoint(self, service, mock_signer):
        """Test getting end timestamp when no checkpoints exist."""
        mock_signer.store.get_latest_checkpoint = AsyncMock(return_value=None)

        end_ts = await service._get_last_checkpoint_end_ts()
        assert end_ts == "2025-01-01T00:00:00Z"  # Epoch fallback

    @pytest.mark.asyncio
    async def test_should_roll_checkpoint_time_based(self, service):
        """Test time-based checkpoint triggering."""
        service._last_checkpoint_ts = 1000  # Old timestamp

        with patch('time.time', return_value=2000):  # 1000 seconds later
            should_roll = await service._should_roll_checkpoint()
            assert should_roll is True

    @pytest.mark.asyncio
    async def test_should_roll_checkpoint_record_based(self, service, mock_signer):
        """Test record-based checkpoint triggering."""
        service._last_checkpoint_ts = 2000  # Recent timestamp
        mock_signer.store.count_records_since = AsyncMock(return_value=1500)  # Above threshold

        with patch('time.time', return_value=2100):  # Within time window
            should_roll = await service._should_roll_checkpoint()
            assert should_roll is True

    @pytest.mark.asyncio
    async def test_should_roll_checkpoint_no_trigger(self, service, mock_signer):
        """Test checkpoint not triggered when conditions not met."""
        service._last_checkpoint_ts = 2000  # Recent timestamp
        mock_signer.store.count_records_since = AsyncMock(return_value=500)  # Below threshold

        with patch('time.time', return_value=2100):  # Within time window
            should_roll = await service._should_roll_checkpoint()
            assert should_roll is False

    @pytest.mark.asyncio
    async def test_run_forever_disabled(self):
        """Test service doesn't run when disabled."""
        service = CheckpointService(
            signer=MagicMock(),
            enabled=False
        )

        stop_event = asyncio.Event()
        stop_event.set()  # Immediately stop

        await service.run_forever(stop_event)
        assert not service.is_running

    def test_current_iso_timestamp(self, service):
        """Test ISO timestamp generation."""
        with patch('nova.ledger.checkpoint_service.datetime') as mock_dt:
            mock_dt.now.return_value.now.return_value.isoformat.return_value = "2025-01-01T12:00:00Z"

            ts = service._current_iso_timestamp()
            assert ts == "2025-01-01T12:00:00Z"

    @pytest.mark.asyncio
    async def test_disabled_service_roll_fails(self):
        """Test disabled service rejects roll operations."""
        service = CheckpointService(
            signer=MagicMock(),
            enabled=False
        )

        with pytest.raises(RuntimeError, match="Checkpoint service is disabled"):
            await service.roll_once()