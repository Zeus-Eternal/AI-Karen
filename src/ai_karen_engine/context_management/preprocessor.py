"""
Context Preprocessor for Content Analysis and Extraction

Handles text preprocessing, entity extraction, keyword extraction,
summarization, and content analysis for context entries.
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from ai_karen_engine.context_management.models import ContextEntry, ContextType

logger = logging.getLogger(__name__)


class ContextPreprocessor:
    """
    Advanced content preprocessor for context entries.
    
    Features:
    - Text cleaning and normalization
    - Entity extraction (people, places, organizations)
    - Keyword extraction
    - Automatic summarization
    - Content analysis
    - Language detection
    """

    def __init__(
        self,
        min_keyword_length: int = 3,
        max_keywords: int = 10,
        max_summary_length: int = 500,
        enable_entity_extraction: bool = True,
        enable_summarization: bool = True,
    ):
        """
        Initialize context preprocessor.
        
        Args:
            min_keyword_length: Minimum length for keywords
            max_keywords: Maximum number of keywords to extract
            max_summary_length: Maximum length for summaries
            enable_entity_extraction: Whether to extract entities
            enable_summarization: Whether to generate summaries
        """
        self.min_keyword_length = min_keyword_length
        self.max_keywords = max_keywords
        self.max_summary_length = max_summary_length
        self.enable_entity_extraction = enable_entity_extraction
        self.enable_summarization = enable_summarization
        
        # Initialize NLP components if available
        self._initialize_nlp_components()
        
        logger.info("ContextPreprocessor initialized")

    def _initialize_nlp_components(self) -> None:
        """Initialize NLP components if available."""
        try:
            # Try to initialize spaCy
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("spaCy NLP model loaded")
        except (ImportError, OSError):
            self.nlp = None
            logger.warning("spaCy not available, using basic preprocessing")
        
        try:
            # Try to initialize NLTK
            import nltk
            from nltk.corpus import stopwords
            from nltk.tokenize import word_tokenize
            from nltk.stem import WordNetLemmatizer
            
            # Download required NLTK data
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                nltk.download('punkt', quiet=True)
            
            try:
                nltk.data.find('corpora/stopwords')
            except LookupError:
                nltk.download('stopwords', quiet=True)
            
            try:
                nltk.data.find('corpora/wordnet')
            except LookupError:
                nltk.download('wordnet', quiet=True)
            
            self.stop_words = set(stopwords.words('english'))
            self.lemmatizer = WordNetLemmatizer()
            self.word_tokenize = word_tokenize
            logger.info("NLTK components loaded")
        except ImportError:
            self.stop_words = set()
            self.lemmatizer = None
            self.word_tokenize = None
            logger.warning("NLTK not available, using basic tokenization")

    async def preprocess_context(
        self,
        context: ContextEntry,
    ) -> ContextEntry:
        """
        Preprocess context entry with full analysis pipeline.
        
        Args:
            context: Context entry to preprocess
            
        Returns:
            Preprocessed context entry
        """
        try:
            # Clean and normalize text
            cleaned_content = self._clean_text(context.content)
            
            # Detect language
            language = self._detect_language(cleaned_content)
            
            # Extract keywords
            keywords = await self._extract_keywords(cleaned_content, language)
            
            # Extract entities
            entities = []
            if self.enable_entity_extraction:
                entities = await self._extract_entities(cleaned_content, language)
            
            # Generate summary
            summary = None
            if self.enable_summarization and len(cleaned_content) > 200:
                summary = await self._generate_summary(cleaned_content, language)
            
            # Analyze content characteristics
            content_analysis = self._analyze_content(cleaned_content, context.context_type)
            
            # Update context with preprocessing results
            context.keywords = keywords
            context.entities = entities
            context.summary = summary
            context.metadata.update({
                "preprocessed_at": datetime.utcnow().isoformat(),
                "language": language,
                "content_analysis": content_analysis,
                "original_length": len(context.content),
                "cleaned_length": len(cleaned_content),
            })
            
            logger.info(f"Preprocessed context {context.id}")
            return context
            
        except Exception as e:
            logger.error(f"Failed to preprocess context {context.id}: {e}")
            # Return original context if preprocessing fails
            return context

    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text content.
        
        Args:
            text: Original text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}\'\"]', ' ', text)
        
        # Normalize quotes
        text = text.replace('"', '"').replace('"', '"').replace(''', "'").replace(''', "'")
        
        # Remove extra spaces around punctuation
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        
        # Strip and normalize
        text = text.strip()
        
        return text

    def _detect_language(self, text: str) -> str:
        """
        Detect language of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Language code (e.g., 'en', 'es', 'fr')
        """
        if not text or len(text) < 10:
            return "unknown"
        
        try:
            # Try langdetect
            from langdetect import detect
            return detect(text)
        except ImportError:
            # Fallback to basic heuristics
            english_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
            words = text.lower().split()
            english_word_count = sum(1 for word in words if word in english_words)
            
            if len(words) > 0 and english_word_count / len(words) > 0.1:
                return "en"
            else:
                return "unknown"
        except Exception:
            return "unknown"

    async def _extract_keywords(
        self,
        text: str,
        language: str,
    ) -> List[str]:
        """
        Extract keywords from text.
        
        Args:
            text: Text to analyze
            language: Language code
            
        Returns:
            List of keywords
        """
        if not text:
            return []
        
        keywords = []
        
        try:
            if self.nlp and language == "en":
                # Use spaCy for keyword extraction
                doc = self.nlp(text)
                
                # Extract noun chunks and named entities
                for chunk in doc.noun_chunks:
                    if len(chunk.text) >= self.min_keyword_length:
                        keywords.append(chunk.text.lower().strip())
                
                # Extract important tokens
                for token in doc:
                    if (token.pos_ in ['NOUN', 'PROPN'] and 
                        not token.is_stop and 
                        not token.is_punct and
                        len(token.text) >= self.min_keyword_length):
                        keywords.append(token.lemma_.lower())
            
            elif self.word_tokenize and language == "en":
                # Use NLTK for keyword extraction
                tokens = self.word_tokenize(text.lower())
                
                # Filter tokens
                filtered_tokens = []
                for token in tokens:
                    if (token.isalpha() and 
                        len(token) >= self.min_keyword_length and
                        token not in self.stop_words):
                        
                        # Lemmatize if available
                        if self.lemmatizer:
                            token = self.lemmatizer.lemmatize(token)
                        
                        filtered_tokens.append(token)
                
                # Count frequency
                token_freq = {}
                for token in filtered_tokens:
                    token_freq[token] = token_freq.get(token, 0) + 1
                
                # Sort by frequency and take top keywords
                sorted_tokens = sorted(token_freq.items(), key=lambda x: x[1], reverse=True)
                keywords = [token for token, freq in sorted_tokens[:self.max_keywords]]
            
            else:
                # Basic keyword extraction for other languages
                words = text.lower().split()
                word_freq = {}
                
                for word in words:
                    # Clean word
                    word = re.sub(r'[^\w]', '', word)
                    if len(word) >= self.min_keyword_length:
                        word_freq[word] = word_freq.get(word, 0) + 1
                
                # Sort by frequency
                sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
                keywords = [word for word, freq in sorted_words[:self.max_keywords]]
        
        except Exception as e:
            logger.warning(f"Keyword extraction failed: {e}")
            # Fallback to basic word frequency
            words = text.lower().split()
            word_freq = {}
            for word in words:
                word = re.sub(r'[^\w]', '', word)
                if len(word) >= self.min_keyword_length:
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            keywords = [word for word, freq in sorted_words[:self.max_keywords]]
        
        # Remove duplicates and return
        return list(dict.fromkeys(keywords))

    async def _extract_entities(
        self,
        text: str,
        language: str,
    ) -> List[Dict[str, Any]]:
        """
        Extract entities from text.
        
        Args:
            text: Text to analyze
            language: Language code
            
        Returns:
            List of entity dictionaries
        """
        entities = []
        
        if not text or language != "en":
            return entities
        
        try:
            if self.nlp:
                # Use spaCy for entity extraction
                doc = self.nlp(text)
                
                for ent in doc.ents:
                    entity = {
                        "text": ent.text,
                        "label": ent.label_,
                        "start": ent.start_char,
                        "end": ent.end_char,
                        "confidence": 1.0,  # spaCy doesn't provide confidence
                    }
                    entities.append(entity)
            
            else:
                # Basic entity extraction using regex patterns
                entities = self._basic_entity_extraction(text)
        
        except Exception as e:
            logger.warning(f"Entity extraction failed: {e}")
            entities = []
        
        return entities

    def _basic_entity_extraction(self, text: str) -> List[Dict[str, Any]]:
        """
        Basic entity extraction using regex patterns.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of entity dictionaries
        """
        entities = []
        
        # Email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        for match in re.finditer(email_pattern, text):
            entities.append({
                "text": match.group(),
                "label": "EMAIL",
                "start": match.start(),
                "end": match.end(),
                "confidence": 0.9,
            })
        
        # URLs
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        for match in re.finditer(url_pattern, text):
            entities.append({
                "text": match.group(),
                "label": "URL",
                "start": match.start(),
                "end": match.end(),
                "confidence": 0.9,
            })
        
        # Phone numbers (US format)
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        for match in re.finditer(phone_pattern, text):
            entities.append({
                "text": match.group(),
                "label": "PHONE",
                "start": match.start(),
                "end": match.end(),
                "confidence": 0.8,
            })
        
        # Dates
        date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'
        for match in re.finditer(date_pattern, text):
            entities.append({
                "text": match.group(),
                "label": "DATE",
                "start": match.start(),
                "end": match.end(),
                "confidence": 0.7,
            })
        
        return entities

    async def _generate_summary(
        self,
        text: str,
        language: str,
    ) -> Optional[str]:
        """
        Generate summary of text.
        
        Args:
            text: Text to summarize
            language: Language code
            
        Returns:
            Summary text or None if generation failed
        """
        if not text or len(text) < 200:
            return None
        
        try:
            # Try extractive summarization
            summary = self._extractive_summarization(text)
            
            if summary and len(summary) <= self.max_summary_length:
                return summary
            
            # Fallback to truncation
            return text[:self.max_summary_length] + "..." if len(text) > self.max_summary_length else text
        
        except Exception as e:
            logger.warning(f"Summary generation failed: {e}")
            return None

    def _extractive_summarization(self, text: str) -> Optional[str]:
        """
        Perform extractive summarization using sentence scoring.
        
        Args:
            text: Text to summarize
            
        Returns:
            Summary text or None
        """
        try:
            # Split into sentences
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if len(sentences) <= 3:
                return text
            
            # Score sentences based on various factors
            sentence_scores = []
            
            for i, sentence in enumerate(sentences):
                score = 0.0
                
                # Length score (prefer medium-length sentences)
                words = sentence.split()
                length_score = min(1.0, len(words) / 20.0)
                score += length_score * 0.3
                
                # Position score (prefer earlier sentences)
                position_score = 1.0 - (i / len(sentences))
                score += position_score * 0.3
                
                # Keyword score (count keywords)
                sentence_lower = sentence.lower()
                common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
                content_words = [w for w in sentence_lower.split() if w not in common_words]
                keyword_score = min(1.0, len(content_words) / 10.0)
                score += keyword_score * 0.4
                
                sentence_scores.append((sentence, score))
            
            # Sort by score and select top sentences
            sentence_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Select top 3 sentences or 30% of sentences, whichever is less
            num_sentences = max(2, min(3, len(sentences) // 3))
            top_sentences = [s[0] for s in sentence_scores[:num_sentences]]
            
            # Combine sentences
            summary = '. '.join(top_sentences)
            
            # Ensure it doesn't exceed max length
            if len(summary) > self.max_summary_length:
                summary = summary[:self.max_summary_length - 3] + "..."
            
            return summary
        
        except Exception as e:
            logger.warning(f"Extractive summarization failed: {e}")
            return None

    def _analyze_content(
        self,
        text: str,
        context_type: ContextType,
    ) -> Dict[str, Any]:
        """
        Analyze content characteristics.
        
        Args:
            text: Text to analyze
            context_type: Type of context
            
        Returns:
            Dictionary with content analysis
        """
        analysis = {}
        
        try:
            # Basic statistics
            words = text.split()
            sentences = re.split(r'[.!?]+', text)
            
            analysis.update({
                "word_count": len(words),
                "sentence_count": len([s for s in sentences if s.strip()]),
                "paragraph_count": len([p for p in text.split('\n\n') if p.strip()]),
                "avg_word_length": sum(len(word) for word in words) / len(words) if words else 0,
                "avg_sentence_length": len(words) / len(sentences) if sentences else 0,
            })
            
            # Readability metrics
            analysis.update(self._calculate_readability(text))
            
            # Type-specific analysis
            if context_type == ContextType.CODE:
                analysis.update(self._analyze_code_content(text))
            elif context_type == ContextType.DOCUMENT:
                analysis.update(self._analyze_document_content(text))
            elif context_type == ContextType.CONVERSATION:
                analysis.update(self._analyze_conversation_content(text))
            
            # Content quality metrics
            analysis.update(self._calculate_content_quality(text))
        
        except Exception as e:
            logger.warning(f"Content analysis failed: {e}")
            analysis = {"error": str(e)}
        
        return analysis

    def _calculate_readability(self, text: str) -> Dict[str, Any]:
        """Calculate readability metrics."""
        if not text:
            return {}
        
        try:
            sentences = re.split(r'[.!?]+', text)
            sentences = [s for s in sentences if s.strip()]
            
            words = text.split()
            words = [w for w in words if w.strip()]
            
            # Count syllables (approximate)
            syllable_count = 0
            for word in words:
                syllable_count += max(1, len(re.findall(r'[aeiouy]', word.lower())))
            
            # Flesch Reading Ease
            if len(sentences) > 0 and len(words) > 0:
                avg_sentence_length = len(words) / len(sentences)
                avg_syllables_per_word = syllable_count / len(words)
                
                flesch_score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
                
                return {
                    "flesch_reading_ease": max(0, min(100, flesch_score)),
                    "avg_sentence_length": avg_sentence_length,
                    "avg_syllables_per_word": avg_syllables_per_word,
                }
            
            return {}
        
        except Exception:
            return {}

    def _analyze_code_content(self, text: str) -> Dict[str, Any]:
        """Analyze code-specific content."""
        analysis = {}
        
        try:
            # Count code constructs
            analysis.update({
                "line_count": len(text.split('\n')),
                "comment_lines": len([line for line in text.split('\n') if line.strip().startswith('#') or '//' in line]),
                "function_count": len(re.findall(r'def\s+\w+|function\s+\w+', text)),
                "class_count": len(re.findall(r'class\s+\w+', text)),
                "import_count": len(re.findall(r'import\s+\w+|from\s+\w+\s+import', text)),
            })
        
        except Exception:
            pass
        
        return analysis

    def _analyze_document_content(self, text: str) -> Dict[str, Any]:
        """Analyze document-specific content."""
        analysis = {}
        
        try:
            # Document structure
            analysis.update({
                "heading_count": len(re.findall(r'^#+\s', text, re.MULTILINE)),
                "list_count": len(re.findall(r'^\s*[-*+]\s', text, re.MULTILINE)),
                "link_count": len(re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', text)),
                "table_count": len(re.findall(r'\|.*\|', text)),
            })
        
        except Exception:
            pass
        
        return analysis

    def _analyze_conversation_content(self, text: str) -> Dict[str, Any]:
        """Analyze conversation-specific content."""
        analysis = {}
        
        try:
            # Conversation patterns
            analysis.update({
                "question_count": len(re.findall(r'\?', text)),
                "exclamation_count": len(re.findall(r'!', text)),
                "user_mentions": len(re.findall(r'@\w+', text)),
                "timestamp_count": len(re.findall(r'\d{1,2}:\d{2}', text)),
            })
        
        except Exception:
            pass
        
        return analysis

    def _calculate_content_quality(self, text: str) -> Dict[str, Any]:
        """Calculate content quality metrics."""
        quality = {}
        
        try:
            # Text quality indicators
            words = text.split()
            
            # Ratio of unique words to total words (vocabulary diversity)
            unique_words = set(word.lower().strip('.,!?;:') for word in words)
            vocabulary_diversity = len(unique_words) / len(words) if words else 0
            
            # Capitalization patterns
            all_caps_words = [w for w in words if w.isupper() and len(w) > 1]
            all_caps_ratio = len(all_caps_words) / len(words) if words else 0
            
            # Punctuation usage
            punctuation_chars = len(re.findall(r'[.,!?;:]', text))
            punctuation_ratio = punctuation_chars / len(words) if words else 0
            
            quality.update({
                "vocabulary_diversity": vocabulary_diversity,
                "all_caps_ratio": all_caps_ratio,
                "punctuation_ratio": punctuation_ratio,
                "quality_score": self._calculate_overall_quality(
                    vocabulary_diversity, all_caps_ratio, punctuation_ratio
                ),
            })
        
        except Exception:
            pass
        
        return quality

    def _calculate_overall_quality(
        self,
        vocabulary_diversity: float,
        all_caps_ratio: float,
        punctuation_ratio: float,
    ) -> float:
        """Calculate overall content quality score."""
        # Vocabulary diversity (higher is better)
        vocab_score = min(1.0, vocabulary_diversity)
        
        # All caps ratio (lower is better)
        caps_score = max(0.0, 1.0 - all_caps_ratio)
        
        # Punctuation ratio (moderate is better)
        if punctuation_ratio < 0.05:
            punct_score = punctuation_ratio * 20  # Boost low punctuation
        elif punctuation_ratio > 0.2:
            punct_score = max(0.0, 1.0 - (punctuation_ratio - 0.2))
        else:
            punct_score = 1.0
        
        # Weighted average
        overall_score = (vocab_score * 0.5 + caps_score * 0.3 + punct_score * 0.2)
        
        return max(0.0, min(1.0, overall_score))

    def get_preprocessor_config(self) -> Dict[str, Any]:
        """Get current preprocessor configuration."""
        return {
            "min_keyword_length": self.min_keyword_length,
            "max_keywords": self.max_keywords,
            "max_summary_length": self.max_summary_length,
            "enable_entity_extraction": self.enable_entity_extraction,
            "enable_summarization": self.enable_summarization,
            "nlp_available": self.nlp is not None,
            "nltk_available": self.word_tokenize is not None,
        }

    def update_config(
        self,
        min_keyword_length: Optional[int] = None,
        max_keywords: Optional[int] = None,
        max_summary_length: Optional[int] = None,
        enable_entity_extraction: Optional[bool] = None,
        enable_summarization: Optional[bool] = None,
    ) -> None:
        """Update preprocessor configuration."""
        if min_keyword_length is not None:
            self.min_keyword_length = min_keyword_length
        if max_keywords is not None:
            self.max_keywords = max_keywords
        if max_summary_length is not None:
            self.max_summary_length = max_summary_length
        if enable_entity_extraction is not None:
            self.enable_entity_extraction = enable_entity_extraction
        if enable_summarization is not None:
            self.enable_summarization = enable_summarization