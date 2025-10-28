"""
Prometheus metrics for Autonomous Verification Ledger (AVL).

Phase 13/14: Ledger operations observability + PostgreSQL persistence metrics.
"""

from prometheus_client import Counter, Gauge, Histogram, Summary

# Append operations
ledger_appends_total = Counter(
    "ledger_appends_total",
    "Total number of ledger append operations",
    ["slot", "kind", "status"],  # status: success, error, continuity_error
)

ledger_append_duration_seconds = Histogram(
    "ledger_append_duration_seconds",
    "Duration of ledger append operations",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

# Query operations
ledger_query_total = Counter(
    "ledger_query_total",
    "Total number of ledger query operations",
    ["query_type", "status"],  # query_type: chain, search, checkpoint
)

ledger_query_duration_seconds = Histogram(
    "ledger_query_duration_seconds",
    "Duration of ledger query operations",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

# Verification operations
ledger_verify_requests_total = Counter(
    "ledger_verify_requests_total",
    "Total number of ledger verification requests",
    ["result"],  # result: pass, fail, continuity_break
)

ledger_verify_duration_seconds = Histogram(
    "ledger_verify_duration_seconds",
    "Duration of ledger verification operations",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

# Trust scores
ledger_trust_score = Gauge(
    "ledger_trust_score",
    "Trust score for anchors based on ledger evidence",
    ["anchor_id"],
)

ledger_chain_length = Gauge(
    "ledger_chain_length",
    "Length of record chain for anchors",
    ["anchor_id"],
)

# Checkpoints
ledger_checkpoints_total = Counter(
    "ledger_checkpoints_total",
    "Total number of ledger checkpoints created",
)

ledger_checkpoint_record_count = Gauge(
    "ledger_checkpoint_record_count",
    "Number of records in the latest checkpoint",
)

# Health metrics
ledger_continuity_breaks_total = Counter(
    "ledger_continuity_breaks_total",
    "Total number of hash chain continuity breaks detected",
    ["anchor_id"],
)

ledger_records_total = Gauge(
    "ledger_records_total",
    "Total number of records in the ledger",
)

# Phase 14-1: PostgreSQL persistence metrics
ledger_persist_latency_ms = Summary(
    "ledger_persist_latency_ms",
    "Ledger write latency (ms)",
    ["operation"]
)

ledger_persist_errors_total = Counter(
    "ledger_persist_errors_total",
    "Ledger persistence errors",
    ["operation"]
)

ledger_backend_up = Gauge(
    "ledger_backend_up",
    "1 if PostgreSQL backend is reachable"
)

ledger_persist_fallback_total = Counter(
    "ledger_persist_fallback_total",
    "Ledger fallback to memory store",
    ["reason"]
)

# Phase 14-2: Checkpoint metrics
ledger_checkpoints_total = Counter(
    "ledger_checkpoints_total",
    "Total number of checkpoints created"
)

ledger_checkpoint_verify_failures_total = Counter(
    "ledger_checkpoint_verify_failures_total",
    "Total number of checkpoint verification failures"
)

ledger_checkpoint_latency_ms = Summary(
    "ledger_checkpoint_latency_ms",
    "Checkpoint build and sign latency (ms)"
)
