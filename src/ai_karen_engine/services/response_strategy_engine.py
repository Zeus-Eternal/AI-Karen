"""
Response Strategy Engine for Intelligent Response Optimization

This module determines optimal response strategies based on query analysis,
available models, and system resources to deliver the most efficient and
relevant responses.
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime

from .query_analyzer import QueryAnalysis, ComplexityLevel, ContentType, ExpertiseLevel, Priority, ModalityType

logger = logging.getLogger(__name__)


class ResponseFormat(Enum):
    """Response format types"""
    PLAIN_TEXT = "plain_text"
    MARKDOWN = "markdown"
    CODE_BLOCK = "code_block"
    STRUCTURED_LIST = "structured_list"
    TABLE = "table"
    MIXED = "mixed"


class ProcessingMode(Enum):
    """Processing modes for different response strategies"""
    FAST = "fast"
    BALANCED = "balanced"
    COMPREHENSIVE = "comprehensive"
    STREAMING = "streaming"


class OptimizationType(Enum):
    """Types of optimizations to apply"""
    CONTENT_COMPRESSION = "content_compression"
    PROGRESSIVE_DELIVERY = "progressive_delivery"
    CACHE_UTILIZATION = "cache_utilization"
    RESOURCE_OPTIMIZATION = "resource_optimization"
    FORMAT_OPTIMIZATION = "format_optimization"


@dataclass
class ModelRequirement:
    """Requirements for model selection"""
    modalities: List[ModalityType]
    min_capability_score: float
    preferred_types: List[str]
    max_resource_usage: Dict[str, float]
    fallback_options: List[str]


@dataclass
class ResourceAllocation:
    """Resource allocation plan for response generation"""
    cpu_limit: float
    memory_limit: int
    gpu_allocation: Optional[float]
    timeout_seconds: int
    priority_level: int
    concurrent_limit: int


@dataclass
class ResponseStrategy:
    """Comprehensive response strategy configuration"""
    processing_mode: ProcessingMode
    response_format: ResponseFormat
    model_requirements: ModelRequirement
    resource_allocation: ResourceAllocation
    optimizations: List[OptimizationType]
    content_depth: str
    streaming_enabled: bool
    cache_strategy: str
    estimated_generation_time: float
    confidence_score: float
    strategy_metadata: Dict[str, Any]


class ResponseStrategyEngine:
    """
    Engine that determines optimal response strategies based on query analysis,
    available models, and system resources.
    """
    
    def __init__(self):
        self.strategy_cache = {}
        self.model_capabilities = {}
        self.resource_limits = self._load_resource_limits()
        self.optimization_rules = self._load_optimization_rules()
        
    def _load_resource_limits(self) -> Dict[str, Dict[str, float]]:
        """Load resource limits for different processing modes"""
        return {
            'fast': {
                'cpu_limit': 2.0,  # 2% CPU per response
                'memory_limit': 100 * 1024 * 1024,  # 100MB
                'timeout_seconds': 5,
                'gpu_allocation': 0.1
            },
            'balanced': {
                'cpu_limit': 5.0,  # 5% CPU per response (requirement)
                'memory_limit': 250 * 1024 * 1024,  # 250MB
                'timeout_seconds': 15,
                'gpu_allocation': 0.3
            },
            'comprehensive': {
                'cpu_limit': 8.0,  # 8% CPU for complex queries
                'memory_limit': 500 * 1024 * 1024,  # 500MB
                'timeout_seconds': 30,
                'gpu_allocation': 0.5
            }
        }
    
    def _load_optimization_rules(self) -> Dict[str, List[OptimizationType]]:
        """Load optimization rules for different scenarios"""
        return {
            'simple_text': [
                OptimizationType.CONTENT_COMPRESSION,
                OptimizationType.CACHE_UTILIZATION
            ],
            'complex_technical': [
                OptimizationType.PROGRESSIVE_DELIVERY,
                OptimizationType.RESOURCE_OPTIMIZATION,
                OptimizationType.FORMAT_OPTIMIZATION
            ],
            'code_generation': [
                OptimizationType.FORMAT_OPTIMIZATION,
                OptimizationType.CACHE_UTILIZATION,
                OptimizationType.RESOURCE_OPTIMIZATION
            ],
            'creative_content': [
                OptimizationType.CONTENT_COMPRESSION,
                OptimizationType.PROGRESSIVE_DELIVERY
            ]
        }
    
    async def determine_response_strategy(
        self, 
        query_analysis: QueryAnalysis, 
        available_models: List[Dict[str, Any]],
        system_resources: Optional[Dict[str, float]] = None
    ) -> ResponseStrategy:
        """
        Determine optimal response strategy based on query analysis and available resources
        
        Args:
            query_analysis: Comprehensive query analysis results
            available_models: List of available models with capabilities
            system_resources: Current system resource availability
            
        Returns:
            ResponseStrategy: Optimal strategy configuration
        """
        try:
            # Determine processing mode based on complexity and priority
            processing_mode = await self._determine_processing_mode(query_analysis, system_resources)
            
            # Determine response format based on content type
            response_format = await self._determine_response_format(query_analysis)
            
            # Determine model requirements
            model_requirements = await self._determine_model_requirements(query_analysis, available_models)
            
            # Allocate resources based on processing mode and priority
            resource_allocation = await self._allocate_resources(processing_mode, query_analysis, system_resources)
            
            # Select optimizations based on query characteristics
            optimizations = await self._select_optimizations(query_analysis, processing_mode)
            
            # Determine content depth based on expertise level
            content_depth = await self._determine_content_depth(query_analysis)
            
            # Determine if streaming should be enabled
            streaming_enabled = await self._should_enable_streaming(query_analysis, processing_mode)
            
            # Determine cache strategy
            cache_strategy = await self._determine_cache_strategy(query_analysis)
            
            # Estimate generation time
            estimated_time = await self._estimate_generation_time(query_analysis, processing_mode, available_models)
            
            # Calculate strategy confidence
            confidence = await self._calculate_strategy_confidence(query_analysis, available_models)
            
            # Create strategy metadata
            metadata = {
                'created_at': datetime.utcnow().isoformat(),
                'query_complexity': query_analysis.complexity.value,
                'content_type': query_analysis.content_type.value,
                'user_expertise': query_analysis.user_expertise_level.value,
                'priority': query_analysis.processing_priority.value,
                'modalities': [m.value for m in query_analysis.modality_requirements],
                'requires_code_execution': query_analysis.requires_code_execution,
                'requires_external_data': query_analysis.requires_external_data
            }
            
            return ResponseStrategy(
                processing_mode=processing_mode,
                response_format=response_format,
                model_requirements=model_requirements,
                resource_allocation=resource_allocation,
                optimizations=optimizations,
                content_depth=content_depth,
                streaming_enabled=streaming_enabled,
                cache_strategy=cache_strategy,
                estimated_generation_time=estimated_time,
                confidence_score=confidence,
                strategy_metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error determining response strategy: {e}")
            return await self._create_fallback_strategy(query_analysis)
    
    async def _determine_processing_mode(
        self, 
        query_analysis: QueryAnalysis, 
        system_resources: Optional[Dict[str, float]]
    ) -> ProcessingMode:
        """Determine optimal processing mode"""
        try:
            # High priority queries get faster processing
            if query_analysis.processing_priority in [Priority.URGENT, Priority.HIGH]:
                return ProcessingMode.FAST
            
            # Simple queries can use fast mode
            if query_analysis.complexity == ComplexityLevel.SIMPLE:
                return ProcessingMode.FAST
            
            # Complex queries need comprehensive processing
            if query_analysis.complexity == ComplexityLevel.COMPLEX:
                # Check if we have resources for comprehensive processing
                if system_resources and system_resources.get('cpu_usage', 0) > 80:
                    return ProcessingMode.BALANCED  # Fallback to balanced
                return ProcessingMode.COMPREHENSIVE
            
            # Long responses benefit from streaming
            if query_analysis.estimated_response_length > 2000:
                return ProcessingMode.STREAMING
            
            return ProcessingMode.BALANCED
            
        except Exception as e:
            logger.error(f"Error determining processing mode: {e}")
            return ProcessingMode.BALANCED
    
    async def _determine_response_format(self, query_analysis: QueryAnalysis) -> ResponseFormat:
        """Determine optimal response format"""
        try:
            if query_analysis.content_type == ContentType.CODE:
                return ResponseFormat.CODE_BLOCK
            elif query_analysis.content_type == ContentType.MIXED:
                return ResponseFormat.MIXED
            elif query_analysis.content_type == ContentType.TECHNICAL:
                return ResponseFormat.STRUCTURED_LIST
            elif 'compare' in query_analysis.analysis_metadata.get('indicators', []):
                return ResponseFormat.TABLE
            else:
                return ResponseFormat.MARKDOWN
                
        except Exception as e:
            logger.error(f"Error determining response format: {e}")
            return ResponseFormat.MARKDOWN
    
    async def _determine_model_requirements(
        self, 
        query_analysis: QueryAnalysis, 
        available_models: List[Dict[str, Any]]
    ) -> ModelRequirement:
        """Determine model requirements based on query analysis"""
        try:
            # Base requirements from query analysis
            modalities = query_analysis.modality_requirements
            
            # Determine minimum capability score based on complexity
            min_capability = {
                ComplexityLevel.SIMPLE: 0.6,
                ComplexityLevel.MODERATE: 0.7,
                ComplexityLevel.COMPLEX: 0.8
            }.get(query_analysis.complexity, 0.7)
            
            # Preferred model types based on content type
            preferred_types = []
            if query_analysis.content_type == ContentType.CODE:
                preferred_types = ['code-specialized', 'programming', 'technical']
            elif query_analysis.content_type == ContentType.CREATIVE:
                preferred_types = ['creative', 'language', 'general']
            elif query_analysis.content_type == ContentType.TECHNICAL:
                preferred_types = ['technical', 'analytical', 'reasoning']
            else:
                preferred_types = ['general', 'chat', 'conversational']
            
            # Resource usage limits based on processing mode
            max_resource_usage = {
                'cpu_percent': 5.0,  # Stay under 5% CPU requirement
                'memory_mb': 250,
                'gpu_percent': 30.0
            }
            
            # Fallback options
            fallback_options = ['general', 'chat', 'default']
            
            return ModelRequirement(
                modalities=modalities,
                min_capability_score=min_capability,
                preferred_types=preferred_types,
                max_resource_usage=max_resource_usage,
                fallback_options=fallback_options
            )
            
        except Exception as e:
            logger.error(f"Error determining model requirements: {e}")
            return ModelRequirement(
                modalities=[ModalityType.TEXT],
                min_capability_score=0.6,
                preferred_types=['general'],
                max_resource_usage={'cpu_percent': 5.0, 'memory_mb': 250},
                fallback_options=['default']
            )
    
    async def _allocate_resources(
        self, 
        processing_mode: ProcessingMode, 
        query_analysis: QueryAnalysis,
        system_resources: Optional[Dict[str, float]]
    ) -> ResourceAllocation:
        """Allocate resources based on processing mode and system state"""
        try:
            base_limits = self.resource_limits[processing_mode.value]
            
            # Adjust based on priority
            priority_multiplier = {
                Priority.URGENT: 1.5,
                Priority.HIGH: 1.2,
                Priority.NORMAL: 1.0,
                Priority.LOW: 0.8
            }.get(query_analysis.processing_priority, 1.0)
            
            # Adjust based on system resources
            resource_multiplier = 1.0
            if system_resources:
                cpu_usage = system_resources.get('cpu_usage', 0)
                memory_usage = system_resources.get('memory_usage', 0)
                
                # Reduce allocation if system is under pressure
                if cpu_usage > 80 or memory_usage > 80:
                    resource_multiplier = 0.7
                elif cpu_usage > 60 or memory_usage > 60:
                    resource_multiplier = 0.85
            
            # Calculate final allocation
            cpu_limit = min(base_limits['cpu_limit'] * priority_multiplier * resource_multiplier, 5.0)  # Never exceed 5%
            memory_limit = int(base_limits['memory_limit'] * priority_multiplier * resource_multiplier)
            gpu_allocation = base_limits.get('gpu_allocation', 0) * resource_multiplier if system_resources and system_resources.get('gpu_available') else None
            timeout = int(base_limits['timeout_seconds'] * priority_multiplier)
            
            # Priority level for scheduling
            priority_level = {
                Priority.URGENT: 4,
                Priority.HIGH: 3,
                Priority.NORMAL: 2,
                Priority.LOW: 1
            }.get(query_analysis.processing_priority, 2)
            
            # Concurrent processing limit
            concurrent_limit = 3 if processing_mode == ProcessingMode.FAST else 2
            
            return ResourceAllocation(
                cpu_limit=cpu_limit,
                memory_limit=memory_limit,
                gpu_allocation=gpu_allocation,
                timeout_seconds=timeout,
                priority_level=priority_level,
                concurrent_limit=concurrent_limit
            )
            
        except Exception as e:
            logger.error(f"Error allocating resources: {e}")
            return ResourceAllocation(
                cpu_limit=5.0,
                memory_limit=250 * 1024 * 1024,
                gpu_allocation=None,
                timeout_seconds=15,
                priority_level=2,
                concurrent_limit=2
            )
    
    async def _select_optimizations(
        self, 
        query_analysis: QueryAnalysis, 
        processing_mode: ProcessingMode
    ) -> List[OptimizationType]:
        """Select appropriate optimizations based on query characteristics"""
        try:
            optimizations = []
            
            # Base optimizations by content type
            if query_analysis.content_type == ContentType.CODE:
                optimizations.extend(self.optimization_rules['code_generation'])
            elif query_analysis.content_type == ContentType.CREATIVE:
                optimizations.extend(self.optimization_rules['creative_content'])
            elif query_analysis.content_type == ContentType.TECHNICAL:
                optimizations.extend(self.optimization_rules['complex_technical'])
            else:
                optimizations.extend(self.optimization_rules['simple_text'])
            
            # Add optimizations based on processing mode
            if processing_mode == ProcessingMode.STREAMING:
                optimizations.append(OptimizationType.PROGRESSIVE_DELIVERY)
            
            if processing_mode == ProcessingMode.FAST:
                optimizations.append(OptimizationType.CACHE_UTILIZATION)
                optimizations.append(OptimizationType.RESOURCE_OPTIMIZATION)
            
            # Add optimizations based on complexity
            if query_analysis.complexity == ComplexityLevel.COMPLEX:
                optimizations.append(OptimizationType.PROGRESSIVE_DELIVERY)
                optimizations.append(OptimizationType.RESOURCE_OPTIMIZATION)
            
            # Add optimizations based on response length
            if query_analysis.estimated_response_length > 1500:
                optimizations.append(OptimizationType.PROGRESSIVE_DELIVERY)
                optimizations.append(OptimizationType.CONTENT_COMPRESSION)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_optimizations = []
            for opt in optimizations:
                if opt not in seen:
                    seen.add(opt)
                    unique_optimizations.append(opt)
            
            return unique_optimizations
            
        except Exception as e:
            logger.error(f"Error selecting optimizations: {e}")
            return [OptimizationType.RESOURCE_OPTIMIZATION, OptimizationType.CACHE_UTILIZATION]
    
    async def _determine_content_depth(self, query_analysis: QueryAnalysis) -> str:
        """Determine appropriate content depth based on user expertise"""
        try:
            depth_mapping = {
                ExpertiseLevel.BEGINNER: 'basic',
                ExpertiseLevel.INTERMEDIATE: 'moderate',
                ExpertiseLevel.ADVANCED: 'detailed',
                ExpertiseLevel.EXPERT: 'comprehensive'
            }
            
            base_depth = depth_mapping.get(query_analysis.user_expertise_level, 'moderate')
            
            # Adjust based on complexity
            if query_analysis.complexity == ComplexityLevel.SIMPLE and base_depth == 'comprehensive':
                return 'detailed'  # Don't over-explain simple concepts
            elif query_analysis.complexity == ComplexityLevel.COMPLEX and base_depth == 'basic':
                return 'moderate'  # Provide more detail for complex topics
            
            return base_depth
            
        except Exception as e:
            logger.error(f"Error determining content depth: {e}")
            return 'moderate'
    
    async def _should_enable_streaming(self, query_analysis: QueryAnalysis, processing_mode: ProcessingMode) -> bool:
        """Determine if streaming should be enabled"""
        try:
            # Always enable for streaming mode
            if processing_mode == ProcessingMode.STREAMING:
                return True
            
            # Enable for long responses
            if query_analysis.estimated_response_length > 1500:
                return True
            
            # Enable for complex queries
            if query_analysis.complexity == ComplexityLevel.COMPLEX:
                return True
            
            # Enable for high priority queries to show immediate progress
            if query_analysis.processing_priority in [Priority.URGENT, Priority.HIGH]:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error determining streaming: {e}")
            return False
    
    async def _determine_cache_strategy(self, query_analysis: QueryAnalysis) -> str:
        """Determine appropriate cache strategy"""
        try:
            # Time-sensitive queries should not use cache
            if query_analysis.requires_external_data:
                return 'no_cache'
            
            # Personal queries should use user-specific cache
            personal_context = any(req.type == 'personal' for req in query_analysis.context_requirements)
            if personal_context:
                return 'user_cache'
            
            # Technical queries can use aggressive caching
            if query_analysis.content_type in [ContentType.TECHNICAL, ContentType.CODE]:
                return 'aggressive_cache'
            
            # Default to standard caching
            return 'standard_cache'
            
        except Exception as e:
            logger.error(f"Error determining cache strategy: {e}")
            return 'standard_cache'
    
    async def _estimate_generation_time(
        self, 
        query_analysis: QueryAnalysis, 
        processing_mode: ProcessingMode,
        available_models: List[Dict[str, Any]]
    ) -> float:
        """Estimate response generation time"""
        try:
            # Base time by complexity
            base_times = {
                ComplexityLevel.SIMPLE: 2.0,
                ComplexityLevel.MODERATE: 5.0,
                ComplexityLevel.COMPLEX: 10.0
            }
            
            base_time = base_times.get(query_analysis.complexity, 5.0)
            
            # Adjust by processing mode
            mode_multipliers = {
                ProcessingMode.FAST: 0.6,
                ProcessingMode.BALANCED: 1.0,
                ProcessingMode.COMPREHENSIVE: 1.8,
                ProcessingMode.STREAMING: 1.2
            }
            
            time_estimate = base_time * mode_multipliers.get(processing_mode, 1.0)
            
            # Adjust by content type
            if query_analysis.content_type == ContentType.CODE:
                time_estimate *= 1.3
            elif query_analysis.content_type == ContentType.CREATIVE:
                time_estimate *= 1.5
            
            # Adjust by response length
            length_factor = min(query_analysis.estimated_response_length / 1000, 3.0)
            time_estimate *= length_factor
            
            return max(time_estimate, 1.0)  # Minimum 1 second
            
        except Exception as e:
            logger.error(f"Error estimating generation time: {e}")
            return 5.0
    
    async def _calculate_strategy_confidence(
        self, 
        query_analysis: QueryAnalysis, 
        available_models: List[Dict[str, Any]]
    ) -> float:
        """Calculate confidence in the strategy selection"""
        try:
            confidence = query_analysis.confidence_score  # Start with query analysis confidence
            
            # Boost confidence if we have good model matches
            if available_models:
                confidence += 0.1
            
            # Boost confidence for clear content types
            if query_analysis.content_type in [ContentType.CODE, ContentType.TECHNICAL]:
                confidence += 0.1
            
            # Reduce confidence for complex multimodal queries
            if len(query_analysis.modality_requirements) > 2:
                confidence -= 0.1
            
            # Boost confidence for standard priorities
            if query_analysis.processing_priority == Priority.NORMAL:
                confidence += 0.05
            
            return max(min(confidence, 1.0), 0.3)  # Clamp between 0.3 and 1.0
            
        except Exception as e:
            logger.error(f"Error calculating strategy confidence: {e}")
            return 0.5
    
    async def _create_fallback_strategy(self, query_analysis: QueryAnalysis) -> ResponseStrategy:
        """Create a safe fallback strategy when errors occur"""
        return ResponseStrategy(
            processing_mode=ProcessingMode.BALANCED,
            response_format=ResponseFormat.MARKDOWN,
            model_requirements=ModelRequirement(
                modalities=[ModalityType.TEXT],
                min_capability_score=0.6,
                preferred_types=['general'],
                max_resource_usage={'cpu_percent': 5.0, 'memory_mb': 250},
                fallback_options=['default']
            ),
            resource_allocation=ResourceAllocation(
                cpu_limit=5.0,
                memory_limit=250 * 1024 * 1024,
                gpu_allocation=None,
                timeout_seconds=15,
                priority_level=2,
                concurrent_limit=2
            ),
            optimizations=[OptimizationType.RESOURCE_OPTIMIZATION],
            content_depth='moderate',
            streaming_enabled=False,
            cache_strategy='standard_cache',
            estimated_generation_time=5.0,
            confidence_score=0.3,
            strategy_metadata={'fallback': True, 'error_recovery': True}
        )
    
    async def update_model_capabilities(self, model_id: str, capabilities: Dict[str, Any]) -> None:
        """Update model capabilities for better strategy determination"""
        try:
            self.model_capabilities[model_id] = capabilities
            logger.info(f"Updated capabilities for model {model_id}")
        except Exception as e:
            logger.error(f"Error updating model capabilities: {e}")
    
    async def get_strategy_recommendations(
        self, 
        query_analysis: QueryAnalysis,
        available_models: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Get strategy recommendations with explanations"""
        try:
            strategy = await self.determine_response_strategy(query_analysis, available_models)
            
            recommendations = []
            
            # Processing mode recommendation
            recommendations.append({
                'type': 'processing_mode',
                'value': strategy.processing_mode.value,
                'reason': f"Selected based on complexity ({query_analysis.complexity.value}) and priority ({query_analysis.processing_priority.value})"
            })
            
            # Resource allocation recommendation
            recommendations.append({
                'type': 'resource_allocation',
                'value': f"CPU: {strategy.resource_allocation.cpu_limit}%, Memory: {strategy.resource_allocation.memory_limit // (1024*1024)}MB",
                'reason': "Optimized to stay under 5% CPU usage requirement while meeting performance needs"
            })
            
            # Optimization recommendations
            recommendations.append({
                'type': 'optimizations',
                'value': [opt.value for opt in strategy.optimizations],
                'reason': f"Selected based on content type ({query_analysis.content_type.value}) and complexity"
            })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting strategy recommendations: {e}")
            return []