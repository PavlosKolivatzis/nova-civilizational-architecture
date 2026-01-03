# Nova Civilizational Architecture Documentation

## 📖 Documentation Index

Welcome to the Nova Civilizational Architecture documentation. This index provides a comprehensive navigation map to all documentation, organized by category and purpose.

## 🏗️ Architecture & System Design

### Core Architecture
- **[Architecture Overview](architecture/ARCHITECTURE.md)** - System architecture and design principles
- **[System Analysis](architecture/SYSTEM_ANALYSIS.md)** - Detailed system analysis and components
- **[Ontology](architecture/ontology/)** - Mother Ontology v1.7.1 specifications and contracts

### Design Decisions
- **[ADR Index](architecture/adr/)** - Architectural Decision Records
- **[System Map](architecture/system_map.yaml)** - Component relationships and dependencies

## 🧭 User Guides

### Getting Started
- **[Quick Start Guide](guides/quickstart/QUICKSTART_PROFESSOR.md)** - Rapid onboarding and basic setup
- **[Integration Guide](guides/deployment/integration_guide.md)** - Integration patterns and best practices

### Development & Contribution
- **[Contributing Guide](guides/contributing/CONTRIBUTING.md)** - How to contribute to the project
- **[Slot System Guide](guides/slots/)** - Understanding and working with the slot system

## 🔧 Operations & Maintenance

### Operations
- **[Runbooks](operations/runbooks/)** - Operational procedures and troubleshooting
- **[Monitoring](operations/monitoring/)** - Observability and alerting setup

### Infrastructure
- **[Alerts Configuration](operations/alerts/)** - Alert rules and monitoring configuration
- **[Deployment](operations/deployment/)** - Deployment procedures and configurations

## 📋 Compliance & Governance

### Security & Compliance
- **[Security Policy](compliance/security/SECURITY.md)** - Security guidelines and policies
- **[Implementation Audit](compliance/audits/IMPLEMENTATION_AUDIT.md)** - Current compliance status
- **[Meta Lens Production Ready](compliance/audits/META_LENS_PRODUCTION_READY.md)** - Production readiness assessment
- **[Audit Series Index](audits/README.md)** - Governance and derivative audit artifacts

### Attestations
- **[Meta Lens Tether Confirmation](compliance/attestations/META_LENS_TETHER_CONFIRMATION.md)** - System integrity attestations
- **[Regime Attestation](compliance/attestations/)** - Regime compliance attestations

## 🔬 Research & Analysis

### Research Papers
- **[Civilizational Analysis](research/civilizational/)** - Research on civilizational architecture
- **[Ontological Research](research/ontology/)** - Foundational research papers

### Analysis & Reports
- **[Defects Register](compliance/defects/DEFECTS_REGISTER.yml)** - Known issues and defect tracking
- **[Drift Report](compliance/audits/DRIFT_REPORT.md)** - System drift analysis
- **[Epoch Manifest](research/manifests/EPOCH_V10_MANIFEST.md)** - Current epoch specifications

## 📦 API Reference

### Contracts
- **[Contract Specifications](api/contracts/)** - All contract definitions and schemas
- **[Slot Interfaces](api/slots/)** - Slot 01-10 API specifications

### System APIs
- **[Ledger APIs](api/ledger/)** - Three Ledgers API documentation
- **[Ontology APIs](api/ontology/)** - Ontology loading and validation APIs

## 🗂️ Historical Archive

### Phase Documentation
- **[Phase 11 Completion](archive/phase-docs/PHASE11_COMPLETION.md)** - Phase 11 implementation summary
- **[Phase 5 Summary](archive/phase-docs/PHASE5_SUMMARY.md)** - Historical phase documentation

### Legacy Content
- **[Legacy Systems](archive/legacy/)** - Deprecated system documentation
- **[Archived Contracts](archive/contracts/)** - Superseded contract definitions

## 📊 Key Metrics & Status

- **Ontology Version**: Mother Ontology v1.7.1
- **Phase Status**: Phase 14-3 (USM Bias Detection; snapshot, see docs/architecture/SYSTEM_ARCHITECTURE.md)
- **Test Coverage**: Snapshot-based; see docs/TESTS_OVERVIEW.md
- **Documentation Integrity**: Sunlight Doctrine compliant
- **New Capability**: Automated cognitive bias detection (BIAS_REPORT@1)

## 🔍 Search & Navigation

- **[Glossary](GLOSSARY.md)** - Term definitions and concepts
- **[Navigation Guide](NAVIGATION.md)** - How to find information
- **[Dependency Map](architecture/DEPENDENCY_MAP.md)** - Module relationships

## 🌟 Getting Started

1. **New Developers**: Start with [Quick Start Guide](guides/quickstart/QUICKSTART_PROFESSOR.md)
2. **System Architects**: Review [Architecture Overview](architecture/ARCHITECTURE.md)
3. **Operators**: Check [Runbooks](operations/runbooks/)
4. **Researchers**: Explore [Research Papers](research/)

## 📝 Documentation Standards

All documentation follows the Sunlight Doctrine:
- **Observe** → Document current state
- **Canonize** → Establish canonical references  
- **Attest** → Provide evidence and validation
- **Publish** → Make accessible and discoverable

For questions or contributions to documentation, see [Contributing Guide](guides/contributing/CONTRIBUTING.md).

---
*Last updated: snapshot-based; see docs/architecture/SYSTEM_ARCHITECTURE.md*
*Next review: Phase 15 (TBD)*

## 🆕 Phase 14.3: USM Bias Detection

**Implemented:** Automated cognitive bias detection for input text analysis.

**Specification:** [`docs/specs/slot02_usm_bias_detection_spec.md`](specs/slot02_usm_bias_detection_spec.md)

**Components:**
- TextGraphParser (Slot02): Text → SystemGraph
- BiasCalculator (Slot02): USM → B(T) → C(B)
- QualityOracle (Slot01): Independent validation
- CognitiveLoopController (Slot07): Recursive refinement

**Contract:** [`contracts/bias_report@1.yaml`](../contracts/bias_report@1.yaml)

**Feature Flag:** `NOVA_ENABLE_BIAS_DETECTION=0` (default off)

**Research:** [`archive/ai_biases/`](../archive/ai_biases/) - ΔTHRESH signal framework analysis
