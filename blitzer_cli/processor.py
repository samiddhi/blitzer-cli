"""New core text processing functionality following the specified architecture."""

import re
import sqlite3
import sys
from collections import Counter, defaultdict
from typing import List, Dict, Optional, Any
from pathlib import Path


# In-memory cache for database connections (per language)
_db_cache = {}


def regex_tokenize(text: str) -> list[str]:
    """Core fallback tokenizer using the regex library."""
    import regex
    # Pattern that works for 95% of languages: letters with optional diacritics/numbers/apostrophes/hyphens
    tokens = regex.findall(r"\p{L}+(?:[\p{M}\p{N}'\-]+\p{L}+)*", text.lower())
    return tokens


def process_text(
    text: str,
    language_code: str,
    lemmatize_flag: bool = False,
    freq_flag: bool = False,
    context_flag: bool = False,
    prompt_flag: bool = False,
    src_flag: bool = False,
) -> str:
    """Process text according to specified flags following the new architecture."""
    # Load language specification via entry points
    language_spec = get_language_spec(language_code)
    
    # Handle prompt flag - if flag is used but language doesn't have a configured prompt, warn and ignore
    if prompt_flag:
        prompt_text = get_language_prompt(language_code)
        if not prompt_text:
            print("WARNING: No language-specific prompt configured for this language. Ignoring --prompt flag.", file=sys.stderr)
            prompt_flag = False
    
    # 1. Normalization
    if language_spec.get("normalizer"):
        normalized_text = language_spec["normalizer"](text)
    else:
        normalized_text = text.lower()
    
    # 2. Tokenization  
    if language_spec.get("tokenizer"):
        tokens = language_spec["tokenizer"](normalized_text)
    else:
        tokens = regex_tokenize(normalized_text)
    
    # 3. Lemmatization (only if --lemmatize/-L and valid database provided)
    processed_tokens = []
    if lemmatize_flag and language_code in ['base', 'generic']:
        # If using base/generic language with lemmatize flag, issue warning and continue with original tokens
        print(f"WARNING: Base/generic mode has no lemmatization. Proceeding without lemmatization.", file=sys.stderr)
        processed_tokens = tokens
    elif lemmatize_flag and language_spec.get("custom_lemmatizer"):
        # Use custom lemmatizer if provided
        processed_tokens = language_spec["custom_lemmatizer"](tokens)
    elif lemmatize_flag and language_spec.get("db_path"):
        # Use generic SQL lemmatizer
        processed_tokens = sql_lemmatize_tokens(tokens, language_spec["db_path"])
    elif lemmatize_flag:
        # If lemmatize flag is set but no lemmatizer available, issue warning and continue with original tokens
        print(f"WARNING: No lemmatizer available for language {language_code}. Proceeding without lemmatization.", file=sys.stderr)
        processed_tokens = tokens
    else:
        # No lemmatization, keep original tokens
        processed_tokens = tokens
    
    # 4. Post-processing with exclusion list and formatting
    excluded_terms = get_exclusion_terms(language_code)
    return _format_output(
        processed_tokens, 
        normalized_text, 
        excluded_terms,
        freq_flag, 
        context_flag, 
        prompt_flag, 
        src_flag,
        language_code
    )


def get_language_spec(language_code: str) -> Dict[str, Any]:
    """Load language specification via entry points. Special handling for 'base' language."""
    # Special handling for 'base'/'generic' - return basic config without requiring a plugin
    if language_code in ['base', 'generic']:
        return {
            "db_path": None,
            "normalizer": None,
            "tokenizer": None,
            "custom_lemmatizer": None
        }
    
    try:
        from importlib.metadata import entry_points
    except ImportError:
        import importlib_metadata as metadata
        entry_points = metadata.entry_points
    
    # Check which version of entry_points API is available
    eps_obj = entry_points()
    if hasattr(eps_obj, 'select'):
        # Python 3.10+ syntax: entry_points() returns a selection object
        language_eps = eps_obj.select(group='blitzer.languages')
    else:
        # Python 3.8-3.9 syntax: entry_points() returns a dict-like object
        language_eps = eps_obj.get('blitzer.languages', [])
    
    for ep in language_eps:
        if ep.name == language_code:
            register_func = ep.load()
            return register_func()
    
    raise ValueError(f"Unsupported language: {language_code}")


def sql_lemmatize_tokens(tokens: List[str], db_path: str) -> List[str]:
    """Lemmatize tokens using SQLite database lookup with in-memory caching."""
    global _db_cache
    
    if not tokens:
        return []
    
    # Get or create database connection in cache
    if db_path not in _db_cache:
        conn = sqlite3.connect(db_path)
        _db_cache[db_path] = conn
    else:
        conn = _db_cache[db_path]
    
    cursor = conn.cursor()
    
    # Create mapping to preserve original tokens and their order
    token_to_lower = {token: token.lower() for token in tokens}
    unique_tokens = list(set(token_to_lower.values()))
    
    # Create a temporary table approach for batch lookup
    # First, create a temporary table with all the tokens we need to look up
    cursor.execute("CREATE TEMP TABLE temp_lookup (form TEXT)")
    
    # Insert all unique tokens into the temp table
    cursor.executemany("INSERT INTO temp_lookup (form) VALUES (?)", [(token,) for token in unique_tokens])
    
    # Perform a single JOIN query to get all lemmas at once
    cursor.execute("""
        SELECT tl.form, l.lemma 
        FROM temp_lookup tl
        JOIN Forms f ON f.form_representation = tl.form COLLATE NOCASE
        JOIN Lemmas l ON l.id = f.lemma_id
    """)
    
    # Group the results by form
    form_to_lemmas = {}
    for form, lemma in cursor.fetchall():
        if form not in form_to_lemmas:
            form_to_lemmas[form] = []
        form_to_lemmas[form].append(lemma)
    
    # Drop the temporary table
    cursor.execute("DROP TABLE temp_lookup")
    
    # For tokens not found in the database, we need to identify them
    # All unique tokens that have no lemmas are not found in DB
    not_found_tokens = set(unique_tokens) - set(form_to_lemmas.keys())
    
    # Build the result list in the original order
    processed_tokens = []
    for token in tokens:
        lower_token = token_to_lower[token]
        if lower_token in form_to_lemmas:
            # Token was found in DB, add all its lemmas
            processed_tokens.extend(form_to_lemmas[lower_token])
        else:
            # Token was not found in DB, add the original token
            processed_tokens.append(token)
    
    return processed_tokens


def get_exclusion_terms(language_code: str) -> set:
    """Get exclusion terms for the language."""
    from .config import get_config_dir
    config_dir = get_config_dir()
    exclusion_path = config_dir / f"{language_code}_exclusion.txt"
    exclusion_terms = set()
    if exclusion_path.exists():
        with open(exclusion_path, "r", encoding="utf-8") as f:
            exclusion_terms = {line.strip().lower() for line in f if line.strip()}
    return exclusion_terms


def get_language_prompt(language_code: str) -> Optional[str]:
    """Get language-specific prompt from configuration."""
    from .config import load_config
    config = load_config()
    prompts = config.get('prompts', {})
    return prompts.get(language_code)


def _format_output(
    tokens: List[str], 
    normalized_text: str, 
    excluded_terms: set,
    freq_flag: bool, 
    context_flag: bool, 
    prompt_flag: bool, 
    src_flag: bool,
    language_code: str
) -> str:
    """Format output based on flags."""
    import sys
    
    result_lines = []
    
    if src_flag:
        result_lines.extend(["SOURCE TEXT:", "", normalized_text, "", "------"])
    
    if prompt_flag:
        prompt_text = get_language_prompt(language_code)
        if prompt_text:
            result_lines.extend(["PROMPT:", "", prompt_text, "", "------", "******", "------", ""])
    
    # Calculate frequencies if needed
    if freq_flag:
        token_counts = Counter(token for token in tokens if token.lower() not in excluded_terms)
        for token, count in sorted(token_counts.items(), key=lambda x: x[1], reverse=True):
            result_lines.append(f"{token}; {count}")
    else:
        if context_flag:
            # For context, we need to map tokens back to sentences
            sentences = split_sentences(normalized_text)
            token_counts = Counter(token for token in tokens if token.lower() not in excluded_terms)
            
            for token, count in sorted(token_counts.items(), key=lambda x: x[1], reverse=True):
                contexts = []
                for sentence in sentences:
                    if token in sentence and len(contexts) < 2:  # Limit to 2 contexts
                        # Highlight the token in the sentence
                        escaped_token = re.escape(token)
                        highlighted = re.sub(
                            escaped_token,
                            f"<b>{token}</b>",
                            sentence,
                            flags=re.IGNORECASE
                        )
                        contexts.append(highlighted)
                
                if contexts:
                    context_str = ", ".join([f'"{c}"' for c in contexts])
                    if freq_flag:
                        result_lines.append(f"{token}; {count}; [{context_str}]")
                    else:
                        result_lines.append(f"{token}; [{context_str}]")
        else:
            # Simple token list without frequencies
            unique_tokens = set(token for token in tokens if token.lower() not in excluded_terms)
            for token in sorted(unique_tokens):
                result_lines.append(token)
    
    return "\n".join(result_lines) + "\n"


def split_sentences(text: str) -> List[str]:
    """Basic sentence tokenizer."""
    sentences = re.split(r"(?<!\b[A-Z]\.)(?<!\b[A-Z][a-z]\.)(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def get_available_languages():
    """Get a list of all available languages (plugins only + base)."""
    try:
        from importlib.metadata import entry_points
    except ImportError:
        import importlib_metadata as metadata
        entry_points = metadata.entry_points
    
    # Check which version of entry_points API is available
    eps_obj = entry_points()
    if hasattr(eps_obj, 'select'):
        # Python 3.10+ syntax: entry_points() returns a selection object
        language_eps = eps_obj.select(group='blitzer.languages')
    else:
        # Python 3.8-3.9 syntax: entry_points() returns a dict-like object
        language_eps = eps_obj.get('blitzer.languages', [])
    
    available_languages = ['base']  # Add base as always available (generic is equivalent but not listed separately)
    for ep in language_eps:
        available_languages.append(ep.name)
    
    return sorted(set(available_languages))  # Use set to avoid duplicates