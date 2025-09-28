# Slot 6: Cultural Synthesis Engine

## Status: Production Ready ✅ (v7.5.0 - Phase 4)
**Maturity Level**: 90% - Flow mesh consumer with anomaly-aware unlearning

Cultural adaptation and guardrail validation engine with TRI integration, system context awareness, and **Phase 4 anomaly-aware pulse weighting**. **Downstream consumer of Nova's flow mesh architecture.**

---

## 🎯 Core Functions
- **Cultural Synthesis**: Multi-dimensional cultural profile analysis and synthesis
- **Guardrail Validation**: Deployment approval/transformation/blocking decisions
- **TRI Processing**: Truth Resonance Index score integration from flow mesh
- **Context Awareness**: System-wide context integration via Semantic Mirror
- **Principle Preservation**: Core value protection during cultural adaptation
- **Risk Assessment**: Residual risk calculation and mitigation
- **🆕 Anomaly-Aware Unlearning**: Phase 4 intelligent pulse weight decay with anomaly multipliers

---

## 🏗️ Architecture

### **Core Components**
- **`CulturalSynthesisEngine`**: Main synthesis calculation engine (219 lines)
- **`ContextAwareCulturalSynthesis`**: System context integration (367 lines)
- **`CulturalSynthesisAdapter`**: Slot integration and validation (194 lines)
- **`MulticulturalTruthSynthesis`**: Legacy synthesis implementation (125 lines)
- **🆕 `receiver.py`**: Phase 4 unlearn pulse processing with anomaly weighting (79 lines)
- **Health Monitoring**: System health and metrics collection (77 lines)

### **Files Overview**
```
engine.py                       (219 lines) - Core synthesis calculations
context_aware_synthesis.py      (367 lines) - System context awareness
adapter.py                      (194 lines) - Slot integration adapter
legacy_engine.py                (595 lines) - Legacy implementation
multicultural_truth_synthesis.py (125 lines) - Legacy wrapper
receiver.py                     (79 lines)  - Phase 4 unlearn pulse receiver
health/__init__.py              (77 lines)  - Health monitoring
plugin.py                       (98 lines)  - Plugin interface
shadow_delta.py                 (70 lines)  - Shadow analysis
serializers.py                  (19 lines)  - Data serialization
usage_example.py                (23 lines)  - Usage examples
__init__.py                     (20 lines)  - Module exports
```

**Total**: 12 Python files, 1,886 lines of cultural synthesis logic

---

## 🔗 Flow Mesh Connections & Integration

### **🔄 FLOW MESH CONSUMER**

**Flow Mesh Position:**
```
Slot4 (TRI) ↔ Slot5 (Constellation) → Slot6 (Cultural) → Slot10 (Deployment)
```

#### **Integration Role:**
- **Position**: **Downstream consumer** of flow mesh outputs
- **Function**: Receives TRI scores and layer analysis from upstream flow mesh
- **Coordination**: Provides cultural validation to deployment decisions
- **Context**: System-wide awareness via Semantic Mirror integration

#### **TRI Integration Methods:**
```python
# TRI score processing (consumer pattern)
def synthesize(self, profile: CulturalProfile) -> Dict[str, Any]:
    """Process cultural profile with TRI scores"""

    # Extract TRI data from upstream flow mesh
    tri_score = profile.get("tri_score", 1.0)
    layer_scores = profile.get("layer_scores", {})

    # Calculate cultural metrics
    adaptation = self._score_adaptation(clarity, foresight, empiricism)
    principle = self._principle_preservation(anchor_confidence, tri_score)
    risk = self._residual_risk(layer_scores, tri_score)
```

#### **System Context Integration:**
```python
# Semantic Mirror integration for system awareness
system_context = self.semantic_mirror.get_context("slot07.pressure_level")
breaker_state = self.semantic_mirror.get_context("slot07.breaker_state")

# Apply context-aware adaptations
if system_context.production_pressure > 0.8:
    # Reduce synthesis complexity during system pressure
    adapted_results = self._reduce_synthesis_complexity(results)
```

### **Orchestrator Integration**
- **Adapter**: Available via `orchestrator.slot6`
- **Status**: Active and operational in Nova orchestrator
- **Contracts**: `CULTURAL_PROFILE@1` production contract

### **Prometheus Metrics**
- **Decision Tracking**: Approval/transformation/blocking metrics
- **Performance Metrics**: Synthesis timing and throughput
- **Risk Assessment**: Residual risk and principle preservation tracking
- **🆕 Phase 4 Unlearn Metrics**: Decay events, decay amounts, pulse processing

---

## 📊 API Contracts & Usage

### **Meta.yaml Contracts**
- **`CULTURAL_PROFILE@1`**: Core cultural synthesis (production stability)
- **Consumes**: `TRI_REPORT@1` from upstream flow mesh
- **Provides**: Cultural validation for deployment decisions

### **Core Cultural Synthesis API**
```python
from slots.slot06_cultural_synthesis.engine import CulturalSynthesisEngine

# Initialize synthesis engine
engine = CulturalSynthesisEngine()

# Basic cultural synthesis
profile = {
    "clarity": 0.8,
    "foresight": 0.7,
    "empiricism": 0.9,
    "anchor_confidence": 0.85,
    "tri_score": 0.8,          # From flow mesh
    "layer_scores": {"default": 0.75},
    "ideology_push": False
}

metrics = engine.synthesize(profile)
print(f"Adaptation effectiveness: {metrics['adaptation_effectiveness']}")
print(f"Principle preservation: {metrics['principle_preservation_score']}")
print(f"Residual risk: {metrics['residual_risk']}")
```

### **Context-Aware Synthesis**
```python
from slots.slot06_cultural_synthesis.context_aware_synthesis import get_context_aware_synthesis

# Context-aware cultural synthesis
context_engine = get_context_aware_synthesis()

# Synthesis with system context awareness
results = context_engine.synthesize_with_context(
    cultural_profile=profile,
    institution_data={"type": "educational", "region": "EU"}
)

# Check for system pressure adaptations
if results["_context"]["adaptations_applied"]:
    print(f"System adaptations: {results['_context']['adaptations_applied']}")
```

### **Guardrail Validation**
```python
from slots.slot06_cultural_synthesis.adapter import CulturalSynthesisAdapter

# Guardrail validation for deployment
adapter = CulturalSynthesisAdapter(engine)

validation = adapter.validate_cultural_deployment(
    profile=profile,
    institution_type="educational",
    payload={"content": "Content to validate"},
    slot2_result=slot2_processing_result
)

if validation.result == DeploymentGuardrailResult.APPROVED:
    print("✅ Content approved for deployment")
elif validation.result == DeploymentGuardrailResult.REQUIRES_TRANSFORMATION:
    print("⚠️ Content requires transformation")
elif validation.result == DeploymentGuardrailResult.BLOCKED_PRINCIPLE_VIOLATION:
    print("❌ Content blocked - principle violation")
```

### **Phase 4 Unlearn Pulse Receiver**
```python
from slots.slot06_cultural_synthesis.receiver import register_slot06_receiver, get_pulse_metrics

# Register Slot06 as unlearn pulse receiver
register_slot06_receiver()

# Monitor unlearn pulse processing
metrics = get_pulse_metrics()
print(f"Pulse count: {metrics['pulse_count']}")
print(f"Time since last pulse: {metrics['time_since_last']:.1f}s")
```

### **Health Monitoring**
```python
# Cultural synthesis health check
{
    "principle_preservation_score": 0.85,
    "residual_risk": 0.15,
    "adaptation_effectiveness": 0.80,
    "engine_status": "operational",
    "context_awareness": "active",
    "system_pressure": 0.3,
    "unlearn_decay_events": 42,
    "unlearn_decay_amount": 12.34
}
```

---

## 🔧 Configuration & Operational Modes

### **Synthesis Configuration**
- **Cultural Methods**: Weighted cultural reasoning approaches
- **Ideology Penalty**: Penalty factor for ideological push detection
- **TRI Thresholds**: Minimum TRI score requirements
- **Risk Thresholds**: Residual risk blocking/transformation limits

### **Context Awareness**
- **System Pressure**: Automatic complexity reduction during high load
- **Circuit Breaker**: Conservative mode during system instability
- **Resource Optimization**: Adaptive caching during resource constraints
- **Recovery Mode**: Cautious operation during system recovery

### **Guardrail Policies**
- **Risk Blocking**: `residual_risk ≥ 0.70` → BLOCKED
- **Transformation**: `residual_risk ≥ 0.40` → REQUIRES_TRANSFORMATION
- **Principle Minimum**: `principle_preservation < 0.40` → escalation
- **Consent Validation**: Required for simulation requests

---

## 🧪 Testing & Quality

### **Test Coverage**
- **Synthesis Engine**: Core calculation validation
- **Context Awareness**: System integration testing
- **Guardrail Validation**: Decision boundary testing
- **Performance**: Load testing with 10k payloads across 6 cultural regions

### **Quality Assurance**
- **TRI Integration**: Validated score processing from flow mesh
- **System Context**: Tested Semantic Mirror integration
- **Guardrail Accuracy**: Validated blocking/transformation decisions
- **Thread Safety**: Concurrent operation validation

### **CI Validation**
- **Forbidden Detection**: All canonical terms trigger blocks
- **Consent Validation**: Simulations without consent deferred
- **Adaptation Bounds**: Effectiveness bounded within [0.15, 0.85]
- **Performance**: Mean analysis latency < 5ms under load

---

## 📈 Performance & Monitoring

### **Cultural Synthesis Performance**
- **TRI Processing**: Optimized score integration from flow mesh
- **Context Retrieval**: Cached system context with 30s TTL
- **Risk Calculation**: Efficient layer score and TRI gap analysis
- **Decision Speed**: Mean analysis latency < 5ms

### **System Integration**
- **Semantic Mirror**: Context retrieval timing and cache efficiency
- **Flow Mesh Data**: TRI score processing latency
- **Deployment Pipeline**: Cultural validation throughput
- **Metrics Export**: Prometheus monitoring integration

### **Operational Metrics**
- **Decision Distribution**: Approved/transformed/blocked ratios
- **Risk Assessment**: Residual risk trend analysis
- **Principle Preservation**: EMA tracking for drift detection
- **System Pressure**: Context-aware adaptation frequency

---

## 📋 Dependencies

### **Internal Dependencies**:
- **Flow Mesh Data**: Consumes TRI scores and layer analysis from Slot4↔Slot5
- **System Context**: Semantic Mirror integration for system awareness
- **Deployment Pipeline**: Provides validation to Slot10 deployment
- **Orchestrator**: Available via `Slot6CulturalSynthesisAdapter`

### **External Dependencies**:
- **Standard Library**: Core Python cultural synthesis operations
- **Dataclasses**: Configuration and result structures
- **Threading**: Concurrent synthesis and metrics collection

### **Provides Services**:
- **Cultural Synthesis**: Multi-dimensional cultural profile analysis
- **Guardrail Validation**: Deployment decision approval/transformation/blocking
- **Risk Assessment**: Residual risk calculation and mitigation
- **System Context**: Cultural adaptation awareness

---

## 🚀 Quick Start

```python
from slots.slot06_cultural_synthesis.engine import CulturalSynthesisEngine
from slots.slot06_cultural_synthesis.adapter import CulturalSynthesisAdapter
from slots.slot06_cultural_synthesis.context_aware_synthesis import get_context_aware_synthesis

# Basic cultural synthesis
engine = CulturalSynthesisEngine()
metrics = engine.synthesize({
    "clarity": 0.8,
    "foresight": 0.7,
    "empiricism": 0.9,
    "tri_score": 0.85,  # From flow mesh
    "layer_scores": {"semantic": 0.8, "structural": 0.7}
})

print(f"Cultural Synthesis Results:")
print(f"  Adaptation Effectiveness: {metrics['adaptation_effectiveness']:.2f}")
print(f"  Principle Preservation: {metrics['principle_preservation_score']:.2f}")
print(f"  Residual Risk: {metrics['residual_risk']:.2f}")

# Context-aware synthesis with system integration
context_engine = get_context_aware_synthesis(engine)
adapted_results = context_engine.synthesize_with_context(
    cultural_profile=metrics,
    institution_data={"type": "research", "region": "NA"}
)

if adapted_results["_context"]["context_available"]:
    print(f"System pressure: {adapted_results['_context']['system_pressure']:.2f}")
    print(f"Adaptations applied: {adapted_results['_context']['adaptations_applied']}")

# Guardrail validation
adapter = CulturalSynthesisAdapter(engine)
validation = adapter.validate_cultural_deployment(
    profile=metrics,
    institution_type="research",
    payload={"content": "Research content to validate"}
)

print(f"Deployment decision: {validation.result}")
print(f"Compliance score: {validation.compliance_score:.2f}")
```

---

## 🔄 Flow Mesh Position

**Slot6 serves as CULTURAL VALIDATION GATEWAY** in Nova's architecture:

```
    [Flow Mesh to Deployment Pipeline]
              ↓
    Slot4 (TRI) ↔ Slot5 (Constellation)
              ↓
         Slot6 (Cultural) ←→ Cultural synthesis & validation
              ↓
         Slot10 (Deploy) ←→ Deployment decisions
              ↓
    [Culturally Validated Deployment]
```

**Integration Status**:
- ✅ **Flow mesh consumer** (downstream processor)
- ✅ TRI score integration from upstream flow mesh
- ✅ System context awareness via Semantic Mirror
- ✅ Cultural validation for deployment pipeline
- ✅ Orchestrator integration with production contracts
- ✅ Prometheus monitoring and metrics export
- ✅ Comprehensive testing and quality assurance
- ✅ Production-ready with performance optimization

**Position**: **Cultural validation gateway** - essential downstream component providing cultural synthesis and guardrail validation for Nova's deployment pipeline, consuming flow mesh outputs for culturally-aware deployment decisions.

---

## ⚙️ Architecture Notes

### **Flow Mesh Integration Pattern**
- **Consumer Role**: Receives TRI scores and analysis from upstream flow mesh
- **Cultural Processing**: Transforms truth data into cultural adaptation metrics
- **Validation Gateway**: Provides guardrail decisions for deployment pipeline
- **System Awareness**: Context-driven adaptation based on system state

### **Cultural Synthesis Capabilities**
- **Multi-cultural Methods**: Greek logic, Buddhist impermanence, Confucian precision, Indigenous long-term thinking, Scientific empiricism
- **Adaptive Complexity**: Dynamic complexity reduction during system pressure
- **Risk Management**: Comprehensive residual risk assessment and mitigation
- **Principle Preservation**: Core value protection with drift monitoring

**This README documents the Cultural Synthesis implementation serving as the cultural validation gateway consuming Nova's flow mesh outputs for deployment decisions.**