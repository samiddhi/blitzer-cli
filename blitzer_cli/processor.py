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
    
    # Process each unique token only once to minimize database queries
    seen_tokens = set()
    token_cache = {}  # Cache for query results
    
    processed_tokens = []
    
    for token in tokens:
        lower_token = token.lower()
        
        # Check if we've already processed this token (case-insensitively)
        if lower_token not in token_cache:
            # Query for lemma using case-insensitive match
            cursor.execute(
                "SELECT l.lemma FROM Lemmas l JOIN Forms f ON l.id = f.lemma_id WHERE f.form_representation = ? COLLATE NOCASE", 
                (lower_token,)
            )
            results = cursor.fetchall()
            
            if not results:
                # If no rows found, keep surface token
                token_cache[lower_token] = [token]
            elif len(results) == 1:
                # If one row, use that lemma
                token_cache[lower_token] = [results[0][0]]
            else:
                # If multiple rows, return each possible lemma
                token_cache[lower_token] = [row[0] for row in results]
        
        # Add the cached result(s) to the output
        processed_tokens.extend(token_cache[lower_token])
    
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
    
    available_languages = ['base', 'generic']  # Add base/generic as always available
    for ep in language_eps:
        available_languages.append(ep.name)
    
    return sorted(set(available_languages))  # Use set to avoid duplicates