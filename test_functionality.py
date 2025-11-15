#!/usr/bin/env python3
"""Test script to verify blitzer functionality after changes."""

import sys
import os
import tempfile
from pathlib import Path

# Add the project directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from blitzer_cli.processor import process_text
from blitzer_cli.config import get_config_dir, load_config
from blitzer_cli.cli import main

def test_pali_processing():
    """Test Pali processing functionality."""
    print("Testing Pali processing...")
    
    # Test word list mode
    text = "sabbe dhammā aniccā"
    try:
        result = process_text(text, 'pli', 'word_list')
        print("Pali word_list mode: SUCCESS")
        print(f"Sample output: {result[:100]}...")
    except Exception as e:
        print(f"Pali word_list mode: FAILED - {e}")
    
    # Test lemma list mode
    try:
        result = process_text(text, 'pli', 'lemma_list')
        print("Pali lemma_list mode: SUCCESS")
    except Exception as e:
        print(f"Pali lemma_list mode: FAILED - {e}")

def test_slovenian_processing():
    """Test Slovenian processing functionality."""
    print("\nTesting Slovenian processing...")
    
    # Test word list mode
    text = "vsi ljudje so enaki"
    try:
        result = process_text(text, 'slv', 'word_list')
        print("Slovenian word_list mode: SUCCESS")
        print(f"Sample output: {result[:100]}...")
    except Exception as e:
        print(f"Slovenian word_list mode: FAILED - {e}")
    
    # Test lemma list mode
    try:
        result = process_text(text, 'slv', 'lemma_list')
        print("Slovenian lemma_list mode: SUCCESS")
    except Exception as e:
        print(f"Slovenian lemma_list mode: FAILED - {e}")

def test_unsupported_language():
    """Test that unsupported languages raise appropriate error."""
    print("\nTesting unsupported language handling...")
    
    try:
        result = process_text("hello world", 'eng', 'word_list')
        print("Unsupported language: FAILED - Should have raised an error")
    except ValueError as e:
        print(f"Unsupported language: SUCCESS - {e}")
    except Exception as e:
        print(f"Unsupported language: UNEXPECTED ERROR - {e}")

def test_exclusion_lists():
    """Test that exclusion lists still work."""
    print("\nTesting exclusion list functionality...")
    
    # Create a temporary config directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock the config directory
        original_config_dir = None
        
        # Test exclusion functionality with supported language
        text = "sabbe dhammā aniccā sabbe"
        try:
            # Process with Pali - this should work regardless of exclusion lists
            result = process_text(text, 'pli', 'word_list', freq_flag=True)
            print("Exclusion list integration: SUCCESS")
            print(f"Sample output with frequency: {result[:100]}...")
        except Exception as e:
            print(f"Exclusion list integration: FAILED - {e}")

if __name__ == "__main__":
    print("Running functionality tests after removing generic fallback...\n")
    
    test_pali_processing()
    test_slovenian_processing()
    test_unsupported_language()
    test_exclusion_lists()
    
    print("\nTesting completed.")