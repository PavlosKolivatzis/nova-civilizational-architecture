# Slot 4: TRI (Truth Resonance Index) Engine

## Status: Production Ready ✅ (v1.0.0)
**Maturity Level**: 80% - Active flow mesh participant

Truth Resonance Index calculation engine for content evaluation with adaptive recovery and flow mesh integration. **Central node in Nova's active flow mesh architecture.**

---

## 🎯 Core Functions
- **TRI Calculation**: Real-time Truth Resonance Index scoring for content evaluation
- **Adaptive Recovery**: Automatic drift detection and safe mode activation
- **Flow Mesh Integration**: Central participant in Slot4 ↔ Slot5 ↔ Slot6 active flow
- **Safe Mode Operation**: Protective mode during instability or drift events
- **Performance Monitoring**: Statistical tracking with drift and surge detection
- **State Persistence**: Snapshots and recovery mechanisms for reliability

---

## 🏗️ Architecture

### **Core Components**
- **`TriEngine`**: Main TRI calculation engine with adaptive recovery (224 lines)
- **`DriftDetector`**: Real-time TRI score stability monitoring (87 lines)
- **`SafeMode`**: Protective operation during instability (79 lines)
- **`RepairPlanner`**: Automatic recovery strategy selection (23 lines)
- **`TriSnapshotter`**: State persistence and recovery (123 lines)
- **`SurgeDetector`**: Rapid change detection and mitigation

### **Files Overview**
```
core/tri_engine.py       (224 lines) - Main TRI calculation engine
core/detectors.py        (87 lines)  - Drift and surge detection
core/snapshotter.py      (123 lines) - State persistence
core/safe_mode.py        (79 lines)  - Protective mode operations
core/__init__.py         (60 lines)  - Public API exports
core/repair_planner.py   (23 lines)  - Recovery strategy selection
core/policy.py           (27 lines)  - Configuration policies
core/types.py            (22 lines)  - Data structures
tests/test_processual_tri.py (96 lines) - Comprehensive testing
```

**Total**: 10 Python files, 743 lines of sophisticated TRI processing logic

---

## 🔗 Flow Mesh Connections & Integration

### **✅ ACTIVE FLOW MESH PARTICIPANT**

**Current Flow Mesh Architecture:**
```
Slot4 (TRI) ↔ Slot5 (Constellation) ↔ Slot6 (Cultural Synthesis)
```

#### **Flow Mesh Role:**
- **Position**: **Central TRI calculation node**
- **Function**: Provides real-time Truth Resonance Index scores to flow mesh
- **Coordination**: Feeds TRI data to Constellation navigation and Cultural synthesis
- **Feature Flag**: `NOVA_ENABLE_TRI_LINK` controls flow mesh connectivity

#### **Flow Mesh Responsibilities:**
- **Truth Scoring**: Calculate TRI values for content flowing through mesh
- **Stability Monitoring**: Detect and respond to TRI drift events
- **Safe Mode Coordination**: Protect flow mesh during instability
- **Real-time Processing**: Live TRI scoring for mesh operations

### **Orchestrator Integration**
- **Adapter**: Available via `orchestrator.slot4`
- **Status**: Active and operational in Nova orchestrator
- **Feature Flag Monitoring**: `nova_feature_flag_enabled{flag="NOVA_ENABLE_TRI_LINK"}`

### **Prometheus Metrics**
- **Feature Flag Status**: `NOVA_ENABLE_TRI_LINK` state exported
- **Flow Mesh Health**: TRI Link connectivity monitoring
- **Performance Metrics**: TRI calculation timing and throughput

---

## 📊 API Contracts & Usage

### **Meta.yaml Contracts**
- **`tri.calculate`**: Standard TRI scoring (beta stability)
- **`tri.gated_calculate`**: Flow mesh gated calculation (stable)

### **Core TRI Engine API**
```python
from nova.slots.slot04_tri.core import TriEngine

# Initialize TRI engine
engine = TriEngine()

# Calculate TRI score
score = engine.calculate(content="Sample content")
print(f"TRI Score: {score}")

# Check engine health
health = engine.health()
print(f"Drift Z-score: {health.drift_z}")
print(f"Safe mode active: {engine.safe_mode.is_active()}")

# Get performance metrics
print(f"TRI mean: {health.tri_mean}")
print(f"TRI std: {health.tri_std}")
print(f"Samples processed: {health.n_samples}")
```

### **Advanced Features**
```python
# Safe mode operations
if engine.safe_mode.is_active():
    print("Engine in safe mode - using conservative TRI values")

# Drift detection
if health.drift_z > engine.policy.drift_z_threshold:
    print("TRI drift detected - automatic recovery initiated")

# State persistence
engine.snapshot()  # Save current state
engine.restore()   # Restore from snapshot
```

### **Health Monitoring**
```python
# Health structure
{
    "drift_z": float,        # Z-score of TRI drift
    "surge_events": int,     # Number of recent surge events
    "data_ok": bool,         # Data quality status
    "perf_ok": bool,         # Performance status
    "tri_mean": float,       # Current TRI mean
    "tri_std": float,        # Current TRI standard deviation
    "n_samples": int         # Number of samples processed
}
```

---

## 🔧 Configuration & Operational Modes

### **Feature Flag Control**
- **`NOVA_ENABLE_TRI_LINK=1`**: Enable flow mesh connectivity (default)
- **Gated Calculation**: Flow mesh operations use `tri.gated_calculate`
- **Monitoring**: Feature flag status exported to Prometheus

### **TRI Engine Policies**
- **Drift Detection**: Configurable Z-score threshold for drift alerts
- **Safe Mode**: Automatic activation during instability
- **Recovery**: Adaptive repair strategy selection
- **Surge Detection**: Rapid change mitigation

### **Safe Mode Operation**
- **Trigger**: Activated during TRI instability or drift events
- **Behavior**: Conservative TRI scoring to protect flow mesh
- **Recovery**: Automatic deactivation when stability restored
- **Coordination**: Notifies flow mesh participants of safe mode status

---

## 🧪 Testing & Quality

### **Test Coverage**
- **`test_processual_tri.py`** (96 lines): Comprehensive TRI engine testing
- **Processual Maturity**: Tests for 4.0/4.0 processual capabilities
- **Integration Testing**: Flow mesh connectivity and coordination
- **Performance Testing**: TRI calculation speed and accuracy

### **Quality Assurance**
- **Drift Detection**: Validated stability monitoring
- **Safe Mode**: Tested protective behavior
- **Recovery**: Automatic repair strategy validation
- **State Persistence**: Snapshot and restore functionality

### **Processual Validation**
- **4.0/4.0 Processual Maturity**: Full adaptive capability
- **Real-time Adaptation**: Dynamic response to changing conditions
- **Self-Healing**: Automatic recovery from instability
- **Flow Coordination**: Seamless mesh integration

---

## 📈 Performance & Monitoring

### **TRI Calculation Performance**
- **Real-time Processing**: Optimized for flow mesh requirements
- **Statistical Tracking**: Running mean and standard deviation
- **Drift Monitoring**: Continuous stability assessment
- **Surge Detection**: Rapid change identification

### **Operational Metrics**
- **TRI Score Distribution**: Statistical analysis of truth scores
- **Drift Events**: Frequency and severity of instability
- **Safe Mode Activation**: Duration and trigger analysis
- **Recovery Success**: Repair strategy effectiveness

### **Flow Mesh Coordination**
- **Latency**: TRI calculation timing for mesh operations
- **Throughput**: Content processing rate through TRI engine
- **Reliability**: Uptime and availability metrics
- **Synchronization**: Coordination timing with Slot5 and Slot6

---

## 📋 Dependencies

### **Internal Dependencies**:
- **Flow Mesh**: Active participant in Slot4 ↔ Slot5 ↔ Slot6 flow
- **Orchestrator**: Available via `Slot4TRIAdapter`
- **Feature Flags**: `NOVA_ENABLE_TRI_LINK` integration

### **External Dependencies**:
- **Standard Library**: Pure Python implementation
- **File System**: State persistence and snapshot storage

### **Provides Services**:
- **TRI Calculation**: Truth Resonance Index scoring
- **Flow Mesh Coordination**: Central truth scoring for mesh operations
- **Stability Monitoring**: Drift detection and safe mode protection
- **State Management**: Persistence and recovery capabilities

---

## 🚀 Quick Start

```python
from nova.slots.slot04_tri.core import TriEngine

# Basic TRI calculation
engine = TriEngine()
score = engine.calculate("Content to evaluate")
print(f"Truth Resonance Index: {score}")

# Monitor engine health
health = engine.health()
print(f"Engine status - Drift: {health.drift_z:.3f}, Samples: {health.n_samples}")

# Check safe mode status
if engine.safe_mode.is_active():
    print("⚠️  Safe mode active - conservative TRI scoring")
else:
    print("✅ Normal operation - full TRI capabilities")

# Advanced configuration
from nova.slots.slot04_tri.core.policy import TriPolicy

custom_policy = TriPolicy(
    drift_z_threshold=2.5,  # Custom drift sensitivity
    safe_mode_max_s=300     # 5-minute safe mode maximum
)

engine = TriEngine(policy=custom_policy)
```

---

## 🔄 Flow Mesh Position

**Slot4 serves as the CENTRAL TRI CALCULATION NODE** in Nova's flow mesh:

```
    [Flow Mesh Architecture]
              ↓
         Slot4 (TRI) ←→ Real-time truth scoring
         ↕         ↕
    Slot5 (Constellation) ←→ Navigation coordination
         ↕         ↕
    Slot6 (Cultural) ←→ Cultural synthesis
              ↓
    [Coordinated Truth Assessment]
```

**Integration Status**:
- ✅ **Active flow mesh participant** (central node)
- ✅ Orchestrator integration with feature flag control
- ✅ Prometheus monitoring and metrics export
- ✅ Comprehensive testing and quality assurance
- ✅ Production-ready with adaptive recovery
- 🔧 **Dual implementation cleanup needed** (legacy `slot04_tri_engine`)

**Position**: **Central truth calculation node** - essential component of Nova's active flow mesh providing real-time TRI scoring and stability monitoring for coordinated operations.

---

## ⚙️ Architecture Notes

### **Flow Mesh vs Standalone**
- **This implementation (`slot04_tri`)**: Flow mesh connected, adaptive, production-ready
- **Legacy implementation (`slot04_tri_engine`)**: Standalone, plugin-based, not flow mesh connected

### **Feature Flag Coordination**
- **`NOVA_ENABLE_TRI_LINK=1`**: Enables flow mesh participation
- **Gated Operations**: Flow mesh uses stable `tri.gated_calculate` contract
- **Monitoring**: Feature flag status exported for observability

**This README documents the primary, flow mesh connected TRI implementation.**