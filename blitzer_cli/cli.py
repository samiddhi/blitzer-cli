#!/usr/bin/env python3
"""
Minimalist CLI tool for language text processing.
Accepts text via stdin and outputs word lists via stdout.
"""

import sys
import subprocess
import click
from blitzer_cli.processor import process_text, get_available_languages
from blitzer_cli.config import load_config


@click.group(invoke_without_command=False)
def cli():
    """Blitzer CLI: Vocabulary extraction for language learners."""
    pass


@cli.command("blitz", help="Return wordlist from text.")
@click.option("--text", "-t", help="Direct text input (overrides stdin).")
@click.option("--language_code", "-l", required=True, help="ISO 639 three-character language code or \"base\"/\"generic\" for simple processing.")
@click.option("--lemmatize", "-L", is_flag=True, help="Treats different declensions/forms of the same word as one word.")
@click.option("--freq", "-f", is_flag=True, help="Includes word frequency count in output.")
@click.option("--context", "-c", is_flag=True, help="Includes sample context for each word in output.")
@click.option("--prompt", "-p", is_flag=True, help="Includes custom prompt for LLM at the top of output.",)
@click.option("--src", "-s", is_flag=True, help="Includes the full source text at the top of output.")
def blitz(text, language_code, lemmatize, freq, context, prompt, src):
    # Language code must be provided
    if language_code is None:
        click.echo("Language code is required. Use -l or --language_code to specify a language.", err=True)
        raise click.Abort()

    input_text = text.strip() if text else sys.stdin.read().strip()

    if not input_text:
        click.echo("No input text provided.", err=True)
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
        print(f"Error processing text: {e}", file=sys.stderr)
        sys.exit(1)


@cli.command("languages", help="Manage language packs.")
@click.argument('action', type=click.Choice(['install', 'uninstall', 'list']))
@click.argument('language_code', required=False)
def manage_languages(action, language_code):
    if action == 'list':
        for lang in get_available_languages():
            click.echo(lang)
    elif action == 'install':
        if not language_code:
            click.echo("Please specify a language code to install.", err=True)
            raise click.Abort()
        
        package_name = f"blitzer-language-{language_code}"
        click.echo(f"Installing language pack: {package_name}")
        
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "install", package_name], 
                                  capture_output=True, text=True, check=True)
            click.echo(f"Successfully installed {package_name}")
            click.echo(result.stdout)
        except subprocess.CalledProcessError as e:
            click.echo(f"Failed to install {package_name}: {e}")
            click.echo(e.stderr)
            sys.exit(1)
    elif action == 'uninstall':
        if not language_code:
            click.echo("Please specify a language code to uninstall.", err=True)
            raise click.Abort()
        
        package_name = f"blitzer-language-{language_code}"
        click.echo(f"Uninstalling language pack: {package_name}")
        
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", package_name], 
                                  capture_output=True, text=True, check=True)
            click.echo(f"Successfully uninstalled {package_name}")
            click.echo(result.stdout)
        except subprocess.CalledProcessError as e:
            click.echo(f"Failed to uninstall {package_name}: {e}")
            click.echo(e.stderr)
            sys.exit(1)


if __name__ == "__main__":
    cli()
