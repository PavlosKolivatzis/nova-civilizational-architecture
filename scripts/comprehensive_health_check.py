#!/usr/bin/env python3
"""Comprehensive Nova system health check - all slots assessment."""

import time
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Tuple

def check_slot_implementation(slot_name: str, slot_path: Path) -> Dict[str, Any]:
    """Check if slot has proper implementation structure."""
    try:
        # Check for key files/directories that indicate implementation maturity
        core_dir = slot_path / "core"
        tests_dir = slot_path / "tests"
        test_dir = slot_path / "test"  # Some slots use singular

        has_core = core_dir.exists() and (core_dir / "__init__.py").exists()
        has_tests = tests_dir.exists() or test_dir.exists()

        # Try to import core module if it exists
        import_status = "unknown"
        if has_core:
            try:
                import importlib
                importlib.import_module(f"nova.slots.{slot_name}.core")
                import_status = "success"
            except Exception as e:
                import_status = f"error: {str(e)[:100]}"

        return {
            "status": "implemented" if has_core and has_tests else "skeleton",
            "has_core": has_core,
            "has_tests": has_tests,
            "import_status": import_status,
            "files": list(slot_path.glob("*.py"))[:3]  # Sample files
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

def run_slot_tests(slot_name: str, slot_path: Path) -> Dict[str, Any]:
    """Run tests for a specific slot."""
    tests_dir = slot_path / "tests"
    test_dir = slot_path / "test"

    test_targets = []
    tests_root = Path("tests")
    patterns = [f"test_{slot_name}*.py"]
    for pattern in patterns:
        matches = list(tests_root.rglob(pattern))
        if matches:
            test_targets = sorted({str(m.parent) for m in matches})
            break

    if not test_targets:
        return {"status": "no_tests", "reason": "No slot-specific tests found"}

    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", *test_targets, "-q", "--tb=no"
        ], capture_output=True, text=True, cwd=".", timeout=60)

        if result.returncode == 0:
            # Parse test count from output
            lines = result.stdout.split('\n')
            summary_line = next((line for line in lines if "passed" in line), "")
            return {
                "status": "pass",
                "summary": summary_line.strip() if summary_line else "tests passed",
                "stdout": result.stdout[:200]  # Truncate for readability
            }
        else:
            return {
                "status": "fail",
                "error": (result.stdout + result.stderr)[:300]
            }
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "error": "Tests exceeded 30s timeout"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def assess_slot_maturity(slot_name: str, implementation: Dict, tests: Dict) -> Tuple[float, str]:
    """Assess slot maturity level based on implementation and test results."""

    # Base maturity levels:
    # 1.0 = Conceptual (basic structure)
    # 2.0 = Relational (working but basic)
    # 3.0 = Structural (solid implementation)
    # 4.0 = Processual (autonomous, self-healing)

    if implementation["status"] == "error" or implementation["status"] == "skeleton":
        return 1.0, "Conceptual"

    if tests["status"] == "no_tests" or tests["status"] == "fail":
        return 1.5, "Conceptual"

    if tests["status"] == "pass":
        # Check for advanced features indicating higher maturity
        any([
            "autonomous" in str(implementation.get("files", [])).lower(),
            "self_healing" in str(implementation.get("files", [])).lower(),
            "adaptive" in str(implementation.get("files", [])).lower(),
            "processual" in str(implementation.get("files", [])).lower(),
        ])

        # Parse test count for complexity assessment
        test_count = 0
        if "summary" in tests:
            try:
                test_count = int(tests["summary"].split()[0])
            except Exception:
                pass

        if test_count >= 20:  # High test coverage suggests maturity
            return 4.0, "Processual"
        elif test_count >= 10:
            return 3.0, "Structural"
        elif test_count >= 5:
            return 2.5, "Structural"
        else:
            return 2.0, "Relational"

    return 1.5, "Conceptual"

def comprehensive_health_check():
    """Run comprehensive health check across all Nova slots."""
    print("Nova Civilizational Architecture - Comprehensive Health Assessment")
    print("=" * 70)
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    print()

    slots_dir = Path("src/nova/slots")
    slot_results = {}
    total_tests = 0
    maturity_scores = []
    processual_count = 0

    # Process each slot
    for slot_path in sorted(slots_dir.glob("slot*")):
        if not slot_path.is_dir():
            continue

        slot_name = slot_path.name
        print(f"Assessing {slot_name}...")

        # Check implementation
        implementation = check_slot_implementation(slot_name, slot_path)

        # Run tests
        tests = run_slot_tests(slot_name, slot_path)

        # Assess maturity
        maturity_score, maturity_level = assess_slot_maturity(slot_name, implementation, tests)

        slot_results[slot_name] = {
            "implementation": implementation,
            "tests": tests,
            "maturity_score": maturity_score,
            "maturity_level": maturity_level
        }

        # Update counters
        maturity_scores.append(maturity_score)
        if maturity_level == "Processual":
            processual_count += 1

        if tests.get("status") == "pass" and "summary" in tests:
            try:
                test_count = int(tests["summary"].split()[0])
                total_tests += test_count
            except Exception:
                pass

    print()
    print("=" * 70)
    print("SYSTEM ASSESSMENT RESULTS")
    print("=" * 70)

    # Summary metrics
    overall_maturity = sum(maturity_scores) / len(maturity_scores) if maturity_scores else 0
    print(f"Overall System Maturity: {overall_maturity:.1f}/4.0")
    print(f"Total Tests Passing: {total_tests}")
    print(f"Processual Slots: {processual_count}")
    print()

    # Per-slot details
    print("SLOT-BY-SLOT BREAKDOWN:")
    print("-" * 70)
    for slot_name, result in slot_results.items():
        status_icon = "✓" if result["tests"].get("status") == "pass" else "✗"
        test_summary = result["tests"].get("summary", "No tests")

        print(f"{status_icon} {slot_name:<35} {result['maturity_score']:.1f}/4.0 {result['maturity_level']}")
        if result["tests"].get("status") == "pass":
            print(f"    Tests: {test_summary}")
        elif result["tests"].get("status") != "no_tests":
            error = result["tests"].get("error", "Unknown error")[:60]
            print(f"    Tests: FAILED - {error}")
        print()

    print("=" * 70)
    if processual_count >= 7:
        print("🚀 ACHIEVEMENT: 7+ Processual slots - Civilizational-scale readiness!")
    elif processual_count >= 5:
        print("⭐ PROGRESS: Strong autonomous capabilities across multiple slots")
    elif processual_count >= 3:
        print("📈 DEVELOPMENT: Good progress toward autonomous operation")

    return {
        "overall_maturity": overall_maturity,
        "total_tests": total_tests,
        "processual_count": processual_count,
        "slot_results": slot_results
    }

if __name__ == "__main__":
    comprehensive_health_check()
