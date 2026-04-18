"""
Behavior Tracker module for tracking agent behavior.

This module provides functionality to track agent behavior,
including behavior data collection, storage, and retrieval.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from collections import defaultdict

from ai_karen_engine.core.services.base import BaseService, ServiceConfig

from ..agent_safety_types import BehaviorData

logger = logging.getLogger(__name__)


class BehaviorTracker(BaseService):
    """
    Behavior Tracker for tracking agent behavior.
    
    This class provides functionality to track agent behavior,
    including behavior data collection, storage, and retrieval.
    """
    
    def __init__(self, config: ServiceConfig):
        """Initialize the Behavior Tracker."""
        super().__init__(config)
        self._initialized = False
        self._lock = asyncio.Lock()
        
        # Thread-safe data structures
        self._behavior_data: Dict[str, List[BehaviorData]] = defaultdict(list)
        
        # Configuration
        self._max_entries_per_agent = 1000
        self._enable_real_time_tracking = True
        self._enable_persistence = True
    
    async def initialize(self) -> None:
        """Initialize the Behavior Tracker."""
        if self._initialized:
            return
            
        async with self._lock:
            try:
                # Initialize behavior tracking
                logger.debug("Behavior Tracker initialized")
                
                self._initialized = True
                logger.info("Behavior Tracker initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Behavior Tracker: {e}")
                raise RuntimeError(f"Behavior Tracker initialization failed: {e}")
    
    async def track_behavior(self, behavior_data: BehaviorData) -> bool:
        """
        Track agent behavior.
        
        Args:
            behavior_data: Behavior data to track
            
        Returns:
            True if tracking was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            async with self._lock:
                # Add behavior data to agent's history
                self._behavior_data[behavior_data.agent_id].append(behavior_data)
                
                # Limit history size
                if len(self._behavior_data[behavior_data.agent_id]) > self._max_entries_per_agent:
                    self._behavior_data[behavior_data.agent_id] = self._behavior_data[behavior_data.agent_id][-self._max_entries_per_agent:]
            
            return True
        except Exception as e:
            logger.error(f"Error tracking behavior: {e}")
            return False
    
    async def get_behavior_data(
        self,
        agent_id: str,
        limit: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[BehaviorData]:
        """
        Get behavior data for an agent.
        
        Args:
            agent_id: ID of the agent
            limit: Maximum number of entries to return
            start_time: Optional start time for filtering
            end_time: Optional end time for filtering
            
        Returns:
            List of behavior data
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            async with self._lock:
                behavior_data = self._behavior_data.get(agent_id, [])
                
                # Filter by time range
                if start_time or end_time:
                    filtered_data = []
                    for data in behavior_data:
                        if start_time and data.timestamp < start_time:
                            continue
                        if end_time and data.timestamp > end_time:
                            continue
                        filtered_data.append(data)
                    behavior_data = filtered_data
                
                # Limit number of entries
                if limit and len(behavior_data) > limit:
                    behavior_data = behavior_data[-limit:]
                
                return behavior_data
        except Exception as e:
            logger.error(f"Error getting behavior data: {e}")
            return []
    
    async def get_latest_behavior_data(self, agent_id: str) -> Optional[BehaviorData]:
        """
        Get the latest behavior data for an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Latest behavior data if found, None otherwise
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            async with self._lock:
                behavior_data = self._behavior_data.get(agent_id, [])
                return behavior_data[-1] if behavior_data else None
        except Exception as e:
            logger.error(f"Error getting latest behavior data: {e}")
            return None
    
    async def clear_behavior_data(self, agent_id: Optional[str] = None) -> bool:
        """
        Clear behavior data.
        
        Args:
            agent_id: Optional agent ID to clear data for. If None, clears all data.
            
        Returns:
            True if clearing was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            async with self._lock:
                if agent_id:
                    self._behavior_data[agent_id].clear()
                else:
                    self._behavior_data.clear()
            
            return True
        except Exception as e:
            logger.error(f"Error clearing behavior data: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check health of the Behavior Tracker."""
        if not self._initialized:
            return False
            
        try:
            # Check if behavior tracking is enabled
            if not self._enable_real_time_tracking:
                return False
            
            return True
        except Exception as e:
            logger.error(f"Behavior Tracker health check failed: {e}")
            return False
    
    async def start(self) -> None:
        """Start the Behavior Tracker."""
        if not self._initialized:
            await self.initialize()
        
        logger.info("Behavior Tracker started successfully")
    
    async def stop(self) -> None:
        """Stop the Behavior Tracker."""
        if not self._initialized:
            return
        
        # Clear data structures
        async with self._lock:
            self._behavior_data.clear()
        
        # Reset initialization state
        self._initialized = False
        
        logger.info("Behavior Tracker stopped successfully")
