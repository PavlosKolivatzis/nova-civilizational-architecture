"""
Deterministic Merkle tree builder for ledger checkpoints.

Phase 14-2: Merkle Checkpoints & PQC Signer
"""

import hashlib
from typing import Iterable, List


def _h(x: bytes) -> bytes:
    """SHA3-256 hash function for Merkle tree."""
    return hashlib.sha3_256(x).digest()


def merkle_root(hashes: Iterable[bytes]) -> bytes:
    """
    Compute deterministic Merkle root from ordered hash list.

    Uses left-padding for odd levels (duplicate last hash).
    Empty tree returns hash of empty string.

    Args:
        hashes: Ordered iterable of hash bytes

    Returns:
        Merkle root as bytes
    """
    level: List[bytes] = list(hashes)

    # Empty tree convention
    if not level:
        return _h(b"")

    # Build tree level by level
    while len(level) > 1:
        # Pad odd levels by duplicating last hash
        if len(level) % 2 == 1:
            level.append(level[-1])

        # Hash pairs
        level = [_h(level[i] + level[i + 1]) for i in range(0, len(level), 2)]

    return level[0]


def merkle_proof(hashes: List[bytes], target_index: int) -> List[bytes]:
    """
    Generate Merkle proof for a specific hash in the tree.

    Args:
        hashes: Ordered list of all hashes in the tree
        target_index: Index of the hash to prove

    Returns:
        List of sibling hashes needed for verification
    """
    if not hashes or target_index >= len(hashes):
        raise ValueError("Invalid target index")

    proof = []
    level = hashes[:]

    while len(level) > 1:
        # Ensure even length
        if len(level) % 2 == 1:
            level.append(level[-1])

        # Find sibling
        if target_index % 2 == 0:
            # Left sibling
            if target_index + 1 < len(level):
                proof.append(level[target_index + 1])
        else:
            # Right sibling
            proof.append(level[target_index - 1])

        # Move to next level
        level = [_h(level[i] + level[i + 1]) for i in range(0, len(level), 2)]
        target_index //= 2

    return proof


def verify_merkle_proof(root: bytes, target_hash: bytes, proof: List[bytes], target_index: int) -> bool:
    """
    Verify a Merkle proof.

    Args:
        root: Expected Merkle root
        target_hash: Hash being proven
        proof: List of sibling hashes
        target_index: Original index of target_hash

    Returns:
        True if proof is valid
    """
    current = target_hash
    index = target_index

    for sibling in proof:
        if index % 2 == 0:
            # Current is left, sibling is right
            current = _h(current + sibling)
        else:
            # Current is right, sibling is left
            current = _h(sibling + current)
        index //= 2

    return current == root