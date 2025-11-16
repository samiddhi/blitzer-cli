"""Generic language processor for fallback use with space-separated languages."""

import re
from typing import List, Optional, Dict
from .base import BaseLanguageProcessor


class GenericProcessor(BaseLanguageProcessor):
    """Basic language processing for space-separated languages without specific features."""
    
    def __init__(self, language_code: str, exclusion_list: List[str], lexicon_db_path: Optional[str] = None):
        super().__init__(language_code, exclusion_list, lexicon_db_path)
        self.exclusion_list = exclusion_list

    def tokenize_words(self, text: str) -> List[str]:
        """Basic tokenization for space-separated languages using word boundaries."""
        return re.findall(r"\b\w+\b", text.lower())

    def lemmatize(self, word: str) -> List[str]:
        """Return the word as-is (no lemmatization)."""
        return [word.lower()]

    def get_definition(self, lemma: str) -> Optional[str]:
        """No definition support."""
        return None

    def get_grammar_data(self, lemma: str) -> Optional[Dict]:
        """No grammar data support."""
        return None

    def normalize(self, text: str) -> str:
        """No special normalization."""
        return text


def get_processor(language_code: str, exclusion_list: List[str], lexicon_db_path: Optional[str] = None):
    """Factory function to return a GenericProcessor instance."""
    return GenericProcessor(language_code, exclusion_list, lexicon_db_path)