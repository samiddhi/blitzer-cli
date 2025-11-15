#!/usr/bin/env python3
"""Test script to verify exclusion functionality still works after removing fallback."""

import sys
import os
import tempfile
from pathlib import Path

# Add the project directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from blitzer_cli.processor import process_text
from blitzer_cli.config import get_config_dir
from blitzer_cli.cli import main

def test_exclusion_with_config_file():
    """Test that exclusion lists work when specified in config location."""
    print("Testing exclusion list functionality with config file...")
    
    # Create a temporary directory to simulate the config directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create the config directory structure
        config_dir = Path(temp_dir) / 'blitzer'
        config_dir.mkdir()
        
        # Create an exclusion file for Pali
        exclusion_file = config_dir / 'pli_exclusion.txt'
        with open(exclusion_file, 'w', encoding='utf-8') as f:
            f.write("sabbe\n")  # Add "sabbe" to exclusion list
            f.write("dhammā\n")  # Add "dhammā" to exclusion list
        
        # Temporarily set the XDG config home to our temp directory
        original_xdg = os.environ.get('XDG_CONFIG_HOME')
        os.environ['XDG_CONFIG_HOME'] = temp_dir
        
        try:
            # Import after setting environment variable
            from blitzer_cli.processor import get_language_processor
            
            # Create a temporary config directory override function
            import blitzer_cli.processor as proc_module
            original_get_config_dir = proc_module.get_config_dir
            
            # Mock the get_config_dir to return our temp directory
            def mock_get_config_dir():
                return config_dir
            
            proc_module.get_config_dir = mock_get_config_dir
            
            try:
                # Test that excluded words are filtered out
                text = "sabbe dhammā aniccā sabbe"
                result = process_text(text, 'pli', 'word_list', freq_flag=True)
                
                # Check that excluded words are not in the result
                lines = result.strip().split('\n')
                result_words = [line.split(';')[0] for line in lines if line and ';' in line]
                
                if 'sabbe' not in result_words and 'dhammā' not in result_words:
                    print("Exclusion functionality: SUCCESS - Excluded words were filtered out")
                    print(f"Result: {result[:100]}...")
                else:
                    print("Exclusion functionality: FAILED - Excluded words were not filtered out")
                    print(f"Result: {result}")
                    
            finally:
                # Restore original function
                proc_module.get_config_dir = original_get_config_dir
                
        finally:
            # Restore original environment variable
            if original_xdg is not None:
                os.environ['XDG_CONFIG_HOME'] = original_xdg
            else:
                os.environ.pop('XDG_CONFIG_HOME', None)


def test_generic_processor():
    """Test that generic processor works for unsupported languages."""
    print("\nTesting generic processor for unsupported language...")
    
    try:
        # The generic processor should handle any language code
        text = "hello world hello"
        result = process_text(text, 'eng', 'word_list', freq_flag=True)
        print("Generic processor: SUCCESS - Processed unsupported language")
        print(f"Sample output: {result[:100]}...")
    except Exception as e:
        print(f"Generic processor: FAILED - {e}")


def test_no_exclusion_file():
    """Test that processing works when no exclusion file exists."""
    print("\nTesting processing without exclusion file...")
    
    try:
        text = "hello world hello"
        result = process_text(text, 'eng', 'word_list', freq_flag=True)
        print("No exclusion file: SUCCESS - Processing works without exclusion file")
        print(f"Sample output: {result[:100]}...")
    except Exception as e:
        print(f"No exclusion file: FAILED - {e}")


if __name__ == "__main__":
    print("Running exclusion tests after fallback removal...\n")
    
    test_exclusion_with_config_file()
    test_generic_processor()
    test_no_exclusion_file()
    
    print("\nExclusion tests completed.")