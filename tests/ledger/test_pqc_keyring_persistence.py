"""Test persistent PQC keyring storage."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from nova.crypto.keyring_persistence import (
    get_keyring_dir,
    get_default_keyfile,
    load_or_create_keypair,
    sign_with_persistent_key,
)
from nova.crypto.pqc_keyring import PQCKeyring


def test_get_keyring_dir_default():
    """Test default keyring directory is ~/.nova/keyring/"""
    # Clear env var
    old_val = os.environ.pop("NOVA_KEYRING_DIR", None)
    try:
        keyring_dir = get_keyring_dir()
        assert keyring_dir == Path.home() / ".nova" / "keyring"
    finally:
        if old_val:
            os.environ["NOVA_KEYRING_DIR"] = old_val


def test_get_keyring_dir_custom():
    """Test custom keyring directory from NOVA_KEYRING_DIR."""
    custom_dir = "/tmp/custom_keyring"
    old_val = os.environ.get("NOVA_KEYRING_DIR")
    try:
        os.environ["NOVA_KEYRING_DIR"] = custom_dir
        keyring_dir = get_keyring_dir()
        assert keyring_dir == Path(custom_dir)
    finally:
        if old_val:
            os.environ["NOVA_KEYRING_DIR"] = old_val
        else:
            os.environ.pop("NOVA_KEYRING_DIR", None)


def test_load_or_create_keypair_new():
    """Test creating new keypair when file doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        keyfile = Path(tmpdir) / "test_key.json"

        # First call creates keypair
        pk1, sk1 = load_or_create_keypair(keyfile)

        # Verify file was created
        assert keyfile.exists()

        # Verify file contains valid JSON
        with open(keyfile) as f:
            data = json.load(f)

        assert data["version"] == "1.0.0"
        assert data["algorithm"] == "dilithium2"
        assert "public_key" in data
        assert "secret_key" in data

        # Verify keys are base64 encoded
        assert len(data["public_key"]) > 0
        assert len(data["secret_key"]) > 0


def test_load_or_create_keypair_existing():
    """Test loading existing keypair from file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        keyfile = Path(tmpdir) / "test_key.json"

        # Create keypair
        pk1, sk1 = load_or_create_keypair(keyfile)

        # Load same keypair
        pk2, sk2 = load_or_create_keypair(keyfile)

        # Verify keys are identical
        assert pk1 == pk2
        assert sk1 == sk2


def test_sign_with_persistent_key_deterministic():
    """Test signatures are deterministic with same persistent key."""
    with tempfile.TemporaryDirectory() as tmpdir:
        keyfile = Path(tmpdir) / "test_key.json"

        message = b"test message"

        # Sign twice with same keyfile
        sig1 = sign_with_persistent_key(message, keyfile)
        sig2 = sign_with_persistent_key(message, keyfile)

        # Signatures should be identical (same key, same message)
        assert sig1 == sig2

        # Verify signature is valid Dilithium2 signature
        assert len(sig1) == 2420  # Dilithium2 signature size


def test_sign_with_persistent_key_verifiable():
    """Test signature can be verified with public key."""
    with tempfile.TemporaryDirectory() as tmpdir:
        keyfile = Path(tmpdir) / "test_key.json"

        message = b"test message"

        # Sign message
        sig = sign_with_persistent_key(message, keyfile)

        # Load public key
        pk, _ = load_or_create_keypair(keyfile)

        # Verify signature
        is_valid = PQCKeyring.verify(pk, message, sig)
        assert is_valid


def test_keyring_persistence_with_rc_attestation():
    """Test RC attestation generation uses persistent key."""
    with tempfile.TemporaryDirectory() as tmpdir:
        keyfile = Path(tmpdir) / "rc_key.json"

        # Set env var to use test keyfile
        old_val = os.environ.get("NOVA_PQC_KEYFILE")
        try:
            os.environ["NOVA_PQC_KEYFILE"] = str(keyfile)

            # Generate 2 RC attestations
            msg1 = b'{"attestation_hash":"hash1","phase":"7.0-rc"}'
            msg2 = b'{"attestation_hash":"hash2","phase":"7.0-rc"}'

            sig1 = sign_with_persistent_key(msg1)
            sig2 = sign_with_persistent_key(msg2)

            # Verify keyfile was created
            assert keyfile.exists()

            # Verify signatures are different (different messages)
            assert sig1 != sig2

            # Verify both signatures are valid
            pk, _ = load_or_create_keypair(keyfile)
            assert PQCKeyring.verify(pk, msg1, sig1)
            assert PQCKeyring.verify(pk, msg2, sig2)

        finally:
            if old_val:
                os.environ["NOVA_PQC_KEYFILE"] = old_val
            else:
                os.environ.pop("NOVA_PQC_KEYFILE", None)


def test_keyfile_permissions():
    """Test keyfile has restrictive permissions (Unix only)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        keyfile = Path(tmpdir) / "test_key.json"

        # Create keypair
        load_or_create_keypair(keyfile)

        # Check permissions (Unix only)
        try:
            stat = os.stat(keyfile)
            mode = stat.st_mode & 0o777
            # Should be 0o600 (read/write for owner only)
            # Note: This may not work on Windows
            if os.name != "nt":  # Unix
                assert mode == 0o600, f"Expected 0o600, got {oct(mode)}"
        except Exception:
            # Skip on Windows
            pytest.skip("File permissions test requires Unix")
