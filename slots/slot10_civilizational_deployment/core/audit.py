"""Signed audit logging for canary deployments with hash-chaining."""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import json, time, os, hmac, hashlib
from typing import Any, Dict, Optional, Union

# Shared hash integration (Phase 2)
try:
    from slots.common.hashutils import compute_audit_hash  # blake2b
    SHARED_HASH_AVAILABLE = True
except Exception:  # ImportError or init error → fallback cleanly
    SHARED_HASH_AVAILABLE = False
    compute_audit_hash = None

def _env_truthy(name: str) -> bool:
    """Check if environment variable is truthy."""
    v = os.getenv(name, "").strip().lower()
    return v in {"1", "true", "yes", "on"}

def _canon(obj: Dict[str, Any]) -> bytes:
    """Minimal canonical JSON for signing / hashing."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()

class AuditSigner:
    """Default HMAC signer for audit payloads."""
    def __init__(self, secret: Optional[bytes] = None):
        self._secret = secret or b"default-nova-secret"

    def sign(self, payload: bytes) -> str:
        mac = hmac.new(self._secret, payload, hashlib.sha256).hexdigest()
        return "hmac256:" + mac

@dataclass
class AuditRecord:
    action: str
    stage_idx: int
    reason: str
    metrics: Dict[str, Any]
    gate: Dict[str, Any]
    prev: str                    # previous chain hash (legacy alias)
    hash: str                    # computed hash (blake2b or sha256)
    sig: str                     # hmac signature
    hash_method: str             # "shared_blake2b" or "fallback_sha256"
    api_version: str             # e.g., "3.1.0-slot10"
    pct_from: Optional[float] = None
    pct_to: Optional[float] = None
    extra: Dict[str, Any] = field(default_factory=dict)

class AuditLog:
    """Simple append-style audit log that maintains chain state."""
    def __init__(self, root: Union[str, Path], signer: Optional[AuditSigner] = None):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.signer = signer or AuditSigner()
        self._last_hash: str = ""   # chain head

    def record(
        self,
        action: str,
        stage_idx: int,
        reason: str,
        metrics: Optional[Dict[str, Any]] = None,
        gate: Optional[Dict[str, Any]] = None,
        pct_from: Optional[float] = None,
        pct_to: Optional[float] = None,
        **extra: Any,
    ) -> AuditRecord:
        prev = self._last_hash
        body: Dict[str, Any] = {
            "ts": int(time.time()),
            "event": {"action": action, "stage_idx": stage_idx, "reason": reason},
            "metrics": metrics or {},
            "gate": gate or {},
            "prev": prev,                  # keep legacy key for consumers
            "previous_hash": prev,         # canonical key for chain linking
            "api_version": "3.1.0-slot10",
        }
        # Include canary rollout details when provided
        canary = {}
        if pct_from is not None:
            canary["pct_from"] = pct_from
        if pct_to is not None:
            canary["pct_to"] = pct_to
        if canary:
            body["canary"] = canary
        # Preserve any future kwargs without breaking callers
        if extra:
            body["extra"] = extra
        use_shared = _env_truthy("NOVA_USE_SHARED_HASH")
        if SHARED_HASH_AVAILABLE and use_shared and compute_audit_hash:
            body["hash_method"] = "shared_blake2b"
            digest = compute_audit_hash(body)
        else:
            body["hash_method"] = "fallback_sha256"
            digest = hashlib.sha256(_canon(body)).hexdigest()

        sig = self.signer.sign(_canon(body))
        body["hash"] = digest
        body["sig"] = sig

        # persist head and (optionally) append to disk if you already do
        self._last_hash = digest

        return AuditRecord(
            action=action,
            stage_idx=stage_idx,
            reason=reason,
            metrics=metrics or {},
            gate=gate or {},
            prev=prev,
            hash=digest,
            sig=sig,
            hash_method=body["hash_method"],
            api_version=body["api_version"],
            pct_from=pct_from,
            pct_to=pct_to,
            extra=extra or {},
        )