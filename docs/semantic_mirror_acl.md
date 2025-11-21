# Semantic Mirror ACL Registry

## Active Context Keys

| Key | Publisher | Allowed Readers | Default TTL | Description |
|-----|-----------|----------------|-------------|-------------|
| `slot07.breaker_state` | slot07_production_controls | slot06_cultural_synthesis | 300s | Circuit breaker state |
| `slot07.pressure_level` | slot07_production_controls | slot06_cultural_synthesis | 180s | System pressure metric |
| `slot07.resource_status` | slot07_production_controls | slot06_cultural_synthesis | 240s | Resource availability |
| `slot07.heartbeat` | slot07_production_controls | * | 120s | Keepalive signal |
| `slot07.cutover_tick` | slot07_production_controls | * | 120s | Deployment marker |
| `slot07.health_summary` | slot07_production_controls | slot06_cultural_synthesis, slot03_emotional_matrix | 180s | S7 → consumers |
| `slot07.public_metrics` | slot07_production_controls | slot06_cultural_synthesis | 180s | S7 → S6 |
| `slot06.synthesis_results` | slot06_cultural_synthesis | slot07_production_controls | 240s | S6 → S7 |
| `slot06.cultural_profile` | slot06_cultural_synthesis | * | 240s | Cultural analysis output |
| `slot03.confidence_level` | slot03_emotional_matrix | * | 180s | Emotional confidence metric |
| `slot03.emotional_state` | slot03_emotional_matrix | * | 180s | Current emotional state |
| `slot06.adaptation_rate` | slot06_cultural_synthesis | * | 240s | Synthesis adaptation rate |
| `slot06.synthesis_complexity` | slot06_cultural_synthesis | * | 240s | Complexity metric |
| `slot07.context_published` | slot07_production_controls | * | 180s | Context publication event |
| `slot07.internal_state` | slot07_production_controls | * | 180s | Internal state snapshot |
| `slot10.deployer` | slot10_deployment_model | * | 300s | Deployment configuration |
| `slot05.adaptation_event` | slot05_constellation_navigation | * | 300s | Adaptive threshold changes |
| `slot05.constellation_mapped` | slot05_constellation_navigation | * | 600s | Constellation mapping results |

## Router Context Keys

| Key | Publisher | Allowed Readers | Default TTL | Description |
|-----|-----------|----------------|-------------|-------------|
| `router.constraint_snapshot` | Epistemic Router | slot07_production_controls, slot10_civilizational_deployment, governance | 180s | Latest deterministic constraint evaluation |
| `router.anr_policy` | Epistemic Router | slot07_production_controls, slot10_civilizational_deployment, governance | 180s | Static policy outcome used for routing |
| `router.final_route` | Epistemic Router | slot07_production_controls, slot10_civilizational_deployment, governance | 120s | Published route + final scoring metadata |

## Governance Context Keys

| Key | Publisher | Allowed Readers | Default TTL | Description |
|-----|-----------|----------------|-------------|-------------|
| `governance.snapshot` | Governance Engine | * | 300s | Canonical governance state snapshot |
| `governance.ethics` | Governance Engine | * | 300s | Per-rule ethical evaluation results |
| `governance.policy_scores` | Governance Engine | * | 300s | Aggregated governance metrics |
| `governance.final_decision` | Governance Engine | * | 300s | Final governance verdict with metadata |
| `governance.trajectory_warning` | Governance Engine | * | 180s | Predictive warning metadata when foresight triggers |

## Temporal Context Keys

| Key | Publisher | Allowed Readers | Default TTL | Description |
|-----|-----------|----------------|-------------|-------------|
| `temporal.snapshot` | Temporal Engine | router, governance, slot07_production_controls, slot10_civilizational_deployment, temporal_api | 300s | Latest temporal drift/variance snapshot |
| `temporal.ledger_head` | Temporal Engine | governance, slot10_civilizational_deployment, temporal_api | 300s | Serialized ledger head for audit |
| `temporal.router_modifiers` | Epistemic Router | governance, slot07_production_controls, slot10_civilizational_deployment | 180s | Temporal penalties/allowances applied to routing |
| `predictive.prediction_snapshot` | Predictive Trajectory Engine | governance, router, slot07_production_controls, slot10_civilizational_deployment | 180s | Forward-projected temporal snapshot (velocity/acceleration/risks) |
| `predictive.ledger_head` | Predictive Trajectory Engine | governance, router | 300s | Latest foresight ledger entry (hash chained) |

### Test-only keys (ignored by linter)
- slot07.test_data
- slot07.rate_test
- slot07.test


## Maintenance Notes

- Update this table when adding new context keys
- ACL linter validates keys against this registry
- Unknown keys in code → linter failure
- Unused documented keys → linter warning
