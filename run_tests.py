#!/usr/bin/env python3
"""Simple test runner script."""

import os
import subprocess
import sys


def run_tests():
    """Run the test suite with pytest."""
    print("Running tests with pytest...")

    # Change to project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)

    try:
        # Run pytest
        result = subprocess.run([sys.executable, "-m", "pytest"], check=True)

        print("\n[SUCCESS] All tests passed!")
        return 0

    except subprocess.CalledProcessError as e:
        print(f"\n[FAIL] Tests failed with exit code {e.returncode}")
        return e.returncode
    except FileNotFoundError:
        print("[ERROR] pytest not found. Install with: pip install pytest")
        return 1


def run_quick_tests():
    """Run tests without coverage for faster execution."""
    print("Running quick tests...")

    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)

    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "--no-cov",  # Skip coverage
                "-x",  # Stop on first failure
            ],
            check=True,
        )

        print("\n[SUCCESS] Quick tests passed!")
        return 0

    except subprocess.CalledProcessError as e:
        print(f"\n[FAIL] Quick tests failed with exit code {e.returncode}")
        return e.returncode


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        exit_code = run_quick_tests()
    else:
        exit_code = run_tests()

    sys.exit(exit_code)
