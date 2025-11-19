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