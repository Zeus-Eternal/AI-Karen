"""
Baseline Generator module for generating behavior baselines.

This module provides functionality to generate behavior baselines for agents,
including baseline calculation, storage, and comparison.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

from ai_karen_engine.core.services.base import BaseService, ServiceConfig

from ..agent_safety_types import BehaviorData, BaselineResult

logger = logging.getLogger(__name__)


class BaselineGenerator(BaseService):
    """
    Baseline Generator for generating behavior baselines.
    
    This class provides functionality to generate behavior baselines for agents,
    including baseline calculation, storage, and comparison.
    """
    
    def __init__(self, config: ServiceConfig):
        """Initialize the Baseline Generator."""
        super().__init__(config)
        self._initialized = False
        self._lock = asyncio.Lock()
        
        # Thread-safe data structures
        self._baselines: Dict[str, Dict[str, Any]] = {}
        self._baseline_history: Dict[str, List[BaselineResult]] = defaultdict(list)
        
        # Configuration
        self._baseline_window_days = 7
        self._min_data_points = 10
        self._update_interval_hours = 24
        self._deviation_threshold = 0.2
        self._enable_auto_update = True
    
    async def initialize(self) -> None:
        """Initialize the Baseline Generator."""
        if self._initialized:
            return
            
        async with self._lock:
            try:
                # Initialize baseline generation
                logger.debug("Baseline Generator initialized")
                
                self._initialized = True
                logger.info("Baseline Generator initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Baseline Generator: {e}")
                raise RuntimeError(f"Baseline Generator initialization failed: {e}")
    
    async def generate_baseline(
        self,
        agent_id: str,
        behavior_data: List[BehaviorData]
    ) -> Optional[BaselineResult]:
        """
        Generate baseline for an agent.
        
        Args:
            agent_id: ID of the agent
            behavior_data: List of behavior data to use for baseline generation
            
        Returns:
            Baseline result if successful, None otherwise
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            # Check if we have enough data
            if len(behavior_data) < self._min_data_points:
                logger.warning(f"Insufficient data for baseline generation: {len(behavior_data)} < {self._min_data_points}")
                return None
            
            # Calculate baseline metrics
            baseline_metrics = await self._calculate_baseline_metrics(behavior_data)
            
            # Create baseline ID
            baseline_id = f"baseline_{agent_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            # Create baseline result
            baseline_result = BaselineResult(
                baseline_id=baseline_id,
                deviation_score=0.0,
                is_within_threshold=True,
                threshold=self._deviation_threshold
            )
            
            # Store baseline
            async with self._lock:
                self._baselines[agent_id] = baseline_metrics
                self._baseline_history[agent_id].append(baseline_result)
                
                # Limit history size
                if len(self._baseline_history[agent_id]) > 100:
                    self._baseline_history[agent_id] = self._baseline_history[agent_id][-100:]
            
            return baseline_result
        except Exception as e:
            logger.error(f"Error generating baseline: {e}")
            return None
    
    async def _calculate_baseline_metrics(
        self,
        behavior_data: List[BehaviorData]
    ) -> Dict[str, Any]:
        """
        Calculate baseline metrics from behavior data.
        
        Args:
            behavior_data: List of behavior data to analyze
            
        Returns:
            Dictionary of baseline metrics
        """
        try:
            # Initialize metrics
            baseline_metrics = {
                "metrics": {},
                "resource_usage": {},
                "response_patterns": {},
                "interaction_patterns": {}
            }
            
            # Calculate metric averages
            metric_sums = defaultdict(float)
            metric_counts = defaultdict(int)
            
            # Calculate resource usage averages
            resource_sums = defaultdict(float)
            resource_counts = defaultdict(int)
            
            for data in behavior_data:
                # Process metrics
                for metric_name, metric_value in data.metrics.items():
                    if isinstance(metric_value, (int, float)):
                        metric_sums[metric_name] += metric_value
                        metric_counts[metric_name] += 1
                
                # Process resource usage
                for resource_name, resource_value in data.resource_usage.items():
                    if isinstance(resource_value, (int, float)):
                        resource_sums[resource_name] += resource_value
                        resource_counts[resource_name] += 1
            
            # Calculate averages
            for metric_name in metric_sums:
                baseline_metrics["metrics"][metric_name] = metric_sums[metric_name] / metric_counts[metric_name]
            
            for resource_name in resource_sums:
                baseline_metrics["resource_usage"][resource_name] = resource_sums[resource_name] / resource_counts[resource_name]
            
            # Calculate metric ranges
            metric_ranges = {}
            for metric_name in metric_sums:
                values = [data.metrics.get(metric_name, 0) for data in behavior_data if metric_name in data.metrics]
                if values:
                    metric_ranges[metric_name] = {
                        "min": min(values),
                        "max": max(values),
                        "std_dev": self._calculate_std_dev(values)
                    }
            
            baseline_metrics["metric_ranges"] = metric_ranges
            
            # Calculate resource usage ranges
            resource_ranges = {}
            for resource_name in resource_sums:
                values = [data.resource_usage.get(resource_name, 0) for data in behavior_data if resource_name in data.resource_usage]
                if values:
                    resource_ranges[resource_name] = {
                        "min": min(values),
                        "max": max(values),
                        "std_dev": self._calculate_std_dev(values)
                    }
            
            baseline_metrics["resource_ranges"] = resource_ranges
            
            return baseline_metrics
        except Exception as e:
            logger.error(f"Error calculating baseline metrics: {e}")
            return {}
    
    def _calculate_std_dev(self, values: List[float]) -> float:
        """
        Calculate standard deviation of values.
        
        Args:
            values: List of values
            
        Returns:
            Standard deviation
        """
        try:
            if not values:
                return 0.0
            
            mean = sum(values) / len(values)
            variance = sum((x - mean) ** 2 for x in values) / len(values)
            return variance ** 0.5
        except Exception as e:
            logger.error(f"Error calculating standard deviation: {e}")
            return 0.0
    
    async def compare_to_baseline(
        self,
        agent_id: str,
        behavior_data: BehaviorData
    ) -> BaselineResult:
        """
        Compare behavior data to baseline.
        
        Args:
            agent_id: ID of the agent
            behavior_data: Behavior data to compare
            
        Returns:
            Baseline comparison result
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            # Get baseline for agent
            async with self._lock:
                baseline = self._baselines.get(agent_id, {})
            
            if not baseline:
                logger.warning(f"No baseline found for agent {agent_id}")
                return BaselineResult(
                    baseline_id="none",
                    deviation_score=1.0,
                    is_within_threshold=False,
                    threshold=self._deviation_threshold
                )
            
            # Calculate deviation score
            deviation_score = await self._calculate_deviation_score(
                behavior_data, baseline
            )
            
            # Check if within threshold
            is_within_threshold = deviation_score <= self._deviation_threshold
            
            # Create baseline ID
            baseline_id = f"comparison_{agent_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            # Create baseline result
            baseline_result = BaselineResult(
                baseline_id=baseline_id,
                deviation_score=deviation_score,
                is_within_threshold=is_within_threshold,
                threshold=self._deviation_threshold
            )
            
            # Store in history
            async with self._lock:
                self._baseline_history[agent_id].append(baseline_result)
                
                # Limit history size
                if len(self._baseline_history[agent_id]) > 100:
                    self._baseline_history[agent_id] = self._baseline_history[agent_id][-100:]
            
            return baseline_result
        except Exception as e:
            logger.error(f"Error comparing to baseline: {e}")
            return BaselineResult(
                baseline_id="error",
                deviation_score=1.0,
                is_within_threshold=False,
                threshold=self._deviation_threshold
            )
    
    async def _calculate_deviation_score(
        self,
        behavior_data: BehaviorData,
        baseline: Dict[str, Any]
    ) -> float:
        """
        Calculate deviation score from baseline.
        
        Args:
            behavior_data: Behavior data to compare
            baseline: Baseline metrics
            
        Returns:
            Deviation score (0.0 to 1.0)
        """
        try:
            total_deviation = 0.0
            deviation_count = 0
            
            # Compare metrics
            baseline_metrics = baseline.get("metrics", {})
            metric_ranges = baseline.get("metric_ranges", {})
            
            for metric_name, metric_value in behavior_data.metrics.items():
                if isinstance(metric_value, (int, float)) and metric_name in baseline_metrics:
                    baseline_value = baseline_metrics[metric_name]
                    if baseline_value != 0:
                        deviation = abs(metric_value - baseline_value) / baseline_value
                        total_deviation += min(deviation, 1.0)
                        deviation_count += 1
            
            # Compare resource usage
            baseline_resources = baseline.get("resource_usage", {})
            resource_ranges = baseline.get("resource_ranges", {})
            
            for resource_name, resource_value in behavior_data.resource_usage.items():
                if isinstance(resource_value, (int, float)) and resource_name in baseline_resources:
                    baseline_value = baseline_resources[resource_name]
                    if baseline_value != 0:
                        deviation = abs(resource_value - baseline_value) / baseline_value
                        total_deviation += min(deviation, 1.0)
                        deviation_count += 1
            
            return total_deviation / deviation_count if deviation_count > 0 else 0.0
        except Exception as e:
            logger.error(f"Error calculating deviation score: {e}")
            return 1.0
    
    async def get_baseline(
        self,
        agent_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get baseline for an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Baseline metrics if found, None otherwise
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            async with self._lock:
                return self._baselines.get(agent_id, {}).copy()
        except Exception as e:
            logger.error(f"Error getting baseline: {e}")
            return None
    
    async def get_baseline_history(
        self,
        agent_id: str,
        limit: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[BaselineResult]:
        """
        Get baseline history for an agent.
        
        Args:
            agent_id: ID of the agent
            limit: Maximum number of entries to return
            start_time: Optional start time for filtering
            end_time: Optional end time for filtering
            
        Returns:
            List of baseline results
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            async with self._lock:
                baseline_history = self._baseline_history.get(agent_id, [])
                
                # Filter by time range
                if start_time or end_time:
                    filtered_history = []
                    for baseline in baseline_history:
                        if start_time and baseline.created_at < start_time:
                            continue
                        if end_time and baseline.created_at > end_time:
                            continue
                        filtered_history.append(baseline)
                    baseline_history = filtered_history
                
                # Limit number of entries
                if limit and len(baseline_history) > limit:
                    baseline_history = baseline_history[-limit:]
                
                return baseline_history
        except Exception as e:
            logger.error(f"Error getting baseline history: {e}")
            return []
    
    async def update_baseline(
        self,
        agent_id: str,
        behavior_data: List[BehaviorData]
    ) -> bool:
        """
        Update baseline for an agent.
        
        Args:
            agent_id: ID of the agent
            behavior_data: List of behavior data to use for baseline update
            
        Returns:
            True if update was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            # Generate new baseline
            baseline_result = await self.generate_baseline(agent_id, behavior_data)
            
            return baseline_result is not None
        except Exception as e:
            logger.error(f"Error updating baseline: {e}")
            return False
    
    async def clear_baseline(self, agent_id: Optional[str] = None) -> bool:
        """
        Clear baseline data.
        
        Args:
            agent_id: Optional agent ID to clear baseline for. If None, clears all baselines.
            
        Returns:
            True if clearing was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            async with self._lock:
                if agent_id:
                    if agent_id in self._baselines:
                        del self._baselines[agent_id]
                    if agent_id in self._baseline_history:
                        self._baseline_history[agent_id].clear()
                else:
                    self._baselines.clear()
                    self._baseline_history.clear()
            
            return True
        except Exception as e:
            logger.error(f"Error clearing baseline: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check health of the Baseline Generator."""
        if not self._initialized:
            return False
            
        try:
            # Check if auto update is enabled
            if not self._enable_auto_update:
                return False
            
            return True
        except Exception as e:
            logger.error(f"Baseline Generator health check failed: {e}")
            return False
    
    async def start(self) -> None:
        """Start the Baseline Generator."""
        if not self._initialized:
            await self.initialize()
        
        logger.info("Baseline Generator started successfully")
    
    async def stop(self) -> None:
        """Stop the Baseline Generator."""
        if not self._initialized:
            return
        
        # Clear data structures
        async with self._lock:
            self._baselines.clear()
            self._baseline_history.clear()
        
        # Reset initialization state
        self._initialized = False
        
        logger.info("Baseline Generator stopped successfully")
