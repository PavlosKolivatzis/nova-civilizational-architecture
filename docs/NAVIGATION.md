# Nova Civilizational Architecture - Navigation Guide

## 🧭 How to Find Information in This Repository

This guide helps you navigate the Nova Civilizational Architecture repository effectively, understanding the organization and finding the information you need quickly.

## 📁 Repository Structure Overview

### Top-Level Directory Organization

```
nova-civilizational-architecture/
├── src/nova/                    # Core source code (Nova framework)
├── tests/                       # Test suite (2145 tests, 100% pass rate)
├── docs/                        # 📖 All documentation (comprehensive index)
├── contracts/                   # Contract definitions and schemas
├── scripts/                     # Maintenance and utility scripts
├── config/                      # Configuration files (13 moved from root)
├── .github/                     # CI/CD and GitHub workflows
├── .build/                      # Build artifacts and compilations
└── ops/                         # Operations and monitoring setup
```

## 📖 Documentation Navigation

### Primary Documentation Entry Points

1. **[Main Documentation Index](README.md)** - Start here for all documentation
2. **[Quick Start Guide](guides/quickstart/QUICKSTART_PROFESSOR.md)** - Rapid onboarding
3. **[Architecture Overview](architecture/ARCHITECTURE.md)** - System design and structure
4. **[Ontology Reference](architecture/ontology/)** - Mother Ontology v1.7.1 specifications

### Documentation Categories

#### 🏗️ Architecture & Design
- **System Architecture**: `docs/architecture/ARCHITECTURE.md`
- **Ontology Specifications**: `docs/architecture/ontology/`
- **Design Decisions**: `docs/architecture/adr/`
- **System Analysis**: `docs/architecture/SYSTEM_ANALYSIS.md`

#### 🧭 User Guides
- **Getting Started**: `docs/guides/quickstart/`
- **Contributing**: `docs/guides/contributing/`
- **Integration**: `docs/guides/deployment/`

#### 🔧 Operations
- **Runbooks**: `docs/operations/runbooks/`
- **Monitoring**: `docs/operations/monitoring/`
- **Alerts**: `docs/operations/alerts/`

#### 📋 Compliance
- **Security**: `docs/compliance/security/`
- **Audits**: `docs/compliance/audits/`
- **Defects**: `docs/compliance/defects/`

#### 🔬 Research
- **Analysis**: `docs/research/analysis/`
- **Papers**: `docs/research/papers/`
- **Reality Studies**: `docs/research/reality/`

#### 📦 Historical
- **Phase Documentation**: `docs/archive/phase-docs/`
- **Legacy Systems**: `docs/archive/legacy/`
- **Deprecated Content**: `docs/archive/deprecated/`

## 🔍 Finding Specific Information

### By Purpose

**Need something? Try these paths:**

- **How to contribute**: `docs/guides/contributing/CONTRIBUTING.md`
- **System architecture**: `docs/architecture/ARCHITECTURE.md`
- **Security policies**: `docs/compliance/security/SECURITY.md`
- **Known issues**: `docs/compliance/defects/DEFECTS_REGISTER.yml`
- **Test coverage**: `docs/architecture/SYSTEM_ANALYSIS.md`
- **API contracts**: `contracts/`
- **Ontology specs**: `docs/architecture/ontology/`

### By Lifecycle Status

**Current Documentation** (ACTIVE):
- Most files in `docs/guides/`, `docs/architecture/`, `docs/compliance/`

**Historical Documentation** (ARCHIVED):
- Phase-specific docs in `docs/archive/`
- Legacy system docs in `docs/archive/legacy/`

**Development Documentation** (ACTIVE):
- ADRs in `docs/architecture/adr/`
- Implementation notes in `docs/engineering-notes/`

## 🚨 Current Documentation Status

### Active Organization Project

**Phase 14-0: Repository Consolidation** is currently in progress:

- ✅ **Completed**: Root directory cleanup (47 → 14 files)
- ✅ **Completed**: Documentation taxonomy reorganization
- ⏳ **In Progress**: Lifecycle tagging (217 documents need tags)
- ⏳ **In Progress**: Orphaned file categorization (201 files)

### How This Affects Navigation

**New Structure**:
- Documentation has been reorganized into logical categories
- Navigation may require updating bookmarks/links
- Some files may have moved locations

**Finding Recently Moved Files**:
- Use `find` commands if file paths have changed
- Check `docs/README.md` for the main index
- Look for files in the category that matches their purpose

## 🧰 Tools and Scripts

### Navigation Aids

- **[Sunlight Scanner](scripts/maintenance/sunlight_scan.py)**: Validates document lifecycle status
- **[Ontology Validator](scripts/validate_ontology_structure.py)**: Checks ontology compliance
- **[File Search](https://git-scm.com/docs/gitgrep)**: Use `git grep` to find content

### Quick Commands

```bash
# Find documentation by content
git grep -i "slot.*interface" -- "*.md"

# Find files by pattern
find . -name "*slot*" -type f

# Check document lifecycle status
python3 scripts/maintenance/sunlight_scan.py --verbose
```

## 🎯 Common Tasks & Locations

### For New Developers
1. Start: `docs/guides/quickstart/QUICKSTART_PROFESSOR.md`
2. Contribute: `docs/guides/contributing/CONTRIBUTING.md`
3. Architecture: `docs/architecture/ARCHITECTURE.md`

### For System Architects
1. Design decisions: `docs/architecture/adr/`
2. Ontology specs: `docs/architecture/ontology/`
3. System analysis: `docs/architecture/SYSTEM_ANALYSIS.md`

### For Operations Teams
1. Runbooks: `docs/operations/runbooks/`
2. Monitoring: `docs/operations/monitoring/`
3. Security: `docs/compliance/security/`

### For Researchers
1. Research papers: `docs/research/papers/`
2. Analysis: `docs/research/analysis/`
3. Reality studies: `docs/research/reality/`

## 📞 Getting Help

### Documentation Issues
- Missing information: Open an issue describing what's needed
- Outdated docs: Use the defect register
- Navigation problems: This navigation guide

### Contributing
- See `docs/guides/contributing/CONTRIBUTING.md`
- Follow the Sunlight Doctrine: Observe → Canonize → Attest → Publish

---

## 🔄 Living Document

This navigation guide is a living document that evolves with the repository structure. Last updated during Phase 14-0 Repository Consolidation.

For the most current information, always check `docs/README.md` for the main documentation index.