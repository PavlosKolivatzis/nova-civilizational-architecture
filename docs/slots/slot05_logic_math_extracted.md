# Slot 05 Logic and Math Extraction

This document extracts Slot 05 behavior from implementation code in:
- `src/nova/slots/slot05_constellation/constellation_engine.py`
- `src/nova/slots/slot05_constellation/enhanced_constellation_engine.py`
- `src/nova/slots/slot05_constellation/adaptive_processor.py`
- `src/nova/orchestrator/adapters/slot5_constellation.py`
- `src/nova/orchestrator/adapters/enhanced_slot5_constellation.py`
- `src/nova/slots/slot05_constellation/plugin.py`

Historical cross-check from `archive/NOVA_HISTORY.md`:
- `d87030f`: "Enhanced ConstellationEngine"
- `8ff7b37`: "shared infra, gated TRI->Constellation ..."

## 1. Runtime Logic

### 1.1 Base Slot05 pipeline (`ConstellationEngine.map`)
For non-empty `items`, Slot05 executes:

1. Build constellation nodes (`_create_constellation_mapping`).
2. Compute pairwise links (`_compute_links`).
3. Compute stability package (`_calculate_stability_metrics`).
4. Append history entry (`_update_history`).
5. Return:
   - `constellation`
   - `links`
   - `stability`
   - `metadata` (`item_count`, `link_count`, version)

Empty input is a hardcoded stable empty result:
- `constellation=[]`
- `links=[]`
- `stability.score=1.0`, `stability.status="empty"`

### 1.2 TRI signal ingestion and fallback chain
Node weighting reads Slot04 TRI signals in this order:

1. If `NOVA_LIGHTCLOCK_DEEP=0` -> TRI signals disabled (`None`).
2. Semantic Mirror keys:
   - `slot04.coherence`
   - `slot04.phase_jitter`
3. Env fallback:
   - `TRI_COHERENCE`
   - `TRI_PHASE_JITTER`
4. Conservative default:
   - `{"coherence": 0.7}`

### 1.3 TRI-gated state APIs
`NOVA_ENABLE_TRI_LINK` gates two Slot05 APIs:

- `get_current_position()`:
  - disabled -> zero vector + `disabled=True`
  - enabled -> history-derived position.

- `update_from_tri(tri_score, layer_scores)`:
  - disabled -> zero vector + `disabled=True`
  - enabled -> blend current position with TRI layers, update TRI-influenced history.

### 1.4 Adapter logic (orchestrator)
- Standard adapter (`slot5_constellation.py`):
  - routes `map(items)` to base engine
  - returns structured unavailable/error fallbacks on failure.
- Enhanced adapter (`enhanced_slot5_constellation.py`):
  - prefers enhanced engine (`EnhancedConstellationEngine`)
  - falls back to base engine if enhanced import fails
  - exposes adaptive metrics/config/reset/cross-slot coordination.

### 1.5 Enhanced processual path
`EnhancedConstellationEngine.map(items, context)`:
1. Infer context when absent.
2. Pull adaptive thresholds from `AdaptiveProcessor`.
3. Apply thresholds to base engine.
4. Run base map.
5. Compute performance metrics.
6. Adapt thresholds from context + performance feedback.
7. Add `adaptive` block to result and publish coordination event (best effort).

## 2. Base Slot05 Math (`constellation_engine.py`)

### 2.1 Item type + weight logic
Type is keyword-routed in priority order:
- `problem` if contains any of: `error|fail|bug|issue`
- else `solution` if `solution|fix|resolve|answer`
- else `process` if `process|method|approach|way`
- else `data` if `data|metric|value|number`
- else `concept`

Base weight:

```text
base_weight = min(1.0, len(lower_stripped_item)/100.0)
```

TRI-adjusted weight (if TRI signals available):

```text
weight_modifier = 0.9 + 0.1*coherence
jitter_penalty  = max(0.0, 1.0 - phase_jitter)
adjusted_weight = base_weight * weight_modifier * jitter_penalty
```

Annotation `stable` is:

```text
stable = (phase_jitter < TRI_JITTER_STABLE)
```

Default `TRI_JITTER_STABLE=0.3`.

### 2.2 Complexity score

```text
f1 = word_count/20
f2 = unique_chars/26
f3 = comma_count/10
f4 = open_paren_count/5
complexity = min(1.0, (f1+f2+f3+f4)/4)
```

### 2.3 Constellation position layout
For node index `i` among `N`:

```text
angle  = 2*pi*i/N
radius = 0.3
x = 0.5 + radius*cos(angle)
y = 0.5 + radius*sin(angle)
```

For `N=1`: `(x,y)=(0.5,0.5)`.

### 2.4 Similarity and link creation
Pairwise link candidate score:

```text
jaccard        = |W1 ∩ W2| / |W1 ∪ W2|
char_similarity= |C1 ∩ C2| / |C1 ∪ C2|
len_similarity = 1 - |len1-len2| / max(len1,len2,1)

similarity = min(1.0, 0.5*jaccard + 0.3*char_similarity + 0.2*len_similarity)
```

Link exists iff:

```text
similarity >= similarity_threshold
```

Default `similarity_threshold=0.3`.

### 2.5 Base stability score
Base stability is average of three factors:

1. Weight stability:

```text
var_w = variance(node_weights)
weight_stability = 1 - min(1, var_w)
```

2. Link-strength stability:

```text
if links:
  var_s = variance(link_strengths)
  strength_stability = 1 - min(1, var_s)
else:
  strength_stability = 0.8
```

3. Position stability:

```text
distances = pairwise euclidean distances between node positions
mean_d = mean(distances)
var_d  = variance(distances)

position_stability = max(0, 1-var_d) * min(1, mean_d/0.5)
```

Then:

```text
base_stability = mean([weight_stability, strength_stability, position_stability])
```

Variance function used is population variance:

```text
variance(values) = mean((x-mean(values))^2)
```

### 2.6 Additional stability metrics
Density:

```text
density = link_count / max(1, n*(n-1)/2)
```

Connectivity (via connected components count `k`):

```text
connectivity = 1 - (k-1)/max(1, n-1)
```

Distribution stability (type-balance):

```text
type_shares = [count_t / n]
distribution_stability = max(0, 1 - variance(type_shares))
```

Link stability:

```text
mean_strength = mean(link_strengths)
var_strength  = variance(link_strengths)
link_stability = 0.7*mean_strength + 0.3*(1-var_strength)
```

Structure balance:

```text
degree_i = link incidence counts
var_deg = variance(degree_i)
structure_balance = max(0, 1 - var_deg/max(1, max_degree))
```

### 2.7 Stability status thresholds

```text
score >= 0.8 -> "stable"
score >= 0.6 -> "moderate"
score >= 0.4 -> "unstable"
else         -> "critical"
```

### 2.8 Historical trend math
From last up-to-5 history scores:

```text
change_rate = (last_score - first_score) / len(recent_scores)
```

Trend classification:

```text
|change_rate| < 0.01 -> stable
change_rate > 0      -> improving
else                 -> declining
```

Confidence:

```text
confidence = min(1.0, len(recent_scores)/5)
```

### 2.9 TRI-linked constellation update math
Influence magnitude:

```text
base_influence = tri_score * 0.3
layer_values = [structural, semantic, expression]
layer_variance = variance(layer_values)
consistency_bonus = (1 - layer_variance) * 0.2
tri_influence = min(0.5, base_influence + consistency_bonus)
```

Coordinate blending:

```text
new_coord = clamp(current_coord*(1-tri_influence) + tri_layer*tri_influence, 0, 1)
```

Stability update:

```text
tri_stability_factor = 1 - 0.5*abs(tri_score - 0.5)
new_stability = base_stability * (0.7 + 0.3*tri_stability_factor)
stability_index = clamp(new_stability, 0, 1)
```

### 2.10 Current position from history
If enabled and history exists:

```text
x = min(1.0, constellation_size/20.0)
y = min(1.0, link_count/50.0)
z = stability_score
```

## 3. Processual Adaptive Math (`adaptive_processor.py` + enhanced engine)

### 3.1 Context-signature discretization
Signature factors:
- data volume: `sparse` (`<5`), `moderate`, `dense` (`>20`)
- complexity: `simple` (`<0.3`), `balanced`, `complex` (`>0.7`)
- `stability_{requirement}`
- `time_{constraint}`

### 3.2 Heuristic adjustments (new/low-history contexts)
Initial context-driven deltas:

```text
if sparse: similarity -= 0.05, link_strength -= 0.03
if dense:  similarity += 0.05, link_strength += 0.03

if complex: stability_window += 3
if simple:  stability_window -= 2
```

Performance modifiers:

```text
if stability_score < 0.5:
  similarity -= 0.02
  stability_window += 2
elif stability_score > 0.8:
  similarity += 0.02
  stability_window -= 1
```

### 3.3 History-driven learning adjustments
Used when context history length `>= 3`.

Pearson correlation for each threshold series vs stability series:

```text
corr = cov(x,y) / (std(x)*std(y))
```

Target stability is fixed:

```text
target_performance = 0.8
gap = target_performance - current_stability
```

For `similarity` and `link_strength`:

```text
if current_stability < target:
  if corr > 0: delta = +learning_rate*gap
  else:        delta = -learning_rate*gap
else:
  delta = 0
```

Stability-window adjustment from historical average stability:

```text
avg_stability < 0.6 -> +2
avg_stability > 0.9 -> -1
else                -> 0
```

### 3.4 Bounds enforcement

```text
similarity       in [0.1, 0.8]
link_strength    in [0.05, 0.6]
stability_window in [3, 50]   (int)
```

### 3.5 Enhanced performance metrics math
From enhanced wrapper:

```text
processing_efficiency = item_count / max(0.001, processing_time)
quality_score = 0.5*stability_score + 0.3*connectivity + 0.2*density
```

## 4. Plugin Contract Math (`plugin.py`)

For `CONSTELLATION_STATE@1` adapter:

```text
pattern_stability = clamp(1 - 0.1*len(patterns_detected), 0, 1)
stability_index = clamp(0.7*tri_score + 0.3*pattern_stability, 0, 1)
constellation_state = "stable" if stability_index > 0.6 else "unstable"
```

## 5. Feature Gates and Defaults

### 5.1 Flags affecting Slot05 behavior
- `NOVA_LIGHTCLOCK_DEEP`
  - `0` disables TRI coherence/jitter weighting in item analysis.
- `NOVA_ENABLE_TRI_LINK`
  - `1` enables `get_current_position` and `update_from_tri` non-stub behavior.

### 5.2 Core defaults
- `similarity_threshold=0.3`
- `stability_window=10`
- `link_strength_threshold=0.2`

Implementation note:
- `link_strength_threshold` is currently configurable/exposed but not directly used in base link creation logic (links are filtered by `similarity_threshold`).

## 6. What Slot05 Math Is in Practice

Slot05 is a deterministic, heuristic graph-construction + stability-scoring system with:
- weighted lexical similarity,
- geometry-based node placement,
- variance/connectivity-derived stability metrics,
- optional TRI-driven weighting and coordinate blending,
- optional processual adaptive threshold control loop.

It is not an ML-optimized latent-space model in current implementation.
