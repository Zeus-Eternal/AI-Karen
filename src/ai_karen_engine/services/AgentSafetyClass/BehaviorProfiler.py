"""
Behavior Profiler module for profiling agent behavior.

This module provides functionality to profile agent behavior,
including behavior analysis, categorization, and trend identification.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

from ai_karen_engine.core.services.base import BaseService, ServiceConfig

from ..agent_safety_types import BehaviorData, BehaviorProfile, RiskAssessment, RiskLevel

logger = logging.getLogger(__name__)


class BehaviorProfiler(BaseService):
    """
    Behavior Profiler for profiling agent behavior.
    
    This class provides functionality to profile agent behavior,
    including behavior analysis, categorization, and trend identification.
    """
    
    def __init__(self, config: ServiceConfig):
        """Initialize the Behavior Profiler."""
        super().__init__(config)
        self._initialized = False
        self._lock = asyncio.Lock()
        
        # Thread-safe data structures
        self._profiles: Dict[str, BehaviorProfile] = {}
        self._profile_history: Dict[str, List[BehaviorProfile]] = defaultdict(list)
        
        # Configuration
        self._profile_update_interval_hours = 24
        self._min_data_points_for_profile = 20
        self._enable_trend_analysis = True
        self._enable_risk_assessment = True
        self._max_history_size = 100
    
    async def initialize(self) -> None:
        """Initialize the Behavior Profiler."""
        if self._initialized:
            return
            
        async with self._lock:
            try:
                # Initialize behavior profiling
                logger.debug("Behavior Profiler initialized")
                
                self._initialized = True
                logger.info("Behavior Profiler initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Behavior Profiler: {e}")
                raise RuntimeError(f"Behavior Profiler initialization failed: {e}")
    
    async def create_profile(
        self,
        agent_id: str,
        behavior_data: List[BehaviorData],
        profile_type: str = "default"
    ) -> Optional[BehaviorProfile]:
        """
        Create behavior profile for an agent.
        
        Args:
            agent_id: ID of the agent
            behavior_data: List of behavior data to use for profiling
            profile_type: Type of profile to create
            
        Returns:
            Behavior profile if successful, None otherwise
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            # Check if we have enough data
            if len(behavior_data) < self._min_data_points_for_profile:
                logger.warning(f"Insufficient data for profile creation: {len(behavior_data)} < {self._min_data_points_for_profile}")
                return None
            
            # Analyze behavior trends
            behavior_trends = await self._analyze_behavior_trends(behavior_data)
            
            # Analyze risk history
            risk_history = await self._analyze_risk_history(behavior_data)
            
            # Categorize behavior
            behavior_categories = await self._categorize_behavior(behavior_data)
            
            # Create behavior profile
            profile = BehaviorProfile(
                agent_id=agent_id,
                profile_type=profile_type,
                behavior_trends=behavior_trends,
                risk_history=risk_history,
                behavior_categories=behavior_categories
            )
            
            # Store profile
            async with self._lock:
                self._profiles[agent_id] = profile
                self._profile_history[agent_id].append(profile)
                
                # Limit history size
                if len(self._profile_history[agent_id]) > self._max_history_size:
                    self._profile_history[agent_id] = self._profile_history[agent_id][-self._max_history_size:]
            
            return profile
        except Exception as e:
            logger.error(f"Error creating behavior profile: {e}")
            return None
    
    async def _analyze_behavior_trends(
        self,
        behavior_data: List[BehaviorData]
    ) -> Dict[str, Any]:
        """
        Analyze behavior trends from behavior data.
        
        Args:
            behavior_data: List of behavior data to analyze
            
        Returns:
            Dictionary of behavior trends
        """
        try:
            trends = {
                "metrics": {},
                "resource_usage": {},
                "activity_patterns": {},
                "temporal_patterns": {}
            }
            
            # Sort data by timestamp
            sorted_data = sorted(behavior_data, key=lambda x: x.timestamp)
            
            # Analyze metric trends
            for metric_name in ["cpu_usage", "memory_usage", "response_time", "error_rate", "task_completion_rate"]:
                values = [data.metrics.get(metric_name, 0) for data in sorted_data if metric_name in data.metrics]
                if values:
                    # Calculate trend direction
                    if len(values) >= 2:
                        first_half = values[:len(values)//2]
                        second_half = values[len(values)//2:]
                        
                        first_avg = sum(first_half) / len(first_half)
                        second_avg = sum(second_half) / len(second_half)
                        
                        if second_avg > first_avg * 1.1:
                            trend_direction = "increasing"
                        elif second_avg < first_avg * 0.9:
                            trend_direction = "decreasing"
                        else:
                            trend_direction = "stable"
                    else:
                        trend_direction = "insufficient_data"
                    
                    trends["metrics"][metric_name] = {
                        "trend": trend_direction,
                        "average": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values),
                        "volatility": self._calculate_volatility(values)
                    }
            
            # Analyze resource usage trends
            for resource_name in ["cpu", "memory", "disk", "network"]:
                values = [data.resource_usage.get(resource_name, 0) for data in sorted_data if resource_name in data.resource_usage]
                if values:
                    # Calculate trend direction
                    if len(values) >= 2:
                        first_half = values[:len(values)//2]
                        second_half = values[len(values)//2:]
                        
                        first_avg = sum(first_half) / len(first_half)
                        second_avg = sum(second_half) / len(second_half)
                        
                        if second_avg > first_avg * 1.1:
                            trend_direction = "increasing"
                        elif second_avg < first_avg * 0.9:
                            trend_direction = "decreasing"
                        else:
                            trend_direction = "stable"
                    else:
                        trend_direction = "insufficient_data"
                    
                    trends["resource_usage"][resource_name] = {
                        "trend": trend_direction,
                        "average": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values),
                        "volatility": self._calculate_volatility(values)
                    }
            
            # Analyze activity patterns
            timestamps = [data.timestamp for data in sorted_data]
            if len(timestamps) >= 2:
                # Calculate time intervals between data points
                intervals = []
                for i in range(1, len(timestamps)):
                    interval = (timestamps[i] - timestamps[i-1]).total_seconds()
                    intervals.append(interval)
                
                if intervals:
                    trends["activity_patterns"] = {
                        "average_interval": sum(intervals) / len(intervals),
                        "min_interval": min(intervals),
                        "max_interval": max(intervals),
                        "interval_volatility": self._calculate_volatility(intervals)
                    }
            
            # Analyze temporal patterns
            if len(timestamps) >= 24:  # Need at least 24 data points for hourly analysis
                # Group by hour of day
                hourly_counts = defaultdict(int)
                for timestamp in timestamps:
                    hour = timestamp.hour
                    hourly_counts[hour] += 1
                
                # Find peak hours
                max_count = max(hourly_counts.values())
                peak_hours = [hour for hour, count in hourly_counts.items() if count == max_count]
                
                trends["temporal_patterns"] = {
                    "peak_hours": peak_hours,
                    "hourly_distribution": dict(hourly_counts)
                }
            
            return trends
        except Exception as e:
            logger.error(f"Error analyzing behavior trends: {e}")
            return {}
    
    def _calculate_volatility(self, values: List[float]) -> float:
        """
        Calculate volatility of values.
        
        Args:
            values: List of values
            
        Returns:
            Volatility measure (coefficient of variation)
        """
        try:
            if not values or len(values) < 2:
                return 0.0
            
            mean = sum(values) / len(values)
            variance = sum((x - mean) ** 2 for x in values) / len(values)
            std_dev = variance ** 0.5
            
            return std_dev / mean if mean != 0 else 0.0
        except Exception as e:
            logger.error(f"Error calculating volatility: {e}")
            return 0.0
    
    async def _analyze_risk_history(
        self,
        behavior_data: List[BehaviorData]
    ) -> List[Dict[str, Any]]:
        """
        Analyze risk history from behavior data.
        
        Args:
            behavior_data: List of behavior data to analyze
            
        Returns:
            List of risk assessments
        """
        try:
            risk_history = []
            
            # Sort data by timestamp
            sorted_data = sorted(behavior_data, key=lambda x: x.timestamp)
            
            # Analyze risk for each data point
            for data in sorted_data:
                # Calculate risk level based on metrics and resource usage
                risk_score = 0.0
                risk_factors = []
                
                # Check CPU usage
                cpu_usage = data.metrics.get("cpu_usage", 0)
                if cpu_usage > 0.9:
                    risk_score += 0.3
                    risk_factors.append("high_cpu_usage")
                elif cpu_usage > 0.7:
                    risk_score += 0.1
                    risk_factors.append("elevated_cpu_usage")
                
                # Check memory usage
                memory_usage = data.metrics.get("memory_usage", 0)
                if memory_usage > 0.9:
                    risk_score += 0.3
                    risk_factors.append("high_memory_usage")
                elif memory_usage > 0.7:
                    risk_score += 0.1
                    risk_factors.append("elevated_memory_usage")
                
                # Check error rate
                error_rate = data.metrics.get("error_rate", 0)
                if error_rate > 0.2:
                    risk_score += 0.4
                    risk_factors.append("high_error_rate")
                elif error_rate > 0.1:
                    risk_score += 0.2
                    risk_factors.append("elevated_error_rate")
                
                # Check response time
                response_time = data.metrics.get("response_time", 0)
                if response_time > 10.0:
                    risk_score += 0.2
                    risk_factors.append("high_response_time")
                elif response_time > 5.0:
                    risk_score += 0.1
                    risk_factors.append("elevated_response_time")
                
                # Determine risk level
                if risk_score > 0.7:
                    risk_level = RiskLevel.HIGH_RISK
                elif risk_score > 0.4:
                    risk_level = RiskLevel.MEDIUM_RISK
                elif risk_score > 0.2:
                    risk_level = RiskLevel.LOW_RISK
                else:
                    risk_level = RiskLevel.SAFE
                
                # Create risk assessment
                risk_assessment = RiskAssessment(
                    risk_level=risk_level,
                    risk_score=risk_score,
                    factors=risk_factors,
                    assessed_at=data.timestamp
                )
                
                risk_history.append({
                    "timestamp": data.timestamp,
                    "risk_assessment": risk_assessment
                })
            
            return risk_history
        except Exception as e:
            logger.error(f"Error analyzing risk history: {e}")
            return []
    
    async def _categorize_behavior(
        self,
        behavior_data: List[BehaviorData]
    ) -> Dict[str, float]:
        """
        Categorize behavior from behavior data.
        
        Args:
            behavior_data: List of behavior data to analyze
            
        Returns:
            Dictionary of behavior categories with scores
        """
        try:
            categories = {
                "resource_intensive": 0.0,
                "error_prone": 0.0,
                "high_performance": 0.0,
                "interactive": 0.0,
                "stable": 0.0,
                "volatile": 0.0
            }
            
            # Calculate average metrics
            avg_metrics = {}
            for metric_name in ["cpu_usage", "memory_usage", "response_time", "error_rate", "task_completion_rate"]:
                values = [data.metrics.get(metric_name, 0) for data in behavior_data if metric_name in data.metrics]
                if values:
                    avg_metrics[metric_name] = sum(values) / len(values)
            
            # Calculate average resource usage
            avg_resource_usage = {}
            for resource_name in ["cpu", "memory", "disk", "network"]:
                values = [data.resource_usage.get(resource_name, 0) for data in behavior_data if resource_name in data.resource_usage]
                if values:
                    avg_resource_usage[resource_name] = sum(values) / len(values)
            
            # Calculate category scores
            # Resource intensive
            resource_score = sum(avg_resource_usage.values()) / len(avg_resource_usage) if avg_resource_usage else 0
            categories["resource_intensive"] = min(resource_score, 1.0)
            
            # Error prone
            error_rate = avg_metrics.get("error_rate", 0)
            categories["error_prone"] = min(error_rate * 5, 1.0)  # Scale up to 0.0-1.0
            
            # High performance
            task_completion = avg_metrics.get("task_completion_rate", 1.0)
            response_time = avg_metrics.get("response_time", 0)
            performance_score = (task_completion * 0.7) + (max(0, 1.0 - response_time / 10.0) * 0.3)
            categories["high_performance"] = performance_score
            
            # Interactive
            interaction_freq = avg_metrics.get("interaction_frequency", 0)
            categories["interactive"] = min(interaction_freq / 20.0, 1.0)
            
            # Stable
            # Calculate stability based on volatility of metrics
            stability_score = 0.0
            metric_count = 0
            
            for metric_name in ["cpu_usage", "memory_usage", "response_time"]:
                values = [data.metrics.get(metric_name, 0) for data in behavior_data if metric_name in data.metrics]
                if len(values) >= 2:
                    volatility = self._calculate_volatility(values)
                    stability_score += max(0, 1.0 - volatility * 5)  # Lower volatility = higher stability
                    metric_count += 1
            
            categories["stable"] = stability_score / metric_count if metric_count > 0 else 0.5
            
            # Volatile (opposite of stable)
            categories["volatile"] = 1.0 - categories["stable"]
            
            return categories
        except Exception as e:
            logger.error(f"Error categorizing behavior: {e}")
            return {}
    
    async def get_profile(
        self,
        agent_id: str
    ) -> Optional[BehaviorProfile]:
        """
        Get behavior profile for an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Behavior profile if found, None otherwise
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            async with self._lock:
                profile = self._profiles.get(agent_id)
                return profile if profile else None
        except Exception as e:
            logger.error(f"Error getting behavior profile: {e}")
            return None
    
    async def get_profile_history(
        self,
        agent_id: str,
        limit: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[BehaviorProfile]:
        """
        Get profile history for an agent.
        
        Args:
            agent_id: ID of the agent
            limit: Maximum number of entries to return
            start_time: Optional start time for filtering
            end_time: Optional end time for filtering
            
        Returns:
            List of behavior profiles
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            async with self._lock:
                profile_history = self._profile_history.get(agent_id, [])
                
                # Filter by time range
                if start_time or end_time:
                    filtered_history = []
                    for profile in profile_history:
                        if start_time and profile.last_updated < start_time:
                            continue
                        if end_time and profile.last_updated > end_time:
                            continue
                        filtered_history.append(profile)
                    profile_history = filtered_history
                
                # Limit number of entries
                if limit and len(profile_history) > limit:
                    profile_history = profile_history[-limit:]
                
                return profile_history
        except Exception as e:
            logger.error(f"Error getting profile history: {e}")
            return []
    
    async def update_profile(
        self,
        agent_id: str,
        behavior_data: List[BehaviorData],
        profile_type: str = "default"
    ) -> bool:
        """
        Update behavior profile for an agent.
        
        Args:
            agent_id: ID of the agent
            behavior_data: List of behavior data to use for profile update
            profile_type: Type of profile to create
            
        Returns:
            True if update was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            # Create new profile
            profile = await self.create_profile(agent_id, behavior_data, profile_type)
            
            return profile is not None
        except Exception as e:
            logger.error(f"Error updating behavior profile: {e}")
            return False
    
    async def clear_profile(self, agent_id: Optional[str] = None) -> bool:
        """
        Clear behavior profile.
        
        Args:
            agent_id: Optional agent ID to clear profile for. If None, clears all profiles.
            
        Returns:
            True if clearing was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            async with self._lock:
                if agent_id:
                    if agent_id in self._profiles:
                        del self._profiles[agent_id]
                    if agent_id in self._profile_history:
                        self._profile_history[agent_id].clear()
                else:
                    self._profiles.clear()
                    self._profile_history.clear()
            
            return True
        except Exception as e:
            logger.error(f"Error clearing behavior profile: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check health of the Behavior Profiler."""
        if not self._initialized:
            return False
            
        try:
            # Check if trend analysis is enabled
            if not self._enable_trend_analysis:
                return False
            
            # Check if risk assessment is enabled
            if not self._enable_risk_assessment:
                return False
            
            return True
        except Exception as e:
            logger.error(f"Behavior Profiler health check failed: {e}")
            return False
    
    async def start(self) -> None:
        """Start the Behavior Profiler."""
        if not self._initialized:
            await self.initialize()
        
        logger.info("Behavior Profiler started successfully")
    
    async def stop(self) -> None:
        """Stop the Behavior Profiler."""
        if not self._initialized:
            return
        
        # Clear data structures
        async with self._lock:
            self._profiles.clear()
            self._profile_history.clear()
        
        # Reset initialization state
        self._initialized = False
        
        logger.info("Behavior Profiler stopped successfully")
