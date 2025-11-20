"""Configuration management using XDG specifications."""

import os
import sys
from pathlib import Path

# Import TOML library with fallback for older Python versions
try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # Python < 3.11

from blitzer_cli.utils import print_error


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
    
    # Load the config
    try:
        with open(config_file, 'rb') as f:
            return tomllib.load(f)
    except Exception:
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

# Language-specific prompts
# Each key in the prompts table represents a language code with its custom prompt
[prompts]
"base" = "Convert the following wordlist into tab separated anki cards."
"en" = "Convert the following wordlist into tab separated anki cards."

"""
    
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(default_config)