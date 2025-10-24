#!/usr/bin/env python3
"""Download and verify audit tooling artifacts on demand.

This helper avoids storing heavyweight binaries in the repository by
fetching the required executables (e.g., cosign) at run time.  Invoking
the script is idempotent: files are downloaded only when missing or when
the recorded checksum does not match.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import sys
import urllib.request
from pathlib import Path
from typing import Dict

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools" / "audit"
METADATA_FILE = TOOLS_DIR / "cosign.json"


def read_metadata() -> Dict[str, str]:
    if not METADATA_FILE.exists():
        raise SystemExit(f"Metadata file not found: {METADATA_FILE}")
    with METADATA_FILE.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if "artifacts" not in data:
        raise SystemExit("Metadata missing 'artifacts' mapping.")
    return data


def download_file(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as response, dest.open("wb") as target:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            target.write(chunk)


def sha256sum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def determine_platform_key(metadata: Dict[str, object]) -> str:
    override = os.environ.get("COSIGN_PLATFORM")
    if override:
        key = override.lower()
    else:
        system = platform.system().lower()
        machine = platform.machine().lower()
        if system == "windows" and machine in {"amd64", "x86_64"}:
            key = "windows-amd64"
        elif system == "linux" and machine in {"amd64", "x86_64"}:
            key = "linux-amd64"
        else:
            raise SystemExit(f"Unsupported platform: {system}/{machine}")
    artifacts = metadata.get("artifacts", {})
    if key not in artifacts:
        raise SystemExit(f"No cosign artifact metadata for platform '{key}'.")
    return key


def ensure_cosign(metadata: Dict[str, object]) -> Path:
    platform_key = determine_platform_key(metadata)
    artifact = metadata["artifacts"][platform_key]
    required = {"url", "sha256", "filename"}
    if not required.issubset(artifact):
        missing = required - artifact.keys()
        raise SystemExit(f"Artifact metadata missing fields: {missing}")

    target = TOOLS_DIR / artifact["filename"]
    expected = artifact["sha256"]
    if target.exists():
        actual = sha256sum(target)
        if actual == expected:
            print(f"cosign already present ({target}), checksum verified.")
            return target
        print("existing cosign checksum mismatch; redownloading...")
        target.unlink()

    print(f"Downloading cosign from {artifact['url']}...")
    download_file(artifact["url"], target)
    actual = sha256sum(target)
    if actual != expected:
        target.unlink(missing_ok=True)
        raise SystemExit(f"Checksum mismatch for cosign: {actual} != {expected}")
    if os.name != "nt":
        target.chmod(0o755)
    print("cosign download complete and verified.")
    return target


def ensure_sha256sum() -> Path:
    path = shutil.which("sha256sum")
    if path:
        return Path(path)
    git_bin = Path(r"C:\Program Files\Git\usr\bin\sha256sum.exe")
    if git_bin.exists():
        return git_bin
    raise SystemExit("sha256sum.exe not found; install Git for Windows to provide it.")


def main() -> int:
    metadata = read_metadata()
    tools = {
        "cosign": ensure_cosign(metadata),
        "sha256sum": ensure_sha256sum(),
    }

    mapping = {
        "COSIGN_PATH": str(tools["cosign"]),
        "SHA256SUM_PATH": str(tools["sha256sum"]),
    }
    output = TOOLS_DIR / "paths.env"
    with output.open("w", encoding="utf-8") as handle:
        for key, value in mapping.items():
            handle.write(f"{key}={value}\n")
    print(f"Wrote tool path hints to {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
