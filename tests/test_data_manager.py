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
