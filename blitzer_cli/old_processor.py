"""Core text processing functionality."""

import re
from collections import Counter, defaultdict
from typing import List, Dict, Optional
from pathlib import Path
import importlib
from .config import get_config_dir
from .data_manager import get_language_data_path, ensure_language_data


def process_text(
    text: str,
    language_code: str,
    lemmatize_flag: bool = False,
    freq_flag: bool = False,
    context_flag: bool = False,
    prompt_flag: bool = False,
    src_flag: bool = False,
) -> str:
    """Process text according to specified flags."""
    processor = get_language_processor(language_code)
    normalized_text = processor.normalize(text)
    return _process_core(
        normalized_text,
        processor,
        lemmatize_flag,
        freq_flag,
        context_flag,
        prompt_flag,
        src_flag,
    )


def _process_core(
    text: str,
    processor,
    lemmatize_flag: bool,
    freq_flag: bool,
    context_flag: bool,
    prompt_flag: bool,
    src_flag: bool,
) -> str:
    """Unified core: tokenize, lemmatize/count/exclude, optional contexts."""
    excluded_terms = set(processor.exclusion_list)
    counts = Counter()
    occurrences = defaultdict(list)
    seen_sentences = defaultdict(set)

    if context_flag:
        sentences = split_sentences(text)
        for sentence in sentences:
            words_in_sentence = processor.tokenize_words(sentence)
            for original_word in words_in_sentence:
                if (
                    original_word.lower() in excluded_terms
                ):  # Case-insensitive exclude on form
                    continue
                lemmas = (
                    processor.lemmatize(original_word)
                    if lemmatize_flag
                    else [original_word]
                )
                if not lemmas:
                    lemmas = [original_word]
                for lemma in lemmas:
                    key = lemma.lower()
                    counts[key] += 1
                    if (
                        len(occurrences[key]) < 2
                        and sentence not in seen_sentences[key]
                    ):
                        seen_sentences[key].add(sentence)
                        escaped = re.escape(original_word)
                        bolded = re.sub(
                            r"\b(" + escaped + r")\b",
                            r"<b>\1</b>",
                            sentence,
                            flags=re.IGNORECASE,
                        )
                        occurrences[key].append(bolded)
    else:
        words = processor.tokenize_words(text)
        for original_word in words:
            if original_word.lower() in excluded_terms:
                continue
            if lemmatize_flag:
                lemmas = processor.lemmatize(original_word)
                if not lemmas:
                    counts[original_word.lower()] += 1
                else:
                    for lemma in lemmas:
                        counts[lemma.lower()] += 1
            else:
                counts[original_word.lower()] += 1

    output_lines = []
    for key, count in sorted(counts.items(), key=lambda item: item[1], reverse=True):
        if key in excluded_terms:
            continue
        if context_flag:
            contexts = occurrences[key]
            formatted = ['"' + s.replace("\n", "\\n") + '"' for s in contexts]
            joiner = ", ".join(formatted)
            if freq_flag:
                output_lines.append(f"{key}; {count}; [{joiner}]")
            else:
                output_lines.append(f"{key}; [{joiner}]")
        else:
            if freq_flag:
                output_lines.append(f"{key}; {count}")
            else:
                output_lines.append(f"{key}")

    return _format_output(output_lines, prompt_flag, src_flag, text)


def split_sentences(text: str) -> List[str]:
    """Basic sentence tokenizer."""
    sentences = re.split(r"(?<!\b[A-Z]\.)(?<!\b[A-Z][a-z]\.)(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def get_available_languages():
    """Get a list of all available languages (built-in + plugins)."""
    import importlib.util
    import pkgutil
    import logging
    from .languages import __path__ as languages_path
    
    # Get built-in languages
    builtin_languages = []
    for _, module_name, _ in pkgutil.iter_modules(languages_path):
        if module_name not in ["__init__", "base"]:  # Include all language modules including generic
            builtin_languages.append(module_name)
    
    # Get plugin languages
    plugin_languages = []
    try:
        # For Python 3.8+ with importlib.metadata, for older versions we use importlib_metadata
        try:
            from importlib.metadata import entry_points
        except ImportError:
            import importlib_metadata as metadata
            entry_points = metadata.entry_points
        
        # Check which version of entry_points API is available
        eps_obj = entry_points()
        if hasattr(eps_obj, 'select'): # 3.10+ syntax: entry_points() returns a selection object
            language_eps = eps_obj.select(group='blitzer.languages')
            logging.debug(f"Found {len(language_eps)} language entry points via select: {[ep.name for ep in language_eps]}")
        else: # 3.8-3.9 syntax: entry_points() returns a dict-like object
            language_eps = eps_obj.get('blitzer.languages', [])
            logging.debug(f"Found {len(language_eps)} language entry points via get: {[ep.name for ep in language_eps]}")
        
        for ep in language_eps:
            logging.debug(f"Processing entry point: {ep.name} -> {ep.value}")
            try:
                # Try loading the processor function to ensure it's valid
                processor_func = ep.load()
                logging.debug(f"Successfully loaded processor for {ep.name}")
                plugin_languages.append(ep.name)
            except Exception as e:
                logging.debug(f"Failed to load processor for {ep.name}: {e}")
                # Still add to plugin_languages but we might want to validate differently
                plugin_languages.append(ep.name)
    except Exception as e:
        logging.debug(f"Exception in plugin discovery: {e}")
        import traceback
        logging.debug(f"Traceback: {traceback.format_exc()}")
        pass  # If plugin discovery fails, continue with just builtin languages
    
    logging.debug(f"Builtin languages: {builtin_languages}")
    logging.debug(f"Plugin languages: {plugin_languages}")
    
    return sorted(set(builtin_languages + plugin_languages))


def get_language_processor(language_code: str):
    """Dynamically load processor for the language, with fallback to base."""
    import logging
    import importlib
    config_dir = get_config_dir()
    lexicon_db_path = config_dir / f"{language_code}_lexicon.db"
    exclusion_path = config_dir / f"{language_code}_exclusion.txt"
    exclusion_terms = []
    if exclusion_path.exists():
        with open(exclusion_path, "r", encoding="utf-8") as f:
            exclusion_terms = [line.strip().lower() for line in f if line.strip()]
    
    # Try to find a language-specific data file in the language_data directory
    db_path = None
    if lexicon_db_path.exists():
        db_path = str(lexicon_db_path)
    else:
        # Try to find language-specific data file using data manager
        db_file_path = get_language_data_path(language_code, f"{language_code}_lexicon.db")
        if db_file_path:
            db_path = str(db_file_path)
    
    # Try to load via plugin system first
    try:
        # For Python 3.8+ with importlib.metadata, for older versions we use importlib_metadata
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
            logging.debug(f"Found {len(language_eps)} language entry points for {language_code}: {[ep.name for ep in language_eps]}")
        else:
            # Python 3.8-3.9 syntax: entry_points() returns a dict-like object
            language_eps = eps_obj.get('blitzer.languages', [])
            logging.debug(f"Found {len(language_eps)} language entry points for {language_code} via get: {[ep.name for ep in language_eps]}")
        
        for ep in language_eps:
            logging.debug(f"Checking entry point: {ep.name} == {language_code} ?")
            if ep.name == language_code:
                logging.debug(f"Found matching entry point {ep.name}, loading: {ep.value}")
                try:
                    processor_func = ep.load()
                    logging.debug(f"Successfully loaded processor function for {language_code}")
                    return processor_func(language_code, exclusion_terms, db_path)
                except Exception as e:
                    logging.debug(f"Failed to load processor for {language_code}: {e}")
                    raise  # Re-raise to trigger fallback
    except Exception as e:
        logging.debug(f"Exception in plugin loading for {language_code}: {e}")
        import traceback
        logging.debug(f"Traceback: {traceback.format_exc()}")
        pass  # If plugin discovery fails, fall back to builtin
    
    # Fall back to built-in languages
    logging.debug(f"Falling back to built-in language module: {language_code}")
    try:
        module = importlib.import_module(f"blitzer_cli.languages.{language_code}")
        return module.get_processor(language_code, exclusion_terms, db_path)
    except ImportError:
        raise ValueError(f"Unsupported language: {language_code}")


def _format_output(
    output_lines: List[str], prompt_flag: bool, src_flag: bool, source_text: str
) -> str:
    """Format output with optional prompt and source text."""
    result = []
    if src_flag:
        result.extend(["SOURCE TEXT:", "", source_text, "", "------"])
    if prompt_flag:
        result.extend(
            [
                "PROMPT:",
                "",
                "Process the following text for vocabulary extraction.",
                "",
                "------",
                "******",
                "------",
                "",
            ]
        )
    result.extend(output_lines)
    result.append("")
    return "\n".join(result)
