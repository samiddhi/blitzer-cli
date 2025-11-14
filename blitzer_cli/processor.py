"""Core text processing functionality."""

import re
import os
import importlib.util
from collections import Counter
from typing import List, Dict, Optional
from pathlib import Path
from .config import get_config_dir


def split_sentences(text: str) -> List[str]:
    """Basic sentence tokenizer."""
    # Split on sentence delimiters followed by whitespace, but avoid splitting on abbreviations
    sentences = re.split(r'(?<!\b[A-Z]\.)(?<!\b[A-Z][a-z]\.)(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def basic_word_tokenize(text: str) -> List[str]:
    """Basic word tokenizer using alphanumeric characters."""
    words = re.findall(r'\b\w+\b', text.lower())
    return words


def get_language_processor(language_code: str):
    """Get the appropriate language processor based on language code."""
    # Set up paths for language-specific resources
    config_dir = get_config_dir()
    
    # Try to find language database in XDG config directory
    lexicon_db_path = config_dir / f"{language_code}_lexicon.db"
    exclusion_path = config_dir / f"{language_code}_exclusion.txt"
    
    # Load exclusion terms
    exclusion_terms = []
    if exclusion_path.exists():
        with open(exclusion_path, 'r', encoding="utf-8") as f:
            exclusion_terms = [line.strip() for line in f if line.strip()]
    else:
        # If exclusion file doesn't exist in config, try default location in package
        package_dir = Path(__file__).parent
        default_exclusion_path = package_dir / 'languages' / language_code / 'exclusion.txt'
        if default_exclusion_path.exists():
            with open(default_exclusion_path, 'r', encoding="utf-8") as f:
                exclusion_terms = [line.strip() for line in f if line.strip()]
    
    # Try to import the specific language processor
    if language_code == 'pli':
        from .languages.pli import PaliProcessor
        if lexicon_db_path.exists():
            return PaliProcessor(language_code, exclusion_terms, str(lexicon_db_path))
        else:
            return PaliProcessor(language_code, exclusion_terms, None)
    elif language_code == 'slv':
        from .languages.slv import SlovenianProcessor
        if lexicon_db_path.exists():
            return SlovenianProcessor(language_code, exclusion_terms, str(lexicon_db_path))
        else:
            return SlovenianProcessor(language_code, exclusion_terms, None)
    else:
        # If no specific processor found, use a generic one
        from .languages.base import BaseLanguageProcessor
        
        class GenericProcessor(BaseLanguageProcessor):
            def __init__(self, language_code: str, exclusion_list, lexicon_db_path=None):
                super().__init__(language_code, exclusion_list, lexicon_db_path)
            
            def tokenize_words(self, text: str) -> List[str]:
                return basic_word_tokenize(text)
            
            def lemmatize(self, word: str) -> List[str]:
                return [word.lower()]
            
            def get_definition(self, lemma: str) -> Optional[str]:
                return None
            
            def get_grammar_data(self, lemma: str) -> Optional[Dict]:
                return None
            
            def normalize(self, text: str) -> str:
                return text
        
        return GenericProcessor(language_code, exclusion_terms)


def process_text(text: str, language_code: str, mode: str, freq_flag: bool = False, 
                prompt_flag: bool = False, src_flag: bool = False) -> str:
    """Process text according to specified mode and options."""
    processor = get_language_processor(language_code)
    
    # Normalize text
    normalized_text = processor.normalize(text)
    
    # Apply mode-specific processing
    if mode == 'word_list':
        return _run_word_list_mode(normalized_text, processor, freq_flag, prompt_flag, src_flag)
    elif mode == 'lemma_list':
        return _run_lemma_list_mode(normalized_text, processor, freq_flag, prompt_flag, src_flag)
    elif mode == 'word_list_context':
        return _run_word_list_context_mode(normalized_text, processor, freq_flag, prompt_flag, src_flag)
    elif mode == 'lemma_list_context':
        return _run_lemma_list_context_mode(normalized_text, processor, freq_flag, prompt_flag, src_flag)
    else:
        raise ValueError(f"Unknown mode: {mode}")


def _run_word_list_mode(text: str, processor, freq_flag: bool, 
                       prompt_flag: bool, src_flag: bool) -> str:
    """Run word list mode."""
    words = processor.tokenize_words(text)
    word_counts = Counter(w.lower() for w in words)
    excluded_terms = set(processor.exclusion_list)  # Using set for faster lookup

    output_lines = []
    for word, count in sorted(word_counts.items(), key=lambda item: item[1], reverse=True):
        if word in excluded_terms:
            continue
        if freq_flag:
            output_lines.append(f"{word}; {count}")
        else:
            output_lines.append(f"{word}")
    
    return _format_output(output_lines, prompt_flag, src_flag, text)


def _run_lemma_list_mode(text: str, processor, freq_flag: bool, 
                        prompt_flag: bool, src_flag: bool) -> str:
    """Run lemma list mode."""
    words = processor.tokenize_words(text)
    lemma_counts = Counter()
    excluded_terms = set(processor.exclusion_list)  # Using set for faster lookup

    for word in words:
        if word in excluded_terms:  # This is not redundant!
            # This is for when the user would like to exclude a certain word form which /also/ is a form of an unknown word.
            # For example, in pali "samayaṃ" is a very common word for "time" but is also a valid declension of "samayanta".
            # It is common to know the former but not the rarer later. This if statement allows for the user to exclude
            # samayaṃ w/o needing to collaterally exclude samayanta as well. Hope this makes sense.
            continue
        lemmas = processor.lemmatize(word)
        if not lemmas:
            lemma_counts[word.lower()] += 1
        else:
            for lemma in lemmas:
                lemma_counts[lemma.lower()] += 1

    output_lines = []
    for lemma, count in sorted(lemma_counts.items(), key=lambda item: item[1], reverse=True):
        if lemma in excluded_terms:
            continue
        if freq_flag:
            output_lines.append(f"{lemma}; {count}")
        else:
            output_lines.append(f"{lemma}")
    
    return _format_output(output_lines, prompt_flag, src_flag, text)


def _run_word_list_context_mode(text: str, processor, freq_flag: bool, 
                               prompt_flag: bool, src_flag: bool) -> str:
    """Run word list with context mode."""
    sentences = split_sentences(text)
    word_occurrences = {}  # word -> list of sentences
    word_counts = Counter()
    excluded_terms = set(processor.exclusion_list)  # Using set for faster lookup

    for sentence in sentences:
        words_in_sentence = processor.tokenize_words(sentence)
        for original_word in words_in_sentence:
            if original_word in excluded_terms:
                continue
            word_lower = original_word.lower()
            word_counts[word_lower] += 1
            if word_lower not in word_occurrences:
                word_occurrences[word_lower] = []

            # Add sentence if not already added for this word and limit context sentences
            if len(word_occurrences[word_lower]) < 2 and sentence not in word_occurrences[word_lower]:
                # Bold the exact word in the sentence, preserving original casing
                # Use regex with word boundaries to avoid partial word bolding
                # Escape special characters in the word for regex
                escaped_word = re.escape(original_word)
                # Find all occurrences of the word (case-insensitive) and replace with bolded version
                # Use a callback to preserve original casing for the bolded word
                bolded_sentence = re.sub(r'\b(' + escaped_word + r')\b', r'<b>\1</b>', sentence, flags=re.IGNORECASE)
                word_occurrences[word_lower].append(bolded_sentence)

    output_lines = []
    for word, count in sorted(word_counts.items(), key=lambda item: item[1], reverse=True):
        contexts = word_occurrences.get(word, [])
        formatted_contexts = ['"' + s.replace('\n', '\\n') + '"' for s in contexts]
        if freq_flag:
            output_lines.append(word + "; " + str(count) + "; [" + ', '.join(formatted_contexts) + "]")
        else:
            output_lines.append(word + "; [" + ', '.join(formatted_contexts) + "]")
    
    return _format_output(output_lines, prompt_flag, src_flag, text)


def _run_lemma_list_context_mode(text: str, processor, freq_flag: bool, 
                                prompt_flag: bool, src_flag: bool) -> str:
    """Run lemma list with context mode."""
    sentences = split_sentences(text)
    lemma_occurrences = {}  # lemma -> list of sentences
    lemma_counts = Counter()
    excluded_terms = set(processor.exclusion_list)  # Using set for faster lookup

    for sentence in sentences:
        words_in_sentence = processor.tokenize_words(sentence)
        for original_word in words_in_sentence:
            if original_word in excluded_terms:  # This is not redundant!
                # This is for when the user would like to exclude a certain word form which /also/ is a form of an unknown word.
                # For example, in pali "samayaṃ" is a very common word for "time" but is also a valid declension of "samayanta".
                # It is common to know the former but not the rarer later. This if statement allows for the user to exclude
                # samayaṃ w/o needing to collaterally exclude samayanta as well. Hope this makes sense.
                continue
            lemmas = processor.lemmatize(original_word)
            if not lemmas:
                lemmas = [original_word.lower()]  # Fallback to original word if no lemma

            for lemma in lemmas:
                lemma_lower = lemma.lower()
                lemma_counts[lemma_lower] += 1
                if lemma_lower not in lemma_occurrences:
                    lemma_occurrences[lemma_lower] = []

                if len(lemma_occurrences[lemma_lower]) < 2 and sentence not in lemma_occurrences[lemma_lower]:
                    # Bold the original word form that maps to the lemma
                    escaped_original_word = re.escape(original_word)
                    bolded_sentence = re.sub(r'\b(' + escaped_original_word + r')\b', r'<b>\1</b>', sentence, flags=re.IGNORECASE)
                    lemma_occurrences[lemma_lower].append(bolded_sentence)

    output_lines = []
    for lemma, count in sorted(lemma_counts.items(), key=lambda item: item[1], reverse=True):
        if lemma in excluded_terms:
            continue
        contexts = lemma_occurrences.get(lemma, [])
        formatted_contexts = ['"' + s.replace('\n', '\\n') + '"' for s in contexts]
        if freq_flag:
            output_lines.append(lemma + "; " + str(count) + "; [" + ', '.join(formatted_contexts) + "]")
        else:
            output_lines.append(lemma + "; [" + ', '.join(formatted_contexts) + "]")
    
    return _format_output(output_lines, prompt_flag, src_flag, text)


def _format_output(output_lines: List[str], prompt_flag: bool, src_flag: bool, source_text: str) -> str:
    """Format output with optional prompt and source text."""
    result = []
    
    if src_flag:
        result.append("SOURCE TEXT:")
        result.append("")
        result.append(source_text)
        result.append("")
        result.append("------")
    
    if prompt_flag:
        result.append("PROMPT:")
        result.append("")
        result.append("Process the following text for vocabulary extraction.")
        result.append("")
        result.append("------")
        result.append("******")
        result.append("------")
        result.append("")
    
    result.extend(output_lines)
    result.append("")  # Add final newline
    
    return "\n".join(result)