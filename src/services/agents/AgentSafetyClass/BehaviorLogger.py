"""
Behavior Logger module for logging agent behavior.

This module provides functionality to log agent behavior,
including log storage, retrieval, and analysis.
"""

import asyncio
import logging
import json
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path

from ai_karen_engine.core.services.base import BaseService, ServiceConfig

from ..agent_safety_types import BehaviorData

logger = logging.getLogger(__name__)


class BehaviorLogger(BaseService):
    """
    Behavior Logger for logging agent behavior.
    
    This class provides functionality to log agent behavior,
    including log storage, retrieval, and analysis.
    """
    
    def __init__(self, config: ServiceConfig):
        """Initialize the Behavior Logger."""
        super().__init__(config)
        self._initialized = False
        self._lock = asyncio.Lock()
        
        # Thread-safe data structures
        self._behavior_logs: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._log_file_path: Optional[str] = None
        
        # Configuration
        self._enable_file_logging = True
        self._enable_memory_logging = True
        self._log_rotation_size = 10485760  # 10MB
        self._max_logs_in_memory = 10000
        self._log_retention_days = 30
        self._log_format = "json"
    
    async def initialize(self) -> None:
        """Initialize the Behavior Logger."""
        if self._initialized:
            return
            
        async with self._lock:
            try:
                # Initialize log file path
                if self._enable_file_logging:
                    log_dir = Path("logs/agent_behavior")
                    log_dir.mkdir(parents=True, exist_ok=True)
                    self._log_file_path = str(log_dir / "agent_behavior.log")
                
                self._initialized = True
                logger.info("Behavior Logger initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Behavior Logger: {e}")
                raise RuntimeError(f"Behavior Logger initialization failed: {e}")
    
    async def log_behavior_data(self, behavior_data: BehaviorData) -> bool:
        """
        Log agent behavior data.
        
        Args:
            behavior_data: Behavior data to log
            
        Returns:
            True if logging was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            # Create log entry
            log_entry = {
                "timestamp": behavior_data.timestamp.isoformat(),
                "agent_id": behavior_data.agent_id,
                "metrics": behavior_data.metrics,
                "resource_usage": behavior_data.resource_usage,
                "response_patterns": behavior_data.response_patterns,
                "interaction_patterns": behavior_data.interaction_patterns,
                "metadata": behavior_data.metadata
            }
            
            # Log to memory
            if self._enable_memory_logging:
                async with self._lock:
                    self._behavior_logs[behavior_data.agent_id].append(log_entry)
                    
                    # Limit logs in memory
                    if len(self._behavior_logs[behavior_data.agent_id]) > self._max_logs_in_memory:
                        self._behavior_logs[behavior_data.agent_id] = self._behavior_logs[behavior_data.agent_id][-self._max_logs_in_memory:]
            
            # Log to file
            if self._enable_file_logging and self._log_file_path:
                await self._log_to_file(log_entry)
            
            return True
        except Exception as e:
            logger.error(f"Error logging behavior data: {e}")
            return False
    
    async def _log_to_file(self, log_entry: Dict[str, Any]) -> None:
        """
        Log entry to file.
        
        Args:
            log_entry: Log entry to write
        """
        try:
            # Format log entry
            if self._log_format == "json":
                log_line = json.dumps(log_entry)
            else:
                # Simple text format
                log_line = (
                    f"{log_entry['timestamp']} - {log_entry['agent_id']} - "
                    f"Metrics: {log_entry['metrics']} - "
                    f"Resources: {log_entry['resource_usage']}"
                )
            
            # Write to file
            if self._log_file_path:
                with open(self._log_file_path, "a", encoding="utf-8") as f:
                    f.write(log_line + "\n")
                
                # Check if log rotation is needed
                if Path(self._log_file_path).stat().st_size > self._log_rotation_size:
                    await self._rotate_log_file()
        except Exception as e:
            logger.error(f"Error writing to log file: {e}")
    
    async def _rotate_log_file(self) -> None:
        """Rotate log file when it gets too large."""
        try:
            if not self._log_file_path:
                return
            
            log_path = Path(self._log_file_path)
            if not log_path.exists():
                return
            
            # Create backup filename with timestamp
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_path = log_path.with_suffix(f".log.{timestamp}")
            
            # Rename current log file to backup
            log_path.rename(backup_path)
            
            # Clean up old log files
            await self._cleanup_old_log_files()
        except Exception as e:
            logger.error(f"Error rotating log file: {e}")
    
    async def _cleanup_old_log_files(self) -> None:
        """Clean up old log files."""
        try:
            if not self._log_file_path:
                return
            
            log_dir = Path(self._log_file_path).parent
            if not log_dir.exists():
                return
            
            # Get cutoff time
            cutoff_time = datetime.utcnow() - timedelta(days=self._log_retention_days)
            
            # Remove old log files
            for log_file in log_dir.glob("*.log.*"):
                try:
                    # Extract timestamp from filename
                    timestamp_str = log_file.suffix.replace(".log.", "")
                    file_time = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    
                    # Remove if older than retention period
                    if file_time < cutoff_time:
                        log_file.unlink()
                except Exception:
                    # Skip files that don't match expected format
                    continue
        except Exception as e:
            logger.error(f"Error cleaning up old log files: {e}")
    
    async def get_behavior_logs(
        self,
        agent_id: str,
        limit: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get behavior logs for an agent.
        
        Args:
            agent_id: ID of the agent
            limit: Maximum number of entries to return
            start_time: Optional start time for filtering
            end_time: Optional end time for filtering
            
        Returns:
            List of behavior log entries
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            async with self._lock:
                logs = self._behavior_logs.get(agent_id, [])
                
                # Filter by time range
                if start_time or end_time:
                    filtered_logs = []
                    for log in logs:
                        log_time = datetime.fromisoformat(log["timestamp"])
                        if start_time and log_time < start_time:
                            continue
                        if end_time and log_time > end_time:
                            continue
                        filtered_logs.append(log)
                    logs = filtered_logs
                
                # Limit number of entries
                if limit and len(logs) > limit:
                    logs = logs[-limit:]
                
                return logs
        except Exception as e:
            logger.error(f"Error getting behavior logs: {e}")
            return []
    
    async def get_behavior_logs_from_file(
        self,
        agent_id: str,
        limit: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get behavior logs for an agent from file.
        
        Args:
            agent_id: ID of the agent
            limit: Maximum number of entries to return
            start_time: Optional start time for filtering
            end_time: Optional end time for filtering
            
        Returns:
            List of behavior log entries
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            if not self._enable_file_logging or not self._log_file_path:
                return []
            
            logs = []
            
            # Read from current log file
            try:
                with open(self._log_file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            log_entry = json.loads(line.strip())
                            if log_entry.get("agent_id") == agent_id:
                                logs.append(log_entry)
                        except json.JSONDecodeError:
                            # Skip invalid JSON lines
                            continue
            except FileNotFoundError:
                # Log file doesn't exist yet
                pass
            
            # Read from backup log files if needed
            if not logs or (start_time and logs[0].get("timestamp") > start_time.isoformat()):
                log_dir = Path(self._log_file_path).parent
                if log_dir.exists():
                    # Get all backup log files, sorted by modification time (newest first)
                    backup_files = sorted(
                        log_dir.glob("*.log.*"),
                        key=lambda x: x.stat().st_mtime,
                        reverse=True
                    )
                    
                    for backup_file in backup_files:
                        try:
                            with open(backup_file, "r", encoding="utf-8") as f:
                                for line in f:
                                    try:
                                        log_entry = json.loads(line.strip())
                                        if log_entry.get("agent_id") == agent_id:
                                            logs.append(log_entry)
                                    except json.JSONDecodeError:
                                        # Skip invalid JSON lines
                                        continue
                            
                            # Check if we have enough logs or have reached start_time
                            if limit and len(logs) >= limit:
                                break
                            if start_time:
                                earliest_log = min(logs, key=lambda x: x["timestamp"])
                                if datetime.fromisoformat(earliest_log["timestamp"]) <= start_time:
                                    break
                        except Exception as e:
                            logger.error(f"Error reading backup log file {backup_file}: {e}")
                            continue
            
            # Filter by time range
            if start_time or end_time:
                filtered_logs = []
                for log in logs:
                    log_time = datetime.fromisoformat(log["timestamp"])
                    if start_time and log_time < start_time:
                        continue
                    if end_time and log_time > end_time:
                        continue
                    filtered_logs.append(log)
                logs = filtered_logs
            
            # Sort by timestamp
            logs.sort(key=lambda x: x["timestamp"])
            
            # Limit number of entries
            if limit and len(logs) > limit:
                logs = logs[-limit:]
            
            return logs
        except Exception as e:
            logger.error(f"Error getting behavior logs from file: {e}")
            return []
    
    async def get_all_behavior_logs(
        self,
        limit: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get behavior logs for all agents.
        
        Args:
            limit: Maximum number of entries to return per agent
            start_time: Optional start time for filtering
            end_time: Optional end time for filtering
            
        Returns:
            Dictionary mapping agent IDs to lists of behavior log entries
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            async with self._lock:
                all_logs = {}
                
                for agent_id, logs in self._behavior_logs.items():
                    # Filter by time range
                    if start_time or end_time:
                        filtered_logs = []
                        for log in logs:
                            log_time = datetime.fromisoformat(log["timestamp"])
                            if start_time and log_time < start_time:
                                continue
                            if end_time and log_time > end_time:
                                continue
                            filtered_logs.append(log)
                        logs = filtered_logs
                    
                    # Limit number of entries
                    if limit and len(logs) > limit:
                        logs = logs[-limit:]
                    
                    all_logs[agent_id] = logs
                
                return all_logs
        except Exception as e:
            logger.error(f"Error getting all behavior logs: {e}")
            return {}
    
    async def clear_behavior_logs(self, agent_id: Optional[str] = None) -> bool:
        """
        Clear behavior logs.
        
        Args:
            agent_id: Optional agent ID to clear logs for. If None, clears all logs.
            
        Returns:
            True if clearing was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            async with self._lock:
                if agent_id:
                    self._behavior_logs[agent_id].clear()
                else:
                    self._behavior_logs.clear()
            
            return True
        except Exception as e:
            logger.error(f"Error clearing behavior logs: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check health of the Behavior Logger."""
        if not self._initialized:
            return False
            
        try:
            # Check if at least one logging method is enabled
            if not self._enable_file_logging and not self._enable_memory_logging:
                return False
            
            # Check if log file is accessible if file logging is enabled
            if self._enable_file_logging and self._log_file_path:
                log_dir = Path(self._log_file_path).parent
                if not log_dir.exists():
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Behavior Logger health check failed: {e}")
            return False
    
    async def start(self) -> None:
        """Start the Behavior Logger."""
        if not self._initialized:
            await self.initialize()
        
        logger.info("Behavior Logger started successfully")
    
    async def stop(self) -> None:
        """Stop the Behavior Logger."""
        if not self._initialized:
            return
        
        # Clear data structures
        async with self._lock:
            self._behavior_logs.clear()
        
        # Reset initialization state
        self._initialized = False
        
        logger.info("Behavior Logger stopped successfully")
    
    async def log_analysis_result(self, analysis_result: Any) -> None:
        """
        Log analysis result.
        
        Args:
            analysis_result: Analysis result to log
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Create log entry
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "type": "analysis_result",
                "data": analysis_result
            }
            
            # Log to memory
            if self._enable_memory_logging:
                async with self._lock:
                    self._behavior_logs["system"].append(log_entry)
            
            # Log to file
            if self._enable_file_logging and self._log_file_path:
                await self._log_to_file(log_entry)
        except Exception as e:
            logger.error(f"Error logging analysis result: {e}")
    
    async def log_event(
        self,
        event_type: str = "event",
        event_data: Optional[Dict[str, Any]] = None,
        component: Optional[str] = None,
        level: Optional[str] = None,
        message: Optional[str] = None,
        agent_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log event.
        
        Args:
            event_type: Type of event
            event_data: Event data to log
            component: Component that generated the event
            level: Log level
            message: Log message
            agent_id: Agent ID
            data: Additional data
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Create log entry
            log_entry: Dict[str, Union[str, Dict[str, Any]]] = {
                "timestamp": datetime.utcnow().isoformat(),
                "type": "event",
                "event_type": event_type
            }
            
            # Add optional parameters if provided
            if event_data:
                log_entry["event_data"] = event_data
            if component:
                log_entry["component"] = component
            if level:
                log_entry["level"] = level
            if message:
                log_entry["message"] = message
            if agent_id:
                log_entry["agent_id"] = agent_id
            if data:
                log_entry["data"] = data
            
            # Log to memory
            if self._enable_memory_logging:
                async with self._lock:
                    self._behavior_logs["system"].append(log_entry)
            
            # Log to file
            if self._enable_file_logging and self._log_file_path:
                await self._log_to_file(log_entry)
        except Exception as e:
            logger.error(f"Error logging event: {e}")
    
    async def get_agent_logs(
        self,
        agent_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_type: Optional[str] = None,
        level: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get logs for a specific agent.
        
        Args:
            agent_id: ID of the agent
            start_time: Optional start time for filtering
            end_time: Optional end time for filtering
            event_type: Optional event type for filtering
            level: Optional log level for filtering
            limit: Optional limit on number of logs to return
            
        Returns:
            List of log entries
        """
        return await self.get_behavior_logs(agent_id, limit, start_time, end_time)
    
    async def get_all_logs(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_type: Optional[str] = None,
        level: Optional[str] = None,
        agent_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all logs.
        
        Args:
            start_time: Optional start time for filtering
            end_time: Optional end time for filtering
            event_type: Optional event type for filtering
            level: Optional log level for filtering
            agent_id: Optional agent ID for filtering
            limit: Optional limit on number of logs to return
            
        Returns:
            List of log entries
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            all_logs = []
            
            async with self._lock:
                # Get logs for all agents
                for agent_id_key, logs in self._behavior_logs.items():
                    if agent_id and agent_id_key != agent_id:
                        continue
                    
                    # Filter by time range
                    if start_time or end_time:
                        filtered_logs = []
                        for log in logs:
                            log_time = datetime.fromisoformat(log["timestamp"])
                            if start_time and log_time < start_time:
                                continue
                            if end_time and log_time > end_time:
                                continue
                            filtered_logs.append(log)
                        logs = filtered_logs
                    
                    # Add to all logs
                    all_logs.extend(logs)
            
            # Sort by timestamp
            all_logs.sort(key=lambda x: x["timestamp"])
            
            # Limit number of entries
            if limit and len(all_logs) > limit:
                all_logs = all_logs[-limit:]
            
            return all_logs
        except Exception as e:
            logger.error(f"Error getting all logs: {e}")
            return []
    
    def set_log_file_path(self, log_file_path: str) -> None:
        """
        Set log file path.
        
        Args:
            log_file_path: Path to log file
        """
        self._log_file_path = log_file_path
    
    def set_log_level(self, log_level: str) -> None:
        """
        Set log level.
        
        Args:
            log_level: Log level to set
        """
        # Implementation would depend on logging framework
        pass
    
    def set_detailed_logging(self, detailed_logging: bool) -> None:
        """
        Set detailed logging.
        
        Args:
            detailed_logging: Whether to enable detailed logging
        """
        # Implementation would depend on logging framework
        pass
    
    def set_max_log_size(self, max_log_size: int) -> None:
        """
        Set maximum log size.
        
        Args:
            max_log_size: Maximum log size in bytes
        """
        self._log_rotation_size = max_log_size
    
    def set_log_backup_count(self, log_backup_count: int) -> None:
        """
        Set log backup count.
        
        Args:
            log_backup_count: Number of log backups to keep
        """
        # Implementation would depend on logging framework
        pass
    
    def set_log_rotation(self, log_rotation: bool) -> None:
        """
        Set log rotation.
        
        Args:
            log_rotation: Whether to enable log rotation
        """
        # Implementation would depend on logging framework
        pass
