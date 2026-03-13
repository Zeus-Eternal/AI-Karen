"""
Correlation Engine module for correlating agent behavior.

This module provides functionality to correlate agent behavior,
including correlation analysis, pattern matching, and relationship detection.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict

from ai_karen_engine.core.services.base import BaseService, ServiceConfig

from ..agent_safety_types import BehaviorData, CorrelationResult

logger = logging.getLogger(__name__)


class CorrelationEngine(BaseService):
    """
    Correlation Engine for correlating agent behavior.
    
    This class provides functionality to correlate agent behavior,
    including correlation analysis, pattern matching, and relationship detection.
    """
    
    def __init__(self, config: ServiceConfig):
        """Initialize the Correlation Engine."""
        super().__init__(config)
        self._initialized = False
        self._lock = asyncio.Lock()
        
        # Thread-safe data structures
        self._agent_behavior_data: Dict[str, List[BehaviorData]] = defaultdict(list)
        self._correlation_results: Dict[str, List[CorrelationResult]] = defaultdict(list)
        self._correlation_patterns: Dict[str, Dict[str, Any]] = {}
        
        # Configuration
        self._correlation_threshold = 0.7
        self._time_window_hours = 24
        self._enable_cross_agent_correlation = True
        self._enable_temporal_correlation = True
        self._enable_behavioral_correlation = True
        self._max_history_size = 1000
        self._max_correlated_agents = 10
    
    async def initialize(self) -> None:
        """Initialize the Correlation Engine."""
        if self._initialized:
            return
            
        async with self._lock:
            try:
                # Initialize correlation patterns
                await self._load_correlation_patterns()
                
                self._initialized = True
                logger.info("Correlation Engine initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Correlation Engine: {e}")
                raise RuntimeError(f"Correlation Engine initialization failed: {e}")
    
    async def _load_correlation_patterns(self) -> None:
        """Load correlation patterns."""
        # Default correlation patterns
        self._correlation_patterns = {
            "resource_usage_spikes": {
                "description": "Multiple agents experiencing resource usage spikes",
                "condition": self._check_resource_usage_spikes,
                "correlation_type": "resource"
            },
            "error_cascades": {
                "description": "Errors cascading between agents",
                "condition": self._check_error_cascades,
                "correlation_type": "error"
            },
            "temporal_patterns": {
                "description": "Agents exhibiting similar temporal patterns",
                "condition": self._check_temporal_patterns,
                "correlation_type": "temporal"
            },
            "behavioral_similarity": {
                "description": "Agents exhibiting similar behavior patterns",
                "condition": self._check_behavioral_similarity,
                "correlation_type": "behavioral"
            }
        }
        
        logger.debug(f"Loaded {len(self._correlation_patterns)} correlation patterns")
    
    async def add_behavior_data(self, behavior_data: BehaviorData) -> None:
        """
        Add behavior data for correlation analysis.
        
        Args:
            behavior_data: Behavior data to add
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            async with self._lock:
                # Add behavior data
                self._agent_behavior_data[behavior_data.agent_id].append(behavior_data)
                
                # Limit history size
                if len(self._agent_behavior_data[behavior_data.agent_id]) > self._max_history_size:
                    self._agent_behavior_data[behavior_data.agent_id] = self._agent_behavior_data[behavior_data.agent_id][-self._max_history_size:]
                
                # Perform correlation analysis
                if self._enable_cross_agent_correlation:
                    await self._analyze_cross_agent_correlations(behavior_data)
        except Exception as e:
            logger.error(f"Error adding behavior data: {e}")
    
    async def _analyze_cross_agent_correlations(self, behavior_data: BehaviorData) -> None:
        """
        Analyze correlations between agents.
        
        Args:
            behavior_data: New behavior data to analyze
        """
        try:
            # Get time window for correlation
            time_window_start = behavior_data.timestamp - timedelta(hours=self._time_window_hours)
            time_window_end = behavior_data.timestamp + timedelta(hours=self._time_window_hours)
            
            # Get agents with behavior data in time window
            correlated_agents = []
            for agent_id, agent_data in self._agent_behavior_data.items():
                if agent_id == behavior_data.agent_id:
                    continue
                
                # Check if agent has data in time window
                for data in agent_data:
                    if time_window_start <= data.timestamp <= time_window_end:
                        correlated_agents.append(agent_id)
                        break
            
            # Limit number of correlated agents
            if len(correlated_agents) > self._max_correlated_agents:
                correlated_agents = correlated_agents[:self._max_correlated_agents]
            
            # Check each correlation pattern
            for pattern_name, pattern_def in self._correlation_patterns.items():
                try:
                    condition_func = pattern_def["condition"]
                    correlation_detected, correlation_strength, confidence = await condition_func(
                        behavior_data.agent_id,
                        correlated_agents,
                        time_window_start,
                        time_window_end
                    )
                    
                    if correlation_detected and correlation_strength >= self._correlation_threshold:
                        # Create correlation result
                        correlation_result = CorrelationResult(
                            correlation_detected=True,
                            correlation_type=pattern_def["correlation_type"],
                            correlated_agents=correlated_agents,
                            correlation_strength=correlation_strength,
                            confidence=confidence,
                            description=pattern_def["description"]
                        )
                        
                        # Store correlation result
                        self._correlation_results[behavior_data.agent_id].append(correlation_result)
                        
                        # Limit history size
                        if len(self._correlation_results[behavior_data.agent_id]) > self._max_history_size:
                            self._correlation_results[behavior_data.agent_id] = self._correlation_results[behavior_data.agent_id][-self._max_history_size:]
                except Exception as e:
                    logger.error(f"Error checking correlation pattern {pattern_name}: {e}")
        except Exception as e:
            logger.error(f"Error analyzing cross-agent correlations: {e}")
    
    async def _check_resource_usage_spikes(
        self,
        agent_id: str,
        correlated_agents: List[str],
        time_window_start: datetime,
        time_window_end: datetime
    ) -> Tuple[bool, float, float]:
        """
        Check for resource usage spikes between agents.
        
        Args:
            agent_id: ID of the primary agent
            correlated_agents: List of potentially correlated agents
            time_window_start: Start of time window
            time_window_end: End of time window
            
        Returns:
            Tuple of (correlation_detected, correlation_strength, confidence)
        """
        try:
            # Get behavior data for primary agent in time window
            primary_data = [
                data for data in self._agent_behavior_data[agent_id]
                if time_window_start <= data.timestamp <= time_window_end
            ]
            
            if not primary_data:
                return False, 0.0, 0.0
            
            # Check for resource spikes in primary agent
            primary_spikes = 0
            for data in primary_data:
                for resource_name, usage in data.resource_usage.items():
                    if usage > 0.8:  # High resource usage
                        primary_spikes += 1
            
            if primary_spikes == 0:
                return False, 0.0, 0.0
            
            # Check for resource spikes in correlated agents
            correlated_spikes = 0
            total_correlated_agents = 0
            
            for correlated_agent_id in correlated_agents:
                if correlated_agent_id not in self._agent_behavior_data:
                    continue
                
                correlated_data = [
                    data for data in self._agent_behavior_data[correlated_agent_id]
                    if time_window_start <= data.timestamp <= time_window_end
                ]
                
                if not correlated_data:
                    continue
                
                total_correlated_agents += 1
                
                # Check for resource spikes
                for data in correlated_data:
                    for resource_name, usage in data.resource_usage.items():
                        if usage > 0.8:  # High resource usage
                            correlated_spikes += 1
            
            if total_correlated_agents == 0:
                return False, 0.0, 0.0
            
            # Calculate correlation strength
            correlation_strength = correlated_spikes / (primary_spikes * total_correlated_agents)
            
            # Calculate confidence based on number of correlated agents
            confidence = min(total_correlated_agents / len(correlated_agents), 1.0)
            
            return correlation_strength >= self._correlation_threshold, correlation_strength, confidence
        except Exception as e:
            logger.error(f"Error checking resource usage spikes: {e}")
            return False, 0.0, 0.0
    
    async def _check_error_cascades(
        self,
        agent_id: str,
        correlated_agents: List[str],
        time_window_start: datetime,
        time_window_end: datetime
    ) -> Tuple[bool, float, float]:
        """
        Check for error cascades between agents.
        
        Args:
            agent_id: ID of the primary agent
            correlated_agents: List of potentially correlated agents
            time_window_start: Start of time window
            time_window_end: End of time window
            
        Returns:
            Tuple of (correlation_detected, correlation_strength, confidence)
        """
        try:
            # Get behavior data for primary agent in time window
            primary_data = [
                data for data in self._agent_behavior_data[agent_id]
                if time_window_start <= data.timestamp <= time_window_end
            ]
            
            if not primary_data:
                return False, 0.0, 0.0
            
            # Check for errors in primary agent
            primary_errors = 0
            for data in primary_data:
                error_rate = data.metrics.get("error_rate", 0)
                if error_rate > 0.1:  # High error rate
                    primary_errors += 1
            
            if primary_errors == 0:
                return False, 0.0, 0.0
            
            # Check for errors in correlated agents
            correlated_errors = 0
            total_correlated_agents = 0
            
            for correlated_agent_id in correlated_agents:
                if correlated_agent_id not in self._agent_behavior_data:
                    continue
                
                correlated_data = [
                    data for data in self._agent_behavior_data[correlated_agent_id]
                    if time_window_start <= data.timestamp <= time_window_end
                ]
                
                if not correlated_data:
                    continue
                
                total_correlated_agents += 1
                
                # Check for errors
                for data in correlated_data:
                    error_rate = data.metrics.get("error_rate", 0)
                    if error_rate > 0.1:  # High error rate
                        correlated_errors += 1
            
            if total_correlated_agents == 0:
                return False, 0.0, 0.0
            
            # Calculate correlation strength
            correlation_strength = correlated_errors / (primary_errors * total_correlated_agents)
            
            # Calculate confidence based on number of correlated agents
            confidence = min(total_correlated_agents / len(correlated_agents), 1.0)
            
            return correlation_strength >= self._correlation_threshold, correlation_strength, confidence
        except Exception as e:
            logger.error(f"Error checking error cascades: {e}")
            return False, 0.0, 0.0
    
    async def _check_temporal_patterns(
        self,
        agent_id: str,
        correlated_agents: List[str],
        time_window_start: datetime,
        time_window_end: datetime
    ) -> Tuple[bool, float, float]:
        """
        Check for temporal patterns between agents.
        
        Args:
            agent_id: ID of the primary agent
            correlated_agents: List of potentially correlated agents
            time_window_start: Start of time window
            time_window_end: End of time window
            
        Returns:
            Tuple of (correlation_detected, correlation_strength, confidence)
        """
        try:
            # Get behavior data for primary agent in time window
            primary_data = [
                data for data in self._agent_behavior_data[agent_id]
                if time_window_start <= data.timestamp <= time_window_end
            ]
            
            if not primary_data:
                return False, 0.0, 0.0
            
            # Extract timestamps for primary agent
            primary_timestamps = [data.timestamp for data in primary_data]
            
            # Check for temporal patterns in correlated agents
            temporal_matches = 0
            total_correlated_agents = 0
            
            for correlated_agent_id in correlated_agents:
                if correlated_agent_id not in self._agent_behavior_data:
                    continue
                
                correlated_data = [
                    data for data in self._agent_behavior_data[correlated_agent_id]
                    if time_window_start <= data.timestamp <= time_window_end
                ]
                
                if not correlated_data:
                    continue
                
                total_correlated_agents += 1
                
                # Extract timestamps for correlated agent
                correlated_timestamps = [data.timestamp for data in correlated_data]
                
                # Check for temporal correlation
                # Simple check: similar activity patterns within time windows
                for primary_ts in primary_timestamps:
                    for correlated_ts in correlated_timestamps:
                        time_diff = abs((primary_ts - correlated_ts).total_seconds())
                        if time_diff <= 300:  # Within 5 minutes
                            temporal_matches += 1
                            break
            
            if total_correlated_agents == 0:
                return False, 0.0, 0.0
            
            # Calculate correlation strength
            max_possible_matches = len(primary_timestamps) * total_correlated_agents
            correlation_strength = temporal_matches / max_possible_matches if max_possible_matches > 0 else 0.0
            
            # Calculate confidence based on number of correlated agents
            confidence = min(total_correlated_agents / len(correlated_agents), 1.0)
            
            return correlation_strength >= self._correlation_threshold, correlation_strength, confidence
        except Exception as e:
            logger.error(f"Error checking temporal patterns: {e}")
            return False, 0.0, 0.0
    
    async def _check_behavioral_similarity(
        self,
        agent_id: str,
        correlated_agents: List[str],
        time_window_start: datetime,
        time_window_end: datetime
    ) -> Tuple[bool, float, float]:
        """
        Check for behavioral similarity between agents.
        
        Args:
            agent_id: ID of the primary agent
            correlated_agents: List of potentially correlated agents
            time_window_start: Start of time window
            time_window_end: End of time window
            
        Returns:
            Tuple of (correlation_detected, correlation_strength, confidence)
        """
        try:
            # Get behavior data for primary agent in time window
            primary_data = [
                data for data in self._agent_behavior_data[agent_id]
                if time_window_start <= data.timestamp <= time_window_end
            ]
            
            if not primary_data:
                return False, 0.0, 0.0
            
            # Calculate average metrics for primary agent
            primary_metrics = {}
            for metric_name in ["cpu_usage", "memory_usage", "response_time", "error_rate", "task_completion_rate"]:
                values = [data.metrics.get(metric_name, 0) for data in primary_data if metric_name in data.metrics]
                if values:
                    primary_metrics[metric_name] = sum(values) / len(values)
            
            # Calculate average resource usage for primary agent
            primary_resources = {}
            for resource_name in ["cpu", "memory", "disk", "network"]:
                values = [data.resource_usage.get(resource_name, 0) for data in primary_data if resource_name in data.resource_usage]
                if values:
                    primary_resources[resource_name] = sum(values) / len(values)
            
            # Check for behavioral similarity in correlated agents
            similarity_scores = []
            total_correlated_agents = 0
            
            for correlated_agent_id in correlated_agents:
                if correlated_agent_id not in self._agent_behavior_data:
                    continue
                
                correlated_data = [
                    data for data in self._agent_behavior_data[correlated_agent_id]
                    if time_window_start <= data.timestamp <= time_window_end
                ]
                
                if not correlated_data:
                    continue
                
                total_correlated_agents += 1
                
                # Calculate average metrics for correlated agent
                correlated_metrics = {}
                for metric_name in ["cpu_usage", "memory_usage", "response_time", "error_rate", "task_completion_rate"]:
                    values = [data.metrics.get(metric_name, 0) for data in correlated_data if metric_name in data.metrics]
                    if values:
                        correlated_metrics[metric_name] = sum(values) / len(values)
                
                # Calculate average resource usage for correlated agent
                correlated_resources = {}
                for resource_name in ["cpu", "memory", "disk", "network"]:
                    values = [data.resource_usage.get(resource_name, 0) for data in correlated_data if resource_name in data.resource_usage]
                    if values:
                        correlated_resources[resource_name] = sum(values) / len(values)
                
                # Calculate similarity score
                metric_similarity = 0.0
                metric_count = 0
                
                for metric_name, primary_value in primary_metrics.items():
                    if metric_name in correlated_metrics:
                        correlated_value = correlated_metrics[metric_name]
                        # Calculate normalized difference
                        if primary_value != 0 or correlated_value != 0:
                            diff = abs(primary_value - correlated_value) / max(primary_value, correlated_value, 0.01)
                            similarity = max(0, 1 - diff)
                            metric_similarity += similarity
                            metric_count += 1
                
                resource_similarity = 0.0
                resource_count = 0
                
                for resource_name, primary_value in primary_resources.items():
                    if resource_name in correlated_resources:
                        correlated_value = correlated_resources[resource_name]
                        # Calculate normalized difference
                        if primary_value != 0 or correlated_value != 0:
                            diff = abs(primary_value - correlated_value) / max(primary_value, correlated_value, 0.01)
                            similarity = max(0, 1 - diff)
                            resource_similarity += similarity
                            resource_count += 1
                
                # Calculate overall similarity
                overall_similarity = 0.0
                total_count = 0
                
                if metric_count > 0:
                    overall_similarity += metric_similarity / metric_count
                    total_count += 1
                
                if resource_count > 0:
                    overall_similarity += resource_similarity / resource_count
                    total_count += 1
                
                if total_count > 0:
                    similarity_scores.append(overall_similarity / total_count)
            
            if total_correlated_agents == 0:
                return False, 0.0, 0.0
            
            # Calculate correlation strength
            correlation_strength = sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.0
            
            # Calculate confidence based on number of correlated agents
            confidence = min(total_correlated_agents / len(correlated_agents), 1.0)
            
            return correlation_strength >= self._correlation_threshold, correlation_strength, confidence
        except Exception as e:
            logger.error(f"Error checking behavioral similarity: {e}")
            return False, 0.0, 0.0
    
    async def get_correlations(
        self,
        agent_id: str,
        correlation_type: Optional[str] = None,
        limit: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[CorrelationResult]:
        """
        Get correlations for an agent.
        
        Args:
            agent_id: ID of the agent
            correlation_type: Optional correlation type to filter by
            limit: Maximum number of entries to return
            start_time: Optional start time for filtering
            end_time: Optional end time for filtering
            
        Returns:
            List of correlation results
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            async with self._lock:
                correlations = self._correlation_results.get(agent_id, [])
                
                # Filter by correlation type
                if correlation_type:
                    correlations = [
                        c for c in correlations
                        if c.correlation_type == correlation_type
                    ]
                
                # Filter by time range
                if start_time or end_time:
                    # Note: CorrelationResult doesn't have a timestamp field in the dataclass
                    # We'll need to add one or use a different approach
                    pass
                
                # Limit number of entries
                if limit and len(correlations) > limit:
                    correlations = correlations[-limit:]
                
                return correlations
        except Exception as e:
            logger.error(f"Error getting correlations: {e}")
            return []
    
    async def get_correlated_agents(
        self,
        agent_id: str,
        correlation_type: Optional[str] = None,
        min_correlation_strength: float = 0.5
    ) -> Set[str]:
        """
        Get agents correlated with a specific agent.
        
        Args:
            agent_id: ID of the agent
            correlation_type: Optional correlation type to filter by
            min_correlation_strength: Minimum correlation strength
            
        Returns:
            Set of correlated agent IDs
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            correlations = await self.get_correlations(agent_id, correlation_type)
            
            # Filter by correlation strength
            correlations = [
                c for c in correlations
                if c.correlation_strength >= min_correlation_strength
            ]
            
            # Extract correlated agents
            correlated_agents = set()
            for correlation in correlations:
                correlated_agents.update(correlation.correlated_agents)
            
            return correlated_agents
        except Exception as e:
            logger.error(f"Error getting correlated agents: {e}")
            return set()
    
    async def clear_correlations(self, agent_id: Optional[str] = None) -> bool:
        """
        Clear correlation data.
        
        Args:
            agent_id: Optional agent ID to clear correlations for. If None, clears all correlations.
            
        Returns:
            True if clearing was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            async with self._lock:
                if agent_id:
                    self._correlation_results[agent_id].clear()
                else:
                    self._correlation_results.clear()
            
            return True
        except Exception as e:
            logger.error(f"Error clearing correlations: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check health of the Correlation Engine."""
        if not self._initialized:
            return False
            
        try:
            # Check if cross-agent correlation is enabled
            if not self._enable_cross_agent_correlation:
                return False
            
            # Check if correlation patterns are loaded
            if not self._correlation_patterns:
                return False
            
            return True
        except Exception as e:
            logger.error(f"Correlation Engine health check failed: {e}")
            return False
    
    async def start(self) -> None:
        """Start the Correlation Engine."""
        if not self._initialized:
            await self.initialize()
        
        logger.info("Correlation Engine started successfully")
    
    async def stop(self) -> None:
        """Stop the Correlation Engine."""
        if not self._initialized:
            return
        
        # Clear data structures
        async with self._lock:
            self._agent_behavior_data.clear()
            self._correlation_results.clear()
            self._correlation_patterns.clear()
        
        # Reset initialization state
        self._initialized = False
        
        logger.info("Correlation Engine stopped successfully")
