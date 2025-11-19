"""Data management utilities for language packs."""

import os
from pathlib import Path
import requests
from typing import Optional
from blitzer_cli.config import get_config_dir


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
            print(f"\033[31mFailed to download language data: {e}\033[0m", file=sys.stderr)
            return None
    
    return None