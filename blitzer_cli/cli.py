#!/usr/bin/env python3
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

"""
Minimalist CLI tool for language text processing.
Accepts text via stdin and outputs word lists via stdout.
"""

import re
import sys
import subprocess
import click
from blitzer_cli.processor import process_text, get_available_languages
from blitzer_cli.config import load_config
from blitzer_cli.utils import print_error


@click.group(invoke_without_command=False)
def cli():
    """Blitzer CLI: Vocabulary extraction for language learners."""
    pass


@cli.command("blitz", help="Return wordlist from text.")
@click.option("--text", "-t", help="Direct text input (overrides stdin).")
@click.option("--language_code", "-l", required=True, help="ISO 639 three-character language code or \"base\" for simple processing.")
@click.option("--lemmatize/--no-lemmatize", "-L", default=None, help="Treats different declensions/forms of the same word as one word.")
@click.option("--freq/--no-freq", "-f", default=None, help="Includes word frequency count in output.")
@click.option("--context/--no-context", "-c", default=None, help="Includes sample context for each word in output.")
@click.option("--prompt/--no-prompt", "-p", default=None, help="Includes custom prompt for LLM at the top of output.",)
@click.option("--src/--no-src", "-s", default=None, help="Includes the full source text at the top of output.")
def blitz(text, language_code, lemmatize, freq, context, prompt, src):
    # Load config to use defaults for flags
    config = load_config()
    
    # Use config defaults if CLI flags weren't explicitly set
    lemmatize = lemmatize if lemmatize is not None else config.get('default_lemmatize', False)
    freq = freq if freq is not None else config.get('default_freq', False)
    context = context if context is not None else config.get('default_context', False)
    prompt = prompt if prompt is not None else config.get('default_prompt', False)
    src = src if src is not None else config.get('default_src', False)

    input_text = text.strip() if text else sys.stdin.read().strip()

    if not input_text:
        print_error("No input text provided.")
        raise click.Abort()

    # Process the text
    try:
        output = process_text(
            input_text,
            language_code,
            lemmatize_flag=lemmatize,
            freq_flag=freq,
            context_flag=context,
            prompt_flag=prompt,
            src_flag=src,
        )

        # Output to stdout
        print(output, end="")

    except Exception as e:
        print_error(f"Error processing text: {e}")
        sys.exit(1)


def validate_language_code(language_code: str) -> bool:
    """Validate language code format to prevent injection."""
    if not language_code:
        return False
    # Require 3-letter ISO 639 language codes
    return bool(re.match(r'^[a-z]{3}$', language_code))


@cli.command("languages", help="Manage language packs.")
@click.argument('action', type=click.Choice(['install', 'uninstall', 'list']))
@click.argument('language_code', required=False)
def manage_languages(action, language_code):
    if action == 'list':
        for lang in get_available_languages():
            click.echo(lang)
    elif action in ['install', 'uninstall']:
        if not language_code:
            print_error("Please specify a language code to install.")
            raise click.Abort()
        
        # Validate the language code to prevent injection
        if not validate_language_code(language_code):
            print_error(f"Invalid language code format: {language_code}. Use 3 lowercase letters (ISO 639-3).")
            raise click.Abort()
        
        package_name = f"blitzer-language-{language_code}"
        click.echo(f"Installing language pack: {package_name}")
        
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "install", package_name], 
                                  capture_output=True, text=True, check=True)
            click.echo(f"Successfully installed {package_name}")
            click.echo(result.stdout)
        except subprocess.CalledProcessError as e:
            print_error(f"Failed to install {package_name}: {e}")
            print_error(e.stderr)
            sys.exit(1)
    elif action == 'uninstall':
        if not language_code:
            print_error("Please specify a language code to uninstall.")
            raise click.Abort()
        
        # Validate the language code to prevent injection
        if not validate_language_code(language_code):
            print_error(f"Invalid language code format: {language_code}. Use 3 lowercase letters (ISO 639-3).")
            raise click.Abort()
        
        package_name = f"blitzer-language-{language_code}"
        click.echo(f"Uninstalling language pack: {package_name}")
        
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", package_name], 
                                  capture_output=True, text=True, check=True)
            click.echo(f"Successfully uninstalled {package_name}")
            click.echo(result.stdout)
        except subprocess.CalledProcessError as e:
            print_error(f"Failed to uninstall {package_name}: {e}")
            print_error(e.stderr)
            sys.exit(1)


if __name__ == "__main__":
    cli()
