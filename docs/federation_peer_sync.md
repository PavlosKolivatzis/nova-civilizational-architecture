# Federation Peer Synchronization (Phase 16-2)

## Overview

Federation peer synchronization enables multi-node deployments to share metrics for distributed generativity calculation. The system uses pull-based HTTP synchronization to collect peer state without requiring shared infrastructure.

**Status:** Implemented, flag-gated, observability-only (does not drive governance or routing)

**Single-node safety:** Enabling federation flags in a single-node deployment is safe but yields no generativity benefit beyond observability. The structural constraint (N=0 without peer diversity) cannot be overcome through configuration—it requires multi-node deployment.

## Federation Flow Diagram

```mermaid
flowchart TD
    %% Entry Point
    START[Orchestrator Startup<br/>lifespan hook]
    GATE{NOVA_FED_SYNC_ENABLED=1<br/>AND<br/>NOVA_FED_PEERS configured?}

    %% Core Components
    PEER_SYNC[PeerSync Background Task<br/>Pull-based HTTP polling]
    PEER_STORE[PeerStore<br/>Thread-safe rolling windows<br/>5-minute retention]

    %% Peer Communication
    PEERS[Configured Peers<br/>NOVA_FED_PEERS]
    ENDPOINT[Peer Endpoint<br/>/federation/sync/summary]

    %% Quality Calculation
    QUALITY[Quality Scoring<br/>success_rate + latency_p95 + freshness]

    %% Outputs
    PROM[Prometheus Metrics<br/>federation_sync_latency<br/>federation_peer_last_seen<br/>peer_quality]
    WISDOM[Wisdom Governor<br/>Novelty (N) calculation]

    %% Single-Node Limitation
    SINGLE[Single-Node Deployment<br/>N = 0 (no peer diversity)<br/>G* capped at 0.30]

    %% Flow
    START --> GATE
    GATE -->|Yes| PEER_SYNC
    GATE -->|No| SINGLE

    PEER_SYNC -->|HTTP GET every 30s| PEERS
    PEERS --> ENDPOINT
    ENDPOINT -->|PeerSyncPayload<br/>validate schema| PEER_SYNC

    PEER_SYNC -->|Update rolling windows| PEER_STORE
    PEER_STORE --> QUALITY

    QUALITY --> PROM
    PEER_STORE -.->|get_peer_gstars| WISDOM

    %% Observability-only path (dashed)
    WISDOM -.->|Observability only<br/>No governance integration| PROM

    %% Styling
    classDef gate fill:#fff4e6,stroke:#ff9800,stroke-width:3px
    classDef core fill:#e1f5ff,stroke:#0066cc,stroke-width:2px
    classDef external fill:#f3e5f5,stroke:#9c27b0,stroke-width:2px
    classDef output fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
    classDef limitation fill:#ffebee,stroke:#c62828,stroke-width:2px

    class GATE gate
    class PEER_SYNC,PEER_STORE,QUALITY core
    class PEERS,ENDPOINT external
    class PROM,WISDOM output
    class SINGLE limitation
```

What Federation Does (Implemented)

Pull-Based Synchronization

- PeerSync background task polls configured peers via HTTP GET
- Interval: NOVA_FED_SYNC_INTERVAL (default: 30s)
- Timeout: NOVA_FED_SYNC_TIMEOUT (default: 2.5s)
- Validates PeerSyncPayload schema (Pydantic)

Peer Metrics Collection

- Pulls from /federation/sync/summary endpoint
- Schema fields:
  - peer_quality, stability_margin, hopf_distance, spectral_radius
  - gamma (wisdom), g_star (generativity), g_components (P, N, Cc)
- Stores samples in PeerStore (thread-safe, deque-based rolling windows)
- Window size: 5 minutes (300s)

Quality Scoring

- Success rate: Ratio of successful pulls
- Latency p95: 95th percentile pull duration
- Freshness: Exponential decay based on last_seen timestamp
- Formula: quality = w1*success_rate + w2*latency_score + w3*freshness
- Weights: NOVA_FED_QUALITY_W1/W2/W3 (default: 0.5, 0.3, 0.2)

Observability

- Prometheus metrics:
  - federation_sync_latency_histogram - Pull duration
  - federation_peer_last_seen_gauge - Last successful sync timestamp
  - federation_sync_errors_counter - HTTP/validation/unexpected errors
  - peer_quality - Computed quality score per peer
  - peer_p95 - Latency p95 per peer
  - peer_success - Success rate per peer

What Federation Does NOT Do

- No governance integration: Peer state does not drive routing or regime decisions
- No ledger synchronization: No checkpoint exchange (Phase 16+ design)
- No peer-to-peer writes: Pull-only, no state mutations on remote peers
- No automatic failover: Does not redirect requests to healthy peers
- No consensus: No distributed coordination or voting

Single-Node Limitation

Structural constraint: In single-node deployments:
- Novelty (N) = 0 (no peer diversity in quality scores)
- Maximum G* = 0.30 (from Progress + Consistency only)
- Federation infrastructure exists but provides no generativity benefit

Multi-node requirement for G > 0.30:*
- Minimum 3-5 active peers with varying quality scores
- FEDERATION_ENABLED=1 + NOVA_FED_SYNC_ENABLED=1
- NOVA_FED_PEERS configured with reachable peer URLs

Feature Flags

All federation features are flag-gated (default off):

FEDERATION_ENABLED=0               # Enable federation subsystem
NOVA_FED_SYNC_ENABLED=0            # Enable PeerSync background task
NOVA_FED_PEERS=""                  # Comma-separated peer URLs (e.g., "http://10.0.0.11:8100,http://10.0.0.12:8100")
NOVA_FED_SYNC_INTERVAL=30          # Pull interval (seconds)
NOVA_FED_SYNC_TIMEOUT=2.5          # HTTP timeout (seconds)
NOVA_FED_QUALITY_W1=0.5            # Quality weight: success rate
NOVA_FED_QUALITY_W2=0.3            # Quality weight: latency
NOVA_FED_QUALITY_W3=0.2            # Quality weight: freshness

Integration with Wisdom Governor

Novelty (N) calculation:
- Wisdom Governor calls peer_store.get_peer_gstars(max_age_seconds=90)
- Computes standard deviation of peer G* values
- Formula: N = clip(σ(peer_gstars) / 0.5, 0, 1)
- If no peers or single-node: N = 0

Connection: Observability-only, not governance-coupled
- Peer state influences G* score (used in generativity bias)
- G* bias influences η (learning rate) via wisdom controller
- η modulates TRI cap (Slot 4 coherence)
- TRI cap drives Slot 7 backpressure (job parallelism)

This is an indirect, metrics-based influence-not a direct governance signal.

Contracts

- contracts/peer_sync_payload@1.yaml - Schema for /federation/sync/summary
- contracts/peer_sample@1.yaml - Internal PeerSample structure

Test Coverage

- Unit tests: tests/orchestrator/test_federation_synchronizer.py
- Integration tests: tests/integration/test_federation_peer_sync.py
- Mock HTTP clients (httpx) for peer endpoint simulation

References

- Implementation: src/nova/orchestrator/federation_synchronizer.py
- Poller: src/nova/orchestrator/federation_poller.py
- Singleton: src/nova/orchestrator/peer_store_singleton.py
- Wisdom integration: src/nova/governor/adaptive_wisdom.py
- Metrics: src/nova/orchestrator/prometheus_metrics.py

**Annotation check:**
- ✔ Matches Assumption 16 ("Adaptive Wisdom Governor uses **peer sync state** as an input")
- ✔ Matches Assumption 17 ("Prometheus metrics are **opt-in**")
- ✔ Matches Assumption 23 ("Nova does **not** assume all slots are always healthy")
- ⚠ Implies connection to wisdom governor (acknowledged as indirect, metrics-based)

**No new claims. No future arrows. No implied autonomy. Federation is observability-only.**
(optional) tightening suggestion

This is not a blocker. Think of it as future-proofing.

Suggestion (optional)

In the Overview or Single-Node Limitation section, consider adding one explicit sentence like:

“Enabling federation flags in a single-node deployment is safe but yields no generativity benefit beyond observability.”

Why?

It reassures operators that they're not "doing something wrong"

It prevents support churn

It frames the limitation as structural, not misconfiguration

You already imply this. One explicit sentence would make it unmissable.

Again: optional, not required.
