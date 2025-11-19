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
@click.option("--lemmatize/--no-lemmatize", "-L", default=None, help="Treats different declensions/forms of the same word as one word.")
@click.option("--freq/--no-freq", "-f", default=None, help="Includes word frequency count in output.")
@click.option("--context/--no-context", "-c", default=None, help="Includes sample context for each word in output.")
@click.option("--prompt/--no-prompt", "-p", default=None, help="Includes custom prompt for LLM at the top of output.",)
@click.option("--src/--no-src", "-s", default=None, help="Includes the full source text at the top of output.")
def blitz(text, language_code, lemmatize, freq, context, prompt, src):
    # Load config to use defaults for flags
    config = load_config()
    
    # Use config defaults if CLI flags weren't explicitly set
    if lemmatize is None:
        lemmatize = config.get('default_lemmatize', False)
    if freq is None:
        freq = config.get('default_freq', False)
    if context is None:
        context = config.get('default_context', False)
    if prompt is None:
        prompt = config.get('default_prompt', False)
    if src is None:
        src = config.get('default_src', False)

    input_text = text.strip() if text else sys.stdin.read().strip()

    if not input_text:
        print("\033[31mNo input text provided.\033[0m", file=sys.stderr)
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
        print(f"\033[31mError processing text: {e}\033[0m", file=sys.stderr)
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
            print("\033[31mPlease specify a language code to install.\033[0m", file=sys.stderr)
            raise click.Abort()
        
        package_name = f"blitzer-language-{language_code}"
        click.echo(f"Installing language pack: {package_name}")
        
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "install", package_name], 
                                  capture_output=True, text=True, check=True)
            click.echo(f"Successfully installed {package_name}")
            click.echo(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"\033[31mFailed to install {package_name}: {e}\033[0m", file=sys.stderr)
            print(f"\033[31m{e.stderr}\033[0m", file=sys.stderr)
            sys.exit(1)
    elif action == 'uninstall':
        if not language_code:
            print("\033[31mPlease specify a language code to uninstall.\033[0m", file=sys.stderr)
            raise click.Abort()
        
        package_name = f"blitzer-language-{language_code}"
        click.echo(f"Uninstalling language pack: {package_name}")
        
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", package_name], 
                                  capture_output=True, text=True, check=True)
            click.echo(f"Successfully uninstalled {package_name}")
            click.echo(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"\033[31mFailed to uninstall {package_name}: {e}\033[0m", file=sys.stderr)
            print(f"\033[31m{e.stderr}\033[0m", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    cli()
