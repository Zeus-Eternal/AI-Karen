"""
Unit tests for Model Download Manager

Tests the comprehensive model download management functionality including:
- Progress tracking and cancellation
- Resumable downloads with retry logic
- Checksum validation and secure HTTPS support
- Exponential backoff for network failures
- Disk space validation
"""

import hashlib
import pytest
import tempfile
import time
import threading
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock, mock_open
from requests.exceptions import ConnectionError, Timeout, HTTPError

from src.ai_karen_engine.services.model_download_manager import (
    ModelDownloadManager,
    DownloadTask
)
from src.ai_karen_engine.utils.error_handling import (
    NetworkError, DiskSpaceError, PermissionError, ValidationError
)


class TestModelDownloadManager:
    """Test cases for ModelDownloadManager."""
    
    @pytest.fixture
    def temp_download_dir(self):
        """Create temporary download directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def download_manager(self, temp_download_dir):
        """Create download manager instance."""
        return ModelDownloadManager(download_dir=temp_download_dir, max_concurrent_downloads=2)
    
    def test_manager_initialization(self, download_manager, temp_download_dir):
        """Test download manager initialization."""
        assert download_manager.download_dir == Path(temp_download_dir)
        assert download_manager.max_concurrent_downloads == 2
        assert len(download_manager.active_downloads) == 0
        assert len(download_manager.download_threads) == 0
        assert download_manager.session is not None
        assert download_manager.download_dir.exists()
    
    def test_create_secure_session(self, download_manager):
        """Test secure session creation."""
        session = download_manager._create_secure_session()
        
        assert session is not None
        assert 'User-Agent' in session.headers
        assert session.verify is True
        
        # Check retry strategy is configured
        adapter = session.get_adapter('https://')
        assert adapter is not None
    
    @patch('shutil.disk_usage')
    def test_validate_disk_space_sufficient(self, mock_disk_usage, download_manager):
        """Test disk space validation with sufficient space."""
        # Mock 5GB free space
        mock_usage = Mock()
        mock_usage.free = 5 * 1024 * 1024 * 1024
        mock_disk_usage.return_value = mock_usage
        
        # Request 1GB
        result = download_manager.validate_disk_space(1024 * 1024 * 1024)
        assert result is True
    
    @patch('shutil.disk_usage')
    def test_validate_disk_space_insufficient(self, mock_disk_usage, download_manager):
        """Test disk space validation with insufficient space."""
        # Mock 500MB free space
        mock_usage = Mock()
        mock_usage.free = 500 * 1024 * 1024
        mock_disk_usage.return_value = mock_usage
        
        # Request 1GB
        result = download_manager.validate_disk_space(1024 * 1024 * 1024)
        assert result is False
    
    def test_validate_url_security_https(self, download_manager):
        """Test URL security validation with HTTPS."""
        result = download_manager._validate_url_security("https://example.com/model.gguf")
        assert result is True
    
    def test_validate_url_security_http(self, download_manager):
        """Test URL security validation with HTTP (should fail)."""
        result = download_manager._validate_url_security("http://example.com/model.gguf")
        assert result is False
    
    def test_validate_url_security_localhost(self, download_manager):
        """Test URL security validation with localhost (should fail)."""
        result = download_manager._validate_url_security("https://localhost/model.gguf")
        assert result is False
    
    def test_validate_url_security_invalid(self, download_manager):
        """Test URL security validation with invalid URL."""
        result = download_manager._validate_url_security("not-a-url")
        assert result is False
    
    @patch('requests.Session.head')
    def test_download_model_success_initiation(self, mock_head, download_manager):
        """Test successful download initiation."""
        # Mock HEAD response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {
            'content-length': '1000000',
            'accept-ranges': 'bytes'
        }
        mock_response.raise_for_status.return_value = None
        mock_head.return_value = mock_response
        
        with patch('shutil.disk_usage') as mock_disk_usage:
            mock_usage = Mock()
            mock_usage.free = 5 * 1024 * 1024 * 1024  # 5GB free
            mock_disk_usage.return_value = mock_usage
            
            task = download_manager.download_model(
                model_id="test-model",
                url="https://example.com/model.gguf",
                filename="model.gguf"
            )
            
            assert task is not None
            assert task.model_id == "test-model"
            assert task.url == "https://example.com/model.gguf"
            assert task.filename == "model.gguf"
            assert task.total_size == 1000000
            assert task.resume_supported is True
            assert task.task_id in download_manager.active_downloads
    
    def test_download_model_insecure_url(self, download_manager):
        """Test download with insecure URL."""
        with pytest.raises(ValidationError):
            download_manager.download_model(
                model_id="test-model",
                url="http://example.com/model.gguf",
                filename="model.gguf"
            )
    
    @patch('requests.Session.head')
    def test_download_model_insufficient_disk_space(self, mock_head, download_manager):
        """Test download with insufficient disk space."""
        # Mock HEAD response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-length': '5000000000'}  # 5GB
        mock_response.raise_for_status.return_value = None
        mock_head.return_value = mock_response
        
        with patch('shutil.disk_usage') as mock_disk_usage:
            mock_usage = Mock()
            mock_usage.free = 1024 * 1024 * 1024  # 1GB free
            mock_disk_usage.return_value = mock_usage
            
            task = download_manager.download_model(
                model_id="test-model",
                url="https://example.com/model.gguf",
                filename="model.gguf"
            )
            
            assert task.status == 'failed'
            assert 'disk space' in task.error_message.lower()
    
    def test_download_model_max_concurrent_reached(self, download_manager):
        """Test download when max concurrent downloads reached."""
        # Fill up active downloads
        for i in range(download_manager.max_concurrent_downloads):
            download_manager.active_downloads[f"task-{i}"] = Mock()
        
        task = download_manager.download_model(
            model_id="test-model",
            url="https://example.com/model.gguf",
            filename="model.gguf"
        )
        
        assert task.status == 'failed'
        assert 'maximum concurrent downloads' in task.error_message.lower()
    
    @patch('requests.Session.head')
    @patch('requests.Session.get')
    def test_attempt_download_success(self, mock_get, mock_head, download_manager, temp_download_dir):
        """Test successful download attempt."""
        # Mock HEAD response
        mock_head_response = Mock()
        mock_head_response.status_code = 200
        mock_head_response.headers = {'content-length': '100'}
        mock_head_response.raise_for_status.return_value = None
        mock_head.return_value = mock_head_response
        
        # Mock GET response
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.headers = {'content-length': '100'}
        mock_get_response.iter_content.return_value = [b'x' * 50, b'y' * 50]
        mock_get_response.raise_for_status.return_value = None
        mock_get.return_value = mock_get_response
        
        # Create task
        task = DownloadTask(
            task_id="test-task",
            model_id="test-model",
            url="https://example.com/model.gguf",
            filename="model.gguf",
            destination_path=str(Path(temp_download_dir) / "model.gguf"),
            total_size=100,
            start_time=time.time()
        )
        
        temp_path = Path(task.destination_path + '.tmp')
        
        with patch('shutil.disk_usage') as mock_disk_usage:
            mock_usage = Mock()
            mock_usage.free = 5 * 1024 * 1024 * 1024  # 5GB free
            mock_disk_usage.return_value = mock_usage
            
            result = download_manager._attempt_download(task, temp_path)
            
            assert result is True
            assert task.downloaded_size == 100
            assert task.progress == 100.0
            assert temp_path.exists()
            assert temp_path.read_bytes() == b'x' * 50 + b'y' * 50
    
    @patch('requests.Session.get')
    def test_attempt_download_network_error(self, mock_get, download_manager, temp_download_dir):
        """Test download attempt with network error."""
        # Mock network error
        mock_get.side_effect = ConnectionError("Network error")
        
        task = DownloadTask(
            task_id="test-task",
            model_id="test-model",
            url="https://example.com/model.gguf",
            filename="model.gguf",
            destination_path=str(Path(temp_download_dir) / "model.gguf"),
            start_time=time.time()
        )
        
        temp_path = Path(task.destination_path + '.tmp')
        
        with pytest.raises(NetworkError):
            download_manager._attempt_download(task, temp_path)
    
    @patch('requests.Session.get')
    def test_attempt_download_resume(self, mock_get, download_manager, temp_download_dir):
        """Test download resume functionality."""
        # Create partial download file
        temp_path = Path(temp_download_dir) / "model.gguf.tmp"
        temp_path.write_bytes(b'x' * 50)  # 50 bytes already downloaded
        
        # Mock GET response for resume
        mock_response = Mock()
        mock_response.status_code = 206  # Partial content
        mock_response.headers = {'content-length': '50'}
        mock_response.iter_content.return_value = [b'y' * 50]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        task = DownloadTask(
            task_id="test-task",
            model_id="test-model",
            url="https://example.com/model.gguf",
            filename="model.gguf",
            destination_path=str(Path(temp_download_dir) / "model.gguf"),
            total_size=100,
            resume_supported=True,
            start_time=time.time()
        )
        
        with patch('shutil.disk_usage') as mock_disk_usage:
            mock_usage = Mock()
            mock_usage.free = 5 * 1024 * 1024 * 1024  # 5GB free
            mock_disk_usage.return_value = mock_usage
            
            result = download_manager._attempt_download(task, temp_path)
            
            assert result is True
            assert task.downloaded_size == 100  # 50 existing + 50 new
            assert temp_path.read_bytes() == b'x' * 50 + b'y' * 50
            
            # Verify Range header was used
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert 'Range' in call_args[1]['headers']
            assert call_args[1]['headers']['Range'] == 'bytes=50-'
    
    def test_validate_checksum_sha256_success(self, download_manager, temp_download_dir):
        """Test successful SHA256 checksum validation."""
        # Create test file
        test_file = Path(temp_download_dir) / "test_file.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        # Calculate expected hash
        expected_hash = hashlib.sha256(test_content).hexdigest()
        
        result = download_manager._validate_checksum(test_file, expected_hash, 'sha256')
        assert result is True
    
    def test_validate_checksum_sha256_failure(self, download_manager, temp_download_dir):
        """Test SHA256 checksum validation failure."""
        # Create test file
        test_file = Path(temp_download_dir) / "test_file.txt"
        test_file.write_bytes(b"Hello, World!")
        
        # Use wrong hash
        wrong_hash = "wrong_hash_value"
        
        result = download_manager._validate_checksum(test_file, wrong_hash, 'sha256')
        assert result is False
    
    def test_validate_checksum_with_prefix(self, download_manager, temp_download_dir):
        """Test checksum validation with algorithm prefix."""
        # Create test file
        test_file = Path(temp_download_dir) / "test_file.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        # Calculate expected hash with prefix
        expected_hash = hashlib.sha256(test_content).hexdigest()
        checksum_with_prefix = f"sha256:{expected_hash}"
        
        result = download_manager._validate_checksum(test_file, checksum_with_prefix, 'md5')
        assert result is True  # Should use sha256 from prefix, not md5 from parameter
    
    def test_validate_checksum_md5(self, download_manager, temp_download_dir):
        """Test MD5 checksum validation."""
        # Create test file
        test_file = Path(temp_download_dir) / "test_file.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        # Calculate expected MD5 hash
        expected_hash = hashlib.md5(test_content).hexdigest()
        
        result = download_manager._validate_checksum(test_file, expected_hash, 'md5')
        assert result is True
    
    def test_validate_checksum_placeholder(self, download_manager, temp_download_dir):
        """Test checksum validation with placeholder."""
        # Create test file
        test_file = Path(temp_download_dir) / "test_file.txt"
        test_file.write_bytes(b"Hello, World!")
        
        # Use placeholder checksum
        placeholder = "placeholder_checksum_for_validation"
        
        result = download_manager._validate_checksum(test_file, placeholder, 'sha256')
        assert result is True  # Should skip validation for placeholders
    
    def test_validate_checksum_unsupported_algorithm(self, download_manager, temp_download_dir):
        """Test checksum validation with unsupported algorithm."""
        # Create test file
        test_file = Path(temp_download_dir) / "test_file.txt"
        test_file.write_bytes(b"Hello, World!")
        
        result = download_manager._validate_checksum(test_file, "some_hash", 'unsupported')
        assert result is True  # Should skip validation for unsupported algorithms
    
    def test_cancel_download(self, download_manager):
        """Test download cancellation."""
        # Create mock task
        task = DownloadTask(
            task_id="cancel-test",
            model_id="test-model",
            url="https://example.com/model.gguf",
            filename="model.gguf",
            destination_path="/tmp/model.gguf",
            status="downloading"
        )
        
        download_manager.active_downloads["cancel-test"] = task
        
        result = download_manager.cancel_download("cancel-test")
        
        assert result is True
        assert task.status == 'cancelled'
    
    def test_cancel_download_not_found(self, download_manager):
        """Test canceling non-existent download."""
        result = download_manager.cancel_download("non-existent")
        assert result is False
    
    def test_get_download_status(self, download_manager):
        """Test getting download status."""
        # Create mock task
        task = DownloadTask(
            task_id="status-test",
            model_id="test-model",
            url="https://example.com/model.gguf",
            filename="model.gguf",
            destination_path="/tmp/model.gguf",
            progress=75.0,
            status="downloading"
        )
        
        download_manager.active_downloads["status-test"] = task
        
        retrieved_task = download_manager.get_download_status("status-test")
        
        assert retrieved_task is not None
        assert retrieved_task.task_id == "status-test"
        assert retrieved_task.progress == 75.0
        assert retrieved_task.status == "downloading"
    
    def test_get_download_status_not_found(self, download_manager):
        """Test getting status for non-existent download."""
        result = download_manager.get_download_status("non-existent")
        assert result is None
    
    def test_cleanup_completed_downloads(self, download_manager):
        """Test cleanup of completed downloads."""
        # Create tasks with different statuses
        completed_task = DownloadTask(
            task_id="completed",
            model_id="model1",
            url="https://example.com/model1.gguf",
            filename="model1.gguf",
            destination_path="/tmp/model1.gguf",
            status="completed"
        )
        
        failed_task = DownloadTask(
            task_id="failed",
            model_id="model2",
            url="https://example.com/model2.gguf",
            filename="model2.gguf",
            destination_path="/tmp/model2.gguf",
            status="failed"
        )
        
        downloading_task = DownloadTask(
            task_id="downloading",
            model_id="model3",
            url="https://example.com/model3.gguf",
            filename="model3.gguf",
            destination_path="/tmp/model3.gguf",
            status="downloading"
        )
        
        download_manager.active_downloads.update({
            "completed": completed_task,
            "failed": failed_task,
            "downloading": downloading_task
        })
        
        download_manager.cleanup_completed_downloads()
        
        # Only downloading task should remain
        assert len(download_manager.active_downloads) == 1
        assert "downloading" in download_manager.active_downloads
        assert "completed" not in download_manager.active_downloads
        assert "failed" not in download_manager.active_downloads
    
    def test_notify_progress_callback(self, download_manager):
        """Test progress notification callback."""
        callback = Mock()
        
        task = DownloadTask(
            task_id="callback-test",
            model_id="test-model",
            url="https://example.com/model.gguf",
            filename="model.gguf",
            destination_path="/tmp/model.gguf",
            progress=50.0
        )
        
        download_manager._notify_progress(task, callback)
        
        callback.assert_called_once_with(task)
    
    def test_notify_progress_callback_exception(self, download_manager):
        """Test progress notification with callback exception."""
        callback = Mock()
        callback.side_effect = Exception("Callback error")
        
        task = DownloadTask(
            task_id="callback-error-test",
            model_id="test-model",
            url="https://example.com/model.gguf",
            filename="model.gguf",
            destination_path="/tmp/model.gguf",
            progress=50.0
        )
        
        # Should not raise exception
        download_manager._notify_progress(task, callback)
        
        callback.assert_called_once_with(task)
    
    @patch('requests.Session.head')
    @patch('threading.Thread')
    def test_download_worker_thread_creation(self, mock_thread, mock_head, download_manager):
        """Test that download worker thread is created."""
        # Mock HEAD response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-length': '1000'}
        mock_response.raise_for_status.return_value = None
        mock_head.return_value = mock_response
        
        with patch('shutil.disk_usage') as mock_disk_usage:
            mock_usage = Mock()
            mock_usage.free = 5 * 1024 * 1024 * 1024  # 5GB free
            mock_disk_usage.return_value = mock_usage
            
            task = download_manager.download_model(
                model_id="thread-test",
                url="https://example.com/model.gguf",
                filename="model.gguf"
            )
            
            # Verify thread was created and started
            mock_thread.assert_called_once()
            thread_instance = mock_thread.return_value
            thread_instance.start.assert_called_once()
            
            assert task.task_id in download_manager.download_threads
    
    def test_download_task_dataclass(self):
        """Test DownloadTask dataclass functionality."""
        task = DownloadTask(
            task_id="dataclass-test",
            model_id="test-model",
            url="https://example.com/model.gguf",
            filename="model.gguf",
            destination_path="/tmp/model.gguf",
            total_size=1000000,
            downloaded_size=500000,
            progress=50.0,
            status="downloading",
            error_message=None,
            start_time=1234567890,
            end_time=None,
            estimated_time_remaining=120.0,
            download_speed=8192.0,
            retry_count=1,
            max_retries=3,
            checksum="sha256:abc123",
            checksum_type="sha256",
            resume_supported=True,
            created_at=1234567800
        )
        
        # Test to_dict method
        task_dict = task.to_dict()
        
        assert isinstance(task_dict, dict)
        assert task_dict['task_id'] == "dataclass-test"
        assert task_dict['model_id'] == "test-model"
        assert task_dict['progress'] == 50.0
        assert task_dict['status'] == "downloading"
        assert task_dict['download_speed'] == 8192.0
        assert task_dict['retry_count'] == 1
        assert task_dict['checksum'] == "sha256:abc123"
        assert task_dict['resume_supported'] is True
    
    @patch('requests.Session.head')
    def test_download_model_network_error_during_head(self, mock_head, download_manager):
        """Test download when HEAD request fails with network error."""
        # Mock network error during HEAD request
        mock_head.side_effect = ConnectionError("Network error")
        
        with patch('shutil.disk_usage') as mock_disk_usage:
            mock_usage = Mock()
            mock_usage.free = 5 * 1024 * 1024 * 1024  # 5GB free
            mock_disk_usage.return_value = mock_usage
            
            # Should still create task but without file size info
            task = download_manager.download_model(
                model_id="network-error-test",
                url="https://example.com/model.gguf",
                filename="model.gguf"
            )
            
            assert task is not None
            assert task.total_size == 0  # No size info available
            assert task.resume_supported is False  # Default value
    
    def test_concurrent_download_limit(self, download_manager):
        """Test concurrent download limit enforcement."""
        # Set max concurrent to 1 for this test
        download_manager.max_concurrent_downloads = 1
        
        # Add one active download
        download_manager.active_downloads["existing"] = Mock()
        
        # Try to add another
        task = download_manager.download_model(
            model_id="concurrent-test",
            url="https://example.com/model.gguf",
            filename="model.gguf"
        )
        
        assert task.status == 'failed'
        assert 'maximum concurrent downloads' in task.error_message.lower()


class TestDownloadTaskDataclass:
    """Test cases for DownloadTask dataclass."""
    
    def test_download_task_creation_minimal(self):
        """Test creating DownloadTask with minimal required fields."""
        task = DownloadTask(
            task_id="minimal-task",
            model_id="minimal-model",
            url="https://example.com/model.gguf",
            filename="model.gguf",
            destination_path="/tmp/model.gguf"
        )
        
        assert task.task_id == "minimal-task"
        assert task.model_id == "minimal-model"
        assert task.url == "https://example.com/model.gguf"
        assert task.filename == "model.gguf"
        assert task.destination_path == "/tmp/model.gguf"
        
        # Check default values
        assert task.total_size == 0
        assert task.downloaded_size == 0
        assert task.progress == 0.0
        assert task.status == 'pending'
        assert task.error_message is None
        assert task.start_time is None
        assert task.end_time is None
        assert task.estimated_time_remaining is None
        assert task.download_speed == 0.0
        assert task.retry_count == 0
        assert task.max_retries == 3
        assert task.checksum is None
        assert task.checksum_type == 'sha256'
        assert task.resume_supported is False
        assert task.created_at is not None  # Should be set by field factory
    
    def test_download_task_to_dict_complete(self):
        """Test converting complete DownloadTask to dictionary."""
        current_time = time.time()
        
        task = DownloadTask(
            task_id="complete-task",
            model_id="complete-model",
            url="https://example.com/model.gguf",
            filename="model.gguf",
            destination_path="/tmp/model.gguf",
            total_size=2000000,
            downloaded_size=1500000,
            progress=75.0,
            status="downloading",
            error_message=None,
            start_time=current_time - 100,
            end_time=None,
            estimated_time_remaining=25.0,
            download_speed=61440.0,  # 60 KB/s
            retry_count=0,
            max_retries=5,
            checksum="sha256:def456",
            checksum_type="sha256",
            resume_supported=True,
            created_at=current_time - 200
        )
        
        task_dict = task.to_dict()
        
        # Verify all fields are present and correct
        expected_fields = [
            'task_id', 'model_id', 'url', 'filename', 'destination_path',
            'total_size', 'downloaded_size', 'progress', 'status', 'error_message',
            'start_time', 'end_time', 'estimated_time_remaining', 'download_speed',
            'retry_count', 'max_retries', 'checksum', 'checksum_type',
            'resume_supported', 'created_at'
        ]
        
        for field in expected_fields:
            assert field in task_dict
        
        assert task_dict['task_id'] == "complete-task"
        assert task_dict['model_id'] == "complete-model"
        assert task_dict['total_size'] == 2000000
        assert task_dict['downloaded_size'] == 1500000
        assert task_dict['progress'] == 75.0
        assert task_dict['status'] == "downloading"
        assert task_dict['download_speed'] == 61440.0
        assert task_dict['max_retries'] == 5
        assert task_dict['checksum'] == "sha256:def456"
        assert task_dict['resume_supported'] is True


if __name__ == '__main__':
    pytest.main([__file__])