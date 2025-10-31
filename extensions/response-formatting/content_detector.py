"""
Content type detection service using existing NLP services.

This module provides intelligent content type detection by analyzing
user queries and response content using the existing spaCy and DistilBERT services.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from base import ContentType, ResponseContext

logger = logging.getLogger(__name__)


@dataclass
class ContentDetectionResult:
    """Result of content type detection."""
    content_type: ContentType
    confidence: float
    reasoning: str
    detected_entities: List[str]
    keywords: List[str]


class ContentTypeDetector:
    """
    Service for detecting content types from user queries and responses.
    
    This detector uses the existing NLP services (spaCy and DistilBERT) to analyze
    content and determine the most appropriate formatting approach.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Content type patterns and keywords
        self._content_patterns = {
            ContentType.MOVIE: {
                'keywords': [
                    'movie', 'film', 'cinema', 'actor', 'actress', 'director', 'rating', 'imdb',
                    'box office', 'trailer', 'review', 'cast', 'plot', 'genre', 'oscar', 'award',
                    'hollywood', 'netflix', 'streaming', 'theater', 'premiere', 'sequel'
                ],
                'entities': ['PERSON', 'ORG', 'WORK_OF_ART'],
                'patterns': [
                    r'\b(?:movie|film|cinema)\b',
                    r'\b(?:directed by|starring)\b',
                    r'\b(?:imdb|rotten tomatoes|metacritic)\b.*(?:rating|score)',
                    r'\b(?:trailer|review|plot|genre|runtime)\b',
                    r'\b(?:actor|actress|director)\b'
                ]
            },
            ContentType.RECIPE: {
                'keywords': [
                    'recipe', 'cook', 'cooking', 'bake', 'baking', 'ingredient', 'ingredients',
                    'preparation', 'serve', 'serving', 'dish', 'meal', 'cuisine', 'kitchen',
                    'oven', 'temperature', 'minutes', 'hours', 'cup', 'tablespoon', 'teaspoon',
                    'salt', 'pepper', 'oil', 'butter', 'flour', 'sugar', 'egg', 'milk'
                ],
                'entities': ['QUANTITY', 'TIME'],
                'patterns': [
                    r'\b(?:recipe|how to (?:cook|make|bake))\b',
                    r'\b(?:ingredients?|preparation|cooking time)\b',
                    r'\b\d+\s*(?:cups?|tbsp|tsp|oz|lbs?|minutes?|hours?)\b',
                    r'\b(?:preheat|bake|cook|simmer|boil)\b.*(?:for|at|until)'
                ]
            },
            ContentType.WEATHER: {
                'keywords': [
                    'weather', 'temperature', 'forecast', 'rain', 'snow', 'sunny', 'cloudy',
                    'wind', 'humidity', 'pressure', 'storm', 'thunder', 'lightning', 'tornado',
                    'hurricane', 'celsius', 'fahrenheit', 'degrees', 'hot', 'cold', 'warm', 'cool',
                    'precipitation', 'visibility', 'uv index', 'sunrise', 'sunset'
                ],
                'entities': ['GPE', 'TIME', 'DATE'],
                'patterns': [
                    r'\b(?:weather|forecast|temperature)\b.*(?:in|for|today|tomorrow)',
                    r'\b\d+\s*(?:degrees?|°[CF]?)\b',
                    r'\b(?:rain|snow|sunny|cloudy|windy)\b',
                    r'\b(?:humidity|pressure|wind speed)\b.*\d+'
                ]
            },
            ContentType.NEWS: {
                'keywords': [
                    'news', 'article', 'report', 'breaking', 'headline', 'story', 'journalist',
                    'reporter', 'newspaper', 'magazine', 'press', 'media', 'source', 'publish',
                    'update', 'latest', 'current', 'recent', 'today', 'yesterday', 'politics',
                    'economy', 'sports', 'technology', 'health', 'science', 'world', 'local'
                ],
                'entities': ['ORG', 'PERSON', 'GPE', 'DATE'],
                'patterns': [
                    r'\b(?:news|article|report|story)\b.*(?:about|on|regarding)',
                    r'\b(?:breaking|latest|recent)\b.*(?:news|update|development)',
                    r'\b(?:according to|sources say|reported by)\b',
                    r'\b(?:published|updated|posted)\b.*(?:on|at|by)'
                ]
            },
            ContentType.PRODUCT: {
                'keywords': [
                    'product', 'buy', 'purchase', 'price', 'cost', 'sale', 'discount', 'deal',
                    'review', 'rating', 'specification', 'specs', 'feature', 'brand', 'model',
                    'amazon', 'ebay', 'store', 'shop', 'shopping', 'cart', 'checkout', 'order',
                    'delivery', 'shipping', 'warranty', 'return', 'refund', 'compare', 'available',
                    'laptop', 'phone', 'smartphone', 'tablet', 'computer', 'headphones', 'camera',
                    'watch', 'tv', 'monitor', 'keyboard', 'mouse', 'speaker', 'gaming', 'electronics',
                    'macbook', 'iphone', 'ipad', 'samsung', 'dell', 'hp', 'lenovo', 'asus', 'sony'
                ],
                'entities': ['MONEY', 'ORG', 'PRODUCT'],
                'patterns': [
                    r'\$\d+(?:,\d{3})*(?:\.\d{2})?|\b\d+\s*(?:dollars?|USD|EUR|GBP)\b',
                    r'\b(?:buy|purchase|order|shop)\b.*(?:for|from|at)',
                    r'\b(?:price|cost|rating|review)\b.*(?:of|for|on)',
                    r'\b(?:specification|features?|specs)\b.*(?:of|for|include)',
                    r'\b(?:brand|model)\s*[:\-]?\s*\w+',
                    r'\b(?:available|in stock|shipping|warranty)\b',
                    r'\b(?:stars?|/5|\d+\.\d+/5)\b'
                ]
            },
            ContentType.TRAVEL: {
                'keywords': [
                    'travel', 'trip', 'vacation', 'holiday', 'flight', 'hotel', 'booking',
                    'destination', 'itinerary', 'tourist', 'tourism', 'visit', 'explore',
                    'airport', 'airline', 'passport', 'visa', 'luggage', 'suitcase',
                    'restaurant', 'attraction', 'museum', 'beach', 'mountain', 'city',
                    'country', 'guide', 'map', 'directions', 'transportation'
                ],
                'entities': ['GPE', 'FAC', 'ORG', 'DATE', 'TIME'],
                'patterns': [
                    r'\b(?:travel|trip|vacation)\b.*(?:to|in|from|for)',
                    r'\b(?:flight|hotel|booking)\b.*(?:to|from|in|for)',
                    r'\b(?:visit|explore|see)\b.*(?:in|at|the)',
                    r'\b(?:itinerary|guide|directions)\b.*(?:for|to|in)'
                ]
            },
            ContentType.CODE: {
                'keywords': [
                    'code', 'programming', 'function', 'variable', 'class', 'method', 'algorithm',
                    'debug', 'error', 'bug', 'syntax', 'compile', 'execute', 'run', 'script',
                    'python', 'javascript', 'java', 'c++', 'html', 'css', 'sql', 'api',
                    'database', 'framework', 'library', 'import', 'export', 'return', 'loop',
                    'condition', 'if', 'else', 'for', 'while', 'try', 'catch', 'exception'
                ],
                'entities': ['LANGUAGE'],
                'patterns': [
                    r'\b(?:def|function|class|var|let|const)\s+\w+',
                    r'\b(?:import|from|include|require)\b.*(?:import|from)',
                    r'\b(?:if|else|for|while|try|catch)\b.*[{:]',
                    r'```\w*\n.*\n```',  # Code blocks
                    r'`[^`]+`'  # Inline code
                ]
            }
        }
    
    async def detect_content_type(
        self, 
        user_query: str, 
        response_content: str,
        context: Optional[ResponseContext] = None
    ) -> ContentDetectionResult:
        """
        Detect the content type of a user query and response.
        
        Args:
            user_query: The user's original query
            response_content: The AI's response content
            context: Optional additional context
            
        Returns:
            ContentDetectionResult with detected type and confidence
        """
        try:
            # Combine query and response for analysis
            combined_text = f"{user_query} {response_content}"
            
            # Get NLP analysis if available
            entities = []
            keywords = []
            
            try:
                # Try to use existing NLP services
                nlp_analysis = await self._get_nlp_analysis(combined_text)
                entities = nlp_analysis.get('entities', [])
                keywords = nlp_analysis.get('keywords', [])
            except Exception as e:
                self.logger.debug(f"NLP analysis not available: {e}")
                # Fall back to pattern-based detection
            
            # Score each content type
            scores = {}
            for content_type, patterns in self._content_patterns.items():
                score = self._calculate_content_score(
                    combined_text, 
                    patterns, 
                    entities, 
                    keywords
                )
                scores[content_type] = score
            
            # Find the best match
            best_type = max(scores, key=scores.get)
            best_score = scores[best_type]
            
            # If no strong match, use default
            if best_score < 0.25:  # Lowered threshold slightly
                best_type = ContentType.DEFAULT
                best_score = 0.1
            
            # Generate reasoning
            reasoning = self._generate_reasoning(best_type, combined_text, entities, keywords)
            
            return ContentDetectionResult(
                content_type=best_type,
                confidence=best_score,
                reasoning=reasoning,
                detected_entities=entities,
                keywords=keywords
            )
            
        except Exception as e:
            self.logger.error(f"Content detection failed: {e}")
            return ContentDetectionResult(
                content_type=ContentType.DEFAULT,
                confidence=0.1,
                reasoning=f"Detection failed: {e}",
                detected_entities=[],
                keywords=[]
            )
    
    async def _get_nlp_analysis(self, text: str) -> Dict[str, Any]:
        """
        Get NLP analysis using existing services.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with entities and keywords
        """
        try:
            # Import NLP service manager
            from ai_karen_engine.services.nlp_service_manager import nlp_service_manager
            
            # Get spaCy analysis
            parsed_message = await nlp_service_manager.spacy_service.parse_message(text)
            entities = [ent.label_ for ent in parsed_message.entities] if parsed_message.entities else []
            
            # Get linguistic features
            features = await nlp_service_manager.spacy_service.get_linguistic_features(text)
            keywords = features.get('keywords', []) if features else []
            
            return {
                'entities': entities,
                'keywords': keywords,
                'parsed_message': parsed_message,
                'features': features
            }
            
        except ImportError:
            self.logger.debug("NLP service manager not available")
            return {'entities': [], 'keywords': []}
        except Exception as e:
            self.logger.debug(f"NLP analysis failed: {e}")
            return {'entities': [], 'keywords': []}
    
    def _calculate_content_score(
        self, 
        text: str, 
        patterns: Dict[str, Any], 
        entities: List[str], 
        keywords: List[str]
    ) -> float:
        """
        Calculate content type score based on patterns and NLP analysis.
        
        Args:
            text: Text to analyze
            patterns: Content type patterns
            entities: Detected entities
            keywords: Detected keywords
            
        Returns:
            Score between 0.0 and 1.0
        """
        score = 0.0
        text_lower = text.lower()
        
        # Keyword matching (40% of score)
        keyword_matches = sum(1 for keyword in patterns['keywords'] if keyword in text_lower)
        keyword_score = min(keyword_matches / len(patterns['keywords']), 1.0) * 0.4
        score += keyword_score
        
        # Pattern matching (30% of score)
        pattern_matches = sum(1 for pattern in patterns['patterns'] if re.search(pattern, text, re.IGNORECASE))
        pattern_score = min(pattern_matches / len(patterns['patterns']), 1.0) * 0.3
        score += pattern_score
        
        # Entity matching (20% of score)
        if entities and patterns.get('entities'):
            entity_matches = sum(1 for entity in entities if entity in patterns['entities'])
            entity_score = min(entity_matches / len(patterns['entities']), 1.0) * 0.2
            score += entity_score
        
        # NLP keyword matching (10% of score)
        if keywords:
            nlp_keyword_matches = sum(1 for kw in keywords if kw.lower() in patterns['keywords'])
            nlp_score = min(nlp_keyword_matches / max(len(keywords), 1), 1.0) * 0.1
            score += nlp_score
        
        return min(score, 1.0)
    
    def _generate_reasoning(
        self, 
        content_type: ContentType, 
        text: str, 
        entities: List[str], 
        keywords: List[str]
    ) -> str:
        """
        Generate human-readable reasoning for the detection result.
        
        Args:
            content_type: Detected content type
            text: Original text
            entities: Detected entities
            keywords: Detected keywords
            
        Returns:
            Reasoning string
        """
        if content_type == ContentType.DEFAULT:
            return "No specific content type detected, using default formatting"
        
        reasoning_parts = [f"Detected as {content_type.value} content"]
        
        # Add keyword evidence
        if content_type in self._content_patterns:
            matched_keywords = [
                kw for kw in self._content_patterns[content_type]['keywords']
                if kw in text.lower()
            ]
            if matched_keywords:
                reasoning_parts.append(f"Keywords: {', '.join(matched_keywords[:5])}")
        
        # Add entity evidence
        if entities:
            reasoning_parts.append(f"Entities: {', '.join(set(entities[:3]))}")
        
        return "; ".join(reasoning_parts)
    
    def get_supported_content_types(self) -> List[ContentType]:
        """
        Get all content types supported by this detector.
        
        Returns:
            List of supported ContentType enums
        """
        return list(self._content_patterns.keys()) + [ContentType.DEFAULT]
    
    def get_detection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the content detection patterns.
        
        Returns:
            Dictionary with detection statistics
        """
        return {
            'supported_types': [ct.value for ct in self.get_supported_content_types()],
            'pattern_counts': {
                ct.value: {
                    'keywords': len(patterns['keywords']),
                    'patterns': len(patterns['patterns']),
                    'entities': len(patterns.get('entities', []))
                }
                for ct, patterns in self._content_patterns.items()
            }
        }