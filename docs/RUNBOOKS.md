# NOVA Production Runbooks

## Contract Schema Validation

### If contract CI fails (schema drift)

1. **Read CI log** → identify which schema failed validation
2. **If change was intended:**
   - Bump `schema_version` field in the schema
   - Add `CONTRACT:BUMP` tag to PR description
   - Explain breaking change rationale in PR
3. **If change was accidental:**
   - Revert the schema change
   - Re-run CI to confirm green status

### If runtime validation fails (health/profile)

**Slot 3 Health Endpoint:**
```bash
# Get current health payload
curl -s http://localhost:8000/health | jq .

# Validate against schema
python -c "
import json, urllib.request, jsonschema, pathlib
schema = json.loads(pathlib.Path('contracts/slot3_health_schema.json').read_text())
data = json.loads(urllib.request.urlopen('http://localhost:8000/health').read())
jsonschema.validate(data, schema)
print('Health payload validates ✓')
"
```

**Debugging Steps:**
- Check feature flags that influence payload shape (e.g., `SLOT3_ESCALATION_ENABLED`)
- Verify all required fields are present in response
- Check for unexpected extra fields if `additionalProperties: false`

## Local Validation Commands

### Validate All Schemas
```bash
python - <<'PY'
import json, pathlib
from jsonschema import Draft7Validator
for p in ["contracts/slot3_health_schema.json","contracts/slot6_cultural_profile_schema.json"]:
    s = json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
    Draft7Validator.check_schema(s)
    print("OK:", p)
PY
```

### Quick Health Endpoint Smoke Test
```bash
python - <<'PY'
import json, urllib.request, jsonschema, pathlib
schema = json.loads(pathlib.Path("contracts/slot3_health_schema.json").read_text())
data = json.loads(urllib.request.urlopen("http://localhost:8000/health").read())
jsonschema.validate(data, schema)
print("health ✓")
PY
```

### Run Contract Test Suite
```bash
# Contract tests only (fast)
python -m pytest -q tests/contracts/

# All contract tests with verbose output
python -m pytest -v tests/contracts/
```

## Schema Governance

### Adding New Protected Schemas

1. Create schema in `contracts/[name]_schema.json`
2. Add contract test in `tests/contracts/test_[name]_contract.py`
3. Update `.github/workflows/contracts-freeze.yml` to include new schema
4. Document in `docs/ARCHITECTURE.md` under "Protected Schemas"

### Schema Versioning Policy

- **Breaking changes:** Require `schema_version` bump + `CONTRACT:BUMP` PR tag
- **Compatible changes:** Require `CONTRACT:EXPLAIN` PR tag
- **All changes:** Must pass CI contract tests + CODEOWNERS review

## Emergency Procedures

### Immediate Schema Revert
```bash
# If schema change breaks production
git revert [bad-commit-sha]
git push origin main
git tag v6.7.1-hotfix -m "Emergency revert of schema change"
git push origin v6.7.1-hotfix
```

### Bypass Freeze Gate (Emergency Only)
Add this exact text to PR description:
```
EMERGENCY BYPASS: Production critical fix
CONTRACT:EMERGENCY - [explain situation]
```
(Note: Update contracts-freeze.yml to recognize EMERGENCY tag if needed)