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

"""Data management utilities for language packs."""

from pathlib import Path
import requests
from typing import Optional
from blitzer_cli.config import get_config_dir
from blitzer_cli.utils import print_error


def get_language_data_dir(language_code: str) -> Path:
    """Get the data directory for a specific language."""
    config_dir = get_config_dir()
    data_dir = config_dir / "language_data" / language_code
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def download_language_data(url: str, language_code: str, filename: str) -> Path:
    """Download language data file to the appropriate location."""
    data_dir = get_language_data_dir(language_code)
    filepath = data_dir / filename
    
    print(f"Downloading {filename} for language {language_code}...")
    response = requests.get(url)
    response.raise_for_status()
    
    with open(filepath, 'wb') as f:
        f.write(response.content)
    
    print(f"Downloaded to {filepath}")
    return filepath


def get_language_data_path(language_code: str, filename: str) -> Optional[Path]:
    """Get the path to a language data file if it exists."""
    data_dir = get_language_data_dir(language_code)
    filepath = data_dir / filename
    
    if filepath.exists():
        return filepath
    return None


def ensure_language_data(language_code: str, filename: str, url: Optional[str] = None) -> Optional[Path]:
    """Ensure a language data file exists, downloading if necessary."""
    # Check if file already exists
    path = get_language_data_path(language_code, filename)
    if path:
        return path
    
    # If URL provided, attempt to download
    if url:
        try:
            return download_language_data(url, language_code, filename)
        except Exception as e:
            print_error(f"Failed to download language data: {e}")
            return None
    
    return None


def cleanup_language_data(language_code: Optional[str] = None) -> None:
    """Clean up language data files, either for a specific language or all languages."""
    config_dir = get_config_dir()
    data_dir = config_dir / "language_data"
    
    if not data_dir.exists():
        return  # Nothing to clean up
    
    if language_code:
        # Clean up data for specific language
        lang_data_dir = data_dir / language_code
        if lang_data_dir.exists():
            import shutil
            shutil.rmtree(lang_data_dir)
    else:
        # Clean up all language data
        import shutil
        shutil.rmtree(data_dir)
