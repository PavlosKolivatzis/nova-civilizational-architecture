# Nova Configuration Inventory (Phase 2.1)

**Audit Date**: 2025-11-13
**Total Flags Found**: 162
**Documented Flags**: 167
**Undocumented Flags**: 0

---

## Summary Statistics

- **Total unique NOVA_* variables**: 162
- **Documented in README/docs**: 167
- **Undocumented**: 0
- **Total usage locations**: 600

---

## Detailed Inventory

| Flag | Default | Impact | Files | Documented? |
|------|---------|--------|-------|-------------|
| `NOVA_ADAPTIVE_CONNECTIONS_ENABLED` | `false` | 🟡 HIGH (Feature Gate) | 3 | ✅ |
| `NOVA_ALLOW_EXPIRE_TEST` | `1` | 🟡 HIGH (Feature Gate) | 1 | ✅ |
| `NOVA_ANCHOR_VALIDATION_MODE` | `STRICT` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_ANR_ALPHA` | `0.8` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_ANR_ENABLED` | `0` | 🟡 HIGH (Feature Gate) | 2 | ✅ |
| `NOVA_ANR_EPSILON` | `0.05` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_ANR_KILL` | `0` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_ANR_LEARN_SHADOW` | `0` | 🟢 LOW (Limited Scope) | 2 | ✅ |
| `NOVA_ANR_MAX_FAST_PROB` | `0.15` | 🟡 MEDIUM (Performance) | 1 | ✅ |
| `NOVA_ANR_PILOT` | `0.0` | 🟢 LOW (Limited Scope) | 2 | ✅ |
| `NOVA_ANR_RIDGE` | `0.01` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_ANR_SHADOW_SAMPLE` | `1.0` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_ANR_STATE_PATH` | `NO_DEFAULT` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_ANR_STRICT_ON_ANOMALY` | `0` | 🟢 LOW (Limited Scope) | 2 | ✅ |
| `NOVA_ARC_ENABLED` | `0` | 🟡 HIGH (Feature Gate) | 1 | ✅ |
| `NOVA_ARC_SAMPLE` | `0.10` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_BUILD_SHA` | `unknown` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_CREATIVITY_BNB` | `0` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_CREATIVITY_BNB_MARGIN` | `0.05` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_CREATIVITY_BNB_Q` | `0.40` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_CREATIVITY_DEBUG` | `0` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_CREATIVITY_EARLY_STOP` | `0` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_CREATIVITY_EARLY_STOP_IG` | `0.03` | 🟡 MEDIUM (Performance) | 1 | ✅ |
| `NOVA_CREATIVITY_EARLY_STOP_SCORE` | `0.62` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_CREATIVITY_ENTROPY_DELTA_STALL` | `0.01` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_CREATIVITY_ENTROPY_MAX` | `2.8` | 🟡 MEDIUM (Performance) | 1 | ✅ |
| `NOVA_CREATIVITY_ENTROPY_MIN` | `1.2` | 🟡 MEDIUM (Performance) | 1 | ✅ |
| `NOVA_CREATIVITY_EWMA_ALPHA` | `0.01` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_CREATIVITY_INFO_GAIN_EPS` | `0.02` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_CREATIVITY_MAX_BRANCHES` | `6` | 🟡 MEDIUM (Performance) | 1 | ✅ |
| `NOVA_CREATIVITY_MAX_DEPTH` | `3` | 🟡 MEDIUM (Performance) | 1 | ✅ |
| `NOVA_CREATIVITY_MAX_TOKENS` | `64` | 🔴 CRITICAL (Security) | 1 | ✅ |
| `NOVA_CREATIVITY_NOVELTY_ETA` | `0.08` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_CREATIVITY_TWO_PHASE` | `0` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_CREATIVITY_TWO_PHASE_MIN` | `3` | 🟡 MEDIUM (Performance) | 1 | ✅ |
| `NOVA_CREATIVITY_TWO_PHASE_THRESH` | `0.045` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_CURRENT_MODE` | `development` | 🟢 LOW (Limited Scope) | 2 | ✅ |
| `NOVA_DISTORTION_DETECTION_SENSITIVITY` | `NO_DEFAULT` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_EMO_PHASE_LOCK_THRESH` | `0.6` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_ENABLE_CREATIVITY_METRICS` | `1` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_ENABLE_META_LENS` | `0` | 🟡 HIGH (Feature Gate) | 3 | ✅ |
| `NOVA_ENABLE_PROBABILISTIC_CONTRACTS` | `1` | 🟡 MEDIUM (Wide Usage) | 4 | ✅ |
| `NOVA_ENABLE_PROMETHEUS` | `false` | 🟡 HIGH (Feature Gate) | 2 | ✅ |
| `NOVA_ENABLE_TRI_LINK` | `NO_DEFAULT` | 🟡 HIGH (Feature Gate) | 3 | ✅ |
| `NOVA_ENTROPY_SEED` | `NO_DEFAULT` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_EXPIRE_TEST_AGE` | `120` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_FEDERATION_AUTOREMEDIATE` | `NO_DEFAULT` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_FEDERATION_BODY_MAX` | `str(64 * 1024` | 🟡 MEDIUM (Performance) | 1 | ✅ |
| `NOVA_FEDERATION_CHUNK_BYTES_MAX` | `str(64 * 1024` | 🟡 MEDIUM (Performance) | 1 | ✅ |
| `NOVA_FEDERATION_HTTP_TIMEOUT_S` | `2.5` | 🟡 MEDIUM (Performance) | 1 | ✅ |
| `NOVA_FEDERATION_MANIFEST_TTL_S` | `3600` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_FEDERATION_MAX_DIVERGENCE` | `2` | 🟡 MEDIUM (Performance) | 1 | ✅ |
| `NOVA_FEDERATION_NO_PEER_COOLDOWN` | `600` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_FEDERATION_NO_PEER_THRESHOLD` | `5` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_FEDERATION_RANGE_MAX` | `256` | 🟡 MEDIUM (Performance) | 1 | ✅ |
| `NOVA_FEDERATION_RATE_BURST` | `30` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_FEDERATION_RATE_RPS` | `0.5` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_FEDERATION_REGISTRY` | `NO_DEFAULT` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_FEDERATION_REPLAY_CACHE_SIZE` | `4096` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_FEDERATION_REPLAY_MODE` | `block` | 🟡 HIGH (Feature Gate) | 1 | ✅ |
| `NOVA_FEDERATION_RETRIES` | `2` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_FEDERATION_SKEW_S` | `120` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_FEDERATION_TRUST_W_AGE` | `0.15` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_FEDERATION_TRUST_W_CONTINUITY` | `0.15` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_FEDERATION_TRUST_W_LATENCY` | `0.15` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_FEDERATION_TRUST_W_VERIFIED` | `NO_DEFAULT` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_FED_FORCE_ERRORS` | `0` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_FED_MIN_GOOD_PEERS` | `NO_DEFAULT` | 🟡 MEDIUM (Performance) | 1 | ✅ |
| `NOVA_FED_MIN_PEER_QUALITY` | `NO_DEFAULT` | 🟡 MEDIUM (Performance) | 1 | ✅ |
| `NOVA_FED_MOCK_PEERS` | `0` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_FED_MOCK_STD` | `0.15` | 🟢 LOW (Limited Scope) | 2 | ✅ |
| `NOVA_FED_PEERS` | `NO_DEFAULT` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_FED_QUALITY_LAT_CAP_SEC` | `NO_DEFAULT` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_FED_QUALITY_TAU_SEC` | `NO_DEFAULT` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_FED_SCRAPE_INTERVAL` | `NO_DEFAULT` | 🟡 MEDIUM (Performance) | 1 | ✅ |
| `NOVA_FED_SCRAPE_MAX_INTERVAL` | `str(max(_MIN_INTERVAL * 8, ...` | 🟡 MEDIUM (Performance) | 1 | ✅ |
| `NOVA_FED_SCRAPE_TIMEOUT` | `NO_DEFAULT` | 🟡 MEDIUM (Performance) | 1 | ✅ |
| `NOVA_FED_SYNC_ENABLED` | `0` | 🟡 HIGH (Feature Gate) | 3 | ✅ |
| `NOVA_FED_SYNC_INTERVAL` | `30` | 🟡 MEDIUM (Performance) | 1 | ✅ |
| `NOVA_FED_SYNC_TIMEOUT` | `2.5` | 🟡 MEDIUM (Performance) | 1 | ✅ |
| `NOVA_FLOW_FABRIC_LAZY_INIT` | `1` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_FLOW_METRICS_ENABLED` | `NO_DEFAULT` | 🟡 HIGH (Feature Gate) | 2 | ✅ |
| `NOVA_FLOW_MODE` | `BALANCED` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_GAMMA_ETA_DEFAULT` | `0.10` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_GAMMA_ETA_MAX` | `0.15` | 🟡 MEDIUM (Performance) | 1 | ✅ |
| `NOVA_GAMMA_ETA_MIN` | `0.05` | 🟡 MEDIUM (Performance) | 1 | ✅ |
| `NOVA_GM_ENABLED` | `false` | 🟡 HIGH (Feature Gate) | 1 | ✅ |
| `NOVA_HOT_RELOAD` | `NO_DEFAULT` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_LEDGER_STATUS_CMD` | `NO_DEFAULT` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_LEDGER_STATUS_URL` | `NO_DEFAULT` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_LIGHTCLOCK_DEEP` | `1` | 🟡 MEDIUM (Wide Usage) | 9 | ✅ |
| `NOVA_LIGHTCLOCK_GATING` | `1` | 🟡 HIGH (Feature Gate) | 2 | ✅ |
| `NOVA_LOG_LEVEL` | `INFO` | 🟢 LOW (Limited Scope) | 2 | ✅ |
| `NOVA_MAX_CONCURRENT_PROCESSES` | `NO_DEFAULT` | 🟡 MEDIUM (Performance) | 1 | ✅ |
| `NOVA_MEMORY_ETHICS_ENABLED` | `true` | 🟡 HIGH (Feature Gate) | 1 | ✅ |
| `NOVA_META_LENS_ALPHA` | `0.5` | 🟡 MEDIUM (Performance) | 1 | ✅ |
| `NOVA_META_LENS_EPSILON` | `NO_DEFAULT` | 🟡 MEDIUM (Performance) | 1 | ✅ |
| `NOVA_META_LENS_MAX_ITERS` | `3` | 🟡 MEDIUM (Performance) | 1 | ✅ |
| `NOVA_META_LENS_TEST_ENFORCE_REAL` | `0` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_NODE_ID` | `NO_DEFAULT` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_PHASE_LOCK_GATE` | `0.70` | 🟡 HIGH (Feature Gate) | 2 | ✅ |
| `NOVA_PUBLISH_PHASE_LOCK` | `1` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_PUBLISH_TRI` | `1` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_REFLECTION_SECRET` | `nova-reflection-default-key` | 🔴 CRITICAL (Security) | 1 | ✅ |
| `NOVA_REFLEX_ENABLED` | `false` | 🟡 HIGH (Feature Gate) | 3 | ✅ |
| `NOVA_REFLEX_SHADOW` | `NO_DEFAULT` | 🟡 MEDIUM (Wide Usage) | 3 | ✅ |
| `NOVA_ROUTER_ERROR_THRESHOLD` | `NO_DEFAULT` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_ROUTER_LATENCY_MS` | `1000.0` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_ROUTER_TIMEOUT_CAP_S` | `30.0` | 🟡 MEDIUM (Performance) | 1 | ✅ |
| `NOVA_ROUTER_TIMEOUT_MULTIPLIER` | `1.5` | 🟡 MEDIUM (Performance) | 1 | ✅ |
| `NOVA_SMEEP_INTERVAL` | `15` | 🟡 MEDIUM (Performance) | 1 | ✅ |
| `NOVA_TRI_COHERENCE_HIGH` | `0.85` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_TRI_COHERENCE_LOW` | `0.40` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_TRI_ETA_CAP_ENABLED` | `1` | 🟡 HIGH (Feature Gate) | 1 | ✅ |
| `NOVA_TRI_ETA_CAP_HIGH` | `0.18` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_TRI_ETA_CAP_LOW` | `0.08` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_TRI_GATE` | `0.66` | 🟡 HIGH (Feature Gate) | 1 | ✅ |
| `NOVA_TRUTH_THRESHOLD` | `0.87` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_UNLEARN_ANOMALY` | `0` | 🟡 MEDIUM (Wide Usage) | 3 | ✅ |
| `NOVA_UNLEARN_ANOM_ALPHA` | `0.30` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_UNLEARN_ANOM_CAP` | `3.00` | 🟡 MEDIUM (Performance) | 1 | ✅ |
| `NOVA_UNLEARN_ANOM_GAIN` | `0.50` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_UNLEARN_ANOM_MARGIN` | `0.20` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_UNLEARN_ANOM_REQ` | `3` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_UNLEARN_ANOM_TAU` | `1.00` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_UNLEARN_ANOM_WIN` | `5` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_UNLEARN_CANARY` | `0` | 🟡 HIGH (Feature Gate) | 2 | ✅ |
| `NOVA_UNLEARN_CANARY_AGE` | `120` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_UNLEARN_CANARY_KEY` | `slot06.cultural_profile` | 🔴 CRITICAL (Security) | 1 | ✅ |
| `NOVA_UNLEARN_CANARY_PERIOD` | `3600` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_UNLEARN_CANARY_PUBLISHER` | `slot05` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_UNLEARN_CANARY_TTL` | `60` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_UNLEARN_LOG_BACKUPS` | `NO_DEFAULT` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_UNLEARN_LOG_MAX_BYTES` | `NO_DEFAULT` | 🟡 MEDIUM (Performance) | 1 | ✅ |
| `NOVA_UNLEARN_MAX_HALF_LIFE` | `1800` | 🟡 MEDIUM (Performance) | 1 | ✅ |
| `NOVA_UNLEARN_MIN_HALF_LIFE` | `60` | 🟡 MEDIUM (Performance) | 1 | ✅ |
| `NOVA_UNLEARN_PULSE_LOG` | `1` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_UNLEARN_PULSE_PATH` | `logs/unlearn_pulses.ndjson` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_UNLEARN_W_JITTER` | `0.1` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_UNLEARN_W_PRESS` | `0.4` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_UNLEARN_W_TRI` | `0.5` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_USE_SHARED_HASH` | `0` | 🟡 HIGH (Feature Gate) | 2 | ✅ |
| `NOVA_VERSION` | `5.1.1-polish` | 🟢 LOW (Limited Scope) | 2 | ✅ |
| `NOVA_WISDOM_BACKPRESSURE_ENABLED` | `0` | 🟡 HIGH (Feature Gate) | 1 | ✅ |
| `NOVA_WISDOM_ETA_DEFAULT` | `0.10` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_WISDOM_ETA_MAX` | `0.18` | 🟡 MEDIUM (Performance) | 1 | ✅ |
| `NOVA_WISDOM_ETA_MIN` | `0.05` | 🟡 MEDIUM (Performance) | 1 | ✅ |
| `NOVA_WISDOM_GOVERNOR_ENABLED` | `NO_DEFAULT` | 🟡 HIGH (Feature Gate) | 2 | ✅ |
| `NOVA_WISDOM_G_CONTEXT` | `auto` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_WISDOM_G_HYSTERESIS_SEC` | `120` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_WISDOM_G_KAPPA` | `0.02` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_WISDOM_G_MIN_H` | `0.02` | 🟡 MEDIUM (Performance) | 1 | ✅ |
| `NOVA_WISDOM_G_MIN_PEERS` | `1` | 🟡 MEDIUM (Performance) | 1 | ✅ |
| `NOVA_WISDOM_G_MIN_S` | `0.03` | 🟡 MEDIUM (Performance) | 1 | ✅ |
| `NOVA_WISDOM_G_TARGET` | `0.6` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_WISDOM_G_WEIGHTS` | `0.4,0.3,0.3` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_WISDOM_HOPF_THRESHOLD` | `0.02` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_WISDOM_KD` | `0.15` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_WISDOM_KP` | `0.3` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_WISDOM_POLL_INTERVAL` | `NO_DEFAULT` | 🟡 MEDIUM (Performance) | 1 | ✅ |
| `NOVA_WISDOM_Q` | `0.7` | 🟢 LOW (Limited Scope) | 1 | ✅ |
| `NOVA_WISDOM_S_REF` | `0.05` | 🟢 LOW (Limited Scope) | 1 | ✅ |

---

## Detailed Usage Breakdown

### `NOVA_ADAPTIVE_CONNECTIONS_ENABLED`

**Defaults**: Multiple values found:
  - `NO_DEFAULT` (3 locations)
  - `false` (4 locations)
  - `str(adaptive_enabled` (1 locations)

**Impact**: 🟡 HIGH (Feature Gate)

**Documentation**: ✅ Documented

**Usage Locations** (8 total):

- `adaptive_connections.py:265`
  ```python
  "adaptive_connections_active": os.getenv("NOVA_ADAPTIVE_CONNECTIONS_ENABLED", "false").lower() == "true",
  ```

- `adaptive_connections.py:265`
  ```python
  "adaptive_connections_active": os.getenv("NOVA_ADAPTIVE_CONNECTIONS_ENABLED", "false").lower() == "true",
  ```

- `adaptive_connections.py:265`
  ```python
  "adaptive_connections_active": os.getenv("NOVA_ADAPTIVE_CONNECTIONS_ENABLED", "false").lower() == "true",
  ```

- `config.py:38`
  ```python
  ADAPTIVE_CONNECTIONS_ENABLED: bool = os.getenv("NOVA_ADAPTIVE_CONNECTIONS_ENABLED", "false").lower() == "true"
  ```

- `config.py:38`
  ```python
  ADAPTIVE_CONNECTIONS_ENABLED: bool = os.getenv("NOVA_ADAPTIVE_CONNECTIONS_ENABLED", "false").lower() == "true"
  ```

- `config.py:38`
  ```python
  ADAPTIVE_CONNECTIONS_ENABLED: bool = os.getenv("NOVA_ADAPTIVE_CONNECTIONS_ENABLED", "false").lower() == "true"
  ```

- `flow_fabric_init.py:79`
  ```python
  adaptive_enabled = os.getenv("NOVA_ADAPTIVE_CONNECTIONS_ENABLED", str(adaptive_enabled)).lower() == "true"
  ```

- `flow_fabric_init.py:79`
  ```python
  adaptive_enabled = os.getenv("NOVA_ADAPTIVE_CONNECTIONS_ENABLED", str(adaptive_enabled)).lower() == "true"
  ```

---

### `NOVA_ALLOW_EXPIRE_TEST`

**Defaults**: Multiple values found:
  - `1` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟡 HIGH (Feature Gate)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `app.py:688`
  ```python
  if os.getenv("NOVA_ALLOW_EXPIRE_TEST", "1") == "1":
  ```

- `app.py:688`
  ```python
  if os.getenv("NOVA_ALLOW_EXPIRE_TEST", "1") == "1":
  ```

- `app.py:688`
  ```python
  if os.getenv("NOVA_ALLOW_EXPIRE_TEST", "1") == "1":
  ```

---

### `NOVA_ANCHOR_VALIDATION_MODE`

**Defaults**: Multiple values found:
  - `NO_DEFAULT` (1 locations)
  - `STRICT` (2 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `core/__init__.py:42`
  ```python
  mode = os.getenv("NOVA_ANCHOR_VALIDATION_MODE", "STRICT").upper()
  ```

- `core/__init__.py:42`
  ```python
  mode = os.getenv("NOVA_ANCHOR_VALIDATION_MODE", "STRICT").upper()
  ```

- `core/__init__.py:42`
  ```python
  mode = os.getenv("NOVA_ANCHOR_VALIDATION_MODE", "STRICT").upper()
  ```

---

### `NOVA_ANR_ALPHA`

**Defaults**: Multiple values found:
  - `0.8` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `router/anr.py:51`
  ```python
  self.bandit_alpha = float(os.getenv("NOVA_ANR_ALPHA", "0.8"))
  ```

- `router/anr.py:51`
  ```python
  self.bandit_alpha = float(os.getenv("NOVA_ANR_ALPHA", "0.8"))
  ```

- `router/anr.py:51`
  ```python
  self.bandit_alpha = float(os.getenv("NOVA_ANR_ALPHA", "0.8"))
  ```

---

### `NOVA_ANR_ENABLED`

**Defaults**: Multiple values found:
  - `0` (4 locations)
  - `NO_DEFAULT` (2 locations)

**Impact**: 🟡 HIGH (Feature Gate)

**Documentation**: ✅ Documented

**Usage Locations** (6 total):

- `reflection.py:116`
  ```python
  "NOVA_ANR_ENABLED": os.getenv("NOVA_ANR_ENABLED", "0"),
  ```

- `reflection.py:116`
  ```python
  "NOVA_ANR_ENABLED": os.getenv("NOVA_ANR_ENABLED", "0"),
  ```

- `reflection.py:116`
  ```python
  "NOVA_ANR_ENABLED": os.getenv("NOVA_ANR_ENABLED", "0"),
  ```

- `router/anr.py:42`
  ```python
  self.enabled = os.getenv("NOVA_ANR_ENABLED", "0") == "1"  # keep 0 for 5.0 shadow
  ```

- `router/anr.py:42`
  ```python
  self.enabled = os.getenv("NOVA_ANR_ENABLED", "0") == "1"  # keep 0 for 5.0 shadow
  ```

- `router/anr.py:42`
  ```python
  self.enabled = os.getenv("NOVA_ANR_ENABLED", "0") == "1"  # keep 0 for 5.0 shadow
  ```

---

### `NOVA_ANR_EPSILON`

**Defaults**: Multiple values found:
  - `0.05` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `router/anr.py:44`
  ```python
  self.eps = float(os.getenv("NOVA_ANR_EPSILON", "0.05"))
  ```

- `router/anr.py:44`
  ```python
  self.eps = float(os.getenv("NOVA_ANR_EPSILON", "0.05"))
  ```

- `router/anr.py:44`
  ```python
  self.eps = float(os.getenv("NOVA_ANR_EPSILON", "0.05"))
  ```

---

### `NOVA_ANR_KILL`

**Defaults**: Multiple values found:
  - `0` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `router/anr.py:164`
  ```python
  if os.getenv("NOVA_ANR_KILL", "0") == "1":
  ```

- `router/anr.py:164`
  ```python
  if os.getenv("NOVA_ANR_KILL", "0") == "1":
  ```

- `router/anr.py:164`
  ```python
  if os.getenv("NOVA_ANR_KILL", "0") == "1":
  ```

---

### `NOVA_ANR_LEARN_SHADOW`

**Defaults**: Multiple values found:
  - `0` (2 locations)
  - `1` (2 locations)
  - `NO_DEFAULT` (2 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (6 total):

- `reflection.py:118`
  ```python
  "NOVA_ANR_LEARN_SHADOW": os.getenv("NOVA_ANR_LEARN_SHADOW", "0"),
  ```

- `reflection.py:118`
  ```python
  "NOVA_ANR_LEARN_SHADOW": os.getenv("NOVA_ANR_LEARN_SHADOW", "0"),
  ```

- `reflection.py:118`
  ```python
  "NOVA_ANR_LEARN_SHADOW": os.getenv("NOVA_ANR_LEARN_SHADOW", "0"),
  ```

- `router/anr.py:49`
  ```python
  self.learn_in_shadow = os.getenv("NOVA_ANR_LEARN_SHADOW", "1") == "1"
  ```

- `router/anr.py:49`
  ```python
  self.learn_in_shadow = os.getenv("NOVA_ANR_LEARN_SHADOW", "1") == "1"
  ```

- `router/anr.py:49`
  ```python
  self.learn_in_shadow = os.getenv("NOVA_ANR_LEARN_SHADOW", "1") == "1"
  ```

---

### `NOVA_ANR_MAX_FAST_PROB`

**Defaults**: Multiple values found:
  - `0.15` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟡 MEDIUM (Performance)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `router/anr.py:137`
  ```python
  cap = float(os.getenv("NOVA_ANR_MAX_FAST_PROB", "0.15"))
  ```

- `router/anr.py:137`
  ```python
  cap = float(os.getenv("NOVA_ANR_MAX_FAST_PROB", "0.15"))
  ```

- `router/anr.py:137`
  ```python
  cap = float(os.getenv("NOVA_ANR_MAX_FAST_PROB", "0.15"))
  ```

---

### `NOVA_ANR_PILOT`

**Defaults**: Multiple values found:
  - `0.0` (4 locations)
  - `NO_DEFAULT` (2 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (6 total):

- `reflection.py:117`
  ```python
  "NOVA_ANR_PILOT": os.getenv("NOVA_ANR_PILOT", "0.0"),
  ```

- `reflection.py:117`
  ```python
  "NOVA_ANR_PILOT": os.getenv("NOVA_ANR_PILOT", "0.0"),
  ```

- `reflection.py:117`
  ```python
  "NOVA_ANR_PILOT": os.getenv("NOVA_ANR_PILOT", "0.0"),
  ```

- `router/anr.py:43`
  ```python
  self.pilot = float(os.getenv("NOVA_ANR_PILOT", "0.0"))
  ```

- `router/anr.py:43`
  ```python
  self.pilot = float(os.getenv("NOVA_ANR_PILOT", "0.0"))
  ```

- `router/anr.py:43`
  ```python
  self.pilot = float(os.getenv("NOVA_ANR_PILOT", "0.0"))
  ```

---

### `NOVA_ANR_RIDGE`

**Defaults**: Multiple values found:
  - `0.01` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `router/anr.py:52`
  ```python
  self.bandit_ridge = float(os.getenv("NOVA_ANR_RIDGE", "0.01"))
  ```

- `router/anr.py:52`
  ```python
  self.bandit_ridge = float(os.getenv("NOVA_ANR_RIDGE", "0.01"))
  ```

- `router/anr.py:52`
  ```python
  self.bandit_ridge = float(os.getenv("NOVA_ANR_RIDGE", "0.01"))
  ```

---

### `NOVA_ANR_SHADOW_SAMPLE`

**Defaults**: Multiple values found:
  - `1.0` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `router/anr.py:45`
  ```python
  self.shadow_sample = float(os.getenv("NOVA_ANR_SHADOW_SAMPLE", "1.0"))
  ```

- `router/anr.py:45`
  ```python
  self.shadow_sample = float(os.getenv("NOVA_ANR_SHADOW_SAMPLE", "1.0"))
  ```

- `router/anr.py:45`
  ```python
  self.shadow_sample = float(os.getenv("NOVA_ANR_SHADOW_SAMPLE", "1.0"))
  ```

---

### `NOVA_ANR_STATE_PATH`

**Defaults**: Multiple values found:
  - `NO_DEFAULT` (1 locations)
  - `os.path.join(".", "state", "anr_linucb.json` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (2 total):

- `router/anr.py:50`
  ```python
  self.bandit_state_path = os.getenv("NOVA_ANR_STATE_PATH", os.path.join(".", "state", "anr_linucb.json"))
  ```

- `router/anr.py:50`
  ```python
  self.bandit_state_path = os.getenv("NOVA_ANR_STATE_PATH", os.path.join(".", "state", "anr_linucb.json"))
  ```

---

### `NOVA_ANR_STRICT_ON_ANOMALY`

**Defaults**: Multiple values found:
  - `0` (2 locations)
  - `NO_DEFAULT` (2 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (4 total):

- `reflection.py:119`
  ```python
  "NOVA_ANR_STRICT_ON_ANOMALY": os.getenv("NOVA_ANR_STRICT_ON_ANOMALY", "0"),
  ```

- `reflection.py:119`
  ```python
  "NOVA_ANR_STRICT_ON_ANOMALY": os.getenv("NOVA_ANR_STRICT_ON_ANOMALY", "0"),
  ```

- `reflection.py:119`
  ```python
  "NOVA_ANR_STRICT_ON_ANOMALY": os.getenv("NOVA_ANR_STRICT_ON_ANOMALY", "0"),
  ```

- `router/anr.py:98`
  ```python
  if os.getenv("NOVA_ANR_STRICT_ON_ANOMALY") == "1":
  ```

---

### `NOVA_ARC_ENABLED`

**Defaults**: Multiple values found:
  - `0` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟡 HIGH (Feature Gate)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `arc.py:30`
  ```python
  return os.getenv("NOVA_ARC_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"}
  ```

- `arc.py:30`
  ```python
  return os.getenv("NOVA_ARC_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"}
  ```

- `arc.py:30`
  ```python
  return os.getenv("NOVA_ARC_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"}
  ```

---

### `NOVA_ARC_SAMPLE`

**Defaults**: Multiple values found:
  - `0.10` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `arc.py:35`
  ```python
  return float(os.getenv("NOVA_ARC_SAMPLE", "0.10"))
  ```

- `arc.py:35`
  ```python
  return float(os.getenv("NOVA_ARC_SAMPLE", "0.10"))
  ```

- `arc.py:35`
  ```python
  return float(os.getenv("NOVA_ARC_SAMPLE", "0.10"))
  ```

---

### `NOVA_BUILD_SHA`

**Defaults**: Multiple values found:
  - `NO_DEFAULT` (2 locations)
  - `unknown` (4 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (6 total):

- `reflection.py:124`
  ```python
  "NOVA_BUILD_SHA": os.getenv("NOVA_BUILD_SHA", "unknown"),
  ```

- `reflection.py:124`
  ```python
  "NOVA_BUILD_SHA": os.getenv("NOVA_BUILD_SHA", "unknown"),
  ```

- `reflection.py:124`
  ```python
  "NOVA_BUILD_SHA": os.getenv("NOVA_BUILD_SHA", "unknown"),
  ```

- `reflection.py:138`
  ```python
  "sha": os.getenv("NOVA_BUILD_SHA", "unknown"),
  ```

- `reflection.py:138`
  ```python
  "sha": os.getenv("NOVA_BUILD_SHA", "unknown"),
  ```

- `reflection.py:138`
  ```python
  "sha": os.getenv("NOVA_BUILD_SHA", "unknown"),
  ```

---

### `NOVA_CREATIVITY_BNB`

**Defaults**: Multiple values found:
  - `0` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `semantic_creativity.py:677`
  ```python
  bnb_val = os.getenv("NOVA_CREATIVITY_BNB", "0")
  ```

- `semantic_creativity.py:677`
  ```python
  bnb_val = os.getenv("NOVA_CREATIVITY_BNB", "0")
  ```

- `semantic_creativity.py:677`
  ```python
  bnb_val = os.getenv("NOVA_CREATIVITY_BNB", "0")
  ```

---

### `NOVA_CREATIVITY_BNB_MARGIN`

**Defaults**: Multiple values found:
  - `0.05` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `semantic_creativity.py:707`
  ```python
  bnb_safety_margin=float(os.getenv("NOVA_CREATIVITY_BNB_MARGIN","0.05")),
  ```

- `semantic_creativity.py:707`
  ```python
  bnb_safety_margin=float(os.getenv("NOVA_CREATIVITY_BNB_MARGIN","0.05")),
  ```

- `semantic_creativity.py:707`
  ```python
  bnb_safety_margin=float(os.getenv("NOVA_CREATIVITY_BNB_MARGIN","0.05")),
  ```

---

### `NOVA_CREATIVITY_BNB_Q`

**Defaults**: Multiple values found:
  - `0.40` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `semantic_creativity.py:706`
  ```python
  bnb_quality_threshold=float(os.getenv("NOVA_CREATIVITY_BNB_Q","0.40")),
  ```

- `semantic_creativity.py:706`
  ```python
  bnb_quality_threshold=float(os.getenv("NOVA_CREATIVITY_BNB_Q","0.40")),
  ```

- `semantic_creativity.py:706`
  ```python
  bnb_quality_threshold=float(os.getenv("NOVA_CREATIVITY_BNB_Q","0.40")),
  ```

---

### `NOVA_CREATIVITY_DEBUG`

**Defaults**: Multiple values found:
  - `0` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `reflection.py:223`
  ```python
  if os.getenv("NOVA_CREATIVITY_DEBUG", "0") == "1":
  ```

- `reflection.py:223`
  ```python
  if os.getenv("NOVA_CREATIVITY_DEBUG", "0") == "1":
  ```

- `reflection.py:223`
  ```python
  if os.getenv("NOVA_CREATIVITY_DEBUG", "0") == "1":
  ```

---

### `NOVA_CREATIVITY_EARLY_STOP`

**Defaults**: Multiple values found:
  - `0` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `semantic_creativity.py:675`
  ```python
  early_stop_val = os.getenv("NOVA_CREATIVITY_EARLY_STOP", "0")
  ```

- `semantic_creativity.py:675`
  ```python
  early_stop_val = os.getenv("NOVA_CREATIVITY_EARLY_STOP", "0")
  ```

- `semantic_creativity.py:675`
  ```python
  early_stop_val = os.getenv("NOVA_CREATIVITY_EARLY_STOP", "0")
  ```

---

### `NOVA_CREATIVITY_EARLY_STOP_IG`

**Defaults**: Multiple values found:
  - `0.03` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟡 MEDIUM (Performance)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `semantic_creativity.py:699`
  ```python
  early_stop_min_info_gain=float(os.getenv("NOVA_CREATIVITY_EARLY_STOP_IG", "0.03")),
  ```

- `semantic_creativity.py:699`
  ```python
  early_stop_min_info_gain=float(os.getenv("NOVA_CREATIVITY_EARLY_STOP_IG", "0.03")),
  ```

- `semantic_creativity.py:699`
  ```python
  early_stop_min_info_gain=float(os.getenv("NOVA_CREATIVITY_EARLY_STOP_IG", "0.03")),
  ```

---

### `NOVA_CREATIVITY_EARLY_STOP_SCORE`

**Defaults**: Multiple values found:
  - `0.62` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `semantic_creativity.py:698`
  ```python
  early_stop_target_score=float(os.getenv("NOVA_CREATIVITY_EARLY_STOP_SCORE", "0.62")),
  ```

- `semantic_creativity.py:698`
  ```python
  early_stop_target_score=float(os.getenv("NOVA_CREATIVITY_EARLY_STOP_SCORE", "0.62")),
  ```

- `semantic_creativity.py:698`
  ```python
  early_stop_target_score=float(os.getenv("NOVA_CREATIVITY_EARLY_STOP_SCORE", "0.62")),
  ```

---

### `NOVA_CREATIVITY_ENTROPY_DELTA_STALL`

**Defaults**: Multiple values found:
  - `0.01` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `semantic_creativity.py:695`
  ```python
  entropy_delta_stall_threshold=float(os.getenv("NOVA_CREATIVITY_ENTROPY_DELTA_STALL", "0.01")),
  ```

- `semantic_creativity.py:695`
  ```python
  entropy_delta_stall_threshold=float(os.getenv("NOVA_CREATIVITY_ENTROPY_DELTA_STALL", "0.01")),
  ```

- `semantic_creativity.py:695`
  ```python
  entropy_delta_stall_threshold=float(os.getenv("NOVA_CREATIVITY_ENTROPY_DELTA_STALL", "0.01")),
  ```

---

### `NOVA_CREATIVITY_ENTROPY_MAX`

**Defaults**: Multiple values found:
  - `2.8` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟡 MEDIUM (Performance)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `semantic_creativity.py:693`
  ```python
  entropy_max=float(os.getenv("NOVA_CREATIVITY_ENTROPY_MAX", "2.8")),
  ```

- `semantic_creativity.py:693`
  ```python
  entropy_max=float(os.getenv("NOVA_CREATIVITY_ENTROPY_MAX", "2.8")),
  ```

- `semantic_creativity.py:693`
  ```python
  entropy_max=float(os.getenv("NOVA_CREATIVITY_ENTROPY_MAX", "2.8")),
  ```

---

### `NOVA_CREATIVITY_ENTROPY_MIN`

**Defaults**: Multiple values found:
  - `1.2` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟡 MEDIUM (Performance)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `semantic_creativity.py:692`
  ```python
  entropy_min=float(os.getenv("NOVA_CREATIVITY_ENTROPY_MIN", "1.2")),
  ```

- `semantic_creativity.py:692`
  ```python
  entropy_min=float(os.getenv("NOVA_CREATIVITY_ENTROPY_MIN", "1.2")),
  ```

- `semantic_creativity.py:692`
  ```python
  entropy_min=float(os.getenv("NOVA_CREATIVITY_ENTROPY_MIN", "1.2")),
  ```

---

### `NOVA_CREATIVITY_EWMA_ALPHA`

**Defaults**: Multiple values found:
  - `0.01` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `semantic_creativity.py:694`
  ```python
  ewma_alpha=float(os.getenv("NOVA_CREATIVITY_EWMA_ALPHA", "0.01")),
  ```

- `semantic_creativity.py:694`
  ```python
  ewma_alpha=float(os.getenv("NOVA_CREATIVITY_EWMA_ALPHA", "0.01")),
  ```

- `semantic_creativity.py:694`
  ```python
  ewma_alpha=float(os.getenv("NOVA_CREATIVITY_EWMA_ALPHA", "0.01")),
  ```

---

### `NOVA_CREATIVITY_INFO_GAIN_EPS`

**Defaults**: Multiple values found:
  - `0.02` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `semantic_creativity.py:691`
  ```python
  info_gain_eps=float(os.getenv("NOVA_CREATIVITY_INFO_GAIN_EPS", "0.02")),
  ```

- `semantic_creativity.py:691`
  ```python
  info_gain_eps=float(os.getenv("NOVA_CREATIVITY_INFO_GAIN_EPS", "0.02")),
  ```

- `semantic_creativity.py:691`
  ```python
  info_gain_eps=float(os.getenv("NOVA_CREATIVITY_INFO_GAIN_EPS", "0.02")),
  ```

---

### `NOVA_CREATIVITY_MAX_BRANCHES`

**Defaults**: Multiple values found:
  - `6` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟡 MEDIUM (Performance)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `semantic_creativity.py:688`
  ```python
  max_branches=int(os.getenv("NOVA_CREATIVITY_MAX_BRANCHES", "6")),
  ```

- `semantic_creativity.py:688`
  ```python
  max_branches=int(os.getenv("NOVA_CREATIVITY_MAX_BRANCHES", "6")),
  ```

- `semantic_creativity.py:688`
  ```python
  max_branches=int(os.getenv("NOVA_CREATIVITY_MAX_BRANCHES", "6")),
  ```

---

### `NOVA_CREATIVITY_MAX_DEPTH`

**Defaults**: Multiple values found:
  - `3` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟡 MEDIUM (Performance)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `semantic_creativity.py:687`
  ```python
  max_depth=int(os.getenv("NOVA_CREATIVITY_MAX_DEPTH", "3")),
  ```

- `semantic_creativity.py:687`
  ```python
  max_depth=int(os.getenv("NOVA_CREATIVITY_MAX_DEPTH", "3")),
  ```

- `semantic_creativity.py:687`
  ```python
  max_depth=int(os.getenv("NOVA_CREATIVITY_MAX_DEPTH", "3")),
  ```

---

### `NOVA_CREATIVITY_MAX_TOKENS`

**Defaults**: Multiple values found:
  - `64` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🔴 CRITICAL (Security)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `semantic_creativity.py:689`
  ```python
  max_tokens_per_probe=int(os.getenv("NOVA_CREATIVITY_MAX_TOKENS", "64")),
  ```

- `semantic_creativity.py:689`
  ```python
  max_tokens_per_probe=int(os.getenv("NOVA_CREATIVITY_MAX_TOKENS", "64")),
  ```

- `semantic_creativity.py:689`
  ```python
  max_tokens_per_probe=int(os.getenv("NOVA_CREATIVITY_MAX_TOKENS", "64")),
  ```

---

### `NOVA_CREATIVITY_NOVELTY_ETA`

**Defaults**: Multiple values found:
  - `0.08` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `semantic_creativity.py:690`
  ```python
  novelty_eta=float(os.getenv("NOVA_CREATIVITY_NOVELTY_ETA", "0.08")),
  ```

- `semantic_creativity.py:690`
  ```python
  novelty_eta=float(os.getenv("NOVA_CREATIVITY_NOVELTY_ETA", "0.08")),
  ```

- `semantic_creativity.py:690`
  ```python
  novelty_eta=float(os.getenv("NOVA_CREATIVITY_NOVELTY_ETA", "0.08")),
  ```

---

### `NOVA_CREATIVITY_TWO_PHASE`

**Defaults**: Multiple values found:
  - `0` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `semantic_creativity.py:676`
  ```python
  two_phase_val = os.getenv("NOVA_CREATIVITY_TWO_PHASE", "0")
  ```

- `semantic_creativity.py:676`
  ```python
  two_phase_val = os.getenv("NOVA_CREATIVITY_TWO_PHASE", "0")
  ```

- `semantic_creativity.py:676`
  ```python
  two_phase_val = os.getenv("NOVA_CREATIVITY_TWO_PHASE", "0")
  ```

---

### `NOVA_CREATIVITY_TWO_PHASE_MIN`

**Defaults**: Multiple values found:
  - `3` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟡 MEDIUM (Performance)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `semantic_creativity.py:703`
  ```python
  two_phase_min_branches=int(os.getenv("NOVA_CREATIVITY_TWO_PHASE_MIN", "3")),
  ```

- `semantic_creativity.py:703`
  ```python
  two_phase_min_branches=int(os.getenv("NOVA_CREATIVITY_TWO_PHASE_MIN", "3")),
  ```

- `semantic_creativity.py:703`
  ```python
  two_phase_min_branches=int(os.getenv("NOVA_CREATIVITY_TWO_PHASE_MIN", "3")),
  ```

---

### `NOVA_CREATIVITY_TWO_PHASE_THRESH`

**Defaults**: Multiple values found:
  - `0.045` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `semantic_creativity.py:702`
  ```python
  two_phase_refine_threshold=float(os.getenv("NOVA_CREATIVITY_TWO_PHASE_THRESH", "0.045")),
  ```

- `semantic_creativity.py:702`
  ```python
  two_phase_refine_threshold=float(os.getenv("NOVA_CREATIVITY_TWO_PHASE_THRESH", "0.045")),
  ```

- `semantic_creativity.py:702`
  ```python
  two_phase_refine_threshold=float(os.getenv("NOVA_CREATIVITY_TWO_PHASE_THRESH", "0.045")),
  ```

---

### `NOVA_CURRENT_MODE`

**Defaults**: Multiple values found:
  - `NO_DEFAULT` (2 locations)
  - `development` (2 locations)
  - `testing` (2 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (6 total):

- `nova/slots/slot07_production_controls/reflex_emitter.py:71`
  ```python
  current_env = os.getenv("NOVA_CURRENT_MODE", "development")
  ```

- `nova/slots/slot07_production_controls/reflex_emitter.py:71`
  ```python
  current_env = os.getenv("NOVA_CURRENT_MODE", "development")
  ```

- `nova/slots/slot07_production_controls/reflex_emitter.py:71`
  ```python
  current_env = os.getenv("NOVA_CURRENT_MODE", "development")
  ```

- `config.py:35`
  ```python
  CURRENT_MODE: str = os.getenv("NOVA_CURRENT_MODE", "testing")
  ```

- `config.py:35`
  ```python
  CURRENT_MODE: str = os.getenv("NOVA_CURRENT_MODE", "testing")
  ```

- `config.py:35`
  ```python
  CURRENT_MODE: str = os.getenv("NOVA_CURRENT_MODE", "testing")
  ```

---

### `NOVA_DISTORTION_DETECTION_SENSITIVITY`

**Defaults**: Multiple values found:
  - `0.92` (1 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (2 total):

- `config.py:25`
  ```python
  DISTORTION_DETECTION_SENSITIVITY: float = float(os.getenv("NOVA_DISTORTION_DETECTION_SENSITIVITY", 0.92))
  ```

- `config.py:25`
  ```python
  DISTORTION_DETECTION_SENSITIVITY: float = float(os.getenv("NOVA_DISTORTION_DETECTION_SENSITIVITY", 0.92))
  ```

---

### `NOVA_EMO_PHASE_LOCK_THRESH`

**Defaults**: Multiple values found:
  - `0.6` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `nova/slots/slot03_emotional_matrix/emotional_matrix_engine.py:145`
  ```python
  thresh = float(os.getenv("NOVA_EMO_PHASE_LOCK_THRESH", "0.6"))
  ```

- `nova/slots/slot03_emotional_matrix/emotional_matrix_engine.py:145`
  ```python
  thresh = float(os.getenv("NOVA_EMO_PHASE_LOCK_THRESH", "0.6"))
  ```

- `nova/slots/slot03_emotional_matrix/emotional_matrix_engine.py:145`
  ```python
  thresh = float(os.getenv("NOVA_EMO_PHASE_LOCK_THRESH", "0.6"))
  ```

---

### `NOVA_ENABLE_CREATIVITY_METRICS`

**Defaults**: Multiple values found:
  - `1` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `reflection.py:212`
  ```python
  if os.getenv("NOVA_ENABLE_CREATIVITY_METRICS", "1") == "1":
  ```

- `reflection.py:212`
  ```python
  if os.getenv("NOVA_ENABLE_CREATIVITY_METRICS", "1") == "1":
  ```

- `reflection.py:212`
  ```python
  if os.getenv("NOVA_ENABLE_CREATIVITY_METRICS", "1") == "1":
  ```

---

### `NOVA_ENABLE_META_LENS`

**Defaults**: Multiple values found:
  - `0` (6 locations)
  - `NO_DEFAULT` (3 locations)

**Impact**: 🟡 HIGH (Feature Gate)

**Documentation**: ✅ Documented

**Usage Locations** (9 total):

- `nova/slots/slot02_deltathresh/plugin_meta_lens_addition.py:9`
  ```python
  if os.getenv("NOVA_ENABLE_META_LENS", "0") not in ("1", "true", "TRUE"):
  ```

- `nova/slots/slot02_deltathresh/plugin_meta_lens_addition.py:9`
  ```python
  if os.getenv("NOVA_ENABLE_META_LENS", "0") not in ("1", "true", "TRUE"):
  ```

- `nova/slots/slot02_deltathresh/plugin_meta_lens_addition.py:9`
  ```python
  if os.getenv("NOVA_ENABLE_META_LENS", "0") not in ("1", "true", "TRUE"):
  ```

- `reflection.py:122`
  ```python
  "NOVA_ENABLE_META_LENS": os.getenv("NOVA_ENABLE_META_LENS", "0"),
  ```

- `reflection.py:122`
  ```python
  "NOVA_ENABLE_META_LENS": os.getenv("NOVA_ENABLE_META_LENS", "0"),
  ```

- `reflection.py:122`
  ```python
  "NOVA_ENABLE_META_LENS": os.getenv("NOVA_ENABLE_META_LENS", "0"),
  ```

- `health_pulse.py:53`
  ```python
  enabled = os.getenv("NOVA_ENABLE_META_LENS", "0") in ("1", "true", "TRUE")
  ```

- `health_pulse.py:53`
  ```python
  enabled = os.getenv("NOVA_ENABLE_META_LENS", "0") in ("1", "true", "TRUE")
  ```

- `health_pulse.py:53`
  ```python
  enabled = os.getenv("NOVA_ENABLE_META_LENS", "0") in ("1", "true", "TRUE")
  ```

---

### `NOVA_ENABLE_PROBABILISTIC_CONTRACTS`

**Defaults**: Multiple values found:
  - `0` (2 locations)
  - `1` (6 locations)
  - `NO_DEFAULT` (4 locations)

**Impact**: 🟡 MEDIUM (Wide Usage)

**Documentation**: ✅ Documented

**Usage Locations** (12 total):

- `nova/slots/slot04_tri/wisdom_feedback.py:100`
  ```python
  if os.getenv("NOVA_ENABLE_PROBABILISTIC_CONTRACTS", "1") == "1":
  ```

- `nova/slots/slot04_tri/wisdom_feedback.py:100`
  ```python
  if os.getenv("NOVA_ENABLE_PROBABILISTIC_CONTRACTS", "1") == "1":
  ```

- `nova/slots/slot04_tri/wisdom_feedback.py:100`
  ```python
  if os.getenv("NOVA_ENABLE_PROBABILISTIC_CONTRACTS", "1") == "1":
  ```

- `nova/slots/slot04_tri/core/tri_engine.py:142`
  ```python
  os.getenv("NOVA_ENABLE_PROBABILISTIC_CONTRACTS", "1") == "1"):
  ```

- `nova/slots/slot04_tri/core/tri_engine.py:142`
  ```python
  os.getenv("NOVA_ENABLE_PROBABILISTIC_CONTRACTS", "1") == "1"):
  ```

- `nova/slots/slot04_tri/core/tri_engine.py:142`
  ```python
  os.getenv("NOVA_ENABLE_PROBABILISTIC_CONTRACTS", "1") == "1"):
  ```

- `nova/slots/slot07_production_controls/production_control_engine.py:628`
  ```python
  os.getenv("NOVA_ENABLE_PROBABILISTIC_CONTRACTS", "1") == "1"):
  ```

- `nova/slots/slot07_production_controls/production_control_engine.py:628`
  ```python
  os.getenv("NOVA_ENABLE_PROBABILISTIC_CONTRACTS", "1") == "1"):
  ```

- `nova/slots/slot07_production_controls/production_control_engine.py:628`
  ```python
  os.getenv("NOVA_ENABLE_PROBABILISTIC_CONTRACTS", "1") == "1"):
  ```

- `reflection.py:120`
  ```python
  "NOVA_ENABLE_PROBABILISTIC_CONTRACTS": os.getenv("NOVA_ENABLE_PROBABILISTIC_CONTRACTS", "0"),
  ```

*... and 2 more locations*

---

### `NOVA_ENABLE_PROMETHEUS`

**Defaults**: Multiple values found:
  - `0` (2 locations)
  - `NO_DEFAULT` (3 locations)
  - `false` (4 locations)

**Impact**: 🟡 HIGH (Feature Gate)

**Documentation**: ✅ Documented

**Usage Locations** (9 total):

- `app.py:310`
  ```python
  prom_enabled = os.getenv("NOVA_ENABLE_PROMETHEUS", "false").strip().lower() in {"1", "true", "yes", "on"}
  ```

- `app.py:310`
  ```python
  prom_enabled = os.getenv("NOVA_ENABLE_PROMETHEUS", "false").strip().lower() in {"1", "true", "yes", "on"}
  ```

- `app.py:310`
  ```python
  prom_enabled = os.getenv("NOVA_ENABLE_PROMETHEUS", "false").strip().lower() in {"1", "true", "yes", "on"}
  ```

- `app.py:584`
  ```python
  flag = os.getenv("NOVA_ENABLE_PROMETHEUS", "false").strip().lower()
  ```

- `app.py:584`
  ```python
  flag = os.getenv("NOVA_ENABLE_PROMETHEUS", "false").strip().lower()
  ```

- `app.py:584`
  ```python
  flag = os.getenv("NOVA_ENABLE_PROMETHEUS", "false").strip().lower()
  ```

- `reflection.py:115`
  ```python
  "NOVA_ENABLE_PROMETHEUS": os.getenv("NOVA_ENABLE_PROMETHEUS", "0"),
  ```

- `reflection.py:115`
  ```python
  "NOVA_ENABLE_PROMETHEUS": os.getenv("NOVA_ENABLE_PROMETHEUS", "0"),
  ```

- `reflection.py:115`
  ```python
  "NOVA_ENABLE_PROMETHEUS": os.getenv("NOVA_ENABLE_PROMETHEUS", "0"),
  ```

---

### `NOVA_ENABLE_TRI_LINK`

**Defaults**: Multiple values found:
  - `` (3 locations)
  - `0` (2 locations)
  - `NO_DEFAULT` (7 locations)

**Impact**: 🟡 HIGH (Feature Gate)

**Documentation**: ✅ Documented

**Usage Locations** (12 total):

- `nova/slots/slot05_constellation/constellation_engine.py:574`
  ```python
  flag = os.getenv("NOVA_ENABLE_TRI_LINK", "").strip().lower()
  ```

- `nova/slots/slot05_constellation/constellation_engine.py:574`
  ```python
  flag = os.getenv("NOVA_ENABLE_TRI_LINK", "").strip().lower()
  ```

- `nova/slots/slot05_constellation/constellation_engine.py:574`
  ```python
  flag = os.getenv("NOVA_ENABLE_TRI_LINK", "").strip().lower()
  ```

- `nova/slots/slot05_constellation/constellation_engine.py:620`
  ```python
  flag = os.getenv("NOVA_ENABLE_TRI_LINK", "").strip().lower()
  ```

- `nova/slots/slot05_constellation/constellation_engine.py:620`
  ```python
  flag = os.getenv("NOVA_ENABLE_TRI_LINK", "").strip().lower()
  ```

- `nova/slots/slot05_constellation/constellation_engine.py:620`
  ```python
  flag = os.getenv("NOVA_ENABLE_TRI_LINK", "").strip().lower()
  ```

- `nova/slots/slot04_tri/health.py:91`
  ```python
  tri_link_enabled = os.getenv("NOVA_ENABLE_TRI_LINK", "0") == "1"
  ```

- `nova/slots/slot04_tri/health.py:91`
  ```python
  tri_link_enabled = os.getenv("NOVA_ENABLE_TRI_LINK", "0") == "1"
  ```

- `nova/slots/slot04_tri/health.py:91`
  ```python
  tri_link_enabled = os.getenv("NOVA_ENABLE_TRI_LINK", "0") == "1"
  ```

- `nova/slots/slot04_tri/core/tri_engine.py:221`
  ```python
  flag = os.getenv("NOVA_ENABLE_TRI_LINK", "").strip().lower()
  ```

*... and 2 more locations*

---

### `NOVA_ENTROPY_SEED`

**Default**: `NO_DEFAULT`

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (1 total):

- `nova/slots/slot01_truth_anchor/quantum_entropy.py:104`
  ```python
  env_seed = os.getenv("NOVA_ENTROPY_SEED")
  ```

---

### `NOVA_EXPIRE_TEST_AGE`

**Defaults**: Multiple values found:
  - `120` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `app.py:692`
  ```python
  desired_age = float(os.getenv("NOVA_EXPIRE_TEST_AGE", "120"))  # seconds
  ```

- `app.py:692`
  ```python
  desired_age = float(os.getenv("NOVA_EXPIRE_TEST_AGE", "120"))  # seconds
  ```

- `app.py:692`
  ```python
  desired_age = float(os.getenv("NOVA_EXPIRE_TEST_AGE", "120"))  # seconds
  ```

---

### `NOVA_FEDERATION_AUTOREMEDIATE`

**Default**: `NO_DEFAULT`

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (1 total):

- `app.py:318`
  ```python
  auto_remediate_env = os.getenv("NOVA_FEDERATION_AUTOREMEDIATE")
  ```

---

### `NOVA_FEDERATION_BODY_MAX`

**Defaults**: Multiple values found:
  - `NO_DEFAULT` (1 locations)
  - `str(64 * 1024` (1 locations)

**Impact**: 🟡 MEDIUM (Performance)

**Documentation**: ✅ Documented

**Usage Locations** (2 total):

- `nova/federation/federation_server.py:211`
  ```python
  body_limit = int(os.getenv("NOVA_FEDERATION_BODY_MAX", str(64 * 1024)))
  ```

- `nova/federation/federation_server.py:211`
  ```python
  body_limit = int(os.getenv("NOVA_FEDERATION_BODY_MAX", str(64 * 1024)))
  ```

---

### `NOVA_FEDERATION_CHUNK_BYTES_MAX`

**Defaults**: Multiple values found:
  - `NO_DEFAULT` (1 locations)
  - `str(64 * 1024` (1 locations)

**Impact**: 🟡 MEDIUM (Performance)

**Documentation**: ✅ Documented

**Usage Locations** (2 total):

- `nova/federation/federation_server.py:224`
  ```python
  chunk_bytes_limit = int(os.getenv("NOVA_FEDERATION_CHUNK_BYTES_MAX", str(64 * 1024)))
  ```

- `nova/federation/federation_server.py:224`
  ```python
  chunk_bytes_limit = int(os.getenv("NOVA_FEDERATION_CHUNK_BYTES_MAX", str(64 * 1024)))
  ```

---

### `NOVA_FEDERATION_HTTP_TIMEOUT_S`

**Defaults**: Multiple values found:
  - `2.5` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟡 MEDIUM (Performance)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `nova/federation/federation_client.py:23`
  ```python
  return float(os.getenv("NOVA_FEDERATION_HTTP_TIMEOUT_S", "2.5"))
  ```

- `nova/federation/federation_client.py:23`
  ```python
  return float(os.getenv("NOVA_FEDERATION_HTTP_TIMEOUT_S", "2.5"))
  ```

- `nova/federation/federation_client.py:23`
  ```python
  return float(os.getenv("NOVA_FEDERATION_HTTP_TIMEOUT_S", "2.5"))
  ```

---

### `NOVA_FEDERATION_MANIFEST_TTL_S`

**Defaults**: Multiple values found:
  - `3600` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `nova/federation/sync.py:44`
  ```python
  raw = os.getenv("NOVA_FEDERATION_MANIFEST_TTL_S", "3600")
  ```

- `nova/federation/sync.py:44`
  ```python
  raw = os.getenv("NOVA_FEDERATION_MANIFEST_TTL_S", "3600")
  ```

- `nova/federation/sync.py:44`
  ```python
  raw = os.getenv("NOVA_FEDERATION_MANIFEST_TTL_S", "3600")
  ```

---

### `NOVA_FEDERATION_MAX_DIVERGENCE`

**Defaults**: Multiple values found:
  - `2` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟡 MEDIUM (Performance)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `nova/federation/sync.py:53`
  ```python
  raw = os.getenv("NOVA_FEDERATION_MAX_DIVERGENCE", "2")
  ```

- `nova/federation/sync.py:53`
  ```python
  raw = os.getenv("NOVA_FEDERATION_MAX_DIVERGENCE", "2")
  ```

- `nova/federation/sync.py:53`
  ```python
  raw = os.getenv("NOVA_FEDERATION_MAX_DIVERGENCE", "2")
  ```

---

### `NOVA_FEDERATION_NO_PEER_COOLDOWN`

**Defaults**: Multiple values found:
  - `600` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `federation_poller.py:51`
  ```python
  _NO_PEERS_COOLDOWN_RAW = os.getenv("NOVA_FEDERATION_NO_PEER_COOLDOWN", "600")
  ```

- `federation_poller.py:51`
  ```python
  _NO_PEERS_COOLDOWN_RAW = os.getenv("NOVA_FEDERATION_NO_PEER_COOLDOWN", "600")
  ```

- `federation_poller.py:51`
  ```python
  _NO_PEERS_COOLDOWN_RAW = os.getenv("NOVA_FEDERATION_NO_PEER_COOLDOWN", "600")
  ```

---

### `NOVA_FEDERATION_NO_PEER_THRESHOLD`

**Defaults**: Multiple values found:
  - `5` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `federation_poller.py:45`
  ```python
  _NO_PEERS_THRESHOLD_RAW = os.getenv("NOVA_FEDERATION_NO_PEER_THRESHOLD", "5")
  ```

- `federation_poller.py:45`
  ```python
  _NO_PEERS_THRESHOLD_RAW = os.getenv("NOVA_FEDERATION_NO_PEER_THRESHOLD", "5")
  ```

- `federation_poller.py:45`
  ```python
  _NO_PEERS_THRESHOLD_RAW = os.getenv("NOVA_FEDERATION_NO_PEER_THRESHOLD", "5")
  ```

---

### `NOVA_FEDERATION_RANGE_MAX`

**Defaults**: Multiple values found:
  - `256` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟡 MEDIUM (Performance)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `nova/federation/federation_server.py:222`
  ```python
  range_limit = int(os.getenv("NOVA_FEDERATION_RANGE_MAX", "256"))
  ```

- `nova/federation/federation_server.py:222`
  ```python
  range_limit = int(os.getenv("NOVA_FEDERATION_RANGE_MAX", "256"))
  ```

- `nova/federation/federation_server.py:222`
  ```python
  range_limit = int(os.getenv("NOVA_FEDERATION_RANGE_MAX", "256"))
  ```

---

### `NOVA_FEDERATION_RATE_BURST`

**Defaults**: Multiple values found:
  - `30` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `nova/federation/federation_server.py:218`
  ```python
  rate_burst = float(os.getenv("NOVA_FEDERATION_RATE_BURST", "30"))
  ```

- `nova/federation/federation_server.py:218`
  ```python
  rate_burst = float(os.getenv("NOVA_FEDERATION_RATE_BURST", "30"))
  ```

- `nova/federation/federation_server.py:218`
  ```python
  rate_burst = float(os.getenv("NOVA_FEDERATION_RATE_BURST", "30"))
  ```

---

### `NOVA_FEDERATION_RATE_RPS`

**Defaults**: Multiple values found:
  - `0.5` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `nova/federation/federation_server.py:217`
  ```python
  rate_rps = float(os.getenv("NOVA_FEDERATION_RATE_RPS", "0.5"))
  ```

- `nova/federation/federation_server.py:217`
  ```python
  rate_rps = float(os.getenv("NOVA_FEDERATION_RATE_RPS", "0.5"))
  ```

- `nova/federation/federation_server.py:217`
  ```python
  rate_rps = float(os.getenv("NOVA_FEDERATION_RATE_RPS", "0.5"))
  ```

---

### `NOVA_FEDERATION_REGISTRY`

**Default**: `NO_DEFAULT`

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (1 total):

- `nova/config/federation_config.py:47`
  ```python
  registry_env = os.getenv("NOVA_FEDERATION_REGISTRY")
  ```

---

### `NOVA_FEDERATION_REPLAY_CACHE_SIZE`

**Defaults**: Multiple values found:
  - `4096` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `nova/federation/federation_server.py:214`
  ```python
  replay_cache_size = int(os.getenv("NOVA_FEDERATION_REPLAY_CACHE_SIZE", "4096"))
  ```

- `nova/federation/federation_server.py:214`
  ```python
  replay_cache_size = int(os.getenv("NOVA_FEDERATION_REPLAY_CACHE_SIZE", "4096"))
  ```

- `nova/federation/federation_server.py:214`
  ```python
  replay_cache_size = int(os.getenv("NOVA_FEDERATION_REPLAY_CACHE_SIZE", "4096"))
  ```

---

### `NOVA_FEDERATION_REPLAY_MODE`

**Defaults**: Multiple values found:
  - `NO_DEFAULT` (1 locations)
  - `block` (2 locations)

**Impact**: 🟡 HIGH (Feature Gate)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `nova/federation/federation_server.py:213`
  ```python
  replay_mode = os.getenv("NOVA_FEDERATION_REPLAY_MODE", "block").lower()
  ```

- `nova/federation/federation_server.py:213`
  ```python
  replay_mode = os.getenv("NOVA_FEDERATION_REPLAY_MODE", "block").lower()
  ```

- `nova/federation/federation_server.py:213`
  ```python
  replay_mode = os.getenv("NOVA_FEDERATION_REPLAY_MODE", "block").lower()
  ```

---

### `NOVA_FEDERATION_RETRIES`

**Defaults**: Multiple values found:
  - `2` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `nova/federation/federation_client.py:27`
  ```python
  return int(os.getenv("NOVA_FEDERATION_RETRIES", "2"))
  ```

- `nova/federation/federation_client.py:27`
  ```python
  return int(os.getenv("NOVA_FEDERATION_RETRIES", "2"))
  ```

- `nova/federation/federation_client.py:27`
  ```python
  return int(os.getenv("NOVA_FEDERATION_RETRIES", "2"))
  ```

---

### `NOVA_FEDERATION_SKEW_S`

**Defaults**: Multiple values found:
  - `120` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `nova/federation/federation_server.py:212`
  ```python
  skew_seconds = int(os.getenv("NOVA_FEDERATION_SKEW_S", "120"))
  ```

- `nova/federation/federation_server.py:212`
  ```python
  skew_seconds = int(os.getenv("NOVA_FEDERATION_SKEW_S", "120"))
  ```

- `nova/federation/federation_server.py:212`
  ```python
  skew_seconds = int(os.getenv("NOVA_FEDERATION_SKEW_S", "120"))
  ```

---

### `NOVA_FEDERATION_TRUST_W_AGE`

**Defaults**: Multiple values found:
  - `0.15` (1 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (2 total):

- `nova/federation/trust_model.py:22`
  ```python
  w_age: float = float(os.getenv("NOVA_FEDERATION_TRUST_W_AGE", 0.15)),
  ```

- `nova/federation/trust_model.py:22`
  ```python
  w_age: float = float(os.getenv("NOVA_FEDERATION_TRUST_W_AGE", 0.15)),
  ```

---

### `NOVA_FEDERATION_TRUST_W_CONTINUITY`

**Defaults**: Multiple values found:
  - `0.15` (1 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (2 total):

- `nova/federation/trust_model.py:23`
  ```python
  w_continuity: float = float(os.getenv("NOVA_FEDERATION_TRUST_W_CONTINUITY", 0.15)),
  ```

- `nova/federation/trust_model.py:23`
  ```python
  w_continuity: float = float(os.getenv("NOVA_FEDERATION_TRUST_W_CONTINUITY", 0.15)),
  ```

---

### `NOVA_FEDERATION_TRUST_W_LATENCY`

**Defaults**: Multiple values found:
  - `0.15` (1 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (2 total):

- `nova/federation/trust_model.py:21`
  ```python
  w_latency: float = float(os.getenv("NOVA_FEDERATION_TRUST_W_LATENCY", 0.15)),
  ```

- `nova/federation/trust_model.py:21`
  ```python
  w_latency: float = float(os.getenv("NOVA_FEDERATION_TRUST_W_LATENCY", 0.15)),
  ```

---

### `NOVA_FEDERATION_TRUST_W_VERIFIED`

**Defaults**: Multiple values found:
  - `0.55` (1 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (2 total):

- `nova/federation/trust_model.py:20`
  ```python
  w_verified: float = float(os.getenv("NOVA_FEDERATION_TRUST_W_VERIFIED", 0.55)),
  ```

- `nova/federation/trust_model.py:20`
  ```python
  w_verified: float = float(os.getenv("NOVA_FEDERATION_TRUST_W_VERIFIED", 0.55)),
  ```

---

### `NOVA_FED_FORCE_ERRORS`

**Defaults**: Multiple values found:
  - `0` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `federation_client.py:92`
  ```python
  return os.getenv("NOVA_FED_FORCE_ERRORS", "0").strip() == "1"
  ```

- `federation_client.py:92`
  ```python
  return os.getenv("NOVA_FED_FORCE_ERRORS", "0").strip() == "1"
  ```

- `federation_client.py:92`
  ```python
  return os.getenv("NOVA_FED_FORCE_ERRORS", "0").strip() == "1"
  ```

---

### `NOVA_FED_MIN_GOOD_PEERS`

**Defaults**: Multiple values found:
  - `` (1 locations)
  - `NO_DEFAULT` (2 locations)

**Impact**: 🟡 MEDIUM (Performance)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `federation_poller.py:112`
  ```python
  min_peers_raw = os.getenv("NOVA_FED_MIN_GOOD_PEERS", "").strip()
  ```

- `federation_poller.py:112`
  ```python
  min_peers_raw = os.getenv("NOVA_FED_MIN_GOOD_PEERS", "").strip()
  ```

- `federation_poller.py:112`
  ```python
  min_peers_raw = os.getenv("NOVA_FED_MIN_GOOD_PEERS", "").strip()
  ```

---

### `NOVA_FED_MIN_PEER_QUALITY`

**Defaults**: Multiple values found:
  - `` (1 locations)
  - `NO_DEFAULT` (2 locations)

**Impact**: 🟡 MEDIUM (Performance)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `federation_poller.py:105`
  ```python
  threshold_raw = os.getenv("NOVA_FED_MIN_PEER_QUALITY", "").strip()
  ```

- `federation_poller.py:105`
  ```python
  threshold_raw = os.getenv("NOVA_FED_MIN_PEER_QUALITY", "").strip()
  ```

- `federation_poller.py:105`
  ```python
  threshold_raw = os.getenv("NOVA_FED_MIN_PEER_QUALITY", "").strip()
  ```

---

### `NOVA_FED_MOCK_PEERS`

**Defaults**: Multiple values found:
  - `0` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `nova/config/flags.py:41`
  ```python
  peers_str = os.getenv("NOVA_FED_MOCK_PEERS", "0")
  ```

- `nova/config/flags.py:41`
  ```python
  peers_str = os.getenv("NOVA_FED_MOCK_PEERS", "0")
  ```

- `nova/config/flags.py:41`
  ```python
  peers_str = os.getenv("NOVA_FED_MOCK_PEERS", "0")
  ```

---

### `NOVA_FED_MOCK_STD`

**Defaults**: Multiple values found:
  - `0.15` (4 locations)
  - `NO_DEFAULT` (2 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (6 total):

- `nova/config/flags.py:68`
  ```python
  std_str = os.getenv("NOVA_FED_MOCK_STD", "0.15")
  ```

- `nova/config/flags.py:68`
  ```python
  std_str = os.getenv("NOVA_FED_MOCK_STD", "0.15")
  ```

- `nova/config/flags.py:68`
  ```python
  std_str = os.getenv("NOVA_FED_MOCK_STD", "0.15")
  ```

- `nova/federation/mock_peer_service.py:57`
  ```python
  std_str = os.getenv("NOVA_FED_MOCK_STD", "0.15")
  ```

- `nova/federation/mock_peer_service.py:57`
  ```python
  std_str = os.getenv("NOVA_FED_MOCK_STD", "0.15")
  ```

- `nova/federation/mock_peer_service.py:57`
  ```python
  std_str = os.getenv("NOVA_FED_MOCK_STD", "0.15")
  ```

---

### `NOVA_FED_PEERS`

**Defaults**: Multiple values found:
  - `` (1 locations)
  - `NO_DEFAULT` (2 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `federation_synchronizer.py:186`
  ```python
  self._peers = self._parse_peers(os.getenv("NOVA_FED_PEERS", ""))
  ```

- `federation_synchronizer.py:186`
  ```python
  self._peers = self._parse_peers(os.getenv("NOVA_FED_PEERS", ""))
  ```

- `federation_synchronizer.py:186`
  ```python
  self._peers = self._parse_peers(os.getenv("NOVA_FED_PEERS", ""))
  ```

---

### `NOVA_FED_QUALITY_LAT_CAP_SEC`

**Defaults**: Multiple values found:
  - `` (1 locations)
  - `NO_DEFAULT` (2 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `federation_poller.py:87`
  ```python
  raw_lat_cap = os.getenv("NOVA_FED_QUALITY_LAT_CAP_SEC", "")
  ```

- `federation_poller.py:87`
  ```python
  raw_lat_cap = os.getenv("NOVA_FED_QUALITY_LAT_CAP_SEC", "")
  ```

- `federation_poller.py:87`
  ```python
  raw_lat_cap = os.getenv("NOVA_FED_QUALITY_LAT_CAP_SEC", "")
  ```

---

### `NOVA_FED_QUALITY_TAU_SEC`

**Defaults**: Multiple values found:
  - `` (1 locations)
  - `NO_DEFAULT` (2 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `federation_poller.py:94`
  ```python
  raw_tau = os.getenv("NOVA_FED_QUALITY_TAU_SEC", "")
  ```

- `federation_poller.py:94`
  ```python
  raw_tau = os.getenv("NOVA_FED_QUALITY_TAU_SEC", "")
  ```

- `federation_poller.py:94`
  ```python
  raw_tau = os.getenv("NOVA_FED_QUALITY_TAU_SEC", "")
  ```

---

### `NOVA_FED_SCRAPE_INTERVAL`

**Defaults**: Multiple values found:
  - `` (1 locations)
  - `NO_DEFAULT` (2 locations)

**Impact**: 🟡 MEDIUM (Performance)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `federation_poller.py:19`
  ```python
  raw = os.getenv("NOVA_FED_SCRAPE_INTERVAL", "")
  ```

- `federation_poller.py:19`
  ```python
  raw = os.getenv("NOVA_FED_SCRAPE_INTERVAL", "")
  ```

- `federation_poller.py:19`
  ```python
  raw = os.getenv("NOVA_FED_SCRAPE_INTERVAL", "")
  ```

---

### `NOVA_FED_SCRAPE_MAX_INTERVAL`

**Defaults**: Multiple values found:
  - `NO_DEFAULT` (1 locations)
  - `str(max(_MIN_INTERVAL * 8, _MIN_INTERVAL` (1 locations)

**Impact**: 🟡 MEDIUM (Performance)

**Documentation**: ✅ Documented

**Usage Locations** (2 total):

- `federation_poller.py:38`
  ```python
  _MAX_INTERVAL = float(os.getenv("NOVA_FED_SCRAPE_MAX_INTERVAL", str(max(_MIN_INTERVAL * 8, _MIN_INTERVAL))))
  ```

- `federation_poller.py:38`
  ```python
  _MAX_INTERVAL = float(os.getenv("NOVA_FED_SCRAPE_MAX_INTERVAL", str(max(_MIN_INTERVAL * 8, _MIN_INTERVAL))))
  ```

---

### `NOVA_FED_SCRAPE_TIMEOUT`

**Defaults**: Multiple values found:
  - `` (1 locations)
  - `NO_DEFAULT` (2 locations)

**Impact**: 🟡 MEDIUM (Performance)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `federation_poller.py:27`
  ```python
  raw = os.getenv("NOVA_FED_SCRAPE_TIMEOUT", "")
  ```

- `federation_poller.py:27`
  ```python
  raw = os.getenv("NOVA_FED_SCRAPE_TIMEOUT", "")
  ```

- `federation_poller.py:27`
  ```python
  raw = os.getenv("NOVA_FED_SCRAPE_TIMEOUT", "")
  ```

---

### `NOVA_FED_SYNC_ENABLED`

**Defaults**: Multiple values found:
  - `0` (6 locations)
  - `NO_DEFAULT` (3 locations)

**Impact**: 🟡 HIGH (Feature Gate)

**Documentation**: ✅ Documented

**Usage Locations** (9 total):

- `app.py:350`
  ```python
  peer_sync_enabled = os.getenv("NOVA_FED_SYNC_ENABLED", "0") == "1"
  ```

- `app.py:350`
  ```python
  peer_sync_enabled = os.getenv("NOVA_FED_SYNC_ENABLED", "0") == "1"
  ```

- `app.py:350`
  ```python
  peer_sync_enabled = os.getenv("NOVA_FED_SYNC_ENABLED", "0") == "1"
  ```

- `federation_health.py:111`
  ```python
  sync_enabled = os.getenv("NOVA_FED_SYNC_ENABLED", "0") == "1"
  ```

- `federation_health.py:111`
  ```python
  sync_enabled = os.getenv("NOVA_FED_SYNC_ENABLED", "0") == "1"
  ```

- `federation_health.py:111`
  ```python
  sync_enabled = os.getenv("NOVA_FED_SYNC_ENABLED", "0") == "1"
  ```

- `federation_synchronizer.py:185`
  ```python
  self._enabled = os.getenv("NOVA_FED_SYNC_ENABLED", "0") == "1"
  ```

- `federation_synchronizer.py:185`
  ```python
  self._enabled = os.getenv("NOVA_FED_SYNC_ENABLED", "0") == "1"
  ```

- `federation_synchronizer.py:185`
  ```python
  self._enabled = os.getenv("NOVA_FED_SYNC_ENABLED", "0") == "1"
  ```

---

### `NOVA_FED_SYNC_INTERVAL`

**Defaults**: Multiple values found:
  - `30` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟡 MEDIUM (Performance)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `federation_synchronizer.py:187`
  ```python
  self._interval = float(os.getenv("NOVA_FED_SYNC_INTERVAL", "30"))
  ```

- `federation_synchronizer.py:187`
  ```python
  self._interval = float(os.getenv("NOVA_FED_SYNC_INTERVAL", "30"))
  ```

- `federation_synchronizer.py:187`
  ```python
  self._interval = float(os.getenv("NOVA_FED_SYNC_INTERVAL", "30"))
  ```

---

### `NOVA_FED_SYNC_TIMEOUT`

**Defaults**: Multiple values found:
  - `2.5` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟡 MEDIUM (Performance)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `federation_synchronizer.py:188`
  ```python
  self._timeout = float(os.getenv("NOVA_FED_SYNC_TIMEOUT", "2.5"))
  ```

- `federation_synchronizer.py:188`
  ```python
  self._timeout = float(os.getenv("NOVA_FED_SYNC_TIMEOUT", "2.5"))
  ```

- `federation_synchronizer.py:188`
  ```python
  self._timeout = float(os.getenv("NOVA_FED_SYNC_TIMEOUT", "2.5"))
  ```

---

### `NOVA_FLOW_FABRIC_LAZY_INIT`

**Defaults**: Multiple values found:
  - `1` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `flow_fabric_init.py:122`
  ```python
  if __name__ != "__main__" and os.getenv("NOVA_FLOW_FABRIC_LAZY_INIT", "1") == "0":
  ```

- `flow_fabric_init.py:122`
  ```python
  if __name__ != "__main__" and os.getenv("NOVA_FLOW_FABRIC_LAZY_INIT", "1") == "0":
  ```

- `flow_fabric_init.py:122`
  ```python
  if __name__ != "__main__" and os.getenv("NOVA_FLOW_FABRIC_LAZY_INIT", "1") == "0":
  ```

---

### `NOVA_FLOW_METRICS_ENABLED`

**Defaults**: Multiple values found:
  - `NO_DEFAULT` (2 locations)
  - `str(flow_metrics_enabled` (1 locations)
  - `true` (2 locations)

**Impact**: 🟡 HIGH (Feature Gate)

**Documentation**: ✅ Documented

**Usage Locations** (5 total):

- `config.py:39`
  ```python
  FLOW_METRICS_ENABLED: bool = os.getenv("NOVA_FLOW_METRICS_ENABLED", "true").lower() == "true"
  ```

- `config.py:39`
  ```python
  FLOW_METRICS_ENABLED: bool = os.getenv("NOVA_FLOW_METRICS_ENABLED", "true").lower() == "true"
  ```

- `config.py:39`
  ```python
  FLOW_METRICS_ENABLED: bool = os.getenv("NOVA_FLOW_METRICS_ENABLED", "true").lower() == "true"
  ```

- `flow_fabric_init.py:80`
  ```python
  flow_metrics_enabled = os.getenv("NOVA_FLOW_METRICS_ENABLED", str(flow_metrics_enabled)).lower() == "true"
  ```

- `flow_fabric_init.py:80`
  ```python
  flow_metrics_enabled = os.getenv("NOVA_FLOW_METRICS_ENABLED", str(flow_metrics_enabled)).lower() == "true"
  ```

---

### `NOVA_FLOW_MODE`

**Defaults**: Multiple values found:
  - `BALANCED` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `config.py:40`
  ```python
  FLOW_MODE: str = os.getenv("NOVA_FLOW_MODE", "BALANCED")
  ```

- `config.py:40`
  ```python
  FLOW_MODE: str = os.getenv("NOVA_FLOW_MODE", "BALANCED")
  ```

- `config.py:40`
  ```python
  FLOW_MODE: str = os.getenv("NOVA_FLOW_MODE", "BALANCED")
  ```

---

### `NOVA_GAMMA_ETA_DEFAULT`

**Defaults**: Multiple values found:
  - `0.10` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `nova/governor/adaptive_wisdom.py:74`
  ```python
  eta_default = float(os.getenv("NOVA_GAMMA_ETA_DEFAULT", "0.10"))
  ```

- `nova/governor/adaptive_wisdom.py:74`
  ```python
  eta_default = float(os.getenv("NOVA_GAMMA_ETA_DEFAULT", "0.10"))
  ```

- `nova/governor/adaptive_wisdom.py:74`
  ```python
  eta_default = float(os.getenv("NOVA_GAMMA_ETA_DEFAULT", "0.10"))
  ```

---

### `NOVA_GAMMA_ETA_MAX`

**Defaults**: Multiple values found:
  - `0.15` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟡 MEDIUM (Performance)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `nova/governor/adaptive_wisdom.py:73`
  ```python
  eta_max = float(os.getenv("NOVA_GAMMA_ETA_MAX", "0.15"))
  ```

- `nova/governor/adaptive_wisdom.py:73`
  ```python
  eta_max = float(os.getenv("NOVA_GAMMA_ETA_MAX", "0.15"))
  ```

- `nova/governor/adaptive_wisdom.py:73`
  ```python
  eta_max = float(os.getenv("NOVA_GAMMA_ETA_MAX", "0.15"))
  ```

---

### `NOVA_GAMMA_ETA_MIN`

**Defaults**: Multiple values found:
  - `0.05` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟡 MEDIUM (Performance)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `nova/governor/adaptive_wisdom.py:72`
  ```python
  eta_min = float(os.getenv("NOVA_GAMMA_ETA_MIN", "0.05"))
  ```

- `nova/governor/adaptive_wisdom.py:72`
  ```python
  eta_min = float(os.getenv("NOVA_GAMMA_ETA_MIN", "0.05"))
  ```

- `nova/governor/adaptive_wisdom.py:72`
  ```python
  eta_min = float(os.getenv("NOVA_GAMMA_ETA_MIN", "0.05"))
  ```

---

### `NOVA_GM_ENABLED`

**Defaults**: Multiple values found:
  - `NO_DEFAULT` (1 locations)
  - `false` (2 locations)

**Impact**: 🟡 HIGH (Feature Gate)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `core/__init__.py:62`
  ```python
  if GeometricMemory is not None and os.getenv("NOVA_GM_ENABLED", "false").lower() == "true":
  ```

- `core/__init__.py:62`
  ```python
  if GeometricMemory is not None and os.getenv("NOVA_GM_ENABLED", "false").lower() == "true":
  ```

- `core/__init__.py:62`
  ```python
  if GeometricMemory is not None and os.getenv("NOVA_GM_ENABLED", "false").lower() == "true":
  ```

---

### `NOVA_HOT_RELOAD`

**Default**: `NO_DEFAULT`

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (1 total):

- `nova/slots/config/enhanced_manager.py:158`
  ```python
  env_toggle = os.getenv("NOVA_HOT_RELOAD")  # explicit override
  ```

---

### `NOVA_LEDGER_STATUS_CMD`

**Defaults**: Multiple values found:
  - `` (1 locations)
  - `NO_DEFAULT` (2 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `ledger_reader.py:24`
  ```python
  cmd = os.getenv("NOVA_LEDGER_STATUS_CMD", "").strip()
  ```

- `ledger_reader.py:24`
  ```python
  cmd = os.getenv("NOVA_LEDGER_STATUS_CMD", "").strip()
  ```

- `ledger_reader.py:24`
  ```python
  cmd = os.getenv("NOVA_LEDGER_STATUS_CMD", "").strip()
  ```

---

### `NOVA_LEDGER_STATUS_URL`

**Defaults**: Multiple values found:
  - `` (1 locations)
  - `NO_DEFAULT` (2 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `ledger_reader.py:23`
  ```python
  url = os.getenv("NOVA_LEDGER_STATUS_URL", "").strip()
  ```

- `ledger_reader.py:23`
  ```python
  url = os.getenv("NOVA_LEDGER_STATUS_URL", "").strip()
  ```

- `ledger_reader.py:23`
  ```python
  url = os.getenv("NOVA_LEDGER_STATUS_URL", "").strip()
  ```

---

### `NOVA_LIGHTCLOCK_DEEP`

**Defaults**: Multiple values found:
  - `1` (24 locations)
  - `NO_DEFAULT` (12 locations)

**Impact**: 🟡 MEDIUM (Wide Usage)

**Documentation**: ✅ Documented

**Usage Locations** (36 total):

- `nova/slots/slot09_distortion_protection/ids_policy.py:13`
  ```python
  if os.getenv("NOVA_LIGHTCLOCK_DEEP", "1") == "0":
  ```

- `nova/slots/slot09_distortion_protection/ids_policy.py:13`
  ```python
  if os.getenv("NOVA_LIGHTCLOCK_DEEP", "1") == "0":
  ```

- `nova/slots/slot09_distortion_protection/ids_policy.py:13`
  ```python
  if os.getenv("NOVA_LIGHTCLOCK_DEEP", "1") == "0":
  ```

- `nova/slots/slot09_distortion_protection/health.py:154`
  ```python
  lightclock_deep = os.getenv("NOVA_LIGHTCLOCK_DEEP", "1") == "1"
  ```

- `nova/slots/slot09_distortion_protection/health.py:154`
  ```python
  lightclock_deep = os.getenv("NOVA_LIGHTCLOCK_DEEP", "1") == "1"
  ```

- `nova/slots/slot09_distortion_protection/health.py:154`
  ```python
  lightclock_deep = os.getenv("NOVA_LIGHTCLOCK_DEEP", "1") == "1"
  ```

- `nova/slots/slot08_memory_lock/core/repair_planner.py:40`
  ```python
  if os.getenv("NOVA_LIGHTCLOCK_DEEP", "1") == "0":
  ```

- `nova/slots/slot08_memory_lock/core/repair_planner.py:40`
  ```python
  if os.getenv("NOVA_LIGHTCLOCK_DEEP", "1") == "0":
  ```

- `nova/slots/slot08_memory_lock/core/repair_planner.py:40`
  ```python
  if os.getenv("NOVA_LIGHTCLOCK_DEEP", "1") == "0":
  ```

- `nova/slots/slot06_cultural_synthesis/context_aware_synthesis.py:103`
  ```python
  if os.getenv("NOVA_LIGHTCLOCK_DEEP", "1") == "1":
  ```

*... and 26 more locations*

---

### `NOVA_LIGHTCLOCK_GATING`

**Defaults**: Multiple values found:
  - `1` (6 locations)
  - `NO_DEFAULT` (3 locations)

**Impact**: 🟡 HIGH (Feature Gate)

**Documentation**: ✅ Documented

**Usage Locations** (9 total):

- `nova/slots/slot10_civilizational_deployment/core/factory.py:56`
  ```python
  if os.getenv("NOVA_LIGHTCLOCK_GATING", "1") == "1":
  ```

- `nova/slots/slot10_civilizational_deployment/core/factory.py:56`
  ```python
  if os.getenv("NOVA_LIGHTCLOCK_GATING", "1") == "1":
  ```

- `nova/slots/slot10_civilizational_deployment/core/factory.py:56`
  ```python
  if os.getenv("NOVA_LIGHTCLOCK_GATING", "1") == "1":
  ```

- `nova/slots/slot10_civilizational_deployment/core/factory.py:83`
  ```python
  if os.getenv("NOVA_LIGHTCLOCK_GATING", "1") == "0":
  ```

- `nova/slots/slot10_civilizational_deployment/core/factory.py:83`
  ```python
  if os.getenv("NOVA_LIGHTCLOCK_GATING", "1") == "0":
  ```

- `nova/slots/slot10_civilizational_deployment/core/factory.py:83`
  ```python
  if os.getenv("NOVA_LIGHTCLOCK_GATING", "1") == "0":
  ```

- `nova/slots/slot10_civilizational_deployment/core/lightclock_canary.py:146`
  ```python
  if os.getenv("NOVA_LIGHTCLOCK_GATING", "1") == "0" or gate_result.phase_lock_value is None:
  ```

- `nova/slots/slot10_civilizational_deployment/core/lightclock_canary.py:146`
  ```python
  if os.getenv("NOVA_LIGHTCLOCK_GATING", "1") == "0" or gate_result.phase_lock_value is None:
  ```

- `nova/slots/slot10_civilizational_deployment/core/lightclock_canary.py:146`
  ```python
  if os.getenv("NOVA_LIGHTCLOCK_GATING", "1") == "0" or gate_result.phase_lock_value is None:
  ```

---

### `NOVA_LOG_LEVEL`

**Defaults**: Multiple values found:
  - `INFO` (4 locations)
  - `NO_DEFAULT` (2 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (6 total):

- `nova/slots/slot10_civilizational_deployment/deployer.py:42`
  ```python
  level = os.getenv("NOVA_LOG_LEVEL", "INFO").upper()
  ```

- `nova/slots/slot10_civilizational_deployment/deployer.py:42`
  ```python
  level = os.getenv("NOVA_LOG_LEVEL", "INFO").upper()
  ```

- `nova/slots/slot10_civilizational_deployment/deployer.py:42`
  ```python
  level = os.getenv("NOVA_LOG_LEVEL", "INFO").upper()
  ```

- `core/__init__.py:39`
  ```python
  level = os.getenv("NOVA_LOG_LEVEL", "INFO").upper()
  ```

- `core/__init__.py:39`
  ```python
  level = os.getenv("NOVA_LOG_LEVEL", "INFO").upper()
  ```

- `core/__init__.py:39`
  ```python
  level = os.getenv("NOVA_LOG_LEVEL", "INFO").upper()
  ```

---

### `NOVA_MAX_CONCURRENT_PROCESSES`

**Defaults**: Multiple values found:
  - `12` (1 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟡 MEDIUM (Performance)

**Documentation**: ✅ Documented

**Usage Locations** (2 total):

- `config.py:23`
  ```python
  MAX_CONCURRENT_PROCESSES: int = int(os.getenv("NOVA_MAX_CONCURRENT_PROCESSES", 12))
  ```

- `config.py:23`
  ```python
  MAX_CONCURRENT_PROCESSES: int = int(os.getenv("NOVA_MAX_CONCURRENT_PROCESSES", 12))
  ```

---

### `NOVA_MEMORY_ETHICS_ENABLED`

**Defaults**: Multiple values found:
  - `NO_DEFAULT` (1 locations)
  - `true` (2 locations)

**Impact**: 🟡 HIGH (Feature Gate)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `config.py:24`
  ```python
  MEMORY_ETHICS_ENABLED: bool = os.getenv("NOVA_MEMORY_ETHICS_ENABLED", "true").lower() == "true"
  ```

- `config.py:24`
  ```python
  MEMORY_ETHICS_ENABLED: bool = os.getenv("NOVA_MEMORY_ETHICS_ENABLED", "true").lower() == "true"
  ```

- `config.py:24`
  ```python
  MEMORY_ETHICS_ENABLED: bool = os.getenv("NOVA_MEMORY_ETHICS_ENABLED", "true").lower() == "true"
  ```

---

### `NOVA_META_LENS_ALPHA`

**Defaults**: Multiple values found:
  - `0.5` (1 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟡 MEDIUM (Performance)

**Documentation**: ✅ Documented

**Usage Locations** (2 total):

- `nova/slots/slot02_deltathresh/meta_lens_processor.py:12`
  ```python
  ALPHA = max(0.1, min(1.0, float(os.getenv("META_LENS_ALPHA", os.getenv("NOVA_META_LENS_ALPHA", "0.5")))))
  ```

- `nova/slots/slot02_deltathresh/meta_lens_processor.py:12`
  ```python
  ALPHA = max(0.1, min(1.0, float(os.getenv("META_LENS_ALPHA", os.getenv("NOVA_META_LENS_ALPHA", "0.5")))))
  ```

---

### `NOVA_META_LENS_EPSILON`

**Defaults**: Multiple values found:
  - `0.02` (1 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟡 MEDIUM (Performance)

**Documentation**: ✅ Documented

**Usage Locations** (2 total):

- `nova/slots/slot02_deltathresh/meta_lens_processor.py:13`
  ```python
  EPSILON = max(0.001, min(0.1, float(os.getenv("META_LENS_EPSILON", os.getenv("NOVA_META_LENS_EPSILON", "0.02")))))
  ```

- `nova/slots/slot02_deltathresh/meta_lens_processor.py:13`
  ```python
  EPSILON = max(0.001, min(0.1, float(os.getenv("META_LENS_EPSILON", os.getenv("NOVA_META_LENS_EPSILON", "0.02")))))
  ```

---

### `NOVA_META_LENS_MAX_ITERS`

**Defaults**: Multiple values found:
  - `3` (1 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟡 MEDIUM (Performance)

**Documentation**: ✅ Documented

**Usage Locations** (2 total):

- `nova/slots/slot02_deltathresh/meta_lens_processor.py:11`
  ```python
  MAX_ITERS = max(1, min(10, int(os.getenv("META_LENS_MAX_ITERS", os.getenv("NOVA_META_LENS_MAX_ITERS", "3")))))
  ```

- `nova/slots/slot02_deltathresh/meta_lens_processor.py:11`
  ```python
  MAX_ITERS = max(1, min(10, int(os.getenv("META_LENS_MAX_ITERS", os.getenv("NOVA_META_LENS_MAX_ITERS", "3")))))
  ```

---

### `NOVA_META_LENS_TEST_ENFORCE_REAL`

**Defaults**: Multiple values found:
  - `0` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `nova/slots/slot02_deltathresh/plugin_meta_lens_addition.py:79`
  ```python
  enforce_real = os.getenv("NOVA_META_LENS_TEST_ENFORCE_REAL", "0") in ("1", "true", "TRUE")
  ```

- `nova/slots/slot02_deltathresh/plugin_meta_lens_addition.py:79`
  ```python
  enforce_real = os.getenv("NOVA_META_LENS_TEST_ENFORCE_REAL", "0") in ("1", "true", "TRUE")
  ```

- `nova/slots/slot02_deltathresh/plugin_meta_lens_addition.py:79`
  ```python
  enforce_real = os.getenv("NOVA_META_LENS_TEST_ENFORCE_REAL", "0") in ("1", "true", "TRUE")
  ```

---

### `NOVA_NODE_ID`

**Default**: `NO_DEFAULT`

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (1 total):

- `routes/peer_sync.py:33`
  ```python
  _cached_node_id = os.getenv("NOVA_NODE_ID")
  ```

---

### `NOVA_PHASE_LOCK_GATE`

**Defaults**: Multiple values found:
  - `0.70` (2 locations)
  - `NO_DEFAULT` (2 locations)

**Impact**: 🟡 HIGH (Feature Gate)

**Documentation**: ✅ Documented

**Usage Locations** (4 total):

- `nova/slots/slot10_civilizational_deployment/core/lightclock_gatekeeper.py:40`
  ```python
  self._phase_gate = float(os.getenv("NOVA_PHASE_LOCK_GATE", "0.70"))
  ```

- `nova/slots/slot10_civilizational_deployment/core/lightclock_gatekeeper.py:40`
  ```python
  self._phase_gate = float(os.getenv("NOVA_PHASE_LOCK_GATE", "0.70"))
  ```

- `nova/slots/slot10_civilizational_deployment/core/lightclock_gatekeeper.py:40`
  ```python
  self._phase_gate = float(os.getenv("NOVA_PHASE_LOCK_GATE", "0.70"))
  ```

- `nova/slots/slot10_civilizational_deployment/tests/test_slot10_lightclock_gate.py:25`
  ```python
  os.environ["NOVA_PHASE_LOCK_GATE"] = "0.7"
  ```

---

### `NOVA_PUBLISH_PHASE_LOCK`

**Defaults**: Multiple values found:
  - `1` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `nova/slots/slot07_production_controls/production_control_engine.py:627`
  ```python
  if (os.getenv("NOVA_PUBLISH_PHASE_LOCK", "1") == "1" and
  ```

- `nova/slots/slot07_production_controls/production_control_engine.py:627`
  ```python
  if (os.getenv("NOVA_PUBLISH_PHASE_LOCK", "1") == "1" and
  ```

- `nova/slots/slot07_production_controls/production_control_engine.py:627`
  ```python
  if (os.getenv("NOVA_PUBLISH_PHASE_LOCK", "1") == "1" and
  ```

---

### `NOVA_PUBLISH_TRI`

**Defaults**: Multiple values found:
  - `1` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `nova/slots/slot04_tri/core/tri_engine.py:141`
  ```python
  os.getenv("NOVA_PUBLISH_TRI", "1") == "1" and
  ```

- `nova/slots/slot04_tri/core/tri_engine.py:141`
  ```python
  os.getenv("NOVA_PUBLISH_TRI", "1") == "1" and
  ```

- `nova/slots/slot04_tri/core/tri_engine.py:141`
  ```python
  os.getenv("NOVA_PUBLISH_TRI", "1") == "1" and
  ```

---

### `NOVA_REFLECTION_SECRET`

**Defaults**: Multiple values found:
  - `NO_DEFAULT` (1 locations)
  - `nova-reflection-default-key` (2 locations)

**Impact**: 🔴 CRITICAL (Security)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `reflection.py:196`
  ```python
  secret_key = os.getenv("NOVA_REFLECTION_SECRET", "nova-reflection-default-key")
  ```

- `reflection.py:196`
  ```python
  secret_key = os.getenv("NOVA_REFLECTION_SECRET", "nova-reflection-default-key")
  ```

- `reflection.py:196`
  ```python
  secret_key = os.getenv("NOVA_REFLECTION_SECRET", "nova-reflection-default-key")
  ```

---

### `NOVA_REFLEX_ENABLED`

**Defaults**: Multiple values found:
  - `` (1 locations)
  - `NO_DEFAULT` (4 locations)
  - `false` (4 locations)

**Impact**: 🟡 HIGH (Feature Gate)

**Documentation**: ✅ Documented

**Usage Locations** (9 total):

- `nova/slots/slot07_production_controls/reflex_emitter.py:122`
  ```python
  env_enabled = os.getenv("NOVA_REFLEX_ENABLED", "").lower()
  ```

- `nova/slots/slot07_production_controls/reflex_emitter.py:122`
  ```python
  env_enabled = os.getenv("NOVA_REFLEX_ENABLED", "").lower()
  ```

- `nova/slots/slot07_production_controls/reflex_emitter.py:122`
  ```python
  env_enabled = os.getenv("NOVA_REFLEX_ENABLED", "").lower()
  ```

- `nova/slots/slot07_production_controls/health.py:187`
  ```python
  return os.getenv("NOVA_REFLEX_ENABLED", "false").lower() == "true"
  ```

- `nova/slots/slot07_production_controls/health.py:187`
  ```python
  return os.getenv("NOVA_REFLEX_ENABLED", "false").lower() == "true"
  ```

- `nova/slots/slot07_production_controls/health.py:187`
  ```python
  return os.getenv("NOVA_REFLEX_ENABLED", "false").lower() == "true"
  ```

- `config.py:43`
  ```python
  REFLEX_ENABLED: bool = os.getenv("NOVA_REFLEX_ENABLED", "false").lower() == "true"
  ```

- `config.py:43`
  ```python
  REFLEX_ENABLED: bool = os.getenv("NOVA_REFLEX_ENABLED", "false").lower() == "true"
  ```

- `config.py:43`
  ```python
  REFLEX_ENABLED: bool = os.getenv("NOVA_REFLEX_ENABLED", "false").lower() == "true"
  ```

---

### `NOVA_REFLEX_SHADOW`

**Defaults**: Multiple values found:
  - `` (1 locations)
  - `NO_DEFAULT` (4 locations)
  - `true` (4 locations)

**Impact**: 🟡 MEDIUM (Wide Usage)

**Documentation**: ✅ Documented

**Usage Locations** (9 total):

- `nova/slots/slot07_production_controls/reflex_emitter.py:130`
  ```python
  env_shadow = os.getenv("NOVA_REFLEX_SHADOW", "").lower()
  ```

- `nova/slots/slot07_production_controls/reflex_emitter.py:130`
  ```python
  env_shadow = os.getenv("NOVA_REFLEX_SHADOW", "").lower()
  ```

- `nova/slots/slot07_production_controls/reflex_emitter.py:130`
  ```python
  env_shadow = os.getenv("NOVA_REFLEX_SHADOW", "").lower()
  ```

- `nova/slots/slot07_production_controls/health.py:193`
  ```python
  return os.getenv("NOVA_REFLEX_SHADOW", "true").lower() == "true"
  ```

- `nova/slots/slot07_production_controls/health.py:193`
  ```python
  return os.getenv("NOVA_REFLEX_SHADOW", "true").lower() == "true"
  ```

- `nova/slots/slot07_production_controls/health.py:193`
  ```python
  return os.getenv("NOVA_REFLEX_SHADOW", "true").lower() == "true"
  ```

- `config.py:44`
  ```python
  REFLEX_SHADOW: bool = os.getenv("NOVA_REFLEX_SHADOW", "true").lower() == "true"
  ```

- `config.py:44`
  ```python
  REFLEX_SHADOW: bool = os.getenv("NOVA_REFLEX_SHADOW", "true").lower() == "true"
  ```

- `config.py:44`
  ```python
  REFLEX_SHADOW: bool = os.getenv("NOVA_REFLEX_SHADOW", "true").lower() == "true"
  ```

---

### `NOVA_ROUTER_ERROR_THRESHOLD`

**Defaults**: Multiple values found:
  - `0.2` (1 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (2 total):

- `config.py:29`
  ```python
  ROUTER_ERROR_THRESHOLD: float = float(os.getenv("NOVA_ROUTER_ERROR_THRESHOLD", 0.2))
  ```

- `config.py:29`
  ```python
  ROUTER_ERROR_THRESHOLD: float = float(os.getenv("NOVA_ROUTER_ERROR_THRESHOLD", 0.2))
  ```

---

### `NOVA_ROUTER_LATENCY_MS`

**Defaults**: Multiple values found:
  - `1000.0` (1 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (2 total):

- `config.py:28`
  ```python
  ROUTER_LATENCY_MS: float = float(os.getenv("NOVA_ROUTER_LATENCY_MS", 1000.0))
  ```

- `config.py:28`
  ```python
  ROUTER_LATENCY_MS: float = float(os.getenv("NOVA_ROUTER_LATENCY_MS", 1000.0))
  ```

---

### `NOVA_ROUTER_TIMEOUT_CAP_S`

**Defaults**: Multiple values found:
  - `30.0` (1 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟡 MEDIUM (Performance)

**Documentation**: ✅ Documented

**Usage Locations** (2 total):

- `config.py:31`
  ```python
  ROUTER_TIMEOUT_CAP_S: float = float(os.getenv("NOVA_ROUTER_TIMEOUT_CAP_S", 30.0))
  ```

- `config.py:31`
  ```python
  ROUTER_TIMEOUT_CAP_S: float = float(os.getenv("NOVA_ROUTER_TIMEOUT_CAP_S", 30.0))
  ```

---

### `NOVA_ROUTER_TIMEOUT_MULTIPLIER`

**Defaults**: Multiple values found:
  - `1.5` (1 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟡 MEDIUM (Performance)

**Documentation**: ✅ Documented

**Usage Locations** (2 total):

- `config.py:30`
  ```python
  ROUTER_TIMEOUT_MULTIPLIER: float = float(os.getenv("NOVA_ROUTER_TIMEOUT_MULTIPLIER", 1.5))
  ```

- `config.py:30`
  ```python
  ROUTER_TIMEOUT_MULTIPLIER: float = float(os.getenv("NOVA_ROUTER_TIMEOUT_MULTIPLIER", 1.5))
  ```

---

### `NOVA_SMEEP_INTERVAL`

**Defaults**: Multiple values found:
  - `15` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟡 MEDIUM (Performance)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `app.py:106`
  ```python
  interval = int(os.getenv("NOVA_SMEEP_INTERVAL", "15"))  # seconds
  ```

- `app.py:106`
  ```python
  interval = int(os.getenv("NOVA_SMEEP_INTERVAL", "15"))  # seconds
  ```

- `app.py:106`
  ```python
  interval = int(os.getenv("NOVA_SMEEP_INTERVAL", "15"))  # seconds
  ```

---

### `NOVA_TRI_COHERENCE_HIGH`

**Defaults**: Multiple values found:
  - `0.85` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `nova/slots/slot04_tri/wisdom_feedback.py:39`
  ```python
  high_threshold = float(os.getenv("NOVA_TRI_COHERENCE_HIGH", "0.85"))
  ```

- `nova/slots/slot04_tri/wisdom_feedback.py:39`
  ```python
  high_threshold = float(os.getenv("NOVA_TRI_COHERENCE_HIGH", "0.85"))
  ```

- `nova/slots/slot04_tri/wisdom_feedback.py:39`
  ```python
  high_threshold = float(os.getenv("NOVA_TRI_COHERENCE_HIGH", "0.85"))
  ```

---

### `NOVA_TRI_COHERENCE_LOW`

**Defaults**: Multiple values found:
  - `0.40` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `nova/slots/slot04_tri/wisdom_feedback.py:40`
  ```python
  low_threshold = float(os.getenv("NOVA_TRI_COHERENCE_LOW", "0.40"))
  ```

- `nova/slots/slot04_tri/wisdom_feedback.py:40`
  ```python
  low_threshold = float(os.getenv("NOVA_TRI_COHERENCE_LOW", "0.40"))
  ```

- `nova/slots/slot04_tri/wisdom_feedback.py:40`
  ```python
  low_threshold = float(os.getenv("NOVA_TRI_COHERENCE_LOW", "0.40"))
  ```

---

### `NOVA_TRI_ETA_CAP_ENABLED`

**Defaults**: Multiple values found:
  - `1` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟡 HIGH (Feature Gate)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `adaptive_wisdom_poller.py:315`
  ```python
  if os.getenv("NOVA_TRI_ETA_CAP_ENABLED", "1") == "1":
  ```

- `adaptive_wisdom_poller.py:315`
  ```python
  if os.getenv("NOVA_TRI_ETA_CAP_ENABLED", "1") == "1":
  ```

- `adaptive_wisdom_poller.py:315`
  ```python
  if os.getenv("NOVA_TRI_ETA_CAP_ENABLED", "1") == "1":
  ```

---

### `NOVA_TRI_ETA_CAP_HIGH`

**Defaults**: Multiple values found:
  - `0.18` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `nova/slots/slot04_tri/wisdom_feedback.py:41`
  ```python
  eta_cap_high = float(os.getenv("NOVA_TRI_ETA_CAP_HIGH", "0.18"))
  ```

- `nova/slots/slot04_tri/wisdom_feedback.py:41`
  ```python
  eta_cap_high = float(os.getenv("NOVA_TRI_ETA_CAP_HIGH", "0.18"))
  ```

- `nova/slots/slot04_tri/wisdom_feedback.py:41`
  ```python
  eta_cap_high = float(os.getenv("NOVA_TRI_ETA_CAP_HIGH", "0.18"))
  ```

---

### `NOVA_TRI_ETA_CAP_LOW`

**Defaults**: Multiple values found:
  - `0.08` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `nova/slots/slot04_tri/wisdom_feedback.py:42`
  ```python
  eta_cap_low = float(os.getenv("NOVA_TRI_ETA_CAP_LOW", "0.08"))
  ```

- `nova/slots/slot04_tri/wisdom_feedback.py:42`
  ```python
  eta_cap_low = float(os.getenv("NOVA_TRI_ETA_CAP_LOW", "0.08"))
  ```

- `nova/slots/slot04_tri/wisdom_feedback.py:42`
  ```python
  eta_cap_low = float(os.getenv("NOVA_TRI_ETA_CAP_LOW", "0.08"))
  ```

---

### `NOVA_TRI_GATE`

**Defaults**: Multiple values found:
  - `0.66` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟡 HIGH (Feature Gate)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `nova/slots/slot10_civilizational_deployment/core/lightclock_gatekeeper.py:39`
  ```python
  self._tri_gate = float(os.getenv("NOVA_TRI_GATE", "0.66"))
  ```

- `nova/slots/slot10_civilizational_deployment/core/lightclock_gatekeeper.py:39`
  ```python
  self._tri_gate = float(os.getenv("NOVA_TRI_GATE", "0.66"))
  ```

- `nova/slots/slot10_civilizational_deployment/core/lightclock_gatekeeper.py:39`
  ```python
  self._tri_gate = float(os.getenv("NOVA_TRI_GATE", "0.66"))
  ```

---

### `NOVA_TRUTH_THRESHOLD`

**Defaults**: Multiple values found:
  - `0.87` (1 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (2 total):

- `config.py:10`
  ```python
  TRUTH_THRESHOLD: float = float(os.getenv("NOVA_TRUTH_THRESHOLD", 0.87))
  ```

- `config.py:10`
  ```python
  TRUTH_THRESHOLD: float = float(os.getenv("NOVA_TRUTH_THRESHOLD", 0.87))
  ```

---

### `NOVA_UNLEARN_ANOMALY`

**Defaults**: Multiple values found:
  - `0` (8 locations)
  - `NO_DEFAULT` (4 locations)

**Impact**: 🟡 MEDIUM (Wide Usage)

**Documentation**: ✅ Documented

**Usage Locations** (12 total):

- `app.py:123`
  ```python
  if update_anomaly_inputs and os.getenv("NOVA_UNLEARN_ANOMALY", "0") == "1":
  ```

- `app.py:123`
  ```python
  if update_anomaly_inputs and os.getenv("NOVA_UNLEARN_ANOMALY", "0") == "1":
  ```

- `app.py:123`
  ```python
  if update_anomaly_inputs and os.getenv("NOVA_UNLEARN_ANOMALY", "0") == "1":
  ```

- `reflection.py:123`
  ```python
  "NOVA_UNLEARN_ANOMALY": os.getenv("NOVA_UNLEARN_ANOMALY", "0"),
  ```

- `reflection.py:123`
  ```python
  "NOVA_UNLEARN_ANOMALY": os.getenv("NOVA_UNLEARN_ANOMALY", "0"),
  ```

- `reflection.py:123`
  ```python
  "NOVA_UNLEARN_ANOMALY": os.getenv("NOVA_UNLEARN_ANOMALY", "0"),
  ```

- `unlearn_weighting.py:163`
  ```python
  if os.getenv("NOVA_UNLEARN_ANOMALY", "0") != "1":
  ```

- `unlearn_weighting.py:163`
  ```python
  if os.getenv("NOVA_UNLEARN_ANOMALY", "0") != "1":
  ```

- `unlearn_weighting.py:163`
  ```python
  if os.getenv("NOVA_UNLEARN_ANOMALY", "0") != "1":
  ```

- `unlearn_weighting.py:183`
  ```python
  if os.getenv("NOVA_UNLEARN_ANOMALY", "0") != "1":
  ```

*... and 2 more locations*

---

### `NOVA_UNLEARN_ANOM_ALPHA`

**Defaults**: Multiple values found:
  - `0.30` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `unlearn_weighting.py:22`
  ```python
  ALPHA = float(os.getenv("NOVA_UNLEARN_ANOM_ALPHA", "0.30"))    # EWMA smoothing factor
  ```

- `unlearn_weighting.py:22`
  ```python
  ALPHA = float(os.getenv("NOVA_UNLEARN_ANOM_ALPHA", "0.30"))    # EWMA smoothing factor
  ```

- `unlearn_weighting.py:22`
  ```python
  ALPHA = float(os.getenv("NOVA_UNLEARN_ANOM_ALPHA", "0.30"))    # EWMA smoothing factor
  ```

---

### `NOVA_UNLEARN_ANOM_CAP`

**Defaults**: Multiple values found:
  - `3.00` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟡 MEDIUM (Performance)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `unlearn_weighting.py:26`
  ```python
  CAP = float(os.getenv("NOVA_UNLEARN_ANOM_CAP", "3.00"))        # maximum multiplier
  ```

- `unlearn_weighting.py:26`
  ```python
  CAP = float(os.getenv("NOVA_UNLEARN_ANOM_CAP", "3.00"))        # maximum multiplier
  ```

- `unlearn_weighting.py:26`
  ```python
  CAP = float(os.getenv("NOVA_UNLEARN_ANOM_CAP", "3.00"))        # maximum multiplier
  ```

---

### `NOVA_UNLEARN_ANOM_GAIN`

**Defaults**: Multiple values found:
  - `0.50` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `unlearn_weighting.py:25`
  ```python
  GAIN = float(os.getenv("NOVA_UNLEARN_ANOM_GAIN", "0.50"))      # linear gain above threshold
  ```

- `unlearn_weighting.py:25`
  ```python
  GAIN = float(os.getenv("NOVA_UNLEARN_ANOM_GAIN", "0.50"))      # linear gain above threshold
  ```

- `unlearn_weighting.py:25`
  ```python
  GAIN = float(os.getenv("NOVA_UNLEARN_ANOM_GAIN", "0.50"))      # linear gain above threshold
  ```

---

### `NOVA_UNLEARN_ANOM_MARGIN`

**Defaults**: Multiple values found:
  - `0.20` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `unlearn_weighting.py:24`
  ```python
  MARGIN = float(os.getenv("NOVA_UNLEARN_ANOM_MARGIN", "0.20"))  # hysteresis margin
  ```

- `unlearn_weighting.py:24`
  ```python
  MARGIN = float(os.getenv("NOVA_UNLEARN_ANOM_MARGIN", "0.20"))  # hysteresis margin
  ```

- `unlearn_weighting.py:24`
  ```python
  MARGIN = float(os.getenv("NOVA_UNLEARN_ANOM_MARGIN", "0.20"))  # hysteresis margin
  ```

---

### `NOVA_UNLEARN_ANOM_REQ`

**Defaults**: Multiple values found:
  - `3` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `unlearn_weighting.py:28`
  ```python
  REQ = int(os.getenv("NOVA_UNLEARN_ANOM_REQ", "3"))             # required breaches for engagement
  ```

- `unlearn_weighting.py:28`
  ```python
  REQ = int(os.getenv("NOVA_UNLEARN_ANOM_REQ", "3"))             # required breaches for engagement
  ```

- `unlearn_weighting.py:28`
  ```python
  REQ = int(os.getenv("NOVA_UNLEARN_ANOM_REQ", "3"))             # required breaches for engagement
  ```

---

### `NOVA_UNLEARN_ANOM_TAU`

**Defaults**: Multiple values found:
  - `1.00` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `unlearn_weighting.py:23`
  ```python
  TAU = float(os.getenv("NOVA_UNLEARN_ANOM_TAU", "1.00"))        # engagement threshold
  ```

- `unlearn_weighting.py:23`
  ```python
  TAU = float(os.getenv("NOVA_UNLEARN_ANOM_TAU", "1.00"))        # engagement threshold
  ```

- `unlearn_weighting.py:23`
  ```python
  TAU = float(os.getenv("NOVA_UNLEARN_ANOM_TAU", "1.00"))        # engagement threshold
  ```

---

### `NOVA_UNLEARN_ANOM_WIN`

**Defaults**: Multiple values found:
  - `5` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `unlearn_weighting.py:27`
  ```python
  WIN = int(os.getenv("NOVA_UNLEARN_ANOM_WIN", "5"))             # sliding window size
  ```

- `unlearn_weighting.py:27`
  ```python
  WIN = int(os.getenv("NOVA_UNLEARN_ANOM_WIN", "5"))             # sliding window size
  ```

- `unlearn_weighting.py:27`
  ```python
  WIN = int(os.getenv("NOVA_UNLEARN_ANOM_WIN", "5"))             # sliding window size
  ```

---

### `NOVA_UNLEARN_CANARY`

**Defaults**: Multiple values found:
  - `0` (4 locations)
  - `NO_DEFAULT` (2 locations)

**Impact**: 🟡 HIGH (Feature Gate)

**Documentation**: ✅ Documented

**Usage Locations** (6 total):

- `prometheus_metrics.py:464`
  ```python
  canary_enabled_gauge.set(1.0 if _os.getenv("NOVA_UNLEARN_CANARY", "0") == "1" else 0.0)
  ```

- `prometheus_metrics.py:464`
  ```python
  canary_enabled_gauge.set(1.0 if _os.getenv("NOVA_UNLEARN_CANARY", "0") == "1" else 0.0)
  ```

- `prometheus_metrics.py:464`
  ```python
  canary_enabled_gauge.set(1.0 if _os.getenv("NOVA_UNLEARN_CANARY", "0") == "1" else 0.0)
  ```

- `app.py:175`
  ```python
  if os.getenv("NOVA_UNLEARN_CANARY", "0") != "1":
  ```

- `app.py:175`
  ```python
  if os.getenv("NOVA_UNLEARN_CANARY", "0") != "1":
  ```

- `app.py:175`
  ```python
  if os.getenv("NOVA_UNLEARN_CANARY", "0") != "1":
  ```

---

### `NOVA_UNLEARN_CANARY_AGE`

**Defaults**: Multiple values found:
  - `120` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `app.py:182`
  ```python
  age_after  = float(os.getenv("NOVA_UNLEARN_CANARY_AGE",   "120"))  # age since expiry
  ```

- `app.py:182`
  ```python
  age_after  = float(os.getenv("NOVA_UNLEARN_CANARY_AGE",   "120"))  # age since expiry
  ```

- `app.py:182`
  ```python
  age_after  = float(os.getenv("NOVA_UNLEARN_CANARY_AGE",   "120"))  # age since expiry
  ```

---

### `NOVA_UNLEARN_CANARY_KEY`

**Defaults**: Multiple values found:
  - `NO_DEFAULT` (1 locations)
  - `slot06.cultural_profile` (2 locations)

**Impact**: 🔴 CRITICAL (Security)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `app.py:179`
  ```python
  key        = os.getenv("NOVA_UNLEARN_CANARY_KEY",        "slot06.cultural_profile")
  ```

- `app.py:179`
  ```python
  key        = os.getenv("NOVA_UNLEARN_CANARY_KEY",        "slot06.cultural_profile")
  ```

- `app.py:179`
  ```python
  key        = os.getenv("NOVA_UNLEARN_CANARY_KEY",        "slot06.cultural_profile")
  ```

---

### `NOVA_UNLEARN_CANARY_PERIOD`

**Defaults**: Multiple values found:
  - `3600` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `app.py:174`
  ```python
  period = int(os.getenv("NOVA_UNLEARN_CANARY_PERIOD", "3600"))  # 1h
  ```

- `app.py:174`
  ```python
  period = int(os.getenv("NOVA_UNLEARN_CANARY_PERIOD", "3600"))  # 1h
  ```

- `app.py:174`
  ```python
  period = int(os.getenv("NOVA_UNLEARN_CANARY_PERIOD", "3600"))  # 1h
  ```

---

### `NOVA_UNLEARN_CANARY_PUBLISHER`

**Defaults**: Multiple values found:
  - `NO_DEFAULT` (1 locations)
  - `slot05` (2 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `app.py:180`
  ```python
  publisher  = os.getenv("NOVA_UNLEARN_CANARY_PUBLISHER",  "slot05")
  ```

- `app.py:180`
  ```python
  publisher  = os.getenv("NOVA_UNLEARN_CANARY_PUBLISHER",  "slot05")
  ```

- `app.py:180`
  ```python
  publisher  = os.getenv("NOVA_UNLEARN_CANARY_PUBLISHER",  "slot05")
  ```

---

### `NOVA_UNLEARN_CANARY_TTL`

**Defaults**: Multiple values found:
  - `60` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `app.py:181`
  ```python
  ttl        = float(os.getenv("NOVA_UNLEARN_CANARY_TTL",   "60"))   # >=60s to be eligible
  ```

- `app.py:181`
  ```python
  ttl        = float(os.getenv("NOVA_UNLEARN_CANARY_TTL",   "60"))   # >=60s to be eligible
  ```

- `app.py:181`
  ```python
  ttl        = float(os.getenv("NOVA_UNLEARN_CANARY_TTL",   "60"))   # >=60s to be eligible
  ```

---

### `NOVA_UNLEARN_LOG_BACKUPS`

**Defaults**: Multiple values found:
  - `NO_DEFAULT` (1 locations)
  - `str(backups or 5` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (2 total):

- `app.py:244`
  ```python
  self.backups   = int(os.getenv("NOVA_UNLEARN_LOG_BACKUPS",  str(backups or 5)))
  ```

- `app.py:244`
  ```python
  self.backups   = int(os.getenv("NOVA_UNLEARN_LOG_BACKUPS",  str(backups or 5)))
  ```

---

### `NOVA_UNLEARN_LOG_MAX_BYTES`

**Defaults**: Multiple values found:
  - `NO_DEFAULT` (1 locations)
  - `str(max_bytes or 10 * 1024 * 1024` (1 locations)

**Impact**: 🟡 MEDIUM (Performance)

**Documentation**: ✅ Documented

**Usage Locations** (2 total):

- `app.py:243`
  ```python
  self.max_bytes = int(os.getenv("NOVA_UNLEARN_LOG_MAX_BYTES", str(max_bytes or 10 * 1024 * 1024)))  # 10MB
  ```

- `app.py:243`
  ```python
  self.max_bytes = int(os.getenv("NOVA_UNLEARN_LOG_MAX_BYTES", str(max_bytes or 10 * 1024 * 1024)))  # 10MB
  ```

---

### `NOVA_UNLEARN_MAX_HALF_LIFE`

**Defaults**: Multiple values found:
  - `1800` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟡 MEDIUM (Performance)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `unlearn_weighting.py:202`
  ```python
  max_half_life = float(os.getenv("NOVA_UNLEARN_MAX_HALF_LIFE", "1800"))  # 30 minutes
  ```

- `unlearn_weighting.py:202`
  ```python
  max_half_life = float(os.getenv("NOVA_UNLEARN_MAX_HALF_LIFE", "1800"))  # 30 minutes
  ```

- `unlearn_weighting.py:202`
  ```python
  max_half_life = float(os.getenv("NOVA_UNLEARN_MAX_HALF_LIFE", "1800"))  # 30 minutes
  ```

---

### `NOVA_UNLEARN_MIN_HALF_LIFE`

**Defaults**: Multiple values found:
  - `60` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟡 MEDIUM (Performance)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `unlearn_weighting.py:201`
  ```python
  min_half_life = float(os.getenv("NOVA_UNLEARN_MIN_HALF_LIFE", "60"))    # 1 minute
  ```

- `unlearn_weighting.py:201`
  ```python
  min_half_life = float(os.getenv("NOVA_UNLEARN_MIN_HALF_LIFE", "60"))    # 1 minute
  ```

- `unlearn_weighting.py:201`
  ```python
  min_half_life = float(os.getenv("NOVA_UNLEARN_MIN_HALF_LIFE", "60"))    # 1 minute
  ```

---

### `NOVA_UNLEARN_PULSE_LOG`

**Defaults**: Multiple values found:
  - `1` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `semantic_mirror.py:372`
  ```python
  if os.getenv("NOVA_UNLEARN_PULSE_LOG", "1") == "1":
  ```

- `semantic_mirror.py:372`
  ```python
  if os.getenv("NOVA_UNLEARN_PULSE_LOG", "1") == "1":
  ```

- `semantic_mirror.py:372`
  ```python
  if os.getenv("NOVA_UNLEARN_PULSE_LOG", "1") == "1":
  ```

---

### `NOVA_UNLEARN_PULSE_PATH`

**Defaults**: Multiple values found:
  - `NO_DEFAULT` (1 locations)
  - `logs/unlearn_pulses.ndjson` (2 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `app.py:272`
  ```python
  path = os.getenv("NOVA_UNLEARN_PULSE_PATH", "logs/unlearn_pulses.ndjson")
  ```

- `app.py:272`
  ```python
  path = os.getenv("NOVA_UNLEARN_PULSE_PATH", "logs/unlearn_pulses.ndjson")
  ```

- `app.py:272`
  ```python
  path = os.getenv("NOVA_UNLEARN_PULSE_PATH", "logs/unlearn_pulses.ndjson")
  ```

---

### `NOVA_UNLEARN_W_JITTER`

**Defaults**: Multiple values found:
  - `0.1` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `unlearn_weighting.py:34`
  ```python
  "phase_jitter": float(os.getenv("NOVA_UNLEARN_W_JITTER", "0.1")),
  ```

- `unlearn_weighting.py:34`
  ```python
  "phase_jitter": float(os.getenv("NOVA_UNLEARN_W_JITTER", "0.1")),
  ```

- `unlearn_weighting.py:34`
  ```python
  "phase_jitter": float(os.getenv("NOVA_UNLEARN_W_JITTER", "0.1")),
  ```

---

### `NOVA_UNLEARN_W_PRESS`

**Defaults**: Multiple values found:
  - `0.4` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `unlearn_weighting.py:33`
  ```python
  "system_pressure": float(os.getenv("NOVA_UNLEARN_W_PRESS", "0.4")),
  ```

- `unlearn_weighting.py:33`
  ```python
  "system_pressure": float(os.getenv("NOVA_UNLEARN_W_PRESS", "0.4")),
  ```

- `unlearn_weighting.py:33`
  ```python
  "system_pressure": float(os.getenv("NOVA_UNLEARN_W_PRESS", "0.4")),
  ```

---

### `NOVA_UNLEARN_W_TRI`

**Defaults**: Multiple values found:
  - `0.5` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `unlearn_weighting.py:32`
  ```python
  "tri_drift_z": float(os.getenv("NOVA_UNLEARN_W_TRI", "0.5")),
  ```

- `unlearn_weighting.py:32`
  ```python
  "tri_drift_z": float(os.getenv("NOVA_UNLEARN_W_TRI", "0.5")),
  ```

- `unlearn_weighting.py:32`
  ```python
  "tri_drift_z": float(os.getenv("NOVA_UNLEARN_W_TRI", "0.5")),
  ```

---

### `NOVA_USE_SHARED_HASH`

**Defaults**: Multiple values found:
  - `0` (4 locations)
  - `NO_DEFAULT` (2 locations)

**Impact**: 🟡 HIGH (Feature Gate)

**Documentation**: ✅ Documented

**Usage Locations** (6 total):

- `nova/slots/slot09_distortion_protection/health.py:119`
  ```python
  shared_hash_enabled = os.getenv("NOVA_USE_SHARED_HASH", "0") == "1"
  ```

- `nova/slots/slot09_distortion_protection/health.py:119`
  ```python
  shared_hash_enabled = os.getenv("NOVA_USE_SHARED_HASH", "0") == "1"
  ```

- `nova/slots/slot09_distortion_protection/health.py:119`
  ```python
  shared_hash_enabled = os.getenv("NOVA_USE_SHARED_HASH", "0") == "1"
  ```

- `nova/slots/slot10_civilizational_deployment/health.py:157`
  ```python
  shared_hash_enabled = os.getenv("NOVA_USE_SHARED_HASH", "0") == "1"
  ```

- `nova/slots/slot10_civilizational_deployment/health.py:157`
  ```python
  shared_hash_enabled = os.getenv("NOVA_USE_SHARED_HASH", "0") == "1"
  ```

- `nova/slots/slot10_civilizational_deployment/health.py:157`
  ```python
  shared_hash_enabled = os.getenv("NOVA_USE_SHARED_HASH", "0") == "1"
  ```

---

### `NOVA_VERSION`

**Defaults**: Multiple values found:
  - `16.2` (2 locations)
  - `5.1.1-polish` (4 locations)
  - `NO_DEFAULT` (3 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (9 total):

- `reflection.py:125`
  ```python
  "NOVA_VERSION": os.getenv("NOVA_VERSION", "5.1.1-polish"),
  ```

- `reflection.py:125`
  ```python
  "NOVA_VERSION": os.getenv("NOVA_VERSION", "5.1.1-polish"),
  ```

- `reflection.py:125`
  ```python
  "NOVA_VERSION": os.getenv("NOVA_VERSION", "5.1.1-polish"),
  ```

- `reflection.py:139`
  ```python
  "version": os.getenv("NOVA_VERSION", "5.1.1-polish"),
  ```

- `reflection.py:139`
  ```python
  "version": os.getenv("NOVA_VERSION", "5.1.1-polish"),
  ```

- `reflection.py:139`
  ```python
  "version": os.getenv("NOVA_VERSION", "5.1.1-polish"),
  ```

- `routes/peer_sync.py:85`
  ```python
  version = os.getenv("NOVA_VERSION", "16.2")
  ```

- `routes/peer_sync.py:85`
  ```python
  version = os.getenv("NOVA_VERSION", "16.2")
  ```

- `routes/peer_sync.py:85`
  ```python
  version = os.getenv("NOVA_VERSION", "16.2")
  ```

---

### `NOVA_WISDOM_BACKPRESSURE_ENABLED`

**Defaults**: Multiple values found:
  - `0` (4 locations)
  - `NO_DEFAULT` (2 locations)

**Impact**: 🟡 HIGH (Feature Gate)

**Documentation**: ✅ Documented

**Usage Locations** (6 total):

- `nova/slots/slot07_production_controls/production_control_engine.py:192`
  ```python
  if os.getenv("NOVA_WISDOM_BACKPRESSURE_ENABLED", "0") == "1":
  ```

- `nova/slots/slot07_production_controls/production_control_engine.py:192`
  ```python
  if os.getenv("NOVA_WISDOM_BACKPRESSURE_ENABLED", "0") == "1":
  ```

- `nova/slots/slot07_production_controls/production_control_engine.py:192`
  ```python
  if os.getenv("NOVA_WISDOM_BACKPRESSURE_ENABLED", "0") == "1":
  ```

- `nova/slots/slot07_production_controls/production_control_engine.py:232`
  ```python
  if os.getenv("NOVA_WISDOM_BACKPRESSURE_ENABLED", "0") == "1":
  ```

- `nova/slots/slot07_production_controls/production_control_engine.py:232`
  ```python
  if os.getenv("NOVA_WISDOM_BACKPRESSURE_ENABLED", "0") == "1":
  ```

- `nova/slots/slot07_production_controls/production_control_engine.py:232`
  ```python
  if os.getenv("NOVA_WISDOM_BACKPRESSURE_ENABLED", "0") == "1":
  ```

---

### `NOVA_WISDOM_ETA_DEFAULT`

**Defaults**: Multiple values found:
  - `0.10` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `adaptive_wisdom_poller.py:203`
  ```python
  eta_default = float(os.getenv("NOVA_WISDOM_ETA_DEFAULT", "0.10"))
  ```

- `adaptive_wisdom_poller.py:203`
  ```python
  eta_default = float(os.getenv("NOVA_WISDOM_ETA_DEFAULT", "0.10"))
  ```

- `adaptive_wisdom_poller.py:203`
  ```python
  eta_default = float(os.getenv("NOVA_WISDOM_ETA_DEFAULT", "0.10"))
  ```

---

### `NOVA_WISDOM_ETA_MAX`

**Defaults**: Multiple values found:
  - `0.18` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟡 MEDIUM (Performance)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `adaptive_wisdom_poller.py:202`
  ```python
  eta_max = float(os.getenv("NOVA_WISDOM_ETA_MAX", "0.18"))
  ```

- `adaptive_wisdom_poller.py:202`
  ```python
  eta_max = float(os.getenv("NOVA_WISDOM_ETA_MAX", "0.18"))
  ```

- `adaptive_wisdom_poller.py:202`
  ```python
  eta_max = float(os.getenv("NOVA_WISDOM_ETA_MAX", "0.18"))
  ```

---

### `NOVA_WISDOM_ETA_MIN`

**Defaults**: Multiple values found:
  - `0.05` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟡 MEDIUM (Performance)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `adaptive_wisdom_poller.py:201`
  ```python
  eta_min = float(os.getenv("NOVA_WISDOM_ETA_MIN", "0.05"))
  ```

- `adaptive_wisdom_poller.py:201`
  ```python
  eta_min = float(os.getenv("NOVA_WISDOM_ETA_MIN", "0.05"))
  ```

- `adaptive_wisdom_poller.py:201`
  ```python
  eta_min = float(os.getenv("NOVA_WISDOM_ETA_MIN", "0.05"))
  ```

---

### `NOVA_WISDOM_GOVERNOR_ENABLED`

**Defaults**: Multiple values found:
  - `` (1 locations)
  - `NO_DEFAULT` (3 locations)
  - `false` (2 locations)

**Impact**: 🟡 HIGH (Feature Gate)

**Documentation**: ✅ Documented

**Usage Locations** (6 total):

- `app.py:371`
  ```python
  wisdom_enabled = os.getenv("NOVA_WISDOM_GOVERNOR_ENABLED", "false").strip().lower() in {
  ```

- `app.py:371`
  ```python
  wisdom_enabled = os.getenv("NOVA_WISDOM_GOVERNOR_ENABLED", "false").strip().lower() in {
  ```

- `app.py:371`
  ```python
  wisdom_enabled = os.getenv("NOVA_WISDOM_GOVERNOR_ENABLED", "false").strip().lower() in {
  ```

- `adaptive_wisdom_poller.py:60`
  ```python
  raw = os.getenv("NOVA_WISDOM_GOVERNOR_ENABLED", "").lower()
  ```

- `adaptive_wisdom_poller.py:60`
  ```python
  raw = os.getenv("NOVA_WISDOM_GOVERNOR_ENABLED", "").lower()
  ```

- `adaptive_wisdom_poller.py:60`
  ```python
  raw = os.getenv("NOVA_WISDOM_GOVERNOR_ENABLED", "").lower()
  ```

---

### `NOVA_WISDOM_G_CONTEXT`

**Defaults**: Multiple values found:
  - `NO_DEFAULT` (1 locations)
  - `auto` (2 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `nova/wisdom/generativity_context.py:47`
  ```python
  self._mode = os.getenv("NOVA_WISDOM_G_CONTEXT", "auto").lower()
  ```

- `nova/wisdom/generativity_context.py:47`
  ```python
  self._mode = os.getenv("NOVA_WISDOM_G_CONTEXT", "auto").lower()
  ```

- `nova/wisdom/generativity_context.py:47`
  ```python
  self._mode = os.getenv("NOVA_WISDOM_G_CONTEXT", "auto").lower()
  ```

---

### `NOVA_WISDOM_G_HYSTERESIS_SEC`

**Defaults**: Multiple values found:
  - `120` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `nova/wisdom/generativity_context.py:48`
  ```python
  self._hysteresis_sec = float(os.getenv("NOVA_WISDOM_G_HYSTERESIS_SEC", "120"))
  ```

- `nova/wisdom/generativity_context.py:48`
  ```python
  self._hysteresis_sec = float(os.getenv("NOVA_WISDOM_G_HYSTERESIS_SEC", "120"))
  ```

- `nova/wisdom/generativity_context.py:48`
  ```python
  self._hysteresis_sec = float(os.getenv("NOVA_WISDOM_G_HYSTERESIS_SEC", "120"))
  ```

---

### `NOVA_WISDOM_G_KAPPA`

**Defaults**: Multiple values found:
  - `0.02` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `adaptive_wisdom_poller.py:79`
  ```python
  kappa = float(os.getenv("NOVA_WISDOM_G_KAPPA", "0.02"))
  ```

- `adaptive_wisdom_poller.py:79`
  ```python
  kappa = float(os.getenv("NOVA_WISDOM_G_KAPPA", "0.02"))
  ```

- `adaptive_wisdom_poller.py:79`
  ```python
  kappa = float(os.getenv("NOVA_WISDOM_G_KAPPA", "0.02"))
  ```

---

### `NOVA_WISDOM_G_MIN_H`

**Defaults**: Multiple values found:
  - `0.02` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟡 MEDIUM (Performance)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `adaptive_wisdom_poller.py:87`
  ```python
  min_h = float(os.getenv("NOVA_WISDOM_G_MIN_H", "0.02"))
  ```

- `adaptive_wisdom_poller.py:87`
  ```python
  min_h = float(os.getenv("NOVA_WISDOM_G_MIN_H", "0.02"))
  ```

- `adaptive_wisdom_poller.py:87`
  ```python
  min_h = float(os.getenv("NOVA_WISDOM_G_MIN_H", "0.02"))
  ```

---

### `NOVA_WISDOM_G_MIN_PEERS`

**Defaults**: Multiple values found:
  - `1` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟡 MEDIUM (Performance)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `nova/wisdom/generativity_context.py:49`
  ```python
  self._min_peers = int(os.getenv("NOVA_WISDOM_G_MIN_PEERS", "1"))
  ```

- `nova/wisdom/generativity_context.py:49`
  ```python
  self._min_peers = int(os.getenv("NOVA_WISDOM_G_MIN_PEERS", "1"))
  ```

- `nova/wisdom/generativity_context.py:49`
  ```python
  self._min_peers = int(os.getenv("NOVA_WISDOM_G_MIN_PEERS", "1"))
  ```

---

### `NOVA_WISDOM_G_MIN_S`

**Defaults**: Multiple values found:
  - `0.03` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟡 MEDIUM (Performance)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `adaptive_wisdom_poller.py:86`
  ```python
  min_s = float(os.getenv("NOVA_WISDOM_G_MIN_S", "0.03"))
  ```

- `adaptive_wisdom_poller.py:86`
  ```python
  min_s = float(os.getenv("NOVA_WISDOM_G_MIN_S", "0.03"))
  ```

- `adaptive_wisdom_poller.py:86`
  ```python
  min_s = float(os.getenv("NOVA_WISDOM_G_MIN_S", "0.03"))
  ```

---

### `NOVA_WISDOM_G_TARGET`

**Defaults**: Multiple values found:
  - `0.6` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `adaptive_wisdom_poller.py:78`
  ```python
  g0 = float(os.getenv("NOVA_WISDOM_G_TARGET", "0.6"))
  ```

- `adaptive_wisdom_poller.py:78`
  ```python
  g0 = float(os.getenv("NOVA_WISDOM_G_TARGET", "0.6"))
  ```

- `adaptive_wisdom_poller.py:78`
  ```python
  g0 = float(os.getenv("NOVA_WISDOM_G_TARGET", "0.6"))
  ```

---

### `NOVA_WISDOM_G_WEIGHTS`

**Defaults**: Multiple values found:
  - `0.4,0.3,0.3` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `adaptive_wisdom_poller.py:67`
  ```python
  weights_raw = os.getenv("NOVA_WISDOM_G_WEIGHTS", "0.4,0.3,0.3")
  ```

- `adaptive_wisdom_poller.py:67`
  ```python
  weights_raw = os.getenv("NOVA_WISDOM_G_WEIGHTS", "0.4,0.3,0.3")
  ```

- `adaptive_wisdom_poller.py:67`
  ```python
  weights_raw = os.getenv("NOVA_WISDOM_G_WEIGHTS", "0.4,0.3,0.3")
  ```

---

### `NOVA_WISDOM_HOPF_THRESHOLD`

**Defaults**: Multiple values found:
  - `0.02` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `adaptive_wisdom_poller.py:198`
  ```python
  hopf_threshold=float(os.getenv("NOVA_WISDOM_HOPF_THRESHOLD", "0.02"))
  ```

- `adaptive_wisdom_poller.py:198`
  ```python
  hopf_threshold=float(os.getenv("NOVA_WISDOM_HOPF_THRESHOLD", "0.02"))
  ```

- `adaptive_wisdom_poller.py:198`
  ```python
  hopf_threshold=float(os.getenv("NOVA_WISDOM_HOPF_THRESHOLD", "0.02"))
  ```

---

### `NOVA_WISDOM_KD`

**Defaults**: Multiple values found:
  - `0.15` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `nova/adaptive_wisdom_core.py:55`
  ```python
  k_d=float(os.getenv("NOVA_WISDOM_KD", "0.15")),
  ```

- `nova/adaptive_wisdom_core.py:55`
  ```python
  k_d=float(os.getenv("NOVA_WISDOM_KD", "0.15")),
  ```

- `nova/adaptive_wisdom_core.py:55`
  ```python
  k_d=float(os.getenv("NOVA_WISDOM_KD", "0.15")),
  ```

---

### `NOVA_WISDOM_KP`

**Defaults**: Multiple values found:
  - `0.3` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `nova/adaptive_wisdom_core.py:54`
  ```python
  k_p=float(os.getenv("NOVA_WISDOM_KP", "0.3")),
  ```

- `nova/adaptive_wisdom_core.py:54`
  ```python
  k_p=float(os.getenv("NOVA_WISDOM_KP", "0.3")),
  ```

- `nova/adaptive_wisdom_core.py:54`
  ```python
  k_p=float(os.getenv("NOVA_WISDOM_KP", "0.3")),
  ```

---

### `NOVA_WISDOM_POLL_INTERVAL`

**Defaults**: Multiple values found:
  - `` (1 locations)
  - `NO_DEFAULT` (2 locations)

**Impact**: 🟡 MEDIUM (Performance)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `adaptive_wisdom_poller.py:51`
  ```python
  raw = os.getenv("NOVA_WISDOM_POLL_INTERVAL", "")
  ```

- `adaptive_wisdom_poller.py:51`
  ```python
  raw = os.getenv("NOVA_WISDOM_POLL_INTERVAL", "")
  ```

- `adaptive_wisdom_poller.py:51`
  ```python
  raw = os.getenv("NOVA_WISDOM_POLL_INTERVAL", "")
  ```

---

### `NOVA_WISDOM_Q`

**Defaults**: Multiple values found:
  - `0.7` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `nova/adaptive_wisdom_core.py:50`
  ```python
  Q=float(os.getenv("NOVA_WISDOM_Q", "0.7")),
  ```

- `nova/adaptive_wisdom_core.py:50`
  ```python
  Q=float(os.getenv("NOVA_WISDOM_Q", "0.7")),
  ```

- `nova/adaptive_wisdom_core.py:50`
  ```python
  Q=float(os.getenv("NOVA_WISDOM_Q", "0.7")),
  ```

---

### `NOVA_WISDOM_S_REF`

**Defaults**: Multiple values found:
  - `0.05` (2 locations)
  - `NO_DEFAULT` (1 locations)

**Impact**: 🟢 LOW (Limited Scope)

**Documentation**: ✅ Documented

**Usage Locations** (3 total):

- `nova/adaptive_wisdom_core.py:51`
  ```python
  S_ref=float(os.getenv("NOVA_WISDOM_S_REF", "0.05")),
  ```

- `nova/adaptive_wisdom_core.py:51`
  ```python
  S_ref=float(os.getenv("NOVA_WISDOM_S_REF", "0.05")),
  ```

- `nova/adaptive_wisdom_core.py:51`
  ```python
  S_ref=float(os.getenv("NOVA_WISDOM_S_REF", "0.05")),
  ```

---
