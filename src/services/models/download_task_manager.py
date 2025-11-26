"""
Download Task Manager

Provides comprehensive download task management with:
- Individual download task tracking
- Progress callbacks and status updates
- Disk space validation before download initiation
- Task persistence and recovery
- Batch task management

This service manages the lifecycle of download tasks and provides
detailed tracking and management capabilities.
"""

import json
import logging
import shutil
import time
import threading
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any, Set
from enum import Enum
import uuid

logger = logging.getLogger("kari.download_task_manager")

class TaskStatus(Enum):
    """Download task status enumeration."""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"
    QUEUED = "queued"

class TaskPriority(Enum):
    """Download task priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

@dataclass
class DownloadTask:
    """
    Comprehensive download task with detailed tracking capabilities.
    
    This class represents an individual download operation with all
    necessary metadata for tracking, recovery, and management.
    """
    task_id: str
    model_id: str
    url: str
    filename: str
    destination_path: str
    
    # Size and progress tracking
    total_size: int = 0
    downloaded_size: int = 0
    progress: float = 0.0
    
    # Status and timing
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    last_updated: float = field(default_factory=time.time)
    
    # Error handling and retry
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    # Performance metrics
    download_speed: float = 0.0  # bytes per second
    average_speed: float = 0.0
    estimated_time_remaining: Optional[float] = None
    
    # Validation and security
    checksum: Optional[str] = None
    checksum_type: str = 'sha256'
    checksum_validated: bool = False
    
    # Download capabilities
    resume_supported: bool = False
    partial_download_path: Optional[str] = None
    
    # Metadata
    model_metadata: Optional[Dict[str, Any]] = None
    download_source: str = "unknown"
    user_agent: str = "ModelDownloadManager/1.0"
    
    # Callbacks
    progress_callbacks: List[Callable] = field(default_factory=list)
    completion_callbacks: List[Callable] = field(default_factory=list)
    
    def __post_init__(self):
        """Post-initialization setup."""
        if self.partial_download_path is None:
            self.partial_download_path = self.destination_path + '.tmp'
    
    def update_progress(self, downloaded_size: int, total_size: Optional[int] = None):
        """Update download progress."""
        self.downloaded_size = downloaded_size
        if total_size is not None:
            self.total_size = total_size
        
        if self.total_size > 0:
            self.progress = (self.downloaded_size / self.total_size) * 100
        
        self.last_updated = time.time()
        
        # Calculate download speed
        if self.started_at:
            elapsed = self.last_updated - self.started_at
            if elapsed > 0:
                self.download_speed = self.downloaded_size / elapsed
                
                # Calculate average speed (smoothed)
                if self.average_speed == 0:
                    self.average_speed = self.download_speed
                else:
                    # Exponential moving average
                    alpha = 0.1
                    self.average_speed = alpha * self.download_speed + (1 - alpha) * self.average_speed
                
                # Estimate time remaining
                if self.download_speed > 0 and self.total_size > 0:
                    remaining_bytes = self.total_size - self.downloaded_size
                    self.estimated_time_remaining = remaining_bytes / self.download_speed
    
    def set_status(self, status: TaskStatus, error_message: Optional[str] = None):
        """Update task status."""
        old_status = self.status
        self.status = status
        self.last_updated = time.time()
        
        if error_message:
            self.error_message = error_message
        
        # Update timing
        if status == TaskStatus.DOWNLOADING and old_status != TaskStatus.DOWNLOADING:
            self.started_at = time.time()
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            self.completed_at = time.time()
        
        logger.debug(f"Task {self.task_id} status changed from {old_status.value} to {status.value}")
    
    def add_progress_callback(self, callback: Callable[['DownloadTask'], None]):
        """Add progress callback."""
        if callback not in self.progress_callbacks:
            self.progress_callbacks.append(callback)
    
    def add_completion_callback(self, callback: Callable[['DownloadTask'], None]):
        """Add completion callback."""
        if callback not in self.completion_callbacks:
            self.completion_callbacks.append(callback)
    
    def notify_progress(self):
        """Notify all progress callbacks."""
        for callback in self.progress_callbacks:
            try:
                callback(self)
            except Exception as e:
                logger.error(f"Progress callback failed for task {self.task_id}: {e}")
    
    def notify_completion(self):
        """Notify all completion callbacks."""
        for callback in self.completion_callbacks:
            try:
                callback(self)
            except Exception as e:
                logger.error(f"Completion callback failed for task {self.task_id}: {e}")
    
    def get_elapsed_time(self) -> Optional[float]:
        """Get elapsed download time."""
        if self.started_at:
            end_time = self.completed_at or time.time()
            return end_time - self.started_at
        return None
    
    def get_eta_formatted(self) -> str:
        """Get formatted ETA string."""
        if self.estimated_time_remaining is None:
            return "Unknown"
        
        eta = int(self.estimated_time_remaining)
        if eta < 60:
            return f"{eta}s"
        elif eta < 3600:
            return f"{eta // 60}m {eta % 60}s"
        else:
            hours = eta // 3600
            minutes = (eta % 3600) // 60
            return f"{hours}h {minutes}m"
    
    def get_speed_formatted(self) -> str:
        """Get formatted download speed."""
        speed = self.average_speed if self.average_speed > 0 else self.download_speed
        
        if speed < 1024:
            return f"{speed:.1f} B/s"
        elif speed < 1024 * 1024:
            return f"{speed / 1024:.1f} KB/s"
        else:
            return f"{speed / (1024 * 1024):.1f} MB/s"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        # Convert enums to strings
        data['status'] = self.status.value
        data['priority'] = self.priority.value
        # Remove non-serializable callbacks
        data.pop('progress_callbacks', None)
        data.pop('completion_callbacks', None)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DownloadTask':
        """Create from dictionary."""
        # Convert string enums back to enum objects
        if 'status' in data:
            data['status'] = TaskStatus(data['status'])
        if 'priority' in data:
            data['priority'] = TaskPriority(data['priority'])
        
        return cls(**data)

class DownloadTaskManager:
    """
    Manages download tasks with comprehensive tracking and control.
    
    Provides:
    - Task lifecycle management
    - Progress tracking and callbacks
    - Disk space validation
    - Task persistence and recovery
    - Batch operations
    """
    
    def __init__(self, storage_dir: str = "models/downloads", 
                 persistence_file: str = "download_tasks.json"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.persistence_file = self.storage_dir / persistence_file
        self.tasks: Dict[str, DownloadTask] = {}
        self.task_queue: List[str] = []  # Task IDs in queue order
        self._lock = threading.RLock()
        
        # Load persisted tasks
        self._load_tasks()
        
        logger.info(f"DownloadTaskManager initialized with {len(self.tasks)} tasks")
    
    def create_task(self, model_id: str, url: str, filename: str, 
                   destination_path: Optional[str] = None,
                   priority: TaskPriority = TaskPriority.NORMAL,
                   checksum: Optional[str] = None,
                   checksum_type: str = 'sha256',
                   model_metadata: Optional[Dict[str, Any]] = None) -> DownloadTask:
        """
        Create a new download task.
        
        Args:
            model_id: Unique identifier for the model
            url: Download URL
            filename: Name of the file to download
            destination_path: Optional custom destination path
            priority: Task priority level
            checksum: Expected checksum for validation
            checksum_type: Type of checksum (sha256, md5, etc.)
            model_metadata: Optional model metadata
            
        Returns:
            Created DownloadTask
        """
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        # Determine destination path
        if destination_path is None:
            destination_path = str(self.storage_dir / filename)
        
        # Validate disk space before creating task
        if not self._validate_disk_space_for_task(url, destination_path):
            raise ValueError("Insufficient disk space for download")
        
        # Create task
        task = DownloadTask(
            task_id=task_id,
            model_id=model_id,
            url=url,
            filename=filename,
            destination_path=destination_path,
            priority=priority,
            checksum=checksum,
            checksum_type=checksum_type,
            model_metadata=model_metadata or {}
        )
        
        with self._lock:
            self.tasks[task_id] = task
            self._add_to_queue(task_id, priority)
        
        self._persist_tasks()
        
        logger.info(f"Created download task {task_id} for model {model_id}")
        return task
    
    def _validate_disk_space_for_task(self, url: str, destination_path: str) -> bool:
        """Validate disk space for a potential download."""
        try:
            # Try to get file size from URL
            import requests
            response = requests.head(url, timeout=10)
            if response.status_code == 200:
                content_length = response.headers.get('content-length')
                if content_length:
                    required_size = int(content_length)
                    return self.validate_disk_space(required_size, Path(destination_path).parent)
            
            # If we can't get size, assume we have space (will be checked again during download)
            return True
            
        except Exception as e:
            logger.warning(f"Could not validate disk space for {url}: {e}")
            return True  # Assume we have space if check fails
    
    def validate_disk_space(self, required_size: int, path: Optional[Path] = None) -> bool:
        """
        Validate available disk space before download.
        
        Args:
            required_size: Required space in bytes
            path: Path to check (defaults to storage directory)
            
        Returns:
            True if sufficient space is available
        """
        if path is None:
            path = self.storage_dir
        
        try:
            # Get available disk space
            stat = shutil.disk_usage(path)
            available_space = stat.free
            
            # Add 15% buffer for safety and temporary files
            required_with_buffer = int(required_size * 1.15)
            
            if available_space < required_with_buffer:
                logger.error(f"Insufficient disk space. Required: {required_with_buffer / (1024**3):.2f}GB, "
                           f"Available: {available_space / (1024**3):.2f}GB")
                return False
            
            logger.debug(f"Disk space validation passed. Required: {required_with_buffer / (1024**3):.2f}GB, "
                        f"Available: {available_space / (1024**3):.2f}GB")
            return True
            
        except Exception as e:
            logger.error(f"Failed to check disk space: {e}")
            return False
    
    def _add_to_queue(self, task_id: str, priority: TaskPriority):
        """Add task to queue based on priority."""
        # Find insertion point based on priority
        insert_index = len(self.task_queue)
        for i, existing_task_id in enumerate(self.task_queue):
            existing_task = self.tasks.get(existing_task_id)
            if existing_task and existing_task.priority.value < priority.value:
                insert_index = i
                break
        
        self.task_queue.insert(insert_index, task_id)
    
    def get_task(self, task_id: str) -> Optional[DownloadTask]:
        """Get task by ID."""
        with self._lock:
            return self.tasks.get(task_id)
    
    def get_tasks_by_model(self, model_id: str) -> List[DownloadTask]:
        """Get all tasks for a specific model."""
        with self._lock:
            return [task for task in self.tasks.values() if task.model_id == model_id]
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[DownloadTask]:
        """Get all tasks with specific status."""
        with self._lock:
            return [task for task in self.tasks.values() if task.status == status]
    
    def get_all_tasks(self) -> List[DownloadTask]:
        """Get all tasks."""
        with self._lock:
            return list(self.tasks.values())
    
    def get_next_queued_task(self) -> Optional[DownloadTask]:
        """Get the next task from the queue."""
        with self._lock:
            for task_id in self.task_queue:
                task = self.tasks.get(task_id)
                if task and task.status in [TaskStatus.PENDING, TaskStatus.QUEUED]:
                    return task
            return None
    
    def update_task_progress(self, task_id: str, downloaded_size: int, 
                           total_size: Optional[int] = None):
        """Update task progress and notify callbacks."""
        with self._lock:
            task = self.tasks.get(task_id)
            if task:
                task.update_progress(downloaded_size, total_size)
                task.notify_progress()
                
                # Persist periodically (every 1MB or 5% progress)
                if (downloaded_size % (1024 * 1024) == 0 or 
                    int(task.progress) % 5 == 0):
                    self._persist_tasks()
    
    def update_task_status(self, task_id: str, status: TaskStatus, 
                          error_message: Optional[str] = None):
        """Update task status."""
        with self._lock:
            task = self.tasks.get(task_id)
            if task:
                old_status = task.status
                task.set_status(status, error_message)
                
                # Notify completion callbacks for terminal states
                if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                    task.notify_completion()
                
                # Remove from queue if completed
                if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                    if task_id in self.task_queue:
                        self.task_queue.remove(task_id)
                
                self._persist_tasks()
                
                logger.info(f"Task {task_id} status updated from {old_status.value} to {status.value}")
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task."""
        with self._lock:
            task = self.tasks.get(task_id)
            if task and task.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
                self.update_task_status(task_id, TaskStatus.CANCELLED, "Cancelled by user")
                return True
            return False
    
    def pause_task(self, task_id: str) -> bool:
        """Pause a task (if supported)."""
        with self._lock:
            task = self.tasks.get(task_id)
            if task and task.status == TaskStatus.DOWNLOADING and task.resume_supported:
                self.update_task_status(task_id, TaskStatus.PAUSED)
                return True
            return False
    
    def resume_task(self, task_id: str) -> bool:
        """Resume a paused task."""
        with self._lock:
            task = self.tasks.get(task_id)
            if task and task.status == TaskStatus.PAUSED:
                self.update_task_status(task_id, TaskStatus.QUEUED)
                if task_id not in self.task_queue:
                    self._add_to_queue(task_id, task.priority)
                return True
            return False
    
    def retry_task(self, task_id: str) -> bool:
        """Retry a failed task."""
        with self._lock:
            task = self.tasks.get(task_id)
            if task and task.status == TaskStatus.FAILED:
                if task.retry_count < task.max_retries:
                    task.retry_count += 1
                    task.error_message = None
                    self.update_task_status(task_id, TaskStatus.QUEUED)
                    if task_id not in self.task_queue:
                        self._add_to_queue(task_id, task.priority)
                    return True
            return False
    
    def delete_task(self, task_id: str, cleanup_files: bool = True) -> bool:
        """Delete a task and optionally clean up files."""
        with self._lock:
            task = self.tasks.get(task_id)
            if not task:
                return False
            
            # Cancel if still active
            if task.status in [TaskStatus.DOWNLOADING, TaskStatus.QUEUED, TaskStatus.PENDING]:
                self.cancel_task(task_id)
            
            # Clean up files if requested
            if cleanup_files:
                try:
                    # Remove partial download
                    if task.partial_download_path:
                        partial_path = Path(task.partial_download_path)
                        if partial_path.exists():
                            partial_path.unlink()
                    
                    # Remove completed file if it exists
                    dest_path = Path(task.destination_path)
                    if dest_path.exists():
                        dest_path.unlink()
                        
                except Exception as e:
                    logger.warning(f"Failed to clean up files for task {task_id}: {e}")
            
            # Remove from tracking
            del self.tasks[task_id]
            if task_id in self.task_queue:
                self.task_queue.remove(task_id)
            
            self._persist_tasks()
            
            logger.info(f"Deleted task {task_id}")
            return True
    
    def cleanup_completed_tasks(self, max_age_hours: int = 24) -> int:
        """Clean up old completed tasks."""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        with self._lock:
            tasks_to_remove = []
            
            for task_id, task in self.tasks.items():
                if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                    if task.completed_at and (current_time - task.completed_at) > max_age_seconds:
                        tasks_to_remove.append(task_id)
            
            for task_id in tasks_to_remove:
                self.delete_task(task_id, cleanup_files=False)
            
            if tasks_to_remove:
                logger.info(f"Cleaned up {len(tasks_to_remove)} old tasks")
            
            return len(tasks_to_remove)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get download task statistics."""
        with self._lock:
            stats = {
                'total_tasks': len(self.tasks),
                'pending_tasks': len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING]),
                'queued_tasks': len([t for t in self.tasks.values() if t.status == TaskStatus.QUEUED]),
                'downloading_tasks': len([t for t in self.tasks.values() if t.status == TaskStatus.DOWNLOADING]),
                'completed_tasks': len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]),
                'failed_tasks': len([t for t in self.tasks.values() if t.status == TaskStatus.FAILED]),
                'cancelled_tasks': len([t for t in self.tasks.values() if t.status == TaskStatus.CANCELLED]),
                'paused_tasks': len([t for t in self.tasks.values() if t.status == TaskStatus.PAUSED]),
                'total_bytes_downloaded': sum(t.downloaded_size for t in self.tasks.values()),
                'total_bytes_to_download': sum(t.total_size for t in self.tasks.values() if t.total_size > 0),
                'average_download_speed': 0,
                'queue_length': len(self.task_queue)
            }
            
            # Calculate average download speed for active downloads
            active_tasks = [t for t in self.tasks.values() if t.status == TaskStatus.DOWNLOADING and t.download_speed > 0]
            if active_tasks:
                stats['average_download_speed'] = sum(t.download_speed for t in active_tasks) / len(active_tasks)
            
            return stats
    
    def _persist_tasks(self):
        """Persist tasks to storage."""
        try:
            data = {
                'tasks': {task_id: task.to_dict() for task_id, task in self.tasks.items()},
                'queue': self.task_queue,
                'last_updated': time.time()
            }
            
            with open(self.persistence_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to persist tasks: {e}")
    
    def _load_tasks(self):
        """Load tasks from storage."""
        if not self.persistence_file.exists():
            return
        
        try:
            with open(self.persistence_file, 'r') as f:
                data = json.load(f)
            
            # Load tasks
            for task_id, task_data in data.get('tasks', {}).items():
                try:
                    task = DownloadTask.from_dict(task_data)
                    self.tasks[task_id] = task
                except Exception as e:
                    logger.warning(f"Failed to load task {task_id}: {e}")
            
            # Load queue
            self.task_queue = data.get('queue', [])
            
            # Clean up queue of non-existent tasks
            self.task_queue = [tid for tid in self.task_queue if tid in self.tasks]
            
            logger.info(f"Loaded {len(self.tasks)} tasks from persistence")
            
        except Exception as e:
            logger.error(f"Failed to load tasks: {e}")
    
    def add_global_progress_callback(self, callback: Callable[[DownloadTask], None]):
        """Add a global progress callback to all tasks."""
        with self._lock:
            for task in self.tasks.values():
                task.add_progress_callback(callback)
    
    def add_global_completion_callback(self, callback: Callable[[DownloadTask], None]):
        """Add a global completion callback to all tasks."""
        with self._lock:
            for task in self.tasks.values():
                task.add_completion_callback(callback)