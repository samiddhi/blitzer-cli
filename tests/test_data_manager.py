"""Tests for the data manager module."""
import os
import tempfile
from pathlib import Path
import pytest
from blitzer_cli.data_manager import get_language_data_dir, get_language_data_path, ensure_language_data


class TestDataManager:
    """Test class for data manager functionality."""
    
    def test_get_language_data_dir(self):
        """Test getting language data directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock the config directory to point to temp directory
            import blitzer_cli.data_manager
            # Temporarily modify the config directory for testing
            original_get_config_dir = blitzer_cli.data_manager.get_config_dir
            
            def mock_get_config_dir():
                temp_config = Path(temp_dir) / 'config' / 'blitzer'
                temp_config.mkdir(parents=True, exist_ok=True)
                return temp_config
            
            blitzer_cli.data_manager.get_config_dir = mock_get_config_dir
            
            try:
                data_dir = get_language_data_dir('test_lang')
                assert isinstance(data_dir, Path)
                assert data_dir.name == 'test_lang'
                assert 'language_data' in str(data_dir)
                assert data_dir.exists()  # Should be created automatically
            finally:
                # Restore original function
                blitzer_cli.data_manager.get_config_dir = original_get_config_dir
    
    def test_get_language_data_path_nonexistent(self):
        """Test getting language data path for non-existent file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            import blitzer_cli.data_manager
            original_get_config_dir = blitzer_cli.data_manager.get_config_dir
            
            def mock_get_config_dir():
                temp_config = Path(temp_dir) / 'config' / 'blitzer'
                temp_config.mkdir(parents=True, exist_ok=True)
                return temp_config
            
            blitzer_cli.data_manager.get_config_dir = mock_get_config_dir
            
            try:
                path = get_language_data_path('test_lang', 'nonexistent.db')
                assert path is None
            finally:
                blitzer_cli.data_manager.get_config_dir = original_get_config_dir
    
    def test_ensure_language_data_no_url(self):
        """Test ensure language data when file doesn't exist and no URL provided."""
        with tempfile.TemporaryDirectory() as temp_dir:
            import blitzer_cli.data_manager
            original_get_config_dir = blitzer_cli.data_manager.get_config_dir
            
            def mock_get_config_dir():
                temp_config = Path(temp_dir) / 'config' / 'blitzer'
                temp_config.mkdir(parents=True, exist_ok=True)
                return temp_config
            
            blitzer_cli.data_manager.get_config_dir = mock_get_config_dir
            
            try:
                result = ensure_language_data('test_lang', 'nonexistent.db', url=None)
                assert result is None
            finally:
                blitzer_cli.data_manager.get_config_dir = original_get_config_dir