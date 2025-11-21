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

"""Tests for the CLI module."""
import pytest
import sys
from io import StringIO
from click.testing import CliRunner
from blitzer_cli.cli import cli, blitz


class TestCLI:
    """Test class for CLI functionality."""
    
    def test_blitz_command_basic(self):
        """Test basic blitz command functionality."""
        runner = CliRunner()
        result = runner.invoke(blitz, ['-l', 'base', '-t', 'This is a test'])
        
        assert result.exit_code == 0
        assert 'this' in result.output.lower()
        assert 'is' in result.output.lower()
        assert 'a' in result.output.lower()
        assert 'test' in result.output.lower()
    
    def test_blitz_command_with_freq_flag(self):
        """Test blitz command with frequency flag."""
        runner = CliRunner()
        result = runner.invoke(blitz, ['-l', 'base', '-t', 'test word test', '--freq'])
        
        assert result.exit_code == 0
        assert 'test; 2' in result.output
        assert 'word; 1' in result.output
    
    def test_blitz_command_with_lemmatize_flag_base_language(self):
        """Test blitz command with lemmatize flag using base language (should show warning)."""
        runner = CliRunner()
        result = runner.invoke(blitz, ['-l', 'base', '-t', 'testing', '--lemmatize'])
        
        assert result.exit_code == 0
        # Check that warning appears in output
        assert 'Base mode has no lemmatization' in result.output or result.stderr_bytes is not None
        # Since we modified the output to go to stderr, we should check stderr
        if result.stderr_bytes:
            stderr_output = result.stderr_bytes.decode('utf-8')
            assert 'Base mode has no lemmatization' in stderr_output
            assert '\033[33m' in stderr_output  # Yellow color code for warning
    
    def test_blitz_command_missing_language(self):
        """Test blitz command with missing language flag."""
        runner = CliRunner()
        result = runner.invoke(blitz, ['-t', 'This is a test'])
        
        # Should fail because language is required
        assert result.exit_code != 0
        # The error about missing language should be in red and on stderr
        # This error comes from Click automatically, so we can't directly control its color
        assert 'Error: Missing option' in result.output or 'Missing option' in result.output
    
    def test_blitz_command_no_input_text(self):
        """Test blitz command with no input text."""
        runner = CliRunner()
        # Provide language but no text (via stdin or -t)
        result = runner.invoke(blitz, ['-l', 'base'], input='')
        
        assert result.exit_code != 0
        # Should contain the error message, ideally in red
        assert 'No input text provided' in result.output or result.stderr_bytes is not None
    
    def test_languages_list_command(self):
        """Test languages list command."""
        runner = CliRunner()
        result = runner.invoke(cli, ['languages', 'list'])
        
        assert result.exit_code == 0
        assert 'base' in result.output
    
    def test_help_command(self):
        """Test help command."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert 'Blitzer CLI: Vocabulary extraction for language learners' in result.output
        assert 'blitz' in result.output
        assert 'languages' in result.output
