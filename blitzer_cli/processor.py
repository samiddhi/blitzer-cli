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

"""New core text processing functionality following the specified architecture."""

import re
import sqlite3
from collections import Counter
from contextlib import contextmanager
from typing import List, Dict, Optional, Any

from blitzer_cli.utils import print_warning


# In-memory cache for database connections (per language)
_db_cache = {}


def regex_tokenize(text: str) -> List[str]:
    """Core fallback tokenizer using the standard re library with improved Unicode support."""
    import re
    # Use a space-based split first, then refine to handle punctuation within words
    # This approach better preserves international characters
    words = text.lower().split()
    tokens = []
    for word in words:
        # Extract sequences of letter characters (Unicode-aware)
        # This handles punctuation and special characters around words
        extracted = re.findall(r"[a-zA-Z\u00C0-\u017F\u0100-\u024F\u1E00-\u1EFF]+", word)
        tokens.extend(extracted)
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
            print("\033[31mWARNING: No language-specific prompt configured for this language. Ignoring --prompt flag.\033[0m", file=sys.stderr)
            prompt_flag = False
    
    # 1. Normalization
    if language_spec.get("normalizer"):
        normalized_text = language_spec["normalizer"](text)
    else:
        normalized_text = text.lower()
    
    # 2. Tokenization  
    if language_spec.get("tokenizer"):
        original_tokens = language_spec["tokenizer"](normalized_text)
    else:
        original_tokens = regex_tokenize(normalized_text)
    
    # 3. Lemmatization (only if --lemmatize/-L and valid database provided)
    processed_tokens = []
    original_to_processed_map = {}
    
    if lemmatize_flag and language_code == 'base':
        # If using base language with lemmatize flag, issue warning and continue with original tokens
        print_warning("Base mode has no lemmatization. Proceeding without lemmatization.")
        processed_tokens = original_tokens
        # Map each original token to itself
        for token in original_tokens:
            original_to_processed_map[token] = token
    elif lemmatize_flag and language_spec.get("custom_lemmatizer"):
        # Use custom lemmatizer if provided
        # This is more complex - need to get the mapping from the custom lemmatizer
        processed_tokens = language_spec["custom_lemmatizer"](original_tokens)
        # For now, assume the custom lemmatizer maintains order and maps 1:1
        # A more robust solution would return the mapping from the lemmatizer
        for orig, proc in zip(original_tokens, processed_tokens):
            if orig not in original_to_processed_map:
                original_to_processed_map[orig] = proc
    elif lemmatize_flag and language_spec.get("db_path"):
        # Use generic SQL lemmatizer with mapping support
        processed_tokens, original_to_processed_map = sql_lemmatize_tokens_with_mapping(original_tokens, language_spec["db_path"])
    elif lemmatize_flag:
        # If lemmatize flag is set but no lemmatizer available, issue warning and continue with original tokens
        print(f"\033[31mWARNING: No lemmatizer available for language {language_code}. Proceeding without lemmatization.\033[0m", file=sys.stderr)
        processed_tokens = original_tokens
        # Map each original token to itself
        for token in original_tokens:
            original_to_processed_map[token] = token
    else:
        # No lemmatization, keep original tokens
        processed_tokens = original_tokens
        # Map each original token to itself
        for token in original_tokens:
            original_to_processed_map[token] = token
    
    # 4. Post-processing with exclusion list and formatting
    excluded_terms = get_exclusion_terms(language_code)
    return _format_output(
        processed_tokens, 
        original_tokens,  # Pass original tokens for context extraction
        original_to_processed_map,  # Pass the mapping for context extraction
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
    # Special handling for 'base' - return basic config without requiring a plugin
    if language_code == 'base':
        return {
            "db_path": None,
            "normalizer": None,
            "tokenizer": None,
            "custom_lemmatizer": None
        }
    
    # Use the consistent function for entry points
    language_eps = get_entry_points()
    
    for ep in language_eps:
        if ep.name == language_code:
            register_func = ep.load()
            return register_func()
    
    raise ValueError(f"Unsupported language: {language_code}")


@contextmanager
def get_db_connection(db_path: str):
    """Context manager for database connections."""
    if db_path in _db_cache:
        conn = _db_cache[db_path]
        yield conn
    else:
        conn = sqlite3.connect(db_path)
        _db_cache[db_path] = conn
        try:
            yield conn
        finally:
            # Close connection on exception or when done, but only for new connections
            # In a production system, we might want more sophisticated connection management
            pass


def sql_lemmatize_tokens_with_mapping(tokens: List[str], db_path: str) -> tuple[List[str], Dict[str, str]]:
    """Lemmatize tokens using SQLite database lookup with in-memory caching and return mapping."""
    global _db_cache
    
    if not tokens:
        return [], {}
    
    with get_db_connection(db_path) as conn:
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
        
        # Build the result list in the original order and create mapping
        processed_tokens = []
        original_to_processed_map = {}
        for token in tokens:
            lower_token = token_to_lower[token]
            if lower_token in form_to_lemmas:
                # Token was found in DB, typically add the first lemma (most common/principal)
                lemmas = form_to_lemmas[lower_token]
                chosen_lemma = lemmas[0]  # Take first/default lemma
                processed_tokens.append(chosen_lemma)
                # Map the original token to the chosen lemma
                original_to_processed_map[token] = chosen_lemma
            else:
                # Token was not found in DB, add the original token
                processed_tokens.append(token)
                # Map the original token to itself  
                original_to_processed_map[token] = token
        
        return processed_tokens, original_to_processed_map


def sql_lemmatize_tokens(tokens: List[str], db_path: str) -> List[str]:
    """Lemmatize tokens using SQLite database lookup with in-memory caching."""
    processed_tokens, _ = sql_lemmatize_tokens_with_mapping(tokens, db_path)
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


def get_entry_points():
    """Get entry points in a version-compatible way."""
    try:
        from importlib.metadata import entry_points
        eps = entry_points()
        if hasattr(eps, 'select'):
            return eps.select(group='blitzer.languages')
        else:
            return eps.get('blitzer.languages', [])
    except ImportError:
        import importlib_metadata as metadata
        eps = metadata.entry_points()
        if hasattr(eps, 'select'):
            return eps.select(group='blitzer.languages')
        else:
            return eps.get('blitzer.languages', [])


def _format_output(
    tokens: List[str], 
    original_tokens: List[str], 
    original_to_processed_map: Dict[str, str],
    normalized_text: str, 
    excluded_terms: set,
    freq_flag: bool, 
    context_flag: bool, 
    prompt_flag: bool, 
    src_flag: bool,
    language_code: str
) -> str:
    """Format output based on flags."""
    
    result_lines = []
    
    if src_flag:
        result_lines.extend(["SOURCE TEXT:", "", normalized_text, "", "------"])
    
    if prompt_flag:
        prompt_text = get_language_prompt(language_code)
        if prompt_text:
            result_lines.extend(["PROMPT:", "", prompt_text, "", "------", "******", "------", ""])
    
    # Get token counts for frequency calculations using processed tokens
    token_counts = Counter(token for token in tokens if token.lower() not in excluded_terms)
    
    # Prepare sentence contexts if context flag is enabled
    sentence_contexts = {}
    if context_flag:
        sentences = split_sentences(normalized_text)
        
        for processed_token in token_counts.keys():
            contexts = []
            
            # For each sentence, check if it contains any original tokens that map to this processed token
            for sentence in sentences:
                sentence_lower = sentence.lower()
                
                # Find original tokens that map to the current processed token and appear in this sentence
                found_original_forms = []
                for orig_token, proc_token in original_to_processed_map.items():
                    if proc_token == processed_token:
                        # Check if this original token appears as a whole word in the sentence
                        pattern = r'\b' + re.escape(orig_token.lower()) + r'\b'
                        if re.search(pattern, sentence_lower):
                            found_original_forms.append(orig_token)
                
                # If we found original forms in this sentence, create the highlighted context
                if found_original_forms:
                    highlighted_sentence = sentence
                    # Highlight the first matching original form found in the sentence
                    # (to avoid overlapping replacements)
                    for orig_form in found_original_forms:
                        pattern = r'\b' + re.escape(orig_form) + r'\b'
                        highlighted_sentence = re.sub(
                            pattern,
                            f"<b>{orig_form}</b>",
                            highlighted_sentence,
                            flags=re.IGNORECASE
                        )
                    
                    # Replace newlines with <br> tags for proper formatting
                    highlighted_sentence = highlighted_sentence.replace('\n', '<br>').replace('\r', '<br>')
                    contexts.append(highlighted_sentence)
                    
                if len(contexts) >= 2:  # Limit to 2 contexts
                    break
    
            sentence_contexts[processed_token] = contexts
    
    # Build output for each token based on active flags
    for token, count in sorted(token_counts.items(), key=lambda x: x[1], reverse=True):
        output_parts = [token]
        
        # Add frequency if flag is set
        if freq_flag:
            output_parts.append(str(count))
        
        # Add context if flag is set and contexts were found
        if context_flag and sentence_contexts.get(token):
            context_str = ", ".join([f'"{c}"' for c in sentence_contexts[token]])
            output_parts.append(f"[{context_str}]")
        
        # Join parts with semicolons
        result_lines.append("; ".join(output_parts))
    
    return "\n".join(result_lines) + "\n"


def split_sentences(text: str) -> List[str]:
    """Basic sentence tokenizer."""
    sentences = re.split(r"(?<!\b[A-Z]\.)(?<!\b[A-Z][a-z]\.)(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def get_available_languages():
    """Get a list of all available languages (plugins only + base)."""
    # Use the consistent function for entry points
    language_eps = get_entry_points()
    
    available_languages = ['base']  # Add base as always available
    for ep in language_eps:
        available_languages.append(ep.name)
    
    return sorted(set(available_languages))  # Use set to avoid duplicates


def cleanup_db_connections():
    """Close all cached database connections."""
    global _db_cache
    for conn in _db_cache.values():
        conn.close()
    _db_cache.clear()
