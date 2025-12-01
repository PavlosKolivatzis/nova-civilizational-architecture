# Security Policy

## Known Vulnerabilities

### Active CVEs

#### DEF-010: pip 25.2 Tarfile Link Escape (CVE-2025-8869)

**Status**: Tracked, mitigation enforced, awaiting upstream fix

**Details**:
- **CVE**: CVE-2025-8869 (GHSA-4xh5-x5gv-qwph)
- **Component**: pip 25.2
- **Severity**: HIGH
- **Impact**: Arbitrary file overwrite during sdist installation via symbolic/hard link escape
- **Vulnerable Path**: Fallback tarfile extraction when installing source distributions
- **Fix Status**: Planned for pip 25.3 (not yet released as of 2025-10-05)

**Mitigation**:
```bash
# Enforce wheel-only installations (bypass vulnerable sdist path)
pip install --only-binary :all: <package>

# Or with uv (recommended)
uv pip install --only-binary :all: <package>
```

**CI/CD Policy**:
- All automated installs MUST use `--only-binary :all:` flag
- Manual installs SHOULD prefer wheels over source distributions
- Monitor https://github.com/pypa/pip/releases for pip 25.3 release
- Upgrade immediately when 25.3 is available

**Rollback**: Remove `--only-binary :all:` flag after pip upgrade to 25.3+

**Evidence**:
```bash
python -m pip_audit --format=json 2>&1 | grep -A5 "GHSA-4xh5-x5gv-qwph"
```

**References**:
- https://github.com/pypa/pip/security/advisories/GHSA-4xh5-x5gv-qwph
- https://github.com/pypa/pip/pull/13550 (fix PR)

---

## Reporting Security Issues

Please report security vulnerabilities via GitHub Security Advisories or contact the project maintainer directly.

**DO NOT** open public issues for security vulnerabilities.
