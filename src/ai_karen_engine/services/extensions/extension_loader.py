"""
Extension Loader Service

This service provides capabilities for loading extensions from various sources,
including local directories, remote repositories, and package managers.
"""

from typing import Dict, List, Any, Optional, Union, Tuple, Set, Callable
import logging
import uuid
import json
import os
import shutil
import tempfile
import zipfile
import tarfile
import requests
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from urllib.parse import urlparse

from .extension_registry import Extension, ExtensionMetadata, ExtensionConfig, ExtensionType

logger = logging.getLogger(__name__)


class ExtensionSourceType(Enum):
    """Enumeration of extension source types."""
    LOCAL_DIRECTORY = "local_directory"
    LOCAL_FILE = "local_file"
    GIT_REPOSITORY = "git_repository"
    HTTP_URL = "http_url"
    PACKAGE_MANAGER = "package_manager"
    MARKETPLACE = "marketplace"


class ExtensionLoaderStatus(Enum):
    """Enumeration of extension loader statuses."""
    IDLE = "idle"
    DOWNLOADING = "downloading"
    EXTRACTING = "extracting"
    INSTALLING = "installing"
    VALIDATING = "validating"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class ExtensionSource:
    """A source for an extension."""
    source_type: ExtensionSourceType
    location: str
    version: Optional[str] = None
    checksum: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtensionLoadResult:
    """Result of loading an extension."""
    success: bool
    extension_id: Optional[str] = None
    extension_path: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    warnings: List[str] = field(default_factory=list)


@dataclass
class ExtensionLoadTask:
    """A task for loading an extension."""
    id: str
    source: ExtensionSource
    status: ExtensionLoaderStatus = ExtensionLoaderStatus.IDLE
    progress: float = 0.0
    message: str = ""
    result: Optional[ExtensionLoadResult] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ExtensionLoader:
    """
    Provides capabilities for loading extensions from various sources.
    
    This class is responsible for:
    - Loading extensions from various sources
    - Validating extension manifests
    - Installing extensions to the extensions directory
    - Managing the loading process
    - Providing progress updates
    """
    
    def __init__(self, extensions_dir: str = "extensions"):
        self._extensions_dir = Path(extensions_dir)
        self._tasks: Dict[str, ExtensionLoadTask] = {}
        self._active_tasks: Set[str] = set()
        
        # Callbacks for loader events
        self._on_task_started: Optional[Callable[[ExtensionLoadTask], None]] = None
        self._on_task_progress: Optional[Callable[[ExtensionLoadTask], None]] = None
        self._on_task_completed: Optional[Callable[[ExtensionLoadTask], None]] = None
        self._on_task_failed: Optional[Callable[[ExtensionLoadTask], None]] = None
    
    def initialize(self) -> None:
        """Initialize the extension loader."""
        # Create extensions directory if it doesn't exist
        self._extensions_dir.mkdir(exist_ok=True)
        
        logger.info("Initialized extension loader")
    
    def load_extension(
        self,
        source: ExtensionSource,
        task_id: Optional[str] = None
    ) -> str:
        """
        Load an extension from a source.
        
        Args:
            source: Source of the extension
            task_id: ID for the load task
            
        Returns:
            ID of the load task
        """
        task_id = task_id or str(uuid.uuid4())
        
        # Create load task
        task = ExtensionLoadTask(
            id=task_id,
            source=source
        )
        
        self._tasks[task_id] = task
        
        # Start loading
        self._start_task(task_id)
        
        logger.info(f"Started loading extension from {source.location}")
        return task_id
    
    def load_extension_from_url(
        self,
        url: str,
        version: Optional[str] = None,
        checksum: Optional[str] = None,
        task_id: Optional[str] = None
    ) -> str:
        """
        Load an extension from a URL.
        
        Args:
            url: URL of the extension
            version: Version of the extension
            checksum: Checksum of the extension
            task_id: ID for the load task
            
        Returns:
            ID of the load task
        """
        # Determine source type
        if url.startswith(("http://", "https://")):
            source_type = ExtensionSourceType.HTTP_URL
        elif url.startswith("git://") or url.endswith(".git"):
            source_type = ExtensionSourceType.GIT_REPOSITORY
        else:
            raise ValueError(f"Unsupported URL scheme: {url}")
        
        # Create source
        source = ExtensionSource(
            source_type=source_type,
            location=url,
            version=version,
            checksum=checksum
        )
        
        return self.load_extension(source, task_id)
    
    def load_extension_from_file(
        self,
        file_path: str,
        task_id: Optional[str] = None
    ) -> str:
        """
        Load an extension from a local file.
        
        Args:
            file_path: Path to the extension file
            task_id: ID for the load task
            
        Returns:
            ID of the load task
        """
        path_obj = Path(file_path)
        
        # Determine source type
        if path_obj.is_dir():
            source_type = ExtensionSourceType.LOCAL_DIRECTORY
        elif path_obj.is_file():
            source_type = ExtensionSourceType.LOCAL_FILE
        else:
            raise ValueError(f"File not found: {file_path}")
        
        # Create source
        source = ExtensionSource(
            source_type=source_type,
            location=str(path_obj)
        )
        
        return self.load_extension(source, task_id)
    
    def get_task(self, task_id: str) -> Optional[ExtensionLoadTask]:
        """Get a load task by ID."""
        return self._tasks.get(task_id)
    
    def get_active_tasks(self) -> List[ExtensionLoadTask]:
        """Get all active load tasks."""
        return [self._tasks[task_id] for task_id in self._active_tasks]
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a load task.
        
        Args:
            task_id: ID of the task
            
        Returns:
            True if task was cancelled, False if not found or already completed
        """
        task = self._tasks.get(task_id)
        if not task:
            logger.warning(f"Task not found: {task_id}")
            return False
        
        if task.status in [ExtensionLoaderStatus.COMPLETED, ExtensionLoaderStatus.ERROR]:
            logger.warning(f"Task already completed: {task_id}")
            return False
        
        # Remove from active tasks
        self._active_tasks.discard(task_id)
        
        # Update task status
        task.status = ExtensionLoaderStatus.ERROR
        task.message = "Cancelled by user"
        task.completed_at = datetime.now()
        
        logger.info(f"Cancelled task: {task_id}")
        return True
    
    def set_loader_callbacks(
        self,
        on_task_started: Optional[Callable[[ExtensionLoadTask], None]] = None,
        on_task_progress: Optional[Callable[[ExtensionLoadTask], None]] = None,
        on_task_completed: Optional[Callable[[ExtensionLoadTask], None]] = None,
        on_task_failed: Optional[Callable[[ExtensionLoadTask], None]] = None
    ) -> None:
        """Set callbacks for loader events."""
        self._on_task_started = on_task_started
        self._on_task_progress = on_task_progress
        self._on_task_completed = on_task_completed
        self._on_task_failed = on_task_failed
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about extension loading.
        
        Returns:
            Dictionary of statistics
        """
        stats = {
            "total_tasks": len(self._tasks),
            "active_tasks": len(self._active_tasks),
            "completed_tasks": sum(1 for task in self._tasks.values() if task.status == ExtensionLoaderStatus.COMPLETED),
            "failed_tasks": sum(1 for task in self._tasks.values() if task.status == ExtensionLoaderStatus.ERROR),
            "tasks_by_source_type": {},
            "tasks_by_status": {}
        }
        
        # Count tasks by source type
        for task in self._tasks.values():
            source_type = task.source.source_type.value
            if source_type not in stats["tasks_by_source_type"]:
                stats["tasks_by_source_type"][source_type] = 0
            stats["tasks_by_source_type"][source_type] += 1
        
        # Count tasks by status
        for task in self._tasks.values():
            status = task.status.value
            if status not in stats["tasks_by_status"]:
                stats["tasks_by_status"][status] = 0
            stats["tasks_by_status"][status] += 1
        
        return stats
    
    def _start_task(self, task_id: str) -> None:
        """Start a load task."""
        task = self._tasks.get(task_id)
        if not task:
            logger.error(f"Task not found: {task_id}")
            return
        
        # Update task status
        task.status = ExtensionLoaderStatus.DOWNLOADING
        task.started_at = datetime.now()
        task.message = "Starting load task"
        
        # Add to active tasks
        self._active_tasks.add(task_id)
        
        # Call task started callback if set
        if self._on_task_started:
            self._on_task_started(task)
        
        # Start loading in a separate thread
        import threading
        thread = threading.Thread(target=self._execute_task, args=(task_id,))
        thread.daemon = True
        thread.start()
    
    def _execute_task(self, task_id: str) -> None:
        """Execute a load task."""
        task = self._tasks.get(task_id)
        if not task:
            logger.error(f"Task not found: {task_id}")
            return
        
        try:
            # Execute based on source type
            if task.source.source_type == ExtensionSourceType.LOCAL_DIRECTORY:
                result = self._load_from_local_directory(task)
            elif task.source.source_type == ExtensionSourceType.LOCAL_FILE:
                result = self._load_from_local_file(task)
            elif task.source.source_type == ExtensionSourceType.HTTP_URL:
                result = self._load_from_http_url(task)
            elif task.source.source_type == ExtensionSourceType.GIT_REPOSITORY:
                result = self._load_from_git_repository(task)
            else:
                raise ValueError(f"Unsupported source type: {task.source.source_type}")
            
            # Update task
            task.result = result
            task.status = ExtensionLoaderStatus.COMPLETED if result.success else ExtensionLoaderStatus.ERROR
            task.message = result.error_message or "Completed successfully"
            task.completed_at = datetime.now()
            
            # Remove from active tasks
            self._active_tasks.discard(task_id)
            
            # Call appropriate callback
            if result.success and self._on_task_completed:
                self._on_task_completed(task)
            elif not result.success and self._on_task_failed:
                self._on_task_failed(task)
            
            logger.info(f"Completed task: {task_id} with result: {result.success}")
            
        except Exception as e:
            # Update task
            task.result = ExtensionLoadResult(
                success=False,
                error_message=str(e)
            )
            task.status = ExtensionLoaderStatus.ERROR
            task.message = str(e)
            task.completed_at = datetime.now()
            
            # Remove from active tasks
            self._active_tasks.discard(task_id)
            
            # Call task failed callback if set
            if self._on_task_failed:
                self._on_task_failed(task)
            
            logger.error(f"Task failed: {task_id} with error: {str(e)}")
    
    def _load_from_local_directory(self, task: ExtensionLoadTask) -> ExtensionLoadResult:
        """Load an extension from a local directory."""
        try:
            source_path = Path(task.source.location)
            
            # Check if directory exists
            if not source_path.exists():
                return ExtensionLoadResult(
                    success=False,
                    error_message=f"Directory not found: {source_path}"
                )
            
            # Check for manifest file
            manifest_path = source_path / "extension_manifest.json"
            if not manifest_path.exists():
                return ExtensionLoadResult(
                    success=False,
                    error_message=f"Manifest file not found: {manifest_path}"
                )
            
            # Load manifest
            with open(manifest_path, "r") as f:
                manifest_data = json.load(f)
            
            # Get extension ID
            extension_id = manifest_data.get("id")
            if not extension_id:
                return ExtensionLoadResult(
                    success=False,
                    error_message="Extension ID not found in manifest"
                )
            
            # Create extension directory
            extension_dir = self._extensions_dir / extension_id
            
            # Check if extension already exists
            if extension_dir.exists():
                return ExtensionLoadResult(
                    success=False,
                    error_message=f"Extension already exists: {extension_id}"
                )
            
            # Copy extension files
            self._update_task_progress(task, 0.5, "Copying extension files")
            shutil.copytree(source_path, extension_dir)
            
            # Validate extension
            self._update_task_progress(task, 0.8, "Validating extension")
            validation_result = self._validate_extension(extension_dir)
            
            if not validation_result["valid"]:
                # Clean up
                shutil.rmtree(extension_dir)
                
                return ExtensionLoadResult(
                    success=False,
                    error_message=f"Extension validation failed: {validation_result['error']}",
                    warnings=validation_result.get("warnings", [])
                )
            
            return ExtensionLoadResult(
                success=True,
                extension_id=extension_id,
                extension_path=str(extension_dir),
                metadata=manifest_data,
                warnings=validation_result.get("warnings", [])
            )
            
        except Exception as e:
            return ExtensionLoadResult(
                success=False,
                error_message=str(e)
            )
    
    def _load_from_local_file(self, task: ExtensionLoadTask) -> ExtensionLoadResult:
        """Load an extension from a local file."""
        try:
            source_path = Path(task.source.location)
            
            # Check if file exists
            if not source_path.exists():
                return ExtensionLoadResult(
                    success=False,
                    error_message=f"File not found: {source_path}"
                )
            
            # Create temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Extract file
                self._update_task_progress(task, 0.3, "Extracting extension file")
                
                if source_path.suffix.lower() == ".zip":
                    with zipfile.ZipFile(source_path, "r") as zip_ref:
                        zip_ref.extractall(temp_path)
                elif source_path.suffix.lower() in [".tar", ".tgz", ".tar.gz"]:
                    with tarfile.open(source_path, "r:*") as tar_ref:
                        tar_ref.extractall(temp_path)
                else:
                    return ExtensionLoadResult(
                        success=False,
                        error_message=f"Unsupported file format: {source_path.suffix}"
                    )
                
                # Find extracted directory
                extracted_dirs = [d for d in temp_path.iterdir() if d.is_dir()]
                if not extracted_dirs:
                    return ExtensionLoadResult(
                        success=False,
                        error_message="No directory found in archive"
                    )
                
                # Use the first directory
                extracted_dir = extracted_dirs[0]
                
                # Check for manifest file
                manifest_path = extracted_dir / "extension_manifest.json"
                if not manifest_path.exists():
                    return ExtensionLoadResult(
                        success=False,
                        error_message=f"Manifest file not found: {manifest_path}"
                    )
                
                # Load manifest
                with open(manifest_path, "r") as f:
                    manifest_data = json.load(f)
                
                # Get extension ID
                extension_id = manifest_data.get("id")
                if not extension_id:
                    return ExtensionLoadResult(
                        success=False,
                        error_message="Extension ID not found in manifest"
                    )
                
                # Create extension directory
                extension_dir = self._extensions_dir / extension_id
                
                # Check if extension already exists
                if extension_dir.exists():
                    return ExtensionLoadResult(
                        success=False,
                        error_message=f"Extension already exists: {extension_id}"
                    )
                
                # Copy extension files
                self._update_task_progress(task, 0.6, "Copying extension files")
                shutil.copytree(extracted_dir, extension_dir)
                
                # Validate extension
                self._update_task_progress(task, 0.8, "Validating extension")
                validation_result = self._validate_extension(extension_dir)
                
                if not validation_result["valid"]:
                    # Clean up
                    shutil.rmtree(extension_dir)
                    
                    return ExtensionLoadResult(
                        success=False,
                        error_message=f"Extension validation failed: {validation_result['error']}",
                        warnings=validation_result.get("warnings", [])
                    )
                
                return ExtensionLoadResult(
                    success=True,
                    extension_id=extension_id,
                    extension_path=str(extension_dir),
                    metadata=manifest_data,
                    warnings=validation_result.get("warnings", [])
                )
                
        except Exception as e:
            return ExtensionLoadResult(
                success=False,
                error_message=str(e)
            )
    
    def _load_from_http_url(self, task: ExtensionLoadTask) -> ExtensionLoadResult:
        """Load an extension from an HTTP URL."""
        try:
            url = task.source.location
            
            # Download file
            self._update_task_progress(task, 0.2, "Downloading extension")
            
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_path = Path(temp_file.name)
                
                # Download with progress
                response = requests.get(url, stream=True)
                response.raise_for_status()
                
                total_size = int(response.headers.get("content-length", 0))
                downloaded_size = 0
                
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # Update progress
                        if total_size > 0:
                            progress = 0.2 + 0.3 * (downloaded_size / total_size)
                            self._update_task_progress(task, progress, f"Downloading extension ({downloaded_size}/{total_size})")
            
            # Load from downloaded file
            self._update_task_progress(task, 0.5, "Extracting extension")
            
            # Create a new task for loading from file
            file_task = ExtensionLoadTask(
                id=f"{task.id}_file",
                source=ExtensionSource(
                    source_type=ExtensionSourceType.LOCAL_FILE,
                    location=str(temp_path)
                )
            )
            
            # Load from file
            result = self._load_from_local_file(file_task)
            
            # Clean up temporary file
            temp_path.unlink()
            
            return result
            
        except Exception as e:
            return ExtensionLoadResult(
                success=False,
                error_message=str(e)
            )
    
    def _load_from_git_repository(self, task: ExtensionLoadTask) -> ExtensionLoadResult:
        """Load an extension from a Git repository."""
        try:
            repo_url = task.source.location
            version = task.source.version or "main"
            
            # Create temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Clone repository
                self._update_task_progress(task, 0.3, "Cloning repository")
                
                import subprocess
                result = subprocess.run(
                    ["git", "clone", repo_url, str(temp_path)],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    return ExtensionLoadResult(
                        success=False,
                        error_message=f"Failed to clone repository: {result.stderr}"
                    )
                
                # Checkout version if specified
                if version and version != "main":
                    self._update_task_progress(task, 0.5, f"Checking out version: {version}")
                    
                    result = subprocess.run(
                        ["git", "checkout", version],
                        cwd=temp_path,
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode != 0:
                        return ExtensionLoadResult(
                            success=False,
                            error_message=f"Failed to checkout version: {result.stderr}"
                        )
                
                # Load from local directory
                self._update_task_progress(task, 0.7, "Loading extension")
                
                # Create a new task for loading from directory
                dir_task = ExtensionLoadTask(
                    id=f"{task.id}_dir",
                    source=ExtensionSource(
                        source_type=ExtensionSourceType.LOCAL_DIRECTORY,
                        location=str(temp_path)
                    )
                )
                
                # Load from directory
                result = self._load_from_local_directory(dir_task)
                
                return result
                
        except Exception as e:
            return ExtensionLoadResult(
                success=False,
                error_message=str(e)
            )
    
    def _validate_extension(self, extension_dir: Path) -> Dict[str, Any]:
        """Validate an extension."""
        try:
            warnings = []
            
            # Check for manifest file
            manifest_path = extension_dir / "extension_manifest.json"
            if not manifest_path.exists():
                return {
                    "valid": False,
                    "error": "Manifest file not found",
                    "warnings": warnings
                }
            
            # Load manifest
            with open(manifest_path, "r") as f:
                manifest_data = json.load(f)
            
            # Check required fields
            required_fields = ["id", "name", "version", "type"]
            for field in required_fields:
                if field not in manifest_data:
                    return {
                        "valid": False,
                        "error": f"Required field not found: {field}",
                        "warnings": warnings
                    }
            
            # Check extension type
            try:
                ExtensionType(manifest_data["type"])
            except ValueError:
                return {
                    "valid": False,
                    "error": f"Invalid extension type: {manifest_data['type']}",
                    "warnings": warnings
                }
            
            # Check for main module or entry point
            if "main_module" not in manifest_data and "entry_point" not in manifest_data:
                warnings.append("No main module or entry point specified")
            
            # Check metadata
            metadata = manifest_data.get("metadata", {})
            if not isinstance(metadata, dict):
                warnings.append("Metadata should be a dictionary")
            
            # Check configuration
            config = manifest_data.get("config", {})
            if not isinstance(config, dict):
                warnings.append("Configuration should be a dictionary")
            
            return {
                "valid": True,
                "warnings": warnings
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "warnings": warnings
            }
    
    def _update_task_progress(self, task: ExtensionLoadTask, progress: float, message: str) -> None:
        """Update the progress of a task."""
        task.progress = progress
        task.message = message
        
        # Call task progress callback if set
        if self._on_task_progress:
            self._on_task_progress(task)