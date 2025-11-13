#!/usr/bin/env python3
"""
Phase 2.1: Configuration Audit - Environment Variable Inventory

Scans Nova codebase for NOVA_* environment variables and generates:
1. Comprehensive inventory with defaults, usage locations, and context
2. Cross-reference with documentation
3. Usage patterns and risk analysis
"""

import os
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple

# Patterns to match various os.getenv styles
GETENV_PATTERNS = [
    # Pattern 1: os.getenv with string default
    r'os\.getenv\(\s*["\']([A-Z_]+)["\']\s*,\s*["\']([^"\']*)["\']',
    # Pattern 2: os.getenv with variable default
    r'os\.getenv\(\s*["\']([A-Z_]+)["\']\s*,\s*([^)]+?)\)',
    # Pattern 3: os.getenv without default
    r'os\.getenv\(\s*["\']([A-Z_]+)["\']',
    # Pattern 4: os.environ.get with string default
    r'os\.environ\.get\(\s*["\']([A-Z_]+)["\']\s*,\s*["\']([^"\']*)["\']',
    # Pattern 5: os.environ.get with variable default
    r'os\.environ\.get\(\s*["\']([A-Z_]+)["\']\s*,\s*([^)]+?)\)',
    # Pattern 6: os.environ.get without default
    r'os\.environ\.get\(\s*["\']([A-Z_]+)["\']',
    # Pattern 7: os.environ dict access
    r'os\.environ\[\s*["\']([A-Z_]+)["\']\s*\]',
]

def scan_file_for_flags(filepath: Path) -> List[Tuple[str, str, str, int]]:
    """
    Scan a Python file for environment variable usage.

    Returns list of (var_name, default_value, context_line, line_number)
    """
    findings = []

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        for line_num, line in enumerate(lines, 1):
            for pattern in GETENV_PATTERNS:
                matches = re.finditer(pattern, line)
                for match in matches:
                    var_name = match.group(1)

                    # Skip if not a NOVA_* variable
                    if not var_name.startswith('NOVA_'):
                        continue

                    # Extract default value if present
                    default = match.group(2) if match.lastindex >= 2 else None

                    # Clean up default value
                    if default:
                        default = default.strip().strip('"\'')
                    else:
                        default = "NO_DEFAULT"

                    # Get context (surrounding code)
                    context = line.strip()

                    findings.append((var_name, default, context, line_num))

    except Exception as e:
        print(f"Error scanning {filepath}: {e}")

    return findings

def load_documented_flags() -> Set[str]:
    """Load flags that are documented in README/docs/.env.example"""
    documented = set()

    doc_files = [
        'README.md',
        'docs/README.md',
        '.env.example',
        'CLAUDE.md',
    ]

    for doc_file in doc_files:
        if not Path(doc_file).exists():
            continue

        try:
            with open(doc_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Find all NOVA_* references
            nova_refs = re.findall(r'\b(NOVA_[A-Z_]+)\b', content)
            documented.update(nova_refs)
        except Exception as e:
            print(f"Error reading {doc_file}: {e}")

    return documented

def analyze_flag_impact(var_name: str, usages: List[Tuple[Path, str, str, int]]) -> str:
    """Analyze the impact/criticality of a flag based on usage patterns"""

    # Count unique files
    unique_files = len(set(u[0] for u in usages))

    # Check for critical keywords in context
    critical_keywords = ['security', 'auth', 'secret', 'key', 'password', 'token']
    safety_keywords = ['enabled', 'disable', 'block', 'allow', 'gate']
    performance_keywords = ['timeout', 'interval', 'limit', 'max', 'min']

    contexts = [u[2].lower() for u in usages]

    has_critical = any(any(k in ctx for k in critical_keywords) for ctx in contexts)
    has_safety = any(any(k in ctx for k in safety_keywords) for ctx in contexts)
    has_performance = any(any(k in ctx for k in performance_keywords) for ctx in contexts)

    if has_critical:
        return "🔴 CRITICAL (Security)"
    elif var_name.endswith('_ENABLED') or has_safety:
        return "🟡 HIGH (Feature Gate)"
    elif has_performance:
        return "🟡 MEDIUM (Performance)"
    elif unique_files >= 3:
        return "🟡 MEDIUM (Wide Usage)"
    else:
        return "🟢 LOW (Limited Scope)"

def main():
    print("🔍 Phase 2.1: Configuration Inventory")
    print("=" * 60)
    print()

    # Scan all Python files
    print("Scanning codebase for NOVA_* environment variables...")

    all_flags = defaultdict(list)

    for base_dir in ['src', 'orchestrator']:
        if not Path(base_dir).exists():
            continue

        for py_file in Path(base_dir).rglob('*.py'):
            if '__pycache__' in str(py_file):
                continue

            findings = scan_file_for_flags(py_file)
            for var_name, default, context, line_num in findings:
                all_flags[var_name].append((py_file, default, context, line_num))

    print(f"Found {len(all_flags)} unique NOVA_* environment variables")
    print()

    # Load documented flags
    print("Cross-referencing with documentation...")
    documented = load_documented_flags()
    print(f"Found {len(documented)} documented flags")
    print()

    # Generate markdown table
    output = []
    output.append("# Nova Configuration Inventory (Phase 2.1)")
    output.append("")
    output.append("**Audit Date**: 2025-11-13")
    output.append("**Total Flags Found**: " + str(len(all_flags)))
    output.append("**Documented Flags**: " + str(len(documented)))
    output.append("**Undocumented Flags**: " + str(len([f for f in all_flags if f not in documented])))
    output.append("")
    output.append("---")
    output.append("")

    # Summary statistics
    output.append("## Summary Statistics")
    output.append("")
    output.append(f"- **Total unique NOVA_* variables**: {len(all_flags)}")
    output.append(f"- **Documented in README/docs**: {len(documented)}")
    output.append(f"- **Undocumented**: {len([f for f in all_flags if f not in documented])}")
    output.append(f"- **Total usage locations**: {sum(len(usages) for usages in all_flags.values())}")
    output.append("")
    output.append("---")
    output.append("")

    # Detailed inventory table
    output.append("## Detailed Inventory")
    output.append("")
    output.append("| Flag | Default | Impact | Files | Documented? |")
    output.append("|------|---------|--------|-------|-------------|")

    for var_name in sorted(all_flags.keys()):
        usages = all_flags[var_name]

        # Get most common default value
        defaults = [u[1] for u in usages]
        default_value = max(set(defaults), key=defaults.count)

        # Count unique files
        unique_files = len(set(u[0] for u in usages))

        # Analyze impact
        impact = analyze_flag_impact(var_name, usages)

        # Check if documented
        is_documented = "✅" if var_name in documented else "❌"

        # Truncate default if too long
        if len(default_value) > 30:
            default_display = f"`{default_value[:27]}...`"
        else:
            default_display = f"`{default_value}`"

        output.append(f"| `{var_name}` | {default_display} | {impact} | {unique_files} | {is_documented} |")

    output.append("")
    output.append("---")
    output.append("")

    # Detailed usage breakdown
    output.append("## Detailed Usage Breakdown")
    output.append("")

    for var_name in sorted(all_flags.keys()):
        usages = all_flags[var_name]

        output.append(f"### `{var_name}`")
        output.append("")

        # Get all unique defaults
        unique_defaults = set(u[1] for u in usages)
        if len(unique_defaults) == 1:
            output.append(f"**Default**: `{list(unique_defaults)[0]}`")
        else:
            output.append(f"**Defaults**: Multiple values found:")
            for default in sorted(unique_defaults):
                count = sum(1 for u in usages if u[1] == default)
                output.append(f"  - `{default}` ({count} locations)")

        output.append("")

        # Impact analysis
        impact = analyze_flag_impact(var_name, usages)
        output.append(f"**Impact**: {impact}")
        output.append("")

        # Documentation status
        if var_name in documented:
            output.append("**Documentation**: ✅ Documented")
        else:
            output.append("**Documentation**: ❌ **NEEDS DOCUMENTATION**")

        output.append("")

        # Usage locations
        output.append(f"**Usage Locations** ({len(usages)} total):")
        output.append("")

        for filepath, default, context, line_num in usages[:10]:  # Limit to first 10
            rel_path = str(filepath).replace('src/', '').replace('orchestrator/', '')
            output.append(f"- `{rel_path}:{line_num}`")
            output.append(f"  ```python")
            output.append(f"  {context}")
            output.append(f"  ```")
            output.append("")

        if len(usages) > 10:
            output.append(f"*... and {len(usages) - 10} more locations*")
            output.append("")

        output.append("---")
        output.append("")

    # Write to file
    output_file = Path('.artifacts/audit_config_inventory.md')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))

    print(f"✅ Inventory written to {output_file}")
    print()

    # Print summary to console
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total NOVA_* flags: {len(all_flags)}")
    print(f"Documented: {len([f for f in all_flags if f in documented])}")
    print(f"Undocumented: {len([f for f in all_flags if f not in documented])}")
    print()

    # List undocumented flags
    undocumented = [f for f in sorted(all_flags.keys()) if f not in documented]
    if undocumented:
        print("⚠️  UNDOCUMENTED FLAGS:")
        for flag in undocumented:
            impact = analyze_flag_impact(flag, all_flags[flag])
            print(f"  - {flag} ({impact})")

    print()
    print("✅ Phase 2.1 complete!")

if __name__ == "__main__":
    main()
