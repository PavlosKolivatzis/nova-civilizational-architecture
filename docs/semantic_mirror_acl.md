# Semantic Mirror ACL Registry

## Active Context Keys

| Key | Publisher | Allowed Readers | Default TTL | Description |
|-----|-----------|----------------|-------------|-------------|
| `slot07.breaker_state` | slot07_production_controls | slot06_cultural_synthesis | 300s | Circuit breaker state |
| `slot07.pressure_level` | slot07_production_controls | slot06_cultural_synthesis | 180s | System pressure metric |
| `slot07.resource_status` | slot07_production_controls | slot06_cultural_synthesis | 240s | Resource availability |
| `slot07.heartbeat` | slot07_production_controls | * | 120s | Keepalive signal |
| `slot07.cutover_tick` | slot07_production_controls | * | 120s | Deployment marker |

## Maintenance Notes

- Update this table when adding new context keys
- ACL linter validates keys against this registry
- Unknown keys in code → linter failure
- Unused documented keys → linter warning
