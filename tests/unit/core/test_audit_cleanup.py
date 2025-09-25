"""
Tests for audit log cleanup utilities.

This module tests the audit cleanup service to ensure it properly
manages log files and cleanup operations.
"""

import pytest
import os
import gzip
import tempfile
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from ai_karen_engine.services.audit_cleanup import (
    AuditLogCleanupService,
    get_audit_cleanup_service
)


class TestAuditLogCleanupService:
    """Test cases for AuditLogCleanupService class"""
    
    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary log directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def cleanup_service(self, temp_log_dir):
        """Create cleanup service with temporary directory"""
        with patch('ai_karen_engine.services.audit_cleanup.get_audit_logger') as mock_audit:
            with patch('ai_karen_engine.services.audit_cleanup.get_audit_deduplication_service') as mock_dedup:
                mock_audit.return_value = Mock()
                mock_dedup.return_value = Mock()
                service = AuditLogCleanupService(str(temp_log_dir))
                return service
    
    def create_test_log_file(self, log_dir: Path, filename: str, content: str = "test log content", age_days: int = 0):
        """Helper to create test log files with specific age"""
        log_file = log_dir / filename
        log_file.write_text(content)
        
        # Set file modification time
        if age_days > 0:
            old_time = datetime.now(timezone.utc) - timedelta(days=age_days)
            timestamp = old_time.timestamp()
            os.utime(log_file, (timestamp, timestamp))
        
        return log_file
    
    def test_cleanup_service_initialization(self, temp_log_dir):
        """Test cleanup service initialization"""
        service = AuditLogCleanupService(str(temp_log_dir))
        
        assert service.log_directory == temp_log_dir
        assert service.audit_logger is not None
        assert service.deduplication_service is not None
    
    def test_cleanup_old_log_files_no_files(self, cleanup_service, temp_log_dir):
        """Test cleanup when no log files exist"""
        stats = cleanup_service.cleanup_old_log_files(max_age_days=30)
        
        assert stats["files_processed"] == 0
        assert stats["files_compressed"] == 0
        assert stats["files_deleted"] == 0
        assert stats["bytes_saved"] == 0
        assert len(stats["errors"]) == 0
    
    def test_cleanup_old_log_files_recent_files(self, cleanup_service, temp_log_dir):
        """Test cleanup with recent files (should not be deleted)"""
        # Create recent log files
        self.create_test_log_file(temp_log_dir, "audit.log", "recent log", age_days=1)
        self.create_test_log_file(temp_log_dir, "auth_audit.log", "recent auth log", age_days=5)
        
        stats = cleanup_service.cleanup_old_log_files(max_age_days=30)
        
        assert stats["files_processed"] == 0
        assert stats["files_compressed"] == 0
        assert stats["files_deleted"] == 0
        
        # Files should still exist
        assert (temp_log_dir / "audit.log").exists()
        assert (temp_log_dir / "auth_audit.log").exists()
    
    def test_cleanup_old_log_files_with_compression(self, cleanup_service, temp_log_dir):
        """Test cleanup of old files with compression"""
        # Create old log files
        old_content = "old log content that should be compressed"
        self.create_test_log_file(temp_log_dir, "audit.log", old_content, age_days=35)
        self.create_test_log_file(temp_log_dir, "performance.log", old_content, age_days=40)
        
        stats = cleanup_service.cleanup_old_log_files(
            max_age_days=30,
            compress_before_delete=True
        )
        
        assert stats["files_processed"] == 2
        assert stats["files_compressed"] == 2
        assert stats["files_deleted"] == 2
        assert stats["bytes_saved"] > 0
        
        # Original files should be deleted
        assert not (temp_log_dir / "audit.log").exists()
        assert not (temp_log_dir / "performance.log").exists()
        
        # Compressed files should exist
        assert (temp_log_dir / "audit.log.gz").exists()
        assert (temp_log_dir / "performance.log.gz").exists()
        
        # Verify compressed content
        with gzip.open(temp_log_dir / "audit.log.gz", 'rt') as f:
            assert f.read() == old_content
    
    def test_cleanup_old_log_files_without_compression(self, cleanup_service, temp_log_dir):
        """Test cleanup of old files without compression"""
        # Create old log files
        old_content = "old log content to be deleted"
        log_file = self.create_test_log_file(temp_log_dir, "audit.log", old_content, age_days=35)
        original_size = log_file.stat().st_size
        
        stats = cleanup_service.cleanup_old_log_files(
            max_age_days=30,
            compress_before_delete=False
        )
        
        assert stats["files_processed"] == 1
        assert stats["files_compressed"] == 0
        assert stats["files_deleted"] == 1
        assert stats["bytes_saved"] == original_size
        
        # File should be deleted
        assert not (temp_log_dir / "audit.log").exists()
        
        # No compressed file should exist
        assert not (temp_log_dir / "audit.log.gz").exists()
    
    def test_cleanup_old_log_files_skip_compressed(self, cleanup_service, temp_log_dir):
        """Test that already compressed files are skipped"""
        # Create old compressed file
        compressed_file = temp_log_dir / "old_audit.log.gz"
        with gzip.open(compressed_file, 'wt') as f:
            f.write("already compressed content")
        
        # Set old modification time
        old_time = datetime.now(timezone.utc) - timedelta(days=35)
        timestamp = old_time.timestamp()
        os.utime(compressed_file, (timestamp, timestamp))
        
        stats = cleanup_service.cleanup_old_log_files(max_age_days=30)
        
        assert stats["files_processed"] == 0
        
        # Compressed file should still exist
        assert compressed_file.exists()
    
    def test_cleanup_old_log_files_custom_patterns(self, cleanup_service, temp_log_dir):
        """Test cleanup with custom file patterns"""
        # Create various log files
        self.create_test_log_file(temp_log_dir, "audit.log", "audit", age_days=35)
        self.create_test_log_file(temp_log_dir, "custom.log", "custom", age_days=35)
        self.create_test_log_file(temp_log_dir, "other.log", "other", age_days=35)
        
        stats = cleanup_service.cleanup_old_log_files(
            max_age_days=30,
            file_patterns=["custom*.log"]  # Only match custom files
        )
        
        assert stats["files_processed"] == 1
        assert stats["files_deleted"] == 1
        
        # Only custom.log should be processed
        assert (temp_log_dir / "audit.log").exists()
        assert not (temp_log_dir / "custom.log").exists()
        assert (temp_log_dir / "other.log").exists()
    
    def test_cleanup_duplicate_events(self, cleanup_service):
        """Test cleanup of duplicate event tracking"""
        # Mock deduplication service
        mock_dedup = cleanup_service.deduplication_service
        mock_dedup.get_event_stats.side_effect = [
            {"local_events_count": 10},  # Before cleanup
            {"local_events_count": 5}    # After cleanup
        ]
        
        stats = cleanup_service.cleanup_duplicate_events()
        
        assert stats["events_before"] == 10
        assert stats["events_after"] == 5
        assert stats["events_cleaned"] == 5
        assert "timestamp" in stats
        
        # Verify cleanup was called
        mock_dedup._cleanup_expired_events.assert_called_once()
    
    def test_get_log_file_stats_empty_directory(self, cleanup_service, temp_log_dir):
        """Test getting stats from empty directory"""
        stats = cleanup_service.get_log_file_stats()
        
        assert stats["total_files"] == 0
        assert stats["total_size_bytes"] == 0
        assert stats["compressed_files"] == 0
        assert stats["uncompressed_files"] == 0
        assert stats["oldest_file"] is None
        assert stats["newest_file"] is None
        assert "timestamp" in stats
    
    def test_get_log_file_stats_with_files(self, cleanup_service, temp_log_dir):
        """Test getting stats with various log files"""
        # Create uncompressed files
        log1 = self.create_test_log_file(temp_log_dir, "audit.log", "content1", age_days=1)
        log2 = self.create_test_log_file(temp_log_dir, "performance.log", "content2", age_days=5)
        
        # Create compressed file
        compressed_file = temp_log_dir / "old_audit.log.gz"
        with gzip.open(compressed_file, 'wt') as f:
            f.write("compressed content")
        
        # Set old modification time for compressed file
        old_time = datetime.now(timezone.utc) - timedelta(days=10)
        timestamp = old_time.timestamp()
        os.utime(compressed_file, (timestamp, timestamp))
        
        stats = cleanup_service.get_log_file_stats()
        
        assert stats["total_files"] == 3
        assert stats["uncompressed_files"] == 2
        assert stats["compressed_files"] == 1
        assert stats["total_size_bytes"] > 0
        assert stats["uncompressed_size_bytes"] > 0
        assert stats["compressed_size_bytes"] > 0
        
        # Check oldest/newest file tracking
        assert stats["oldest_file"] is not None
        assert stats["newest_file"] is not None
        assert stats["oldest_file"]["name"] == "old_audit.log.gz"
    
    def test_rotate_current_logs_no_rotation_needed(self, cleanup_service, temp_log_dir):
        """Test log rotation when files are small"""
        # Create small log files
        self.create_test_log_file(temp_log_dir, "audit.log", "small content")
        self.create_test_log_file(temp_log_dir, "performance.log", "small content")
        
        stats = cleanup_service.rotate_current_logs(max_size_mb=1)  # 1MB limit
        
        assert stats["files_rotated"] == 0
        assert stats["files_checked"] == 2
        assert len(stats["errors"]) == 0
        
        # Files should still exist with original names
        assert (temp_log_dir / "audit.log").exists()
        assert (temp_log_dir / "performance.log").exists()
    
    def test_rotate_current_logs_rotation_needed(self, cleanup_service, temp_log_dir):
        """Test log rotation when files are large"""
        # Create large log file (simulate with small limit)
        large_content = "x" * 1000  # 1KB content
        self.create_test_log_file(temp_log_dir, "audit.log", large_content)
        
        stats = cleanup_service.rotate_current_logs(max_size_mb=0.0001)  # Very small limit
        
        assert stats["files_rotated"] == 1
        assert stats["files_checked"] == 1
        assert len(stats["errors"]) == 0
        
        # Original file should be empty (new file created)
        assert (temp_log_dir / "audit.log").exists()
        assert (temp_log_dir / "audit.log").stat().st_size == 0
        
        # Rotated file should exist with timestamp suffix
        rotated_files = list(temp_log_dir.glob("audit_*.log"))
        assert len(rotated_files) == 1
        assert rotated_files[0].read_text() == large_content
    
    def test_cleanup_all_comprehensive(self, cleanup_service, temp_log_dir):
        """Test comprehensive cleanup operation"""
        # Create various test files
        self.create_test_log_file(temp_log_dir, "audit.log", "x" * 1000)  # Large current file
        self.create_test_log_file(temp_log_dir, "old_audit.log", "old content", age_days=35)  # Old file
        self.create_test_log_file(temp_log_dir, "performance.log", "perf content")  # Recent file
        
        # Mock deduplication service
        mock_dedup = cleanup_service.deduplication_service
        mock_dedup.get_event_stats.side_effect = [
            {"local_events_count": 5},  # Before cleanup
            {"local_events_count": 2}   # After cleanup
        ]
        
        stats = cleanup_service.cleanup_all(
            max_age_days=30,
            max_size_mb=0.0001,  # Very small to force rotation
            compress_old_files=True
        )
        
        assert "started_at" in stats
        assert "completed_at" in stats
        assert "file_cleanup" in stats
        assert "duplicate_cleanup" in stats
        assert "rotation" in stats
        assert "final_stats" in stats
        
        # Check that all operations were performed
        assert stats["duplicate_cleanup"]["events_cleaned"] == 3
        assert stats["rotation"]["files_rotated"] >= 1
        assert stats["file_cleanup"]["files_processed"] >= 1
        assert stats["final_stats"]["total_files"] >= 0
    
    def test_cleanup_all_with_errors(self, cleanup_service, temp_log_dir):
        """Test comprehensive cleanup with errors"""
        # Mock an error in one of the cleanup operations
        with patch.object(cleanup_service, 'cleanup_duplicate_events') as mock_cleanup:
            mock_cleanup.side_effect = Exception("Test error")
            
            stats = cleanup_service.cleanup_all()
            
            assert "error" in stats
            assert "completed_at" in stats
            assert stats["error"] == "Test error"
    
    def test_nonexistent_log_directory(self, temp_log_dir):
        """Test behavior with non-existent log directory"""
        # Remove the directory
        shutil.rmtree(temp_log_dir)
        
        service = AuditLogCleanupService(str(temp_log_dir))
        stats = service.cleanup_old_log_files()
        
        assert stats["files_processed"] == 0
        assert len(stats["errors"]) == 0


class TestGlobalInstance:
    """Test cases for global instance management"""
    
    def test_get_audit_cleanup_service(self):
        """Test getting global cleanup service instance"""
        service1 = get_audit_cleanup_service()
        service2 = get_audit_cleanup_service()
        
        # Should return the same instance
        assert service1 is service2
        assert isinstance(service1, AuditLogCleanupService)
    
    def test_get_audit_cleanup_service_custom_directory(self):
        """Test getting cleanup service with custom directory"""
        service = get_audit_cleanup_service("/custom/log/dir")
        
        assert str(service.log_directory) == "/custom/log/dir"


class TestErrorHandling:
    """Test cases for error handling scenarios"""
    
    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary log directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def cleanup_service(self, temp_log_dir):
        """Create cleanup service with temporary directory"""
        with patch('ai_karen_engine.services.audit_cleanup.get_audit_logger') as mock_audit:
            with patch('ai_karen_engine.services.audit_cleanup.get_audit_deduplication_service') as mock_dedup:
                mock_audit.return_value = Mock()
                mock_dedup.return_value = Mock()
                service = AuditLogCleanupService(str(temp_log_dir))
                return service
    
    def test_cleanup_with_permission_error(self, cleanup_service, temp_log_dir):
        """Test cleanup when file permissions prevent deletion"""
        # Create a log file
        log_file = temp_log_dir / "audit.log"
        log_file.write_text("test content")
        
        # Set old modification time
        old_time = datetime.now(timezone.utc) - timedelta(days=35)
        timestamp = old_time.timestamp()
        os.utime(log_file, (timestamp, timestamp))
        
        # Mock permission error
        with patch('pathlib.Path.unlink') as mock_unlink:
            mock_unlink.side_effect = PermissionError("Permission denied")
            
            stats = cleanup_service.cleanup_old_log_files(
                max_age_days=30,
                compress_before_delete=False
            )
            
            assert stats["files_processed"] == 1
            assert stats["files_deleted"] == 0
            assert len(stats["errors"]) == 1
            assert "Permission denied" in stats["errors"][0]
    
    def test_compression_failure(self, cleanup_service, temp_log_dir):
        """Test behavior when compression fails"""
        # Create a log file
        log_file = temp_log_dir / "audit.log"
        log_file.write_text("test content")
        
        # Set old modification time
        old_time = datetime.now(timezone.utc) - timedelta(days=35)
        timestamp = old_time.timestamp()
        os.utime(log_file, (timestamp, timestamp))
        
        # Mock compression failure
        with patch('gzip.open') as mock_gzip:
            mock_gzip.side_effect = OSError("Compression failed")
            
            stats = cleanup_service.cleanup_old_log_files(
                max_age_days=30,
                compress_before_delete=True
            )
            
            assert stats["files_processed"] == 1
            assert stats["files_compressed"] == 0
            assert len(stats["errors"]) == 1
            assert "Compression failed" in stats["errors"][0]
    
    def test_deduplication_service_error(self, cleanup_service):
        """Test behavior when deduplication service fails"""
        # Mock deduplication service error
        mock_dedup = cleanup_service.deduplication_service
        mock_dedup.get_event_stats.side_effect = Exception("Dedup service error")
        
        stats = cleanup_service.cleanup_duplicate_events()
        
        assert "error" in stats
        assert stats["error"] == "Dedup service error"


if __name__ == "__main__":
    pytest.main([__file__])