"""
Session State Manager for CoPilot integration.

This module handles persistence and retrieval of session state across
CoPilot and LangGraph, saving to both LangGraph checkpoints
and Unified Memory Service for long-term persistence.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class SessionStateManager:
    """
    Manages session state across CoPilot and LangGraph.
    
    Saves state to both LangGraph checkpoints and Unified Memory
    Service for long-term persistence.
    """
    
    def __init__(self, thread_manager=None, memory_service=None):
        """Initialize session state manager with dependencies."""
        self.thread_manager = thread_manager
        self.memory_service = memory_service
        
        # In-memory session state (in production, this would be persistent)
        self._session_state: Dict[str, Dict[str, Any]] = {}
        
        # State change callbacks
        self._state_callbacks: Dict[str, list] = {}
        
        logger.info("Session State Manager initialized")
    
    async def save_session_state(self, copilot_session_id: str, state: Dict[str, Any]) -> bool:
        """
        Save session state to both LangGraph and UMS.
        
        Args:
            copilot_session_id: CoPilot session ID
            state: Session state data
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            logger.info(f"Saving session state for {copilot_session_id}")
            
            # Store in memory
            self._session_state[copilot_session_id] = {
                "state": state.copy(),
                "saved_at": datetime.utcnow(),
                "version": self._get_state_version(state)
            }
            
            # Get LangGraph thread ID
            langgraph_thread_id = None
            if self.thread_manager:
                langgraph_thread_id = await self.thread_manager.get_langgraph_thread(copilot_session_id)
            
            # Save to LangGraph checkpoint if available
            if langgraph_thread_id:
                await self._save_to_langgraph_checkpoint(langgraph_thread_id, state)
            
            # Save important state to UMS for long-term persistence
            await self._save_to_memory_service(copilot_session_id, state)
            
            # Trigger state change callbacks
            await self._trigger_state_callbacks(copilot_session_id, "save", state)
            
            logger.info(f"Session state saved successfully for {copilot_session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving session state for {copilot_session_id}: {e}", exc_info=True)
            return False
    
    async def load_session_state(self, copilot_session_id: str) -> Optional[Dict[str, Any]]:
        """
        Load session state from LangGraph or UMS.
        
        Args:
            copilot_session_id: CoPilot session ID
            
        Returns:
            Session state data or None if not found
        """
        try:
            logger.info(f"Loading session state for {copilot_session_id}")
            
            # Check in-memory first
            if copilot_session_id in self._session_state:
                logger.debug(f"Session state found in memory for {copilot_session_id}")
                return self._session_state[copilot_session_id]["state"]
            
            # Get LangGraph thread ID
            langgraph_thread_id = None
            if self.thread_manager:
                langgraph_thread_id = await self.thread_manager.get_langgraph_thread(copilot_session_id)
            
            # Try to load from LangGraph checkpoint first
            if langgraph_thread_id:
                state = await self._load_from_langgraph_checkpoint(langgraph_thread_id)
                if state:
                    # Cache in memory
                    self._session_state[copilot_session_id] = {
                        "state": state,
                        "loaded_at": datetime.utcnow(),
                        "version": self._get_state_version(state),
                        "source": "langgraph"
                    }
                    logger.info(f"Session state loaded from LangGraph for {copilot_session_id}")
                    return state
            
            # Fall back to UMS
            state = await self._load_from_memory_service(copilot_session_id)
            if state:
                # Cache in memory
                self._session_state[copilot_session_id] = {
                    "state": state,
                    "loaded_at": datetime.utcnow(),
                    "version": self._get_state_version(state),
                    "source": "memory"
                }
                logger.info(f"Session state loaded from memory for {copilot_session_id}")
                return state
            
            logger.warning(f"Session state not found for {copilot_session_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error loading session state for {copilot_session_id}: {e}", exc_info=True)
            return None
    
    async def delete_session_state(self, copilot_session_id: str) -> bool:
        """
        Delete session state from all storage locations.
        
        Args:
            copilot_session_id: CoPilot session ID
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            logger.info(f"Deleting session state for {copilot_session_id}")
            
            # Remove from memory
            if copilot_session_id in self._session_state:
                del self._session_state[copilot_session_id]
            
            # Get LangGraph thread ID
            langgraph_thread_id = None
            if self.thread_manager:
                langgraph_thread_id = await self.thread_manager.get_langgraph_thread(copilot_session_id)
            
            # Delete from LangGraph checkpoint if available
            if langgraph_thread_id:
                await self._delete_from_langgraph_checkpoint(langgraph_thread_id)
            
            # Delete from UMS
            await self._delete_from_memory_service(copilot_session_id)
            
            # Trigger state change callbacks
            await self._trigger_state_callbacks(copilot_session_id, "delete", None)
            
            logger.info(f"Session state deleted successfully for {copilot_session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting session state for {copilot_session_id}: {e}", exc_info=True)
            return False
    
    async def update_session_state(self, copilot_session_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update specific fields in session state.
        
        Args:
            copilot_session_id: CoPilot session ID
            updates: Dictionary of field updates
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            # Load current state
            current_state = await self.load_session_state(copilot_session_id)
            if not current_state:
                logger.warning(f"No current state found for {copilot_session_id}")
                return False
            
            # Apply updates
            current_state.update(updates)
            
            # Save updated state
            return await self.save_session_state(copilot_session_id, current_state)
            
        except Exception as e:
            logger.error(f"Error updating session state for {copilot_session_id}: {e}", exc_info=True)
            return False
    
    async def get_session_state_field(self, copilot_session_id: str, field_path: str) -> Any:
        """
        Get a specific field from session state using dot notation.
        
        Args:
            copilot_session_id: CoPilot session ID
            field_path: Dot-separated path to field (e.g., "user.preferences.theme")
            
        Returns:
            Field value or None if not found
        """
        try:
            state = await self.load_session_state(copilot_session_id)
            if not state:
                return None
            
            # Navigate using dot notation
            keys = field_path.split('.')
            value = state
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return None
            
            return value
            
        except Exception as e:
            logger.error(f"Error getting session state field {field_path} for {copilot_session_id}: {e}", exc_info=True)
            return None
    
    async def set_session_state_field(self, copilot_session_id: str, field_path: str, value: Any) -> bool:
        """
        Set a specific field in session state using dot notation.
        
        Args:
            copilot_session_id: CoPilot session ID
            field_path: Dot-separated path to field (e.g., "user.preferences.theme")
            value: Value to set
            
        Returns:
            True if set successfully, False otherwise
        """
        try:
            # Load current state
            state = await self.load_session_state(copilot_session_id)
            if not state:
                state = {}
            
            # Navigate using dot notation
            keys = field_path.split('.')
            current = state
            
            # Navigate to parent of target field
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                elif not isinstance(current[key], dict):
                    current[key] = {}
                current = current[key]
            
            # Set the final value
            current[keys[-1]] = value
            
            # Save updated state
            return await self.save_session_state(copilot_session_id, state)
            
        except Exception as e:
            logger.error(f"Error setting session state field {field_path} for {copilot_session_id}: {e}", exc_info=True)
            return False
    
    def register_state_callback(self, event_type: str, callback):
        """
        Register a callback for state change events.
        
        Args:
            event_type: Type of event ("save", "load", "delete", "update")
            callback: Async callback function
        """
        if event_type not in self._state_callbacks:
            self._state_callbacks[event_type] = []
        
        self._state_callbacks[event_type].append(callback)
        logger.debug(f"Registered callback for {event_type} events")
    
    def unregister_state_callback(self, event_type: str, callback):
        """
        Unregister a state change callback.
        
        Args:
            event_type: Type of event
            callback: Callback function to remove
        """
        if (event_type in self._state_callbacks and 
            callback in self._state_callbacks[event_type]):
            self._state_callbacks[event_type].remove(callback)
            logger.debug(f"Unregistered callback for {event_type} events")
    
    async def _save_to_langgraph_checkpoint(self, thread_id: str, state: Dict[str, Any]) -> None:
        """Save state to LangGraph checkpoint."""
        # In real implementation, this would use LangGraph checkpoint API
        logger.debug(f"Saving state to LangGraph checkpoint {thread_id}")
        # Simulate checkpoint save
        pass
    
    async def _load_from_langgraph_checkpoint(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Load state from LangGraph checkpoint."""
        # In real implementation, this would use LangGraph checkpoint API
        logger.debug(f"Loading state from LangGraph checkpoint {thread_id}")
        # Simulate checkpoint load
        return None
    
    async def _delete_from_langgraph_checkpoint(self, thread_id: str) -> None:
        """Delete state from LangGraph checkpoint."""
        # In real implementation, this would use LangGraph checkpoint API
        logger.debug(f"Deleting state from LangGraph checkpoint {thread_id}")
        # Simulate checkpoint delete
        pass
    
    async def _save_to_memory_service(self, session_id: str, state: Dict[str, Any]) -> None:
        """Save state to Unified Memory Service."""
        if not self.memory_service:
            logger.debug("No memory service available, skipping memory save")
            return
        
        # Filter and save important state elements
        important_state = {
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "version": self._get_state_version(state),
            # Save key state elements
            "tasks": state.get("tasks", []),
            "files_accessed": state.get("files_accessed", []),
            "key_results": state.get("key_results", []),
            "user_preferences": state.get("user_preferences", {}),
            "conversation_context": state.get("conversation_context", {}),
            "execution_history": state.get("execution_history", [])
        }
        
        try:
            # In real implementation, this would call memory service
            logger.debug(f"Saving state to memory service for session {session_id}")
            # Simulate memory save
            pass
        except Exception as e:
            logger.error(f"Error saving to memory service: {e}", exc_info=True)
    
    async def _load_from_memory_service(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load state from Unified Memory Service."""
        if not self.memory_service:
            logger.debug("No memory service available, skipping memory load")
            return None
        
        try:
            # In real implementation, this would call memory service
            logger.debug(f"Loading state from memory service for session {session_id}")
            # Simulate memory load
            return None
        except Exception as e:
            logger.error(f"Error loading from memory service: {e}", exc_info=True)
            return None
    
    async def _delete_from_memory_service(self, session_id: str) -> None:
        """Delete state from Unified Memory Service."""
        if not self.memory_service:
            logger.debug("No memory service available, skipping memory delete")
            return
        
        try:
            # In real implementation, this would call memory service
            logger.debug(f"Deleting state from memory service for session {session_id}")
            # Simulate memory delete
            pass
        except Exception as e:
            logger.error(f"Error deleting from memory service: {e}", exc_info=True)
    
    def _get_state_version(self, state: Dict[str, Any]) -> str:
        """Generate a version hash for state."""
        # Simple version based on state keys and size
        state_str = json.dumps(sorted(state.keys()), sort_keys=True)
        return f"v1_{hash(state_str) % 10000}"
    
    async def _trigger_state_callbacks(self, session_id: str, event_type: str, data: Any) -> None:
        """Trigger registered callbacks for state events."""
        if event_type in self._state_callbacks:
            for callback in self._state_callbacks[event_type]:
                try:
                    await callback(session_id, event_type, data)
                except Exception as e:
                    logger.error(f"Error in state callback for {event_type}: {e}", exc_info=True)
    
    async def cleanup_old_states(self, max_age_days: int = 30) -> int:
        """
        Clean up old session states.
        
        Args:
            max_age_days: Maximum age in days before cleanup
            
        Returns:
            Number of states cleaned up
        """
        cutoff_time = datetime.utcnow() - timedelta(days=max_age_days)
        cleaned_count = 0
        
        # Find old states
        old_sessions = []
        for session_id, state_data in self._session_state.items():
            saved_at = state_data.get("saved_at")
            if saved_at and saved_at < cutoff_time:
                old_sessions.append(session_id)
        
        # Clean up old states
        for session_id in old_sessions:
            if await self.delete_session_state(session_id):
                cleaned_count += 1
        
        logger.info(f"Cleaned up {cleaned_count} old session states (older than {max_age_days} days)")
        return cleaned_count
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about managed session states.
        
        Returns:
            Dictionary with session statistics
        """
        total_sessions = len(self._session_state)
        
        # Calculate session age statistics
        now = datetime.utcnow()
        ages = []
        sources = []
        
        for state_data in self._session_state.values():
            saved_at = state_data.get("saved_at")
            if saved_at:
                age_days = (now - saved_at).days
                ages.append(age_days)
            
            source = state_data.get("source", "memory")
            sources.append(source)
        
        avg_age = sum(ages) / len(ages) if ages else 0
        max_age = max(ages) if ages else 0
        min_age = min(ages) if ages else 0
        
        # Source statistics
        source_counts = {}
        for source in sources:
            source_counts[source] = source_counts.get(source, 0) + 1
        
        return {
            "total_sessions": total_sessions,
            "average_age_days": avg_age,
            "oldest_session_days": max_age,
            "newest_session_days": min_age,
            "source_distribution": source_counts,
            "memory_usage_mb": len(json.dumps(self._session_state)) / (1024 * 1024)  # Rough estimate
        }