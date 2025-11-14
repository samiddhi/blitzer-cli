"""Configuration management using XDG specifications."""

import os
import sys
from pathlib import Path

# Import TOML library with fallback for older Python versions
try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # Python < 3.11


def get_config_dir():
    """Get the XDG config directory for blitzer."""
    # Use XDG_CONFIG_HOME or default to ~/.config
    xdg_config_home = os.environ.get('XDG_CONFIG_HOME')
    if xdg_config_home:
        config_dir = Path(xdg_config_home) / 'blitzer'
    else:
        config_dir = Path.home() / '.config' / 'blitzer'
    
    return config_dir


def load_config():
    """Load configuration from XDG config file."""
    config_dir = get_config_dir()
    config_file = config_dir / 'config.toml'
    
    # Create config directory if it doesn't exist
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a default config file if it doesn't exist
    if not config_file.exists():
        create_default_config(config_file)
    
    # Load the config
    try:
        with open(config_file, 'rb') as f:
            return tomli.load(f)
    except Exception:
        # Return empty config if loading fails
        return {}


def create_default_config(config_file):
    """Create a default configuration file."""
    default_config = """# Blitzer CLI Configuration
# This file uses TOML format

# Default settings
default_language = "pli"  # Default language code
default_mode = "word_list"  # Default processing mode

# Output settings
include_frequency = false  # Whether to include frequency by default
"""
    
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(default_config)