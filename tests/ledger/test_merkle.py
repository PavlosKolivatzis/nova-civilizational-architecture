"""
Tests for Merkle tree builder.

Phase 14-2: Merkle Checkpoints & PQC Signer
"""

import pytest
from nova.ledger.merkle import merkle_root, merkle_proof, verify_merkle_proof


class TestMerkleRoot:
    """Test Merkle root computation."""

    def test_empty_tree(self):
        """Empty tree returns hash of empty string."""
        root = merkle_root([])
        # SHA3-256 of empty string
        expected = "a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a"
        assert root.hex() == expected

    def test_single_hash(self):
        """Single hash returns itself."""
        hash_bytes = b"test_hash_32_bytes_abcdefghijk"
        assert len(hash_bytes) == 32

        root = merkle_root([hash_bytes])
        assert root == hash_bytes

    def test_two_hashes(self):
        """Two hashes create proper root."""
        h1 = b"x" * 32
        h2 = b"y" * 32

        root = merkle_root([h1, h2])

        # Manual computation: SHA3-256(h1 + h2)
        import hashlib
        expected = hashlib.sha3_256(h1 + h2).digest()
        assert root == expected

    def test_three_hashes(self):
        """Three hashes pad and create proper tree."""
        h1 = b"a" * 32
        h2 = b"b" * 32
        h3 = b"c" * 32

        root = merkle_root([h1, h2, h3])

        # Level 1: [h1, h2, h3, h3] (padded)
        # Level 2: [SHA3(h1+h2), SHA3(h3+h3)]
        # Root: SHA3(SHA3(h1+h2) + SHA3(h3+h3))

        import hashlib
        l1_1 = hashlib.sha3_256(h1 + h2).digest()
        l1_2 = hashlib.sha3_256(h3 + h3).digest()
        expected = hashlib.sha3_256(l1_1 + l1_2).digest()

        assert root == expected

    def test_deterministic(self):
        """Same inputs produce same root."""
        hashes = [b"x" * 32 for _ in range(5)]

        root1 = merkle_root(hashes)
        root2 = merkle_root(hashes)

        assert root1 == root2

    def test_order_matters(self):
        """Different order produces different root."""
        h1 = b"a" * 32
        h2 = b"b" * 32

        root1 = merkle_root([h1, h2])
        root2 = merkle_root([h2, h1])

        assert root1 != root2


class TestMerkleProof:
    """Test Merkle proof generation and verification."""

    def test_single_element_proof(self):
        """Proof for single element tree."""
        hashes = [b"x" * 32]
        proof = merkle_proof(hashes, 0)

        # Single element tree: proof should be empty
        assert proof == []

        # Verification should pass
        assert verify_merkle_proof(merkle_root(hashes), hashes[0], proof, 0)

    def test_two_element_proof(self):
        """Proof for two element tree."""
        h1 = b"a" * 32
        h2 = b"b" * 32
        hashes = [h1, h2]

        # Proof for h1 (index 0)
        proof = merkle_proof(hashes, 0)
        assert len(proof) == 1
        assert proof[0] == h2  # Sibling is h2

        root = merkle_root(hashes)
        assert verify_merkle_proof(root, h1, proof, 0)

        # Proof for h2 (index 1)
        proof = merkle_proof(hashes, 1)
        assert len(proof) == 1
        assert proof[0] == h1  # Sibling is h1

        assert verify_merkle_proof(root, h2, proof, 1)

    def test_three_element_proof(self):
        """Proof for three element tree (with padding)."""
        h1 = b"a" * 32
        h2 = b"b" * 32
        h3 = b"c" * 32
        hashes = [h1, h2, h3]

        root = merkle_root(hashes)

        # Proof for h1 (index 0)
        proof = merkle_proof(hashes, 0)
        assert verify_merkle_proof(root, h1, proof, 0)

        # Proof for h3 (index 2) - sibling should be h3 (padded)
        proof = merkle_proof(hashes, 2)
        assert verify_merkle_proof(root, h3, proof, 2)

    def test_invalid_proof(self):
        """Invalid proof should fail verification."""
        h1 = b"a" * 32
        h2 = b"b" * 32
        hashes = [h1, h2]

        root = merkle_root(hashes)

        # Wrong sibling
        wrong_proof = [b"wrong" * 32]
        assert not verify_merkle_proof(root, h1, wrong_proof, 0)

    def test_invalid_index(self):
        """Invalid index should raise ValueError."""
        hashes = [b"x" * 32]
        with pytest.raises(ValueError):
            merkle_proof(hashes, 1)  # Index out of range

        with pytest.raises(ValueError):
            merkle_proof([], 0)  # Empty list