"""Tests for the processor module."""
import pytest
import sys
from io import StringIO
from blitzer_cli.processor import process_text, get_language_spec, get_available_languages


class TestProcessor:
    """Test class for processor functionality."""
    
    def test_basic_processing(self):
        """Test basic text processing."""
        text = "This is a test sentence. This is another test."
        result = process_text(text, "base", lemmatize_flag=False, freq_flag=False, context_flag=False)
        lines = result.strip().split('\n')
        # Should contain individual tokens
        assert 'this' in result
        assert 'is' in result
        assert 'a' in result
    
    def test_frequency_flag(self):
        """Test frequency flag functionality."""
        text = "test word test another word test"
        result = process_text(text, "base", lemmatize_flag=False, freq_flag=True, context_flag=False)
        lines = result.strip().split('\n')
        # Should contain frequency counts
        assert 'test; 3' in result
        assert 'word; 2' in result
        assert 'another; 1' in result
    
    def test_context_flag(self):
        """Test context flag functionality."""
        text = "This is a test sentence. Another test appears here."
        result = process_text(text, "base", lemmatize_flag=False, freq_flag=False, context_flag=True)
        # Should contain contexts
        assert '[\"' in result  # Contexts are enclosed in quotes
        assert '<b>' in result  # Contexts highlight the word
    
    def test_prompt_flag_with_base_language(self):
        """Test prompt flag functionality."""
        text = "This is a test."
        result = process_text(text, "base", lemmatize_flag=False, freq_flag=False, context_flag=False, prompt_flag=True)
        # Should contain the prompt for base language
        assert 'PROMPT:' in result
        assert 'Convert the following wordlist into tab separated anki cards.' in result
    
    def test_lemmatization_warning_base_language(self, capfd):
        """Test that lemmatization with base language shows warning."""
        text = "testing tests"
        process_text(text, "base", lemmatize_flag=True, freq_flag=False, context_flag=False)
        
        captured = capfd.readouterr()
        # Check that error message is in stderr and is yellow-colored (warning)
        assert 'Base mode has no lemmatization' in captured.err
        assert '\033[33m' in captured.err  # Yellow color code for warning
        assert '\033[0m' in captured.err  # Reset color code
    
    def test_language_spec_base(self):
        """Test getting language specification for base language."""
        spec = get_language_spec("base")
        assert isinstance(spec, dict)
        assert spec.get("db_path") is None
        assert spec.get("normalizer") is None
        assert spec.get("tokenizer") is None
        assert spec.get("custom_lemmatizer") is None
    
    def test_available_languages_includes_base(self):
        """Test that available languages includes base."""
        languages = get_available_languages()
        assert 'base' in languages
        assert isinstance(languages, list)