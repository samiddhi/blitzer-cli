"""Utility functions for the Blitzer CLI."""

import sys


def print_error(message: str) -> None:
    """Print error message to stderr in red."""
    print(f"\033[31m{message}\033[0m", file=sys.stderr)


def print_warning(message: str) -> None:
    """Print warning message to stderr in yellow."""
    print(f"\033[33m{message}\033[0m", file=sys.stderr)


def print_success(message: str) -> None:
    """Print success message to stdout in green."""
    print(f"\033[32m{message}\033[0m")