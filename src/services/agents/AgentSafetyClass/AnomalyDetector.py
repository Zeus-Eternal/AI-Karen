"""
Anomaly Detector module for detecting anomalies in agent behavior.

This module provides functionality to detect anomalies in agent behavior,
including anomaly detection algorithms, scoring, and reporting.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict

from ai_karen_engine.core.services.base import BaseService, ServiceConfig

from ..agent_safety_types import BehaviorData, AnomalyResult, RiskLevel

logger = logging.getLogger(__name__)


class AnomalyDetector(BaseService):
    """
    Anomaly Detector for detecting anomalies in agent behavior.
    
    This class provides functionality to detect anomalies in agent behavior,
    including anomaly detection algorithms, scoring, and reporting.
    """
    
    def __init__(self, config: ServiceConfig):
        """Initialize the Anomaly Detector."""
        super().__init__(config)
        self._initialized = False
        self._lock = asyncio.Lock()
        
        # Thread-safe data structures
        self._anomaly_history: Dict[str, List[AnomalyResult]] = defaultdict(list)
        self._baseline_metrics: Dict[str, Dict[str, float]] = {}
        
        # Configuration
        self._anomaly_threshold = 0.7
        self._enable_adaptive_thresholds = True
        self._enable_ml_detection = True
        self._max_history_size = 1000
    
    async def initialize(self) -> None:
        """Initialize the Anomaly Detector."""
        if self._initialized:
            return
            
        async with self._lock:
            try:
                # Initialize anomaly detection
                logger.debug("Anomaly Detector initialized")
                
                self._initialized = True
                logger.info("Anomaly Detector initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Anomaly Detector: {e}")
                raise RuntimeError(f"Anomaly Detector initialization failed: {e}")
    
    async def detect_anomalies(self, behavior_data: BehaviorData) -> AnomalyResult:
        """
        Detect anomalies in agent behavior.
        
        Args:
            behavior_data: Behavior data to analyze
            
        Returns:
            Anomaly detection result
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            # Calculate anomaly score
            anomaly_score = await self._calculate_anomaly_score(behavior_data)
            
            # Determine if anomaly
            is_anomaly = anomaly_score >= self._anomaly_threshold
            
            # Get anomaly type
            anomaly_type = await self._determine_anomaly_type(behavior_data, anomaly_score)
            
            # Calculate confidence
            confidence = min(anomaly_score * 1.5, 1.0)
            
            # Create description
            description = await self._generate_anomaly_description(
                behavior_data, anomaly_score, anomaly_type
            )
            
            # Create anomaly result
            anomaly_result = AnomalyResult(
                is_anomaly=is_anomaly,
                anomaly_score=anomaly_score,
                anomaly_type=anomaly_type,
                confidence=confidence,
                description=description
            )
            
            # Store in history
            async with self._lock:
                self._anomaly_history[behavior_data.agent_id].append(anomaly_result)
                
                # Limit history size
                if len(self._anomaly_history[behavior_data.agent_id]) > self._max_history_size:
                    self._anomaly_history[behavior_data.agent_id] = self._anomaly_history[behavior_data.agent_id][-self._max_history_size:]
            
            return anomaly_result
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return AnomalyResult(
                is_anomaly=False,
                anomaly_score=0.0,
                anomaly_type="error",
                confidence=0.0,
                description=f"Error detecting anomalies: {str(e)}"
            )
    
    async def _calculate_anomaly_score(self, behavior_data: BehaviorData) -> float:
        """
        Calculate anomaly score for behavior data.
        
        Args:
            behavior_data: Behavior data to analyze
            
        Returns:
            Anomaly score (0.0 to 1.0)
        """
        try:
            # Get baseline metrics for agent
            baseline = self._baseline_metrics.get(behavior_data.agent_id, {})
            
            # Calculate deviation from baseline
            deviation_score = 0.0
            metric_count = 0
            
            for metric_name, metric_value in behavior_data.metrics.items():
                if isinstance(metric_value, (int, float)):
                    baseline_value = baseline.get(metric_name, 0.0)
                    if baseline_value != 0:
                        deviation = abs(metric_value - baseline_value) / baseline_value
                        deviation_score += min(deviation, 1.0)
                        metric_count += 1
            
            # Calculate resource usage anomaly
            resource_score = 0.0
            resource_count = 0
            
            for resource_name, resource_value in behavior_data.resource_usage.items():
                baseline_value = baseline.get(f"resource_{resource_name}", 0.0)
                if baseline_value != 0:
                    deviation = abs(resource_value - baseline_value) / baseline_value
                    resource_score += min(deviation, 1.0)
                    resource_count += 1
            
            # Combine scores
            total_score = 0.0
            total_count = 0
            
            if metric_count > 0:
                total_score += deviation_score / metric_count
                total_count += 1
            
            if resource_count > 0:
                total_score += resource_score / resource_count
                total_count += 1
            
            return total_score / total_count if total_count > 0 else 0.0
        except Exception as e:
            logger.error(f"Error calculating anomaly score: {e}")
            return 0.0
    
    async def _determine_anomaly_type(self, behavior_data: BehaviorData, anomaly_score: float) -> str:
        """
        Determine the type of anomaly.
        
        Args:
            behavior_data: Behavior data to analyze
            anomaly_score: Anomaly score
            
        Returns:
            Anomaly type
        """
        try:
            # Check for resource usage anomalies
            for resource_name, resource_value in behavior_data.resource_usage.items():
                if resource_value > 0.9:  # High resource usage
                    return f"high_{resource_name}_usage"
            
            # Check for metric anomalies
            for metric_name, metric_value in behavior_data.metrics.items():
                if isinstance(metric_value, (int, float)) and metric_value < 0.1:  # Low metric value
                    return f"low_{metric_name}"
            
            # Default anomaly type based on score
            if anomaly_score > 0.9:
                return "critical_anomaly"
            elif anomaly_score > 0.7:
                return "high_anomaly"
            elif anomaly_score > 0.5:
                return "medium_anomaly"
            else:
                return "low_anomaly"
        except Exception as e:
            logger.error(f"Error determining anomaly type: {e}")
            return "unknown_anomaly"
    
    async def _generate_anomaly_description(
        self,
        behavior_data: BehaviorData,
        anomaly_score: float,
        anomaly_type: str
    ) -> str:
        """
        Generate description for anomaly.
        
        Args:
            behavior_data: Behavior data to analyze
            anomaly_score: Anomaly score
            anomaly_type: Anomaly type
            
        Returns:
            Anomaly description
        """
        try:
            # Generate description based on anomaly type
            if "high_" in anomaly_type and "_usage" in anomaly_type:
                resource = anomaly_type.replace("high_", "").replace("_usage", "")
                return f"High {resource} usage detected: {behavior_data.resource_usage.get(resource, 0) * 100:.1f}%"
            elif "low_" in anomaly_type:
                metric = anomaly_type.replace("low_", "")
                return f"Low {metric} detected: {behavior_data.metrics.get(metric, 0)}"
            else:
                return f"Anomaly detected with score {anomaly_score:.2f} of type {anomaly_type}"
        except Exception as e:
            logger.error(f"Error generating anomaly description: {e}")
            return f"Anomaly detected with score {anomaly_score:.2f}"
    
    async def get_anomaly_history(
        self,
        agent_id: str,
        limit: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[AnomalyResult]:
        """
        Get anomaly history for an agent.
        
        Args:
            agent_id: ID of the agent
            limit: Maximum number of entries to return
            start_time: Optional start time for filtering
            end_time: Optional end time for filtering
            
        Returns:
            List of anomaly results
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            async with self._lock:
                anomaly_history = self._anomaly_history.get(agent_id, [])
                
                # Filter by time range
                if start_time or end_time:
                    filtered_history = []
                    for anomaly in anomaly_history:
                        if start_time and anomaly.detected_at < start_time:
                            continue
                        if end_time and anomaly.detected_at > end_time:
                            continue
                        filtered_history.append(anomaly)
                    anomaly_history = filtered_history
                
                # Limit number of entries
                if limit and len(anomaly_history) > limit:
                    anomaly_history = anomaly_history[-limit:]
                
                return anomaly_history
        except Exception as e:
            logger.error(f"Error getting anomaly history: {e}")
            return []
    
    async def update_baseline(self, agent_id: str, metrics: Dict[str, float]) -> bool:
        """
        Update baseline metrics for an agent.
        
        Args:
            agent_id: ID of the agent
            metrics: New baseline metrics
            
        Returns:
            True if update was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            async with self._lock:
                if agent_id not in self._baseline_metrics:
                    self._baseline_metrics[agent_id] = {}
                
                # Update metrics
                for metric_name, metric_value in metrics.items():
                    self._baseline_metrics[agent_id][metric_name] = metric_value
            
            return True
        except Exception as e:
            logger.error(f"Error updating baseline: {e}")
            return False
    
    async def clear_anomaly_history(self, agent_id: Optional[str] = None) -> bool:
        """
        Clear anomaly history.
        
        Args:
            agent_id: Optional agent ID to clear history for. If None, clears all history.
            
        Returns:
            True if clearing was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            async with self._lock:
                if agent_id:
                    self._anomaly_history[agent_id].clear()
                else:
                    self._anomaly_history.clear()
            
            return True
        except Exception as e:
            logger.error(f"Error clearing anomaly history: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check health of the Anomaly Detector."""
        if not self._initialized:
            return False
            
        try:
            # Check if anomaly detection is enabled
            if not self._enable_ml_detection:
                return False
            
            return True
        except Exception as e:
            logger.error(f"Anomaly Detector health check failed: {e}")
            return False
    
    async def start(self) -> None:
        """Start the Anomaly Detector."""
        if not self._initialized:
            await self.initialize()
        
        logger.info("Anomaly Detector started successfully")
    
    async def stop(self) -> None:
        """Stop the Anomaly Detector."""
        if not self._initialized:
            return
        
        # Clear data structures
        async with self._lock:
            self._anomaly_history.clear()
            self._baseline_metrics.clear()
        
        # Reset initialization state
        self._initialized = False
        
        logger.info("Anomaly Detector stopped successfully")
