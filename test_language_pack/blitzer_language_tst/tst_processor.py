"""Test language processor (TST)."""

import re
import sqlite3
import os
from pathlib import Path
from typing import List, Optional, Dict
from blitzer_cli.languages.base import BaseLanguageProcessor


class TestProcessor(BaseLanguageProcessor):
    """Test-specific text processing with made-up words."""
    
    def __init__(self, language_code: str, exclusion_list: List[str], lexicon_db_path: Optional[str] = None):
        # If no lexicon_db_path is provided, try to find it in the package
        if not lexicon_db_path:
            # Try to get the database from the installed package
            import blitzer_language_tst
            package_dir = Path(blitzer_language_tst.__file__).parent
            db_path = package_dir / "tst_lexicon.db"
            if db_path.exists():
                lexicon_db_path = str(db_path)
        
        super().__init__(language_code, exclusion_list, lexicon_db_path)
        self._connect_db()
        self.exclusion_list = [self.normalize(word) for word in exclusion_list]

    def tokenize_words(self, text: str) -> List[str]:
        # Test language tokenization with special characters
        words = re.findall(r"\b\w+\b", text, re.IGNORECASE)
        return [self.normalize(word.lower()) for word in words]

    def lemmatize(self, word: str) -> List[str]:
        lemmas = []
        if not self.conn:
            return [word.lower()]

        cursor = self.conn.cursor()
        try:
            # Query 'lookup' table for the word
            cursor.execute("SELECT headwords FROM lookup WHERE lookup_key = lower(?)", (word,))
            result = cursor.fetchone()

            if result:
                headwords_str = result[0]
                if not headwords_str:  # Handles both None and empty string
                    # If headwords is empty or None, lookup_key itself is the lemma
                    return [word.lower()]
                else:
                    # Parse the bracketed, comma-separated list of IDs as per instructions
                    stripped_headwords = headwords_str.strip('[]')
                    id_strings = [s.strip() for s in stripped_headwords.split(',')]

                    int_ids = []
                    for s in id_strings:
                        if s.isdigit():  # Ensure it's a valid number before converting
                            int_ids.append(int(s))

                    if int_ids:  # Check if we actually got any valid IDs
                        # Create placeholders for the IN clause
                        placeholders = ', '.join('?' * len(int_ids))

                        # Query 'dpd_headwords' for all IDs in a single query
                        cursor.execute(f"SELECT lemma_1 FROM dpd_headwords WHERE id IN ({placeholders})", tuple(int_ids))
                        lemma_results = cursor.fetchall()
                        for lemma_result in lemma_results:
                            # Extract the base lemma by splitting at the first space,
                            # effectively stripping numerical suffixes like ' 1', ' 2'
                            base_lemma = lemma_result[0].split(' ')[0].lower()
                            lemmas.append(base_lemma)

            return list(set(lemmas)) if lemmas else [word.lower()]
        except Exception as e:  # Catch any general exception, including parsing errors
            print(f"Error lemmatizing '{word}': {e}")
            return [word.lower()]

    def normalize(self, text: str) -> str:
        """
        Normalize test language text
        """
        return text.lower()


def get_processor(language_code: str, exclusion_list: List[str], lexicon_db_path: Optional[str] = None):
    """Factory function to create and return a TestProcessor instance."""
    return TestProcessor(language_code, exclusion_list, lexicon_db_path)