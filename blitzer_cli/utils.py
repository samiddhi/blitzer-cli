# blitzer-cli: A CLI tool
# Copyright (C) 2025 Samiddhi
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
