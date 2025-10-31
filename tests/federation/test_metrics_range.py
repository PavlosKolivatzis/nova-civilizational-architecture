from datetime import datetime, timezone

import re

from nova.federation.range_proofs import RangeEntry
from nova.federation.schemas import RangeProofRequest, TipSummary


class Provider:
    def __init__(self):
        self.entries = [
            RangeEntry(height=i, merkle_root=f"{i:064x}")
            for i in range(100, 108)
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


def test_range_metrics_increment(client_factory):
    provider = Provider()
    app_client = client_factory(provider=provider)
    payload = RangeProofRequest(from_height=100, max=4).model_dump(mode="json")
    resp = app_client.post("/federation/range_proof", json=payload, headers={"X-Nova-Peer": "node-athens"})
    assert resp.status_code == 200

    metrics_text = app_client.get("/metrics").text
    assert re.search(r"federation_range_chunks_total\{peer=\"node-athens\",result=\"ok\"\} 1\.0", metrics_text)
    assert re.search(r"federation_range_bytes_total\{peer=\"node-athens\"\} \d+", metrics_text)
