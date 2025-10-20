# Continuity Engine – Ops Runbook (Phase 8.0)

## When CSI < 0.75 (2h sustained)
1. Confirm sealed Phase 7.0 hash passed in the last daily run.
2. Check Grafana "CSI Trend" panel for phase/environment scope.
3. If EHS ≥ 0.80 and anomaly_precision ≥ 0.85 → raise WARN; else CRITICAL.
4. Create incident note in `ops/logs/INC-<date>.md` with links to:
   - Daily attestation (`attest/latest_phase_8.0_alpha.json`)
   - Alert firing interval (Prometheus query)
   - Last 24h continuity JSONL (`ops/logs/continuity_validation_*.jsonl`)
5. Assign owner; track until CSI ≥ 0.75 for 6h continuous.

## When Regeneration < 0.90 (1h sustained)
1. Freeze new attestations (append allowed; no chain updates).
2. Run lineage probe; identify break positions in continuity chain.
3. Attempt regeneration using redundant snapshot set.
4. Record success/failure in `ops/logs/regeneration_attempt_<timestamp>.json`.
5. If regeneration fails → escalate to continuity council for manual intervention.

## When EHS < 0.80 (6h sustained)
1. Verify ethics config checksum against last known good state.
2. Roll back to last attested ethics configuration.
3. Document delta and root cause in `ops/logs/ethics_audit_<date>.md`.
4. Schedule ethics board review within 24h.

## When Anomaly Precision < 0.85 (24h sustained)
1. Review last 7 days of anomaly detection logs.
2. Check for false positive/negative patterns in `ops/logs/anomaly_analysis_*.jsonl`.
3. Adjust detection thresholds if needed (document in `docs/analysis/anomaly-thresholds.md`).
4. Retrain anomaly model on updated dataset.

## When Continuity Chain Breaks > 0 (immediate)
1. Halt all continuity operations.
2. Isolate affected chain segments.
3. Attempt automated repair using continuity ledger v2.
4. If repair fails, declare continuity emergency and notify all stakeholders.

## General Continuity Maintenance
- **Daily Checks**: Verify attestation schema compliance and hash integrity.
- **Weekly Reviews**: Analyze CSI/EHS trends and anomaly performance.
- **Monthly Audits**: Full continuity chain verification and ethics compliance review.
- **Emergency Contacts**: Continuity council (escalation path documented in `ops/contacts.md`).

## Rollback Procedures
- **Single Component**: Revert to last known good commit for affected module.
- **Full Continuity**: Restore from last successful chain snapshot.
- **Emergency**: Complete rollback to Phase 7.0-gold state.

## Monitoring Dashboards
- **Primary**: `ops/grafana/dashboards/continuity_engine.json`
- **Alerts**: Prometheus Alertmanager with runbook links
- **Logs**: Structured JSONL in `ops/logs/` with automated rotation

## Communication Protocol
- **Incidents**: Create GitHub issue with `continuity-incident` label
- **Updates**: Daily standup updates in continuity channel
- **Escalations**: Immediate notification to continuity council

---
*This runbook ensures the Continuity Engine maintains civilizational-scale temporal coherence with cryptographic integrity and ethical boundaries.*