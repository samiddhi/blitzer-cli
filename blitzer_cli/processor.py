"""Core text processing functionality."""

import re
from collections import Counter, defaultdict
from typing import List, Dict, Optional
from pathlib import Path
import importlib
from .config import get_config_dir


def split_sentences(text: str) -> List[str]:
    """Basic sentence tokenizer."""
    sentences = re.split(r"(?<!\b[A-Z]\.)(?<!\b[A-Z][a-z]\.)(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def basic_word_tokenize(text: str) -> List[str]:
    """Basic word tokenizer using alphanumeric characters."""
    return re.findall(r"\b\w+\b", text.lower())


def get_language_processor(language_code: str):
    """Dynamically load processor for the language, with fallback to base."""
    config_dir = get_config_dir()
    lexicon_db_path = config_dir / f"{language_code}_lexicon.db"
    exclusion_path = config_dir / f"{language_code}_exclusion.txt"
    exclusion_terms = []
    if exclusion_path.exists():
        with open(exclusion_path, "r", encoding="utf-8") as f:
            exclusion_terms = [line.strip().lower() for line in f if line.strip()]
    db_path = str(lexicon_db_path) if lexicon_db_path.exists() else None
    try:
        module = importlib.import_module(f"blitzer_cli.languages.{language_code}")
    except ImportError:
        raise ValueError(f"Unsupported language: {language_code}")
    return module.get_processor(language_code, exclusion_terms, db_path)


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
