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
        if module_name not in ["__init__", "base"]:  # Exclude abstract base class
            supported.append(module_name)
    return supported


@click.group(invoke_without_command=False)
def cli():
    """Blitzer CLI: Vocabulary extraction for language learners."""
    pass


@cli.command("blitz", help="Return wordlist from text.")
@click.option("--text", "-t", help="Direct text input (overrides stdin).")
@click.option("--language_code", "-l", required=True, help="ISO 639 three-character language code or \"generic\" for simple processing.\"")
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

@cli.command("list", help="Lists supported languages for lemmatization.")
def list_languages():
    for lang in get_supported_languages():
        click.echo(lang)


if __name__ == "__main__":
    cli()
