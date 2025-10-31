# Federation Runbook (Phase 15 Scaffold)

> Status: Draft - federation disabled by default (`FEDERATION_ENABLED=false`)

## Enable (staging or prod canary)
1. Populate `config/federation_peers.yaml` with peer entries (`id`, `url`, `pubkey`).
2. Export env vars or update deployment config:
   ```
   FEDERATION_ENABLED=true
   NOVA_FEDERATION_REGISTRY=config/federation_peers.yaml
   FEDERATION_BIND=0.0.0.0:9414
   NOVA_FEDERATION_SKEW_S=120
   NOVA_FEDERATION_BODY_MAX=65536
   NOVA_FEDERATION_REPLAY_MODE=block   # block|mark|allow
   NOVA_FEDERATION_REPLAY_CACHE_SIZE=4096
   NOVA_FEDERATION_RATE_RPS=0.5
   NOVA_FEDERATION_RATE_BURST=30
   NOVA_FEDERATION_HTTP_TIMEOUT_S=2.5
   NOVA_FEDERATION_RETRIES=2
   NOVA_FEDERATION_TRUST_W_VERIFIED=0.55
   NOVA_FEDERATION_TRUST_W_LATENCY=0.15
   NOVA_FEDERATION_TRUST_W_AGE=0.15
   NOVA_FEDERATION_TRUST_W_CONTINUITY=0.15
   NOVA_FEDERATION_RANGE_MAX=256
   NOVA_FEDERATION_CHUNK_BYTES_MAX=65536
   NOVA_FEDERATION_MAX_DIVERGENCE=2
   NOVA_FEDERATION_MANIFEST_TTL_S=3600
   ```
3. Restart orchestrator; confirm `/federation/health` returns `status=ok`.
4. Monitor Grafana panels (Federation Health dashboard):
   - `sum by(peer) (increase(federation_verifications_total{result="ok"}[5m]))`
   - `sum by(peer) (increase(federation_verifications_total{result="fail"}[5m]))`
   - `federation_peers_up`
   - `federation_last_sync_seconds`
   - `federation_score_gauge`
   - `federation_client_retries_total`
   - `federation_range_bytes_total`
   - `sum by(peer) (increase(federation_range_chunks_total{result="ok"}[5m]))`
   - `federation_divergences_total`
   - `federation_manifest_rotations_total`
   - Optional: `federation_rate_limited_total`, `federation_replay_total`

## Disable / Rollback
1. Set `FEDERATION_ENABLED=false`.
2. Restart orchestrator to remove routes and client tasks.
3. Verify `/federation/health` returns `status=disabled` and metrics flatten to zero.

## Common requests
```bash
# Peers
curl -s http://localhost:8000/federation/peers | jq

# Good checkpoint
curl -s -X POST http://localhost:8000/federation/checkpoint   -H 'Content-Type: application/json'   -d @sample_envelope.json | jq

# Wrong Content-Type
curl -i -X POST http://localhost:8000/federation/checkpoint   -H 'Content-Type: text/plain' -d 'x'

# Oversize payload (expect 413)
curl -i -X POST http://localhost:8000/federation/checkpoint   -H 'Content-Type: application/json'   -H 'Content-Length: 70000' -d @big.json

# Latest checkpoint tip
curl -s http://localhost:8000/federation/checkpoints/latest | jq

# Range proof (from height 120, max 64 entries)
curl -s -X POST http://localhost:8000/federation/range_proof \
  -H 'Content-Type: application/json' \
  -H 'X-Nova-Peer: node-athens' \
  -d '{"from_height":120,"max":64}' | jq
```

## Error codes
Responses conform to `{code, reason}`. Frequent values:
- `unknown_peer` (401)
- `unsupported_media_type` (415)
- `too_large` (413)
- `stale` / `future` (422 clock skew)
- `replay` (409)
- `rate_limited` (429)
- `invalid_payload` / `invalid_json`
- `range_too_large` (422)
- `range_payload_too_large` (413)
- `no_tip` (503)

## Notes
- Phase 15-1 scaffolds interfaces only; checkpoints are not merged into the local ledger yet.
- Keep peer public keys in Dilithium2 PEM format; future phases will automate rotation.
- Ensure NTP is enabled on federation nodes to avoid clock-skew rejections.
- Range proofs remain bounded by `NOVA_FEDERATION_RANGE_MAX` and `NOVA_FEDERATION_CHUNK_BYTES_MAX`; exceeding either returns the error codes above.
- RangeSyncer records continuity/divergence receipts in the append-only receipt log; review via Grafana (`federation_divergences_total`) or inspect the receipt store path configured for the orchestrator.
- Signed peer manifests are cached locally for `NOVA_FEDERATION_MANIFEST_TTL_S`; new key IDs emit `federation_manifest_rotations_total` and append rotation receipts.
