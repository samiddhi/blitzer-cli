"""Base language processing module."""

import abc
import sqlite3
from typing import List, Optional, Dict


class BaseLanguageProcessor(abc.ABC):
    """Base class for language-specific text processing."""
    
    def __init__(self, language_code: str, exclusion_list: List[str], lexicon_db_path: Optional[str] = None):
        self.language_code = language_code
        self.lexicon_db_path = lexicon_db_path
        self.conn = None
        self.exclusion_list = exclusion_list
    
    def _connect_db(self):
        """Establishes an SQLite connection if lexicon_db_path is provided."""
        if self.lexicon_db_path and self.conn is None:
            try:
                self.conn = sqlite3.connect(self.lexicon_db_path)
            except sqlite3.Error as e:
                print(f"Error connecting to database at {self.lexicon_db_path}: {e}")
                self.conn = None
        return self.conn

    @abc.abstractmethod
    def tokenize_words(self, text: str) -> List[str]:
        """Tokenize text into words."""
        pass
    
    @abc.abstractmethod
    def lemmatize(self, word: str) -> List[str]:
        """Lemmatize a word and return its root forms."""
        pass
    
    @abc.abstractmethod
    def get_definition(self, lemma: str) -> Optional[str]:
        """Get definition for a lemma."""
        pass
    
    @abc.abstractmethod
    def get_grammar_data(self, lemma: str) -> Optional[Dict]:
        """Get grammar data for a lemma."""
        pass
    
    @abc.abstractmethod
    def normalize(self, text: str) -> str:
        """Normalize text."""
        pass