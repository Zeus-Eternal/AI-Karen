"""
Test Runner for Phase 6 Integration Tests.

This script provides a convenient way to run all Phase 6 integration tests
and generate comprehensive reports.
"""

import pytest
import sys
import os
import argparse
import json
from datetime import datetime
from pathlib import Path


def create_test_report(test_results, output_dir):
    """Create a comprehensive test report."""
    report = {
        "test_run_info": {
            "timestamp": datetime.now().isoformat(),
            "python_version": sys.version,
            "pytest_version": pytest.__version__,
        },
        "test_categories": {
            "copilotkit_alignment": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "duration": 0.0,
            },
            "runtime_integration": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "duration": 0.0,
            },
            "boundary_layer": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "duration": 0.0,
            },
            "end_to_end_workflow": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "duration": 0.0,
            },
        },
        "test_files": [],
        "summary": {
            "total_tests": 0,
            "total_passed": 0,
            "total_failed": 0,
            "total_skipped": 0,
            "total_duration": 0.0,
            "success_rate": 0.0,
        },
    }

    # Process test results
    test_files = [
        "test_copilotkit_integration_phase6.py",
        "test_runtime_integration_phase6.py",
        "test_boundary_layer_phase6.py",
        "test_end_to_end_workflow_phase6.py",
    ]

    categories = {
        "test_copilotkit_integration_phase6.py": "copilotkit_alignment",
        "test_runtime_integration_phase6.py": "runtime_integration",
        "test_boundary_layer_phase6.py": "boundary_layer",
        "test_end_to_end_workflow_phase6.py": "end_to_end_workflow",
    }

    for test_file in test_files:
        category = categories.get(test_file, "other")
        file_path = Path(__file__).parent / test_file

        if file_path.exists():
            # Run pytest to get results for this file
            result = pytest.main(
                [
                    str(file_path),
                    "--json-report",
                    f"--json-report-file={output_dir}/report_{test_file}.json",
                    "--tb=short",
                ]
            )

            # Update report
            report["test_files"].append(
                {
                    "name": test_file,
                    "path": str(file_path),
                    "category": category,
                    "result": result,
                }
            )

    # Generate summary
    total_tests = sum(cat["total_tests"] for cat in report["test_categories"].values())
    total_passed = sum(cat["passed"] for cat in report["test_categories"].values())
    total_failed = sum(cat["failed"] for cat in report["test_categories"].values())
    total_skipped = sum(cat["skipped"] for cat in report["test_categories"].values())
    total_duration = sum(cat["duration"] for cat in report["test_categories"].values())

    report["summary"] = {
        "total_tests": total_tests,
        "total_passed": total_passed,
        "total_failed": total_failed,
        "total_skipped": total_skipped,
        "total_duration": total_duration,
        "success_rate": (total_passed / total_tests * 100) if total_tests > 0 else 0.0,
    }

    # Save report
    report_path = output_dir / "phase6_test_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    return report


def run_specific_test_category(category, output_dir):
    """Run tests for a specific category."""
    test_files = {
        "copilotkit_alignment": ["test_copilotkit_integration_phase6.py"],
        "runtime_integration": ["test_runtime_integration_phase6.py"],
        "boundary_layer": ["test_boundary_layer_phase6.py"],
        "end_to_end_workflow": ["test_end_to_end_workflow_phase6.py"],
        "all": [
            "test_copilotkit_integration_phase6.py",
            "test_runtime_integration_phase6.py",
            "test_boundary_layer_phase6.py",
            "test_end_to_end_workflow_phase6.py",
        ],
    }

    if category not in test_files:
        print(f"Invalid category: {category}")
        print(f"Available categories: {list(test_files.keys())}")
        return

    files_to_run = test_files[category]

    for test_file in files_to_run:
        file_path = Path(__file__).parent / test_file

        if file_path.exists():
            print(f"\n=== Running {test_file} ===")

            # Run tests
            result = pytest.main([str(file_path), "--tb=short", "--verbose"])

            print(f"Result: {'PASS' if result == 0 else 'FAIL'}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Phase 6 Integration Test Runner")
    parser.add_argument(
        "--category",
        choices=[
            "copilotkit_alignment",
            "runtime_integration",
            "boundary_layer",
            "end_to_end_workflow",
            "all",
        ],
        default="all",
        help="Test category to run",
    )
    parser.add_argument(
        "--output-dir", default="test_results", help="Output directory for test reports"
    )
    parser.add_argument(
        "--generate-report",
        action="store_true",
        help="Generate comprehensive test report",
    )

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    if args.generate_report:
        print("Generating comprehensive test report...")
        report = create_test_report(args.category, output_dir)

        print("\n=== Test Report Summary ===")
        print(f"Total Tests: {report['summary']['total_tests']}")
        print(f"Passed: {report['summary']['total_passed']}")
        print(f"Failed: {report['summary']['total_failed']}")
        print(f"Skipped: {report['summary']['total_skipped']}")
        print(f"Success Rate: {report['summary']['success_rate']:.1f}%")
        print(f"Duration: {report['summary']['total_duration']:.2f}s")

        print(f"\nDetailed report saved to: {output_dir / 'phase6_test_report.json'}")
    else:
        run_specific_test_category(args.category, output_dir)


if __name__ == "__main__":
    main()
