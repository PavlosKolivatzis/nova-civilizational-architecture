from datetime import datetime, timezone

import pytest

from nova.crypto.pqc_keyring import PQCKeyring
from nova.federation.discovery import ManifestCache, ManifestVerifier
from nova.federation.federation_client import FederationClient
from nova.federation.peer_registry import PeerRecord
from nova.federation.range_proofs import RangeEntry
from nova.federation.schemas import RangeProofResponse, TipSummary
from nova.federation.sync import RangeSyncError, RangeSyncer, RangeQuarantineError
from nova.ledger.receipts_store import ReceiptsStore


class StaticProvider:
    def __init__(self, entries):
        self._entries = entries
        self._tip = TipSummary(
            height=entries[-1].height,
            merkle_root=entries[-1].merkle_root,
            ts=datetime.now(timezone.utc),
            producer="node-athens",
        )

    def tip(self):
        return self._tip

    def range_slice(self, start: int, limit: int):
        return [entry for entry in self._entries if entry.height >= start][:limit]


@pytest.fixture
def manifest_tools(monkeypatch):
    monkeypatch.setattr(PQCKeyring, "verify", staticmethod(lambda pub, message, sig: True))
    cache = ManifestCache(ttl_seconds=0)
    verifier = ManifestVerifier()
    return cache, verifier


def test_range_sync_success(client_factory, manifest_tools):
    entries = [RangeEntry(height=i, merkle_root=f"{i:064x}") for i in range(20, 31)]
    provider = StaticProvider(entries)
    app_client = client_factory(provider=provider)
    cache, verifier = manifest_tools
    receipts = ReceiptsStore()
    client = FederationClient()

    def fake_fetch_range(peer, request):
        resp = app_client.post(
            "/federation/range_proof",
            json=request.model_dump(mode="json"),
            headers={"X-Nova-Peer": peer.id},
        )
        return RangeProofResponse(**resp.json())

    client.fetch_range = fake_fetch_range  # type: ignore[assignment]
    client.fetch_manifest = lambda peer: None  # type: ignore[assignment]

    syncer = RangeSyncer(
        client,
        receipts,
        range_limit=64,
        divergence_limit=2,
        manifest_cache=cache,
        manifest_verifier=verifier,
    )
    peer = PeerRecord(id="node-athens", url="http://testserver", pubkey="mock", enabled=True)
    response = syncer.sync(peer, start_height=20)
    assert response.tip.height == entries[-1].height
    entries_logged = list(receipts.entries())
    assert entries_logged and entries_logged[-1]["status"] == "ok"


def test_range_sync_divergence(client_factory, manifest_tools):
    base_entries = [RangeEntry(height=i, merkle_root=f"{i:064x}") for i in range(30, 36)]

    class DivergingProvider(StaticProvider):
        def range_slice(self, start: int, limit: int):
            items = super().range_slice(start, limit)
            if items:
                items[-1] = RangeEntry(height=items[-1].height, merkle_root="f" * 64)
            return items

    provider = DivergingProvider(base_entries)
    app_client = client_factory(provider=provider)
    cache, verifier = manifest_tools
    receipts = ReceiptsStore()
    client = FederationClient()

    def fake_fetch_range(peer, request):
        resp = app_client.post(
            "/federation/range_proof",
            json=request.model_dump(mode="json"),
            headers={"X-Nova-Peer": peer.id},
        )
        return RangeProofResponse(**resp.json())

    client.fetch_range = fake_fetch_range  # type: ignore[assignment]
    client.fetch_manifest = lambda peer: None  # type: ignore[assignment]

    syncer = RangeSyncer(
        client,
        receipts,
        range_limit=32,
        divergence_limit=1,
        manifest_cache=cache,
        manifest_verifier=verifier,
    )
    peer = PeerRecord(id="node-athens", url="http://testserver", pubkey="mock", enabled=True)
    with pytest.raises(RangeSyncError):
        syncer.sync(peer, start_height=30)
    with pytest.raises(RangeQuarantineError):
        syncer.sync(peer, start_height=30)
    logged = list(receipts.entries())
    assert logged and logged[0]["status"] == "divergence"
