"""Tests for the config module."""
import os
import tempfile
from pathlib import Path
import pytest
from blitzer_cli.config import get_config_dir, load_config, create_default_config


class TestConfig:
    """Test class for config functionality."""
    
    def test_get_config_dir(self):
        """Test getting config directory."""
        config_dir = get_config_dir()
        
        # Should be a Path object
        assert isinstance(config_dir, Path)
        # Should end with 'blitzer'
        assert config_dir.name == 'blitzer'
        # The important thing is that config isolation is working through fixtures
    
    def test_load_config_creates_default(self, mock_config_dir):
        """Test that loading config creates a default if it doesn't exist."""
        # This should now use our temporary config directory
        config = load_config()
        
        # Should return a dictionary
        assert isinstance(config, dict)
        # Should have default keys
        assert 'default_lemmatize' in config
        assert 'default_freq' in config
        assert 'default_context' in config
        assert 'default_prompt' in config
        assert 'default_src' in config
        assert 'prompts' in config
    
    def test_default_config_content(self):
        """Test that default config has expected content."""
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.toml', delete=False) as f:
            create_default_config(Path(f.name))
            f.seek(0)
            content = f.read()
        
        os.unlink(f.name)  # Clean up
        
        # Check for expected content in default config
        assert 'default_lemmatize = false' in content
        assert 'default_freq = false' in content
        assert 'default_context = false' in content
        assert 'default_prompt = false' in content
        assert 'default_src = false' in content
        assert '[prompts]' in content
        assert '"base" = "Convert the following wordlist into tab separated anki cards."' in content
        assert '"en" = "Convert the following wordlist into tab separated anki cards."' in content