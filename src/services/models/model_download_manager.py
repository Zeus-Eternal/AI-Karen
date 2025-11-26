"""
Model Download Manager

Provides comprehensive model download management with:
- Progress tracking and cancellation
- Resumable downloads with retry logic
- Checksum validation and secure HTTPS support
- Exponential backoff for network failures
- Disk space validation

This service handles all aspects of model downloading with robust error handling
and recovery mechanisms.
"""

import hashlib
import logging
import os
import shutil
import ssl
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from urllib.parse import urlparse
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from requests.exceptions import RequestException, ConnectionError, Timeout, HTTPError

# Import comprehensive error handling
from ai_karen_engine.utils.error_handling import (
    ErrorHandler, ModelLibraryError, NetworkError, DiskSpaceError, 
    PermissionError, ValidationError, SecurityError,
    handle_network_error, handle_disk_space_error, handle_permission_error,
    handle_validation_error, handle_download_error,
    validate_disk_space, validate_file_permissions, execute_with_retry
)

logger = logging.getLogger("kari.model_download_manager")

@dataclass
class DownloadTask:
    """Download task information with comprehensive tracking."""
    task_id: str
    model_id: str
    url: str
    filename: str
    destination_path: str
    total_size: int = 0
    downloaded_size: int = 0
    progress: float = 0.0
    status: str = 'pending'  # 'pending', 'downloading', 'completed', 'failed', 'cancelled', 'paused'
    error_message: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    estimated_time_remaining: Optional[float] = None
    download_speed: float = 0.0  # bytes per second
    retry_count: int = 0
    max_retries: int = 3
    checksum: Optional[str] = None
    checksum_type: str = 'sha256'
    resume_supported: bool = False
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'task_id': self.task_id,
            'model_id': self.model_id,
            'url': self.url,
            'filename': self.filename,
            'destination_path': self.destination_path,
            'total_size': self.total_size,
            'downloaded_size': self.downloaded_size,
            'progress': self.progress,
            'status': self.status,
            'error_message': self.error_message,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'estimated_time_remaining': self.estimated_time_remaining,
            'download_speed': self.download_speed,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'checksum': self.checksum,
            'checksum_type': self.checksum_type,
            'resume_supported': self.resume_supported,
            'created_at': self.created_at
        }

class ModelDownloadManager:
    """
    Manages model downloads with comprehensive features:
    - Progress tracking and cancellation
    - Resumable downloads
    - Checksum validation
    - Secure HTTPS downloads
    - Retry logic with exponential backoff
    - Disk space validation
    """
    
    def __init__(self, download_dir: str = "models/downloads", max_concurrent_downloads: int = 3):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.max_concurrent_downloads = max_concurrent_downloads
        
        # Thread management
        self.active_downloads: Dict[str, DownloadTask] = {}
        self.download_threads: Dict[str, threading.Thread] = {}
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_downloads)
        self._lock = threading.Lock()
        self._shutdown = False
        
        # Configure secure HTTP session
        self.session = self._create_secure_session()
        
        logger.info(f"ModelDownloadManager initialized with download directory: {self.download_dir}")
    
    def _create_secure_session(self) -> requests.Session:
        """Create a secure HTTP session with retry strategy."""
        session = requests.Session()
        
        # Configure retry strategy with exponential backoff
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS"],
            backoff_factor=1,  # Will create delays of 1, 2, 4 seconds
            raise_on_status=False
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set secure headers
        session.headers.update({
            'User-Agent': 'ModelDownloadManager/1.0',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        
        # Configure SSL context for secure downloads
        session.verify = True
        
        return session
    
    def validate_disk_space(self, required_size: int, path: Optional[Path] = None) -> bool:
        """Validate available disk space before download with comprehensive error handling."""
        if path is None:
            path = self.download_dir
        
        try:
            # Use the comprehensive error handling utility
            validate_disk_space(path, required_size)
            
            logger.debug(f"Disk space validation passed. Required: {required_size / (1024**3):.2f}GB, "
                        f"Path: {path}")
            return True
            
        except DiskSpaceError as e:
            logger.error(f"Disk space validation failed: {e.error_info.message}")
            return False
        except PermissionError as e:
            logger.error(f"Permission error during disk space check: {e.error_info.message}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during disk space validation: {e}")
            return False
    
    def download_model(self, model_id: str, url: str, filename: str, 
                      destination_path: Optional[str] = None,
                      checksum: Optional[str] = None,
                      checksum_type: str = 'sha256',
                      progress_callback: Optional[Callable[[DownloadTask], None]] = None) -> DownloadTask:
        """
        Initiate model download with comprehensive tracking.
        
        Args:
            model_id: Unique identifier for the model
            url: Download URL (must be HTTPS for security)
            filename: Name of the file to download
            destination_path: Optional custom destination path
            checksum: Expected checksum for validation
            checksum_type: Type of checksum (sha256, md5, etc.)
            progress_callback: Optional callback for progress updates
            
        Returns:
            DownloadTask object for tracking progress
        """
        # Validate URL security
        if not self._validate_url_security(url):
            error_info = handle_validation_error(
                "url_security", 
                f"Insecure URL not allowed: {url}",
                {"url": url, "model_id": model_id}
            )
            raise ValidationError(error_info)
        
        # Generate unique task ID
        task_id = f"{model_id}_{int(time.time() * 1000)}"
        
        # Determine destination path
        if destination_path is None:
            destination_path = str(self.download_dir / filename)
        
        # Create download task
        task = DownloadTask(
            task_id=task_id,
            model_id=model_id,
            url=url,
            filename=filename,
            destination_path=destination_path,
            checksum=checksum,
            checksum_type=checksum_type,
            start_time=time.time()
        )
        
        # Check if we can get file size for disk space validation
        try:
            def get_file_info():
                response = self.session.head(url, timeout=30)
                response.raise_for_status()
                return response
            
            response = execute_with_retry(
                get_file_info,
                lambda e: handle_network_error(e, {"url": url, "operation": "head_request"})
            )
            
            task.total_size = int(response.headers.get('content-length', 0))
            task.resume_supported = 'accept-ranges' in response.headers
            
            # Validate disk space if we know the file size
            if task.total_size > 0:
                try:
                    validate_disk_space(self.download_dir, task.total_size)
                except (DiskSpaceError, PermissionError) as e:
                    task.status = 'failed'
                    task.error_message = e.error_info.message
                    logger.error(f"Pre-download validation failed for {model_id}: {e.error_info.message}")
                    return task
                    
        except NetworkError as e:
            logger.warning(f"Could not get file info for {url}: {e.error_info.message}")
            # Continue without file size info - will be checked during download
        except Exception as e:
            logger.warning(f"Unexpected error getting file info for {url}: {e}")
            # Continue without file size info
        
        # Add to active downloads
        with self._lock:
            if len(self.active_downloads) >= self.max_concurrent_downloads:
                task.status = 'failed'
                task.error_message = 'Maximum concurrent downloads reached'
                return task
            
            self.active_downloads[task_id] = task
        
        # Start download in background thread
        thread = threading.Thread(
            target=self._download_worker,
            args=(task, progress_callback),
            name=f"download-{task_id}"
        )
        thread.daemon = True
        thread.start()
        
        self.download_threads[task_id] = thread
        
        logger.info(f"Started download task {task_id} for model {model_id}")
        return task
    
    def _validate_url_security(self, url: str) -> bool:
        """Validate URL for security requirements with comprehensive error handling."""
        try:
            parsed = urlparse(url)
            
            # Require HTTPS for security
            if parsed.scheme != 'https':
                error_info = handle_validation_error(
                    "url_security", 
                    f"Only HTTPS URLs are allowed, got: {parsed.scheme}",
                    {"url": url, "scheme": parsed.scheme}
                )
                logger.error(f"URL security validation failed: {error_info.message}")
                return False
            
            # Basic hostname validation
            if not parsed.hostname:
                error_info = handle_validation_error(
                    "url_format", 
                    "Invalid URL: no hostname",
                    {"url": url}
                )
                logger.error(f"URL format validation failed: {error_info.message}")
                return False
            
            # Check for suspicious patterns
            suspicious_patterns = ['localhost', '127.0.0.1', '0.0.0.0', '::1']
            if any(pattern in parsed.hostname.lower() for pattern in suspicious_patterns):
                error_info = handle_validation_error(
                    "url_security", 
                    f"Suspicious hostname not allowed: {parsed.hostname}",
                    {"url": url, "hostname": parsed.hostname}
                )
                logger.error(f"URL security validation failed: {error_info.message}")
                return False
            
            return True
            
        except Exception as e:
            error_info = handle_validation_error(
                "url_parsing", 
                f"URL validation failed: {str(e)}",
                {"url": url}
            )
            logger.error(f"URL validation error: {error_info.message}")
            return False
    
    def _download_worker(self, task: DownloadTask, progress_callback: Optional[Callable[[DownloadTask], None]] = None):
        """Worker function for downloading models with comprehensive error handling and retry logic."""
        temp_path = Path(task.destination_path + '.tmp')
        final_path = Path(task.destination_path)
        
        try:
            # Validate permissions before starting
            try:
                validate_file_permissions(final_path.parent, "write")
            except PermissionError as e:
                task.status = 'failed'
                task.error_message = e.error_info.message
                self._notify_progress(task, progress_callback)
                return
            
            task.status = 'downloading'
            self._notify_progress(task, progress_callback)
            
            # Attempt download with comprehensive retry logic
            success = False
            last_error_info = None
            
            while task.retry_count <= task.max_retries and not self._shutdown:
                try:
                    success = self._attempt_download(task, temp_path, progress_callback)
                    if success:
                        break
                        
                except NetworkError as e:
                    last_error_info = e.error_info
                    task.error_message = e.error_info.message
                    
                except DiskSpaceError as e:
                    # Disk space errors are not retryable
                    task.status = 'failed'
                    task.error_message = e.error_info.message
                    logger.error(f"Disk space error for {task.model_id}: {e.error_info.message}")
                    return
                    
                except PermissionError as e:
                    # Permission errors might be retryable after user action
                    last_error_info = e.error_info
                    task.error_message = e.error_info.message
                    
                except Exception as e:
                    # Handle unexpected errors
                    error_info = handle_download_error(
                        "unexpected", 
                        str(e),
                        {"model_id": task.model_id, "attempt": task.retry_count + 1}
                    )
                    last_error_info = error_info
                    task.error_message = error_info.message
                
                task.retry_count += 1
                
                if task.retry_count <= task.max_retries and last_error_info and last_error_info.retry_possible:
                    # Calculate delay using error handler
                    error_handler = ErrorHandler()
                    delay = error_handler.calculate_retry_delay(last_error_info, task.retry_count - 1)
                    
                    logger.warning(f"Download attempt {task.retry_count} failed for {task.model_id}: {task.error_message}. "
                                 f"Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
                else:
                    logger.error(f"Download failed after {task.retry_count} attempts for {task.model_id}: {task.error_message}")
                    break
            
            if success:
                # Validate checksum if provided
                if task.checksum:
                    try:
                        if not self._validate_checksum(temp_path, task.checksum, task.checksum_type):
                            error_info = handle_validation_error(
                                "checksum", 
                                "Downloaded file checksum does not match expected value",
                                {"model_id": task.model_id, "expected": task.checksum}
                            )
                            task.status = 'failed'
                            task.error_message = error_info.message
                            if temp_path.exists():
                                temp_path.unlink()
                            return
                    except Exception as e:
                        error_info = handle_validation_error(
                            "checksum", 
                            f"Checksum validation failed: {str(e)}",
                            {"model_id": task.model_id}
                        )
                        task.status = 'failed'
                        task.error_message = error_info.message
                        if temp_path.exists():
                            temp_path.unlink()
                        return
                
                # Move completed file to final location
                try:
                    final_path.parent.mkdir(parents=True, exist_ok=True)
                    if final_path.exists():
                        final_path.unlink()  # Remove existing file
                    temp_path.rename(final_path)
                    
                    task.status = 'completed'
                    task.progress = 100.0
                    task.end_time = time.time()
                    
                    logger.info(f"Successfully downloaded {task.model_id} to {final_path}")
                    
                except OSError as e:
                    error_info = handle_permission_error(
                        str(final_path), 
                        "move downloaded file",
                        {"model_id": task.model_id}
                    )
                    task.status = 'failed'
                    task.error_message = error_info.message
                    logger.error(f"Failed to move downloaded file for {task.model_id}: {error_info.message}")
                    
            else:
                task.status = 'failed'
                if not task.error_message:
                    task.error_message = "Download failed after all retry attempts"
                
                # Clean up temp file
                if temp_path.exists():
                    try:
                        temp_path.unlink()
                    except Exception as cleanup_error:
                        logger.warning(f"Failed to clean up temp file {temp_path}: {cleanup_error}")
                
        except Exception as e:
            # Handle any unexpected errors in the worker
            error_info = handle_download_error(
                "worker_error", 
                f"Unexpected error in download worker: {str(e)}",
                {"model_id": task.model_id}
            )
            task.status = 'failed'
            task.error_message = error_info.message
            logger.error(f"Unexpected error in download worker for {task.model_id}: {error_info.message}")
            
            # Clean up temp file
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
        
        finally:
            self._notify_progress(task, progress_callback)
            
            # Clean up thread reference
            with self._lock:
                if task.task_id in self.download_threads:
                    del self.download_threads[task.task_id]
    
    def _attempt_download(self, task: DownloadTask, temp_path: Path, 
                         progress_callback: Optional[Callable[[DownloadTask], None]] = None) -> bool:
        """Attempt to download the file with resume support and comprehensive error handling."""
        headers = {}
        
        # Check for existing partial download
        if temp_path.exists() and task.resume_supported:
            try:
                existing_size = temp_path.stat().st_size
                if existing_size > 0:
                    headers['Range'] = f'bytes={existing_size}-'
                    task.downloaded_size = existing_size
                    logger.info(f"Resuming download from byte {existing_size}")
            except OSError as e:
                error_info = handle_permission_error(
                    str(temp_path), 
                    "check existing download",
                    {"model_id": task.model_id}
                )
                raise PermissionError(error_info, e)
        
        # Make download request with error handling
        try:
            response = self.session.get(task.url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
        except (ConnectionError, Timeout, HTTPError, RequestException) as e:
            error_info = handle_network_error(e, {
                "url": task.url, 
                "model_id": task.model_id,
                "operation": "download_request"
            })
            raise NetworkError(error_info, e)
        
        # Update total size if not set
        if task.total_size == 0:
            content_length = response.headers.get('content-length')
            if content_length:
                try:
                    if 'Range' in headers:
                        # For resumed downloads, add existing size
                        task.total_size = int(content_length) + task.downloaded_size
                    else:
                        task.total_size = int(content_length)
                        
                    # Validate disk space now that we know the size
                    try:
                        validate_disk_space(temp_path.parent, task.total_size - task.downloaded_size)
                    except DiskSpaceError as e:
                        raise e  # Re-raise disk space errors
                        
                except ValueError as e:
                    logger.warning(f"Invalid content-length header: {content_length}")
        
        # Open file for writing with error handling
        mode = 'ab' if temp_path.exists() and task.resume_supported else 'wb'
        
        try:
            with open(temp_path, mode) as f:
                start_time = time.time()
                last_update = start_time
                bytes_since_last_check = 0
                
                try:
                    for chunk in response.iter_content(chunk_size=8192):
                        # Check for cancellation
                        if task.status == 'cancelled' or self._shutdown:
                            logger.info(f"Download cancelled for {task.model_id}")
                            return False
                        
                        if chunk:
                            try:
                                f.write(chunk)
                                task.downloaded_size += len(chunk)
                                bytes_since_last_check += len(chunk)
                                
                                # Check disk space periodically (every 10MB)
                                if bytes_since_last_check >= 10 * 1024 * 1024:
                                    try:
                                        # Quick disk space check
                                        stat = shutil.disk_usage(temp_path.parent)
                                        if stat.free < 100 * 1024 * 1024:  # Less than 100MB free
                                            error_info = handle_disk_space_error(
                                                100 * 1024 * 1024, stat.free, str(temp_path.parent),
                                                {"model_id": task.model_id, "operation": "download_progress"}
                                            )
                                            raise DiskSpaceError(error_info)
                                    except OSError:
                                        pass  # Ignore disk check errors during download
                                    
                                    bytes_since_last_check = 0
                                
                                # Update progress and speed
                                current_time = time.time()
                                if current_time - last_update >= 0.5:  # Update every 0.5 seconds
                                    elapsed = current_time - start_time
                                    if elapsed > 0:
                                        task.download_speed = task.downloaded_size / elapsed
                                    
                                    if task.total_size > 0:
                                        task.progress = (task.downloaded_size / task.total_size) * 100
                                        
                                        # Estimate time remaining
                                        if task.download_speed > 0:
                                            remaining_bytes = task.total_size - task.downloaded_size
                                            task.estimated_time_remaining = remaining_bytes / task.download_speed
                                    
                                    self._notify_progress(task, progress_callback)
                                    last_update = current_time
                                    
                            except OSError as e:
                                if "No space left on device" in str(e) or e.errno == 28:
                                    # Disk full error
                                    stat = shutil.disk_usage(temp_path.parent)
                                    error_info = handle_disk_space_error(
                                        1024 * 1024, stat.free, str(temp_path.parent),
                                        {"model_id": task.model_id, "operation": "write_chunk"}
                                    )
                                    raise DiskSpaceError(error_info, e)
                                else:
                                    # Other file write errors
                                    error_info = handle_permission_error(
                                        str(temp_path), 
                                        "write to download file",
                                        {"model_id": task.model_id}
                                    )
                                    raise PermissionError(error_info, e)
                
                except (ConnectionError, Timeout, RequestException) as e:
                    # Network error during download
                    error_info = handle_network_error(e, {
                        "url": task.url, 
                        "model_id": task.model_id,
                        "operation": "download_stream",
                        "bytes_downloaded": task.downloaded_size
                    })
                    raise NetworkError(error_info, e)
        
        except OSError as e:
            # File open/access errors
            error_info = handle_permission_error(
                str(temp_path), 
                "open download file",
                {"model_id": task.model_id, "mode": mode}
            )
            raise PermissionError(error_info, e)
        
        return True
    
    def _validate_checksum(self, file_path: Path, expected_checksum: str, checksum_type: str) -> bool:
        """Validate file checksum."""
        if not expected_checksum or expected_checksum.startswith("placeholder"):
            return True  # Skip validation for placeholder checksums
        
        try:
            # Parse checksum format (e.g., "sha256:abc123" or just "abc123")
            if ':' in expected_checksum:
                hash_type, expected_hash = expected_checksum.split(':', 1)
            else:
                hash_type = checksum_type
                expected_hash = expected_checksum
            
            # Create hasher
            if hash_type.lower() == 'sha256':
                hasher = hashlib.sha256()
            elif hash_type.lower() == 'md5':
                hasher = hashlib.md5()
            elif hash_type.lower() == 'sha1':
                hasher = hashlib.sha1()
            else:
                logger.warning(f"Unsupported hash type: {hash_type}")
                return True  # Skip validation for unsupported types
            
            # Calculate file hash
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)
            
            actual_hash = hasher.hexdigest().lower()
            expected_hash = expected_hash.lower()
            
            if actual_hash == expected_hash:
                logger.info(f"Checksum validation passed for {file_path}")
                return True
            else:
                logger.error(f"Checksum validation failed for {file_path}. "
                           f"Expected: {expected_hash}, Got: {actual_hash}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to validate checksum for {file_path}: {e}")
            return False
    
    def _notify_progress(self, task: DownloadTask, callback: Optional[Callable[[DownloadTask], None]]):
        """Notify progress callback if provided."""
        if callback:
            try:
                callback(task)
            except Exception as e:
                logger.error(f"Progress callback failed: {e}")
    
    def cancel_download(self, task_id: str) -> bool:
        """Cancel active download."""
        with self._lock:
            if task_id in self.active_downloads:
                task = self.active_downloads[task_id]
                if task.status in ['pending', 'downloading']:
                    task.status = 'cancelled'
                    task.error_message = 'Download cancelled by user'
                    logger.info(f"Cancelled download task {task_id}")
                    return True
        return False
    
    def pause_download(self, task_id: str) -> bool:
        """Pause active download (if resume is supported)."""
        with self._lock:
            if task_id in self.active_downloads:
                task = self.active_downloads[task_id]
                if task.status == 'downloading' and task.resume_supported:
                    task.status = 'paused'
                    logger.info(f"Paused download task {task_id}")
                    return True
        return False
    
    def resume_download(self, task_id: str) -> bool:
        """Resume paused download."""
        with self._lock:
            if task_id in self.active_downloads:
                task = self.active_downloads[task_id]
                if task.status == 'paused':
                    task.status = 'downloading'
                    logger.info(f"Resumed download task {task_id}")
                    return True
        return False
    
    def get_download_status(self, task_id: str) -> Optional[DownloadTask]:
        """Get download task status."""
        with self._lock:
            return self.active_downloads.get(task_id)
    
    def get_all_downloads(self) -> List[DownloadTask]:
        """Get all download tasks."""
        with self._lock:
            return list(self.active_downloads.values())
    
    def cleanup_completed_downloads(self, max_age_hours: int = 24):
        """Clean up completed download tasks older than specified hours."""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        with self._lock:
            completed_tasks = []
            for task_id, task in self.active_downloads.items():
                if task.status in ['completed', 'failed', 'cancelled']:
                    age = current_time - task.created_at
                    if age > max_age_seconds:
                        completed_tasks.append(task_id)
            
            for task_id in completed_tasks:
                del self.active_downloads[task_id]
                logger.debug(f"Cleaned up old download task {task_id}")
            
            if completed_tasks:
                logger.info(f"Cleaned up {len(completed_tasks)} old download tasks")
    
    def get_download_statistics(self) -> Dict[str, Any]:
        """Get download statistics."""
        with self._lock:
            stats = {
                'total_downloads': len(self.active_downloads),
                'active_downloads': len([t for t in self.active_downloads.values() if t.status == 'downloading']),
                'completed_downloads': len([t for t in self.active_downloads.values() if t.status == 'completed']),
                'failed_downloads': len([t for t in self.active_downloads.values() if t.status == 'failed']),
                'cancelled_downloads': len([t for t in self.active_downloads.values() if t.status == 'cancelled']),
                'total_bytes_downloaded': sum(t.downloaded_size for t in self.active_downloads.values()),
                'average_download_speed': 0
            }
            
            # Calculate average download speed for active downloads
            active_downloads = [t for t in self.active_downloads.values() if t.status == 'downloading' and t.download_speed > 0]
            if active_downloads:
                stats['average_download_speed'] = sum(t.download_speed for t in active_downloads) / len(active_downloads)
            
            return stats
    
    def shutdown(self):
        """Shutdown the download manager gracefully."""
        logger.info("Shutting down ModelDownloadManager...")
        self._shutdown = True
        
        # Cancel all active downloads
        with self._lock:
            for task in self.active_downloads.values():
                if task.status in ['pending', 'downloading']:
                    task.status = 'cancelled'
                    task.error_message = 'Download cancelled due to shutdown'
        
        # Wait for threads to complete
        for thread in list(self.download_threads.values()):
            if thread.is_alive():
                thread.join(timeout=5)
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        # Close session
        self.session.close()
        
        logger.info("ModelDownloadManager shutdown complete")
    
    def __del__(self):
        """Cleanup on destruction."""
        if hasattr(self, '_shutdown') and not self._shutdown:
            self.shutdown()