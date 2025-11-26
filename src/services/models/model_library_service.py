"""
Model Library Service

This service manages on-disk model storage and downloads.
"""

import logging
import os
import shutil
import hashlib
import json
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import aiohttp
import aiofiles


class ModelStatus(Enum):
    """Model download status."""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ModelInfo:
    """Information about a model in the library."""
    id: str
    name: str
    version: str
    size_bytes: int
    format: str
    checksum: str
    download_url: str
    local_path: str = ""
    status: ModelStatus = ModelStatus.PENDING
    download_progress: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DownloadTask:
    """A model download task."""
    model_id: str
    url: str
    destination: str
    checksum: str
    status: ModelStatus = ModelStatus.PENDING
    progress: float = 0.0
    error_message: str = ""
    task_id: str = ""


class ModelLibraryService:
    """
    Model Library Service manages on-disk model storage and downloads.
    
    This service handles downloading, storing, and managing models
    with support for GPU/CPU compatibility, quantization, and caching.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Model Library Service.
        
        Args:
            config: Configuration for the model library
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Model storage directory
        self.storage_dir = Path(config.get("storage_dir", "models"))
        self.storage_dir.mkdir(exist_ok=True)
        
        # Model registry
        self.models: Dict[str, ModelInfo] = {}
        
        # Download tasks
        self.download_tasks: Dict[str, DownloadTask] = {}
        
        # Load existing models
        self._load_existing_models()
        
        # Start background tasks
        self._start_background_tasks()
    
    def _load_existing_models(self):
        """Load existing models from storage."""
        models_file = self.storage_dir / "models.json"
        if models_file.exists():
            try:
                with open(models_file, "r") as f:
                    models_data = json.load(f)
                
                for model_data in models_data:
                    model_info = ModelInfo(**model_data)
                    self.models[model_info.id] = model_info
                
                self.logger.info(f"Loaded {len(self.models)} existing models")
            except Exception as e:
                self.logger.error(f"Error loading existing models: {e}")
    
    def _start_background_tasks(self):
        """Start background tasks for monitoring downloads."""
        # Implementation would start background tasks
        pass
    
    async def add_model(self, model_info: ModelInfo) -> str:
        """
        Add a model to the library.
        
        Args:
            model_info: Information about the model
            
        Returns:
            The model ID
        """
        # Check if model already exists
        if model_info.id in self.models:
            raise ValueError(f"Model {model_info.id} already exists")
        
        # Set local path
        model_info.local_path = str(self.storage_dir / model_info.id)
        
        # Add to registry
        self.models[model_info.id] = model_info
        
        # Save registry
        await self._save_models_registry()
        
        self.logger.info(f"Added model to library: {model_info.id}")
        return model_info.id
    
    async def download_model(self, model_id: str) -> str:
        """
        Download a model.
        
        Args:
            model_id: The model ID to download
            
        Returns:
            The download task ID
        """
        # Get model info
        model_info = self.models.get(model_id)
        if not model_info:
            raise ValueError(f"Model {model_id} not found")
        
        # Check if already downloaded
        if model_info.status == ModelStatus.COMPLETED:
            raise ValueError(f"Model {model_id} already downloaded")
        
        # Create download task
        task_id = f"{model_id}_{int(time.time())}"
        task = DownloadTask(
            task_id=task_id,
            model_id=model_id,
            url=model_info.download_url,
            destination=model_info.local_path,
            checksum=model_info.checksum
        )
        
        self.download_tasks[task_id] = task
        
        # Start download
        asyncio.create_task(self._download_model(task))
        
        return task_id
    
    async def _download_model(self, task: DownloadTask):
        """Download a model in the background."""
        try:
            # Update status
            task.status = ModelStatus.DOWNLOADING
            self.models[task.model_id].status = ModelStatus.DOWNLOADING
            
            # Create destination directory
            os.makedirs(os.path.dirname(task.destination), exist_ok=True)
            
            # Download file
            async with aiohttp.ClientSession() as session:
                async with session.get(task.url) as response:
                    if response.status != 200:
                        raise Exception(f"Download failed with status {response.status}")
                    
                    # Get file size
                    total_size = int(response.headers.get("content-length", 0))
                    
                    # Download with progress
                    downloaded = 0
                    checksum = hashlib.sha256()
                    
                    async with aiofiles.open(task.destination, "wb") as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                            downloaded += len(chunk)
                            checksum.update(chunk)
                            
                            # Update progress
                            if total_size > 0:
                                task.progress = downloaded / total_size
                                self.models[task.model_id].download_progress = task.progress
                    
                    # Verify checksum
                    if checksum.hexdigest() != task.checksum:
                        os.remove(task.destination)
                        raise Exception("Checksum verification failed")
                    
                    # Update status
                    task.status = ModelStatus.COMPLETED
                    self.models[task.model_id].status = ModelStatus.COMPLETED
                    self.models[task.model_id].download_progress = 1.0
                    
                    self.logger.info(f"Downloaded model: {task.model_id}")
                    
        except Exception as e:
            # Update status on error
            task.status = ModelStatus.FAILED
            task.error_message = str(e)
            self.models[task.model_id].status = ModelStatus.FAILED
            
            self.logger.error(f"Error downloading model {task.model_id}: {e}")
    
    async def get_model(self, model_id: str) -> Optional[ModelInfo]:
        """
        Get model information.
        
        Args:
            model_id: The model ID
            
        Returns:
            Model information if found, None otherwise
        """
        return self.models.get(model_id)
    
    async def list_models(
        self, 
        status: Optional[ModelStatus] = None,
        format: Optional[str] = None
    ) -> List[ModelInfo]:
        """
        List models in the library.
        
        Args:
            status: Filter by status
            format: Filter by format
            
        Returns:
            List of matching models
        """
        models = list(self.models.values())
        
        # Apply filters
        if status:
            models = [m for m in models if m.status == status]
        
        if format:
            models = [m for m in models if m.format == format]
        
        return models
    
    async def delete_model(self, model_id: str) -> bool:
        """
        Delete a model from the library.
        
        Args:
            model_id: The model ID to delete
            
        Returns:
            True if deleted, False otherwise
        """
        model_info = self.models.get(model_id)
        if not model_info:
            return False
        
        # Delete files
        try:
            if os.path.exists(model_info.local_path):
                if os.path.isdir(model_info.local_path):
                    shutil.rmtree(model_info.local_path)
                else:
                    os.remove(model_info.local_path)
        except Exception as e:
            self.logger.error(f"Error deleting model files: {e}")
        
        # Remove from registry
        del self.models[model_id]
        
        # Save registry
        await self._save_models_registry()
        
        self.logger.info(f"Deleted model: {model_id}")
        return True
    
    async def get_download_task(self, task_id: str) -> Optional[DownloadTask]:
        """
        Get a download task.
        
        Args:
            task_id: The task ID
            
        Returns:
            The download task if found, None otherwise
        """
        return self.download_tasks.get(task_id)
    
    async def cancel_download(self, task_id: str) -> bool:
        """
        Cancel a download task.
        
        Args:
            task_id: The task ID to cancel
            
        Returns:
            True if cancelled, False otherwise
        """
        task = self.download_tasks.get(task_id)
        if not task:
            return False
        
        if task.status in [ModelStatus.COMPLETED, ModelStatus.FAILED, ModelStatus.CANCELLED]:
            return False
        
        # Update status
        task.status = ModelStatus.CANCELLED
        self.models[task.model_id].status = ModelStatus.CANCELLED
        
        # Delete partial download
        try:
            if os.path.exists(task.destination):
                if os.path.isdir(task.destination):
                    shutil.rmtree(task.destination)
                else:
                    os.remove(task.destination)
        except Exception as e:
            self.logger.error(f"Error deleting partial download: {e}")
        
        self.logger.info(f"Cancelled download: {task.model_id}")
        return True
    
    async def _save_models_registry(self):
        """Save the models registry to disk."""
        models_file = self.storage_dir / "models.json"
        
        try:
            models_data = []
            for model_info in self.models.values():
                model_dict = {
                    "id": model_info.id,
                    "name": model_info.name,
                    "version": model_info.version,
                    "size_bytes": model_info.size_bytes,
                    "format": model_info.format,
                    "checksum": model_info.checksum,
                    "download_url": model_info.download_url,
                    "local_path": model_info.local_path,
                    "status": model_info.status.value,
                    "download_progress": model_info.download_progress,
                    "metadata": model_info.metadata
                }
                models_data.append(model_dict)
            
            with open(models_file, "w") as f:
                json.dump(models_data, f, indent=2)
            
        except Exception as e:
            self.logger.error(f"Error saving models registry: {e}")
    
    async def get_library_stats(self) -> Dict[str, Any]:
        """
        Get library statistics.
        
        Returns:
            Dictionary of statistics
        """
        total_size = sum(m.size_bytes for m in self.models.values())
        downloaded_size = sum(
            m.size_bytes for m in self.models.values() 
            if m.status == ModelStatus.COMPLETED
        )
        
        status_counts = {}
        for status in ModelStatus:
            status_counts[status.value] = sum(
                1 for m in self.models.values() 
                if m.status == status
            )
        
        return {
            "total_models": len(self.models),
            "total_size_bytes": total_size,
            "downloaded_size_bytes": downloaded_size,
            "storage_usage_percent": (downloaded_size / total_size * 100) if total_size > 0 else 0,
            "status_counts": status_counts,
            "active_downloads": sum(
                1 for t in self.download_tasks.values() 
                if t.status == ModelStatus.DOWNLOADING
            )
        }
