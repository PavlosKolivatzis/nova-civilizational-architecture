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

### Test-only keys (ignored by linter)
- slot07.test_data
- slot07.rate_test
- slot07.test


## Maintenance Notes

- Update this table when adding new context keys
- ACL linter validates keys against this registry
- Unknown keys in code → linter failure
- Unused documented keys → linter warning