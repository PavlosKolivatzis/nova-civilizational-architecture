"""Prometheus metrics export for Nova system."""

import logging

from prometheus_client import Gauge, Counter, Histogram, Info, generate_latest, CONTENT_TYPE_LATEST
from collections import defaultdict
from typing import Dict, Optional
import subprocess
from time import strftime, gmtime
from os import getenv

from nova.orchestrator.metrics import get_slot6_metrics
from nova.orchestrator.prometheus.internal_registry import nova_internal_registry
from nova.orchestrator.prometheus.public_registry import nova_public_registry
from nova.federation.metrics import get_registry as get_federation_registry
from nova.metrics.registry import REGISTRY

# Dedicated registries (internal + public)
_INTERNAL_REGISTRY = nova_internal_registry
_PUBLIC_REGISTRY = nova_public_registry
# Backward compatibility for modules importing _REGISTRY directly
_REGISTRY = _INTERNAL_REGISTRY


def _collector_from_registry(registry, name: str):
    mapping = getattr(registry, "_names_to_collectors", None)
    if mapping:
        return mapping.get(name)
    return None


def _get_or_register_info(name: str, documentation: str, registry):
    existing = _collector_from_registry(registry, name)
    if existing:
        return existing
    return Info(name, documentation, registry=registry)


def _get_or_register_gauge(name: str, documentation: str, *, labelnames=(), registry, **kwargs):
    existing = _collector_from_registry(registry, name)
    if existing:
        return existing
    return Gauge(name, documentation, labelnames=labelnames, registry=registry, **kwargs)


def _get_or_register_counter(name: str, documentation: str, *, labelnames=(), registry):
    existing = _collector_from_registry(registry, name)
    if existing:
        return existing
    return Counter(name, documentation, labelnames=labelnames, registry=registry)
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
build_info_internal = _get_or_register_info(
    'nova_build',
    'Nova build information for deployment traceability',
    registry=_INTERNAL_REGISTRY,
)
build_info_public = _get_or_register_info(
    'nova_build',
    'Nova build information for deployment traceability',
    registry=_PUBLIC_REGISTRY,
)

# Initialize build info at module load
for build_info in (build_info_internal, build_info_public):
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
    registry=_INTERNAL_REGISTRY,
)

# --- Flag gauges (Phase 2 feature flags) ------------------------------------
def _env_truthy(name: str) -> bool:
    v = (getenv(name, "") or "").strip()
    return v == "1"

# One gauge, labeled by flag name
feature_flag_gauge_internal = Gauge(
    "nova_feature_flag_enabled",
    "Nova Phase-2 feature flag states",
    ["flag"],
    registry=_INTERNAL_REGISTRY,
)
feature_flag_gauge_public = Gauge(
    "nova_feature_flag_enabled",
    "Nova Phase-2 feature flag states",
    ["flag"],
    registry=_PUBLIC_REGISTRY,
)

# Threshold gauges (Phase 3)
_threshold_value_gauge = Gauge(
    "nova_threshold_value",
    "Configured threshold values across slots",
    ["name"],
    registry=_INTERNAL_REGISTRY,
)
_threshold_override_gauge = Gauge(
    "nova_threshold_override_active",
    "Whether a given threshold is overridden via environment",
    ["name"],
    registry=_INTERNAL_REGISTRY,
)


def threshold_gauge(name: str, value: float) -> None:
    """Expose threshold value to Prometheus (internal registry only)."""
    _threshold_value_gauge.labels(name=name).set(value)


def threshold_override_gauge(name: str, value: float) -> None:
    """Expose whether an environment override is applied (1.0) or not (0.0)."""
    _threshold_override_gauge.labels(name=name).set(value)

# Router metrics
router_route_selected_gauge_public = Gauge(
    "nova_route_selected",
    "Most recent routing decision",
    ["route"],
    registry=_PUBLIC_REGISTRY,
)
router_constraint_counter_public = Counter(
    "nova_route_constraints_total",
    "Constraint evaluation results",
    ["result"],
    registry=_PUBLIC_REGISTRY,
)
router_constraint_snapshot_info = Info(
    "nova_router_constraint_snapshot",
    "Last constraint snapshot (internal)",
    registry=_INTERNAL_REGISTRY,
)
router_policy_info = Info(
    "nova_router_anr_policy",
    "Last ANR/static policy output",
    registry=_INTERNAL_REGISTRY,
)
router_advisor_slot05_gauge = Gauge(
    "nova_router_advisor_slot05",
    "Advisor score from Slot05 constellation",
    registry=_INTERNAL_REGISTRY,
)
router_advisor_slot08_gauge = Gauge(
    "nova_router_advisor_slot08",
    "Advisor score from Slot08 semantic continuity",
    registry=_INTERNAL_REGISTRY,
)
router_final_score_gauge = Gauge(
    "nova_router_final_score",
    "Final deterministic routing score",
    registry=_INTERNAL_REGISTRY,
)

# Temporal placeholder metric (Phase-6 scaffold)
temporal_drift_gauge = _get_or_register_gauge(
    "nova_temporal_drift",
    "Temporal drift between successive TRI snapshots",
    registry=_INTERNAL_REGISTRY,
)
temporal_variance_gauge = _get_or_register_gauge(
    "nova_temporal_variance",
    "Variance of recent TRI coherence values",
    registry=_INTERNAL_REGISTRY,
)
temporal_prediction_error_gauge = _get_or_register_gauge(
    "nova_temporal_prediction_error",
    "Prediction error between expected and observed coherence",
    registry=_INTERNAL_REGISTRY,
)
temporal_convergence_gauge = _get_or_register_gauge(
    "nova_temporal_convergence",
    "Temporal convergence metric",
    registry=_INTERNAL_REGISTRY,
)
temporal_divergence_gauge = _get_or_register_gauge(
    "nova_temporal_divergence",
    "Temporal divergence penalty",
    registry=_INTERNAL_REGISTRY,
)
temporal_snapshot_timestamp_gauge = _get_or_register_gauge(
    "nova_temporal_snapshot_timestamp",
    "Timestamp of last temporal snapshot",
    registry=_INTERNAL_REGISTRY,
)
temporal_router_state_gauge = _get_or_register_gauge(
    "nova_temporal_router_state",
    "Public-safe temporal router readiness",
    registry=_PUBLIC_REGISTRY,
)

# Predictive metrics (Phase-7)
predictive_collapse_risk_gauge = _get_or_register_gauge(
    "nova_predictive_collapse_risk",
    "Predictive collapse likelihood (0-1)",
    registry=_INTERNAL_REGISTRY,
)
predictive_acceleration_gauge = _get_or_register_gauge(
    "nova_predictive_acceleration",
    "Absolute predictive drift acceleration",
    registry=_INTERNAL_REGISTRY,
)
predictive_safe_corridor_gauge = _get_or_register_gauge(
    "nova_predictive_safe_corridor",
    "Predictive safe corridor status (internal)",
    registry=_INTERNAL_REGISTRY,
)
predictive_safe_corridor_public_gauge = _get_or_register_gauge(
    "nova_predictive_safe_corridor_public",
    "Public-safe predictive safe corridor indicator",
    registry=_PUBLIC_REGISTRY,
)
# Continuity metrics (Phase-8)
continuity_stability_index_gauge = _get_or_register_gauge(
    "nova_continuity_stability_index",
    "Continuity Stability Index (CSI) across phases",
    registry=_INTERNAL_REGISTRY,
)
continuity_p6_stability_gauge = _get_or_register_gauge(
    "nova_continuity_p6_stability",
    "Phase 6 stability component of CSI",
    registry=_INTERNAL_REGISTRY,
)
continuity_p7_stability_gauge = _get_or_register_gauge(
    "nova_continuity_p7_stability",
    "Phase 7 stability component of CSI",
    registry=_INTERNAL_REGISTRY,
)
continuity_correlation_gauge = _get_or_register_gauge(
    "nova_continuity_correlation",
    "Inter-phase correlation component of CSI",
    registry=_INTERNAL_REGISTRY,
)

# Phase 9: Unified Risk Field (URF) metrics
risk_alignment_gauge = _get_or_register_gauge(
    "nova_risk_alignment",
    "Unified Risk Field alignment score [0.0, 1.0] (1.0 = perfect RRI/collapse_risk alignment)",
    registry=_INTERNAL_REGISTRY,
)
risk_gap_gauge = _get_or_register_gauge(
    "nova_risk_gap",
    "Absolute gap between RRI and predictive_collapse_risk [0.0, 1.0]",
    registry=_INTERNAL_REGISTRY,
)
composite_risk_gauge = _get_or_register_gauge(
    "nova_composite_risk",
    "Unified composite risk signal for governance [0.0, 1.0]",
    registry=_INTERNAL_REGISTRY,
)

# Phase 10: Meta-Stability Engine (MSE) metrics
meta_instability_gauge = _get_or_register_gauge(
    "nova_meta_instability",
    "Meta-stability variance metric [0.0, 1.0] (variance of composite_risk)",
    registry=_INTERNAL_REGISTRY,
)
mse_trend_gauge = _get_or_register_gauge(
    "nova_mse_trend",
    "MSE trend classification (0=stable, 1=oscillating, 2=runaway)",
    registry=_INTERNAL_REGISTRY,
)
mse_drift_velocity_gauge = _get_or_register_gauge(
    "nova_mse_drift_velocity",
    "Rate of change in meta_instability (d/dt)",
    registry=_INTERNAL_REGISTRY,
)
mse_sample_count_gauge = _get_or_register_gauge(
    "nova_mse_sample_count",
    "Number of samples in current MSE window",
    registry=_INTERNAL_REGISTRY,
)

# Phase 11: Operational Regime Policy (ORP) metrics
orp_regime_gauge = _get_or_register_gauge(
    "nova_orp_regime",
    "Current operational regime (0=normal, 1=heightened, 2=controlled, 3=emergency, 4=recovery)",
    registry=_INTERNAL_REGISTRY,
)
orp_regime_score_gauge = _get_or_register_gauge(
    "nova_orp_regime_score",
    "Composite regime severity score [0.0, 1.0]",
    registry=_INTERNAL_REGISTRY,
)
orp_threshold_multiplier_gauge = _get_or_register_gauge(
    "nova_orp_threshold_multiplier",
    "Active threshold multiplier (1.0=normal, <1.0=tighter)",
    registry=_INTERNAL_REGISTRY,
)
orp_traffic_limit_gauge = _get_or_register_gauge(
    "nova_orp_traffic_limit",
    "Active traffic capacity limit [0.0, 1.0]",
    registry=_INTERNAL_REGISTRY,
)
orp_deployment_freeze_gauge = _get_or_register_gauge(
    "nova_orp_deployment_freeze",
    "Deployment freeze active (0=no, 1=yes)",
    registry=_INTERNAL_REGISTRY,
)
orp_safe_mode_forced_gauge = _get_or_register_gauge(
    "nova_orp_safe_mode_forced",
    "Safe mode forced (0=no, 1=yes)",
    registry=_INTERNAL_REGISTRY,
)
orp_regime_transitions_counter = _get_or_register_counter(
    "nova_orp_regime_transitions_total",
    "Regime transition events",
    labelnames=("from_regime", "to_regime"),
    registry=_INTERNAL_REGISTRY,
)

predictive_penalty_gauge = _get_or_register_gauge(
    "nova_predictive_penalty",
    "Latest predictive routing penalty",
    registry=_INTERNAL_REGISTRY,
)
predictive_warning_counter = _get_or_register_counter(
    "nova_predictive_warning_total",
    "Count of predictive warnings/foresight holds",
    labelnames=("reason",),
    registry=_INTERNAL_REGISTRY,
)

# Phase 7 Step 6: Multi-Slot Consistency (MSC) metrics
consistency_gap_gauge = _get_or_register_gauge(
    "nova_predictive_consistency_gap",
    "Composite consistency gap score (0..1)",
    registry=_INTERNAL_REGISTRY,
)
consistency_severity_gauge = _get_or_register_gauge(
    "nova_predictive_consistency_severity",
    "Maximum component conflict severity (0..1)",
    registry=_INTERNAL_REGISTRY,
)
consistency_safety_prod_gauge = _get_or_register_gauge(
    "nova_predictive_consistency_safety_prod",
    "Safety-production conflict component (0..1)",
    registry=_INTERNAL_REGISTRY,
)
consistency_culture_deploy_gauge = _get_or_register_gauge(
    "nova_predictive_consistency_culture_deploy",
    "Culture-deployment conflict component (0..1)",
    registry=_INTERNAL_REGISTRY,
)
consistency_prod_predictive_gauge = _get_or_register_gauge(
    "nova_predictive_consistency_prod_predictive",
    "Production-predictive conflict component (0..1)",
    registry=_INTERNAL_REGISTRY,
)

# Phase 7.0-RC: Memory Resonance (7-day TRSI stability tracking)
memory_stability_gauge = _get_or_register_gauge(
    "nova_memory_stability",
    "7-day rolling TRSI stability score (mean - stdev)",
    registry=_INTERNAL_REGISTRY,
)
memory_samples_gauge = _get_or_register_gauge(
    "nova_memory_samples",
    "Number of TRSI samples in rolling window",
    registry=_INTERNAL_REGISTRY,
)
memory_volatility_gauge = _get_or_register_gauge(
    "nova_memory_volatility",
    "7-day TRSI volatility (standard deviation)",
    registry=_INTERNAL_REGISTRY,
)
memory_trend_gauge = _get_or_register_gauge(
    "nova_memory_trend_24h",
    "TRSI trend over last 24 hours",
    registry=_INTERNAL_REGISTRY,
)

# Phase 7.0-RC: RIS (Resonance Integrity Score)
ris_score_gauge = _get_or_register_gauge(
    "nova_ris_score",
    "Resonance Integrity Score for RC attestation (sqrt(M_s × E_c))",
    registry=_INTERNAL_REGISTRY,
)
ris_component_gauge = _get_or_register_gauge(
    "nova_ris_component",
    "Individual RIS component scores",
    labelnames=("component_type",),
    registry=_INTERNAL_REGISTRY,
)

# Phase 7.0-RC: Stress Simulation (resilience testing)
stress_injection_active_gauge = _get_or_register_gauge(
    "nova_stress_injection_active",
    "Stress injection active state (1=active, 0=inactive)",
    registry=_INTERNAL_REGISTRY,
)
stress_recovery_rate_gauge = _get_or_register_gauge(
    "nova_stress_recovery_rate",
    "Normalized recovery rate after stress injection [0.0, 1.0]",
    registry=_INTERNAL_REGISTRY,
)
stress_baseline_gauge = _get_or_register_gauge(
    "nova_stress_baseline_ris",
    "Baseline RIS before stress injection",
    registry=_INTERNAL_REGISTRY,
)
stress_recovery_ticks_gauge = _get_or_register_gauge(
    "nova_stress_ticks_to_recover",
    "Number of ticks to recover to 90% baseline",
    registry=_INTERNAL_REGISTRY,
)
stress_max_deviation_gauge = _get_or_register_gauge(
    "nova_stress_max_deviation",
    "Maximum RIS deviation during stress test",
    registry=_INTERNAL_REGISTRY,
)
stress_last_run_gauge = _get_or_register_gauge(
    "nova_stress_last_run_timestamp",
    "Unix timestamp of last stress simulation",
    registry=_INTERNAL_REGISTRY,
)
stress_injection_counter = _get_or_register_counter(
    "nova_stress_injection_total",
    "Total stress injection events by mode",
    labelnames=("mode",),
    registry=_INTERNAL_REGISTRY,
)
stress_min_ris_gauge = _get_or_register_gauge(
    "nova_stress_min_ris",
    "Minimum RIS observed during stress test",
    registry=_INTERNAL_REGISTRY,
)
stress_min_stability_gauge = _get_or_register_gauge(
    "nova_stress_min_stability",
    "Minimum memory stability observed during stress test",
    registry=_INTERNAL_REGISTRY,
)

# Phase 7.0-RC: RC Criteria Gates
rc_gate_status_gauge = _get_or_register_gauge(
    "nova_rc_gate_status",
    "RC criteria gate pass/fail status (1=pass, 0=fail)",
    labelnames=("gate_name",),
    registry=_INTERNAL_REGISTRY,
)
rc_overall_pass_gauge = _get_or_register_gauge(
    "nova_rc_overall_pass",
    "Overall RC criteria pass status (1=pass, 0=fail)",
    registry=_INTERNAL_REGISTRY,
)


# --- LightClock & System Health metrics ------------------------------------
lightclock_phase_lock_gauge = Gauge(
    "nova_lightclock_phase_lock",
    "Current LightClock phase lock value from Slot3",
    registry=_INTERNAL_REGISTRY,
)

# Phase 6.0 Probabilistic Contracts metrics
slot_phase_lock_belief_mean_gauge = Gauge(
    "nova_slot_phase_lock_belief_mean",
    "Phase lock belief mean from probabilistic contracts",
    ["slot"],
    registry=_INTERNAL_REGISTRY,
)

slot_phase_lock_belief_variance_gauge = Gauge(
    "nova_slot_phase_lock_belief_variance",
    "Phase lock belief variance from probabilistic contracts",
    ["slot"],
    registry=_INTERNAL_REGISTRY,
)

system_pressure_gauge = Gauge(
    "nova_system_pressure_level",
    "System pressure level from Slot7",
    registry=_INTERNAL_REGISTRY,
)

tri_coherence_gauge = Gauge(
    "nova_tri_coherence",
    "TRI signal coherence from Slot4",
    registry=_INTERNAL_REGISTRY,
)

tri_coherence_current_gauge = Gauge(
    "nova_tri_coherence_current",
    "Canonical TRI coherence value emitted via tri_truth_signal@1",
    ["slot", "mode", "source"],
    registry=_INTERNAL_REGISTRY,
)
tri_coherence_current_gauge_public = Gauge(
    "nova_tri_coherence_current",
    "Canonical TRI coherence value emitted via tri_truth_signal@1",
    ["slot", "mode", "source"],
    registry=_PUBLIC_REGISTRY,
)

tri_canonization_hash_info = Info(
    "nova_tri_canonization_hash",
    "Latest TRI canonical hash (for debugging/attestation linkage)",
    registry=_INTERNAL_REGISTRY,
)
tri_canonization_hash_info_public = Info(
    "nova_tri_canonization_hash",
    "Latest TRI canonical hash (for debugging/attestation linkage)",
    registry=_PUBLIC_REGISTRY,
)

tri_to_anchor_events_counter = Counter(
    "nova_tri_to_anchor_events_total",
    "Total TRI -> Slot01 attestation events triggered via Root-Mode bridge",
    ["slot", "mode", "source"],
    registry=_INTERNAL_REGISTRY,
)

slot01_attest_latency_gauge = Gauge(
    "nova_slot01_attest_latency_ms",
    "Average latency (ms) for TRI-triggered Slot01 attestation events",
    ["slot", "mode", "source"],
    registry=_INTERNAL_REGISTRY,
)
slot01_attest_latency_gauge_public = Gauge(
    "nova_slot01_attest_latency_ms",
    "Average latency (ms) for TRI-triggered Slot01 attestation events",
    ["slot", "mode", "source"],
    registry=_PUBLIC_REGISTRY,
)

slot07_tri_coherence_gauge = Gauge(
    "nova_slot07_tri_coherence",
    "Latest TRI coherence snapshot consumed by Slot07 backpressure",
    ["slot", "mode", "source"],
    registry=_INTERNAL_REGISTRY,
)
slot07_tri_coherence_gauge_public = Gauge(
    "nova_slot07_tri_coherence",
    "Latest TRI coherence snapshot consumed by Slot07 backpressure",
    ["slot", "mode", "source"],
    registry=_PUBLIC_REGISTRY,
)

slot07_tri_drift_gauge = Gauge(
    "nova_slot07_tri_drift_z",
    "Latest TRI drift Z-score consumed by Slot07 backpressure",
    ["slot", "mode", "source"],
    registry=_INTERNAL_REGISTRY,
)
slot07_tri_drift_gauge_public = Gauge(
    "nova_slot07_tri_drift_z",
    "Latest TRI drift Z-score consumed by Slot07 backpressure",
    ["slot", "mode", "source"],
    registry=_PUBLIC_REGISTRY,
)

slot07_tri_jitter_gauge = Gauge(
    "nova_slot07_tri_jitter",
    "Latest TRI jitter snapshot consumed by Slot07 backpressure",
    ["slot", "mode", "source"],
    registry=_INTERNAL_REGISTRY,
)
slot07_tri_jitter_gauge_public = Gauge(
    "nova_slot07_tri_jitter",
    "Latest TRI jitter snapshot consumed by Slot07 backpressure",
    ["slot", "mode", "source"],
    registry=_PUBLIC_REGISTRY,
)

TRI_SIGNAL_LABELS = {"slot": "04", "mode": "canonized", "source": "tri_truth_signal"}
SLOT07_LABELS = {"slot": "07", "mode": "governor", "source": "tri_truth_signal"}


def _slot01_labels() -> Dict[str, str]:
    mode = "root" if _env_truthy("NOVA_SLOT01_ROOT_MODE") else "legacy"
    return {"slot": "01", "mode": mode, "source": "tri_truth_signal"}

deployment_gate_gauge = Gauge(
    "nova_deployment_gate_open",
    "Whether Slot10 deployment gate is open (1=open, 0=closed)",
    registry=_INTERNAL_REGISTRY,
)

semantic_mirror_ops_counter = Gauge(
    "nova_semantic_mirror_operations_total",
    "Total semantic mirror operations",
    ["operation_type"],
    registry=_INTERNAL_REGISTRY,
)

# Reciprocal Contextual Unlearning metrics (counters)
unlearn_pulses_sent_counter = Counter(
    "nova_unlearn_pulses_sent_total",
    "Total unlearn pulses sent on context expiration",
    registry=_INTERNAL_REGISTRY,
)

entries_expired_counter = Counter(
    "nova_entries_expired_total",
    "Total context entries expired from semantic mirror",
    registry=_INTERNAL_REGISTRY,
)

unlearn_pulse_destinations_counter = Counter(
    "nova_unlearn_pulse_to_slot_total",
    "Unlearn pulses sent to specific slots",
    ["slot"],
    registry=_INTERNAL_REGISTRY,
)

# Contract fanout metrics (counters)
fanout_delivered_counter = Counter(
    "nova_fanout_delivered_total",
    "Total local contract fanout deliveries",
    registry=_INTERNAL_REGISTRY,
)

fanout_errors_counter = Counter(
    "nova_fanout_errors_total",
    "Total local contract fanout errors",
    registry=_INTERNAL_REGISTRY,
)

# Slot6 decay metrics
slot6_decay_events_counter = Counter(
    "nova_slot6_decay_events_total",
    "Total number of decay events processed by Slot6",
    registry=_INTERNAL_REGISTRY,
)

slot6_decay_amount_counter = Counter(
    "nova_slot6_decay_amount_total",
    "Total decay amount processed by Slot6 (sum of old_weight - new_weight)",
    registry=_INTERNAL_REGISTRY,
)

# Canary metrics
canary_enabled_gauge = Gauge(
    "nova_unlearn_canary_enabled",
    "1 when canary is enabled",
    registry=_INTERNAL_REGISTRY,
)

# Phase 10 Ethical Autonomy & Federated Cognition metrics
phase10_eai_gauge = Gauge(
    "nova_phase10_eai",
    "Ethical Autonomy Index (safe_autonomy / decisions × consensus_quality)",
    ["deployment"],
    registry=_INTERNAL_REGISTRY,
)
phase10_eai_gauge_public = Gauge(
    "nova_phase10_eai",
    "Ethical Autonomy Index (safe_autonomy / decisions × consensus_quality)",
    ["deployment"],
    registry=_PUBLIC_REGISTRY,
)

phase10_fcq_gauge = Gauge(
    "nova_phase10_fcq",
    "Federated Consensus Quality for decisions",
    ["decision"],
    registry=_INTERNAL_REGISTRY,
)
phase10_fcq_gauge_public = Gauge(
    "nova_phase10_fcq",
    "Federated Consensus Quality for decisions",
    ["decision"],
    registry=_PUBLIC_REGISTRY,
)

phase10_cgc_gauge = Gauge(
    "nova_phase10_cgc",
    "Cognitive Graph Coherence across deployments",
    ["mesh"],
    registry=_INTERNAL_REGISTRY,
)
phase10_cgc_gauge_public = Gauge(
    "nova_phase10_cgc",
    "Cognitive Graph Coherence across deployments",
    ["mesh"],
    registry=_PUBLIC_REGISTRY,
)

phase10_pis_gauge = Gauge(
    "nova_phase10_pis",
    "Provenance Integrity Score for federated ledger",
    ["ledger"],
    registry=_INTERNAL_REGISTRY,
)
phase10_pis_gauge_public = Gauge(
    "nova_phase10_pis",
    "Provenance Integrity Score for federated ledger",
    ["ledger"],
    registry=_PUBLIC_REGISTRY,
)

phase10_ag_throttle_counter = Counter(
    "nova_phase10_ag_throttle_events_total",
    "Total Autonomy Governor throttle events",
    registry=_INTERNAL_REGISTRY,
)
phase10_ag_throttle_counter_public = Counter(
    "nova_phase10_ag_throttle_events_total",
    "Total Autonomy Governor throttle events",
    registry=_PUBLIC_REGISTRY,
)

phase10_ag_escalation_counter = Counter(
    "nova_phase10_ag_escalations_total",
    "Total Autonomy Governor escalations requiring human review",
    registry=_INTERNAL_REGISTRY,
)
phase10_ag_escalation_counter_public = Counter(
    "nova_phase10_ag_escalations_total",
    "Total Autonomy Governor escalations requiring human review",
    registry=_PUBLIC_REGISTRY,
)

canary_seeded_counter = Counter(
    "nova_unlearn_canary_seeded_total",
    "Total canary contexts seeded",
    registry=_INTERNAL_REGISTRY,
)

canary_errors_counter = Counter(
    "nova_unlearn_canary_errors_total",
    "Total canary errors",
    registry=_INTERNAL_REGISTRY,
)

# Anomaly weighting metrics
anomaly_score_gauge = Gauge(
    "nova_unlearn_anomaly_score",
    "Current EWMA anomaly score for pulse weighting",
    registry=_INTERNAL_REGISTRY,
)

anomaly_multiplier_gauge = Gauge(
    "nova_unlearn_anomaly_multiplier",
    "Current anomaly pulse weight multiplier",
    registry=_INTERNAL_REGISTRY,
)

# Phase 16-2: Live Peer Synchronization & Context Auto-Switch metrics
wisdom_peer_count_gauge = Gauge(
    "nova_wisdom_peer_count",
    "Number of live peers (for generativity context)",
    registry=_INTERNAL_REGISTRY,
)

wisdom_novelty_gauge = Gauge(
    "nova_wisdom_novelty",
    "Current Novelty (N) component from peer diversity",
    registry=_INTERNAL_REGISTRY,
)

wisdom_context_gauge = Gauge(
    "nova_wisdom_context",
    "Generativity context state (0=solo, 1=federated)",
    registry=_INTERNAL_REGISTRY,
)

federation_sync_latency_histogram = Histogram(
    "nova_federation_sync_latency_seconds",
    "Peer sync request latency distribution",
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=_INTERNAL_REGISTRY,
)

federation_sync_errors_counter = Counter(
    "nova_federation_sync_errors_total",
    "Total peer sync errors",
    ["peer_id", "error_type"],
    registry=_INTERNAL_REGISTRY,
)

federation_peer_last_seen_gauge = Gauge(
    "nova_federation_peer_last_seen_timestamp",
    "Last seen timestamp for each peer (unix timestamp)",
    ["peer_id"],
    registry=_INTERNAL_REGISTRY,
)

anomaly_engaged_gauge = Gauge(
    "nova_unlearn_anomaly_engaged",
    "Anomaly engagement state (0=disengaged, 1=engaged)",
    registry=_INTERNAL_REGISTRY,
)

# Phase 17: Secret Scanning & Baseline Attestation metrics
secrets_baseline_findings_gauge = Gauge(
    "nova_secrets_baseline_findings_total",
    "Total secret findings in baseline by risk level",
    ["risk_level"],
    registry=_INTERNAL_REGISTRY,
)

secrets_baseline_info = Info(
    "nova_secrets_baseline",
    "Current secrets baseline hash and metadata",
    registry=_INTERNAL_REGISTRY,
)

secrets_scan_timestamp_gauge = Gauge(
    "nova_secrets_scan_timestamp",
    "Last secrets baseline scan timestamp (unix)",
    registry=_INTERNAL_REGISTRY,
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
    registry=_INTERNAL_REGISTRY,
)
slot1_anchors_gauge_public = Gauge(
    "nova_slot1_anchors_total",
    "Total number of truth anchors registered",
    registry=_PUBLIC_REGISTRY,
)

slot1_lookups_counter = Gauge(
    "nova_slot1_lookups_total",
    "Total number of anchor lookups performed",
    registry=_INTERNAL_REGISTRY,
)
slot1_lookups_counter_public = Gauge(
    "nova_slot1_lookups_total",
    "Total number of anchor lookups performed",
    registry=_PUBLIC_REGISTRY,
)

slot1_recoveries_counter = Gauge(
    "nova_slot1_recoveries_total",
    "Total number of successful anchor recoveries",
    registry=_INTERNAL_REGISTRY,
)
slot1_recoveries_counter_public = Gauge(
    "nova_slot1_recoveries_total",
    "Total number of successful anchor recoveries",
    registry=_PUBLIC_REGISTRY,
)

slot1_failures_counter = Gauge(
    "nova_slot1_failures_total",
    "Total number of anchor verification failures",
    registry=_INTERNAL_REGISTRY,
)
slot1_failures_counter_public = Gauge(
    "nova_slot1_failures_total",
    "Total number of anchor verification failures",
    registry=_PUBLIC_REGISTRY,
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
    def _set_flag(flag_name: str, enabled: bool) -> None:
        value = 1 if enabled else 0
        feature_flag_gauge_internal.labels(flag=flag_name).set(value)
        feature_flag_gauge_public.labels(flag=flag_name).set(value)

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

    _set_flag("NOVA_ENABLE_TRI_LINK", tri_on)
    _set_flag("NOVA_ENABLE_LIFESPAN", life_on)
    _set_flag("NOVA_USE_SHARED_HASH", hash_on)
    _set_flag("NOVA_ENABLE_PROMETHEUS", prom_on)
    _set_flag("FEDERATION_ENABLED", federation_on)
    _set_flag("NOVA_SLOT01_ROOT_MODE", slot01_root_mode)


def update_lightclock_metrics() -> None:
    """Update LightClock phase lock metrics from Slot3."""
    try:
        from nova.orchestrator.semantic_mirror import get_semantic_mirror
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
        from nova.orchestrator.semantic_mirror import get_semantic_mirror
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
        from nova.orchestrator.contracts.emitter import get_fanout_metrics
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
            from nova.orchestrator.unlearn_weighting import get_anomaly_observability
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
        from nova.orchestrator.semantic_mirror import get_semantic_mirror
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
    except Exception:
        # Fallback to conservative defaults instead of blowing up importers
        from os import getenv
        try:
            system_pressure_gauge.set(float(getenv("SLOT07_PRESSURE_LEVEL", "0.3")))
        except Exception:
            system_pressure_gauge.set(0.3)
        try:
            tri_coherence_gauge.set(float(getenv("TRI_COHERENCE", "0.7")))
        except Exception:
            tri_coherence_gauge.set(0.7)


def update_tri_truth_metrics() -> None:
    """Expose canonical TRI truth signal + attestation bridge metrics."""
    try:
        from nova.orchestrator.tri_truth_bridge import get_bridge_metrics
    except Exception:
        return

    try:
        metrics = get_bridge_metrics()
    except Exception:
        return

    mirror = None
    try:
        from nova.orchestrator.semantic_mirror import get_semantic_mirror

        mirror = get_semantic_mirror()
    except Exception:
        mirror = None

    coherence = metrics.get("tri_coherence")
    if coherence is not None:
        tri_coherence_current_gauge.labels(**TRI_SIGNAL_LABELS).set(float(coherence))
        tri_coherence_current_gauge_public.labels(**TRI_SIGNAL_LABELS).set(float(coherence))

    canonical_hash = metrics.get("canonical_hash")
    if canonical_hash:
        payload = {"hash": str(canonical_hash)}
        tri_canonization_hash_info.info(payload)
        tri_canonization_hash_info_public.info(payload)

    global _last_tri_events
    attest_events = metrics.get("attest_events", 0)
    slot01_labels = _slot01_labels()
    if isinstance(attest_events, (int, float)):
        delta = float(attest_events) - float(_last_tri_events)
        if delta > 0:
            tri_to_anchor_events_counter.labels(**slot01_labels).inc(delta)
        _last_tri_events = attest_events

    avg_latency = metrics.get("attest_latency_ms_avg")
    if avg_latency is not None:
        slot01_attest_latency_gauge.labels(**slot01_labels).set(float(avg_latency))
        slot01_attest_latency_gauge_public.labels(**slot01_labels).set(float(avg_latency))

    try:
        from nova.slots.slot07_production_controls import wisdom_backpressure as wb

        tri_snapshot = wb.get_tri_signal_snapshot()
    except Exception:
        tri_snapshot = None

    if tri_snapshot:
        coherence = tri_snapshot.get("tri_coherence")
        if coherence is not None:
            slot07_tri_coherence_gauge.labels(**SLOT07_LABELS).set(float(coherence))
            slot07_tri_coherence_gauge_public.labels(**SLOT07_LABELS).set(float(coherence))
        drift = tri_snapshot.get("tri_drift_z")
        try:
            drift_val = float(drift)
            slot07_tri_drift_gauge.labels(**SLOT07_LABELS).set(drift_val)
            slot07_tri_drift_gauge_public.labels(**SLOT07_LABELS).set(drift_val)
        except (TypeError, ValueError):
            pass
        jitter = tri_snapshot.get("tri_jitter")
        try:
            jitter_val = float(jitter)
            slot07_tri_jitter_gauge.labels(**SLOT07_LABELS).set(jitter_val)
            slot07_tri_jitter_gauge_public.labels(**SLOT07_LABELS).set(jitter_val)
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
        from nova.orchestrator.adapters.slot1_truth_anchor import Slot1TruthAnchorAdapter
        adapter = Slot1TruthAnchorAdapter()

        if adapter.available:
            snapshot = adapter.snapshot()
            anchors = snapshot.get("anchors", 0)
            lookups = snapshot.get("lookups", 0)
            recoveries = snapshot.get("recoveries", 0)
            failures = snapshot.get("failures", 0)
        else:
            # Clear metrics if Slot1 not available
            anchors = lookups = recoveries = failures = 0
    except Exception:
        # Fallback - set all to 0 if Slot1 unavailable
        anchors = lookups = recoveries = failures = 0

    # Update both registries (public + internal)
    slot1_anchors_gauge.set(anchors)
    slot1_anchors_gauge_public.set(anchors)
    slot1_lookups_counter.set(lookups)
    slot1_lookups_counter_public.set(lookups)
    slot1_recoveries_counter.set(recoveries)
    slot1_recoveries_counter_public.set(recoveries)
    slot1_failures_counter.set(failures)
    slot1_failures_counter_public.set(failures)


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


# --- Phase 7.0-RC Step 5: Recording functions for RC monitoring ---

def _clamp_unit(value: float) -> float:
    """Clamp value to [0.0, 1.0] range."""
    return max(0.0, min(1.0, value))


def record_memory_resonance(stats: dict) -> None:
    """
    Record memory resonance window statistics.

    Args:
        stats: Dictionary with keys: stability, count, stdev, trend_24h
    """
    memory_stability_gauge.set(_clamp_unit(stats.get("stability", 0.5)))
    memory_samples_gauge.set(stats.get("count", 0))
    memory_volatility_gauge.set(_clamp_unit(stats.get("stdev", 0.0)))
    memory_trend_gauge.set(stats.get("trend_24h", 0.0))


def record_ris(ris_score: float, memory_stability: float, ethics_score: float) -> None:
    """
    Record RIS composite and component scores.

    Args:
        ris_score: Composite RIS (sqrt(memory × ethics))
        memory_stability: Memory stability component [0.0, 1.0]
        ethics_score: Ethics compliance component [0.0, 1.0]
    """
    ris_score_gauge.set(_clamp_unit(ris_score))
    ris_component_gauge.labels(component_type="memory_stability").set(_clamp_unit(memory_stability))
    ris_component_gauge.labels(component_type="ethics_compliance").set(_clamp_unit(ethics_score))


def record_stress_recovery(metrics: dict) -> None:
    """
    Record stress simulation results.

    Args:
        metrics: Dictionary with keys: recovery_rate, baseline_ris,
                 recovery_time_hours, max_deviation, timestamp
    """
    import time

    stress_recovery_rate_gauge.set(_clamp_unit(metrics.get("recovery_rate", 0.0)))
    stress_baseline_gauge.set(_clamp_unit(metrics.get("baseline_ris", 0.0)))
    stress_recovery_ticks_gauge.set(metrics.get("recovery_time_hours", 0))
    stress_max_deviation_gauge.set(_clamp_unit(metrics.get("max_deviation", 0.0)))
    stress_last_run_gauge.set(metrics.get("timestamp", time.time()))


def record_rc_criteria(criteria: dict) -> None:
    """
    Record RC gate pass/fail status.

    Args:
        criteria: Dictionary with keys: memory_stability_pass, ris_pass,
                  stress_recovery_pass, samples_sufficient, overall_pass
    """
    # Individual gates
    rc_gate_status_gauge.labels(gate_name="memory_stability").set(
        1.0 if criteria.get("memory_stability_pass") else 0.0
    )
    rc_gate_status_gauge.labels(gate_name="ris_score").set(
        1.0 if criteria.get("ris_pass") else 0.0
    )
    rc_gate_status_gauge.labels(gate_name="stress_recovery").set(
        1.0 if criteria.get("stress_recovery_pass") else 0.0
    )
    rc_gate_status_gauge.labels(gate_name="samples_sufficient").set(
        1.0 if criteria.get("samples_sufficient") else 0.0
    )

    # Overall
    rc_overall_pass_gauge.set(1.0 if criteria.get("overall_pass") else 0.0)


def record_csi(breakdown: dict) -> None:
    """
    Record Continuity Stability Index (CSI) and component metrics.

    Phase 8 integration - ontology lines 1024-1030

    Args:
        breakdown: Dictionary from get_csi_breakdown() with keys:
                   csi, p6_stability, p7_stability, correlation
    """
    continuity_stability_index_gauge.set(_clamp_unit(breakdown.get("csi", 0.0)))
    continuity_p6_stability_gauge.set(_clamp_unit(breakdown.get("p6_stability", 0.0)))
    continuity_p7_stability_gauge.set(_clamp_unit(breakdown.get("p7_stability", 0.0)))
    continuity_correlation_gauge.set(_clamp_unit(breakdown.get("correlation", 0.0)))


def record_urf(urf: dict) -> None:
    """
    Record Unified Risk Field (URF) metrics.

    Phase 9 integration - RRI/collapse_risk reconciliation

    Args:
        urf: Dictionary from compute_risk_alignment() with keys:
             alignment_score, risk_gap, composite_risk
    """
    risk_alignment_gauge.set(_clamp_unit(urf.get("alignment_score", 1.0)))
    risk_gap_gauge.set(_clamp_unit(urf.get("risk_gap", 0.0)))
    composite_risk_gauge.set(_clamp_unit(urf.get("composite_risk", 0.0)))


def record_mse(mse_snapshot: dict) -> None:
    """
    Record Meta-Stability Engine (MSE) metrics.

    Phase 10 integration - contracts/mse@1.yaml

    Args:
        mse_snapshot: Dictionary from get_meta_stability_snapshot() with keys:
                      meta_instability, trend, drift_velocity, sample_count
    """
    meta_instability_gauge.set(_clamp_unit(mse_snapshot.get("meta_instability", 0.0)))

    # Map trend to numeric value: stable=0.0, oscillating=1.0, runaway=2.0
    trend_map = {"stable": 0.0, "oscillating": 1.0, "runaway": 2.0}
    trend = mse_snapshot.get("trend", "stable")
    mse_trend_gauge.set(trend_map.get(trend, 0.0))

    mse_drift_velocity_gauge.set(mse_snapshot.get("drift_velocity", 0.0))
    mse_sample_count_gauge.set(float(mse_snapshot.get("sample_count", 0)))


def record_orp(orp_snapshot: dict, transition_from: str | None = None) -> None:
    """
    Record Operational Regime Policy (ORP) metrics.

    Phase 11 integration - contracts/orp@1.yaml

    Args:
        orp_snapshot: Dictionary from get_operational_regime() with keys:
                      regime, regime_score, posture_adjustments, transition_from
        transition_from: Optional previous regime for transition counter
    """
    # Map regime to numeric value
    regime_map = {
        "normal": 0.0,
        "heightened": 1.0,
        "controlled_degradation": 2.0,
        "emergency_stabilization": 3.0,
        "recovery": 4.0,
    }
    regime = orp_snapshot.get("regime", "normal")
    orp_regime_gauge.set(regime_map.get(regime, 0.0))

    orp_regime_score_gauge.set(_clamp_unit(orp_snapshot.get("regime_score", 0.0)))

    # Extract posture adjustments
    posture = orp_snapshot.get("posture_adjustments", {})
    orp_threshold_multiplier_gauge.set(_clamp_unit(posture.get("threshold_multiplier", 1.0)))
    orp_traffic_limit_gauge.set(_clamp_unit(posture.get("traffic_limit", 1.0)))
    orp_deployment_freeze_gauge.set(1.0 if posture.get("deployment_freeze", False) else 0.0)
    orp_safe_mode_forced_gauge.set(1.0 if posture.get("safe_mode_forced", False) else 0.0)

    # Record regime transition if occurred
    trans_from = transition_from or orp_snapshot.get("transition_from")
    if trans_from is not None:
        orp_regime_transitions_counter.labels(from_regime=trans_from, to_regime=regime).inc()


def _refresh_metrics() -> None:
    update_slot6_metrics()
    update_flag_metrics()
    update_slot1_metrics()
    update_lightclock_metrics()
    update_system_health_metrics()
    update_tri_truth_metrics()
    update_semantic_mirror_metrics()
    update_secrets_baseline_metrics()


def record_router_decision(decision) -> None:
    """Record router decisions for observability feeds."""
    # Import lazily to avoid circular dependencies when metrics module loads
    route = getattr(decision, "route", "unknown")
    router_route_selected_gauge_public.labels(route=route).set(1)

    constraint_allowed = getattr(decision.constraints, "allowed", False)
    result_label = "allow" if constraint_allowed else "deny"
    router_constraint_counter_public.labels(result=result_label).inc()

    try:
        info_payload = {
            "allowed": str(constraint_allowed),
            "reasons": ",".join(decision.constraints.reasons),
        }
        router_constraint_snapshot_info.info(info_payload)
    except Exception:
        pass

    try:
        router_policy_info.info(
            {
                "route": decision.policy.route,
                "score": f"{decision.policy.score:.3f}",
            }
        )
    except Exception:
        pass

    advisors = getattr(decision, "advisors", {}) or {}
    slot05 = advisors.get("slot05")
    slot08 = advisors.get("slot08")

    if slot05 is not None:
        router_advisor_slot05_gauge.set(float(slot05.score))
    if slot08 is not None:
        router_advisor_slot08_gauge.set(float(slot08.score))

    router_final_score_gauge.set(float(decision.final_score))


def _generate_payload_for_registry(registry):
    payload = generate_latest(registry)
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


def get_metrics_response():
    """Get sanitized Prometheus metrics response."""
    _refresh_metrics()
    return _generate_payload_for_registry(_PUBLIC_REGISTRY)


def get_internal_metrics_response():
    """Get internal Prometheus metrics response."""
    _refresh_metrics()
    return _generate_payload_for_registry(_INTERNAL_REGISTRY)


def get_temporal_metrics_response():
    """Public-safe temporal metrics (Phase-6)."""
    _refresh_metrics()
    return _generate_payload_for_registry(_PUBLIC_REGISTRY)


def get_predictive_metrics_response():
    """Predictive metrics response (Phase-7)."""
    _refresh_metrics()
    return _generate_payload_for_registry(_INTERNAL_REGISTRY)


def _clamp_unit(value: float) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


def record_predictive_physics(snapshot) -> None:
    """Record predictive physics metrics from the trajectory engine."""
    if snapshot is None:
        return
    data = snapshot.to_dict() if hasattr(snapshot, "to_dict") else dict(snapshot)
    collapse = _clamp_unit(data.get("collapse_risk", data.get("predictive_collapse_risk", 0.0)))
    predictive_collapse_risk_gauge.set(collapse)

    try:
        accel = abs(float(data.get("drift_acceleration", 0.0)))
    except (TypeError, ValueError):
        accel = 0.0
    predictive_acceleration_gauge.set(accel)

    safe = bool(data.get("safe_corridor", data.get("predictive_safe_corridor", False)))
    safe_value = 1.0 if safe else 0.0
    predictive_safe_corridor_gauge.set(safe_value)
    predictive_safe_corridor_public_gauge.set(safe_value)


def record_predictive_penalty(penalty: float) -> None:
    """Record predictive routing penalties."""
    predictive_penalty_gauge.set(_clamp_unit(penalty))


def record_predictive_warning(reason: Optional[str] = None) -> None:
    """Increment predictive warning counter."""
    label = reason or "unknown"
    predictive_warning_counter.labels(reason=label).inc()


def record_consistency_gap(gap_profile: dict) -> None:
    """
    Record multi-slot consistency gap metrics (Step 6).

    Args:
        gap_profile: ConsistencyProfile.to_dict() output
    """
    consistency_gap_gauge.set(_clamp_unit(gap_profile.get("score", 0.0)))
    consistency_severity_gauge.set(_clamp_unit(gap_profile.get("severity", 0.0)))

    components = gap_profile.get("components", {})
    consistency_safety_prod_gauge.set(_clamp_unit(components.get("safety_production_conflict", 0.0)))
    consistency_culture_deploy_gauge.set(_clamp_unit(components.get("culture_deployment_conflict", 0.0)))
    consistency_prod_predictive_gauge.set(_clamp_unit(components.get("production_predictive_conflict", 0.0)))


def record_memory_stability(stability_score: float) -> None:
    """
    Record memory stability from 7-day rolling TRSI window (Phase 7.0-RC).

    Args:
        stability_score: Memory stability score [0.0, 1.0] from MemoryResonanceWindow
    """
    memory_stability_gauge.set(_clamp_unit(stability_score))


def record_ris_score(ris: float) -> None:
    """
    Record Resonance Integrity Score (RIS) for RC attestation (Phase 7.0-RC).

    Args:
        ris: RIS score [0.0, 1.0] computed as sqrt(M_s × E_c)
    """
    ris_score_gauge.set(_clamp_unit(ris))


def record_stress_injection(mode: str, active: bool) -> None:
    """
    Record stress injection state (Phase 7.0-RC stress simulation).

    Args:
        mode: Stress mode ("drift", "jitter", "combined")
        active: Whether injection is currently active
    """
    stress_injection_active_gauge.set(1.0 if active else 0.0)
    if active:
        stress_injection_counter.labels(mode=mode).inc()
