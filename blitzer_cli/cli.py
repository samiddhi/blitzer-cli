#!/usr/bin/env python3
"""
Minimalist CLI tool for language text processing.
Accepts text via stdin and outputs word lists via stdout.
"""

import sys
import click
import pkgutil
from blitzer_cli.processor import process_text
from blitzer_cli.config import load_config
from blitzer_cli.languages import __path__ as languages_path


def get_supported_languages():
    supported = []
    for _, module_name, _ in pkgutil.iter_modules(languages_path):
        if module_name != "__init__":
            supported.append(module_name)
    return supported


@click.group(invoke_without_command=False)
def cli():
    """Blitzer CLI: Vocabulary extraction for language learners."""
    pass


@cli.command("blitz", help="Return wordlist from text.")
@click.option("--text", "-t", help="Direct text input (overrides stdin).")
@click.argument("language_code", required=False)
@click.argument("mode", required=False)
@click.option("--freq", "-f", is_flag=True, help="Includes word frequency count in output.")
@click.option("--prompt", "-p", is_flag=True, help="Includes custom prompt for LLM at the top of output.")
@click.option("--src", "-s", help="Includes the full source text at the top of output.")
def blitz(text, language_code, mode, freq, prompt, src):
    config = load_config()

    # Use config defaults if not provided via command line
    if language_code is None:
        language_code = config.get("default_language", "base")
    if mode is None:
        mode = config.get("default_mode", "word_list")

    input_text = text.strip() if text else sys.stdin.read().strip()

    if not input_text:
        click.echo("No input text provided.", err=True)
        raise click.Abort()

    # Process the text
    try:
        output = process_text(
            input_text,
            language_code,
            mode,
            freq_flag=freq,
            prompt_flag=prompt,
            src_flag=src,
        )

        # Output to stdout
        print(output, end="")

    except Exception as e:
        print(f"Error processing text: {e}", file=sys.stderr)
        sys.exit(1)

@cli.command("list", help="Lists supported languages for lemmatization.")
def list_languages():
    for lang in get_supported_languages():
        click.echo(lang)


if __name__ == "__main__":
    cli()
