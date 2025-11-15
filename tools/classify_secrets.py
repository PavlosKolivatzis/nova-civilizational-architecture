"""Classify secret findings by risk level (Nova audit pattern).

Phase 17: Secret Scanning Enhancement
Provides risk-based classification of detect-secrets findings with
provenance documentation following Nova's sunlight principle.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any


# Risk classification patterns (OWASP-aligned)
RISK_PATTERNS = {
    'CRITICAL': [
        'private_key', 'api_key', 'password', 'token',
        'credentials', 'secret_key', 'aws_access', 'rsa_private'
    ],
    'HIGH': [
        'jwt', 'bearer', 'oauth', 'session_token',
        'auth_token', 'api_token'
    ],
    'MEDIUM': [
        'hash', 'salt', 'nonce', 'seed',
        'entropy', 'random'
    ],
    'LOW': [
        'test', 'demo', 'example', 'sample',
        'placeholder', 'mock', 'fake'
    ]
}

# File patterns that reduce risk level
LOW_RISK_PATHS = [
    'test', 'tests/', 'spec/', 'docs/', '.artifacts/',
    'README', 'CHANGELOG', 'LICENSE', '.md', '.txt',
    'example', 'sample', 'demo', 'tutorial'
]


def classify_finding(finding: Dict[str, Any]) -> str:
    """Classify a secret finding by risk level.

    Args:
        finding: Dict with 'filename' and 'type' keys

    Returns:
        Risk level: CRITICAL, HIGH, MEDIUM, LOW, or INFO
    """
    filename = finding.get('filename', '').lower()
    type_ = finding.get('type', '').lower()

    # Documentation/test files are lower risk (likely examples)
    is_low_risk_path = any(pattern in filename for pattern in LOW_RISK_PATHS)

    # Check secret type against patterns
    for risk, patterns in RISK_PATTERNS.items():
        if any(pattern in type_ for pattern in patterns):
            # Downgrade if in low-risk path
            if is_low_risk_path and risk in ['CRITICAL', 'HIGH']:
                return 'INFO'  # Likely documentation/example
            return risk

    # Default classification
    return 'INFO' if is_low_risk_path else 'MEDIUM'


def generate_report(baseline_path: str, output_path: str | None = None) -> None:
    """Generate risk-classified secret audit report.

    Args:
        baseline_path: Path to .secrets.baseline file
        output_path: Optional output path (default: stdout)
    """
    try:
        with open(baseline_path) as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Baseline file not found: {baseline_path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in baseline: {e}", file=sys.stderr)
        sys.exit(1)

    # Classify all findings
    findings_by_risk: Dict[str, List[Dict[str, Any]]] = {
        'CRITICAL': [], 'HIGH': [], 'MEDIUM': [], 'LOW': [], 'INFO': []
    }

    for filename, secrets in data.get('results', {}).items():
        for secret in secrets:
            risk = classify_finding({
                'filename': filename,
                'type': secret.get('type', 'unknown')
            })

            findings_by_risk[risk].append({
                'file': filename,
                'line': secret.get('line_number', 0),
                'type': secret.get('type', 'unknown'),
                'hashed': secret.get('hashed_secret', '')[:8] + '...'
            })

    # Generate markdown report
    total_findings = sum(len(v) for v in findings_by_risk.values())
    critical_count = len(findings_by_risk['CRITICAL'])
    high_count = len(findings_by_risk['HIGH'])

    lines = [
        "# Secret Scan Audit Report",
        "",
        f"**Scan Date**: {data.get('generated_at', datetime.now(timezone.utc).isoformat())}",
        f"**Baseline Version**: {data.get('version', 'unknown')}",
        f"**Total Findings**: {total_findings}",
        "",
        "## Risk Summary",
        "",
        f"- 🔴 **CRITICAL**: {len(findings_by_risk['CRITICAL'])} findings",
        f"- 🟠 **HIGH**: {len(findings_by_risk['HIGH'])} findings",
        f"- 🟡 **MEDIUM**: {len(findings_by_risk['MEDIUM'])} findings",
        f"- 🟢 **LOW**: {len(findings_by_risk['LOW'])} findings",
        f"- ⚪ **INFO**: {len(findings_by_risk['INFO'])} findings (docs/tests)",
        "",
    ]

    # Risk assessment
    if critical_count > 0:
        lines.extend([
            "## ⚠️ Action Required",
            "",
            f"**{critical_count} CRITICAL findings require immediate attention.**",
            "",
            "Critical secrets must be:",
            "1. Removed from codebase if active credentials",
            "2. Rotated if potentially compromised",
            "3. Documented with provenance if safe examples",
            "",
        ])
    elif high_count > 0:
        lines.extend([
            "## ⚠️ Review Recommended",
            "",
            f"**{high_count} HIGH findings should be reviewed.**",
            "",
            "Verify these are intentional (examples/docs) and add pragma comments.",
            "",
        ])
    else:
        lines.extend([
            "## ✅ No Critical Issues",
            "",
            "All findings are documentation/test artifacts or low-risk patterns.",
            "",
        ])

    # Detailed findings by risk level
    for risk in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']:
        findings = findings_by_risk[risk]
        if not findings:
            continue

        emoji = {
            'CRITICAL': '🔴',
            'HIGH': '🟠',
            'MEDIUM': '🟡',
            'LOW': '🟢',
            'INFO': '⚪'
        }[risk]

        lines.extend([
            f"## {emoji} {risk} Risk ({len(findings)} findings)",
            "",
        ])

        # Group by file for readability
        by_file: Dict[str, List[Dict[str, Any]]] = {}
        for f in findings:
            by_file.setdefault(f['file'], []).append(f)

        for file, file_findings in sorted(by_file.items()):
            lines.append(f"### `{file}`")
            lines.append("")
            for f in file_findings:
                lines.append(f"- Line {f['line']}: `{f['type']}` ({f['hashed']})")
            lines.append("")

    # Remediation guidance
    lines.extend([
        "---",
        "",
        "## Remediation Guide",
        "",
        "### For CRITICAL/HIGH Findings",
        "",
        "**If active credential**:",
        "```bash",
        "# 1. Remove from code",
        "git filter-branch --force --index-filter \\",
        "  'git rm --cached --ignore-unmatch <file>' \\",
        "  --prune-empty --tag-name-filter cat -- --all",
        "",
        "# 2. Rotate credential immediately",
        "# 3. Update .gitignore to prevent re-commit",
        "```",
        "",
        "**If safe example/documentation**:",
        "```markdown",
        "<!-- pragma: allowlist secret",
        "     Reason: Historical audit artifact / documentation example",
        "     Context: Phase 17 security audit, safe to expose",
        "     Safe: Not an active credential, example only",
        "     Reviewed: " + datetime.now(timezone.utc).date().isoformat() + ")",
        "-->",
        "```",
        "",
        "### For MEDIUM/LOW/INFO Findings",
        "",
        "Review and add pragma comments if intentional, or rephrase to avoid",
        "triggering secret detection (e.g., `JWT_SECRET=<redacted>`).",
        "",
        "---",
        "",
        f"**Generated**: {datetime.now(timezone.utc).isoformat()}Z",
        f"**Tool**: classify_secrets.py (Nova Phase 17)",
        "",
    ])

    report = "\n".join(lines)

    # Output
    if output_path:
        Path(output_path).write_text(report, encoding='utf-8')
        print(f"[OK] Report generated: {output_path}")
    else:
        # Output to stdout with UTF-8 encoding
        sys.stdout.reconfigure(encoding='utf-8')
        print(report)


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Classify secret findings by risk level (Nova audit pattern)"
    )
    parser.add_argument(
        'baseline',
        help='Path to .secrets.baseline file'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output file path (default: stdout)',
        default=None
    )

    args = parser.parse_args()

    generate_report(args.baseline, args.output)


if __name__ == '__main__':
    main()
