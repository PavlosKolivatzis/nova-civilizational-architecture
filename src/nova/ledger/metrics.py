"""
Prometheus metrics for Autonomous Verification Ledger (AVL).

Phase 13/14: Ledger operations observability + PostgreSQL persistence + checkpoint metrics.
"""

from ..metrics.registry import get_counter, get_gauge, get_summary

# Append operations
ledger_appends_total = get_counter(
    "ledger_appends_total",
    "Total number of ledger append operations",
    labelnames=["slot", "kind", "status"]
)

ledger_append_duration_seconds = get_summary(
    "ledger_append_duration_seconds",
    "Duration of ledger append operations"
)

# Query operations
ledger_query_total = get_counter(
    "ledger_query_total",
    "Total number of ledger query operations",
    labelnames=["query_type", "status"]
)

ledger_query_duration_seconds = get_summary(
    "ledger_query_duration_seconds",
    "Duration of ledger query operations"
)

# Verification operations
ledger_verify_requests_total = get_counter(
    "ledger_verify_requests_total",
    "Total number of ledger verification requests",
    labelnames=["result"]
)

ledger_verify_duration_seconds = get_summary(
    "ledger_verify_duration_seconds",
    "Duration of ledger verification operations"
)

# Trust scores
ledger_trust_score = get_gauge(
    "ledger_trust_score",
    "Trust score for anchors based on ledger evidence",
    labelnames=["anchor_id"]
)

ledger_chain_length = get_gauge(
    "ledger_chain_length",
    "Length of record chain for anchors",
    labelnames=["anchor_id"]
)

# Checkpoints
ledger_checkpoint_record_count = get_gauge(
    "ledger_checkpoint_record_count",
    "Number of records in the latest checkpoint"
)

# Health metrics
ledger_continuity_breaks_total = get_counter(
    "ledger_continuity_breaks_total",
    "Total number of hash chain continuity breaks detected",
    labelnames=["anchor_id"]
)

ledger_records_total = get_gauge(
    "ledger_records_total",
    "Total number of records in the ledger"
)

# Phase 14-1: PostgreSQL persistence metrics
ledger_persist_latency_ms = get_summary(
    "ledger_persist_latency_ms",
    "Ledger write latency (ms)",
    labelnames=["operation"]
)

ledger_persist_errors_total = get_counter(
    "ledger_persist_errors_total",
    "Ledger persistence errors",
    labelnames=["operation"]
)

ledger_backend_up = get_gauge(
    "ledger_backend_up",
    "1 if PostgreSQL backend is reachable"
)

ledger_persist_fallback_total = get_counter(
    "ledger_persist_fallback_total",
    "Ledger fallback to memory store",
    labelnames=["reason"]
)

# Phase 14-2: Checkpoint metrics
ledger_checkpoints_total = get_counter(
    "ledger_checkpoints_total",
    "Total number of checkpoints created"
)

ledger_checkpoint_verify_failures_total = get_counter(
    "ledger_checkpoint_verify_failures_total",
    "Total number of checkpoint verification failures"
)

ledger_checkpoint_latency_ms = get_summary(
    "ledger_checkpoint_latency_ms",
    "Checkpoint build and sign latency (ms)"
)
