"""
Ingestion Pipeline - Orchestrates knowledge connectors

This module orchestrates multiple knowledge connectors for comprehensive
knowledge ingestion with scheduling, error handling, and progress tracking.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Type, Set
from dataclasses import dataclass, field
from enum import Enum
import json

from .base_connector import BaseConnector, ConnectorType, IngestionResult
from .file_connector import FileConnector
from .git_connector import GitConnector
from .database_connector import DatabaseConnector
from .documentation_connector import DocumentationConnector

try:
    from llama_index.core import Document
except ImportError:
    Document = None


class PipelineStatus(Enum):
    """Status of the ingestion pipeline."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    COMPLETED = "completed"


class ScheduleType(Enum):
    """Types of ingestion schedules."""
    MANUAL = "manual"
    INTERVAL = "interval"
    CRON = "cron"
    CONTINUOUS = "continuous"


@dataclass
class ConnectorConfig:
    """Configuration for a connector in the pipeline."""
    connector_id: str
    connector_type: ConnectorType
    config: Dict[str, Any]
    enabled: bool = True
    priority: int = 1  # Lower numbers = higher priority
    schedule: Optional[Dict[str, Any]] = None
    dependencies: List[str] = field(default_factory=list)  # Other connector IDs


@dataclass
class PipelineRun:
    """Represents a single pipeline execution."""
    run_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: PipelineStatus = PipelineStatus.RUNNING
    
    # Results
    connector_results: Dict[str, IngestionResult] = field(default_factory=dict)
    total_documents: int = 0
    total_errors: int = 0
    
    # Metadata
    trigger: str = "manual"  # manual, scheduled, change_detected
    metadata: Dict[str, Any] = field(default_factory=dict)


class IngestionPipeline:
    """
    Orchestrates multiple knowledge connectors for comprehensive
    knowledge ingestion with scheduling and error handling.
    """
    
    def __init__(self, index_hub, config: Dict[str, Any]):
        self.index_hub = index_hub
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Pipeline configuration
        self.pipeline_id = config.get("pipeline_id", "default")
        self.max_concurrent_connectors = config.get("max_concurrent_connectors", 3)
        self.error_retry_attempts = config.get("error_retry_attempts", 3)
        self.error_retry_delay = config.get("error_retry_delay", 60)  # seconds
        
        # Connectors
        self.connectors: Dict[str, BaseConnector] = {}
        self.connector_configs: Dict[str, ConnectorConfig] = {}
        
        # Pipeline state
        self.status = PipelineStatus.IDLE
        self.current_run: Optional[PipelineRun] = None
        self.run_history: List[PipelineRun] = []
        self.max_history_size = config.get("max_history_size", 100)
        
        # Scheduling
        self.scheduler_enabled = config.get("scheduler_enabled", False)
        self.default_schedule = config.get("default_schedule", {"type": "manual"})
        
        # Background tasks
        self.scheduler_task: Optional[asyncio.Task] = None
        self.change_monitor_task: Optional[asyncio.Task] = None
        
        # Connector type mapping
        self.connector_classes: Dict[ConnectorType, Type[BaseConnector]] = {
            ConnectorType.FILE: FileConnector,
            ConnectorType.GIT: GitConnector,
            ConnectorType.DATABASE: DatabaseConnector,
            ConnectorType.DOCUMENTATION: DocumentationConnector
        }
        
        # Initialize from configuration
        asyncio.create_task(self._initialize_from_config())
    
    async def _initialize_from_config(self):
        """Initialize pipeline from configuration."""
        try:
            # Load connector configurations
            connector_configs = self.config.get("connectors", [])
            
            for config_data in connector_configs:
                await self.add_connector(ConnectorConfig(
                    connector_id=config_data["connector_id"],
                    connector_type=ConnectorType(config_data["connector_type"]),
                    config=config_data["config"],
                    enabled=config_data.get("enabled", True),
                    priority=config_data.get("priority", 1),
                    schedule=config_data.get("schedule"),
                    dependencies=config_data.get("dependencies", [])
                ))
            
            # Start scheduler if enabled
            if self.scheduler_enabled:
                await self.start_scheduler()
            
            self.logger.info(f"Initialized pipeline {self.pipeline_id} with {len(self.connectors)} connectors")
        
        except Exception as e:
            self.logger.error(f"Error initializing pipeline: {e}")
    
    async def add_connector(self, connector_config: ConnectorConfig) -> bool:
        """Add a connector to the pipeline."""
        try:
            # Validate configuration
            if connector_config.connector_id in self.connectors:
                self.logger.warning(f"Connector {connector_config.connector_id} already exists")
                return False
            
            # Create connector instance
            connector_class = self.connector_classes.get(connector_config.connector_type)
            if not connector_class:
                self.logger.error(f"Unknown connector type: {connector_config.connector_type}")
                return False
            
            connector = connector_class(
                connector_config.connector_id,
                connector_config.config
            )
            
            # Validate connector configuration
            validation_errors = await connector.validate_configuration()
            if validation_errors:
                self.logger.error(f"Connector validation failed: {validation_errors}")
                return False
            
            # Store connector and configuration
            self.connectors[connector_config.connector_id] = connector
            self.connector_configs[connector_config.connector_id] = connector_config
            
            self.logger.info(f"Added connector: {connector_config.connector_id}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error adding connector {connector_config.connector_id}: {e}")
            return False
    
    async def remove_connector(self, connector_id: str) -> bool:
        """Remove a connector from the pipeline."""
        try:
            if connector_id not in self.connectors:
                return False
            
            # Clean up connector
            connector = self.connectors[connector_id]
            if hasattr(connector, 'cleanup'):
                await connector.cleanup()
            
            # Remove from pipeline
            del self.connectors[connector_id]
            del self.connector_configs[connector_id]
            
            self.logger.info(f"Removed connector: {connector_id}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error removing connector {connector_id}: {e}")
            return False
    
    async def run_pipeline(
        self,
        connector_ids: Optional[List[str]] = None,
        trigger: str = "manual",
        metadata: Optional[Dict[str, Any]] = None
    ) -> PipelineRun:
        """Run the ingestion pipeline."""
        if self.status == PipelineStatus.RUNNING:
            raise RuntimeError("Pipeline is already running")
        
        # Create new run
        run = PipelineRun(
            run_id=f"{self.pipeline_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            started_at=datetime.utcnow(),
            trigger=trigger,
            metadata=metadata or {}
        )
        
        self.current_run = run
        self.status = PipelineStatus.RUNNING
        
        try:
            # Determine which connectors to run
            if connector_ids is None:
                connector_ids = [
                    cid for cid, config in self.connector_configs.items()
                    if config.enabled
                ]
            
            # Sort connectors by priority and dependencies
            sorted_connectors = await self._sort_connectors_by_dependencies(connector_ids)
            
            # Run connectors
            await self._execute_connectors(sorted_connectors, run)
            
            # Update run status
            run.completed_at = datetime.utcnow()
            run.status = PipelineStatus.COMPLETED if run.total_errors == 0 else PipelineStatus.ERROR
            
        except Exception as e:
            self.logger.error(f"Pipeline run failed: {e}")
            run.status = PipelineStatus.ERROR
            run.completed_at = datetime.utcnow()
        
        finally:
            # Clean up
            self.status = PipelineStatus.IDLE
            self.current_run = None
            
            # Add to history
            self.run_history.append(run)
            if len(self.run_history) > self.max_history_size:
                self.run_history = self.run_history[-self.max_history_size:]
        
        return run
    
    async def _sort_connectors_by_dependencies(self, connector_ids: List[str]) -> List[str]:
        """Sort connectors by dependencies and priority."""
        # Simple topological sort with priority
        sorted_connectors = []
        remaining = set(connector_ids)
        
        while remaining:
            # Find connectors with no unmet dependencies
            ready = []
            for connector_id in remaining:
                config = self.connector_configs[connector_id]
                dependencies_met = all(
                    dep not in remaining or dep in sorted_connectors
                    for dep in config.dependencies
                )
                if dependencies_met:
                    ready.append((connector_id, config.priority))
            
            if not ready:
                # Circular dependency or missing dependency
                self.logger.warning("Circular or missing dependencies detected, adding remaining connectors")
                ready = [(cid, self.connector_configs[cid].priority) for cid in remaining]
            
            # Sort by priority and add to result
            ready.sort(key=lambda x: x[1])  # Sort by priority (lower = higher priority)
            
            for connector_id, _ in ready:
                if connector_id in remaining:
                    sorted_connectors.append(connector_id)
                    remaining.remove(connector_id)
        
        return sorted_connectors
    
    async def _execute_connectors(self, connector_ids: List[str], run: PipelineRun):
        """Execute connectors with concurrency control."""
        semaphore = asyncio.Semaphore(self.max_concurrent_connectors)
        
        async def execute_connector(connector_id: str):
            async with semaphore:
                await self._execute_single_connector(connector_id, run)
        
        # Create tasks for all connectors
        tasks = [execute_connector(cid) for cid in connector_ids]
        
        # Wait for all to complete
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _execute_single_connector(self, connector_id: str, run: PipelineRun):
        """Execute a single connector with error handling and retries."""
        connector = self.connectors[connector_id]
        
        for attempt in range(self.error_retry_attempts + 1):
            try:
                self.logger.info(f"Running connector {connector_id} (attempt {attempt + 1})")
                
                # Run connector ingestion
                result = await connector.ingest_incremental()
                
                # Process documents through IndexHub
                if result.success:
                    await self._process_connector_documents(connector, result)
                
                # Store result
                run.connector_results[connector_id] = result
                run.total_documents += (
                    result.documents_created + 
                    result.documents_updated
                )
                
                if not result.success:
                    run.total_errors += 1
                
                # Success - break retry loop
                break
            
            except Exception as e:
                error_msg = f"Connector {connector_id} failed: {str(e)}"
                self.logger.error(error_msg)
                
                if attempt < self.error_retry_attempts:
                    self.logger.info(f"Retrying connector {connector_id} in {self.error_retry_delay} seconds")
                    await asyncio.sleep(self.error_retry_delay)
                else:
                    # Final attempt failed
                    result = IngestionResult(
                        connector_type=connector.connector_type,
                        source_id=connector_id,
                        success=False,
                        errors=[error_msg]
                    )
                    run.connector_results[connector_id] = result
                    run.total_errors += 1
    
    async def _process_connector_documents(self, connector: BaseConnector, result: IngestionResult):
        """Process documents from connector through IndexHub."""
        try:
            documents = []
            
            # Collect documents from connector
            async for document in connector.scan_sources():
                if document:
                    documents.append(document)
                
                # Process in batches
                if len(documents) >= connector.batch_size:
                    await self._index_documents_batch(documents, connector)
                    documents.clear()
            
            # Process remaining documents
            if documents:
                await self._index_documents_batch(documents, connector)
        
        except Exception as e:
            self.logger.error(f"Error processing documents from {connector.connector_id}: {e}")
            result.errors.append(f"Document processing failed: {str(e)}")
    
    async def _index_documents_batch(self, documents: List[Document], connector: BaseConnector):
        """Index a batch of documents through IndexHub."""
        try:
            # Determine department/team from connector configuration
            config = self.connector_configs[connector.connector_id]
            
            # Default department mapping based on connector type
            department_mapping = {
                ConnectorType.FILE: "engineering",
                ConnectorType.GIT: "engineering", 
                ConnectorType.DATABASE: "operations",
                ConnectorType.DOCUMENTATION: "business"
            }
            
            department_name = config.config.get("department", 
                department_mapping.get(connector.connector_type, "engineering"))
            team_name = config.config.get("team")
            
            # Map to IndexHub enums
            from ..index_hub import Department, Team
            
            department = Department(department_name)
            team = Team(team_name) if team_name else None
            
            # Index documents
            success = await self.index_hub.index_documents(documents, department, team)
            
            if success:
                self.logger.debug(f"Indexed {len(documents)} documents from {connector.connector_id}")
            else:
                self.logger.error(f"Failed to index documents from {connector.connector_id}")
        
        except Exception as e:
            self.logger.error(f"Error indexing documents batch: {e}")
    
    async def start_scheduler(self):
        """Start the pipeline scheduler."""
        if self.scheduler_task and not self.scheduler_task.done():
            return
        
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        self.logger.info("Pipeline scheduler started")
    
    async def stop_scheduler(self):
        """Stop the pipeline scheduler."""
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
            self.scheduler_task = None
        
        self.logger.info("Pipeline scheduler stopped")
    
    async def _scheduler_loop(self):
        """Main scheduler loop."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                # Check if any connectors need to run
                for connector_id, config in self.connector_configs.items():
                    if not config.enabled or not config.schedule:
                        continue
                    
                    if await self._should_run_connector(connector_id, config):
                        await self.run_pipeline(
                            connector_ids=[connector_id],
                            trigger="scheduled"
                        )
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}")
    
    async def _should_run_connector(self, connector_id: str, config: ConnectorConfig) -> bool:
        """Check if connector should run based on schedule."""
        if not config.schedule:
            return False
        
        schedule_type = config.schedule.get("type", "manual")
        
        if schedule_type == "interval":
            interval_minutes = config.schedule.get("interval_minutes", 60)
            
            # Check last run time
            last_run = None
            for run in reversed(self.run_history):
                if connector_id in run.connector_results:
                    last_run = run.completed_at or run.started_at
                    break
            
            if last_run is None:
                return True  # Never run before
            
            next_run_time = last_run + timedelta(minutes=interval_minutes)
            return datetime.utcnow() >= next_run_time
        
        # Add other schedule types (cron, etc.) as needed
        return False
    
    async def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status."""
        return {
            "pipeline_id": self.pipeline_id,
            "status": self.status.value,
            "connectors_count": len(self.connectors),
            "enabled_connectors": len([
                c for c in self.connector_configs.values() if c.enabled
            ]),
            "current_run": self.current_run.run_id if self.current_run else None,
            "last_run": self.run_history[-1].run_id if self.run_history else None,
            "scheduler_enabled": self.scheduler_enabled,
            "scheduler_running": self.scheduler_task is not None and not self.scheduler_task.done()
        }
    
    async def get_connector_status(self, connector_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific connector."""
        if connector_id not in self.connectors:
            return None
        
        connector = self.connectors[connector_id]
        config = self.connector_configs[connector_id]
        
        # Get last run result
        last_result = None
        for run in reversed(self.run_history):
            if connector_id in run.connector_results:
                last_result = run.connector_results[connector_id]
                break
        
        status = await connector.get_connector_status()
        status.update({
            "enabled": config.enabled,
            "priority": config.priority,
            "schedule": config.schedule,
            "dependencies": config.dependencies,
            "last_result": last_result.to_dict() if last_result else None
        })
        
        return status
    
    async def get_run_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get pipeline run history."""
        recent_runs = self.run_history[-limit:] if limit > 0 else self.run_history
        
        return [
            {
                "run_id": run.run_id,
                "started_at": run.started_at.isoformat(),
                "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                "status": run.status.value,
                "trigger": run.trigger,
                "total_documents": run.total_documents,
                "total_errors": run.total_errors,
                "connectors_run": len(run.connector_results),
                "duration_seconds": (
                    (run.completed_at - run.started_at).total_seconds()
                    if run.completed_at else None
                )
            }
            for run in reversed(recent_runs)
        ]
    
    async def cleanup(self):
        """Clean up pipeline resources."""
        # Stop scheduler
        await self.stop_scheduler()
        
        # Clean up connectors
        for connector in self.connectors.values():
            if hasattr(connector, 'cleanup'):
                try:
                    await connector.cleanup()
                except Exception as e:
                    self.logger.error(f"Error cleaning up connector: {e}")
        
        self.connectors.clear()
        self.connector_configs.clear()
        
        self.logger.info(f"Pipeline {self.pipeline_id} cleaned up")