"""
Persistent PQC keyring with filesystem storage.

Stores Dilithium2 keypairs in ~/.nova/keyring/ with versioning support.

Phase 14-4: Persistent Key Management
"""

import json
import os
from pathlib import Path
from typing import Optional, Tuple

from .pqc_keyring import PQCKeyring


def get_keyring_dir() -> Path:
    """
    Get keyring directory from environment or default.

    Environment variables:
    - NOVA_KEYRING_DIR: Custom keyring directory path
    - Default: ~/.nova/keyring/ (Unix) or %USERPROFILE%\\.nova\\keyring\\ (Windows)

    Returns:
        Path to keyring directory
    """
    custom_dir = os.getenv("NOVA_KEYRING_DIR")
    if custom_dir:
        return Path(custom_dir)

    # Default: ~/.nova/keyring/
    home = Path.home()
    return home / ".nova" / "keyring"


def get_default_keyfile() -> Path:
    """
    Get default PQC keyfile path.

    Environment variables:
    - NOVA_PQC_KEYFILE: Custom keyfile path
    - Default: <keyring_dir>/pqc_key_01.json

    Returns:
        Path to keyfile
    """
    custom_keyfile = os.getenv("NOVA_PQC_KEYFILE")
    if custom_keyfile:
        return Path(custom_keyfile)

    return get_keyring_dir() / "pqc_key_01.json"


def load_or_create_keypair(keyfile: Optional[Path] = None) -> Tuple[bytes, bytes]:
    """
    Load existing keypair from file or create new one.

    Args:
        keyfile: Path to keyfile (default: from get_default_keyfile())

    Returns:
        (public_key, secret_key) tuple

    Side effects:
        - Creates keyring directory if it doesn't exist
        - Creates keyfile if it doesn't exist
        - Writes keypair to disk in JSON format
    """
    if keyfile is None:
        keyfile = get_default_keyfile()

    # Load existing keypair
    if keyfile.exists():
        with open(keyfile, "r") as f:
            data = json.load(f)

        # Decode base64 keys
        pk = PQCKeyring.decode_key(data["public_key"])
        sk = PQCKeyring.decode_key(data["secret_key"])

        return pk, sk

    # Generate new keypair
    pk, sk = PQCKeyring.generate_keypair()

    # Create keyring directory
    keyfile.parent.mkdir(parents=True, exist_ok=True)

    # Save keypair
    data = {
        "version": "1.0.0",
        "algorithm": "dilithium2",
        "public_key": PQCKeyring.encode_key(pk),
        "secret_key": PQCKeyring.encode_key(sk),
        "created_at": None,  # Will be set on first save
    }

    with open(keyfile, "w") as f:
        json.dump(data, f, indent=2)

    # Set restrictive permissions (Unix only)
    try:
        os.chmod(keyfile, 0o600)
    except Exception:
        pass  # Windows doesn't support chmod

    return pk, sk


def get_public_key(keyfile: Optional[Path] = None) -> bytes:
    """
    Get public key from keyfile.

    Args:
        keyfile: Path to keyfile (default: from get_default_keyfile())

    Returns:
        Public key bytes
    """
    pk, _ = load_or_create_keypair(keyfile)
    return pk


def sign_with_persistent_key(message: bytes, keyfile: Optional[Path] = None) -> bytes:
    """
    Sign message with persistent secret key.

    Args:
        message: Message bytes to sign
        keyfile: Path to keyfile (default: from get_default_keyfile())

    Returns:
        Signature bytes
    """
    _, sk = load_or_create_keypair(keyfile)
    return PQCKeyring.sign(sk, message)
