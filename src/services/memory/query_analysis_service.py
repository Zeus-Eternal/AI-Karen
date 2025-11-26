"""
Query Analysis Service - Main Integration Service

This service integrates all query analysis and response strategy components
to provide a unified interface for intelligent response optimization.
"""

import asyncio
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass
import logging
from datetime import datetime, timedelta
import uuid

from ...internal.query_analyzer import QueryAnalyzer, QueryAnalysis
from ...internal.response_strategy_engine import ResponseStrategyEngine, ResponseStrategy
from ...internal.context_processor import ContextProcessor, ProcessedContext
from ...internal.resource_allocation_system import ResourceAllocationSystem, ResourceAllocation
from ...internal.priority_processing_system import PriorityProcessingSystem

logger = logging.getLogger(__name__)


@dataclass
class QueryAnalysisResult:
    """Complete query analysis result with all components"""
    query_id: str
    query_analysis: QueryAnalysis
    response_strategy: ResponseStrategy
    processed_context: ProcessedContext
    resource_allocation: Optional[ResourceAllocation]
    task_id: Optional[str]
    analysis_metadata: Dict[str, Any]
    created_at: datetime


class QueryAnalysisService:
    """
    Main service that orchestrates query analysis, response strategy determination,
    context processing, resource allocation, and priority-based processing.
    """
    
    def __init__(self, max_concurrent_tasks: int = 5):
        self.query_analyzer = QueryAnalyzer()
        self.response_strategy_engine = ResponseStrategyEngine()
        self.context_processor = ContextProcessor()
        self.resource_allocation_system = ResourceAllocationSystem()
        self.priority_processing_system = PriorityProcessingSystem(max_concurrent_tasks)
        
        self.analysis_cache = {}
        self.active_analyses = {}
        
        logger.info("Query Analysis Service initialized")
    
    async def analyze_query_comprehensive(
        self,
        query: str,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        available_models: Optional[List[Dict[str, Any]]] = None,
        system_resources: Optional[Dict[str, float]] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> QueryAnalysisResult:
        """
        Perform comprehensive query analysis including all optimization components
        
        Args:
            query: The user query to analyze
            user_id: Optional user identifier for personalization
            conversation_id: Optional conversation identifier for history
            available_models: Optional list of available models
            system_resources: Optional current system resource state
            additional_context: Optional additional context information
            
        Returns:
            QueryAnalysisResult: Complete analysis results
        """
        try:
            query_id = str(uuid.uuid4())
            start_time = datetime.utcnow()
            
            logger.info(f"Starting comprehensive analysis for query {query_id}")
            
            # Step 1: Analyze the query
            query_analysis = await self.query_analyzer.analyze_query(
                query=query,
                user_context=additional_context
            )
            
            # Step 2: Process context concurrently with strategy determination
            context_task = self.context_processor.process_context(
                query_analysis=query_analysis,
                user_id=user_id,
                conversation_id=conversation_id,
                additional_context=additional_context
            )
            
            strategy_task = self.response_strategy_engine.determine_response_strategy(
                query_analysis=query_analysis,
                available_models=available_models or [],
                system_resources=system_resources
            )
            
            # Wait for both to complete
            processed_context, response_strategy = await asyncio.gather(
                context_task, strategy_task
            )
            
            # Step 3: Allocate resources based on strategy
            resource_allocation = await self.resource_allocation_system.allocate_resources(
                query_analysis=query_analysis,
                response_strategy=response_strategy,
                query_id=query_id
            )
            
            # Step 4: Create analysis metadata
            analysis_metadata = {
                'analysis_duration_ms': (datetime.utcnow() - start_time).total_seconds() * 1000,
                'components_analyzed': ['query', 'context', 'strategy', 'resources'],
                'optimization_opportunities': self._identify_optimization_opportunities(
                    query_analysis, response_strategy, processed_context
                ),
                'performance_predictions': self._predict_performance(
                    query_analysis, response_strategy, resource_allocation
                ),
                'recommendations': await self._generate_recommendations(
                    query_analysis, response_strategy, processed_context
                )
            }
            
            # Create comprehensive result
            result = QueryAnalysisResult(
                query_id=query_id,
                query_analysis=query_analysis,
                response_strategy=response_strategy,
                processed_context=processed_context,
                resource_allocation=resource_allocation,
                task_id=None,  # Will be set if submitted for processing
                analysis_metadata=analysis_metadata,
                created_at=start_time
            )
            
            # Cache the result
            self.analysis_cache[query_id] = result
            
            logger.info(f"Comprehensive analysis completed for query {query_id} in {analysis_metadata['analysis_duration_ms']:.1f}ms")
            return result
            
        except Exception as e:
            logger.error(f"Error in comprehensive query analysis: {e}")
            raise
    
    async def submit_for_processing(
        self,
        analysis_result: QueryAnalysisResult,
        processing_function: Callable,
        callback: Optional[Callable] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Submit analyzed query for priority-based processing
        
        Args:
            analysis_result: Complete analysis result
            processing_function: Function to execute for processing
            callback: Optional callback for completion
            metadata: Optional additional metadata
            
        Returns:
            str: Task ID for tracking
        """
        try:
            # Prepare metadata
            task_metadata = {
                'query_id': analysis_result.query_id,
                'analysis_timestamp': analysis_result.created_at.isoformat(),
                'complexity': analysis_result.query_analysis.complexity.value,
                'priority': analysis_result.query_analysis.processing_priority.value,
                'estimated_time': analysis_result.response_strategy.estimated_generation_time
            }
            
            if metadata:
                task_metadata.update(metadata)
            
            # Submit to priority processing system
            task_id = await self.priority_processing_system.submit_task(
                query_analysis=analysis_result.query_analysis,
                response_strategy=analysis_result.response_strategy,
                processing_function=processing_function,
                resource_allocation=analysis_result.resource_allocation,
                callback=callback,
                metadata=task_metadata
            )
            
            # Update analysis result with task ID
            analysis_result.task_id = task_id
            self.active_analyses[task_id] = analysis_result
            
            logger.info(f"Query {analysis_result.query_id} submitted for processing as task {task_id}")
            return task_id
            
        except Exception as e:
            logger.error(f"Error submitting query for processing: {e}")
            raise
    
    async def analyze_and_process(
        self,
        query: str,
        processing_function: Callable,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        available_models: Optional[List[Dict[str, Any]]] = None,
        system_resources: Optional[Dict[str, float]] = None,
        additional_context: Optional[Dict[str, Any]] = None,
        callback: Optional[Callable] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[QueryAnalysisResult, str]:
        """
        Convenience method to analyze query and submit for processing in one call
        
        Returns:
            Tuple[QueryAnalysisResult, str]: Analysis result and task ID
        """
        try:
            # Perform comprehensive analysis
            analysis_result = await self.analyze_query_comprehensive(
                query=query,
                user_id=user_id,
                conversation_id=conversation_id,
                available_models=available_models,
                system_resources=system_resources,
                additional_context=additional_context
            )
            
            # Submit for processing
            task_id = await self.submit_for_processing(
                analysis_result=analysis_result,
                processing_function=processing_function,
                callback=callback,
                metadata=metadata
            )
            
            return analysis_result, task_id
            
        except Exception as e:
            logger.error(f"Error in analyze and process: {e}")
            raise
    
    def _identify_optimization_opportunities(
        self,
        query_analysis: QueryAnalysis,
        response_strategy: ResponseStrategy,
        processed_context: ProcessedContext
    ) -> List[str]:
        """Identify optimization opportunities based on analysis"""
        opportunities = []
        
        try:
            # Cache opportunities
            if processed_context.relevance_score > 0.8:
                opportunities.append("high_cache_potential")
            
            # Streaming opportunities
            if query_analysis.estimated_response_length > 1500:
                opportunities.append("streaming_beneficial")
            
            # Resource optimization opportunities
            if response_strategy.resource_allocation.cpu_limit < 3.0:
                opportunities.append("low_resource_usage")
            
            # Content optimization opportunities
            if query_analysis.complexity == query_analysis.complexity.SIMPLE:
                opportunities.append("content_compression_beneficial")
            
            # GPU acceleration opportunities
            if query_analysis.content_type.value in ['code', 'technical']:
                opportunities.append("gpu_acceleration_beneficial")
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error identifying optimization opportunities: {e}")
            return []
    
    def _predict_performance(
        self,
        query_analysis: QueryAnalysis,
        response_strategy: ResponseStrategy,
        resource_allocation: Optional[ResourceAllocation]
    ) -> Dict[str, Any]:
        """Predict performance metrics for the query processing"""
        try:
            predictions = {
                'estimated_response_time': response_strategy.estimated_generation_time,
                'estimated_cpu_usage': response_strategy.resource_allocation.cpu_limit,
                'estimated_memory_usage': response_strategy.resource_allocation.memory_limit // (1024 * 1024),
                'cache_hit_probability': 0.3,  # Default
                'streaming_recommended': response_strategy.streaming_enabled,
                'optimization_impact': 'medium'
            }
            
            # Adjust cache hit probability based on query characteristics
            if query_analysis.content_type.value in ['technical', 'code']:
                predictions['cache_hit_probability'] = 0.6
            elif query_analysis.requires_external_data:
                predictions['cache_hit_probability'] = 0.1
            
            # Predict optimization impact
            optimization_count = len(response_strategy.optimizations)
            if optimization_count >= 4:
                predictions['optimization_impact'] = 'high'
            elif optimization_count >= 2:
                predictions['optimization_impact'] = 'medium'
            else:
                predictions['optimization_impact'] = 'low'
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error predicting performance: {e}")
            return {'error': str(e)}
    
    async def _generate_recommendations(
        self,
        query_analysis: QueryAnalysis,
        response_strategy: ResponseStrategy,
        processed_context: ProcessedContext
    ) -> List[Dict[str, str]]:
        """Generate recommendations for optimization"""
        try:
            recommendations = []
            
            # Resource optimization recommendations
            if response_strategy.resource_allocation.cpu_limit > 4.0:
                recommendations.append({
                    'type': 'resource_optimization',
                    'recommendation': 'Consider using streaming delivery to reduce CPU usage',
                    'impact': 'medium'
                })
            
            # Caching recommendations
            if processed_context.relevance_score > 0.7 and not query_analysis.requires_external_data:
                recommendations.append({
                    'type': 'caching',
                    'recommendation': 'Enable aggressive caching for this query type',
                    'impact': 'high'
                })
            
            # Content optimization recommendations
            if query_analysis.estimated_response_length > 2000:
                recommendations.append({
                    'type': 'content_optimization',
                    'recommendation': 'Use progressive delivery for better user experience',
                    'impact': 'high'
                })
            
            # Model selection recommendations
            if query_analysis.complexity == query_analysis.complexity.SIMPLE:
                recommendations.append({
                    'type': 'model_selection',
                    'recommendation': 'Consider using a faster, smaller model for simple queries',
                    'impact': 'medium'
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []
    
    async def get_analysis_status(self, query_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a query analysis"""
        try:
            # Check cache first
            if query_id in self.analysis_cache:
                result = self.analysis_cache[query_id]
                status = {
                    'query_id': query_id,
                    'status': 'completed',
                    'created_at': result.created_at.isoformat(),
                    'analysis_duration_ms': result.analysis_metadata.get('analysis_duration_ms'),
                    'task_id': result.task_id
                }
                
                # If submitted for processing, get task status
                if result.task_id:
                    task_status = await self.priority_processing_system.get_task_status(result.task_id)
                    if task_status:
                        status['processing_status'] = task_status['status']
                        status['processing_time'] = task_status.get('processing_time')
                
                return status
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting analysis status: {e}")
            return None
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics"""
        try:
            # Get metrics from all components
            resource_stats = await self.resource_allocation_system.get_resource_statistics()
            queue_status = await self.priority_processing_system.get_queue_status()
            
            return {
                'resource_allocation': resource_stats,
                'processing_queues': queue_status,
                'analysis_cache_size': len(self.analysis_cache),
                'active_analyses': len(self.active_analyses),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {'error': str(e)}
    
    async def optimize_system_performance(self) -> Dict[str, Any]:
        """Optimize overall system performance"""
        try:
            optimizations = []
            
            # Optimize resource allocations
            resource_optimizations = await self.resource_allocation_system.optimize_allocations()
            optimizations.extend(resource_optimizations.get('optimizations_applied', []))
            
            # Clean up old cache entries
            cache_cleaned = self._cleanup_analysis_cache()
            if cache_cleaned > 0:
                optimizations.append(f"Cleaned up {cache_cleaned} old cache entries")
            
            return {
                'optimizations_applied': optimizations,
                'optimization_count': len(optimizations),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error optimizing system performance: {e}")
            return {'error': str(e)}
    
    def _cleanup_analysis_cache(self) -> int:
        """Clean up old analysis cache entries"""
        try:
            # Remove entries older than 1 hour
            cutoff_time = datetime.utcnow() - timedelta(hours=1)
            old_entries = [
                query_id for query_id, result in self.analysis_cache.items()
                if result.created_at < cutoff_time
            ]
            
            for query_id in old_entries:
                del self.analysis_cache[query_id]
            
            return len(old_entries)
            
        except Exception as e:
            logger.error(f"Error cleaning up analysis cache: {e}")
            return 0
    
    async def shutdown(self) -> None:
        """Shutdown the service gracefully"""
        try:
            logger.info("Shutting down Query Analysis Service...")
            
            # Shutdown priority processing system
            await self.priority_processing_system.shutdown()
            
            # Stop resource monitoring
            self.resource_allocation_system.stop_monitoring()
            
            logger.info("Query Analysis Service shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during service shutdown: {e}")
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        if hasattr(self, 'priority_processing_system'):
            asyncio.create_task(self.shutdown())