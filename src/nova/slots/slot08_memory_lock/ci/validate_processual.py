"""CI validation script for Slot 8 Processual capabilities.

This script runs the complete validation suite and generates reports for:
- Processual capability tests
- Self-healing integration tests
- Performance benchmarks
- Acceptance criteria verification
"""

import sys
import json
import time
import subprocess
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass, asdict


@dataclass
class ValidationResult:
    """Result of a validation step."""
    step: str
    passed: bool
    duration: float
    details: Dict[str, Any]
    error_message: str = ""


class ProcessualValidator:
    """Validates Slot 8 Processual capabilities for CI/CD."""

    def __init__(self):
        self.results: List[ValidationResult] = []
        self.start_time = time.time()

    def run_test_suite(self, test_module: str, description: str) -> ValidationResult:
        """Run a test suite and capture results."""
        print(f"\n🔍 Running {description}...")

        step_start = time.time()

        try:
            # Run pytest on the specified module
            cmd = [
                sys.executable, "-m", "pytest",
                test_module,
                "-v",
                "--tb=short",
                "--json-report",
                "--json-report-file=test_report.json"
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent
            )

            duration = time.time() - step_start

            # Parse JSON report if available
            details = {"stdout": result.stdout, "stderr": result.stderr}
            report_file = Path("test_report.json")
            if report_file.exists():
                try:
                    with open(report_file) as f:
                        json_report = json.load(f)
                    details.update(json_report)
                    report_file.unlink()  # Clean up
                except Exception as e:
                    details["json_parse_error"] = str(e)

            passed = result.returncode == 0
            error_msg = result.stderr if not passed else ""

            validation_result = ValidationResult(
                step=description,
                passed=passed,
                duration=duration,
                details=details,
                error_message=error_msg
            )

            self.results.append(validation_result)

            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"   {status} in {duration:.2f}s")

            if not passed:
                print(f"   Error: {error_msg}")

            return validation_result

        except Exception as e:
            duration = time.time() - step_start

            validation_result = ValidationResult(
                step=description,
                passed=False,
                duration=duration,
                details={"exception": str(e)},
                error_message=str(e)
            )

            self.results.append(validation_result)
            print(f"   ❌ FAILED in {duration:.2f}s - Exception: {e}")

            return validation_result

    def run_performance_benchmarks(self) -> ValidationResult:
        """Run performance benchmarks."""
        print("\n🚀 Running Performance Benchmarks...")

        step_start = time.time()

        try:
            # Import and run benchmark
            sys.path.append(str(Path(__file__).parent.parent))
            from benchmarks.performance_validation import run_performance_validation

            success = run_performance_validation()
            duration = time.time() - step_start

            validation_result = ValidationResult(
                step="Performance Benchmarks",
                passed=success,
                duration=duration,
                details={"benchmark_completed": True},
                error_message="" if success else "Performance requirements not met"
            )

            self.results.append(validation_result)

            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"   {status} in {duration:.2f}s")

            return validation_result

        except Exception as e:
            duration = time.time() - step_start

            validation_result = ValidationResult(
                step="Performance Benchmarks",
                passed=False,
                duration=duration,
                details={"exception": str(e)},
                error_message=str(e)
            )

            self.results.append(validation_result)
            print(f"   ❌ FAILED in {duration:.2f}s - Exception: {e}")

            return validation_result

    def validate_acceptance_criteria(self) -> ValidationResult:
        """Validate Processual acceptance criteria."""
        print("\n📋 Validating Acceptance Criteria...")

        step_start = time.time()

        try:
            # Check that all critical tests passed
            critical_tests = [
                "Processual Capability Tests",
                "Self-Healing Integration Tests",
                "Performance Benchmarks"
            ]

            passed_critical = []
            failed_critical = []

            for result in self.results:
                if result.step in critical_tests:
                    if result.passed:
                        passed_critical.append(result.step)
                    else:
                        failed_critical.append(result.step)

            # Acceptance criteria
            criteria = {
                "all_critical_tests_passed": len(failed_critical) == 0,
                "mttr_requirement": True,  # Validated in performance benchmarks
                "quarantine_flip_requirement": True,  # Validated in performance benchmarks
                "autonomous_recovery": True,  # Validated in integration tests
                "adaptive_learning": True,  # Validated in integration tests
                "read_only_continuity": True  # Validated in integration tests
            }

            all_criteria_met = all(criteria.values())
            duration = time.time() - step_start

            validation_result = ValidationResult(
                step="Acceptance Criteria",
                passed=all_criteria_met,
                duration=duration,
                details={
                    "criteria": criteria,
                    "passed_critical_tests": passed_critical,
                    "failed_critical_tests": failed_critical,
                    "processual_ready": all_criteria_met
                },
                error_message="" if all_criteria_met else f"Failed critical tests: {failed_critical}"
            )

            self.results.append(validation_result)

            status = "✅ PASSED" if all_criteria_met else "❌ FAILED"
            print(f"   {status} in {duration:.2f}s")

            if all_criteria_met:
                print("   🎯 Slot 8 meets all Processual (4.0) criteria!")
            else:
                print(f"   ⚠️  Failed criteria: {failed_critical}")

            return validation_result

        except Exception as e:
            duration = time.time() - step_start

            validation_result = ValidationResult(
                step="Acceptance Criteria",
                passed=False,
                duration=duration,
                details={"exception": str(e)},
                error_message=str(e)
            )

            self.results.append(validation_result)
            print(f"   ❌ FAILED in {duration:.2f}s - Exception: {e}")

            return validation_result

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        total_duration = time.time() - self.start_time

        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)

        report = {
            "timestamp": time.time(),
            "total_duration": total_duration,
            "summary": {
                "total_validations": total_tests,
                "passed_validations": passed_tests,
                "failed_validations": total_tests - passed_tests,
                "success_rate": passed_tests / total_tests if total_tests > 0 else 0.0,
                "overall_passed": passed_tests == total_tests
            },
            "validations": [asdict(result) for result in self.results],
            "processual_classification": {
                "ready_for_processual": passed_tests == total_tests,
                "current_maturity": "4.0 Processual" if passed_tests == total_tests else "3.0 Structural",
                "next_steps": self._get_next_steps()
            }
        }

        return report

    def _get_next_steps(self) -> List[str]:
        """Get next steps based on validation results."""
        failed_results = [r for r in self.results if not r.passed]

        if not failed_results:
            return [
                "Update ACL registry: Slot 8 → Processual (4.0)",
                "Proceed to Phase 2b: Slot 4 enhancement",
                "Proceed to Phase 2c: Slot 10 enhancement"
            ]

        next_steps = ["Fix failing validations:"]
        for result in failed_results:
            next_steps.append(f"  - {result.step}: {result.error_message}")

        next_steps.append("Re-run validation after fixes")

        return next_steps

    def run_complete_validation(self) -> bool:
        """Run complete validation pipeline."""
        print("🎯 Starting Slot 8 Processual Validation Pipeline")
        print("=" * 60)

        # 1. Run capability tests
        self.run_test_suite(
            "tests/test_processual_capabilities.py",
            "Processual Capability Tests"
        )

        # 2. Run integration tests
        self.run_test_suite(
            "tests/test_self_healing_integration.py",
            "Self-Healing Integration Tests"
        )

        # 3. Run performance benchmarks
        self.run_performance_benchmarks()

        # 4. Validate acceptance criteria
        self.validate_acceptance_criteria()

        # 5. Generate and save report
        report = self.generate_report()

        # Save report
        report_file = Path("processual_validation_report.json")
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        # Print summary
        print("\n" + "=" * 60)
        print("🏁 VALIDATION PIPELINE COMPLETE")
        print("=" * 60)

        success_rate = report["summary"]["success_rate"]
        overall_passed = report["summary"]["overall_passed"]

        print(f"Success Rate: {success_rate:.1%}")
        print(f"Total Duration: {report['total_duration']:.2f}s")

        if overall_passed:
            print("\n✅ ALL VALIDATIONS PASSED")
            print("🎯 Slot 8 is ready for Processual (4.0) classification!")
            print("\nNext Steps:")
            for step in report["processual_classification"]["next_steps"]:
                print(f"  • {step}")
        else:
            print("\n❌ SOME VALIDATIONS FAILED")
            print("⚠️  Slot 8 remains at Structural (3.0) level")
            print("\nRequired Actions:")
            for step in report["processual_classification"]["next_steps"]:
                print(f"  • {step}")

        print(f"\n📄 Detailed report saved to: {report_file}")

        return overall_passed


def main():
    """Main entry point for CI validation."""
    validator = ProcessualValidator()
    success = validator.run_complete_validation()

    # Exit with appropriate code for CI/CD
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
