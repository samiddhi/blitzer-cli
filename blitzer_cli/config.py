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

"""Configuration management using XDG specifications."""

import os
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


def load_config(config_path=None, use_default_config=True):
    """Load configuration from XDG config file or specific path.
    
    Args:
        config_path: Optional path to a specific config file, otherwise use default location
        use_default_config: If True, create and return default config when loading fails
    """
    if config_path:
        # Use the provided config path
        config_file = Path(config_path)
    else:
        # Use default XDG config location
        config_dir = get_config_dir()
        config_file = config_dir / 'config.toml'
        
        # Create config directory if it doesn't exist (only for default location)
        if use_default_config:
            config_dir.mkdir(parents=True, exist_ok=True)
    
    # Load the config
    try:
        with open(config_file, 'rb') as f:
            return tomllib.load(f)
    except Exception:
        if use_default_config and config_path is None:
            # If config doesn't exist or fails to load, create default and reload
            if not config_file.exists():
                create_default_config(config_file)
                # Now load the newly created config
                try:
                    with open(config_file, 'rb') as f:
                        return tomllib.load(f)
                except Exception:
                    # If it still fails after creating default, return empty config
                    return {}
            else:
                # If file exists but loading failed for other reasons, return empty config
                return {}
        else:
            # If use_default_config is False, return empty config without creating default
            return {}


def create_default_config(config_file):
    """Create a default configuration file."""
    default_config = """# Blitzer CLI Configuration
# This file uses TOML format

# Default flag values
default_lemmatize = false  # Default value for --lemmatize/-L flag
default_freq = false       # Default value for --freq/-f flag
default_context = false    # Default value for --context/-c flag
default_prompt = false     # Default value for --prompt/-p flag
default_src = false        # Default value for --src/-s flag

# Language-specific exclusion list paths
# Each key in the exclusions table represents a language code with its exclusion file path
# Example: "slv" = "/path/to/slovenian_exclusion.txt"
# Example: "pli" = "/path/to/pali_exclusion.txt"
[exclusions]

# Language-specific prompts
# Each key in the prompts table represents a language code with its custom prompt
[prompts]
"base" = "Convert the following wordlist into tab separated anki cards."
"en" = "Convert the following wordlist into tab separated anki cards."

"""
    
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(default_config)
