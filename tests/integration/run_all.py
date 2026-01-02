#!/usr/bin/env python3
"""Run all orchestrator integration tests and generate report.

Usage:
    python -m tests.integration.run_all [--output report.md]

This script runs all integration tests and generates a markdown report
suitable for sharing with stakeholders.
"""

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.integration.conftest import get_report


def run_tests(verbose: bool = True) -> int:
    """Run pytest on integration tests.

    Returns:
        Exit code from pytest
    """
    test_dir = Path(__file__).parent

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(test_dir),
        "-v" if verbose else "-q",
        "--tb=short",
        # Run all tests even if some fail
    ]

    print(f"Running: {' '.join(cmd)}")
    print("=" * 60)

    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return result.returncode


def generate_report(output_path: str) -> str:
    """Generate and save report.

    Args:
        output_path: Path to save report

    Returns:
        Report content
    """
    report = get_report()
    report.finalize()

    content = report.to_markdown()

    # Save to file
    with open(output_path, "w") as f:
        f.write(content)

    return content


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run orchestrator integration tests and generate report"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="orchestrator_test_report.md",
        help="Output file for report (default: orchestrator_test_report.md)",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Reduce pytest output verbosity",
    )
    parser.add_argument(
        "--no-run",
        action="store_true",
        help="Generate report from previous run without running tests",
    )

    args = parser.parse_args()

    print()
    print("=" * 60)
    print("MagoneAI Orchestrator Integration Tests")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)
    print()

    if not args.no_run:
        exit_code = run_tests(verbose=not args.quiet)
        print()
        print("=" * 60)
        print(f"Tests completed with exit code: {exit_code}")
        print("=" * 60)
    else:
        exit_code = 0

    # Generate report
    print()
    print(f"Generating report: {args.output}")

    try:
        content = generate_report(args.output)
        print(f"Report saved to: {args.output}")
        print()

        # Print summary
        report = get_report()
        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Total:    {report.total}")
        print(f"Passed:   {report.passed}")
        print(f"Failed:   {report.failed}")
        print(f"Partial:  {report.partial}")
        print(f"Errors:   {report.errors}")
        print(f"Skipped:  {report.skipped}")
        print(f"Pass Rate: {report.pass_rate:.1f}%")
        print(f"Avg Time: {report.avg_elapsed_ms:.0f}ms")
        print("=" * 60)

    except Exception as e:
        print(f"Error generating report: {e}")
        exit_code = 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
