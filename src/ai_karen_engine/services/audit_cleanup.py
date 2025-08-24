"""
Audit Log Cleanup Utilities

This module provides utilities for cleaning up and maintaining audit logs,
including removing old entries, compacting logs, and managing storage.
"""

import os
import gzip
import shutil
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

from ai_karen_engine.core.logging import get_logger
from ai_karen_engine.services.audit_logging import get_audit_logger
from ai_karen_engine.services.audit_deduplication import get_audit_deduplication_service

logger = get_logger(__name__)


class AuditLogCleanupService:
    """Service for cleaning up and maintaining audit logs"""
    
    def __init__(self, log_directory: str = "logs"):
        self.log_directory = Path(log_directory)
        self.audit_logger = get_audit_logger()
        self.deduplication_service = get_audit_deduplication_service()
        
    def cleanup_old_log_files(
        self,
        max_age_days: int = 30,
        compress_before_delete: bool = True,
        file_patterns: List[str] = None
    ) -> Dict[str, Any]:
        """
        Clean up old log files by compressing and/or deleting them.
        
        Args:
            max_age_days: Maximum age of log files to keep (default 30 days)
            compress_before_delete: Whether to compress files before deletion
            file_patterns: List of file patterns to clean up (default: audit logs)
            
        Returns:
            Dictionary with cleanup statistics
        """
        if file_patterns is None:
            file_patterns = [
                "audit*.log",
                "auth_audit*.log", 
                "performance*.log",
                "response_audit*.log"
            ]
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=max_age_days)
        stats = {
            "files_processed": 0,
            "files_compressed": 0,
            "files_deleted": 0,
            "bytes_saved": 0,
            "errors": []
        }
        
        try:
            if not self.log_directory.exists():
                logger.warning(f"Log directory {self.log_directory} does not exist")
                return stats
            
            for pattern in file_patterns:
                for log_file in self.log_directory.glob(pattern):
                    try:
                        # Skip already compressed files
                        if log_file.suffix == '.gz':
                            continue
                            
                        file_stat = log_file.stat()
                        file_modified = datetime.fromtimestamp(file_stat.st_mtime, timezone.utc)
                        
                        if file_modified < cutoff_date:
                            stats["files_processed"] += 1
                            original_size = file_stat.st_size
                            
                            if compress_before_delete:
                                # Compress the file
                                compressed_file = log_file.with_suffix(log_file.suffix + '.gz')
                                
                                with open(log_file, 'rb') as f_in:
                                    with gzip.open(compressed_file, 'wb') as f_out:
                                        shutil.copyfileobj(f_in, f_out)
                                
                                # Verify compression worked
                                if compressed_file.exists():
                                    compressed_size = compressed_file.stat().st_size
                                    stats["bytes_saved"] += original_size - compressed_size
                                    stats["files_compressed"] += 1
                                    
                                    # Delete original file
                                    log_file.unlink()
                                    stats["files_deleted"] += 1
                                    
                                    logger.info(
                                        f"Compressed and deleted old log file: {log_file.name} "
                                        f"(saved {original_size - compressed_size} bytes)"
                                    )
                                else:
                                    stats["errors"].append(f"Failed to compress {log_file.name}")
                            else:
                                # Just delete the file
                                log_file.unlink()
                                stats["files_deleted"] += 1
                                stats["bytes_saved"] += original_size
                                
                                logger.info(f"Deleted old log file: {log_file.name}")
                                
                    except Exception as e:
                        error_msg = f"Error processing {log_file.name}: {str(e)}"
                        stats["errors"].append(error_msg)
                        logger.error(error_msg)
            
            logger.info(
                f"Log cleanup completed: {stats['files_processed']} files processed, "
                f"{stats['files_compressed']} compressed, {stats['files_deleted']} deleted, "
                f"{stats['bytes_saved']} bytes saved"
            )
            
        except Exception as e:
            error_msg = f"Error during log cleanup: {str(e)}"
            stats["errors"].append(error_msg)
            logger.error(error_msg)
        
        return stats
    
    def cleanup_duplicate_events(self) -> Dict[str, Any]:
        """
        Clean up duplicate event tracking data.
        
        Returns:
            Dictionary with cleanup statistics
        """
        stats = {
            "events_before": 0,
            "events_after": 0,
            "events_cleaned": 0,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            # Get current event stats
            event_stats = self.deduplication_service.get_event_stats()
            stats["events_before"] = event_stats.get("local_events_count", 0)
            
            # Force cleanup of expired events
            self.deduplication_service._cleanup_expired_events()
            
            # Get stats after cleanup
            event_stats_after = self.deduplication_service.get_event_stats()
            stats["events_after"] = event_stats_after.get("local_events_count", 0)
            stats["events_cleaned"] = stats["events_before"] - stats["events_after"]
            
            logger.info(
                f"Duplicate event cleanup completed: "
                f"{stats['events_cleaned']} expired events removed"
            )
            
        except Exception as e:
            logger.error(f"Error during duplicate event cleanup: {str(e)}")
            stats["error"] = str(e)
        
        return stats
    
    def get_log_file_stats(self) -> Dict[str, Any]:
        """
        Get statistics about log files in the log directory.
        
        Returns:
            Dictionary with log file statistics
        """
        stats = {
            "total_files": 0,
            "total_size_bytes": 0,
            "compressed_files": 0,
            "compressed_size_bytes": 0,
            "uncompressed_files": 0,
            "uncompressed_size_bytes": 0,
            "oldest_file": None,
            "newest_file": None,
            "file_types": {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            if not self.log_directory.exists():
                return stats
            
            oldest_time = None
            newest_time = None
            
            for log_file in self.log_directory.iterdir():
                if log_file.is_file() and log_file.suffix in ['.log', '.gz']:
                    file_stat = log_file.stat()
                    file_size = file_stat.st_size
                    file_modified = datetime.fromtimestamp(file_stat.st_mtime, timezone.utc)
                    
                    stats["total_files"] += 1
                    stats["total_size_bytes"] += file_size
                    
                    # Track file types
                    file_type = "compressed" if log_file.suffix == '.gz' else "uncompressed"
                    if file_type not in stats["file_types"]:
                        stats["file_types"][file_type] = {"count": 0, "size_bytes": 0}
                    stats["file_types"][file_type]["count"] += 1
                    stats["file_types"][file_type]["size_bytes"] += file_size
                    
                    if log_file.suffix == '.gz':
                        stats["compressed_files"] += 1
                        stats["compressed_size_bytes"] += file_size
                    else:
                        stats["uncompressed_files"] += 1
                        stats["uncompressed_size_bytes"] += file_size
                    
                    # Track oldest and newest files
                    if oldest_time is None or file_modified < oldest_time:
                        oldest_time = file_modified
                        stats["oldest_file"] = {
                            "name": log_file.name,
                            "modified": file_modified.isoformat(),
                            "size_bytes": file_size
                        }
                    
                    if newest_time is None or file_modified > newest_time:
                        newest_time = file_modified
                        stats["newest_file"] = {
                            "name": log_file.name,
                            "modified": file_modified.isoformat(),
                            "size_bytes": file_size
                        }
            
        except Exception as e:
            logger.error(f"Error getting log file stats: {str(e)}")
            stats["error"] = str(e)
        
        return stats
    
    def rotate_current_logs(self, max_size_mb: int = 100) -> Dict[str, Any]:
        """
        Rotate current log files if they exceed the maximum size.
        
        Args:
            max_size_mb: Maximum size in MB before rotating logs
            
        Returns:
            Dictionary with rotation statistics
        """
        max_size_bytes = max_size_mb * 1024 * 1024
        stats = {
            "files_rotated": 0,
            "files_checked": 0,
            "errors": [],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            if not self.log_directory.exists():
                return stats
            
            current_time = datetime.now(timezone.utc)
            timestamp_suffix = current_time.strftime("%Y%m%d_%H%M%S")
            
            for log_file in self.log_directory.glob("*.log"):
                try:
                    stats["files_checked"] += 1
                    file_size = log_file.stat().st_size
                    
                    if file_size > max_size_bytes:
                        # Rotate the file
                        rotated_name = f"{log_file.stem}_{timestamp_suffix}.log"
                        rotated_path = log_file.parent / rotated_name
                        
                        # Move current file to rotated name
                        log_file.rename(rotated_path)
                        
                        # Create new empty log file
                        log_file.touch()
                        
                        stats["files_rotated"] += 1
                        logger.info(
                            f"Rotated log file {log_file.name} to {rotated_name} "
                            f"(size: {file_size / 1024 / 1024:.2f} MB)"
                        )
                        
                except Exception as e:
                    error_msg = f"Error rotating {log_file.name}: {str(e)}"
                    stats["errors"].append(error_msg)
                    logger.error(error_msg)
            
        except Exception as e:
            error_msg = f"Error during log rotation: {str(e)}"
            stats["errors"].append(error_msg)
            logger.error(error_msg)
        
        return stats
    
    def cleanup_all(
        self,
        max_age_days: int = 30,
        max_size_mb: int = 100,
        compress_old_files: bool = True
    ) -> Dict[str, Any]:
        """
        Perform comprehensive cleanup of audit logs.
        
        Args:
            max_age_days: Maximum age of log files to keep
            max_size_mb: Maximum size in MB before rotating logs
            compress_old_files: Whether to compress old files before deletion
            
        Returns:
            Dictionary with comprehensive cleanup statistics
        """
        logger.info("Starting comprehensive audit log cleanup")
        
        cleanup_stats = {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "file_cleanup": {},
            "duplicate_cleanup": {},
            "rotation": {},
            "final_stats": {},
            "completed_at": None
        }
        
        try:
            # 1. Clean up duplicate event tracking
            cleanup_stats["duplicate_cleanup"] = self.cleanup_duplicate_events()
            
            # 2. Rotate large current log files
            cleanup_stats["rotation"] = self.rotate_current_logs(max_size_mb)
            
            # 3. Clean up old log files
            cleanup_stats["file_cleanup"] = self.cleanup_old_log_files(
                max_age_days=max_age_days,
                compress_before_delete=compress_old_files
            )
            
            # 4. Get final statistics
            cleanup_stats["final_stats"] = self.get_log_file_stats()
            
            cleanup_stats["completed_at"] = datetime.now(timezone.utc).isoformat()
            
            logger.info("Comprehensive audit log cleanup completed successfully")
            
        except Exception as e:
            logger.error(f"Error during comprehensive cleanup: {str(e)}")
            cleanup_stats["error"] = str(e)
            cleanup_stats["completed_at"] = datetime.now(timezone.utc).isoformat()
        
        return cleanup_stats


# Global instance
_cleanup_service: Optional[AuditLogCleanupService] = None


def get_audit_cleanup_service(log_directory: str = "logs") -> AuditLogCleanupService:
    """Get the global audit cleanup service instance"""
    global _cleanup_service
    if _cleanup_service is None:
        _cleanup_service = AuditLogCleanupService(log_directory)
    return _cleanup_service


# Export main classes and functions
__all__ = [
    "AuditLogCleanupService",
    "get_audit_cleanup_service"
]