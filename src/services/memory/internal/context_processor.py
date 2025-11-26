"""
Context Processor for Intelligent Response Optimization

This module extracts and processes relevant context information to optimize
response generation, including user context, conversation history, and
environmental factors.
"""

import asyncio
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime, timedelta
import json
import re

from ...internal.query_analyzer import QueryAnalysis, ContextRequirement

logger = logging.getLogger(__name__)


class ContextType(Enum):
    """Types of context information"""
    USER_PROFILE = "user_profile"
    CONVERSATION_HISTORY = "conversation_history"
    TEMPORAL = "temporal"
    GEOGRAPHICAL = "geographical"
    TECHNICAL = "technical"
    PERSONAL = "personal"
    DOMAIN_SPECIFIC = "domain_specific"
    SYSTEM_STATE = "system_state"


class ContextRelevance(Enum):
    """Context relevance levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ContextItem:
    """Individual context item with metadata"""
    type: ContextType
    content: Any
    relevance: ContextRelevance
    confidence: float
    timestamp: datetime
    source: str
    metadata: Dict[str, Any]


@dataclass
class ProcessedContext:
    """Processed context information for response optimization"""
    user_context: Dict[str, Any]
    conversation_context: Dict[str, Any]
    technical_context: Dict[str, Any]
    temporal_context: Dict[str, Any]
    geographical_context: Dict[str, Any]
    domain_context: Dict[str, Any]
    system_context: Dict[str, Any]
    context_summary: str
    relevance_score: float
    processing_metadata: Dict[str, Any]


class ContextProcessor:
    """
    Advanced context processor that extracts and organizes relevant information
    for response optimization based on query analysis and available context sources.
    """
    
    def __init__(self):
        self.context_cache = {}
        self.user_profiles = {}
        self.conversation_histories = {}
        self.context_extractors = self._initialize_extractors()
        self.relevance_weights = self._load_relevance_weights()
        
    def _initialize_extractors(self) -> Dict[str, Any]:
        """Initialize context extractors for different types"""
        return {
            'user_profile': self._extract_user_profile_context,
            'conversation': self._extract_conversation_context,
            'temporal': self._extract_temporal_context,
            'geographical': self._extract_geographical_context,
            'technical': self._extract_technical_context,
            'personal': self._extract_personal_context,
            'domain': self._extract_domain_context,
            'system': self._extract_system_context
        }
    
    def _load_relevance_weights(self) -> Dict[str, float]:
        """Load relevance weights for different context types"""
        return {
            'user_profile': 0.8,
            'conversation_history': 0.9,
            'temporal': 0.7,
            'geographical': 0.6,
            'technical': 0.85,
            'personal': 0.75,
            'domain_specific': 0.8,
            'system_state': 0.5
        }
    
    async def process_context(
        self,
        query_analysis: QueryAnalysis,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> ProcessedContext:
        """
        Process and extract relevant context information for response optimization
        
        Args:
            query_analysis: Comprehensive query analysis results
            user_id: Optional user identifier for personalization
            conversation_id: Optional conversation identifier for history
            additional_context: Optional additional context information
            
        Returns:
            ProcessedContext: Organized context information
        """
        try:
            # Extract context from different sources concurrently
            context_tasks = []
            
            # User profile context
            if user_id:
                context_tasks.append(self._extract_user_profile_context(user_id, query_analysis))
            else:
                context_tasks.append(asyncio.create_task(self._create_empty_context('user_profile')))
            
            # Conversation history context
            if conversation_id:
                context_tasks.append(self._extract_conversation_context(conversation_id, query_analysis))
            else:
                context_tasks.append(asyncio.create_task(self._create_empty_context('conversation')))
            
            # Technical context
            context_tasks.append(self._extract_technical_context(query_analysis))
            
            # Temporal context
            context_tasks.append(self._extract_temporal_context(query_analysis))
            
            # Geographical context
            context_tasks.append(self._extract_geographical_context(query_analysis, additional_context))
            
            # Domain-specific context
            context_tasks.append(self._extract_domain_context(query_analysis))
            
            # System state context
            context_tasks.append(self._extract_system_context(query_analysis, additional_context))
            
            # Wait for all context extraction to complete
            context_results = await asyncio.gather(*context_tasks, return_exceptions=True)
            
            # Process results and handle exceptions
            user_context = context_results[0] if not isinstance(context_results[0], Exception) else {}
            conversation_context = context_results[1] if not isinstance(context_results[1], Exception) else {}
            technical_context = context_results[2] if not isinstance(context_results[2], Exception) else {}
            temporal_context = context_results[3] if not isinstance(context_results[3], Exception) else {}
            geographical_context = context_results[4] if not isinstance(context_results[4], Exception) else {}
            domain_context = context_results[5] if not isinstance(context_results[5], Exception) else {}
            system_context = context_results[6] if not isinstance(context_results[6], Exception) else {}
            
            # Generate context summary
            context_summary = await self._generate_context_summary(
                user_context, conversation_context, technical_context,
                temporal_context, geographical_context, domain_context, system_context
            )
            
            # Calculate overall relevance score
            relevance_score = await self._calculate_relevance_score(
                query_analysis, user_context, conversation_context, technical_context
            )
            
            # Create processing metadata
            processing_metadata = {
                'processed_at': datetime.utcnow().isoformat(),
                'context_sources': len([c for c in context_results if not isinstance(c, Exception)]),
                'extraction_errors': len([c for c in context_results if isinstance(c, Exception)]),
                'query_complexity': query_analysis.complexity.value,
                'context_requirements_count': len(query_analysis.context_requirements)
            }
            
            return ProcessedContext(
                user_context=user_context,
                conversation_context=conversation_context,
                technical_context=technical_context,
                temporal_context=temporal_context,
                geographical_context=geographical_context,
                domain_context=domain_context,
                system_context=system_context,
                context_summary=context_summary,
                relevance_score=relevance_score,
                processing_metadata=processing_metadata
            )
            
        except Exception as e:
            logger.error(f"Error processing context: {e}")
            return await self._create_fallback_context(query_analysis)
    
    async def _extract_user_profile_context(self, user_id: str, query_analysis: QueryAnalysis) -> Dict[str, Any]:
        """Extract user profile context for personalization"""
        try:
            # Get user profile from cache or storage
            user_profile = self.user_profiles.get(user_id, {})
            
            context = {
                'user_id': user_id,
                'expertise_level': user_profile.get('expertise_level', 'intermediate'),
                'preferred_response_style': user_profile.get('response_style', 'balanced'),
                'language_preference': user_profile.get('language', 'english'),
                'technical_background': user_profile.get('technical_background', []),
                'interests': user_profile.get('interests', []),
                'previous_queries_count': user_profile.get('query_count', 0),
                'preferred_formats': user_profile.get('preferred_formats', ['markdown']),
                'timezone': user_profile.get('timezone', 'UTC'),
                'accessibility_needs': user_profile.get('accessibility_needs', [])
            }
            
            # Add context relevance based on query requirements
            personal_requirements = [req for req in query_analysis.context_requirements if req.type == 'personal']
            if personal_requirements:
                context['personalization_required'] = True
                context['personalization_importance'] = max(req.importance for req in personal_requirements)
            
            return context
            
        except Exception as e:
            logger.error(f"Error extracting user profile context: {e}")
            return {'user_id': user_id, 'error': str(e)}
    
    async def _extract_conversation_context(self, conversation_id: str, query_analysis: QueryAnalysis) -> Dict[str, Any]:
        """Extract conversation history context"""
        try:
            # Get conversation history from cache or storage
            conversation_history = self.conversation_histories.get(conversation_id, [])
            
            # Analyze recent messages for context
            recent_messages = conversation_history[-10:] if conversation_history else []
            
            context = {
                'conversation_id': conversation_id,
                'message_count': len(conversation_history),
                'recent_topics': await self._extract_recent_topics(recent_messages),
                'conversation_flow': await self._analyze_conversation_flow(recent_messages),
                'mentioned_entities': await self._extract_mentioned_entities(recent_messages),
                'code_context': await self._extract_code_context(recent_messages),
                'unresolved_questions': await self._find_unresolved_questions(recent_messages),
                'conversation_sentiment': await self._analyze_conversation_sentiment(recent_messages),
                'last_message_timestamp': recent_messages[-1].get('timestamp') if recent_messages else None
            }
            
            # Add follow-up context if this appears to be a follow-up question
            if await self._is_followup_question(query_analysis, recent_messages):
                context['is_followup'] = True
                context['followup_context'] = await self._extract_followup_context(recent_messages)
            
            return context
            
        except Exception as e:
            logger.error(f"Error extracting conversation context: {e}")
            return {'conversation_id': conversation_id, 'error': str(e)}
    
    async def _extract_technical_context(self, query_analysis: QueryAnalysis) -> Dict[str, Any]:
        """Extract technical context for code and technical queries"""
        try:
            context = {
                'requires_code_execution': query_analysis.requires_code_execution,
                'content_type': query_analysis.content_type.value,
                'modalities': [m.value for m in query_analysis.modality_requirements],
                'technical_keywords': [],
                'programming_languages': [],
                'frameworks_mentioned': [],
                'tools_mentioned': [],
                'technical_complexity': query_analysis.complexity.value
            }
            
            # Extract technical keywords from query metadata
            if 'technical_keyword_count' in query_analysis.analysis_metadata:
                context['technical_keyword_count'] = query_analysis.analysis_metadata['technical_keyword_count']
            
            # Extract programming languages if code is involved
            if query_analysis.requires_code_execution or 'code' in query_analysis.content_type.value:
                context['programming_languages'] = await self._detect_programming_languages(query_analysis)
                context['code_complexity'] = await self._assess_code_complexity(query_analysis)
            
            # Add domain-specific technical context
            if query_analysis.domain_specific:
                context['domain'] = query_analysis.domain_specific
                context['domain_technical_requirements'] = await self._get_domain_technical_requirements(query_analysis.domain_specific)
            
            return context
            
        except Exception as e:
            logger.error(f"Error extracting technical context: {e}")
            return {'error': str(e)}
    
    async def _extract_temporal_context(self, query_analysis: QueryAnalysis) -> Dict[str, Any]:
        """Extract temporal context for time-sensitive queries"""
        try:
            context = {
                'current_timestamp': datetime.utcnow().isoformat(),
                'requires_current_data': query_analysis.requires_external_data,
                'time_sensitive': False,
                'temporal_references': []
            }
            
            # Check for temporal requirements
            temporal_requirements = [req for req in query_analysis.context_requirements if req.type == 'temporal']
            if temporal_requirements:
                context['time_sensitive'] = True
                context['temporal_importance'] = max(req.importance for req in temporal_requirements)
                
                # Extract specific temporal references
                for req in temporal_requirements:
                    if 'requires_current_data' in req.data:
                        context['requires_current_data'] = True
            
            # Add time-based context
            now = datetime.utcnow()
            context.update({
                'current_hour': now.hour,
                'current_day_of_week': now.weekday(),
                'current_month': now.month,
                'current_year': now.year,
                'is_weekend': now.weekday() >= 5,
                'is_business_hours': 9 <= now.hour <= 17
            })
            
            return context
            
        except Exception as e:
            logger.error(f"Error extracting temporal context: {e}")
            return {'current_timestamp': datetime.utcnow().isoformat(), 'error': str(e)}
    
    async def _extract_geographical_context(self, query_analysis: QueryAnalysis, additional_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract geographical context for location-based queries"""
        try:
            context = {
                'location_required': False,
                'user_location': None,
                'timezone': 'UTC',
                'locale': 'en_US'
            }
            
            # Check for geographical requirements
            geo_requirements = [req for req in query_analysis.context_requirements if req.type == 'geographical']
            if geo_requirements:
                context['location_required'] = True
                context['location_importance'] = max(req.importance for req in geo_requirements)
            
            # Extract location from additional context if provided
            if additional_context:
                if 'user_location' in additional_context:
                    context['user_location'] = additional_context['user_location']
                if 'timezone' in additional_context:
                    context['timezone'] = additional_context['timezone']
                if 'locale' in additional_context:
                    context['locale'] = additional_context['locale']
            
            return context
            
        except Exception as e:
            logger.error(f"Error extracting geographical context: {e}")
            return {'location_required': False, 'error': str(e)}
    
    async def _extract_domain_context(self, query_analysis: QueryAnalysis) -> Dict[str, Any]:
        """Extract domain-specific context"""
        try:
            context = {
                'domain': query_analysis.domain_specific,
                'domain_specific_requirements': [],
                'specialized_knowledge_required': False
            }
            
            if query_analysis.domain_specific:
                context['specialized_knowledge_required'] = True
                context['domain_specific_requirements'] = await self._get_domain_requirements(query_analysis.domain_specific)
                context['domain_complexity'] = await self._assess_domain_complexity(query_analysis.domain_specific, query_analysis)
            
            return context
            
        except Exception as e:
            logger.error(f"Error extracting domain context: {e}")
            return {'domain': None, 'error': str(e)}
    
    async def _extract_system_context(self, query_analysis: QueryAnalysis, additional_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract system state context"""
        try:
            context = {
                'system_load': 'normal',
                'available_models': [],
                'resource_constraints': {},
                'optimization_opportunities': []
            }
            
            # Extract system information from additional context
            if additional_context:
                if 'system_resources' in additional_context:
                    resources = additional_context['system_resources']
                    context['cpu_usage'] = resources.get('cpu_usage', 0)
                    context['memory_usage'] = resources.get('memory_usage', 0)
                    context['gpu_available'] = resources.get('gpu_available', False)
                    
                    # Determine system load
                    if resources.get('cpu_usage', 0) > 80 or resources.get('memory_usage', 0) > 80:
                        context['system_load'] = 'high'
                    elif resources.get('cpu_usage', 0) > 60 or resources.get('memory_usage', 0) > 60:
                        context['system_load'] = 'moderate'
                
                if 'available_models' in additional_context:
                    context['available_models'] = additional_context['available_models']
            
            # Add optimization opportunities based on query analysis
            if query_analysis.complexity == query_analysis.complexity.SIMPLE:
                context['optimization_opportunities'].append('fast_processing')
            
            if query_analysis.estimated_response_length > 2000:
                context['optimization_opportunities'].append('streaming_delivery')
            
            return context
            
        except Exception as e:
            logger.error(f"Error extracting system context: {e}")
            return {'system_load': 'unknown', 'error': str(e)}
    
    async def _create_empty_context(self, context_type: str) -> Dict[str, Any]:
        """Create empty context for missing sources"""
        return {
            'type': context_type,
            'available': False,
            'reason': 'source_not_available'
        }
    
    async def _generate_context_summary(self, *contexts) -> str:
        """Generate a summary of all extracted context"""
        try:
            summary_parts = []
            
            user_context, conversation_context, technical_context, temporal_context, geographical_context, domain_context, system_context = contexts
            
            # User context summary
            if user_context.get('user_id'):
                expertise = user_context.get('expertise_level', 'intermediate')
                summary_parts.append(f"User expertise: {expertise}")
            
            # Conversation context summary
            if conversation_context.get('conversation_id'):
                msg_count = conversation_context.get('message_count', 0)
                if msg_count > 0:
                    summary_parts.append(f"Conversation history: {msg_count} messages")
                
                if conversation_context.get('is_followup'):
                    summary_parts.append("Follow-up question detected")
            
            # Technical context summary
            if technical_context.get('requires_code_execution'):
                summary_parts.append("Code execution required")
            
            if technical_context.get('programming_languages'):
                langs = ', '.join(technical_context['programming_languages'])
                summary_parts.append(f"Languages: {langs}")
            
            # Temporal context summary
            if temporal_context.get('time_sensitive'):
                summary_parts.append("Time-sensitive query")
            
            # Geographical context summary
            if geographical_context.get('location_required'):
                summary_parts.append("Location context required")
            
            # Domain context summary
            if domain_context.get('domain'):
                summary_parts.append(f"Domain: {domain_context['domain']}")
            
            # System context summary
            system_load = system_context.get('system_load', 'normal')
            if system_load != 'normal':
                summary_parts.append(f"System load: {system_load}")
            
            return "; ".join(summary_parts) if summary_parts else "Standard query context"
            
        except Exception as e:
            logger.error(f"Error generating context summary: {e}")
            return "Context summary unavailable"
    
    async def _calculate_relevance_score(self, query_analysis: QueryAnalysis, *contexts) -> float:
        """Calculate overall context relevance score"""
        try:
            user_context, conversation_context, technical_context = contexts[:3]
            
            relevance_score = 0.5  # Base score
            
            # User context relevance
            if user_context.get('user_id') and not user_context.get('error'):
                relevance_score += 0.15
            
            # Conversation context relevance
            if conversation_context.get('conversation_id') and conversation_context.get('message_count', 0) > 0:
                relevance_score += 0.2
                
                if conversation_context.get('is_followup'):
                    relevance_score += 0.1
            
            # Technical context relevance
            if technical_context.get('requires_code_execution') or technical_context.get('programming_languages'):
                relevance_score += 0.15
            
            # Context requirements fulfillment
            fulfilled_requirements = 0
            total_requirements = len(query_analysis.context_requirements)
            
            for req in query_analysis.context_requirements:
                if req.type == 'personal' and user_context.get('user_id'):
                    fulfilled_requirements += 1
                elif req.type == 'technical' and technical_context.get('requires_code_execution'):
                    fulfilled_requirements += 1
                elif req.type == 'temporal' and any(contexts):
                    fulfilled_requirements += 1
            
            if total_requirements > 0:
                fulfillment_ratio = fulfilled_requirements / total_requirements
                relevance_score += fulfillment_ratio * 0.2
            
            return min(relevance_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating relevance score: {e}")
            return 0.5
    
    async def _create_fallback_context(self, query_analysis: QueryAnalysis) -> ProcessedContext:
        """Create fallback context when processing fails"""
        return ProcessedContext(
            user_context={'fallback': True},
            conversation_context={'fallback': True},
            technical_context={'content_type': query_analysis.content_type.value},
            temporal_context={'current_timestamp': datetime.utcnow().isoformat()},
            geographical_context={'location_required': False},
            domain_context={'domain': query_analysis.domain_specific},
            system_context={'system_load': 'unknown'},
            context_summary="Fallback context due to processing error",
            relevance_score=0.3,
            processing_metadata={'fallback': True, 'error': True}
        )
    
    # Helper methods for context extraction
    async def _extract_recent_topics(self, messages: List[Dict[str, Any]]) -> List[str]:
        """Extract recent conversation topics"""
        # Implementation would analyze message content for topics
        return []
    
    async def _analyze_conversation_flow(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze conversation flow patterns"""
        return {'flow_type': 'linear', 'topic_changes': 0}
    
    async def _extract_mentioned_entities(self, messages: List[Dict[str, Any]]) -> List[str]:
        """Extract mentioned entities from conversation"""
        return []
    
    async def _extract_code_context(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract code-related context from conversation"""
        return {'has_code': False, 'languages': []}
    
    async def _find_unresolved_questions(self, messages: List[Dict[str, Any]]) -> List[str]:
        """Find unresolved questions in conversation"""
        return []
    
    async def _analyze_conversation_sentiment(self, messages: List[Dict[str, Any]]) -> str:
        """Analyze overall conversation sentiment"""
        return 'neutral'
    
    async def _is_followup_question(self, query_analysis: QueryAnalysis, messages: List[Dict[str, Any]]) -> bool:
        """Determine if current query is a follow-up question"""
        return False
    
    async def _extract_followup_context(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract context for follow-up questions"""
        return {}
    
    async def _detect_programming_languages(self, query_analysis: QueryAnalysis) -> List[str]:
        """Detect programming languages mentioned in query"""
        return []
    
    async def _assess_code_complexity(self, query_analysis: QueryAnalysis) -> str:
        """Assess complexity of code-related query"""
        return 'moderate'
    
    async def _get_domain_technical_requirements(self, domain: str) -> List[str]:
        """Get technical requirements for specific domain"""
        return []
    
    async def _get_domain_requirements(self, domain: str) -> List[str]:
        """Get requirements for specific domain"""
        return []
    
    async def _assess_domain_complexity(self, domain: str, query_analysis: QueryAnalysis) -> str:
        """Assess complexity for domain-specific query"""
        return 'moderate'