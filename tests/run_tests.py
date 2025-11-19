#!/usr/bin/env python3
"""
Test runner for Blitzer CLI tests.

This script provides a single entry point to run all tests for the Blitzer CLI project.
It can be used to verify that everything is working correctly across different scenarios.
"""

import sys
import subprocess
import os
from pathlib import Path


def run_tests():
    """Run all tests using pytest."""
    print("Running Blitzer CLI tests...")
    print("=" * 50)
    
    # Change to the project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Check if pytest is available
    try:
        import pytest
    except ImportError:
        print("Error: pytest is not installed. Please install it with 'pip install pytest pytest-cov'.")
        return 1
    
    # Run pytest with verbose output and coverage
    args = [
        'pytest', 
        'tests/', 
        '-v',           # Verbose output
        '--tb=short',   # Short traceback format
        '-ra',          # Show extra test summary
    ]
    
    print(f"Running command: {' '.join(args)}")
    print("-" * 50)
    
    # Execute pytest
    result = subprocess.run(args)
    
    print("-" * 50)
    if result.returncode == 0:
        print("All tests passed! 🎉")
    else:
        print("Some tests failed! ❌")
    
    return result.returncode


def run_tests_with_coverage():
    """Run all tests with coverage report."""
    print("Running Blitzer CLI tests with coverage...")
    print("=" * 50)
    
    # Change to the project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Check if pytest and pytest-cov are available
    try:
        import pytest
        import pytest_cov
    except ImportError:
        print("Error: pytest or pytest-cov is not installed.")
        print("Please install them with 'pip install pytest pytest-cov'.")
        return 1
    
    # Run pytest with coverage
    args = [
        'pytest',
        'tests/',
        '-v',
        '--cov=blitzer_cli',
        '--cov-report=term-missing',
        '--cov-report=html:coverage_report',
        '-ra',
    ]
    
    print(f"Running command: {' '.join(args)}")
    print("-" * 50)
    
    # Execute pytest with coverage
    result = subprocess.run(args)
    
    print("-" * 50)
    if result.returncode == 0:
        print("All tests passed! 🎉")
        print("Coverage report generated in 'coverage_report' directory.")
        print("Open coverage_report/htmlcov/index.html in your browser to view detailed coverage.")
    else:
        print("Some tests failed! ❌")
    
    return result.returncode


def show_help():
    """Show help message."""
    print("Blitzer CLI Test Runner")
    print("=" * 30)
    print("Usage:")
    print("  python run_tests.py              # Run all tests")
    print("  python run_tests.py --coverage   # Run tests with coverage report")
    print("  python run_tests.py --help       # Show this help message")
    print()
    print("This script runs all tests for the Blitzer CLI project to ensure")
    print("everything is working correctly.")


def main():
    """Main function."""
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help', 'help']:
            show_help()
            return 0
        elif sys.argv[1] in ['-c', '--coverage']:
            return run_tests_with_coverage()
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print("Use --help for usage information.")
            return 1
    else:
        return run_tests()


if __name__ == '__main__':
    sys.exit(main())