"""
Text Processing Tool for AI-Karen
Advanced text processing, analysis, and manipulation.
"""

import asyncio
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from collections import Counter
import hashlib

logger = logging.getLogger(__name__)


class TextProcessingTool:
    """
    Production-grade text processing tool.

    Features:
    - Text cleaning and normalization
    - Sentence and word tokenization
    - Text statistics and analysis
    - Pattern matching and extraction
    - Text transformation (case, formatting)
    - Similarity comparison
    - Language detection hints
    - Text summarization helpers
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.max_text_length = self.config.get('max_text_length', 1_000_000)

    async def clean_text(
        self,
        text: str,
        remove_whitespace: bool = True,
        remove_punctuation: bool = False,
        remove_numbers: bool = False,
        lowercase: bool = False
    ) -> str:
        """
        Clean and normalize text.

        Args:
            text: Input text
            remove_whitespace: Remove extra whitespace
            remove_punctuation: Remove punctuation
            remove_numbers: Remove numbers
            lowercase: Convert to lowercase

        Returns:
            Cleaned text
        """
        if len(text) > self.max_text_length:
            raise ValueError(f"Text too long: {len(text)} (max: {self.max_text_length})")

        result = text

        if lowercase:
            result = result.lower()

        if remove_punctuation:
            result = re.sub(r'[^\w\s]', '', result)

        if remove_numbers:
            result = re.sub(r'\d+', '', result)

        if remove_whitespace:
            result = ' '.join(result.split())

        return result

    async def tokenize_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.

        Args:
            text: Input text

        Returns:
            List of sentences
        """
        # Simple sentence tokenization
        # For production, consider using spacy or nltk
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences

    async def tokenize_words(
        self,
        text: str,
        lowercase: bool = True,
        remove_punctuation: bool = True
    ) -> List[str]:
        """
        Split text into words.

        Args:
            text: Input text
            lowercase: Convert to lowercase
            remove_punctuation: Remove punctuation

        Returns:
            List of words
        """
        if lowercase:
            text = text.lower()

        if remove_punctuation:
            text = re.sub(r'[^\w\s]', ' ', text)

        words = text.split()
        return [w for w in words if w]

    async def count_words(self, text: str) -> int:
        """Count words in text."""
        words = await self.tokenize_words(text)
        return len(words)

    async def count_sentences(self, text: str) -> int:
        """Count sentences in text."""
        sentences = await self.tokenize_sentences(text)
        return len(sentences)

    async def count_characters(self, text: str, include_spaces: bool = True) -> int:
        """Count characters in text."""
        if include_spaces:
            return len(text)
        else:
            return len(text.replace(' ', ''))

    async def get_text_stats(self, text: str) -> Dict[str, Any]:
        """
        Get comprehensive text statistics.

        Args:
            text: Input text

        Returns:
            Dictionary with text statistics
        """
        words = await self.tokenize_words(text)
        sentences = await self.tokenize_sentences(text)

        # Calculate statistics
        char_count = len(text)
        char_count_no_spaces = len(text.replace(' ', ''))
        word_count = len(words)
        sentence_count = len(sentences)

        # Average word and sentence length
        avg_word_length = char_count_no_spaces / word_count if word_count > 0 else 0
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0

        # Most common words
        word_freq = Counter(words)
        most_common_words = word_freq.most_common(10)

        # Unique words
        unique_words = len(set(words))
        lexical_diversity = unique_words / word_count if word_count > 0 else 0

        return {
            'character_count': char_count,
            'character_count_no_spaces': char_count_no_spaces,
            'word_count': word_count,
            'sentence_count': sentence_count,
            'average_word_length': round(avg_word_length, 2),
            'average_sentence_length': round(avg_sentence_length, 2),
            'unique_words': unique_words,
            'lexical_diversity': round(lexical_diversity, 2),
            'most_common_words': most_common_words
        }

    async def extract_patterns(
        self,
        text: str,
        pattern: str,
        case_sensitive: bool = True
    ) -> List[str]:
        """
        Extract patterns using regex.

        Args:
            text: Input text
            pattern: Regex pattern
            case_sensitive: Case-sensitive matching

        Returns:
            List of matches
        """
        flags = 0 if case_sensitive else re.IGNORECASE
        matches = re.findall(pattern, text, flags=flags)
        return matches

    async def extract_emails(self, text: str) -> List[str]:
        """Extract email addresses from text."""
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return await self.extract_patterns(text, pattern)

    async def extract_urls(self, text: str) -> List[str]:
        """Extract URLs from text."""
        pattern = r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)'
        return await self.extract_patterns(text, pattern)

    async def extract_phone_numbers(self, text: str) -> List[str]:
        """Extract phone numbers from text."""
        # Simple pattern for US-style phone numbers
        pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        return await self.extract_patterns(text, pattern)

    async def replace_pattern(
        self,
        text: str,
        pattern: str,
        replacement: str,
        case_sensitive: bool = True
    ) -> str:
        """
        Replace pattern in text.

        Args:
            text: Input text
            pattern: Regex pattern to find
            replacement: Replacement string
            case_sensitive: Case-sensitive matching

        Returns:
            Text with replacements
        """
        flags = 0 if case_sensitive else re.IGNORECASE
        return re.sub(pattern, replacement, text, flags=flags)

    async def truncate_text(
        self,
        text: str,
        max_length: int,
        suffix: str = '...'
    ) -> str:
        """
        Truncate text to maximum length.

        Args:
            text: Input text
            max_length: Maximum length
            suffix: Suffix to add if truncated

        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text

        return text[:max_length - len(suffix)] + suffix

    async def wrap_text(
        self,
        text: str,
        width: int = 80,
        break_long_words: bool = True
    ) -> List[str]:
        """
        Wrap text to specified width.

        Args:
            text: Input text
            width: Line width
            break_long_words: Break long words

        Returns:
            List of wrapped lines
        """
        import textwrap
        wrapper = textwrap.TextWrapper(
            width=width,
            break_long_words=break_long_words,
            break_on_hyphens=True
        )
        return wrapper.wrap(text)

    async def calculate_similarity(
        self,
        text1: str,
        text2: str,
        method: str = 'jaccard'
    ) -> float:
        """
        Calculate text similarity.

        Args:
            text1: First text
            text2: Second text
            method: Similarity method ('jaccard', 'cosine', 'levenshtein')

        Returns:
            Similarity score (0-1)
        """
        if method == 'jaccard':
            words1 = set(await self.tokenize_words(text1))
            words2 = set(await self.tokenize_words(text2))
            intersection = len(words1 & words2)
            union = len(words1 | words2)
            return intersection / union if union > 0 else 0.0

        elif method == 'cosine':
            # Simple cosine similarity based on word counts
            words1 = await self.tokenize_words(text1)
            words2 = await self.tokenize_words(text2)
            freq1 = Counter(words1)
            freq2 = Counter(words2)

            all_words = set(words1 + words2)
            vec1 = [freq1.get(w, 0) for w in all_words]
            vec2 = [freq2.get(w, 0) for w in all_words]

            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            magnitude1 = sum(a * a for a in vec1) ** 0.5
            magnitude2 = sum(b * b for b in vec2) ** 0.5

            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0
            return dot_product / (magnitude1 * magnitude2)

        elif method == 'levenshtein':
            # Normalized Levenshtein distance
            def levenshtein_distance(s1: str, s2: str) -> int:
                if len(s1) < len(s2):
                    return levenshtein_distance(s2, s1)
                if len(s2) == 0:
                    return len(s1)

                previous_row = range(len(s2) + 1)
                for i, c1 in enumerate(s1):
                    current_row = [i + 1]
                    for j, c2 in enumerate(s2):
                        insertions = previous_row[j + 1] + 1
                        deletions = current_row[j] + 1
                        substitutions = previous_row[j] + (c1 != c2)
                        current_row.append(min(insertions, deletions, substitutions))
                    previous_row = current_row

                return previous_row[-1]

            distance = levenshtein_distance(text1, text2)
            max_len = max(len(text1), len(text2))
            return 1.0 - (distance / max_len) if max_len > 0 else 1.0

        else:
            raise ValueError(f"Unknown similarity method: {method}")

    async def generate_text_hash(
        self,
        text: str,
        algorithm: str = 'sha256'
    ) -> str:
        """
        Generate hash of text.

        Args:
            text: Input text
            algorithm: Hash algorithm ('md5', 'sha1', 'sha256', 'sha512')

        Returns:
            Hex digest of hash
        """
        if algorithm == 'md5':
            hasher = hashlib.md5()
        elif algorithm == 'sha1':
            hasher = hashlib.sha1()
        elif algorithm == 'sha256':
            hasher = hashlib.sha256()
        elif algorithm == 'sha512':
            hasher = hashlib.sha512()
        else:
            raise ValueError(f"Unknown hash algorithm: {algorithm}")

        hasher.update(text.encode('utf-8'))
        return hasher.hexdigest()

    async def format_text(
        self,
        text: str,
        format_type: str = 'title'
    ) -> str:
        """
        Format text.

        Args:
            text: Input text
            format_type: Format type ('title', 'sentence', 'upper', 'lower', 'capitalize')

        Returns:
            Formatted text
        """
        if format_type == 'title':
            return text.title()
        elif format_type == 'sentence':
            return text.capitalize()
        elif format_type == 'upper':
            return text.upper()
        elif format_type == 'lower':
            return text.lower()
        elif format_type == 'capitalize':
            return text.capitalize()
        else:
            raise ValueError(f"Unknown format type: {format_type}")

    async def remove_duplicates(
        self,
        texts: List[str],
        case_sensitive: bool = False
    ) -> List[str]:
        """
        Remove duplicate texts from list.

        Args:
            texts: List of texts
            case_sensitive: Case-sensitive comparison

        Returns:
            List with duplicates removed
        """
        seen = set()
        result = []

        for text in texts:
            compare_text = text if case_sensitive else text.lower()
            if compare_text not in seen:
                seen.add(compare_text)
                result.append(text)

        return result


# Singleton instance
_text_processing_tool_instance = None


def get_text_processing_tool(
    config: Optional[Dict[str, Any]] = None
) -> TextProcessingTool:
    """Get or create singleton text processing tool instance."""
    global _text_processing_tool_instance
    if _text_processing_tool_instance is None:
        _text_processing_tool_instance = TextProcessingTool(config)
    return _text_processing_tool_instance
