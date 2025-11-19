"""Pytest configuration and fixtures for Blitzer CLI tests."""

import pytest
import tempfile
from pathlib import Path


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for config testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )