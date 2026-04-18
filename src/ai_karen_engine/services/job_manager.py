"""
Background Job Management System

This module provides a comprehensive job management system for long-running operations
such as model downloads, conversions, and quantizations. It supports job tracking,
progress monitoring, and resource management with persistent state.

Key Features:
- Job tracking with progress, status, and logging
- Job controls (pause, resume, cancel) and persistent job state
- Job queue management with concurrency limits and resource monitoring
- Support for different job types (download, convert, quantize, merge_lora)
- Thread-safe operations and cleanup
"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Union

logger = logging.getLogger(__name__)

# -----------------------------
# Data Models
# -----------------------------

@dataclass
class Job:
    """Job information and state."""
    id: str
    kind: str  # download, convert, quantize, merge_lora
    status: str = "queued"  # queued, running, paused, completed, failed, cancelled
    progress: float = 0.0
    logs: List[str] = field(default_factory=list)
    result: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    
    # Metadata
    title: str = ""
    description: str = ""
    tags: Set[str] = field(default_factory=set)
    
    # Timing
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    updated_at: float = field(default_factory=time.time)
    
    # Job parameters
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Resource requirements
    cpu_cores: int = 1
    memory_mb: int = 1024
    disk_space_mb: int = 0
    
    # Priority and dependencies
    priority: int = 0  # Higher number = higher priority
    dependencies: List[str] = field(default_factory=list)  # Job IDs this job depends on
    
    # Internal state (not persisted)
    _worker_thread: Optional[threading.Thread] = field(default=None, init=False, repr=False)
    _cancel_event: Optional[threading.Event] = field(default=None, init=False, repr=False)
    _pause_event: Optional[threading.Event] = field(default=None, init=False, repr=False)
    
    def __post_init__(self):
        """Initialize internal state."""
        self._cancel_event = threading.Event()
        self._pause_event = threading.Event()
    
    def is_active(self) -> bool:
        """Check if job is in an active state."""
        return self.status in ["queued", "running", "paused"]
    
    def is_finished(self) -> bool:
        """Check if job is in a finished state."""
        return self.status in ["completed", "failed", "cancelled"]
    
    def can_start(self) -> bool:
        """Check if job can be started."""
        return self.status == "queued"
    
    def can_pause(self) -> bool:
        """Check if job can be paused."""
        return self.status == "running"
    
    def can_resume(self) -> bool:
        """Check if job can be resumed."""
        return self.status == "paused"
    
    def can_cancel(self) -> bool:
        """Check if job can be cancelled."""
        return self.status in ["queued", "running", "paused"]


@dataclass
class JobStats:
    """Job statistics."""
    total_jobs: int = 0
    queued_jobs: int = 0
    running_jobs: int = 0
    paused_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    cancelled_jobs: int = 0
    
    # Resource usage
    active_cpu_cores: int = 0
    active_memory_mb: int = 0
    active_disk_space_mb: int = 0


@dataclass
class ResourceLimits:
    """Resource limits for job execution."""
    max_concurrent_jobs: int = 3
    max_cpu_cores: int = 8
    max_memory_mb: int = 8192
    max_disk_space_mb: int = 102400  # 100GB
    
    # Per-job limits
    max_job_memory_mb: int = 4096
    max_job_disk_space_mb: int = 51200  # 50GB


# -----------------------------
# Job Manager Implementation
# -----------------------------

class JobManager:
    """
    Background job management system.
    
    Manages long-running operations with progress tracking, resource management,
    and persistent state. Supports job queuing, prioritization, and dependencies.
    """
    
    def __init__(self, 
                 db_path: Optional[str] = None,
                 resource_limits: Optional[ResourceLimits] = None):
        """
        Initialize job manager.
        
        Args:
            db_path: Path to SQLite database for job persistence
            resource_limits: Resource limits for job execution
        """
        self.db_path = db_path or self._get_default_db_path()
        self.resource_limits = resource_limits or ResourceLimits()
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Job storage
        self._jobs: Dict[str, Job] = {}
        self._job_handlers: Dict[str, Callable[[Job], None]] = {}
        
        # Scheduler state
        self._scheduler_thread: Optional[threading.Thread] = None
        self._scheduler_running = False
        self._scheduler_event = threading.Event()
        
        # Initialize database
        self._init_database()
        
        # Load existing jobs
        self._load_jobs()
        
        # Start scheduler
        self.start_scheduler()
    
    def _get_default_db_path(self) -> str:
        """Get default database path."""
        home = Path.home()
        return str(home / ".ai_karen" / "jobs.db")
    
    def _init_database(self) -> None:
        """Initialize SQLite database for job persistence."""
        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress REAL DEFAULT 0.0,
                    logs TEXT,  -- JSON array
                    result TEXT,  -- JSON object
                    error TEXT,
                    title TEXT,
                    description TEXT,
                    tags TEXT,  -- JSON array
                    created_at REAL NOT NULL,
                    started_at REAL,
                    completed_at REAL,
                    updated_at REAL NOT NULL,
                    parameters TEXT,  -- JSON object
                    cpu_cores INTEGER DEFAULT 1,
                    memory_mb INTEGER DEFAULT 1024,
                    disk_space_mb INTEGER DEFAULT 0,
                    priority INTEGER DEFAULT 0,
                    dependencies TEXT  -- JSON array
                )
            """)
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_kind ON jobs(kind)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_priority ON jobs(priority DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at)")
            
            conn.commit()
    
    def _load_jobs(self) -> None:
        """Load jobs from database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM jobs")
            rows = cursor.fetchall()
        
        for row in rows:
            try:
                job = self._row_to_job(row)
                self._jobs[job.id] = job
                
                # Reset running jobs to queued on startup
                if job.status == "running":
                    job.status = "queued"
                    job.updated_at = time.time()
                    self._persist_job(job)
                
            except Exception as e:
                logger.warning(f"Failed to load job {row['id']}: {e}")
        
        logger.info(f"Loaded {len(self._jobs)} jobs from database")
    
    def _row_to_job(self, row: sqlite3.Row) -> Job:
        """Convert database row to Job object."""
        return Job(
            id=row["id"],
            kind=row["kind"],
            status=row["status"],
            progress=row["progress"] or 0.0,
            logs=json.loads(row["logs"] or "[]"),
            result=json.loads(row["result"] or "{}"),
            error=row["error"],
            title=row["title"] or "",
            description=row["description"] or "",
            tags=set(json.loads(row["tags"] or "[]")),
            created_at=row["created_at"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            updated_at=row["updated_at"],
            parameters=json.loads(row["parameters"] or "{}"),
            cpu_cores=row["cpu_cores"] or 1,
            memory_mb=row["memory_mb"] or 1024,
            disk_space_mb=row["disk_space_mb"] or 0,
            priority=row["priority"] or 0,
            dependencies=json.loads(row["dependencies"] or "[]")
        )
    
    def _persist_job(self, job: Job) -> None:
        """Persist job to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO jobs (
                    id, kind, status, progress, logs, result, error,
                    title, description, tags, created_at, started_at,
                    completed_at, updated_at, parameters, cpu_cores,
                    memory_mb, disk_space_mb, priority, dependencies
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job.id, job.kind, job.status, job.progress,
                json.dumps(job.logs), json.dumps(job.result), job.error,
                job.title, job.description, json.dumps(list(job.tags)),
                job.created_at, job.started_at, job.completed_at, job.updated_at,
                json.dumps(job.parameters), job.cpu_cores, job.memory_mb,
                job.disk_space_mb, job.priority, json.dumps(job.dependencies)
            ))
            conn.commit()
    
    # ---------- Job Creation ----------
    
    def create_job(self, 
                   kind: str,
                   title: str = "",
                   description: str = "",
                   parameters: Optional[Dict[str, Any]] = None,
                   **kwargs) -> Job:
        """
        Create a new job.
        
        Args:
            kind: Job type (download, convert, quantize, merge_lora)
            title: Human-readable job title
            description: Job description
            parameters: Job parameters
            **kwargs: Additional job properties
            
        Returns:
            Created job object
        """
        job_id = str(uuid.uuid4())
        
        job = Job(
            id=job_id,
            kind=kind,
            title=title or f"{kind.title()} Job",
            description=description,
            parameters=parameters or {},
            **kwargs
        )
        
        with self._lock:
            self._jobs[job_id] = job
            self._persist_job(job)
        
        # Notify scheduler
        self._scheduler_event.set()
        
        logger.info(f"Created job {job_id}: {job.title}")
        return job
    
    def register_handler(self, kind: str, handler: Callable[[Job], None]) -> None:
        """
        Register a job handler for a specific job type.
        
        Args:
            kind: Job type to handle
            handler: Handler function that takes a Job object
        """
        with self._lock:
            self._job_handlers[kind] = handler
        
        logger.info(f"Registered handler for job type: {kind}")
    
    # ---------- Job Retrieval ----------
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        with self._lock:
            return self._jobs.get(job_id)
    
    def list_jobs(self, 
                  status: Optional[str] = None,
                  kind: Optional[str] = None,
                  limit: Optional[int] = None) -> List[Job]:
        """
        List jobs with optional filtering.
        
        Args:
            status: Filter by status
            kind: Filter by job type
            limit: Maximum number of jobs to return
            
        Returns:
            List of matching jobs
        """
        with self._lock:
            jobs = list(self._jobs.values())
        
        # Apply filters
        if status:
            jobs = [job for job in jobs if job.status == status]
        
        if kind:
            jobs = [job for job in jobs if job.kind == kind]
        
        # Sort by priority and creation time
        jobs.sort(key=lambda j: (-j.priority, -j.created_at))
        
        # Apply limit
        if limit:
            jobs = jobs[:limit]
        
        return jobs
    
    def get_active_jobs(self) -> List[Job]:
        """Get all active jobs."""
        return self.list_jobs(status="running") + self.list_jobs(status="paused")
    
    def get_queued_jobs(self) -> List[Job]:
        """Get all queued jobs."""
        return self.list_jobs(status="queued")
    
    # ---------- Job Control ----------
    
    def start_job(self, job_id: str) -> bool:
        """
        Start a queued job.
        
        Args:
            job_id: Job ID to start
            
        Returns:
            True if job was started, False otherwise
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job or not job.can_start():
                return False
            
            # Check resource availability
            if not self._can_allocate_resources(job):
                logger.debug(f"Cannot start job {job_id}: insufficient resources")
                return False
            
            # Check dependencies
            if not self._dependencies_satisfied(job):
                logger.debug(f"Cannot start job {job_id}: dependencies not satisfied")
                return False
            
            # Check if handler is available
            if job.kind not in self._job_handlers:
                logger.warning(f"No handler registered for job type: {job.kind}")
                return False
            
            # Start the job
            job.status = "running"
            job.started_at = time.time()
            job.updated_at = time.time()
            
            # Create worker thread
            handler = self._job_handlers[job.kind]
            job._worker_thread = threading.Thread(
                target=self._job_worker,
                args=(job, handler),
                daemon=True
            )
            job._worker_thread.start()
            
            self._persist_job(job)
            
            logger.info(f"Started job {job_id}: {job.title}")
            return True
    
    def pause_job(self, job_id: str) -> bool:
        """
        Pause a running job.
        
        Args:
            job_id: Job ID to pause
            
        Returns:
            True if job was paused, False otherwise
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job or not job.can_pause():
                return False
            
            job.status = "paused"
            job.updated_at = time.time()
            
            # Signal pause to worker
            if job._pause_event:
                job._pause_event.set()
            
            self._persist_job(job)
            
            logger.info(f"Paused job {job_id}: {job.title}")
            return True
    
    def resume_job(self, job_id: str) -> bool:
        """
        Resume a paused job.
        
        Args:
            job_id: Job ID to resume
            
        Returns:
            True if job was resumed, False otherwise
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job or not job.can_resume():
                return False
            
            job.status = "running"
            job.updated_at = time.time()
            
            # Clear pause signal
            if job._pause_event:
                job._pause_event.clear()
            
            self._persist_job(job)
            
            logger.info(f"Resumed job {job_id}: {job.title}")
            return True
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a job.
        
        Args:
            job_id: Job ID to cancel
            
        Returns:
            True if job was cancelled, False otherwise
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job or not job.can_cancel():
                return False
            
            job.status = "cancelled"
            job.completed_at = time.time()
            job.updated_at = time.time()
            
            # Signal cancellation to worker
            if job._cancel_event:
                job._cancel_event.set()
            
            self._persist_job(job)
            
            logger.info(f"Cancelled job {job_id}: {job.title}")
            return True
    
    def delete_job(self, job_id: str) -> bool:
        """
        Delete a job from the system.
        
        Args:
            job_id: Job ID to delete
            
        Returns:
            True if job was deleted, False otherwise
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            
            # Cancel if active
            if job.is_active():
                self.cancel_job(job_id)
            
            # Remove from memory and database
            del self._jobs[job_id]
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
                conn.commit()
            
            logger.info(f"Deleted job {job_id}: {job.title}")
            return True
    
    # ---------- Job Updates ----------
    
    def update_progress(self, job_id: str, progress: float) -> None:
        """Update job progress."""
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.progress = max(0.0, min(1.0, progress))
                job.updated_at = time.time()
                self._persist_job(job)
    
    def append_log(self, job_id: str, message: str) -> None:
        """Append log message to job."""
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                job.logs.append(f"[{timestamp}] {message}")
                job.updated_at = time.time()
                
                # Keep only last 1000 log entries
                if len(job.logs) > 1000:
                    job.logs = job.logs[-1000:]
                
                self._persist_job(job)
    
    def set_result(self, job_id: str, result: Dict[str, Any]) -> None:
        """Set job result."""
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.result = result
                job.updated_at = time.time()
                self._persist_job(job)
    
    def set_error(self, job_id: str, error: str) -> None:
        """Set job error."""
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.error = error
                job.status = "failed"
                job.completed_at = time.time()
                job.updated_at = time.time()
                self._persist_job(job)
    
    def complete_job(self, job_id: str, result: Optional[Dict[str, Any]] = None) -> None:
        """Mark job as completed."""
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.status = "completed"
                job.progress = 1.0
                job.completed_at = time.time()
                job.updated_at = time.time()
                
                if result:
                    job.result = result
                
                self._persist_job(job)
    
    # ---------- Resource Management ----------
    
    def _can_allocate_resources(self, job: Job) -> bool:
        """Check if resources can be allocated for job."""
        current_stats = self.get_stats()
        
        # Check concurrent job limit
        if current_stats.running_jobs >= self.resource_limits.max_concurrent_jobs:
            return False
        
        # Check CPU cores
        if (current_stats.active_cpu_cores + job.cpu_cores > 
            self.resource_limits.max_cpu_cores):
            return False
        
        # Check memory
        if (current_stats.active_memory_mb + job.memory_mb > 
            self.resource_limits.max_memory_mb):
            return False
        
        # Check disk space
        if (current_stats.active_disk_space_mb + job.disk_space_mb > 
            self.resource_limits.max_disk_space_mb):
            return False
        
        # Check per-job limits
        if job.memory_mb > self.resource_limits.max_job_memory_mb:
            return False
        
        if job.disk_space_mb > self.resource_limits.max_job_disk_space_mb:
            return False
        
        return True
    
    def _dependencies_satisfied(self, job: Job) -> bool:
        """Check if job dependencies are satisfied."""
        for dep_id in job.dependencies:
            dep_job = self._jobs.get(dep_id)
            if not dep_job or dep_job.status != "completed":
                return False
        return True
    
    # ---------- Job Worker ----------
    
    def _job_worker(self, job: Job, handler: Callable[[Job], None]) -> None:
        """Worker function that executes job handlers."""
        try:
            # Execute the job handler
            handler(job)
            
            # If job wasn't explicitly completed or failed, mark as completed
            if job.status == "running":
                self.complete_job(job.id)
        
        except Exception as e:
            logger.error(f"Job {job.id} failed with error: {e}")
            self.set_error(job.id, str(e))
        
        finally:
            # Clean up worker thread reference
            job._worker_thread = None
    
    # ---------- Scheduler ----------
    
    def start_scheduler(self) -> None:
        """Start the job scheduler."""
        if self._scheduler_running:
            return
        
        self._scheduler_running = True
        self._scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            daemon=True
        )
        self._scheduler_thread.start()
        
        logger.info("Job scheduler started")
    
    def stop_scheduler(self) -> None:
        """Stop the job scheduler."""
        self._scheduler_running = False
        self._scheduler_event.set()
        
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            self._scheduler_thread.join(timeout=5.0)
        
        logger.info("Job scheduler stopped")
    
    def _scheduler_loop(self) -> None:
        """Main scheduler loop."""
        while self._scheduler_running:
            try:
                # Process queued jobs
                self._process_queue()
                
                # Clean up finished jobs
                self._cleanup_finished_jobs()
                
                # Wait for next cycle or event
                self._scheduler_event.wait(timeout=5.0)
                self._scheduler_event.clear()
                
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(1.0)
    
    def _process_queue(self) -> None:
        """Process queued jobs and start them if resources allow."""
        queued_jobs = self.get_queued_jobs()
        
        # Sort by priority and creation time
        queued_jobs.sort(key=lambda j: (-j.priority, j.created_at))
        
        for job in queued_jobs:
            if self.start_job(job.id):
                # Job started successfully
                pass
            else:
                # Cannot start job now, will try again later
                break
    
    def _cleanup_finished_jobs(self) -> None:
        """Clean up finished job threads."""
        with self._lock:
            for job in self._jobs.values():
                if (job.is_finished() and 
                    job._worker_thread and 
                    not job._worker_thread.is_alive()):
                    job._worker_thread = None
    
    # ---------- Statistics ----------
    
    def get_stats(self) -> JobStats:
        """Get job statistics."""
        with self._lock:
            stats = JobStats()
            
            for job in self._jobs.values():
                stats.total_jobs += 1
                
                if job.status == "queued":
                    stats.queued_jobs += 1
                elif job.status == "running":
                    stats.running_jobs += 1
                    stats.active_cpu_cores += job.cpu_cores
                    stats.active_memory_mb += job.memory_mb
                    stats.active_disk_space_mb += job.disk_space_mb
                elif job.status == "paused":
                    stats.paused_jobs += 1
                elif job.status == "completed":
                    stats.completed_jobs += 1
                elif job.status == "failed":
                    stats.failed_jobs += 1
                elif job.status == "cancelled":
                    stats.cancelled_jobs += 1
            
            return stats
    
    def cleanup_old_jobs(self, older_than_hours: int = 168) -> int:  # 1 week default
        """
        Clean up old completed/failed/cancelled jobs.
        
        Args:
            older_than_hours: Remove jobs older than this many hours
            
        Returns:
            Number of jobs cleaned up
        """
        cutoff_time = time.time() - (older_than_hours * 3600)
        cleaned = 0
        
        with self._lock:
            jobs_to_delete = []
            
            for job_id, job in self._jobs.items():
                if (job.is_finished() and 
                    job.completed_at and 
                    job.completed_at < cutoff_time):
                    jobs_to_delete.append(job_id)
            
            for job_id in jobs_to_delete:
                if self.delete_job(job_id):
                    cleaned += 1
        
        logger.info(f"Cleaned up {cleaned} old jobs")
        return cleaned
    
    # ---------- Shutdown ----------
    
    def shutdown(self) -> None:
        """Shutdown the job manager."""
        logger.info("Shutting down job manager...")
        
        # Stop scheduler
        self.stop_scheduler()
        
        # Cancel all active jobs
        with self._lock:
            active_jobs = [job for job in self._jobs.values() if job.is_active()]
        
        for job in active_jobs:
            self.cancel_job(job.id)
        
        # Wait for worker threads to finish
        with self._lock:
            worker_threads = [job._worker_thread for job in self._jobs.values() 
                            if job._worker_thread and job._worker_thread.is_alive()]
        
        for thread in worker_threads:
            thread.join(timeout=5.0)
        
        logger.info("Job manager shutdown complete")


# -----------------------------
# Global Job Manager Instance
# -----------------------------

_global_manager: Optional[JobManager] = None
_global_manager_lock = threading.RLock()


def get_job_manager() -> JobManager:
    """Get the global job manager instance."""
    global _global_manager
    if _global_manager is None:
        with _global_manager_lock:
            if _global_manager is None:
                _global_manager = JobManager()
    return _global_manager


def initialize_job_manager(db_path: Optional[str] = None,
                          resource_limits: Optional[ResourceLimits] = None) -> JobManager:
    """Initialize a fresh global job manager."""
    global _global_manager
    with _global_manager_lock:
        if _global_manager:
            _global_manager.shutdown()
        _global_manager = JobManager(db_path, resource_limits)
    return _global_manager


# -----------------------------
# Convenience Functions
# -----------------------------

def create_job(kind: str, **kwargs) -> Job:
    """Create a job using the global job manager."""
    return get_job_manager().create_job(kind, **kwargs)


def get_job(job_id: str) -> Optional[Job]:
    """Get a job using the global job manager."""
    return get_job_manager().get_job(job_id)


def list_jobs(**kwargs) -> List[Job]:
    """List jobs using the global job manager."""
    return get_job_manager().list_jobs(**kwargs)


def register_handler(kind: str, handler: Callable[[Job], None]) -> None:
    """Register a job handler using the global job manager."""
    get_job_manager().register_handler(kind, handler)