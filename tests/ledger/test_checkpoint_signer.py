"""
Tests for checkpoint signer.

Phase 14-2: Merkle Checkpoints & PQC Signer
"""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from nova.ledger.checkpoint_signer import CheckpointSigner
from nova.ledger.checkpoint_types import Checkpoint


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
        keyring.sign_b64.return_value = ("bW9jay1zaWctMjA3", "test_key")  # base64 of "mock-sig-207"
        # For verification, accept any base64 string and return True
        keyring.verify_b64.side_effect = lambda msg, sig_b64, key_id: key_id == "test_key"
        return keyring

    @pytest.fixture
    def signer(self, mock_store, mock_keyring):
        """Create signer with mocked dependencies."""
        with patch('nova.crypto.pqc_keyring.PQCKeyring', return_value=mock_keyring):
            return CheckpointSigner(mock_store)

    @pytest.mark.asyncio
    async def test_sign_checkpoint_success(self, signer, mock_store):
        """Test successful checkpoint signing."""
        anchor_id = str(uuid.uuid4())
        start_rid = str(uuid.uuid4())
        end_rid = str(uuid.uuid4())
        merkle_root = "abcd" * 16

        checkpoint = await signer.sign_checkpoint(
            anchor_id=anchor_id,
            start_rid=start_rid,
            end_rid=end_rid,
            merkle_root=merkle_root
        )

        assert isinstance(checkpoint, Checkpoint)
        assert checkpoint.anchor_id == anchor_id
        assert checkpoint.start_rid == start_rid
        assert checkpoint.end_rid == end_rid
        assert checkpoint.merkle_root == merkle_root
        assert checkpoint.sig is not None
        assert checkpoint.key_id == "checkpoint-key-001"

    @pytest.mark.asyncio
    async def test_build_and_sign_no_records(self, signer, mock_store):
        """Test checkpoint creation fails with no records."""
        mock_store.query_hashes_between_rids = AsyncMock(return_value=[])

        checkpoint = await signer.build_and_sign(mock_store, "test-anchor", "rid-1", "rid-2")
        assert checkpoint is None  # Returns None when no hashes

    def test_verify_signature(self, mock_keyring):
        """Test signature verification."""
        checkpoint = Checkpoint(
            id="test-cid",
            anchor_id=str(uuid.uuid4()),
            merkle_root="abcd" * 16,
            start_rid=str(uuid.uuid4()),
            end_rid=str(uuid.uuid4()),
            prev_root=None,
            sig=bytes.fromhex("deadbeef"),  # bytes sig
            key_id="test_key"
        )

        # Create signer with mock store and replace _keyring directly
        mock_store = MagicMock()
        signer = CheckpointSigner(mock_store)
        signer._keyring = mock_keyring  # Direct assignment to bypass property
        result = signer.verify_checkpoint(checkpoint)
        assert result is True
        # Verify that verify_b64 was called (not verify)
        mock_keyring.verify_b64.assert_called_once()

    def test_canonical_header(self, signer):
        """Test header canonicalization is deterministic."""
        checkpoint1 = Checkpoint(
            id="test-id",
            anchor_id="test-anchor",
            merkle_root="test_root",
            start_rid="start-uuid",
            end_rid="end-uuid",
            prev_root=None,
            ts="2025-01-01T00:00:00Z"
        )

        # Same content, different order (but frozen dataclass)
        checkpoint2 = Checkpoint(
            id="test-id",
            anchor_id="test-anchor",
            merkle_root="test_root",
            start_rid="start-uuid",
            end_rid="end-uuid",
            prev_root=None,
            ts="2025-01-01T00:00:00Z"
        )

        canonical1 = signer._canonical_bytes(checkpoint1)
        canonical2 = signer._canonical_bytes(checkpoint2)

        assert canonical1 == canonical2
        assert isinstance(canonical1, bytes)

    @pytest.mark.asyncio
    async def test_verify_range_success(self, signer, mock_store):
        """Test successful range verification."""
        # Setup hashes that will produce expected root
        hashes = ["a" * 64, "b" * 64]
        mock_store.query_hashes_between_rids = AsyncMock(return_value=hashes)

        # Calculate expected root from hashes
        from nova.ledger.merkle import merkle_root_from_hashes
        expected_root = merkle_root_from_hashes(hashes)

        anchor_id = str(uuid.uuid4())
        start_rid = str(uuid.uuid4())
        end_rid = str(uuid.uuid4())

        is_valid, error = await signer.verify_range(mock_store, anchor_id, start_rid, end_rid, expected_root)

        assert is_valid is True
        assert error is None

    @pytest.mark.asyncio
    async def test_verify_range_signature_fail(self, signer, mock_store):
        """Test range verification with wrong Merkle root."""
        hashes = ["a" * 64, "b" * 64]
        mock_store.query_hashes_between_rids = AsyncMock(return_value=hashes)

        anchor_id = str(uuid.uuid4())
        start_rid = str(uuid.uuid4())
        end_rid = str(uuid.uuid4())
        wrong_root = "wrong" * 16  # Won't match computed root

        is_valid, error = await signer.verify_range(mock_store, anchor_id, start_rid, end_rid, wrong_root)

        assert is_valid is False
        assert "Merkle root mismatch" in error

    @pytest.mark.asyncio
    async def test_verify_range_root_mismatch(self, signer, mock_store):
        """Test range verification fails on Merkle root mismatch (duplicate test, keeping for coverage)."""
        hashes = ["different" * 16]
        mock_store.query_hashes_between_rids = AsyncMock(return_value=hashes)

        anchor_id = str(uuid.uuid4())
        start_rid = str(uuid.uuid4())
        end_rid = str(uuid.uuid4())
        wrong_root = "abcd" * 16  # Won't match computed root

        is_valid, error = await signer.verify_range(mock_store, anchor_id, start_rid, end_rid, wrong_root)

        assert is_valid is False
        assert "Merkle root mismatch" in error
