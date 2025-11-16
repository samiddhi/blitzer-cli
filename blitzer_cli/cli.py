#!/usr/bin/env python3
"""
Minimalist CLI tool for language text processing.
Accepts text via stdin and outputs word lists via stdout.
"""

import sys
import click
from blitzer_cli.processor import process_text
from blitzer_cli.config import load_config


@click.command(
    epilog='Reads text from stdin, outputs to stdout. Example: `echo "text" | blitzer pli word_list`',
    context_settings={"help_option_names": ['-h', '--help']}
)
@click.argument('text', required=False)
@click.argument('language_code', required=False)
@click.argument('mode', required=False)
@click.option('--freq', 'freq_flag', is_flag=True, help='Include frequency counts')
@click.option('--prompt', 'prompt_flag', is_flag=True, help='Include prompt in output')
@click.option('--src', 'src_flag', is_flag=True, help='Include source text in output')
def main(text, language_code, mode, freq_flag, prompt_flag, src_flag):
    """Blitzer CLI - Process text and generate word lists."""
    # Load configuration
    config = load_config()
    
    # Use config defaults if not provided via command line
    if language_code is None:
        language_code = config.get('default_language', 'pli')
    if mode is None:
        mode = config.get('default_mode', 'word_list')
    

    if text is not None:
        input_text = text.strip()
    else:
        input_text = sys.stdin.read().strip()

    if not input_text:
        click.echo("No input text provided.", err=True)
        raise click.Abort()
    
    # Process the text
    try:
        output = process_text(
            input_text, 
            language_code, 
            mode, 
            freq_flag=freq_flag,
            prompt_flag=prompt_flag,
            src_flag=src_flag
        )
        
        # Output to stdout
        print(output, end='')
        
    except Exception as e:
        print(f"Error processing text: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()