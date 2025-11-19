"""Tests for the data manager module."""
import os
import tempfile
from pathlib import Path
import pytest
from blitzer_cli.data_manager import get_language_data_dir, get_language_data_path, ensure_language_data


class TestDataManager:
    """Test class for data manager functionality."""
    
    def test_get_language_data_dir(self, mock_config_dir):
        """Test getting language data directory."""
        data_dir = get_language_data_dir('test_lang')
        assert isinstance(data_dir, Path)
        assert data_dir.name == 'test_lang'
        assert 'language_data' in str(data_dir)
        assert data_dir.exists()  # Should be created automatically
    
    def test_get_language_data_path_nonexistent(self, mock_config_dir):
        """Test getting language data path for non-existent file."""
        path = get_language_data_path('test_lang', 'nonexistent.db')
        assert path is None
    
    def test_ensure_language_data_no_url(self, mock_config_dir):
        """Test ensure language data when file doesn't exist and no URL provided."""
        result = ensure_language_data('test_lang', 'nonexistent.db', url=None)
        assert result is None