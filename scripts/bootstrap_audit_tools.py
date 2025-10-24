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
    required = {"url", "sha256"}
    if not required.issubset(data):
        raise SystemExit(f"Metadata missing required fields: {required}")
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


def ensure_cosign(metadata: Dict[str, str]) -> Path:
    target = TOOLS_DIR / "cosign.exe"
    expected = metadata["sha256"]
    if target.exists():
        actual = sha256sum(target)
        if actual == expected:
            print(f"cosign already present ({target}), checksum verified.")
            return target
        print("existing cosign checksum mismatch; redownloading...")
        target.unlink()

    print(f"Downloading cosign from {metadata['url']}...")
    download_file(metadata["url"], target)
    actual = sha256sum(target)
    if actual != expected:
        target.unlink(missing_ok=True)
        raise SystemExit(f"Checksum mismatch for cosign: {actual} != {expected}")
    print("cosign download complete and verified.")
    return target


def ensure_sha256sum() -> Path:
    git_bin = Path(r"C:\Program Files\Git\usr\bin\sha256sum.exe")
    if git_bin.exists():
        return git_bin
    raise SystemExit("sha256sum.exe not found; install Git for Windows to provide it.")


def main() -> int:
    metadata = read_metadata()
    Tools = {
        "cosign": ensure_cosign(metadata),
        "sha256sum": ensure_sha256sum(),
    }

    mapping = {
        "COSIGN_PATH": str(Tools["cosign"]),
        "SHA256SUM_PATH": str(Tools["sha256sum"]),
    }
    output = TOOLS_DIR / "paths.env"
    with output.open("w", encoding="utf-8") as handle:
        for key, value in mapping.items():
            handle.write(f"{key}={value}\n")
    print(f"Wrote tool path hints to {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
