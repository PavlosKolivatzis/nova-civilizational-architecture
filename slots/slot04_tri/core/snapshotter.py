from __future__ import annotations
import json
import time
import hashlib
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

@dataclass
class SnapshotMeta:
    id: str
    ts_ms: int
    merkle_root: str
    signer: str
    sig: str  # hex

def _sha256_of_file(path: Path) -> bytes:
    """Streaming SHA-256 of a file (bytes digest)."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):  # 1 MiB chunks
            h.update(chunk)
    return h.digest()

def _merkle_for_dir(root: Path) -> str:
    """
    Compute a simple Merkle root over files under `root`, binding both
    relative path and content: leaf = H(path || 0x00 || H(content)).
    Returns hex digest.
    """
    root = Path(root)
    leaves: List[str] = []
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix().encode("utf-8", "strict")
        content_digest = _sha256_of_file(p)  # bytes
        leaf = hashlib.sha256(rel + b"\x00" + content_digest).hexdigest()
        leaves.append(leaf)
    if not leaves:
        return hashlib.sha256(b"").hexdigest()
    nodes = leaves
    while len(nodes) > 1:
        nxt: List[str] = []
        for i in range(0, len(nodes), 2):
            a = nodes[i]
            b = nodes[i + 1] if i + 1 < len(nodes) else a
            nxt.append(hashlib.sha256((a + b).encode("ascii")).hexdigest())
        nodes = nxt
    return nodes[0]

class DummySigner:
    def pubkey_fpr(self): return "slot4-dev"
    def sign(self, b: bytes) -> bytes: return b"\x02"*64

class TriSnapshotter:
    def __init__(self, model_dir: Path, snapshot_dir: Path, signer=None):
        self.model_dir = Path(model_dir)
        self.snapshot_dir = Path(snapshot_dir)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        self._last_good_id: str | None = None
        self.signer = signer or DummySigner()

    def take(self) -> SnapshotMeta:
        meta: Dict[str, Any] = {
            "id": f"snap_{int(time.time()*1000)}",
            "ts_ms": int(time.time()*1000),
            "merkle_root": _merkle_for_dir(self.model_dir),
            "signer": self.signer.pubkey_fpr(),
        }
        blob = json.dumps(meta, sort_keys=True).encode()
        sig = self.signer.sign(blob).hex()
        meta["sig"] = sig
        out = self.snapshot_dir / f"{meta['id']}.json"
        out.write_text(json.dumps(meta, sort_keys=True))
        self._last_good_id = meta["id"]
        return SnapshotMeta(**meta)

    def last_good_id(self) -> str | None:
        return self._last_good_id

    def verify_current(self) -> bool:
        # Best effort: compare against last manifest if exists
        if not self._last_good_id:
            return False
        path = self.snapshot_dir / f"{self._last_good_id}.json"
        if not path.exists():
            return False
        meta = json.loads(path.read_text())
        return meta["merkle_root"] == _merkle_for_dir(self.model_dir)

    def restore(self, snap_id: str) -> bool:
        # For TRI, assume stateless weights file "weights.json" as minimal stub
        # In real system, copy model files; here we just return True
        return True

    # -------------------------
    # Ops helpers (non-breaking)
    # -------------------------
    def list_snapshots(self) -> List[str]:
        """Return sorted list of snapshot ids in snapshot_dir."""
        ids: List[str] = []
        for p in sorted(self.snapshot_dir.glob("snap_*.json")):
            ids.append(p.stem)
        return ids

    def get_snapshot(self, snap_id: str) -> Optional[SnapshotMeta]:
        p = self.snapshot_dir / f"{snap_id}.json"
        if not p.exists():
            return None
        meta = json.loads(p.read_text())
        return SnapshotMeta(**meta)

    def prune(self, keep_last: int = 10) -> int:
        """
        Delete older snapshot manifests, keeping the N most recent.
        Returns number of files removed.
        """
        files = sorted(self.snapshot_dir.glob("snap_*.json"))
        if len(files) <= keep_last:
            return 0
        to_delete = files[: -keep_last]
        for p in to_delete:
            try:
                p.unlink()
            except Exception:
                pass
        return len(to_delete)