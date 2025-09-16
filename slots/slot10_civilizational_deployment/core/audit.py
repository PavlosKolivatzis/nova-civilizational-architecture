"""Signed audit logging for canary deployments with hash-chaining."""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json, time, os, hmac, hashlib
from typing import Any, Dict, Optional

def _canon(obj: Dict[str, Any]) -> bytes:
    """Minimal canonical JSON for signing / hashing."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()

class AuditSigner:
    """
    HMAC-SHA256 signer (no external deps).
    Key can be provided via SLOT10_AUDIT_KEY env or constructor.
    """
    def __init__(self, key: Optional[bytes] = None) -> None:
        key_env = os.getenv("SLOT10_AUDIT_KEY", "slot10-dev").encode()
        self.key = key or key_env

    def sign(self, payload: bytes) -> str:
        return hmac.new(self.key, payload, hashlib.sha256).hexdigest()

    def verify(self, payload: bytes, sig_hex: str) -> bool:
        expect = self.sign(payload)
        return hmac.compare_digest(expect, sig_hex)

@dataclass
class AuditRecord:
    ts_ms: int
    action: str            # "start" | "promote" | "rollback" | ...
    stage_idx: int
    reason: str = ""
    pct_from: float = 0.0
    pct_to: float = 0.0
    metrics: Dict[str, Any] = None
    gate: Dict[str, Any] = None
    prev: str = ""         # prev chain hash
    hash: str = ""         # sha256(payload)
    sig: str = ""          # hmac signature

    def __post_init__(self):
        if self.metrics is None:
            self.metrics = {}
        if self.gate is None:
            self.gate = {}

class AuditLog:
    """
    Hash-chained JSONL. Each line is an AuditRecord dict with:
      - prev: previous record's hash (empty for first)
      - hash: sha256(canonical_payload_without_sig)
      - sig : signer.sign(canonical_payload_without_sig)
    """
    def __init__(self, log_dir: Path, signer: Optional[AuditSigner] = None) -> None:
        self.dir = Path(log_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.path = self.dir / "canary_audit.log"
        self.signer = signer or AuditSigner()

    def _last_hash(self) -> str:
        """Get the hash of the last record for chaining."""
        if not self.path.exists():
            return ""
        last = ""
        try:
            with self.path.open("r", encoding="utf-8") as f:
                for line in f:
                    try:
                        obj = json.loads(line)
                        last = obj.get("hash", "") or last
                    except Exception:
                        continue
        except Exception:
            pass
        return last

    def record(self, *, action: str, stage_idx: int, reason: str = "",
               pct_from: float = 0.0, pct_to: float = 0.0,
               metrics: Optional[Dict[str, Any]] = None,
               gate: Optional[Dict[str, Any]] = None) -> AuditRecord:
        """Record a new audit entry with hash chaining and signature."""
        prev = self._last_hash()
        body = {
            "ts_ms": int(time.time() * 1000),
            "action": action,
            "stage_idx": stage_idx,
            "reason": reason,
            "pct_from": float(pct_from),
            "pct_to": float(pct_to),
            "metrics": metrics or {},
            "gate": gate or {},
            "prev": prev,
        }
        payload = _canon(body)
        digest = hashlib.sha256(payload).hexdigest()
        sig = self.signer.sign(payload)
        body["hash"] = digest
        body["sig"] = sig

        # Write atomically
        try:
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(body, sort_keys=True) + "\n")
                f.flush()
        except Exception as e:
            # Log error but don't fail deployment
            print(f"Warning: Failed to write audit log: {e}")

        return AuditRecord(**body)

    def verify_file(self) -> bool:
        """Verify all signatures and chain links."""
        prev = ""
        if not self.path.exists():
            return True

        try:
            with self.path.open("r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        print(f"Invalid JSON at line {line_num}")
                        return False

                    # Chain link verification
                    if obj.get("prev", "") != prev:
                        print(f"Chain break at line {line_num}: expected prev={prev}, got {obj.get('prev', '')}")
                        return False

                    sig = obj.get("sig", "")
                    # Rebuild payload without sig/hash to recompute
                    body = {k: v for k, v in obj.items() if k not in ("hash", "sig")}
                    payload = _canon(body)
                    digest = hashlib.sha256(payload).hexdigest()

                    # Verify hash
                    if digest != obj.get("hash"):
                        print(f"Hash mismatch at line {line_num}")
                        return False

                    # Verify signature
                    if not self.signer.verify(payload, sig):
                        print(f"Signature verification failed at line {line_num}")
                        return False

                    prev = obj.get("hash", "")
        except Exception as e:
            print(f"Verification error: {e}")
            return False

        return True

    def count_records(self) -> int:
        """Count total records in the audit log."""
        if not self.path.exists():
            return 0
        count = 0
        try:
            with self.path.open("r", encoding="utf-8") as f:
                for _ in f:
                    count += 1
        except Exception:
            pass
        return count