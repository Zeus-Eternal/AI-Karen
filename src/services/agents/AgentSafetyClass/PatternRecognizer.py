"""
Pattern Recognizer module for recognizing patterns in agent behavior.

This module provides functionality to recognize patterns in agent behavior,
including pattern detection, classification, and analysis.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict

from ai_karen_engine.core.services.base import BaseService, ServiceConfig

from ..agent_safety_types import BehaviorData, PatternResult, RiskLevel

logger = logging.getLogger(__name__)


class PatternRecognizer(BaseService):
    """
    Pattern Recognizer for recognizing patterns in agent behavior.
    
    This class provides functionality to recognize patterns in agent behavior,
    including pattern detection, classification, and analysis.
    """
    
    def __init__(self, config: ServiceConfig):
        """Initialize the Pattern Recognizer."""
        super().__init__(config)
        self._initialized = False
        self._lock = asyncio.Lock()
        
        # Thread-safe data structures
        self._pattern_history: Dict[str, List[PatternResult]] = defaultdict(list)
        self._pattern_definitions: Dict[str, Dict[str, Any]] = {}
        
        # Configuration
        self._enable_pattern_learning = True
        self._enable_adaptive_patterns = True
        self._max_history_size = 1000
        self._pattern_confidence_threshold = 0.7
    
    async def initialize(self) -> None:
        """Initialize the Pattern Recognizer."""
        if self._initialized:
            return
            
        async with self._lock:
            try:
                # Initialize pattern definitions
                await self._load_pattern_definitions()
                
                self._initialized = True
                logger.info("Pattern Recognizer initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Pattern Recognizer: {e}")
                raise RuntimeError(f"Pattern Recognizer initialization failed: {e}")
    
    async def _load_pattern_definitions(self) -> None:
        """Load pattern definitions."""
        # Default pattern definitions
        self._pattern_definitions = {
            "high_cpu_usage": {
                "description": "High CPU usage pattern",
                "condition": lambda metrics: metrics.get("cpu_usage", 0) > 0.8,
                "severity": RiskLevel.MEDIUM_RISK,
                "category": "resource_usage"
            },
            "high_memory_usage": {
                "description": "High memory usage pattern",
                "condition": lambda metrics: metrics.get("memory_usage", 0) > 0.8,
                "severity": RiskLevel.MEDIUM_RISK,
                "category": "resource_usage"
            },
            "high_error_rate": {
                "description": "High error rate pattern",
                "condition": lambda metrics: metrics.get("error_rate", 0) > 0.1,
                "severity": RiskLevel.HIGH_RISK,
                "category": "error"
            },
            "low_task_completion": {
                "description": "Low task completion rate pattern",
                "condition": lambda metrics: metrics.get("task_completion_rate", 1.0) < 0.5,
                "severity": RiskLevel.MEDIUM_RISK,
                "category": "performance"
            },
            "high_interaction_frequency": {
                "description": "High interaction frequency pattern",
                "condition": lambda metrics: metrics.get("interaction_frequency", 0) > 10.0,
                "severity": RiskLevel.LOW_RISK,
                "category": "interaction"
            },
            "resource_spike": {
                "description": "Resource usage spike pattern",
                "condition": lambda metrics: any(
                    metrics.get(f"{resource}_spike", False) 
                    for resource in ["cpu", "memory", "disk", "network"]
                ),
                "severity": RiskLevel.MEDIUM_RISK,
                "category": "resource_usage"
            },
            "unusual_response_time": {
                "description": "Unusual response time pattern",
                "condition": lambda metrics: metrics.get("response_time", 0) > 5.0,
                "severity": RiskLevel.LOW_RISK,
                "category": "performance"
            }
        }
        
        logger.debug(f"Loaded {len(self._pattern_definitions)} pattern definitions")
    
    async def recognize_patterns(self, behavior_data: BehaviorData) -> List[PatternResult]:
        """
        Recognize patterns in agent behavior.
        
        Args:
            behavior_data: Behavior data to analyze
            
        Returns:
            List of pattern recognition results
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            pattern_results = []
            
            # Check each pattern definition
            for pattern_id, pattern_def in self._pattern_definitions.items():
                try:
                    # Check if pattern matches
                    condition_func = pattern_def["condition"]
                    pattern_detected = condition_func(behavior_data.metrics)
                    
                    if pattern_detected:
                        # Calculate confidence
                        confidence = await self._calculate_pattern_confidence(
                            behavior_data, pattern_id
                        )
                        
                        # Create pattern result
                        pattern_result = PatternResult(
                            pattern_detected=True,
                            pattern_type=pattern_def["category"],
                            pattern_id=pattern_id,
                            confidence=confidence,
                            severity=pattern_def["severity"],
                            description=pattern_def["description"]
                        )
                        
                        pattern_results.append(pattern_result)
                        
                        # Store in history
                        async with self._lock:
                            self._pattern_history[behavior_data.agent_id].append(pattern_result)
                            
                            # Limit history size
                            if len(self._pattern_history[behavior_data.agent_id]) > self._max_history_size:
                                self._pattern_history[behavior_data.agent_id] = self._pattern_history[behavior_data.agent_id][-self._max_history_size:]
                except Exception as e:
                    logger.error(f"Error checking pattern {pattern_id}: {e}")
            
            return pattern_results
        except Exception as e:
            logger.error(f"Error recognizing patterns: {e}")
            return []
    
    async def _calculate_pattern_confidence(
        self,
        behavior_data: BehaviorData,
        pattern_id: str
    ) -> float:
        """
        Calculate confidence for a pattern match.
        
        Args:
            behavior_data: Behavior data to analyze
            pattern_id: ID of the pattern
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        try:
            # Get pattern definition
            pattern_def = self._pattern_definitions.get(pattern_id, {})
            
            # Base confidence on how well the pattern matches
            if pattern_id == "high_cpu_usage":
                cpu_usage = behavior_data.metrics.get("cpu_usage", 0)
                return min((cpu_usage - 0.8) * 5, 1.0)  # Scale to 0.0-1.0
            
            elif pattern_id == "high_memory_usage":
                memory_usage = behavior_data.metrics.get("memory_usage", 0)
                return min((memory_usage - 0.8) * 5, 1.0)
            
            elif pattern_id == "high_error_rate":
                error_rate = behavior_data.metrics.get("error_rate", 0)
                return min(error_rate * 10, 1.0)
            
            elif pattern_id == "low_task_completion":
                completion_rate = behavior_data.metrics.get("task_completion_rate", 1.0)
                return min((1.0 - completion_rate) * 2, 1.0)
            
            elif pattern_id == "high_interaction_frequency":
                interaction_freq = behavior_data.metrics.get("interaction_frequency", 0)
                return min(interaction_freq / 20.0, 1.0)
            
            elif pattern_id == "resource_spike":
                # Check for resource spikes
                for resource in ["cpu", "memory", "disk", "network"]:
                    spike_metric = f"{resource}_spike"
                    if behavior_data.metrics.get(spike_metric, False):
                        return 0.9  # High confidence for spikes
                return 0.5  # Medium confidence if no specific spike found
            
            elif pattern_id == "unusual_response_time":
                response_time = behavior_data.metrics.get("response_time", 0)
                return min(response_time / 10.0, 1.0)
            
            else:
                return 0.5  # Default confidence
        except Exception as e:
            logger.error(f"Error calculating pattern confidence: {e}")
            return 0.5
    
    async def get_pattern_history(
        self,
        agent_id: str,
        pattern_type: Optional[str] = None,
        limit: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[PatternResult]:
        """
        Get pattern history for an agent.
        
        Args:
            agent_id: ID of the agent
            pattern_type: Optional pattern type to filter by
            limit: Maximum number of entries to return
            start_time: Optional start time for filtering
            end_time: Optional end time for filtering
            
        Returns:
            List of pattern results
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            async with self._lock:
                pattern_history = self._pattern_history.get(agent_id, [])
                
                # Filter by pattern type
                if pattern_type:
                    pattern_history = [
                        p for p in pattern_history
                        if p.pattern_type == pattern_type
                    ]
                
                # Filter by time range
                if start_time or end_time:
                    filtered_history = []
                    for pattern in pattern_history:
                        # Note: PatternResult doesn't have a timestamp field in the dataclass
                        # We'll need to add one or use a different approach
                        filtered_history.append(pattern)
                    pattern_history = filtered_history
                
                # Limit number of entries
                if limit and len(pattern_history) > limit:
                    pattern_history = pattern_history[-limit:]
                
                return pattern_history
        except Exception as e:
            logger.error(f"Error getting pattern history: {e}")
            return []
    
    async def add_pattern_definition(
        self,
        pattern_id: str,
        description: str,
        condition_func: callable,
        severity: RiskLevel = RiskLevel.LOW_RISK,
        category: str = "custom"
    ) -> bool:
        """
        Add a custom pattern definition.
        
        Args:
            pattern_id: ID of the pattern
            description: Description of the pattern
            condition_func: Function that returns True if pattern is detected
            severity: Severity level of the pattern
            category: Category of the pattern
            
        Returns:
            True if addition was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            async with self._lock:
                self._pattern_definitions[pattern_id] = {
                    "description": description,
                    "condition": condition_func,
                    "severity": severity,
                    "category": category
                }
            
            return True
        except Exception as e:
            logger.error(f"Error adding pattern definition: {e}")
            return False
    
    async def remove_pattern_definition(self, pattern_id: str) -> bool:
        """
        Remove a pattern definition.
        
        Args:
            pattern_id: ID of the pattern to remove
            
        Returns:
            True if removal was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            async with self._lock:
                if pattern_id in self._pattern_definitions:
                    del self._pattern_definitions[pattern_id]
                    return True
                return False
        except Exception as e:
            logger.error(f"Error removing pattern definition: {e}")
            return False
    
    async def get_pattern_definitions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all pattern definitions.
        
        Returns:
            Dictionary of pattern definitions
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            async with self._lock:
                return self._pattern_definitions.copy()
        except Exception as e:
            logger.error(f"Error getting pattern definitions: {e}")
            return {}
    
    async def clear_pattern_history(self, agent_id: Optional[str] = None) -> bool:
        """
        Clear pattern history.
        
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
                    self._pattern_history[agent_id].clear()
                else:
                    self._pattern_history.clear()
            
            return True
        except Exception as e:
            logger.error(f"Error clearing pattern history: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check health of the Pattern Recognizer."""
        if not self._initialized:
            return False
            
        try:
            # Check if pattern recognition is enabled
            if not self._enable_pattern_learning:
                return False
            
            # Check if pattern definitions are loaded
            if not self._pattern_definitions:
                return False
            
            return True
        except Exception as e:
            logger.error(f"Pattern Recognizer health check failed: {e}")
            return False
    
    async def start(self) -> None:
        """Start the Pattern Recognizer."""
        if not self._initialized:
            await self.initialize()
        
        logger.info("Pattern Recognizer started successfully")
    
    async def stop(self) -> None:
        """Stop the Pattern Recognizer."""
        if not self._initialized:
            return
        
        # Clear data structures
        async with self._lock:
            self._pattern_history.clear()
            self._pattern_definitions.clear()
        
        # Reset initialization state
        self._initialized = False
        
        logger.info("Pattern Recognizer stopped successfully")
