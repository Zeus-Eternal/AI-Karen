"""
Content Optimization Engine for Response Quality Improvement

This module implements intelligent content optimization capabilities including:
- Redundancy elimination
- Content relevance analysis and prioritization
- Content depth adaptation based on user expertise
- Intelligent formatting system
- Content synthesis from multiple sources
- Content prioritization for progressive delivery
"""

import re
import asyncio
from typing import List, Dict, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)


class ContentType(Enum):
    """Types of content for optimization"""
    TEXT = "text"
    CODE = "code"
    LIST = "list"
    TABLE = "table"
    MIXED = "mixed"
    TECHNICAL = "technical"
    CONVERSATIONAL = "conversational"


class ExpertiseLevel(Enum):
    """User expertise levels for content adaptation"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class FormatType(Enum):
    """Optimal presentation formats"""
    PLAIN_TEXT = "plain_text"
    MARKDOWN = "markdown"
    BULLET_POINTS = "bullet_points"
    NUMBERED_LIST = "numbered_list"
    TABLE = "table"
    CODE_BLOCK = "code_block"
    HIERARCHICAL = "hierarchical"


class Priority(Enum):
    """Content priority levels for progressive delivery"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    SUPPLEMENTARY = 5


@dataclass
class ContentSection:
    """Represents a section of content with metadata"""
    content: str
    content_type: ContentType
    priority: Priority
    relevance_score: float
    expertise_level: ExpertiseLevel
    format_type: FormatType
    source_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    estimated_read_time: float = 0.0
    is_actionable: bool = False


@dataclass
class RelevanceScore:
    """Detailed relevance scoring for content"""
    overall_score: float
    keyword_relevance: float
    context_relevance: float
    user_relevance: float
    freshness_score: float
    actionability_score: float
    confidence: float


@dataclass
class Context:
    """User and query context for optimization"""
    user_id: Optional[str] = None
    expertise_level: ExpertiseLevel = ExpertiseLevel.INTERMEDIATE
    query_intent: Optional[str] = None
    previous_queries: List[str] = field(default_factory=list)
    domain_knowledge: List[str] = field(default_factory=list)
    preferred_formats: List[FormatType] = field(default_factory=list)
    time_constraints: Optional[float] = None
    device_type: Optional[str] = None


@dataclass
class OptimizedContent:
    """Result of content optimization"""
    sections: List[ContentSection]
    total_length: int
    estimated_read_time: float
    optimization_applied: List[str]
    redundancy_removed: int
    relevance_improved: float
    format_optimized: bool


class ContentOptimizationEngine:
    """
    Main engine for content optimization with redundancy elimination,
    relevance analysis, depth adaptation, and intelligent formatting.
    """
    
    def __init__(self):
        self.redundancy_threshold = 0.8
        self.relevance_threshold = 0.3
        self.max_content_length = 10000
        self.format_patterns = self._initialize_format_patterns()
        self.expertise_adapters = self._initialize_expertise_adapters()
        self.content_cache = {}
        
    def _initialize_format_patterns(self) -> Dict[ContentType, Dict[str, str]]:
        """Initialize patterns for content type detection and formatting"""
        return {
            ContentType.CODE: {
                'patterns': [
                    r'```[\w]*\n.*?\n```',
                    r'`[^`]+`',
                    r'def\s+\w+\(',
                    r'class\s+\w+',
                    r'import\s+\w+',
                    r'from\s+\w+\s+import',
                    r'function\s+\w+\(',
                    r'var\s+\w+\s*=',
                    r'const\s+\w+\s*=',
                    r'let\s+\w+\s*='
                ],
                'format': FormatType.CODE_BLOCK
            },
            ContentType.LIST: {
                'patterns': [
                    r'^\s*[-*+]\s+',
                    r'^\s*\d+\.\s+',
                    r'^\s*[a-zA-Z]\.\s+'
                ],
                'format': FormatType.BULLET_POINTS
            },
            ContentType.TABLE: {
                'patterns': [
                    r'\|.*\|.*\|',
                    r'^\s*\w+\s*:\s*\w+',
                    r'Column\s+\d+',
                    r'Row\s+\d+'
                ],
                'format': FormatType.TABLE
            }
        }
    
    def _initialize_expertise_adapters(self) -> Dict[ExpertiseLevel, Dict[str, Any]]:
        """Initialize content adaptation rules for different expertise levels"""
        return {
            ExpertiseLevel.BEGINNER: {
                'detail_level': 'high',
                'technical_terms': 'explain',
                'examples': 'many',
                'context': 'extensive',
                'max_complexity': 3
            },
            ExpertiseLevel.INTERMEDIATE: {
                'detail_level': 'medium',
                'technical_terms': 'brief_explain',
                'examples': 'some',
                'context': 'moderate',
                'max_complexity': 6
            },
            ExpertiseLevel.ADVANCED: {
                'detail_level': 'low',
                'technical_terms': 'assume_known',
                'examples': 'few',
                'context': 'minimal',
                'max_complexity': 8
            },
            ExpertiseLevel.EXPERT: {
                'detail_level': 'minimal',
                'technical_terms': 'assume_known',
                'examples': 'none',
                'context': 'none',
                'max_complexity': 10
            }
        }

    async def analyze_content_relevance(self, content: str, context: Context) -> RelevanceScore:
        """
        Analyze content relevance based on context and user needs.
        Implements requirement 1.2: eliminate redundant content and prioritize essential information.
        """
        try:
            # Extract keywords from query intent and context
            query_keywords = self._extract_keywords(context.query_intent or "")
            domain_keywords = set()
            for domain in context.domain_knowledge:
                domain_keywords.update(self._extract_keywords(domain))
            
            # Calculate keyword relevance
            content_keywords = self._extract_keywords(content)
            keyword_overlap = len(query_keywords.intersection(content_keywords))
            keyword_relevance = keyword_overlap / max(len(query_keywords), 1)
            
            # Calculate context relevance
            context_relevance = self._calculate_context_relevance(content, context)
            
            # Calculate user relevance based on expertise level
            user_relevance = self._calculate_user_relevance(content, context.expertise_level)
            
            # Calculate freshness score (assume recent content is more relevant)
            freshness_score = 1.0  # Default for now, could be enhanced with timestamps
            
            # Calculate actionability score
            actionability_score = self._calculate_actionability_score(content)
            
            # Calculate overall score with weights
            overall_score = (
                keyword_relevance * 0.3 +
                context_relevance * 0.25 +
                user_relevance * 0.2 +
                freshness_score * 0.1 +
                actionability_score * 0.15
            )
            
            confidence = min(1.0, (keyword_relevance + context_relevance + user_relevance) / 3)
            
            return RelevanceScore(
                overall_score=overall_score,
                keyword_relevance=keyword_relevance,
                context_relevance=context_relevance,
                user_relevance=user_relevance,
                freshness_score=freshness_score,
                actionability_score=actionability_score,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Error analyzing content relevance: {e}")
            return RelevanceScore(
                overall_score=0.5,
                keyword_relevance=0.5,
                context_relevance=0.5,
                user_relevance=0.5,
                freshness_score=0.5,
                actionability_score=0.5,
                confidence=0.1
            )

    async def eliminate_redundant_content(self, content: str) -> str:
        """
        Remove redundant and unnecessary content from responses.
        Implements requirement 1.2: eliminate redundant content.
        """
        try:
            # Split content into sentences
            sentences = self._split_into_sentences(content)
            
            # Calculate similarity matrix
            similarity_matrix = self._calculate_sentence_similarities(sentences)
            
            # Identify redundant sentences
            redundant_indices = set()
            for i in range(len(sentences)):
                for j in range(i + 1, len(sentences)):
                    if similarity_matrix[i][j] > self.redundancy_threshold:
                        # Keep the shorter, more concise sentence
                        if len(sentences[i]) > len(sentences[j]):
                            redundant_indices.add(i)
                        else:
                            redundant_indices.add(j)
            
            # Remove redundant sentences
            filtered_sentences = [
                sentence for i, sentence in enumerate(sentences)
                if i not in redundant_indices
            ]
            
            # Remove redundant phrases within sentences
            optimized_sentences = []
            for sentence in filtered_sentences:
                optimized_sentence = self._remove_redundant_phrases(sentence)
                if optimized_sentence.strip():
                    optimized_sentences.append(optimized_sentence)
            
            return ' '.join(optimized_sentences)
            
        except Exception as e:
            logger.error(f"Error eliminating redundant content: {e}")
            return content

    async def prioritize_content_sections(self, content: str, context: Context) -> List[ContentSection]:
        """
        Prioritize content sections for progressive delivery.
        Implements requirement 1.3: prioritize essential information.
        """
        try:
            # Split content into logical sections
            sections = self._split_into_sections(content)
            
            content_sections = []
            for i, section in enumerate(sections):
                # Analyze section properties
                content_type = self._detect_content_type(section)
                relevance_score = await self.analyze_content_relevance(section, context)
                
                # Determine priority based on relevance and content type
                priority = self._determine_priority(relevance_score, content_type, section)
                
                # Determine optimal format
                format_type = self._determine_optimal_format(section, content_type)
                
                # Check if content is actionable
                is_actionable = self._is_actionable_content(section)
                
                # Estimate read time
                read_time = self._estimate_read_time(section)
                
                content_section = ContentSection(
                    content=section,
                    content_type=content_type,
                    priority=priority,
                    relevance_score=relevance_score.overall_score,
                    expertise_level=context.expertise_level,
                    format_type=format_type,
                    source_id=f"section_{i}",
                    tags=self._extract_tags(section),
                    estimated_read_time=read_time,
                    is_actionable=is_actionable
                )
                
                content_sections.append(content_section)
            
            # Sort by priority (critical first) and relevance
            content_sections.sort(key=lambda x: (x.priority.value, -x.relevance_score))
            
            return content_sections
            
        except Exception as e:
            logger.error(f"Error prioritizing content sections: {e}")
            return [ContentSection(
                content=content,
                content_type=ContentType.TEXT,
                priority=Priority.MEDIUM,
                relevance_score=0.5,
                expertise_level=context.expertise_level,
                format_type=FormatType.PLAIN_TEXT
            )]

    async def optimize_formatting(self, content: str, format_type: FormatType) -> str:
        """
        Optimize formatting for readability and usability.
        Implements requirement 3.4: optimize formatting for clarity and usability.
        """
        try:
            if format_type == FormatType.CODE_BLOCK:
                return self._format_as_code_block(content)
            elif format_type == FormatType.BULLET_POINTS:
                return self._format_as_bullet_points(content)
            elif format_type == FormatType.NUMBERED_LIST:
                return self._format_as_numbered_list(content)
            elif format_type == FormatType.TABLE:
                return self._format_as_table(content)
            elif format_type == FormatType.HIERARCHICAL:
                return self._format_as_hierarchical(content)
            elif format_type == FormatType.MARKDOWN:
                return self._format_as_markdown(content)
            else:
                return self._format_as_plain_text(content)
                
        except Exception as e:
            logger.error(f"Error optimizing formatting: {e}")
            return content

    async def adapt_content_depth(self, content: str, user_level: ExpertiseLevel, context: Context) -> str:
        """
        Adapt content depth based on user expertise and context.
        Implements requirement 1.4: adapt content based on user expertise level and context.
        """
        try:
            adapter_config = self.expertise_adapters[user_level]
            
            # Adjust technical detail level
            if adapter_config['detail_level'] == 'high':
                content = self._add_detailed_explanations(content)
            elif adapter_config['detail_level'] == 'minimal':
                content = self._remove_excessive_detail(content)
            
            # Handle technical terms
            if adapter_config['technical_terms'] == 'explain':
                content = self._explain_technical_terms(content)
            elif adapter_config['technical_terms'] == 'brief_explain':
                content = self._briefly_explain_technical_terms(content)
            
            # Adjust examples
            if adapter_config['examples'] == 'many':
                content = self._add_more_examples(content)
            elif adapter_config['examples'] == 'none':
                content = self._remove_examples(content)
            
            # Adjust context
            if adapter_config['context'] == 'extensive':
                content = self._add_extensive_context(content)
            elif adapter_config['context'] == 'none':
                content = self._remove_context(content)
            
            # Limit complexity
            max_complexity = adapter_config['max_complexity']
            content = self._limit_complexity(content, max_complexity)
            
            return content
            
        except Exception as e:
            logger.error(f"Error adapting content depth: {e}")
            return content

    async def synthesize_content_from_sources(self, sources: List[Dict[str, Any]], context: Context) -> str:
        """
        Synthesize and combine information from multiple sources efficiently.
        Implements requirement 3.4: synthesize information from multiple sources efficiently.
        """
        try:
            if not sources:
                return ""
            
            # Extract and analyze content from each source
            source_contents = []
            for source in sources:
                content = source.get('content', '')
                source_id = source.get('id', 'unknown')
                relevance = await self.analyze_content_relevance(content, context)
                
                source_contents.append({
                    'content': content,
                    'id': source_id,
                    'relevance': relevance.overall_score,
                    'sections': await self.prioritize_content_sections(content, context)
                })
            
            # Sort sources by relevance
            source_contents.sort(key=lambda x: x['relevance'], reverse=True)
            
            # Synthesize content by combining high-relevance sections
            synthesized_sections = []
            seen_content_hashes = set()
            
            for source in source_contents:
                for section in source['sections']:
                    # Check for duplicate content
                    content_hash = hashlib.md5(section.content.encode()).hexdigest()
                    if content_hash not in seen_content_hashes:
                        seen_content_hashes.add(content_hash)
                        
                        # Only include high-relevance sections
                        if section.relevance_score > self.relevance_threshold:
                            synthesized_sections.append(section)
            
            # Sort synthesized sections by priority
            synthesized_sections.sort(key=lambda x: (x.priority.value, -x.relevance_score))
            
            # Combine sections into coherent content
            synthesized_content = self._combine_sections_coherently(synthesized_sections)
            
            # Remove any remaining redundancy
            final_content = await self.eliminate_redundant_content(synthesized_content)
            
            return final_content
            
        except Exception as e:
            logger.error(f"Error synthesizing content from sources: {e}")
            return sources[0].get('content', '') if sources else ""

    async def optimize_content(self, content: str, context: Context) -> OptimizedContent:
        """
        Main optimization method that applies all optimization techniques.
        Implements requirements 1.2, 1.3, 1.4, 3.4, 8.1, 8.2.
        """
        try:
            optimization_applied = []
            original_length = len(content)
            
            # Step 1: Eliminate redundant content
            content = await self.eliminate_redundant_content(content)
            redundancy_removed = original_length - len(content)
            optimization_applied.append("redundancy_elimination")
            
            # Step 2: Adapt content depth based on user expertise
            content = await self.adapt_content_depth(content, context.expertise_level, context)
            optimization_applied.append("depth_adaptation")
            
            # Step 3: Prioritize content sections
            sections = await self.prioritize_content_sections(content, context)
            optimization_applied.append("content_prioritization")
            
            # Step 4: Optimize formatting for each section
            for section in sections:
                section.content = await self.optimize_formatting(section.content, section.format_type)
            optimization_applied.append("format_optimization")
            
            # Calculate metrics
            total_length = sum(len(section.content) for section in sections)
            estimated_read_time = sum(section.estimated_read_time for section in sections)
            
            # Calculate relevance improvement
            relevance_scores = [section.relevance_score for section in sections]
            avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.5
            relevance_improved = max(0, avg_relevance - 0.5)  # Improvement over baseline
            
            return OptimizedContent(
                sections=sections,
                total_length=total_length,
                estimated_read_time=estimated_read_time,
                optimization_applied=optimization_applied,
                redundancy_removed=redundancy_removed,
                relevance_improved=relevance_improved,
                format_optimized=True
            )
            
        except Exception as e:
            logger.error(f"Error optimizing content: {e}")
            # Return minimal optimization on error
            return OptimizedContent(
                sections=[ContentSection(
                    content=content,
                    content_type=ContentType.TEXT,
                    priority=Priority.MEDIUM,
                    relevance_score=0.5,
                    expertise_level=context.expertise_level,
                    format_type=FormatType.PLAIN_TEXT
                )],
                total_length=len(content),
                estimated_read_time=len(content) / 200,  # Rough estimate
                optimization_applied=["error_fallback"],
                redundancy_removed=0,
                relevance_improved=0.0,
                format_optimized=False
            )

    # Helper methods for content analysis and processing
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """Extract keywords from text"""
        if not text:
            return set()
        
        # Simple keyword extraction (could be enhanced with NLP)
        words = re.findall(r'\b\w+\b', text.lower())
        # Filter out common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
        return set(word for word in words if len(word) > 2 and word not in stop_words)
    
    def _calculate_context_relevance(self, content: str, context: Context) -> float:
        """Calculate how relevant content is to the given context"""
        relevance = 0.5  # Base relevance
        
        # Check domain knowledge alignment
        content_lower = content.lower()
        for domain in context.domain_knowledge:
            if domain.lower() in content_lower:
                relevance += 0.1
        
        # Check previous query alignment
        for prev_query in context.previous_queries[-3:]:  # Last 3 queries
            query_keywords = self._extract_keywords(prev_query)
            content_keywords = self._extract_keywords(content)
            overlap = len(query_keywords.intersection(content_keywords))
            if overlap > 0:
                relevance += 0.05 * overlap
        
        return min(1.0, relevance)
    
    def _calculate_user_relevance(self, content: str, expertise_level: ExpertiseLevel) -> float:
        """Calculate relevance based on user expertise level"""
        # Count technical terms and complexity indicators
        technical_patterns = [
            r'\b(?:API|SDK|JSON|XML|HTTP|REST|GraphQL|OAuth|JWT)\b',
            r'\b(?:algorithm|implementation|optimization|architecture)\b',
            r'\b(?:function|method|class|interface|inheritance)\b',
            r'\b(?:database|query|schema|index|transaction)\b'
        ]
        
        technical_count = sum(len(re.findall(pattern, content, re.IGNORECASE)) for pattern in technical_patterns)
        complexity_score = min(1.0, technical_count / 10)  # Normalize
        
        # Adjust relevance based on expertise level
        if expertise_level == ExpertiseLevel.BEGINNER:
            return max(0.2, 1.0 - complexity_score * 0.5)  # Prefer simpler content
        elif expertise_level == ExpertiseLevel.INTERMEDIATE:
            return 0.7 + complexity_score * 0.3  # Balanced
        elif expertise_level == ExpertiseLevel.ADVANCED:
            return 0.5 + complexity_score * 0.5  # Prefer more technical
        else:  # EXPERT
            return 0.3 + complexity_score * 0.7  # Strongly prefer technical
    
    def _calculate_actionability_score(self, content: str) -> float:
        """Calculate how actionable the content is"""
        actionable_patterns = [
            r'\b(?:step|steps|follow|do|run|execute|install|configure)\b',
            r'\b(?:click|select|choose|enter|type|copy|paste)\b',
            r'\b(?:example|sample|demo|tutorial|guide)\b',
            r'```[\w]*\n.*?\n```',  # Code blocks
            r'^\s*[-*+]\s+',  # List items
            r'^\s*\d+\.\s+'  # Numbered steps
        ]
        
        actionable_count = sum(len(re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)) for pattern in actionable_patterns)
        return min(1.0, actionable_count / 5)  # Normalize
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting (could be enhanced with NLP)
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _calculate_sentence_similarities(self, sentences: List[str]) -> List[List[float]]:
        """Calculate similarity matrix between sentences"""
        n = len(sentences)
        similarity_matrix = [[0.0] * n for _ in range(n)]
        
        for i in range(n):
            for j in range(i + 1, n):
                similarity = self._calculate_text_similarity(sentences[i], sentences[j])
                similarity_matrix[i][j] = similarity
                similarity_matrix[j][i] = similarity
        
        return similarity_matrix
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts using Jaccard similarity"""
        words1 = set(self._extract_keywords(text1))
        words2 = set(self._extract_keywords(text2))
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _remove_redundant_phrases(self, sentence: str) -> str:
        """Remove redundant phrases within a sentence"""
        # Remove common redundant phrases
        redundant_phrases = [
            r'\b(?:in other words|that is to say|to put it simply|basically|essentially)\b',
            r'\b(?:as mentioned before|as stated earlier|as we discussed)\b',
            r'\b(?:it should be noted that|it is important to note|please note)\b'
        ]
        
        for pattern in redundant_phrases:
            sentence = re.sub(pattern, '', sentence, flags=re.IGNORECASE)
        
        # Clean up extra spaces
        sentence = re.sub(r'\s+', ' ', sentence).strip()
        return sentence
    
    def _split_into_sections(self, content: str) -> List[str]:
        """Split content into logical sections"""
        # Split by headers, double newlines, or other section markers
        sections = re.split(r'\n\s*\n|\n#{1,6}\s+|\n\*\*[^*]+\*\*\n', content)
        return [section.strip() for section in sections if section.strip()]
    
    def _detect_content_type(self, content: str) -> ContentType:
        """Detect the type of content"""
        content_lower = content.lower()
        
        # Check for code patterns
        for pattern in self.format_patterns[ContentType.CODE]['patterns']:
            if re.search(pattern, content, re.MULTILINE | re.DOTALL):
                return ContentType.CODE
        
        # Check for list patterns
        for pattern in self.format_patterns[ContentType.LIST]['patterns']:
            if re.search(pattern, content, re.MULTILINE):
                return ContentType.LIST
        
        # Check for table patterns
        for pattern in self.format_patterns[ContentType.TABLE]['patterns']:
            if re.search(pattern, content, re.MULTILINE):
                return ContentType.TABLE
        
        # Check for technical content
        technical_keywords = ['api', 'function', 'method', 'class', 'algorithm', 'implementation']
        if any(keyword in content_lower for keyword in technical_keywords):
            return ContentType.TECHNICAL
        
        # Default to conversational
        return ContentType.CONVERSATIONAL
    
    def _determine_priority(self, relevance_score: RelevanceScore, content_type: ContentType, content: str) -> Priority:
        """Determine priority based on relevance and content characteristics"""
        # High actionability gets higher priority
        if relevance_score.actionability_score > 0.7:
            return Priority.CRITICAL
        
        # High overall relevance
        if relevance_score.overall_score > 0.8:
            return Priority.HIGH
        
        # Code and technical content often important
        if content_type in [ContentType.CODE, ContentType.TECHNICAL]:
            return Priority.HIGH
        
        # Medium relevance
        if relevance_score.overall_score > 0.5:
            return Priority.MEDIUM
        
        # Low relevance
        if relevance_score.overall_score > 0.3:
            return Priority.LOW
        
        return Priority.SUPPLEMENTARY
    
    def _determine_optimal_format(self, content: str, content_type: ContentType) -> FormatType:
        """Determine optimal format for content"""
        if content_type == ContentType.CODE:
            return FormatType.CODE_BLOCK
        elif content_type == ContentType.LIST:
            return FormatType.BULLET_POINTS
        elif content_type == ContentType.TABLE:
            return FormatType.TABLE
        elif content_type == ContentType.TECHNICAL:
            return FormatType.MARKDOWN
        else:
            return FormatType.PLAIN_TEXT
    
    def _is_actionable_content(self, content: str) -> bool:
        """Check if content contains actionable information"""
        actionable_indicators = [
            'step', 'follow', 'run', 'execute', 'install', 'configure',
            'click', 'select', 'enter', 'copy', 'example', 'tutorial'
        ]
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in actionable_indicators)
    
    def _estimate_read_time(self, content: str) -> float:
        """Estimate reading time in minutes (assuming 200 words per minute)"""
        word_count = len(content.split())
        return word_count / 200.0
    
    def _extract_tags(self, content: str) -> List[str]:
        """Extract relevant tags from content"""
        tags = []
        content_lower = content.lower()
        
        # Technical tags
        if any(term in content_lower for term in ['code', 'function', 'method', 'class']):
            tags.append('technical')
        
        # Tutorial tags
        if any(term in content_lower for term in ['step', 'tutorial', 'guide', 'example']):
            tags.append('tutorial')
        
        # Reference tags
        if any(term in content_lower for term in ['api', 'documentation', 'reference']):
            tags.append('reference')
        
        return tags
    
    # Formatting methods
    
    def _format_as_code_block(self, content: str) -> str:
        """Format content as a code block"""
        if not content.startswith('```'):
            return f"```\n{content}\n```"
        return content
    
    def _format_as_bullet_points(self, content: str) -> str:
        """Format content as bullet points"""
        lines = content.split('\n')
        formatted_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith(('- ', '* ', '+ ')):
                formatted_lines.append(f"- {line}")
            else:
                formatted_lines.append(line)
        return '\n'.join(formatted_lines)
    
    def _format_as_numbered_list(self, content: str) -> str:
        """Format content as a numbered list"""
        lines = content.split('\n')
        formatted_lines = []
        counter = 1
        for line in lines:
            line = line.strip()
            if line and not re.match(r'^\d+\.', line):
                formatted_lines.append(f"{counter}. {line}")
                counter += 1
            else:
                formatted_lines.append(line)
        return '\n'.join(formatted_lines)
    
    def _format_as_table(self, content: str) -> str:
        """Format content as a table (basic implementation)"""
        # This is a simplified table formatter
        lines = content.split('\n')
        if len(lines) < 2:
            return content
        
        # Try to detect key-value pairs
        table_rows = []
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                table_rows.append(f"| {key.strip()} | {value.strip()} |")
        
        if table_rows:
            header = "| Key | Value |\n|-----|-------|"
            return header + '\n' + '\n'.join(table_rows)
        
        return content
    
    def _format_as_hierarchical(self, content: str) -> str:
        """Format content with hierarchical structure"""
        lines = content.split('\n')
        formatted_lines = []
        indent_level = 0
        
        for line in lines:
            line = line.strip()
            if line:
                # Simple hierarchical formatting
                if line.endswith(':'):
                    formatted_lines.append(f"{'  ' * indent_level}## {line}")
                    indent_level += 1
                else:
                    formatted_lines.append(f"{'  ' * indent_level}- {line}")
        
        return '\n'.join(formatted_lines)
    
    def _format_as_markdown(self, content: str) -> str:
        """Format content as markdown"""
        # Basic markdown formatting
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                # Make headers
                if line.endswith(':') and len(line) < 50:
                    formatted_lines.append(f"## {line[:-1]}")
                # Make code inline
                elif '`' not in line and any(keyword in line.lower() for keyword in ['function', 'method', 'class', 'variable']):
                    formatted_lines.append(f"`{line}`")
                else:
                    formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _format_as_plain_text(self, content: str) -> str:
        """Format content as clean plain text"""
        # Remove excessive formatting and clean up
        content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)  # Remove bold
        content = re.sub(r'\*([^*]+)\*', r'\1', content)      # Remove italic
        content = re.sub(r'`([^`]+)`', r'\1', content)        # Remove inline code
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)   # Remove excessive newlines
        return content.strip()
    
    # Content adaptation methods
    
    def _add_detailed_explanations(self, content: str) -> str:
        """Add detailed explanations for beginners"""
        # This is a simplified implementation
        # In practice, this would use NLP to identify concepts that need explanation
        technical_terms = {
            'API': 'API (Application Programming Interface)',
            'JSON': 'JSON (JavaScript Object Notation)',
            'HTTP': 'HTTP (HyperText Transfer Protocol)',
            'REST': 'REST (Representational State Transfer)'
        }
        
        for term, explanation in technical_terms.items():
            content = re.sub(rf'\b{term}\b', explanation, content, flags=re.IGNORECASE)
        
        return content
    
    def _remove_excessive_detail(self, content: str) -> str:
        """Remove excessive detail for experts"""
        # Remove parenthetical explanations
        content = re.sub(r'\s*\([^)]*\)', '', content)
        # Remove "in other words" type phrases
        content = re.sub(r'\b(?:in other words|that is to say|to put it simply)[^.]*\.', '', content, flags=re.IGNORECASE)
        return content
    
    def _explain_technical_terms(self, content: str) -> str:
        """Add explanations for technical terms"""
        return self._add_detailed_explanations(content)
    
    def _briefly_explain_technical_terms(self, content: str) -> str:
        """Add brief explanations for technical terms"""
        # Similar to detailed but shorter
        return self._add_detailed_explanations(content)
    
    def _add_more_examples(self, content: str) -> str:
        """Add more examples for beginners"""
        # This would be enhanced with actual example generation
        if 'example' not in content.lower():
            content += "\n\nFor example: [This would be enhanced with context-specific examples]"
        return content
    
    def _remove_examples(self, content: str) -> str:
        """Remove examples for experts"""
        # Remove example sections
        content = re.sub(r'\n\s*(?:For example|Example)[^.]*\.', '', content, flags=re.IGNORECASE)
        return content
    
    def _add_extensive_context(self, content: str) -> str:
        """Add extensive context for beginners"""
        # This would be enhanced with actual context generation
        return f"Context: {content}"
    
    def _remove_context(self, content: str) -> str:
        """Remove context for experts"""
        # Remove context sections
        content = re.sub(r'\n\s*(?:Context|Background)[^.]*\.', '', content, flags=re.IGNORECASE)
        return content
    
    def _limit_complexity(self, content: str, max_complexity: int) -> str:
        """Limit content complexity based on level"""
        # Simple complexity limiting based on sentence length and technical terms
        sentences = self._split_into_sentences(content)
        filtered_sentences = []
        
        for sentence in sentences:
            complexity_score = len(sentence.split()) / 10  # Word count based complexity
            technical_count = len(re.findall(r'\b(?:API|SDK|JSON|XML|HTTP|REST|GraphQL|OAuth|JWT)\b', sentence, re.IGNORECASE))
            complexity_score += technical_count
            
            if complexity_score <= max_complexity:
                filtered_sentences.append(sentence)
        
        return '. '.join(filtered_sentences)
    
    def _combine_sections_coherently(self, sections: List[ContentSection]) -> str:
        """Combine content sections into coherent text"""
        if not sections:
            return ""
        
        combined_content = []
        current_topic = None
        
        for section in sections:
            # Add topic headers for organization
            if section.content_type != current_topic:
                if section.content_type == ContentType.CODE:
                    combined_content.append("\n## Code Examples\n")
                elif section.content_type == ContentType.TECHNICAL:
                    combined_content.append("\n## Technical Details\n")
                current_topic = section.content_type
            
            combined_content.append(section.content)
            combined_content.append("\n")
        
        return '\n'.join(combined_content).strip()