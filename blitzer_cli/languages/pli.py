"""Pali language processor."""

import re
import sqlite3
from typing import List, Optional, Dict
from .base import BaseLanguageProcessor


class PaliProcessor(BaseLanguageProcessor):
    """Pali-specific text processing."""
    
    def __init__(self, language_code: str, exclusion_list: List[str], lexicon_db_path: Optional[str] = None):
        super().__init__(language_code, exclusion_list, lexicon_db_path)
        self._connect_db()
        self.exclusion_list = [self.normalize(word) for word in exclusion_list]

    def tokenize_words(self, text: str) -> List[str]:
        # Pali specific tokenization, handling special characters and ensuring case-insensitivity
        # This regex aims to capture words including common Pali diacritics.
        # It also handles hyphens and apostrophes within words.
        words = re.findall(
            r"[a-zA-Zāīūṛḷṅṇñṭḍśṣṃṁ'-]+",
            text,
            re.IGNORECASE,
        )
        return [self.normalize(word.lower()) for word in words]  # Normalize notation
    
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
                if not headwords_str: # Handles both None and empty string
                    # If headwords is empty or None, lookup_key itself is the lemma
                    return [word.lower()]
                else:
                    # Parse the bracketed, comma-separated list of IDs as per instructions
                    stripped_headwords = headwords_str.strip('[]')
                    id_strings = [s.strip() for s in stripped_headwords.split(',')]

                    int_ids = []
                    for s in id_strings:
                        if s.isdigit(): # Ensure it's a valid number before converting
                            int_ids.append(int(s))

                    if int_ids: # Check if we actually got any valid IDs
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
        except Exception as e: # Catch any general exception, including parsing errors
            print(f"Error lemmatizing '{word}': {e}")
            return [word.lower()]

    def get_definition(self, lemma: str) -> Optional[str]:
        if not self.conn:
            return None

        cursor = self.conn.cursor()
        try:
            # Query 'dpd_headwords' table for the definition (meaning_1)
            cursor.execute("SELECT meaning_1 FROM dpd_headwords WHERE lemma_1 = ? COLLATE NOCASE LIMIT 1", (lemma,))
            result = cursor.fetchone()
            return result[0] if result else None
        except sqlite3.Error as e:
            print(f"Error getting definition for '{lemma}': {e}")
            return None

    def get_grammar_data(self, lemma: str) -> Optional[Dict]:
        if not self.conn:
            return None

        cursor = self.conn.cursor()
        try:
            # Query 'dpd_headwords' table for POS and other grammar data
            # Based on schema, 'pos' is available. Other grammar details like Case, Number, Gender are not explicitly mentioned.
            cursor.execute("SELECT pos FROM dpd_headwords WHERE lemma_1 = ? COLLATE NOCASE LIMIT 1", (lemma,))
            result = cursor.fetchone()
            if result:
                grammar_data = {
                    "POS": result[0]
                }
                return {k: v for k, v in grammar_data.items() if v is not None}
            return None
        except sqlite3.Error as e:
            print(f"Error getting grammar data for '{lemma}': {e}")
            return None

    def normalize(self, text: str) -> str:
        """
        Normalize pali notation to ensure exclusion list and text are not mismatched.
        DPD database handles all compounds without (') chars
        """
        return text.replace("ṁ", "ṃ").replace("'", "").replace("”", "").replace("’", "")


def get_processor(language_code: str, exclusion_list: List[str], lexicon_db_path: Optional[str] = None):
    """Factory function to create and return a PaliProcessor instance."""
    return PaliProcessor(language_code, exclusion_list, lexicon_db_path)