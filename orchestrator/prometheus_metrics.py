"""Prometheus metrics export for Nova system."""

import logging

from prometheus_client import (
    Gauge,
    Counter,
    Histogram,
    Info,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from collections import defaultdict
import subprocess
from time import strftime, gmtime
from os import getenv

from orchestrator.metrics import get_slot6_metrics
from nova.federation.metrics import get_registry as get_federation_registry
from nova.metrics.registry import REGISTRY

# Dedicated registry (avoids duplicate registration across tests/imports)
_REGISTRY = REGISTRY
logger = logging.getLogger(__name__)

# --- Build provenance metric ------------------------------------
def _get_git_sha_short():
    """Get current git commit SHA (short form) for build traceability."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            capture_output=True,
            text=True,
            timeout=5,
            cwd='.'
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return getenv('NOVA_BUILD_SHA', 'unknown')

# Build info metric (constant labels for deployment traceability)
build_info = Info(
    'nova_build',
    'Nova build information for deployment traceability',
    registry=_REGISTRY,
)

# Initialize build info at module load
build_info.info({
    'sha': _get_git_sha_short(),
    'component': 'orchestrator',
    'version': '5.1',
    'built_at': strftime("%Y-%m-%dT%H:%M:%SZ", gmtime())
})

# Prometheus gauges
slot6_p95_residual_risk_gauge = Gauge(
    "nova_slot6_p95_residual_risk",
    "Slot6 95th percentile residual risk from cultural synthesis decisions",
    ["slot"],
    registry=_REGISTRY,
)

# --- Flag gauges (Phase 2 feature flags) ------------------------------------
def _env_truthy(name: str) -> bool:
    v = (getenv(name, "") or "").strip()
    return v == "1"

# One gauge, labeled by flag name
feature_flag_gauge = Gauge(
    "nova_feature_flag_enabled",
    "Nova Phase-2 feature flag states",
    ["flag"],
    registry=_REGISTRY,
)

# --- LightClock & System Health metrics ------------------------------------
lightclock_phase_lock_gauge = Gauge(
    "nova_lightclock_phase_lock",
    "Current LightClock phase lock value from Slot3",
    registry=_REGISTRY,
)

# Phase 6.0 Probabilistic Contracts metrics
slot_phase_lock_belief_mean_gauge = Gauge(
    "nova_slot_phase_lock_belief_mean",
    "Phase lock belief mean from probabilistic contracts",
    ["slot"],
    registry=_REGISTRY,
)

slot_phase_lock_belief_variance_gauge = Gauge(
    "nova_slot_phase_lock_belief_variance",
    "Phase lock belief variance from probabilistic contracts",
    ["slot"],
    registry=_REGISTRY,
)

system_pressure_gauge = Gauge(
    "nova_system_pressure_level",
    "System pressure level from Slot7",
    registry=_REGISTRY,
)

tri_coherence_gauge = Gauge(
    "nova_tri_coherence",
    "TRI signal coherence from Slot4",
    registry=_REGISTRY,
)

tri_coherence_current_gauge = Gauge(
    "nova_tri_coherence_current",
    "Canonical TRI coherence value emitted via tri_truth_signal@1",
    registry=_REGISTRY,
)

tri_canonization_hash_info = Info(
    "nova_tri_canonization_hash",
    "Latest TRI canonical hash (for debugging/attestation linkage)",
    registry=_REGISTRY,
)

tri_to_anchor_events_counter = Counter(
    "nova_tri_to_anchor_events_total",
    "Total TRI -> Slot01 attestation events triggered via Root-Mode bridge",
    registry=_REGISTRY,
)

slot01_attest_latency_gauge = Gauge(
    "nova_slot01_attest_latency_ms",
    "Average latency (ms) for TRI-triggered Slot01 attestation events",
    registry=_REGISTRY,
)

slot07_tri_coherence_gauge = Gauge(
    "nova_slot07_tri_coherence",
    "Latest TRI coherence snapshot consumed by Slot07 backpressure",
    registry=_REGISTRY,
)

slot07_tri_drift_gauge = Gauge(
    "nova_slot07_tri_drift_z",
    "Latest TRI drift Z-score consumed by Slot07 backpressure",
    registry=_REGISTRY,
)

slot07_tri_jitter_gauge = Gauge(
    "nova_slot07_tri_jitter",
    "Latest TRI jitter snapshot consumed by Slot07 backpressure",
    registry=_REGISTRY,
)

deployment_gate_gauge = Gauge(
    "nova_deployment_gate_open",
    "Whether Slot10 deployment gate is open (1=open, 0=closed)",
    registry=_REGISTRY,
)

semantic_mirror_ops_counter = Gauge(
    "nova_semantic_mirror_operations_total",
    "Total semantic mirror operations",
    ["operation_type"],
    registry=_REGISTRY,
)

# Reciprocal Contextual Unlearning metrics (counters)
unlearn_pulses_sent_counter = Counter(
    "nova_unlearn_pulses_sent_total",
    "Total unlearn pulses sent on context expiration",
    registry=_REGISTRY,
)

entries_expired_counter = Counter(
    "nova_entries_expired_total",
    "Total context entries expired from semantic mirror",
    registry=_REGISTRY,
)

unlearn_pulse_destinations_counter = Counter(
    "nova_unlearn_pulse_to_slot_total",
    "Unlearn pulses sent to specific slots",
    ["slot"],
    registry=_REGISTRY,
)

# Contract fanout metrics (counters)
fanout_delivered_counter = Counter(
    "nova_fanout_delivered_total",
    "Total local contract fanout deliveries",
    registry=_REGISTRY,
)

fanout_errors_counter = Counter(
    "nova_fanout_errors_total",
    "Total local contract fanout errors",
    registry=_REGISTRY,
)

# Slot6 decay metrics
slot6_decay_events_counter = Counter(
    "nova_slot6_decay_events_total",
    "Total number of decay events processed by Slot6",
    registry=_REGISTRY,
)

slot6_decay_amount_counter = Counter(
    "nova_slot6_decay_amount_total",
    "Total decay amount processed by Slot6 (sum of old_weight - new_weight)",
    registry=_REGISTRY,
)

# Canary metrics
canary_enabled_gauge = Gauge(
    "nova_unlearn_canary_enabled",
    "1 when canary is enabled",
    registry=_REGISTRY,
)

# Phase 10 Ethical Autonomy & Federated Cognition metrics
phase10_eai_gauge = Gauge(
    "nova_phase10_eai",
    "Ethical Autonomy Index (safe_autonomy / decisions × consensus_quality)",
    ["deployment"],
    registry=_REGISTRY,
)

phase10_fcq_gauge = Gauge(
    "nova_phase10_fcq",
    "Federated Consensus Quality for decisions",
    ["decision"],
    registry=_REGISTRY,
)

phase10_cgc_gauge = Gauge(
    "nova_phase10_cgc",
    "Cognitive Graph Coherence across deployments",
    ["mesh"],
    registry=_REGISTRY,
)

phase10_pis_gauge = Gauge(
    "nova_phase10_pis",
    "Provenance Integrity Score for federated ledger",
    ["ledger"],
    registry=_REGISTRY,
)

phase10_ag_throttle_counter = Counter(
    "nova_phase10_ag_throttle_events_total",
    "Total Autonomy Governor throttle events",
    registry=_REGISTRY,
)

phase10_ag_escalation_counter = Counter(
    "nova_phase10_ag_escalations_total",
    "Total Autonomy Governor escalations requiring human review",
    registry=_REGISTRY,
)

canary_seeded_counter = Counter(
    "nova_unlearn_canary_seeded_total",
    "Total canary contexts seeded",
    registry=_REGISTRY,
)

canary_errors_counter = Counter(
    "nova_unlearn_canary_errors_total",
    "Total canary errors",
    registry=_REGISTRY,
)

# Anomaly weighting metrics
anomaly_score_gauge = Gauge(
    "nova_unlearn_anomaly_score",
    "Current EWMA anomaly score for pulse weighting",
    registry=_REGISTRY,
)

anomaly_multiplier_gauge = Gauge(
    "nova_unlearn_anomaly_multiplier",
    "Current anomaly pulse weight multiplier",
    registry=_REGISTRY,
)

# Phase 16-2: Live Peer Synchronization & Context Auto-Switch metrics
wisdom_peer_count_gauge = Gauge(
    "nova_wisdom_peer_count",
    "Number of live peers (for generativity context)",
    registry=_REGISTRY,
)

wisdom_novelty_gauge = Gauge(
    "nova_wisdom_novelty",
    "Current Novelty (N) component from peer diversity",
    registry=_REGISTRY,
)

wisdom_context_gauge = Gauge(
    "nova_wisdom_context",
    "Generativity context state (0=solo, 1=federated)",
    registry=_REGISTRY,
)

federation_sync_latency_histogram = Histogram(
    "nova_federation_sync_latency_seconds",
    "Peer sync request latency distribution",
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=_REGISTRY,
)

federation_sync_errors_counter = Counter(
    "nova_federation_sync_errors_total",
    "Total peer sync errors",
    ["peer_id", "error_type"],
    registry=_REGISTRY,
)

federation_peer_last_seen_gauge = Gauge(
    "nova_federation_peer_last_seen_timestamp",
    "Last seen timestamp for each peer (unix timestamp)",
    ["peer_id"],
    registry=_REGISTRY,
)

anomaly_engaged_gauge = Gauge(
    "nova_unlearn_anomaly_engaged",
    "Anomaly engagement state (0=disengaged, 1=engaged)",
    registry=_REGISTRY,
)

# Phase 17: Secret Scanning & Baseline Attestation metrics
secrets_baseline_findings_gauge = Gauge(
    "nova_secrets_baseline_findings_total",
    "Total secret findings in baseline by risk level",
    ["risk_level"],
    registry=_REGISTRY,
)

secrets_baseline_info = Info(
    "nova_secrets_baseline",
    "Current secrets baseline hash and metadata",
    registry=_REGISTRY,
)

secrets_scan_timestamp_gauge = Gauge(
    "nova_secrets_scan_timestamp",
    "Last secrets baseline scan timestamp (unix)",
    registry=_REGISTRY,
)

# --- local last-seen snapshots so we can turn gauges-in-memory into monotonic counters
_last_sm_totals = {"unlearn_pulses_sent": 0, "entries_expired": 0}
_last_slot_totals: dict[str, int] = defaultdict(int)
_last_fanout = {"fanout_delivered": 0, "fanout_errors": 0}
_last_slot6_metrics = {"decay_events": 0, "decay_amount": 0.0}
_last_canary = {"seeded": 0, "errors": 0}
_last_tri_events = 0

# --- Slot1 Truth Anchor metrics ------------------------------------
slot1_anchors_gauge = Gauge(
    "nova_slot1_anchors_total",
    "Total number of truth anchors registered",
    registry=_REGISTRY,
)

slot1_lookups_counter = Gauge(
    "nova_slot1_lookups_total",
    "Total number of anchor lookups performed",
    registry=_REGISTRY,
)

slot1_recoveries_counter = Gauge(
    "nova_slot1_recoveries_total",
    "Total number of successful anchor recoveries",
    registry=_REGISTRY,
)

slot1_failures_counter = Gauge(
    "nova_slot1_failures_total",
    "Total number of anchor verification failures",
    registry=_REGISTRY,
)


def update_slot6_metrics():
    """Update Slot6 metrics for Prometheus export."""
    s6_metrics = get_slot6_metrics().get_metrics()
    p95 = s6_metrics.get("p95_residual_risk")

    if p95 is not None:
        slot6_p95_residual_risk_gauge.labels(slot="6").set(p95)
    else:
        # Avoid stale sample if window empties / not yet primed
        try:
            slot6_p95_residual_risk_gauge.remove("6")
        except KeyError:
            pass


def update_flag_metrics() -> None:
    """Update feature flag metrics for Prometheus export."""
    # Import inside function to avoid hard import at module import time
    try:
        from nova.slots.slot07_production_controls.flag_metrics import get_flag_state_metrics
        flags = get_flag_state_metrics()
        tri_on   = bool(flags.get("tri_link_enabled", False))
        life_on  = bool(flags.get("lifespan_enabled", False))
        hash_on  = bool(flags.get("shared_hash_enabled", False))
    except Exception:
        # Fallback purely to env (keeps metrics usable even if Slot7 is unavailable)
        tri_on  = _env_truthy("NOVA_ENABLE_TRI_LINK")
        life_on = _env_truthy("NOVA_ENABLE_LIFESPAN")
        hash_on = _env_truthy("NOVA_USE_SHARED_HASH")

    prom_on = _env_truthy("NOVA_ENABLE_PROMETHEUS")
    federation_on = _env_truthy("FEDERATION_ENABLED")
    slot01_root_mode = _env_truthy("NOVA_SLOT01_ROOT_MODE")  # Phase 1f: Root-Mode migration

    feature_flag_gauge.labels(flag="NOVA_ENABLE_TRI_LINK").set(1 if tri_on else 0)
    feature_flag_gauge.labels(flag="NOVA_ENABLE_LIFESPAN").set(1 if life_on else 0)
    feature_flag_gauge.labels(flag="NOVA_USE_SHARED_HASH").set(1 if hash_on else 0)
    feature_flag_gauge.labels(flag="NOVA_ENABLE_PROMETHEUS").set(1 if prom_on else 0)
    feature_flag_gauge.labels(flag="FEDERATION_ENABLED").set(1 if federation_on else 0)
    feature_flag_gauge.labels(flag="NOVA_SLOT01_ROOT_MODE").set(1 if slot01_root_mode else 0)


def update_lightclock_metrics() -> None:
    """Update LightClock phase lock metrics from Slot3."""
    try:
        from orchestrator.semantic_mirror import get_semantic_mirror
        mirror = get_semantic_mirror()
        if mirror:
            phase_lock = mirror.get_context("slot03.phase_lock", "prometheus_metrics")
            if phase_lock is not None:
                lightclock_phase_lock_gauge.set(float(phase_lock))
                return

        # Fallback: try environment variable
        from os import getenv
        env_phase_lock = getenv("SLOT03_PHASE_LOCK")
        if env_phase_lock:
            lightclock_phase_lock_gauge.set(float(env_phase_lock))
        else:
            # Default phase lock value when no data available
            lightclock_phase_lock_gauge.set(0.5)
    except Exception:
        lightclock_phase_lock_gauge.set(0.5)  # Conservative default


def update_semantic_mirror_metrics() -> None:
    """
    Export SemanticMirror metrics into Prometheus counters by incrementing
    with the delta since the last observation. Safe to call on every scrape.
    """
    try:
        from orchestrator.semantic_mirror import get_semantic_mirror
        mirror = get_semantic_mirror()

        if mirror and hasattr(mirror, '_metrics'):
            m = mirror._metrics

            # --- global totals
            for key, counter in (
                ("unlearn_pulses_sent", unlearn_pulses_sent_counter),
                ("entries_expired", entries_expired_counter),
            ):
                cur = int(m.get(key, 0))
                prev = int(_last_sm_totals.get(key, 0))
                delta = cur - prev
                if delta > 0:
                    counter.inc(delta)
                _last_sm_totals[key] = cur

            # --- per-slot totals
            for k, v in m.items():
                if not k.startswith("unlearn_pulse_to_"):
                    continue
                slot = k.split("unlearn_pulse_to_", 1)[1]
                cur = int(v)
                prev = int(_last_slot_totals.get(slot, 0))
                delta = cur - prev
                if delta > 0:
                    unlearn_pulse_destinations_counter.labels(slot=slot).inc(delta)
                _last_slot_totals[slot] = cur
        else:
            # No mirror present: counters remain unchanged (correct for Prometheus)
            pass

        # --- fanout metrics (increment by delta) ---
        from orchestrator.contracts.emitter import get_fanout_metrics
        em = get_fanout_metrics()
        for key, counter in (
            ("fanout_delivered", fanout_delivered_counter),
            ("fanout_errors", fanout_errors_counter),
        ):
            cur = int(em.get(key, 0))
            prev = int(_last_fanout.get(key, 0))
            delta = cur - prev
            if delta > 0:
                counter.inc(delta)
            _last_fanout[key] = cur

        # --- Slot6 decay metrics (increment by delta) ---
        try:
            from nova.slots.slot06_cultural_synthesis.receiver import get_slot6_decay_metrics
            s6 = get_slot6_decay_metrics()
            # events
            cur_e = int(s6.get("decay_events", 0))
            prev_e = int(_last_slot6_metrics.get("decay_events", 0))
            de = cur_e - prev_e
            if de > 0:
                slot6_decay_events_counter.inc(de)
            _last_slot6_metrics["decay_events"] = cur_e
            # amount (float; clamp to non-negative)
            cur_a = float(s6.get("decay_amount", 0.0))
            prev_a = float(_last_slot6_metrics.get("decay_amount", 0.0))
            da = cur_a - prev_a
            if da > 0:
                slot6_decay_amount_counter.inc(da)
            _last_slot6_metrics["decay_amount"] = cur_a
        except Exception:
            # don't increment on exporter errors
            pass

        # --- Canary metrics ---
        import os as _os
        canary_enabled_gauge.set(1.0 if _os.getenv("NOVA_UNLEARN_CANARY", "0") == "1" else 0.0)

        # canary deltas from sm._metrics
        if mirror and hasattr(mirror, '_metrics'):
            m = mirror._metrics
            cur_seeded = int(m.get("canary_seeded", 0))
            delta_seeded = cur_seeded - int(_last_canary.get("seeded", 0))
            if delta_seeded > 0:
                canary_seeded_counter.inc(delta_seeded)
            _last_canary["seeded"] = cur_seeded

            cur_err = int(m.get("canary_errors", 0))
            delta_err = cur_err - int(_last_canary.get("errors", 0))
            if delta_err > 0:
                canary_errors_counter.inc(delta_err)
            _last_canary["errors"] = cur_err

        # --- Anomaly weighting metrics (best-effort; no counters here) ---
        try:
            from orchestrator.unlearn_weighting import get_anomaly_observability
            ao = get_anomaly_observability()
            anomaly_score_gauge.set(float(ao.get("score", 0.0)))
            anomaly_multiplier_gauge.set(float(ao.get("multiplier", 1.0)))
            anomaly_engaged_gauge.set(float(ao.get("engaged", 0.0)))
        except Exception:
            # Leave last values on failure; safe for gauges
            pass
    except Exception:
        # Safe fallback: with counters we do nothing on failure (no false increments)
        pass


def update_system_health_metrics() -> None:
    """Update system pressure, TRI coherence, belief metrics, and deployment gate status."""
    from os import getenv

    try:
        from orchestrator.semantic_mirror import get_semantic_mirror
        mirror = get_semantic_mirror()

        # System pressure from Slot7 (with env fallback)
        pressure = None
        if mirror:
            pressure = mirror.get_context("slot07.pressure_level", "prometheus_metrics")
        if pressure is None:
            pressure = getenv("SLOT07_PRESSURE_LEVEL", "0.3")  # Default low pressure
        system_pressure_gauge.set(float(pressure))

        # TRI coherence from Slot4 (with env fallback)
        coherence = None
        if mirror:
            coherence = mirror.get_context("slot04.coherence", "prometheus_metrics")
        if coherence is None:
            coherence = getenv("TRI_COHERENCE", "0.7")  # Default decent coherence
        tri_coherence_gauge.set(float(coherence))


def update_tri_truth_metrics() -> None:
    """Expose canonical TRI truth signal + attestation bridge metrics."""
    try:
        from orchestrator.tri_truth_bridge import get_bridge_metrics
    except Exception:
        return

    try:
        metrics = get_bridge_metrics()
    except Exception:
        return

    coherence = metrics.get("tri_coherence")
    if coherence is not None:
        tri_coherence_current_gauge.set(float(coherence))

    canonical_hash = metrics.get("canonical_hash")
    if canonical_hash:
        tri_canonization_hash_info.info({"hash": str(canonical_hash)})

    global _last_tri_events
    attest_events = metrics.get("attest_events", 0)
    if isinstance(attest_events, (int, float)):
        delta = float(attest_events) - float(_last_tri_events)
        if delta > 0:
            tri_to_anchor_events_counter.inc(delta)
        _last_tri_events = attest_events

    avg_latency = metrics.get("attest_latency_ms_avg")
    if avg_latency is not None:
        slot01_attest_latency_gauge.set(float(avg_latency))

    try:
        from nova.slots.slot07_production_controls import wisdom_backpressure as wb

        tri_snapshot = wb.get_tri_signal_snapshot()
    except Exception:
        tri_snapshot = None

    if tri_snapshot:
        coherence = tri_snapshot.get("tri_coherence")
        if coherence is not None:
            slot07_tri_coherence_gauge.set(float(coherence))
        drift = tri_snapshot.get("tri_drift_z")
        try:
            slot07_tri_drift_gauge.set(float(drift))
        except (TypeError, ValueError):
            pass
        jitter = tri_snapshot.get("tri_jitter")
        try:
            slot07_tri_jitter_gauge.set(float(jitter))
        except (TypeError, ValueError):
            pass

        # Phase 6.0 Belief metrics from probabilistic contracts
        if mirror:
            # Slot 4 TRI belief
            tri_belief = mirror.get_context("slot04.tri_belief", "prometheus_metrics")
            if tri_belief and hasattr(tri_belief, 'mean'):
                slot_phase_lock_belief_mean_gauge.labels(slot="4").set(tri_belief.mean)
                slot_phase_lock_belief_variance_gauge.labels(slot="4").set(tri_belief.variance)

            # Slot 7 Production Controls belief
            pc_belief = mirror.get_context("slot07.phase_lock_belief", "prometheus_metrics")
            if pc_belief and hasattr(pc_belief, 'mean'):
                slot_phase_lock_belief_mean_gauge.labels(slot="7").set(pc_belief.mean)
                slot_phase_lock_belief_variance_gauge.labels(slot="7").set(pc_belief.variance)

        # Deployment gate status - always compute even with defaults
        try:
            from nova.slots.slot10_civilizational_deployment.core.lightclock_gatekeeper import LightClockGatekeeper
            gatekeeper = LightClockGatekeeper(mirror=mirror)
            gate_open = gatekeeper.should_open_gate()
            deployment_gate_gauge.set(1 if gate_open else 0)
        except Exception:
            deployment_gate_gauge.set(0)  # Conservative: gate closed on error

    except Exception:
        # Complete fallback - set reasonable defaults
        system_pressure_gauge.set(0.3)
        tri_coherence_gauge.set(0.7)
        deployment_gate_gauge.set(0)


def update_slot1_metrics() -> None:
    """Update Slot1 truth anchor metrics for Prometheus export."""
    try:
        from orchestrator.adapters.slot1_truth_anchor import Slot1TruthAnchorAdapter
        adapter = Slot1TruthAnchorAdapter()

        if adapter.available:
            snapshot = adapter.snapshot()
            slot1_anchors_gauge.set(snapshot.get("anchors", 0))
            slot1_lookups_counter.set(snapshot.get("lookups", 0))
            slot1_recoveries_counter.set(snapshot.get("recoveries", 0))
            slot1_failures_counter.set(snapshot.get("failures", 0))
        else:
            # Clear metrics if Slot1 not available
            slot1_anchors_gauge.set(0)
            slot1_lookups_counter.set(0)
            slot1_recoveries_counter.set(0)
            slot1_failures_counter.set(0)
    except Exception:
        # Fallback - set all to 0 if Slot1 unavailable
        slot1_anchors_gauge.set(0)
        slot1_lookups_counter.set(0)
        slot1_recoveries_counter.set(0)
        slot1_failures_counter.set(0)


def update_secrets_baseline_metrics() -> None:
    """Update Phase 17 secret scanning metrics for Prometheus export."""
    from pathlib import Path
    import json
    from datetime import datetime

    try:
        # Load attestation if exists
        attestation_path = Path('.artifacts/secrets-baseline-attestation.json')
        if not attestation_path.exists():
            return  # No baseline yet

        attestation = json.loads(attestation_path.read_text())

        # Update info metric (hash, timestamp, file count)
        secrets_baseline_info.info({
            'hash': attestation.get('baseline_hash', '')[:16],
            'timestamp': attestation.get('timestamp', ''),
            'file_count': str(attestation.get('statistics', {}).get('file_count', 0)),
            'finding_count': str(attestation.get('statistics', {}).get('finding_count', 0))
        })

        # Update scan timestamp
        timestamp_str = attestation.get('timestamp', '')
        if timestamp_str:
            try:
                dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                secrets_scan_timestamp_gauge.set(dt.timestamp())
            except (ValueError, AttributeError):
                pass

        # Load risk classification report if exists
        report_path = Path('.artifacts/secrets-audit.md')
        if report_path.exists():
            report = report_path.read_text()

            # Parse findings counts from report
            for risk in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']:
                # Look for pattern like "## 🔴 CRITICAL Risk (5 findings)"
                import re
                pattern = rf'##.*{risk}.*\((\d+)\s+findings?\)'
                match = re.search(pattern, report)
                if match:
                    count = int(match.group(1))
                    secrets_baseline_findings_gauge.labels(risk_level=risk).set(count)
                else:
                    secrets_baseline_findings_gauge.labels(risk_level=risk).set(0)

    except Exception as e:
        logger.debug(f"Could not update secrets baseline metrics: {e}")


def get_metrics_response():
    """Get Prometheus metrics response."""
    update_slot6_metrics()
    update_flag_metrics()
    update_slot1_metrics()
    update_lightclock_metrics()
    update_system_health_metrics()
    update_tri_truth_metrics()
    update_semantic_mirror_metrics()
    update_secrets_baseline_metrics()
    payload = generate_latest(_REGISTRY)
    try:
        federation_registry = get_federation_registry()
        federation_payload = generate_latest(federation_registry)
        if federation_payload:
            if payload and not payload.endswith(b"\n"):
                payload += b"\n"
            payload += federation_payload
    except Exception as exc:  # pragma: no cover - best-effort federation metrics
        logger.debug("Federation metrics export failed: %s", exc)
    return payload, CONTENT_TYPE_LATEST
