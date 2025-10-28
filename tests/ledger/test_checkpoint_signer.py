"""
Tests for checkpoint signer.

Phase 14-2: Merkle Checkpoints & PQC Signer
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from nova.ledger.checkpoint_signer import CheckpointSigner, Checkpoint


class TestCheckpointSigner:
    """Test checkpoint signing functionality."""

    @pytest.fixture
    def mock_store(self):
        """Mock PostgreSQL store."""
        store = AsyncMock()
        store.query_hashes_between.return_value = [
            "a" * 64,  # 64 hex chars = 32 bytes
            "b" * 64,
            "c" * 64
        ]
        store.insert_checkpoint = AsyncMock()
        return store

    @pytest.fixture
    def mock_keyring(self):
        """Mock PQC keyring."""
        keyring = MagicMock()
        keyring.sign_b64.return_value = ("test_sig_b64", "test_pubkey_id")
        keyring.verify_b64.return_value = True
        return keyring

    @pytest.fixture
    def signer(self, mock_store, mock_keyring):
        """Create signer with mocked dependencies."""
        with patch('nova.ledger.checkpoint_signer.Dilithium2Keyring', return_value=mock_keyring):
            return CheckpointSigner(mock_store)

    @pytest.mark.asyncio
    async def test_build_and_sign_success(self, signer, mock_store):
        """Test successful checkpoint creation and signing."""
        start_ts = "2025-10-28T10:00:00Z"
        end_ts = "2025-10-28T11:00:00Z"

        checkpoint = await signer.build_and_sign(start_ts, end_ts)

        assert isinstance(checkpoint, Checkpoint)
        assert checkpoint.range_start == start_ts
        assert checkpoint.range_end == end_ts
        assert checkpoint.records == 3
        assert checkpoint.sig_b64 == "test_sig_b64"
        assert checkpoint.pubkey_id == "test_pubkey_id"

        # Verify store was called
        mock_store.query_hashes_between.assert_called_once_with(start_ts, end_ts)
        mock_store.insert_checkpoint.assert_called_once()

    @pytest.mark.asyncio
    async def test_build_and_sign_no_records(self, signer, mock_store):
        """Test checkpoint creation fails with no records."""
        mock_store.query_hashes_between.return_value = []

        with pytest.raises(ValueError, match="No records found"):
            await signer.build_and_sign("2025-01-01T00:00:00Z", "2025-01-02T00:00:00Z")

    def test_verify_signature(self, signer, mock_keyring):
        """Test signature verification."""
        checkpoint = Checkpoint(
            cid="test-cid",
            merkle_root_hex="abcd" * 16,
            range_start="2025-01-01T00:00:00Z",
            range_end="2025-01-02T00:00:00Z",
            records=5,
            sig_b64="test_sig",
            pubkey_id="test_key"
        )

        result = signer.verify(checkpoint)
        assert result is True
        mock_keyring.verify_b64.assert_called_once()

    def test_canonical_header(self, signer):
        """Test header canonicalization is deterministic."""
        header1 = {
            "merkle_root_hex": "test_root",
            "range_start": "2025-01-01T00:00:00Z",
            "range_end": "2025-01-02T00:00:00Z",
            "records": 10,
            "algo": "sha3-256",
            "version": "cp-1.0"
        }

        # Same content, different key order
        header2 = {
            "version": "cp-1.0",
            "records": 10,
            "range_end": "2025-01-02T00:00:00Z",
            "range_start": "2025-01-01T00:00:00Z",
            "merkle_root_hex": "test_root",
            "algo": "sha3-256"
        }

        canonical1 = signer._canonical_header(header1)
        canonical2 = signer._canonical_header(header2)

        assert canonical1 == canonical2
        assert isinstance(canonical1, bytes)

    @pytest.mark.asyncio
    async def test_verify_range_success(self, signer, mock_store):
        """Test successful range verification."""
        mock_store.query_hashes_between.return_value = ["a" * 64, "b" * 64]

        checkpoint = Checkpoint(
            cid="test-cid",
            merkle_root_hex="abcd" * 16,  # Mock root
            range_start="2025-01-01T00:00:00Z",
            range_end="2025-01-02T00:00:00Z",
            records=2,
            sig_b64="test_sig",
            pubkey_id="test_key"
        )

        # Mock successful signature verification
        with patch.object(signer, 'verify', return_value=True):
            is_valid, error = await signer.verify_range(checkpoint)

            assert is_valid is True
            assert error == ""

    @pytest.mark.asyncio
    async def test_verify_range_signature_fail(self, signer):
        """Test range verification fails on bad signature."""
        checkpoint = Checkpoint(
            cid="test-cid",
            merkle_root_hex="abcd" * 16,
            range_start="2025-01-01T00:00:00Z",
            range_end="2025-01-02T00:00:00Z",
            records=2,
            sig_b64="bad_sig",
            pubkey_id="test_key"
        )

        with patch.object(signer, 'verify', return_value=False):
            is_valid, error = await signer.verify_range(checkpoint)

            assert is_valid is False
            assert "Invalid signature" in error

    @pytest.mark.asyncio
    async def test_verify_range_root_mismatch(self, signer, mock_store):
        """Test range verification fails on Merkle root mismatch."""
        mock_store.query_hashes_between.return_value = ["different" * 16]

        checkpoint = Checkpoint(
            cid="test-cid",
            merkle_root_hex="abcd" * 16,  # Won't match computed root
            range_start="2025-01-01T00:00:00Z",
            range_end="2025-01-02T00:00:00Z",
            records=2,
            sig_b64="test_sig",
            pubkey_id="test_key"
        )

        with patch.object(signer, 'verify', return_value=True):
            is_valid, error = await signer.verify_range(checkpoint)

            assert is_valid is False
            assert "Merkle root mismatch" in error