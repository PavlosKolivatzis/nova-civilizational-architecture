# Semantic Mirror Access Control List (ACL) Reference

## Principles

The Semantic Mirror implements a **deny-by-default** security model with explicit access control:

- **Read-Only**: Consumers can query context but never mutate it
- **Self-Read Always**: Publishers can always read back their own published contexts
- **Scope-Based Access**:
  - `PRIVATE`: Publisher-only access (no other slots can read)
  - `INTERNAL`: Deny-by-default; requires explicit ACL entry
  - `PUBLIC`: All consumers can read (use sparingly)
- **Explicit Allow-Lists**: INTERNAL contexts require explicit reader permissions

## Canonical Context Keys

| Context Key | Scope | Allowed Readers | Purpose |
|-------------|-------|-----------------|---------|
| `slot07.breaker_state` | INTERNAL | `slot06_cultural_synthesis`, `slot03_emotional_matrix` | Circuit breaker status for system pressure awareness |
| `slot07.pressure_level` | INTERNAL | `slot06_cultural_synthesis`, `slot03_emotional_matrix` | System pressure (0.0-1.0) for load adaptation |
| `slot07.resource_status` | INTERNAL | `slot06_cultural_synthesis` | Resource utilization and active request metrics |
| `slot07.public_metrics` | INTERNAL | `slot06_cultural_synthesis` | Non-sensitive production metrics for testing |
| `slot06.cultural_profile` | INTERNAL | `slot03_emotional_matrix`, `slot07_production_controls` | Cultural synthesis patterns and complexity factors |
| `slot06.adaptation_rate` | INTERNAL | `slot03_emotional_matrix`, `slot07_production_controls` | Rate of cultural adaptation (0.0-1.0) |
| `slot06.synthesis_results` | INTERNAL | `slot07_production_controls` | Synthesis output summaries for testing |

## Extending ACLs Safely

**✅ Preferred**: Use `add_access_rules()` to merge new permissions without replacing defaults:

```python
from orchestrator.semantic_mirror import get_semantic_mirror

mirror = get_semantic_mirror()

# Add new context permissions (preserves existing ACLs)
mirror.add_access_rules({
    "slot08.new_context": ["slot06_cultural_synthesis", "slot07_production_controls"],
    "slot07.debug_metrics": ["slot06_cultural_synthesis"]  # Extends existing slot07 ACLs
})
```

**⚠️ Avoid**: Using `configure_access_rules()` which replaces the entire ACL table:

```python
# DON'T DO THIS - nukes existing defaults
mirror.configure_access_rules({
    "slot08.new_context": ["slot06_cultural_synthesis"]  # Loses all other ACLs!
})
```

## Key Validation

Context keys must follow the pattern `slot_name.context_type` where:
- `slot_name`: Valid Python identifier (e.g., `slot07_production_controls`)
- `context_type`: Alphanumeric with underscores (e.g., `breaker_state`, `public_metrics`)

## Security Notes

- **Rate Limiting**: 1000 queries/minute per slot to prevent abuse
- **TTL Expiration**: All contexts have time-to-live limits (typically 30-300 seconds)
- **Access Logging**: All queries are logged for security audit
- **Thread Safety**: Concurrent access from multiple slots is fully supported