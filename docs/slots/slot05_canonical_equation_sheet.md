# Slot 05 Canonical Equation Sheet

Source anchors:
- `src/nova/slots/slot05_constellation/constellation_engine.py`
- `src/nova/slots/slot05_constellation/adaptive_processor.py`
- `src/nova/slots/slot05_constellation/enhanced_constellation_engine.py`
- `src/nova/slots/slot05_constellation/plugin.py`
- `src/nova/orchestrator/adapters/slot5_constellation.py`
- `src/nova/orchestrator/adapters/enhanced_slot5_constellation.py`

## 1. Runtime Branching

```text
base map(items):
  if empty -> fixed empty stable output
  else -> nodes + links + stability + history update

TRI weighting:
  if NOVA_LIGHTCLOCK_DEEP=0 -> disabled
  else mirror -> env -> default coherence=0.7

TRI position APIs:
  get_current_position/update_from_tri active only if NOVA_ENABLE_TRI_LINK=1
```

## 2. Core Node/Link Math

### 2.1 Node weight

```text
base_weight = min(1, len(item_lower_stripped)/100)
weight_modifier = 0.9 + 0.1*coherence
jitter_penalty = max(0, 1-phase_jitter)
adjusted_weight = base_weight * weight_modifier * jitter_penalty
```

### 2.2 Complexity

```text
complexity = min(1, (word_count/20 + unique_chars/26 + comma_count/10 + open_paren_count/5)/4)
```

### 2.3 Position (circle layout)

```text
angle = 2*pi*i/N
x = 0.5 + 0.3*cos(angle)
y = 0.5 + 0.3*sin(angle)
```

(`N=1` -> `(0.5,0.5)`)

### 2.4 Similarity

```text
jaccard = |W1∩W2|/|W1∪W2|
char_similarity = |C1∩C2|/|C1∪C2|
len_similarity = 1 - |len1-len2|/max(len1,len2,1)

similarity = min(1, 0.5*jaccard + 0.3*char_similarity + 0.2*len_similarity)
```

Link rule:

```text
create link iff similarity >= similarity_threshold
```

## 3. Stability Math

Population variance:

```text
var(x) = mean((x-mean(x))^2)
```

### 3.1 Base stability

```text
weight_stability = 1 - min(1, var(node_weights))

strength_stability =
  1 - min(1, var(link_strengths))   if links exist
  0.8                               otherwise

position_stability =
  max(0, 1-var(pairwise_distances)) * min(1, mean(pairwise_distances)/0.5)

base_stability = mean([weight_stability, strength_stability, position_stability])
```

### 3.2 Derived metrics

```text
density = link_count / max(1, n*(n-1)/2)

connectivity = 1 - (components-1)/max(1, n-1)

distribution_stability = max(0, 1-var(type_shares))

link_stability = 0.7*mean(link_strengths) + 0.3*(1-var(link_strengths))

structure_balance = max(0, 1-var(node_degrees)/max(1,max_degree))
```

### 3.3 Status bands

```text
score >= 0.8 -> stable
score >= 0.6 -> moderate
score >= 0.4 -> unstable
else         -> critical
```

### 3.4 Trend

```text
recent = last up to 5 stability scores
change_rate = (recent[-1]-recent[0]) / len(recent)

trend:
  stable     if |change_rate| < 0.01
  improving  if change_rate > 0
  declining  otherwise

confidence = min(1, len(recent)/5)
```

## 4. TRI->Constellation Update Math

### 4.1 TRI influence

```text
base_influence = tri_score*0.3
layer_variance = var([structural, semantic, expression])
consistency_bonus = (1-layer_variance)*0.2
tri_influence = min(0.5, base_influence + consistency_bonus)
```

### 4.2 Coordinate blend

```text
new_coord = clamp(current_coord*(1-tri_influence) + tri_layer*tri_influence, 0, 1)
```

### 4.3 Stability blend

```text
tri_stability_factor = 1 - 0.5*abs(tri_score-0.5)
new_stability = base_stability * (0.7 + 0.3*tri_stability_factor)
stability_index = clamp(new_stability, 0, 1)
```

### 4.4 History-derived position

```text
x = min(1, constellation_size/20)
y = min(1, link_count/50)
z = stability_score
```

## 5. Adaptive Processor Math (Processual)

### 5.1 Heuristic deltas

```text
if sparse: similarity -= 0.05, link_strength -= 0.03
if dense:  similarity += 0.05, link_strength += 0.03

if complex: stability_window += 3
if simple:  stability_window -= 2

if stability_score < 0.5: similarity -= 0.02, stability_window += 2
if stability_score > 0.8: similarity += 0.02, stability_window -= 1
```

### 5.2 History learning

```text
corr = cov(threshold_series, stability_series)/(std_x*std_y)
target = 0.8
gap = target - current_stability

if current_stability < target:
  delta = +learning_rate*gap   if corr > 0
  delta = -learning_rate*gap   otherwise
else:
  delta = 0
```

Window delta by historical average stability:

```text
avg_stability < 0.6 -> +2
avg_stability > 0.9 -> -1
else                -> 0
```

### 5.3 Bounds

```text
similarity       in [0.1, 0.8]
link_strength    in [0.05, 0.6]
stability_window in [3, 50]  (int)
```

## 6. Enhanced Wrapper Metrics

```text
processing_efficiency = item_count / max(0.001, processing_time)
quality_score = 0.5*stability_score + 0.3*connectivity + 0.2*density
```

## 7. Plugin Contract Math (`CONSTELLATION_STATE@1`)

```text
pattern_stability = clamp(1 - 0.1*len(patterns), 0, 1)
stability_index = clamp(0.7*tri_score + 0.3*pattern_stability, 0, 1)
constellation_state = "stable" if stability_index > 0.6 else "unstable"
```
