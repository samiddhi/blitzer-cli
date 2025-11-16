"""Slovenian language processor."""

import re
import sqlite3
from typing import List, Optional, Dict
from .base import BaseLanguageProcessor


class SlovenianProcessor(BaseLanguageProcessor):
    """Slovenian-specific text processing."""
    
    def __init__(self, language_code: str, exclusion_list: List[str], lexicon_db_path: Optional[str] = None):
        super().__init__(language_code, exclusion_list, lexicon_db_path)
        self._connect_db()
        self.exclusion_list = exclusion_list

    def tokenize_words(self, text: str) -> List[str]:
        # Slovenian specific tokenization with special characters (čšž) and ensuring case-insensitivity.
        # This regex aims to capture words including common Slovene characters.
        words = re.findall(r"[a-zA-ZčČšŠžŽjéć'’-]+", text, re.IGNORECASE)
        return [word.lower() for word in words]

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
                if headwords_str: # Handles both None and empty string
                    # Parse the bracketed, comma-separated list of IDs
                    stripped_headwords = headwords_str.strip('[]')
                    id_strings = [s.strip() for s in stripped_headwords.split(',')]

                    int_ids = []
                    for s in id_strings:
                        if s.isdigit(): # Ensure it's a valid number before converting
                            int_ids.append(int(s))

                    if int_ids: # Check if we actually got any valid IDs
                        # Create placeholders for the IN clause
                        placeholders = ', '.join('?' * len(int_ids))

                        # Query 'Lemmas' for all IDs in a single query
                        cursor.execute(f"SELECT lemma FROM Lemmas WHERE id IN ({placeholders})", tuple(int_ids))
                        lemma_results = cursor.fetchall()
                        for lemma_result in lemma_results:
                            lemmas.append(lemma_result[0].lower())

            return list(set(lemmas)) if lemmas else [word.lower()]
        except Exception as e: # Catch any general exception, including parsing errors
            print(f"Error lemmatizing '{word}': {e}")
            return [word.lower()]

    def get_definition(self, lemma: str) -> Optional[str]:
        if not self.conn:
            return None

        cursor = self.conn.cursor()
        try:
            # Query 'Lemmas' table for the definition (assuming meaning is in the lemma field)
            cursor.execute("SELECT lemma FROM Lemmas WHERE lemma = ? COLLATE NOCASE LIMIT 1", (lemma,))
            result = cursor.fetchone()
            return result[0] if result else None
        except sqlite3.Error as e:
            print(f"Error getting definition for '{lemma}': {e}")
            return None

    def get_grammar_data(self, lemma: str) -> Optional[Dict]:
        if not self.conn:
            return None

        # Placeholder implementation - Slovenian DB structure might be different
        # This would need to be customized based on the actual schema of the Slovenian lexicon.db
        return None

    def normalize(self, text: str) -> str:
        """Normalize Slovenian text (default implementation)."""
        return text


def get_processor(language_code: str, exclusion_list: List[str], lexicon_db_path: Optional[str] = None):
    """Factory function to create and return a SlovenianProcessor instance."""
    return SlovenianProcessor(language_code, exclusion_list, lexicon_db_path)