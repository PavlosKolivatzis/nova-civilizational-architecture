from datetime import datetime, timezone
from itertools import count

import pytest

from nova.crypto.pqc_keyring import PQCKeyring
from nova.federation.discovery import ManifestCache, ManifestVerifier
from nova.federation.peer_registry import PeerRecord
from nova.federation.schemas import PeerManifest, PeerManifestKey
from nova.federation.sync import RangeSyncer
from nova.ledger.receipts_store import ReceiptsStore
from nova.federation.federation_client import FederationClient
from nova.metrics import federation as federation_metrics


def build_manifest(kid: str) -> PeerManifest:
    key = PeerManifestKey(
        kty="pq_dilithium2",
        kid=kid,
        pub="cHVi",  # "pub" base64
        **{"from": datetime.now(timezone.utc)},
    )
    return PeerManifest(
        id="node-athens",
        endpoint="https://athens.example.net",
        keys=[key],
        sig="c2ln",  # "sig" base64
        issued_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def syncer(monkeypatch):
    monkeypatch.setattr(PQCKeyring, "verify", staticmethod(lambda pub, payload, sig: True))
    client = FederationClient()
    receipts = ReceiptsStore()
    cache = ManifestCache(ttl_seconds=0)
    verifier = ManifestVerifier()
    syncer = RangeSyncer(
        client,
        receipts,
        range_limit=10,
        divergence_limit=2,
        manifest_cache=cache,
        manifest_verifier=verifier,
    )
    return syncer, client, receipts


def test_manifest_rotation_receipts(syncer):
    syncer_obj, client, receipts = syncer
    manifests = [build_manifest("2025-10"), build_manifest("2026-01")]
    sequence = count()

    def fake_fetch_manifest(peer):
        idx = next(sequence)
        return manifests[min(idx, len(manifests) - 1)]

    client.fetch_manifest = fake_fetch_manifest  # type: ignore[assignment]
    peer = PeerRecord(id="node-athens", url="https://athens.example.net", pubkey="pub", enabled=True)
    syncer_obj._ensure_manifest(peer)
    syncer_obj._ensure_manifest(peer)
    entries = list(receipts.entries())
    assert len(entries) == 2
    assert all(entry["peer"] == "node-athens" for entry in entries)
    metrics = federation_metrics.client_retries_counter()
    assert metrics._metrics == {}
