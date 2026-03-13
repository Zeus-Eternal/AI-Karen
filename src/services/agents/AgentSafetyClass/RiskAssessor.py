"""
Risk Assessor module for assessing agent behavior risks.

This module provides functionality to assess risks in agent behavior,
including risk calculation, analysis, and reporting.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict

from ai_karen_engine.core.services.base import BaseService, ServiceConfig

from ..agent_safety_types import BehaviorData, RiskAssessment, RiskLevel

logger = logging.getLogger(__name__)


class RiskAssessor(BaseService):
    """
    Risk Assessor for assessing agent behavior risks.
    
    This class provides functionality to assess risks in agent behavior,
    including risk calculation, analysis, and reporting.
    """
    
    def __init__(self, config: ServiceConfig):
        """Initialize the Risk Assessor."""
        super().__init__(config)
        self._initialized = False
        self._lock = asyncio.Lock()
        
        # Thread-safe data structures
        self._risk_history: Dict[str, List[RiskAssessment]] = defaultdict(list)
        self._risk_thresholds: Dict[str, Dict[str, float]] = {}
        
        # Configuration
        self._default_high_threshold = 0.7
        self._default_medium_threshold = 0.4
        self._enable_adaptive_thresholds = True
        self._enable_risk_trends = True
        self._max_history_size = 1000
    
    async def initialize(self) -> None:
        """Initialize the Risk Assessor."""
        if self._initialized:
            return
            
        async with self._lock:
            try:
                # Initialize risk assessment
                await self._load_risk_thresholds()
                
                self._initialized = True
                logger.info("Risk Assessor initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Risk Assessor: {e}")
                raise RuntimeError(f"Risk Assessor initialization failed: {e}")
    
    async def _load_risk_thresholds(self) -> None:
        """Load risk thresholds."""
        # Default risk thresholds
        self._risk_thresholds = {
            "cpu_usage": {
                "high": 0.9,
                "medium": 0.7
            },
            "memory_usage": {
                "high": 0.9,
                "medium": 0.7
            },
            "disk_usage": {
                "high": 0.9,
                "medium": 0.7
            },
            "network_usage": {
                "high": 0.9,
                "medium": 0.7
            },
            "response_time": {
                "high": 10.0,
                "medium": 5.0
            },
            "error_rate": {
                "high": 0.2,
                "medium": 0.1
            },
            "task_completion_rate": {
                "high": 0.5,  # Inverted: lower is worse
                "medium": 0.7
            },
            "interaction_frequency": {
                "high": 20.0,
                "medium": 10.0
            }
        }
        
        logger.debug(f"Loaded {len(self._risk_thresholds)} risk thresholds")
    
    async def assess_risk(
        self,
        agent_id: str,
        behavior_data: BehaviorData
    ) -> RiskAssessment:
        """
        Assess risk for agent behavior.
        
        Args:
            agent_id: ID of the agent
            behavior_data: Behavior data to assess
            
        Returns:
            Risk assessment
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            # Calculate risk score
            risk_score = await self._calculate_risk_score(behavior_data)
            
            # Determine risk level
            risk_level = await self._determine_risk_level(risk_score)
            
            # Identify risk factors
            risk_factors = await self._identify_risk_factors(behavior_data)
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(
                behavior_data, risk_level, risk_factors
            )
            
            # Create risk assessment
            risk_assessment = RiskAssessment(
                risk_level=risk_level,
                risk_score=risk_score,
                factors=risk_factors,
                recommendations=recommendations,
                assessed_at=behavior_data.timestamp
            )
            
            # Store in history
            async with self._lock:
                self._risk_history[agent_id].append(risk_assessment)
                
                # Limit history size
                if len(self._risk_history[agent_id]) > self._max_history_size:
                    self._risk_history[agent_id] = self._risk_history[agent_id][-self._max_history_size:]
            
            return risk_assessment
        except Exception as e:
            logger.error(f"Error assessing risk: {e}")
            return RiskAssessment(
                risk_level=RiskLevel.CRITICAL_RISK,
                risk_score=1.0,
                factors=["risk_assessment_error"],
                recommendations=["Review risk assessment system"],
                assessed_at=datetime.utcnow()
            )
    
    async def _calculate_risk_score(self, behavior_data: BehaviorData) -> float:
        """
        Calculate risk score for behavior data.
        
        Args:
            behavior_data: Behavior data to assess
            
        Returns:
            Risk score (0.0 to 1.0)
        """
        try:
            total_score = 0.0
            total_weight = 0.0
            
            # Weights for different metrics
            weights = {
                "cpu_usage": 0.15,
                "memory_usage": 0.15,
                "disk_usage": 0.1,
                "network_usage": 0.1,
                "response_time": 0.15,
                "error_rate": 0.25,
                "task_completion_rate": 0.1,
                "interaction_frequency": 0.05
            }
            
            # Calculate risk for each metric
            for metric_name, weight in weights.items():
                if metric_name in ["cpu_usage", "memory_usage", "disk_usage", "network_usage"]:
                    # Resource usage metrics
                    value = behavior_data.resource_usage.get(metric_name.replace("_usage", ""), 0)
                    threshold = self._risk_thresholds.get(metric_name, {})
                    
                    if value >= threshold.get("high", self._default_high_threshold):
                        risk_contribution = 1.0
                    elif value >= threshold.get("medium", self._default_medium_threshold):
                        risk_contribution = 0.5
                    else:
                        risk_contribution = 0.0
                    
                    total_score += risk_contribution * weight
                    total_weight += weight
                
                elif metric_name in behavior_data.metrics:
                    # Other metrics
                    value = behavior_data.metrics[metric_name]
                    threshold = self._risk_thresholds.get(metric_name, {})
                    
                    if metric_name == "task_completion_rate":
                        # Inverted: lower is worse
                        if value <= threshold.get("high", self._default_high_threshold):
                            risk_contribution = 1.0
                        elif value <= threshold.get("medium", self._default_medium_threshold):
                            risk_contribution = 0.5
                        else:
                            risk_contribution = 0.0
                    else:
                        # Normal: higher is worse
                        if value >= threshold.get("high", self._default_high_threshold):
                            risk_contribution = 1.0
                        elif value >= threshold.get("medium", self._default_medium_threshold):
                            risk_contribution = 0.5
                        else:
                            risk_contribution = 0.0
                    
                    total_score += risk_contribution * weight
                    total_weight += weight
            
            return total_score / total_weight if total_weight > 0 else 0.0
        except Exception as e:
            logger.error(f"Error calculating risk score: {e}")
            return 1.0
    
    async def _determine_risk_level(self, risk_score: float) -> RiskLevel:
        """
        Determine risk level from risk score.
        
        Args:
            risk_score: Risk score (0.0 to 1.0)
            
        Returns:
            Risk level
        """
        try:
            if risk_score >= 0.8:
                return RiskLevel.CRITICAL_RISK
            elif risk_score >= 0.6:
                return RiskLevel.HIGH_RISK
            elif risk_score >= 0.4:
                return RiskLevel.MEDIUM_RISK
            elif risk_score >= 0.2:
                return RiskLevel.LOW_RISK
            else:
                return RiskLevel.SAFE
        except Exception as e:
            logger.error(f"Error determining risk level: {e}")
            return RiskLevel.CRITICAL_RISK
    
    async def _identify_risk_factors(self, behavior_data: BehaviorData) -> List[str]:
        """
        Identify risk factors from behavior data.
        
        Args:
            behavior_data: Behavior data to analyze
            
        Returns:
            List of risk factors
        """
        try:
            risk_factors = []
            
            # Check resource usage
            for resource_name, value in behavior_data.resource_usage.items():
                metric_name = f"{resource_name}_usage"
                threshold = self._risk_thresholds.get(metric_name, {})
                
                if value >= threshold.get("high", self._default_high_threshold):
                    risk_factors.append(f"high_{resource_name}_usage")
                elif value >= threshold.get("medium", self._default_medium_threshold):
                    risk_factors.append(f"elevated_{resource_name}_usage")
            
            # Check other metrics
            for metric_name, value in behavior_data.metrics.items():
                threshold = self._risk_thresholds.get(metric_name, {})
                
                if metric_name == "task_completion_rate":
                    # Inverted: lower is worse
                    if value <= threshold.get("high", self._default_high_threshold):
                        risk_factors.append(f"low_{metric_name}")
                    elif value <= threshold.get("medium", self._default_medium_threshold):
                        risk_factors.append(f"reduced_{metric_name}")
                else:
                    # Normal: higher is worse
                    if value >= threshold.get("high", self._default_high_threshold):
                        risk_factors.append(f"high_{metric_name}")
                    elif value >= threshold.get("medium", self._default_medium_threshold):
                        risk_factors.append(f"elevated_{metric_name}")
            
            return risk_factors
        except Exception as e:
            logger.error(f"Error identifying risk factors: {e}")
            return ["risk_factor_identification_error"]
    
    async def _generate_recommendations(
        self,
        behavior_data: BehaviorData,
        risk_level: RiskLevel,
        risk_factors: List[str]
    ) -> List[str]:
        """
        Generate recommendations based on risk assessment.
        
        Args:
            behavior_data: Behavior data that was assessed
            risk_level: Assessed risk level
            risk_factors: Identified risk factors
            
        Returns:
            List of recommendations
        """
        try:
            recommendations = []
            
            # Generate recommendations based on risk level
            if risk_level in [RiskLevel.HIGH_RISK, RiskLevel.CRITICAL_RISK]:
                recommendations.append("Immediate attention required")
                recommendations.append("Consider limiting agent operations")
                recommendations.append("Review recent behavior changes")
            
            # Generate recommendations based on risk factors
            for factor in risk_factors:
                if "cpu_usage" in factor:
                    recommendations.append("Optimize CPU usage or allocate more resources")
                elif "memory_usage" in factor:
                    recommendations.append("Optimize memory usage or allocate more memory")
                elif "disk_usage" in factor:
                    recommendations.append("Optimize disk usage or allocate more storage")
                elif "network_usage" in factor:
                    recommendations.append("Optimize network usage or allocate more bandwidth")
                elif "response_time" in factor:
                    recommendations.append("Improve response time through optimization")
                elif "error_rate" in factor:
                    recommendations.append("Investigate and reduce error rate")
                elif "task_completion_rate" in factor:
                    recommendations.append("Improve task completion rate")
                elif "interaction_frequency" in factor:
                    recommendations.append("Monitor and potentially limit interaction frequency")
            
            # Remove duplicates
            recommendations = list(set(recommendations))
            
            # Sort by priority
            priority_order = {
                "Immediate attention required": 0,
                "Consider limiting agent operations": 1,
                "Review recent behavior changes": 2,
                "Optimize CPU usage or allocate more resources": 3,
                "Optimize memory usage or allocate more memory": 4,
                "Optimize disk usage or allocate more storage": 5,
                "Optimize network usage or allocate more bandwidth": 6,
                "Improve response time through optimization": 7,
                "Investigate and reduce error rate": 8,
                "Improve task completion rate": 9,
                "Monitor and potentially limit interaction frequency": 10
            }
            
            recommendations.sort(key=lambda x: priority_order.get(x, 99))
            
            return recommendations
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return ["Review risk assessment system"]
    
    async def get_risk_history(
        self,
        agent_id: str,
        limit: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[RiskAssessment]:
        """
        Get risk history for an agent.
        
        Args:
            agent_id: ID of the agent
            limit: Maximum number of entries to return
            start_time: Optional start time for filtering
            end_time: Optional end time for filtering
            
        Returns:
            List of risk assessments
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            async with self._lock:
                risk_history = self._risk_history.get(agent_id, [])
                
                # Filter by time range
                if start_time or end_time:
                    filtered_history = []
                    for risk in risk_history:
                        if start_time and risk.assessed_at < start_time:
                            continue
                        if end_time and risk.assessed_at > end_time:
                            continue
                        filtered_history.append(risk)
                    risk_history = filtered_history
                
                # Limit number of entries
                if limit and len(risk_history) > limit:
                    risk_history = risk_history[-limit:]
                
                return risk_history
        except Exception as e:
            logger.error(f"Error getting risk history: {e}")
            return []
    
    async def get_risk_trends(
        self,
        agent_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get risk trends for an agent.
        
        Args:
            agent_id: ID of the agent
            days: Number of days to analyze
            
        Returns:
            Dictionary of risk trends
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            # Get risk history for the specified period
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days)
            
            risk_history = await self.get_risk_history(
                agent_id=agent_id,
                start_time=start_time,
                end_time=end_time
            )
            
            if not risk_history:
                return {"error": "No risk history found"}
            
            # Calculate trends
            risk_scores = [risk.risk_score for risk in risk_history]
            
            # Calculate average risk score
            avg_risk = sum(risk_scores) / len(risk_scores)
            
            # Calculate risk trend
            if len(risk_scores) >= 2:
                first_half = risk_scores[:len(risk_scores)//2]
                second_half = risk_scores[len(risk_scores)//2:]
                
                first_avg = sum(first_half) / len(first_half)
                second_avg = sum(second_half) / len(second_half)
                
                if second_avg > first_avg * 1.1:
                    trend = "increasing"
                elif second_avg < first_avg * 0.9:
                    trend = "decreasing"
                else:
                    trend = "stable"
            else:
                trend = "insufficient_data"
            
            # Count risk levels
            risk_level_counts = defaultdict(int)
            for risk in risk_history:
                risk_level_counts[risk.risk_level] += 1
            
            # Get most common risk factors
            factor_counts = defaultdict(int)
            for risk in risk_history:
                for factor in risk.factors:
                    factor_counts[factor] += 1
            
            # Sort factors by count
            sorted_factors = sorted(
                factor_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]  # Top 5 factors
            
            return {
                "average_risk_score": avg_risk,
                "trend": trend,
                "risk_level_distribution": dict(risk_level_counts),
                "top_risk_factors": sorted_factors,
                "total_assessments": len(risk_history)
            }
        except Exception as e:
            logger.error(f"Error getting risk trends: {e}")
            return {"error": str(e)}
    
    async def update_risk_threshold(
        self,
        metric_name: str,
        high_threshold: float,
        medium_threshold: float
    ) -> bool:
        """
        Update risk threshold for a metric.
        
        Args:
            metric_name: Name of the metric
            high_threshold: High risk threshold
            medium_threshold: Medium risk threshold
            
        Returns:
            True if update was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            async with self._lock:
                if metric_name not in self._risk_thresholds:
                    self._risk_thresholds[metric_name] = {}
                
                self._risk_thresholds[metric_name]["high"] = high_threshold
                self._risk_thresholds[metric_name]["medium"] = medium_threshold
            
            return True
        except Exception as e:
            logger.error(f"Error updating risk threshold: {e}")
            return False
    
    async def clear_risk_history(self, agent_id: Optional[str] = None) -> bool:
        """
        Clear risk history.
        
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
                    self._risk_history[agent_id].clear()
                else:
                    self._risk_history.clear()
            
            return True
        except Exception as e:
            logger.error(f"Error clearing risk history: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check health of the Risk Assessor."""
        if not self._initialized:
            return False
            
        try:
            # Check if risk thresholds are loaded
            if not self._risk_thresholds:
                return False
            
            return True
        except Exception as e:
            logger.error(f"Risk Assessor health check failed: {e}")
            return False
    
    async def start(self) -> None:
        """Start the Risk Assessor."""
        if not self._initialized:
            await self.initialize()
        
        logger.info("Risk Assessor started successfully")
    
    async def stop(self) -> None:
        """Stop the Risk Assessor."""
        if not self._initialized:
            return
        
        # Clear data structures
        async with self._lock:
            self._risk_history.clear()
            self._risk_thresholds.clear()
        
        # Reset initialization state
        self._initialized = False
        
        logger.info("Risk Assessor stopped successfully")
