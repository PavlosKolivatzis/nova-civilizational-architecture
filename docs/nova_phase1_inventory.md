# Nova Phase 1 Inventory – A/B/C/D Classification (Read-only)

**Status:** Phase 1 (CT-scan only – no edits, moves, or deletions)  
**Scope:** docs/specs/, docs/architecture/, src/nova/, scripts/  
**Classes:**  
- A – Constitutional / Active (invariants, ontology, jurisdiction, refusal, live runtime logic)  
- B – Reference / Evidence (RT logs, calibration, analyses, design specs)  
- C – Experimental / Prototypal (drafts, spikes, exploratory tools)  
- D – Obsolete / Unknown (dead/superseded/unclear; marked only, not removed)

> This file classifies artifacts structurally. It does **not** judge quality, correctness, or usefulness.

---

## docs/specs/

```markdown
| Path                                         | Class | Rationale                                                |
|----------------------------------------------|-------|----------------------------------------------------------|
| docs/specs/flow_mesh_overview.md            | B     | High-level flow/mesh overview (reference architecture). |
| docs/specs/nova_constitutional_freeze.md    | A     | Constitutional freeze declaration for core domains.     |
| docs/specs/nova_jurisdiction_map.md         | A     | Defines O/R/F jurisdictions and negative space.         |
| docs/specs/nova_system_context_overview.md  | B     | System context overview (reference, non-constitutional).|
| docs/specs/parser_improvement_scope.md      | C     | Parser improvement scope (future work / exploratory).   |
| docs/specs/phase14_5_closeout.md            | B     | Phase 14.5 closeout summary (historical reference).     |
| docs/specs/phase14_5_observation_protocol.md| B     | Observation protocol spec (reference, completed phase). |
| docs/specs/phase14_5_pilot_findings.md      | B     | Pilot findings analysis (evidence / reference).         |
| docs/specs/phase14_5_temporal_usm_spec.md   | B     | Temporal USM spec (reference for Slot02 implementation).|
| docs/specs/phase14_6_activation_criteria.md | B     | Activation criteria (design reference, Phase 14.6).     |
| docs/specs/phase14_6_temporal_governance.md | B     | Temporal governance design (design-only, Phase 14.6).   |
| docs/specs/phase14_7_parser_exploration.md  | C     | Parser exploration (experimental / exploratory).        |
| docs/specs/phase14_extraction_calibration.md| B     | Extraction calibration spec (reference/evidence).       |
| docs/specs/phase14_min_turns_calibration.md | B     | min_turns calibration record (reference/evidence).      |
| docs/specs/phase14_retrospective.md         | B     | Phase 14 retrospective (historical analysis).           |
| docs/specs/phase14_rt_evidence_log.md       | B     | RT-00X evidence log (calibration evidence).             |
| docs/specs/phase15_closure_note.md          | B     | Phase 15 closure note (reference, design closed).       |
| docs/specs/phase15_governance_design.md     | B     | Slot07 governance design (design-only, reference).      |
| docs/specs/phase15_temporal_governance_readiness.md | B | Phase 15 readiness checklist (reference).          |
| docs/specs/phase16_agency_pressure_design.md| B     | Phase 16 A_p design (design-only, non-operational).     |
| docs/specs/phase16_agency_pressure_evidence.md| B    | Phase 16 agency pressure evidence slice (calibration).  |
| docs/specs/phase16_alpha_calibration_protocol.md| A  | Phase 16.α calibration protocol (constitutional).       |
| docs/specs/phase16_alpha_calibration_workbook.md | A | Phase 16.α human workbook template (constitutional tool).|
| docs/specs/phase17_consent_gate_design.md   | B     | Phase 17 consent gate design (design-only reference).   |
| docs/specs/phase18_slot02_manipulation_gate_design.md| B| Phase 18 Slot02 manipulation gate design (reference).|
| docs/specs/refusal_event_contract.md        | A     | Refusal event schema (constitutional refusal semantics).|
| docs/specs/refusal_event_exemplars.md       | A     | Concrete refusal records (constitutional exemplars).    |
| docs/specs/slot_cross_dependencies.md       | B     | Slot cross-dependency mapping (reference architecture). |
| docs/specs/slot02_usm_bias_detection_spec.md| B     | Slot02 USM bias detection spec (runtime reference).     |
| docs/specs/slot07_temporal_governance_14_6_spec.md| B | Slot07 temporal governance spec (design reference). |
```

---

## docs/architecture/ and docs/architecture/ontology/

```markdown
| Path                                                   | Class | Rationale                                                    |
|--------------------------------------------------------|-------|--------------------------------------------------------------|
| docs/architecture/ADR-014-soft-extraction-calibration.md | B   | ADR for soft extraction calibration (reference decision).    |
| docs/architecture/ADR-017-context-aware-routing.md     | B     | ADR for context-aware routing (reference decision).         |
| docs/architecture/anr-slot-interaction-matrix.md       | B     | Slot interaction matrix (reference architecture).           |
| docs/architecture/context_routing_rule.md              | B     | Context routing rule doc (reference architecture).          |
| docs/architecture/Flow_Fabric_Phase2.md                | B     | Flow Fabric Phase 2 design (reference).                     |
| docs/architecture/Flow_Fabric_Phase3.md                | B     | Flow Fabric Phase 3 design (reference).                     |
| docs/architecture/phase13b-temporal-snapshot-integration.md | B | Phase 13b temporal snapshot spec (reference).           |
| docs/architecture/prometheus_split_plan.md             | B     | Prometheus split plan (ops/architecture reference).         |
| docs/architecture/SYSTEM_ARCHITECTURE.md               | B     | Global system architecture overview (reference).            |
| docs/architecture/ontology/_canon.yaml                 | A     | Canonical ontology index (Mother ontology meta).            |
| docs/architecture/ontology/specs/nova_framework_ontology.v1.yaml | A | Core framework ontology (Mother ontology).         |
| docs/architecture/ontology/specs/nova.operating@1.0.yaml| A    | Operating ontology spec (active core contract).             |
| docs/architecture/ontology/specs/nova.slot03@1.0.yaml  | A     | Slot03 ontology spec (core contract).                       |
| docs/architecture/ontology/specs/nova.slot07@1.0.yaml  | A     | Slot07 ontology spec (core contract).                       |
| docs/architecture/ontology/specs/nova.slot09@1.0.yaml  | A     | Slot09 ontology spec (core contract).                       |
| docs/architecture/ontology/specs/slot01_root_mode_api.v1.yaml | A | Slot01 root mode API spec (core contract).          |
```

---

## src/nova/ (overview level)

```markdown
| Path             | Class | Rationale                                                      |
|------------------|-------|----------------------------------------------------------------|
| src/nova/**      | A     | All Nova runtime modules (slots, orchestrator, math, metrics, ontology integration) – active runtime logic. |
```

> Detailed per-file classification for `src/nova/` can be added later if needed; for Phase 1, the entire tree is treated as active runtime logic (Class A).

---

## scripts/

```markdown
| Path                                      | Class | Rationale                                                   |
|-------------------------------------------|-------|-------------------------------------------------------------|
| scripts/capture_reflection_v10.ps1        | C     | Reflection capture script (experimental / ops helper).      |
| scripts/capture_reflection_v10.sh         | C     | Reflection capture script (experimental / ops helper).      |
| scripts/check_merge_integrity.py          | B     | Merge integrity checker (operational tool, reference).      |
| scripts/comprehensive_health_check.py     | B     | Health check tool (ops/diagnostic script).                  |
| scripts/contract_audit.py                 | B     | Contract audit script (ops/diagnostic, non-runtime core).   |
| scripts/diagnose_creativity_reflect.py    | C     | Creativity diagnosis helper (experimental tooling).         |
| scripts/export_conversation_stream.py     | B     | Conversation export tool (evidence/export helper).          |
| scripts/export_manifest.py                | B     | Manifest export tool (ops).                                 |
| scripts/extractive_session_runner.py      | C     | Extractive stimulus generator (Phase 16 evidence, experimental). |
| scripts/find_conversation_by_text.py      | B     | Text-based conversation finder (ops/evidence helper).       |
| scripts/generate_arc_test_domains.py      | C     | ARC domain generator (test/evidence helper, experimental).  |
| scripts/generate_rc_attestation.py        | B     | RC attestation generator (ops).                             |
| scripts/health_verification.py            | B     | Health verification script (ops).                           |
| scripts/journal_reflection.py             | C     | Journal reflection helper (experimental, non-core).         |
| scripts/launch_soak.ps1                   | C     | Soak test launcher (experimental load testing).             |
| scripts/ledger_checkpoint.py              | B     | Ledger checkpoint management (ops).                         |
| scripts/ledger_migrate.py                 | B     | Ledger migration tool (ops).                                |
| scripts/local_health_check.sh             | B     | Local health check script (ops).                            |
| scripts/nova_reality_capture.py           | B     | Reality capture monitor (observability/evidence tool).      |
| scripts/phase14_5_pilot_observation.py    | B     | Phase 14.5 pilot observation harness (reference/evidence).  |
| scripts/plot_wisdom_ab_runs.py            | B     | Plotting tool for wisdom A/B runs (analysis).               |
| scripts/publish_to_zenodo.py              | B     | Publication helper (ops).                                   |
| scripts/query_rc_attestations.py          | B     | RC attestation query tool (ops).                            |
| scripts/replay_stream_slot02.py           | B     | Slot02 replay harness (diagnostic/evidence).                |
| scripts/replay_stream_with_classification.py | B  | Replay + classification harness (diagnostic/evidence).      |
| scripts/run_orchestrator_dev.ps1          | B     | Dev orchestrator launcher (ops, not core logic).            |
| scripts/run_orchestrator_dev.sh           | B     | Dev orchestrator launcher (ops).                            |
| scripts/run_phase14_deployment_validation.py | B | Phase 14 deployment validation harness (diagnostic).        |
| scripts/run_soak.sh                       | C     | Soak test runner (experimental load testing).               |
| scripts/run_weekly_chaos.cmd              | C     | Chaos experiment scheduler (experimental).                  |
| scripts/sanity_check.py                   | B     | Sanity check tool (basic checks, ops).                      |
| scripts/semantic_mirror_dashboard.py      | C     | Semantic mirror dashboard (experimental/ops UI).            |
| scripts/semantic_mirror_flip.py           | C     | Semantic mirror flip experiment (experimental).             |
| scripts/semantic_mirror_loadgen.py        | C     | Load generation for semantic mirror (experimental).         |
| scripts/semantic_mirror_quick_asserts.py  | B     | Quick assertions for semantic mirror (diagnostic).          |
| scripts/setup_bookmarks.py                | B     | Bookmark setup helper (ops).                                |
| scripts/simulate_extraction_dynamics_shield.py | C | Simulation script (experimental).                       |
| scripts/simulate_extraction_dynamics.py   | C     | Simulation script (experimental).                           |
| scripts/simulate_federated_ethics.py      | C     | Simulation script (experimental ethics).                    |
| scripts/simulate_nova_cycle.py            | C     | Full-cycle simulation (experimental scenario).              |
| scripts/slot_registry_check.py            | B     | Slot registry integrity check (ops).                        |
| scripts/slot10_weekly_chaos.py            | C     | Weekly chaos experiment (experimental).                     |
| scripts/slot8_chaos_simple.py             | C     | Slot8 chaos experiment (experimental).                      |
| scripts/slot8_corruption_replay.py        | C     | Corruption replay experiment (experimental).                |
| scripts/soak_ab_wisdom_governor.py        | C     | Wisdom governor A/B soak test (experimental).              |
| scripts/start_server_test.ps1             | C     | Server startup test (experimental/ops).                     |
| scripts/summarize_wisdom_ab_runs.py       | B     | Summary generator for wisdom A/B runs (analysis).           |
| scripts/test_phase14_temporal_metrics.py  | B     | Test harness for temporal metrics (diagnostic/evidence).    |
| scripts/validate_attestations.py          | B     | Attestation validation script (ops).                        |
| scripts/validate_avl_e2e.py               | B     | AVL end-to-end validation (ops).                            |
| scripts/validate_ontology_structure.py    | A     | Ontology structure validator (enforces core contracts).     |
| scripts/validate_ontology.py              | A     | Ontology validator (enforces core contracts).               |
| scripts/validate_phase_7_beta.py          | B     | Phase 7 validation (historical diagnostic).                 |
| scripts/validate_rc_e2e.py                | B     | RC end-to-end validation (ops).                             |
| scripts/validate-schemas.py               | B     | Schema validation tool (ops).                               |
| scripts/verify_pilot_ready.py             | B     | Pilot readiness check (ops).                                |
| scripts/verify_vault.py                   | B     | Vault verification tool (ops).                              |
| scripts/watch_gstar.sh                    | C     | Monitoring helper (experimental/ops).                       |
| scripts/workload_loop.sh                  | C     | Workload loop helper (experimental/ops).                    |
```

---

## Notes

- This inventory is descriptive only. It does **not** imply any deletion, movement, or prioritisation.  
- Any future clean-up or consolidation must re-check against:
  - `docs/specs/nova_constitutional_freeze.md`
  - `docs/specs/nova_jurisdiction_map.md`
  - `docs/specs/refusal_event_contract.md`
  - `docs/CONTRIBUTING_CONSTITUTIONAL_CHECK.md`

