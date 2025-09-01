"""
Model Security Utilities
Integrates security validation with existing file handling and resource management systems.
"""

import hashlib
import logging
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class FileValidationResult:
    """Result of file security validation."""
    file_path: str
    size: int
    checksum: str
    checksum_verified: bool
    quarantined: bool = False
    error_message: Optional[str] = None


@dataclass
class ModelSecurityReport:
    """Security validation report for a model."""
    model_id: str
    total_files: int
    validated_files: int
    failed_validations: int
    quarantined_files: int
    total_size: int
    validation_timestamp: datetime
    file_results: List[FileValidationResult]
    security_issues: List[str]


class ModelFileValidator:
    """Validates model files for security and integrity."""
    
    def __init__(self, quarantine_dir: Optional[Path] = None):
        self.quarantine_dir = quarantine_dir or Path("quarantine")
        self.quarantine_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(f"{__name__}.ModelFileValidator")
    
    def validate_file_checksum(self, file_path: Path, expected_checksum: str) -> FileValidationResult:
        """Validate file checksum against expected value."""
        try:
            if not file_path.exists():
                return FileValidationResult(
                    file_path=str(file_path),
                    size=0,
                    checksum="",
                    checksum_verified=False,
                    error_message="File does not exist"
                )
            
            # Calculate SHA256 checksum
            sha256_hash = hashlib.sha256()
            file_size = 0
            
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
                    file_size += len(chunk)
            
            calculated_checksum = sha256_hash.hexdigest()
            checksum_verified = calculated_checksum.lower() == expected_checksum.lower()
            
            result = FileValidationResult(
                file_path=str(file_path),
                size=file_size,
                checksum=calculated_checksum,
                checksum_verified=checksum_verified
            )
            
            if not checksum_verified:
                result.error_message = f"Checksum mismatch: expected {expected_checksum}, got {calculated_checksum}"
                self.logger.warning(f"Checksum verification failed for {file_path}: {result.error_message}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error validating checksum for {file_path}: {e}")
            return FileValidationResult(
                file_path=str(file_path),
                size=0,
                checksum="",
                checksum_verified=False,
                error_message=str(e)
            )
    
    def quarantine_file(self, file_path: Path, reason: str) -> bool:
        """Move suspicious file to quarantine directory."""
        try:
            if not file_path.exists():
                return False
            
            # Create quarantine subdirectory with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            quarantine_subdir = self.quarantine_dir / timestamp
            quarantine_subdir.mkdir(exist_ok=True)
            
            # Move file to quarantine
            quarantine_path = quarantine_subdir / file_path.name
            shutil.move(str(file_path), str(quarantine_path))
            
            # Create metadata file
            metadata_path = quarantine_subdir / f"{file_path.name}.metadata"
            with open(metadata_path, 'w') as f:
                f.write(f"Original path: {file_path}\n")
                f.write(f"Quarantine reason: {reason}\n")
                f.write(f"Quarantine timestamp: {datetime.now().isoformat()}\n")
            
            self.logger.warning(f"File quarantined: {file_path} -> {quarantine_path} (reason: {reason})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to quarantine file {file_path}: {e}")
            return False
    
    def validate_model_files(
        self, 
        model_id: str, 
        files_info: List[Dict[str, Any]], 
        model_dir: Path
    ) -> ModelSecurityReport:
        """Validate all files for a model."""
        file_results = []
        security_issues = []
        quarantined_count = 0
        
        for file_info in files_info:
            file_path = model_dir / file_info["path"]
            expected_checksum = file_info.get("sha256", "")
            
            if not expected_checksum:
                # Calculate checksum if not provided
                if file_path.exists():
                    result = self._calculate_file_checksum(file_path)
                    file_results.append(result)
                else:
                    file_results.append(FileValidationResult(
                        file_path=str(file_path),
                        size=0,
                        checksum="",
                        checksum_verified=False,
                        error_message="File missing and no checksum provided"
                    ))
                continue
            
            # Validate checksum
            result = self.validate_file_checksum(file_path, expected_checksum)
            
            # Quarantine files with failed validation
            if not result.checksum_verified and file_path.exists():
                quarantined = self.quarantine_file(
                    file_path, 
                    f"Checksum verification failed for model {model_id}"
                )
                if quarantined:
                    result.quarantined = True
                    quarantined_count += 1
                    security_issues.append(f"File quarantined due to checksum mismatch: {file_path.name}")
            
            file_results.append(result)
        
        # Generate report
        validated_files = sum(1 for r in file_results if r.checksum_verified)
        failed_validations = sum(1 for r in file_results if not r.checksum_verified)
        total_size = sum(r.size for r in file_results)
        
        return ModelSecurityReport(
            model_id=model_id,
            total_files=len(file_results),
            validated_files=validated_files,
            failed_validations=failed_validations,
            quarantined_files=quarantined_count,
            total_size=total_size,
            validation_timestamp=datetime.now(),
            file_results=file_results,
            security_issues=security_issues
        )
    
    def _calculate_file_checksum(self, file_path: Path) -> FileValidationResult:
        """Calculate checksum for a file without validation."""
        try:
            sha256_hash = hashlib.sha256()
            file_size = 0
            
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
                    file_size += len(chunk)
            
            return FileValidationResult(
                file_path=str(file_path),
                size=file_size,
                checksum=sha256_hash.hexdigest(),
                checksum_verified=True  # No validation, just calculation
            )
            
        except Exception as e:
            return FileValidationResult(
                file_path=str(file_path),
                size=0,
                checksum="",
                checksum_verified=False,
                error_message=str(e)
            )


class ModelOwnerValidator:
    """Validates model owners against allowlist/denylist."""
    
    def __init__(self, config: Dict[str, Any]):
        self.allowed_owners = set(config.get("allowed_owners", []))
        self.blocked_owners = set(config.get("blocked_owners", []))
        self.logger = logging.getLogger(f"{__name__}.ModelOwnerValidator")
    
    def is_owner_allowed(self, owner: str) -> Tuple[bool, str]:
        """Check if model owner is allowed."""
        owner_lower = owner.lower()
        
        # Check blocklist first
        if self.blocked_owners and owner_lower in self.blocked_owners:
            return False, f"Owner '{owner}' is in the blocked list"
        
        # Check allowlist if configured
        if self.allowed_owners and owner_lower not in self.allowed_owners:
            return False, f"Owner '{owner}' is not in the allowed list"
        
        return True, "Owner is allowed"
    
    def validate_model_owner(self, model_id: str) -> Tuple[bool, str]:
        """Validate the owner of a model ID."""
        try:
            # Extract owner from model_id (format: owner/model)
            if "/" not in model_id:
                return False, "Invalid model ID format (expected owner/model)"
            
            owner = model_id.split("/")[0]
            return self.is_owner_allowed(owner)
            
        except Exception as e:
            self.logger.error(f"Error validating model owner for {model_id}: {e}")
            return False, f"Error validating owner: {str(e)}"


class ResourceQuotaManager:
    """Manages resource quotas for model storage."""
    
    def __init__(self, config: Dict[str, Any]):
        self.max_total_size_gb = config.get("max_total_size_gb")
        self.max_model_size_gb = config.get("max_model_size_gb", 50.0)
        self.max_models_per_user = config.get("max_models_per_user")
        self.logger = logging.getLogger(f"{__name__}.ResourceQuotaManager")
    
    def check_storage_quota(
        self, 
        model_size: int, 
        current_usage: int, 
        user_id: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Check if adding a model would exceed storage quotas."""
        model_size_gb = model_size / (1024**3)
        current_usage_gb = current_usage / (1024**3)
        
        # Check individual model size limit
        if model_size_gb > self.max_model_size_gb:
            return False, f"Model size {model_size_gb:.1f}GB exceeds limit of {self.max_model_size_gb}GB"
        
        # Check total storage limit
        if self.max_total_size_gb:
            total_after_download = current_usage_gb + model_size_gb
            if total_after_download > self.max_total_size_gb:
                return False, (
                    f"Total storage would be {total_after_download:.1f}GB, "
                    f"exceeding limit of {self.max_total_size_gb}GB"
                )
        
        return True, "Storage quota check passed"
    
    def get_current_usage(self, models_dir: Path) -> int:
        """Calculate current storage usage."""
        try:
            total_size = 0
            for root, dirs, files in os.walk(models_dir):
                for file in files:
                    file_path = Path(root) / file
                    if file_path.exists():
                        total_size += file_path.stat().st_size
            return total_size
        except Exception as e:
            self.logger.error(f"Error calculating storage usage: {e}")
            return 0
    
    def get_disk_usage(self, path: Path) -> Tuple[int, int, int]:
        """Get disk usage statistics (total, used, free) in bytes."""
        try:
            usage = shutil.disk_usage(path)
            return usage.total, usage.used, usage.free
        except Exception as e:
            self.logger.error(f"Error getting disk usage for {path}: {e}")
            return 0, 0, 0


class ModelSecurityIntegrator:
    """Integrates all security validation components."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.file_validator = ModelFileValidator(
            quarantine_dir=Path(config.get("quarantine_dir", "quarantine"))
        )
        self.owner_validator = ModelOwnerValidator(config)
        self.quota_manager = ResourceQuotaManager(config)
        self.logger = logging.getLogger(f"{__name__}.ModelSecurityIntegrator")
    
    def validate_model_download(
        self, 
        model_id: str, 
        model_info: Dict[str, Any],
        models_dir: Path,
        user_id: Optional[str] = None
    ) -> Tuple[bool, List[str]]:
        """Comprehensive security validation for model download."""
        issues = []
        
        try:
            # Validate owner
            owner_allowed, owner_message = self.owner_validator.validate_model_owner(model_id)
            if not owner_allowed:
                issues.append(f"Owner validation failed: {owner_message}")
            
            # Check storage quota
            model_size = model_info.get("total_size", 0)
            current_usage = self.quota_manager.get_current_usage(models_dir)
            quota_ok, quota_message = self.quota_manager.check_storage_quota(
                model_size, current_usage, user_id
            )
            if not quota_ok:
                issues.append(f"Quota validation failed: {quota_message}")
            
            # Check disk space
            total, used, free = self.quota_manager.get_disk_usage(models_dir)
            if free < model_size * 1.1:  # Require 10% buffer
                issues.append(
                    f"Insufficient disk space: need {model_size / (1024**3):.1f}GB, "
                    f"available {free / (1024**3):.1f}GB"
                )
            
            # Log validation results
            if issues:
                self.logger.warning(f"Security validation failed for {model_id}: {'; '.join(issues)}")
            else:
                self.logger.info(f"Security validation passed for {model_id}")
            
            return len(issues) == 0, issues
            
        except Exception as e:
            self.logger.error(f"Error during security validation for {model_id}: {e}")
            return False, [f"Validation error: {str(e)}"]
    
    def validate_model_files_post_download(
        self, 
        model_id: str, 
        files_info: List[Dict[str, Any]], 
        model_dir: Path
    ) -> ModelSecurityReport:
        """Validate model files after download."""
        return self.file_validator.validate_model_files(model_id, files_info, model_dir)
    
    def cleanup_quarantined_files(self, max_age_days: int = 30) -> int:
        """Clean up old quarantined files."""
        try:
            cleaned_count = 0
            cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 60 * 60)
            
            for item in self.file_validator.quarantine_dir.iterdir():
                if item.is_dir():
                    # Check if directory is old enough
                    if item.stat().st_mtime < cutoff_time:
                        shutil.rmtree(item)
                        cleaned_count += 1
                        self.logger.info(f"Cleaned up old quarantine directory: {item}")
            
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up quarantined files: {e}")
            return 0


# Export public interface
__all__ = [
    "ModelFileValidator",
    "ModelOwnerValidator", 
    "ResourceQuotaManager",
    "ModelSecurityIntegrator",
    "FileValidationResult",
    "ModelSecurityReport",
]