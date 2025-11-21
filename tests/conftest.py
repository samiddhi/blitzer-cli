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

"""Pytest configuration and fixtures for Blitzer CLI tests."""

import pytest
import tempfile
from pathlib import Path


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for config testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture(autouse=True)
def mock_config_dir(tmp_path, monkeypatch):
    """Create a temporary config directory and mock get_config_dir to return it.
    
    This fixture runs automatically for all tests to ensure config isolation.
    """
    def mock_get_config_dir():
        return tmp_path / 'blitzer'
    
    # Mock the function in the config module
    monkeypatch.setattr('blitzer_cli.config.get_config_dir', mock_get_config_dir)
    return tmp_path / 'blitzer'


def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
