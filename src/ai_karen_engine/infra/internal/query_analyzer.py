"""
Query Analysis Service for Intelligent Response Optimization

This module provides comprehensive query analysis capabilities including:
- Query complexity determination
- Content type detection
- Modality requirements analysis
- User expertise level detection
- Context extraction for response optimization
"""

import re
import asyncio
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ComplexityLevel(Enum):
    """Query complexity levels for response optimization"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class ContentType(Enum):
    """Content types for response strategy determination"""
    CODE = "code"
    TEXT = "text"
    MIXED = "mixed"
    TECHNICAL = "technical"
    CREATIVE = "creative"
    ANALYTICAL = "analytical"


class ModalityType(Enum):
    """Modality types for multi-modal processing"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    MULTIMODAL = "multimodal"


class ExpertiseLevel(Enum):
    """User expertise levels for adaptive response depth"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class Priority(Enum):
    """Processing priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class ContextRequirement:
    """Context requirements for response optimization"""
    type: str
    importance: float
    data: Dict[str, Any]


@dataclass
class QueryAnalysis:
    """Comprehensive query analysis results"""
    complexity: ComplexityLevel
    content_type: ContentType
    modality_requirements: List[ModalityType]
    user_expertise_level: ExpertiseLevel
    context_requirements: List[ContextRequirement]
    processing_priority: Priority
    estimated_response_length: int
    requires_code_execution: bool
    requires_external_data: bool
    language: str
    domain_specific: Optional[str]
    confidence_score: float
    analysis_metadata: Dict[str, Any]


class QueryAnalyzer:
    """
    Advanced query analyzer that determines optimal response strategies
    based on query characteristics, user context, and system capabilities.
    """
    
    def __init__(self):
        self.code_patterns = self._compile_code_patterns()
        self.technical_keywords = self._load_technical_keywords()
        self.complexity_indicators = self._load_complexity_indicators()
        self.domain_keywords = self._load_domain_keywords()
        self.language_patterns = self._compile_language_patterns()
        
    def _compile_code_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for code detection"""
        return {
            'python': re.compile(r'(def\s+\w+|import\s+\w+|from\s+\w+|class\s+\w+|if\s+__name__|print\()', re.IGNORECASE),
            'javascript': re.compile(r'(function\s+\w+|const\s+\w+|let\s+\w+|var\s+\w+|console\.log|=>)', re.IGNORECASE),
            'sql': re.compile(r'(SELECT\s+|INSERT\s+|UPDATE\s+|DELETE\s+|CREATE\s+|ALTER\s+|DROP\s+)', re.IGNORECASE),
            'bash': re.compile(r'(#!/bin/bash|sudo\s+|chmod\s+|grep\s+|awk\s+|sed\s+|\$\{|\|\s)', re.IGNORECASE),
            'generic_code': re.compile(r'(\{|\}|\[|\]|\(|\)|;|//|/\*|\*/|#include|<\w+>)', re.IGNORECASE)
        }
    
    def _load_technical_keywords(self) -> Set[str]:
        """Load technical keywords for content type detection"""
        return {
            'api', 'database', 'algorithm', 'framework', 'library', 'server',
            'client', 'backend', 'frontend', 'deployment', 'docker', 'kubernetes',
            'microservices', 'authentication', 'authorization', 'encryption',
            'machine learning', 'ai', 'neural network', 'deep learning',
            'data science', 'analytics', 'visualization', 'statistics'
        }
    
    def _load_complexity_indicators(self) -> Dict[str, List[str]]:
        """Load indicators for complexity assessment"""
        return {
            'simple': [
                'what is', 'how to', 'define', 'explain', 'simple',
                'basic', 'introduction', 'overview', 'summary'
            ],
            'moderate': [
                'compare', 'analyze', 'implement', 'design', 'optimize',
                'troubleshoot', 'configure', 'integrate', 'migrate'
            ],
            'complex': [
                'architecture', 'scalability', 'performance', 'security',
                'distributed', 'enterprise', 'advanced', 'comprehensive',
                'multi-step', 'end-to-end', 'production-ready'
            ]
        }
    
    def _load_domain_keywords(self) -> Dict[str, Set[str]]:
        """Load domain-specific keywords"""
        return {
            'medical': {'diagnosis', 'treatment', 'patient', 'clinical', 'medical', 'healthcare'},
            'legal': {'contract', 'law', 'legal', 'court', 'attorney', 'litigation'},
            'financial': {'investment', 'trading', 'finance', 'banking', 'portfolio', 'risk'},
            'academic': {'research', 'study', 'analysis', 'thesis', 'academic', 'scholarly'},
            'business': {'strategy', 'management', 'marketing', 'sales', 'revenue', 'profit'}
        }
    
    def _compile_language_patterns(self) -> Dict[str, re.Pattern]:
        """Compile patterns for language detection"""
        return {
            'english': re.compile(r'\b(the|and|or|but|in|on|at|to|for|of|with|by)\b', re.IGNORECASE),
            'spanish': re.compile(r'\b(el|la|los|las|y|o|pero|en|con|de|para|por)\b', re.IGNORECASE),
            'french': re.compile(r'\b(le|la|les|et|ou|mais|dans|avec|de|pour|par)\b', re.IGNORECASE)
        }
    
    async def analyze_query(self, query: str, user_context: Optional[Dict[str, Any]] = None) -> QueryAnalysis:
        """
        Perform comprehensive query analysis to determine optimal response strategy
        
        Args:
            query: The user query to analyze
            user_context: Optional user context for personalization
            
        Returns:
            QueryAnalysis: Comprehensive analysis results
        """
        try:
            # Normalize query for analysis
            normalized_query = query.lower().strip()
            
            # Analyze different aspects concurrently
            complexity_task = self._analyze_complexity(query, normalized_query)
            content_type_task = self._analyze_content_type(query, normalized_query)
            modality_task = self._analyze_modality_requirements(query, normalized_query)
            expertise_task = self._detect_expertise_level(query, normalized_query, user_context)
            context_task = self._extract_context_requirements(query, normalized_query)
            priority_task = self._determine_priority(query, normalized_query, user_context)
            
            # Wait for all analyses to complete
            complexity, content_type, modalities, expertise, context_reqs, priority = await asyncio.gather(
                complexity_task, content_type_task, modality_task, 
                expertise_task, context_task, priority_task
            )
            
            # Additional analysis
            response_length = await self._estimate_response_length(query, complexity, content_type)
            requires_code = await self._requires_code_execution(query, normalized_query)
            requires_external = await self._requires_external_data(query, normalized_query)
            language = await self._detect_language(query)
            domain = await self._detect_domain(query, normalized_query)
            confidence = await self._calculate_confidence_score(query, complexity, content_type)
            
            # Create metadata
            metadata = {
                'query_length': len(query),
                'word_count': len(query.split()),
                'analysis_timestamp': datetime.utcnow().isoformat(),
                'has_code_snippets': any(pattern.search(query) for pattern in self.code_patterns.values()),
                'technical_keyword_count': sum(1 for keyword in self.technical_keywords if keyword in normalized_query)
            }
            
            return QueryAnalysis(
                complexity=complexity,
                content_type=content_type,
                modality_requirements=modalities,
                user_expertise_level=expertise,
                context_requirements=context_reqs,
                processing_priority=priority,
                estimated_response_length=response_length,
                requires_code_execution=requires_code,
                requires_external_data=requires_external,
                language=language,
                domain_specific=domain,
                confidence_score=confidence,
                analysis_metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error analyzing query: {e}")
            # Return default analysis on error
            return self._create_default_analysis(query)
    
    async def _analyze_complexity(self, query: str, normalized_query: str) -> ComplexityLevel:
        """Analyze query complexity based on various indicators"""
        try:
            complexity_score = 0
            
            # Check for complexity indicators
            for level, indicators in self.complexity_indicators.items():
                matches = sum(1 for indicator in indicators if indicator in normalized_query)
                if level == 'simple':
                    complexity_score -= matches * 0.5
                elif level == 'moderate':
                    complexity_score += matches * 1.0
                elif level == 'complex':
                    complexity_score += matches * 2.0
            
            # Length-based complexity
            word_count = len(query.split())
            if word_count > 50:
                complexity_score += 2.0
            elif word_count > 20:
                complexity_score += 1.0
            
            # Technical content increases complexity
            tech_matches = sum(1 for keyword in self.technical_keywords if keyword in normalized_query)
            complexity_score += tech_matches * 0.5
            
            # Code presence increases complexity
            if any(pattern.search(query) for pattern in self.code_patterns.values()):
                complexity_score += 1.5
            
            # Multiple questions increase complexity
            question_count = query.count('?')
            if question_count > 1:
                complexity_score += question_count * 0.5
            
            # Determine final complexity level
            if complexity_score <= 0:
                return ComplexityLevel.SIMPLE
            elif complexity_score <= 3:
                return ComplexityLevel.MODERATE
            else:
                return ComplexityLevel.COMPLEX
                
        except Exception as e:
            logger.error(f"Error analyzing complexity: {e}")
            return ComplexityLevel.MODERATE
    
    async def _analyze_content_type(self, query: str, normalized_query: str) -> ContentType:
        """Analyze content type based on query characteristics"""
        try:
            # Check for code patterns
            code_matches = sum(1 for pattern in self.code_patterns.values() if pattern.search(query))
            if code_matches > 0:
                # Check if it's mixed content
                text_indicators = ['explain', 'what', 'how', 'why', 'describe']
                has_text_request = any(indicator in normalized_query for indicator in text_indicators)
                return ContentType.MIXED if has_text_request else ContentType.CODE
            
            # Check for technical content
            tech_matches = sum(1 for keyword in self.technical_keywords if keyword in normalized_query)
            if tech_matches > 2:
                return ContentType.TECHNICAL
            
            # Check for creative content
            creative_indicators = ['write', 'create', 'generate', 'story', 'poem', 'creative', 'imagine']
            if any(indicator in normalized_query for indicator in creative_indicators):
                return ContentType.CREATIVE
            
            # Check for analytical content
            analytical_indicators = ['analyze', 'compare', 'evaluate', 'assess', 'review', 'critique']
            if any(indicator in normalized_query for indicator in analytical_indicators):
                return ContentType.ANALYTICAL
            
            return ContentType.TEXT
            
        except Exception as e:
            logger.error(f"Error analyzing content type: {e}")
            return ContentType.TEXT
    
    async def _analyze_modality_requirements(self, query: str, normalized_query: str) -> List[ModalityType]:
        """Analyze required modalities for the query"""
        try:
            modalities = [ModalityType.TEXT]  # Always include text
            
            # Image-related keywords
            image_keywords = ['image', 'picture', 'photo', 'visual', 'diagram', 'chart', 'graph']
            if any(keyword in normalized_query for keyword in image_keywords):
                modalities.append(ModalityType.IMAGE)
            
            # Video-related keywords
            video_keywords = ['video', 'movie', 'animation', 'recording', 'stream']
            if any(keyword in normalized_query for keyword in video_keywords):
                modalities.append(ModalityType.VIDEO)
            
            # Audio-related keywords
            audio_keywords = ['audio', 'sound', 'music', 'voice', 'speech', 'podcast']
            if any(keyword in normalized_query for keyword in audio_keywords):
                modalities.append(ModalityType.AUDIO)
            
            # If multiple modalities, mark as multimodal
            if len(modalities) > 2:
                modalities.append(ModalityType.MULTIMODAL)
            
            return modalities
            
        except Exception as e:
            logger.error(f"Error analyzing modality requirements: {e}")
            return [ModalityType.TEXT]
    
    async def _detect_expertise_level(self, query: str, normalized_query: str, user_context: Optional[Dict[str, Any]]) -> ExpertiseLevel:
        """Detect user expertise level for adaptive response depth"""
        try:
            expertise_score = 0
            
            # Use user context if available
            if user_context:
                if 'expertise_level' in user_context:
                    return ExpertiseLevel(user_context['expertise_level'])
                if 'experience_years' in user_context:
                    years = user_context['experience_years']
                    if years >= 10:
                        return ExpertiseLevel.EXPERT
                    elif years >= 5:
                        return ExpertiseLevel.ADVANCED
                    elif years >= 2:
                        return ExpertiseLevel.INTERMEDIATE
                    else:
                        return ExpertiseLevel.BEGINNER
            
            # Analyze query language for expertise indicators
            beginner_indicators = ['basic', 'simple', 'beginner', 'introduction', 'what is', 'how to start']
            intermediate_indicators = ['implement', 'configure', 'setup', 'tutorial', 'guide']
            advanced_indicators = ['optimize', 'architecture', 'performance', 'scalability', 'best practices']
            expert_indicators = ['enterprise', 'production', 'distributed', 'microservices', 'advanced patterns']
            
            for indicator in beginner_indicators:
                if indicator in normalized_query:
                    expertise_score -= 2
            
            for indicator in intermediate_indicators:
                if indicator in normalized_query:
                    expertise_score += 1
            
            for indicator in advanced_indicators:
                if indicator in normalized_query:
                    expertise_score += 3
            
            for indicator in expert_indicators:
                if indicator in normalized_query:
                    expertise_score += 5
            
            # Technical jargon increases expertise score
            tech_matches = sum(1 for keyword in self.technical_keywords if keyword in normalized_query)
            expertise_score += tech_matches * 0.5
            
            # Determine expertise level
            if expertise_score <= -2:
                return ExpertiseLevel.BEGINNER
            elif expertise_score <= 2:
                return ExpertiseLevel.INTERMEDIATE
            elif expertise_score <= 6:
                return ExpertiseLevel.ADVANCED
            else:
                return ExpertiseLevel.EXPERT
                
        except Exception as e:
            logger.error(f"Error detecting expertise level: {e}")
            return ExpertiseLevel.INTERMEDIATE
    
    async def _extract_context_requirements(self, query: str, normalized_query: str) -> List[ContextRequirement]:
        """Extract context requirements for response optimization"""
        try:
            requirements = []
            
            # Time-sensitive context
            time_indicators = ['today', 'now', 'current', 'latest', 'recent', 'this week', 'this month']
            if any(indicator in normalized_query for indicator in time_indicators):
                requirements.append(ContextRequirement(
                    type='temporal',
                    importance=0.8,
                    data={'requires_current_data': True}
                ))
            
            # Location-based context
            location_indicators = ['here', 'local', 'nearby', 'in my area', 'location']
            if any(indicator in normalized_query for indicator in location_indicators):
                requirements.append(ContextRequirement(
                    type='geographical',
                    importance=0.7,
                    data={'requires_location': True}
                ))
            
            # Personal context
            personal_indicators = ['my', 'I', 'me', 'personal', 'for me']
            if any(indicator in normalized_query for indicator in personal_indicators):
                requirements.append(ContextRequirement(
                    type='personal',
                    importance=0.6,
                    data={'requires_personalization': True}
                ))
            
            # Technical context
            if any(pattern.search(query) for pattern in self.code_patterns.values()):
                requirements.append(ContextRequirement(
                    type='technical',
                    importance=0.9,
                    data={'requires_code_context': True}
                ))
            
            return requirements
            
        except Exception as e:
            logger.error(f"Error extracting context requirements: {e}")
            return []
    
    async def _determine_priority(self, query: str, normalized_query: str, user_context: Optional[Dict[str, Any]]) -> Priority:
        """Determine processing priority based on query characteristics"""
        try:
            # Check for urgent indicators
            urgent_indicators = ['urgent', 'emergency', 'critical', 'asap', 'immediately', 'now']
            if any(indicator in normalized_query for indicator in urgent_indicators):
                return Priority.URGENT
            
            # Check for high priority indicators
            high_priority_indicators = ['important', 'priority', 'deadline', 'quick', 'fast']
            if any(indicator in normalized_query for indicator in high_priority_indicators):
                return Priority.HIGH
            
            # Use user context for priority
            if user_context and 'priority' in user_context:
                return Priority(user_context['priority'])
            
            # Complex queries get higher priority
            if len(query.split()) > 50:
                return Priority.HIGH
            
            return Priority.NORMAL
            
        except Exception as e:
            logger.error(f"Error determining priority: {e}")
            return Priority.NORMAL
    
    async def _estimate_response_length(self, query: str, complexity: ComplexityLevel, content_type: ContentType) -> int:
        """Estimate expected response length in characters"""
        try:
            base_length = len(query) * 3  # Base multiplier
            
            # Adjust based on complexity
            if complexity == ComplexityLevel.SIMPLE:
                base_length *= 1.5
            elif complexity == ComplexityLevel.MODERATE:
                base_length *= 2.5
            else:  # COMPLEX
                base_length *= 4.0
            
            # Adjust based on content type
            if content_type == ContentType.CODE:
                base_length *= 2.0  # Code examples are longer
            elif content_type == ContentType.TECHNICAL:
                base_length *= 1.8
            elif content_type == ContentType.CREATIVE:
                base_length *= 1.5
            
            return min(int(base_length), 10000)  # Cap at reasonable length
            
        except Exception as e:
            logger.error(f"Error estimating response length: {e}")
            return 1000
    
    async def _requires_code_execution(self, query: str, normalized_query: str) -> bool:
        """Determine if query requires code execution"""
        try:
            execution_indicators = ['run', 'execute', 'test', 'debug', 'compile', 'output']
            return any(indicator in normalized_query for indicator in execution_indicators) and \
                   any(pattern.search(query) for pattern in self.code_patterns.values())
        except Exception as e:
            logger.error(f"Error checking code execution requirement: {e}")
            return False
    
    async def _requires_external_data(self, query: str, normalized_query: str) -> bool:
        """Determine if query requires external data sources"""
        try:
            external_indicators = ['current', 'latest', 'news', 'weather', 'stock', 'price', 'today']
            return any(indicator in normalized_query for indicator in external_indicators)
        except Exception as e:
            logger.error(f"Error checking external data requirement: {e}")
            return False
    
    async def _detect_language(self, query: str) -> str:
        """Detect query language"""
        try:
            scores = {}
            for lang, pattern in self.language_patterns.items():
                matches = len(pattern.findall(query))
                scores[lang] = matches
            
            return max(scores, key=scores.get) if scores else 'english'
        except Exception as e:
            logger.error(f"Error detecting language: {e}")
            return 'english'
    
    async def _detect_domain(self, query: str, normalized_query: str) -> Optional[str]:
        """Detect domain-specific content"""
        try:
            for domain, keywords in self.domain_keywords.items():
                matches = sum(1 for keyword in keywords if keyword in normalized_query)
                if matches >= 2:  # Require multiple matches for confidence
                    return domain
            return None
        except Exception as e:
            logger.error(f"Error detecting domain: {e}")
            return None
    
    async def _calculate_confidence_score(self, query: str, complexity: ComplexityLevel, content_type: ContentType) -> float:
        """Calculate confidence score for the analysis"""
        try:
            confidence = 0.7  # Base confidence
            
            # Higher confidence for longer, more detailed queries
            word_count = len(query.split())
            if word_count > 20:
                confidence += 0.2
            elif word_count > 10:
                confidence += 0.1
            
            # Higher confidence for queries with clear indicators
            if any(pattern.search(query) for pattern in self.code_patterns.values()):
                confidence += 0.1
            
            tech_matches = sum(1 for keyword in self.technical_keywords if keyword in query.lower())
            confidence += min(tech_matches * 0.05, 0.2)
            
            return min(confidence, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 0.5
    
    def _create_default_analysis(self, query: str) -> QueryAnalysis:
        """Create default analysis when errors occur"""
        return QueryAnalysis(
            complexity=ComplexityLevel.MODERATE,
            content_type=ContentType.TEXT,
            modality_requirements=[ModalityType.TEXT],
            user_expertise_level=ExpertiseLevel.INTERMEDIATE,
            context_requirements=[],
            processing_priority=Priority.NORMAL,
            estimated_response_length=1000,
            requires_code_execution=False,
            requires_external_data=False,
            language='english',
            domain_specific=None,
            confidence_score=0.3,
            analysis_metadata={'error': True, 'query_length': len(query)}
        )