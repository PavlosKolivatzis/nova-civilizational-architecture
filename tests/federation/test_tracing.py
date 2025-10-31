from contextlib import contextmanager
from datetime import datetime, timezone

from nova.crypto.pqc_keyring import PQCKeyring
from nova.federation.discovery import ManifestCache, ManifestVerifier
from nova.federation.federation_client import FederationClient
from nova.federation.peer_registry import PeerRecord
from nova.federation.range_proofs import RangeEntry
from nova.federation.schemas import PeerManifest, PeerManifestKey, TipSummary
from nova.federation.sync import RangeSyncer
from nova.ledger.receipts_store import ReceiptsStore


class Provider:
    def __init__(self):
        self.entries = [
            RangeEntry(height=10 + idx, merkle_root=f"{idx:064x}")
            for idx in range(4)
        ]

    def tip(self):
        return TipSummary(
            height=self.entries[-1].height,
            merkle_root=self.entries[-1].merkle_root,
            ts=datetime.now(timezone.utc),
            producer="node-athens",
        )

    def range_slice(self, start: int, limit: int):
        return [entry for entry in self.entries if entry.height >= start][:limit]


@contextmanager
def capture_span(spans, name):
    spans.append(name)
    yield


def test_range_proof_tracing(monkeypatch, client_factory):
    spans = []
    monkeypatch.setattr(
        "nova.federation.federation_server._start_span",
        lambda name: capture_span(spans, name),
    )
    provider = Provider()
    client = client_factory(provider=provider)
    payload = {"from_height": 10, "max": 2}
    client.post("/federation/range_proof", json=payload)
    assert "federation.range_proof" in spans


def test_sync_tracing(monkeypatch):
    spans = []
    monkeypatch.setattr(
        "nova.federation.sync._start_span",
        lambda name: capture_span(spans, name),
    )
    monkeypatch.setattr(PQCKeyring, "verify", staticmethod(lambda pub, message, sig: True))
    client = FederationClient()
    manifest = PeerManifest(
        id="node",
        endpoint="https://example.com",
        keys=[PeerManifestKey(kty="pq_dilithium2", kid="k1", pub="cHVi", **{"from": datetime.now(timezone.utc)})],
        sig="c2ln",
        issued_at=datetime.now(timezone.utc),
    )
    client.fetch_manifest = lambda peer: manifest  # type: ignore[assignment]
    syncer = RangeSyncer(
        client,
        ReceiptsStore(),
        range_limit=2,
        divergence_limit=1,
        manifest_cache=ManifestCache(ttl_seconds=60),
        manifest_verifier=ManifestVerifier(),
    )
    syncer._ensure_manifest(  # type: ignore[attr-defined]
        PeerRecord(id="node", url="https://example.com", pubkey="pub", enabled=True)
    )
    assert spans
