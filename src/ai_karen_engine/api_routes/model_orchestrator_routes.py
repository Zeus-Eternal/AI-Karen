"""
Model Orchestrator API Routes

Provides REST API endpoints for model management through the Model Orchestrator plugin.
Implements core endpoints for listing, downloading, and managing models with CLI integration.

This module implements:
- Core model operations: list, info, download, remove
- Plugin service integration for CLI command execution
- Real-time progress tracking through WebSocket system
- Authentication and authorization integration with RBAC
- License tracking and security validation
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Request
from fastapi.responses import JSONResponse

from ai_karen_engine.utils.dependency_checks import import_pydantic
# Simple auth - removed complex security imports
# from ai_karen_engine.security.model_security import (
#     ModelSecurityManager,
#     LicenseManager,
#     ModelAuditEvent,
#     RBACError
# )
# from ai_karen_engine.middleware.rbac import require_scopes
from ai_karen_engine.health import get_model_orchestrator_health_checker
from ai_karen_engine.monitoring import get_model_orchestrator_metrics
from ai_karen_engine.error_tracking import get_model_orchestrator_error_tracker

BaseModel, Field = import_pydantic("BaseModel", "Field")

logger = logging.getLogger("kari.model_orchestrator_api")

router = APIRouter(prefix="/api/models", tags=["model-orchestrator"])

# Import plugin service
try:
    import sys
    from pathlib import Path
    plugin_path = Path(__file__).parent.parent.parent.parent / "plugin_marketplace" / "ai" / "model-orchestrator"
    sys.path.append(str(plugin_path))
    
    from ai_karen_engine.services.model_orchestrator_service import (
        ModelOrchestratorService, 
        ModelOrchestratorError,
        ModelSummary,
        ModelInfo,
        DownloadRequest,
        DownloadResult,
        MigrationResult,
        EnsureResult,
        GCResult,
        RemoveResult,
        E_NET, E_DISK, E_PERM, E_LICENSE, E_VERIFY, E_SCHEMA, E_COMPAT, E_QUOTA, E_NOT_FOUND, E_INVALID
    )
except ImportError as e:
    logger.error(f"Failed to import model orchestrator service: {e}")
    # Create fallback classes to prevent import errors
    class ModelOrchestratorService:
        def __init__(self, *args, **kwargs):
            pass

    class ModelOrchestratorError(Exception):
        def __init__(self, code, message, details=None):
            self.code = code
            self.message = message
            self.details = details or {}
            super().__init__(f"{code}: {message}")

    class RemoveResult:
        def __init__(self, model_id: str, deleted_artifacts=None, warnings=None, metadata=None):
            self.model_id = model_id
            self.deleted_artifacts = deleted_artifacts or []
            self.warnings = warnings or []
            self.metadata = metadata or {}

    # Error codes
    E_NET = "E_NET"
    E_DISK = "E_DISK"
    E_PERM = "E_PERM"
    E_LICENSE = "E_LICENSE"
    E_VERIFY = "E_VERIFY"
    E_SCHEMA = "E_SCHEMA"
    E_COMPAT = "E_COMPAT"
    E_QUOTA = "E_QUOTA"
    E_NOT_FOUND = "E_NOT_FOUND"
    E_INVALID = "E_INVALID"

# Global service instance
_orchestrator_service: Optional[ModelOrchestratorService] = None

def get_orchestrator_service() -> ModelOrchestratorService:
    """Get or create the model orchestrator service instance."""
    global _orchestrator_service
    if _orchestrator_service is None:
        # Load configuration from plugin config or defaults
        config = {
            "models_root": "models",
            "registry_path": "models/orchestrator_registry.json",
            "max_concurrent_downloads": 3,
            "enable_metrics": True,
            "enable_rbac": True,
            "offline_mode": False,
            "mirror_url": None,
            "max_storage_gb": None
        }
        _orchestrator_service = ModelOrchestratorService(config)
    return _orchestrator_service

# Job tracking for long-running operations
_active_jobs: Dict[str, Dict[str, Any]] = {}

# Request/Response Models

class ModelListRequest(BaseModel):
    """Request model for listing models."""
    owner: str = Field(..., description="Model owner/organization")
    limit: int = Field(50, ge=1, le=200, description="Maximum number of models to return")
    search: Optional[str] = Field(None, description="Search query")
    sort: str = Field("downloads", description="Sort field (downloads, likes, modified)")
    direction: int = Field(-1, description="Sort direction (1 for ascending, -1 for descending)")

class ModelInfoRequest(BaseModel):
    """Request model for getting model info."""
    model_id: str = Field(..., description="Model identifier (owner/repo)")
    revision: Optional[str] = Field(None, description="Model revision/commit hash")

class ModelDownloadRequest(BaseModel):
    """Request model for downloading models."""
    model_id: str = Field(..., description="Model identifier (owner/repo)")
    revision: Optional[str] = Field(None, description="Model revision/commit hash")
    include_patterns: Optional[List[str]] = Field(None, description="File patterns to include")
    exclude_patterns: Optional[List[str]] = Field(None, description="File patterns to exclude")
    pin: bool = Field(False, description="Pin model to protect from garbage collection")
    force_redownload: bool = Field(False, description="Force redownload even if model exists")
    library_override: Optional[str] = Field(None, description="Override library detection")

class ModelRemoveRequest(BaseModel):
    """Request model for removing models."""
    model_id: str = Field(..., description="Model identifier (owner/repo)")
    delete_files: bool = Field(True, description="Delete model files from disk")

class JobStatusResponse(BaseModel):
    """Response model for job status."""
    job_id: str
    status: str  # pending, running, completed, failed, cancelled
    progress: float  # 0.0 to 1.0
    message: Optional[str] = None
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

class ModelSummaryResponse(BaseModel):
    """Response model for model summary."""
    model_id: str
    last_modified: Optional[datetime]
    likes: Optional[int]
    downloads: Optional[int]
    library_name: Optional[str]
    tags: List[str]
    total_size: Optional[int] = None
    description: Optional[str] = None

class ModelInfoResponse(BaseModel):
    """Response model for detailed model info."""
    model_id: str
    owner: str
    repository: str
    library: str
    files: List[Dict[str, Union[str, int]]]
    total_size: int
    last_modified: Optional[datetime]
    downloads: Optional[int]
    likes: Optional[int]
    tags: List[str]
    license: Optional[str]
    description: Optional[str]
    revision: Optional[str] = None

class DownloadResultResponse(BaseModel):
    """Response model for download results."""
    model_id: str
    install_path: str
    total_size: int
    files_downloaded: int
    duration_seconds: float
    status: str
    error_message: Optional[str] = None


class ModelRemoveResponse(BaseModel):
    """Response payload describing a model removal."""

    model_id: str
    delete_files: bool
    deleted_artifacts: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]
    message: str

# Security and authentication dependencies
# Simple auth - removed security manager
# _security_manager: Optional[ModelSecurityManager] = None
# 
# def get_security_manager() -> ModelSecurityManager:
#     """Get or create the model security manager instance."""
#     global _security_manager
#     if _security_manager is None:
#         _security_manager = ModelSecurityManager()
#     return _security_manager

async def get_current_user(request: Request):
    """Get current authenticated user from request state."""
    if not hasattr(request, 'state'):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_id = getattr(request.state, 'user', None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    roles = getattr(request.state, 'roles', [])
    scopes = getattr(request.state, 'scopes', [])
    
    return {
        "user_id": user_id,
        "roles": roles,
        "scopes": scopes
    }

# Error handling
def handle_orchestrator_error(error: ModelOrchestratorError) -> HTTPException:
    """Convert ModelOrchestratorError to appropriate HTTP exception."""
    status_code_map = {
        E_NET: 503,  # Service Unavailable
        E_DISK: 507,  # Insufficient Storage
        E_PERM: 403,  # Forbidden
        E_LICENSE: 451,  # Unavailable For Legal Reasons
        E_VERIFY: 422,  # Unprocessable Entity
        E_SCHEMA: 422,  # Unprocessable Entity
        E_COMPAT: 409,  # Conflict
        E_QUOTA: 507,  # Insufficient Storage
        E_NOT_FOUND: 404,  # Not Found
        E_INVALID: 400,  # Bad Request
    }
    
    status_code = status_code_map.get(error.code, 500)
    
    return HTTPException(
        status_code=status_code,
        detail={
            "error_code": error.code,
            "message": error.message,
            "details": error.details
        }
    )

# Core Endpoints

@router.get("/list/{owner}", response_model=List[ModelSummaryResponse])
async def list_models(
    owner: str,
    request: Request,
    limit: int = Query(50, ge=1, le=200, description="Maximum number of models to return"),
    search: Optional[str] = Query(None, description="Search query"),
    sort: str = Query("downloads", description="Sort field"),
    direction: int = Query(-1, description="Sort direction"),
    current_user = Depends(get_current_user)
):
    """
    List models for an owner/organization.
    
    Requirements: 9.1, 9.2, 9.5, 4.1, 4.7
    """
    try:
        # Simple auth - check user role
        user_roles = current_user.get("roles", [])
        has_permission = any(role in user_roles for role in ["admin", "user"])
        
        if not has_permission:
            raise HTTPException(status_code=403, detail="Insufficient permissions to browse models")
        
        # Simple audit logging (removed complex audit)
        logger.info(f"User {current_user.get('user_id')} browsing models")
        
        service = get_orchestrator_service()
        models = await service.list_models(
            owner=owner,
            limit=limit,
            search=search,
            sort=sort,
            direction=direction
        )
        
        # Convert to response format
        response = []
        for model in models:
            response.append(ModelSummaryResponse(
                model_id=model.model_id,
                last_modified=model.last_modified,
                likes=model.likes,
                downloads=model.downloads,
                library_name=model.library_name,
                tags=model.tags,
                total_size=model.total_size,
                description=model.description
            ))
        
        return response
        
    except ModelOrchestratorError as e:
        raise handle_orchestrator_error(e)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list models for {owner}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/info/{model_id:path}", response_model=ModelInfoResponse)
async def get_model_info(
    model_id: str,
    request: Request,
    revision: Optional[str] = Query(None, description="Model revision"),
    current_user = Depends(get_current_user)
):
    """
    Get detailed information about a model.
    
    Requirements: 9.1, 9.2, 9.5, 4.1, 4.7
    """
    try:
        # Simple auth - check user role
        user_roles = current_user.get("roles", [])
        has_permission = any(role in user_roles for role in ["admin", "user"])
        
        if not has_permission:
            raise HTTPException(status_code=403, detail="Insufficient permissions to view model information")
        
        # Simple audit logging (removed complex audit)
        logger.info(f"User {current_user.get('user_id')} viewing model info")
        
        service = get_orchestrator_service()
        model_info = await service.get_model_info(model_id, revision)
        
        return ModelInfoResponse(
            model_id=model_info.model_id,
            owner=model_info.owner,
            repository=model_info.repository,
            library=model_info.library,
            files=model_info.files,
            total_size=model_info.total_size,
            last_modified=model_info.last_modified,
            downloads=model_info.downloads,
            likes=model_info.likes,
            tags=model_info.tags,
            license=model_info.license,
            description=model_info.description,
            revision=model_info.revision
        )
        
    except ModelOrchestratorError as e:
        raise handle_orchestrator_error(e)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get model info for {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/download", response_model=Dict[str, str])
async def download_model(
    download_request: ModelDownloadRequest,
    http_request: Request,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """
    Download and install a model.
    
    Requirements: 9.1, 9.2, 9.5, 4.1, 4.7, 12.1, 12.2
    """
    try:
        # Simple auth - check user role for download
        user_roles = current_user.get("roles", [])
        has_permission = any(role in user_roles for role in ["admin", "user"])
        
        if not has_permission:
            raise HTTPException(status_code=403, detail="Insufficient permissions to download models")
        
        # Simple audit logging (removed complex audit)
        logger.info(f"User {current_user.get('user_id')} downloading model {download_request.model_id}")
        
        # Create job for tracking
        job_id = str(uuid.uuid4())
        job = {
            "job_id": job_id,
            "status": "pending",
            "progress": 0.0,
            "message": f"Starting download of {download_request.model_id}",
            "error": None,
            "result": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        _active_jobs[job_id] = job
        
        # Start download in background
        background_tasks.add_task(
            _handle_model_download,
            job_id,
            download_request,
            current_user,
            http_request
        )
        
        return {"job_id": job_id, "message": "Download started"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start model download: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/remove/{model_id:path}", response_model=ModelRemoveResponse)
async def remove_model(
    model_id: str,
    request: Request,
    delete_files: bool = Query(True, description="Delete model files from disk"),
    current_user = Depends(get_current_user)
):
    """
    Remove a model from the registry and optionally delete files.
    
    Requirements: 9.1, 9.2, 9.5, 4.1, 4.7
    """
    try:
        # Check remove permission
        security_manager = get_security_manager()
        has_permission = await security_manager.check_remove_permission(current_user, model_id, request)
        
        if not has_permission:
            raise HTTPException(status_code=403, detail="Insufficient permissions to remove models")
        
        # Audit the remove operation
        await security_manager.audit_model_operation(
            user_id=current_user["user_id"],
            operation="remove",
            model_id=model_id,
            metadata={"delete_files": delete_files},
            request=request
        )
        
        service = get_orchestrator_service()

        removal_result: RemoveResult = await service.remove_model(
            model_id=model_id,
            delete_files=delete_files,
        )

        return ModelRemoveResponse(
            model_id=removal_result.model_id,
            delete_files=delete_files,
            deleted_artifacts=removal_result.deleted_artifacts,
            warnings=removal_result.warnings,
            metadata=removal_result.metadata,
            message=f"Model {model_id} removed successfully",
        )
        
    except ModelOrchestratorError as e:
        raise handle_orchestrator_error(e)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove model {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Job Management Endpoints

@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    current_user = Depends(get_current_user)
):
    """
    Get status of a long-running job.
    
    Requirements: 9.3, 9.6
    """
    job = _active_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatusResponse(
        job_id=job["job_id"],
        status=job["status"],
        progress=job["progress"],
        message=job["message"],
        error=job["error"],
        result=job["result"],
        created_at=job["created_at"],
        updated_at=job["updated_at"]
    )

@router.get("/jobs", response_model=List[JobStatusResponse])
async def list_jobs(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of jobs to return"),
    current_user = Depends(get_current_user)
):
    """
    List active and recent jobs.
    
    Requirements: 9.3, 9.6
    """
    jobs = list(_active_jobs.values())
    
    # Filter by status if specified
    if status:
        jobs = [job for job in jobs if job["status"] == status]
    
    # Sort by creation time (newest first)
    jobs.sort(key=lambda x: x["created_at"], reverse=True)
    
    # Apply limit
    jobs = jobs[:limit]
    
    response = []
    for job in jobs:
        response.append(JobStatusResponse(
            job_id=job["job_id"],
            status=job["status"],
            progress=job["progress"],
            message=job["message"],
            error=job["error"],
            result=job["result"],
            created_at=job["created_at"],
            updated_at=job["updated_at"]
        ))
    
    return response

@router.post("/jobs/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    current_user = Depends(get_current_user)
):
    """
    Cancel a running job.
    
    Requirements: 9.3, 9.6
    """
    job = _active_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] in ["completed", "failed", "cancelled"]:
        raise HTTPException(status_code=400, detail="Job cannot be cancelled")
    
    job["status"] = "cancelled"
    job["updated_at"] = datetime.now(timezone.utc)
    job["message"] = "Job cancelled by user"
    
    return {"message": "Job cancelled successfully"}

# Background task handlers

async def _handle_model_download(job_id: str, request: ModelDownloadRequest, user: Dict[str, Any], http_request: Optional[Request] = None):
    """Handle model download in background task."""
    job = _active_jobs[job_id]
    
    try:
        job["status"] = "running"
        job["message"] = f"Downloading {request.model_id}..."
        job["updated_at"] = datetime.now(timezone.utc)
        
        service = get_orchestrator_service()
        
        # Convert API request to service request
        download_req = DownloadRequest(
            model_id=request.model_id,
            revision=request.revision,
            include_patterns=request.include_patterns,
            exclude_patterns=request.exclude_patterns,
            pin=request.pin,
            force_redownload=request.force_redownload,
            library_override=request.library_override
        )
        
        # Perform download
        result = await service.download_model(download_req)
        
        # Update job with result
        job["status"] = "completed" if result.status == "success" else "failed"
        job["progress"] = 1.0
        job["message"] = f"Download completed: {result.status}"
        job["error"] = result.error_message
        job["result"] = {
            "model_id": result.model_id,
            "install_path": result.install_path,
            "total_size": result.total_size,
            "files_downloaded": result.files_downloaded,
            "duration_seconds": result.duration_seconds,
            "status": result.status
        }
        job["updated_at"] = datetime.now(timezone.utc)
        
        # TODO: Emit WebSocket event for real-time updates
        await _emit_job_update(job_id, job)
        
    except ModelOrchestratorError as e:
        job["status"] = "failed"
        job["error"] = f"{e.code}: {e.message}"
        job["message"] = "Download failed"
        job["updated_at"] = datetime.now(timezone.utc)
        
        await _emit_job_update(job_id, job)
        
    except Exception as e:
        job["status"] = "failed"
        job["error"] = str(e)
        job["message"] = "Download failed with unexpected error"
        job["updated_at"] = datetime.now(timezone.utc)
        
        await _emit_job_update(job_id, job)

async def _emit_job_update(job_id: str, job: Dict[str, Any]):
    """Emit job update via WebSocket for real-time UI updates."""
    try:
        # Import WebSocket gateway
        from ai_karen_engine.chat.websocket_gateway import WebSocketGateway
        
        # Get the global WebSocket gateway instance
        # In a real implementation, this would be injected or retrieved from a service registry
        websocket_gateway = _get_websocket_gateway()
        
        if websocket_gateway:
            # Create model operation event message
            message_data = {
                "type": "model_operation_update",
                "event": "job_update",
                "data": {
                    "job_id": job_id,
                    "status": job["status"],
                    "progress": job["progress"],
                    "message": job["message"],
                    "error": job.get("error"),
                    "result": job.get("result"),
                    "updated_at": job["updated_at"].isoformat() if isinstance(job["updated_at"], datetime) else job["updated_at"]
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Broadcast to all connected users (in a real implementation, this would be more targeted)
            # For now, we'll use the event bus to publish the event
            from ai_karen_engine.event_bus import get_event_bus
            event_bus = get_event_bus()
            
            event_bus.publish(
                capsule="model_orchestrator",
                event_type="job_update",
                payload=message_data["data"],
                roles=["user", "admin"]
            )
            
            logger.info(f"Emitted job update for {job_id}: {job['status']} - {job['message']}")
        else:
            logger.warning("WebSocket gateway not available for job updates")
        
    except Exception as e:
        logger.error(f"Failed to emit job update for {job_id}: {e}")

def _get_websocket_gateway():
    """Get the WebSocket gateway instance. Placeholder for proper dependency injection."""
    # In a real implementation, this would be properly injected or retrieved from a service registry
    # For now, return None and rely on event bus
    return None

# Security Validation Endpoints

class SecurityValidationRequest(BaseModel):
    """Request model for security validation."""
    model_id: str = Field(..., description="Model identifier to validate")
    model_info: Dict[str, Any] = Field(..., description="Model information for validation")

class SecurityValidationResponse(BaseModel):
    """Response model for security validation."""
    model_id: str
    validation_passed: bool
    issues: List[str]
    validation_timestamp: str
    security_report: Optional[Dict[str, Any]] = None

@router.post("/security/validate")
async def validate_model_security(
    validation_request: SecurityValidationRequest,
    http_request: Request,
    current_user = Depends(get_current_user)
):
    """
    Validate model security before download.
    
    Requirements: 7.1, 7.4, 7.6, 7.7
    """
    try:
        # Check admin permission for security validation
        security_manager = get_security_manager()
        has_permission = await security_manager.check_admin_permission(current_user, http_request)
        
        if not has_permission:
            raise HTTPException(status_code=403, detail="Insufficient permissions for security validation")
        
        # Perform security validation
        models_dir = Path("models")  # This would come from config
        is_valid, issues = await security_manager.validate_model_download_security(
            user_id=current_user["user_id"],
            model_id=validation_request.model_id,
            model_info=validation_request.model_info,
            models_dir=models_dir,
            request=http_request
        )
        
        return SecurityValidationResponse(
            model_id=validation_request.model_id,
            validation_passed=is_valid,
            issues=issues,
            validation_timestamp=datetime.now(timezone.utc).isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate model security: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/security/validate-files")
async def validate_model_files(
    model_id: str,
    http_request: Request,
    files_info: List[Dict[str, Any]] = [],
    current_user = Depends(get_current_user)
):
    """
    Validate model files for integrity and security.
    
    Requirements: 7.1, 7.4, 13.6
    """
    try:
        # Check admin permission for file validation
        security_manager = get_security_manager()
        has_permission = await security_manager.check_admin_permission(current_user, http_request)
        
        if not has_permission:
            raise HTTPException(status_code=403, detail="Insufficient permissions for file validation")
        
        # Perform file validation
        models_dir = Path("models") / model_id.replace("/", "_")
        report = await security_manager.validate_model_files_integrity(
            user_id=current_user["user_id"],
            model_id=model_id,
            files_info=files_info,
            model_dir=models_dir
        )
        
        return {
            "model_id": model_id,
            "validation_report": {
                "total_files": report.total_files,
                "validated_files": report.validated_files,
                "failed_validations": report.failed_validations,
                "quarantined_files": report.quarantined_files,
                "total_size": report.total_size,
                "validation_timestamp": report.validation_timestamp.isoformat(),
                "security_issues": report.security_issues,
                "file_results": [
                    {
                        "file_path": result.file_path,
                        "size": result.size,
                        "checksum_verified": result.checksum_verified,
                        "quarantined": result.quarantined,
                        "error_message": result.error_message
                    }
                    for result in report.file_results
                ]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate model files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/security/cleanup")
async def cleanup_security_artifacts(
    http_request: Request,
    max_age_days: int = Query(30, description="Maximum age of artifacts to keep"),
    current_user = Depends(get_current_user)
):
    """
    Clean up old security artifacts like quarantined files.
    
    Requirements: 7.4, 13.6
    """
    try:
        # Check admin permission for security cleanup
        security_manager = get_security_manager()
        has_permission = await security_manager.check_admin_permission(current_user, http_request)
        
        if not has_permission:
            raise HTTPException(status_code=403, detail="Insufficient permissions for security cleanup")
        
        # Perform cleanup
        results = await security_manager.cleanup_security_artifacts(
            user_id=current_user["user_id"],
            max_age_days=max_age_days,
            request=http_request
        )
        
        return {
            "message": "Security cleanup completed",
            "results": results,
            "max_age_days": max_age_days,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cleanup security artifacts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# License Management Endpoints

class LicenseAcceptanceRequest(BaseModel):
    """Request model for license acceptance."""
    model_id: str = Field(..., description="Model identifier requiring license acceptance")
    license_type: str = Field(..., description="Type of license being accepted")
    license_text: str = Field(..., description="Full license text being accepted")
    acceptance_method: str = Field("web_ui", description="Method of acceptance (web_ui, cli, api)")

class LicenseComplianceResponse(BaseModel):
    """Response model for license compliance check."""
    model_id: str
    user_id: str
    compliant: bool
    acceptance_record: Optional[Dict[str, Any]] = None
    required_license: Optional[Dict[str, Any]] = None

@router.post("/license/accept")
async def accept_license(
    license_request: LicenseAcceptanceRequest,
    http_request: Request,
    current_user = Depends(get_current_user)
):
    """
    Accept a model license for compliance tracking.
    
    Requirements: 12.1, 12.2, 12.3
    """
    try:
        security_manager = get_security_manager()
        license_manager = security_manager.license_manager
        
        # Create license info from request
        license_info = {
            "type": license_request.license_type,
            "text": license_request.license_text
        }
        
        # Record license acceptance
        acceptance = await license_manager.require_license_acceptance(
            user_id=current_user["user_id"],
            model_id=license_request.model_id,
            license_info=license_info,
            request=http_request
        )
        
        # Audit the license acceptance
        await security_manager.audit_model_operation(
            user_id=current_user["user_id"],
            operation="license_accept",
            model_id=license_request.model_id,
            metadata={
                "license_type": license_request.license_type,
                "acceptance_method": license_request.acceptance_method
            },
            request=http_request
        )
        
        return {
            "message": "License accepted successfully",
            "model_id": license_request.model_id,
            "accepted_at": acceptance.accepted_at.isoformat(),
            "acceptance_id": f"{current_user['user_id']}_{license_request.model_id}_{int(acceptance.accepted_at.timestamp())}"
        }
        
    except Exception as e:
        logger.error(f"Failed to accept license for {license_request.model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/license/compliance/{model_id:path}", response_model=LicenseComplianceResponse)
async def check_license_compliance(
    model_id: str,
    http_request: Request,
    current_user = Depends(get_current_user)
):
    """
    Check license compliance for a model and user.
    
    Requirements: 12.1, 12.4
    """
    try:
        security_manager = get_security_manager()
        license_manager = security_manager.license_manager
        
        # Check compliance
        compliant = await license_manager.check_license_compliance(
            user_id=current_user["user_id"],
            model_id=model_id
        )
        
        # Get acceptance record if exists
        acceptance_record = await license_manager.get_license_acceptance_record(
            user_id=current_user["user_id"],
            model_id=model_id
        )
        
        return LicenseComplianceResponse(
            model_id=model_id,
            user_id=current_user["user_id"],
            compliant=compliant,
            acceptance_record=acceptance_record,
            required_license=None  # Would be populated with actual license info
        )
        
    except Exception as e:
        logger.error(f"Failed to check license compliance for {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/license/report")
async def get_license_compliance_report(
    http_request: Request,
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    current_user = Depends(get_current_user)
):
    """
    Generate license compliance report.
    
    Requirements: 12.5
    """
    try:
        # Check admin permission for compliance reports
        security_manager = get_security_manager()
        has_permission = await security_manager.check_admin_permission(current_user, http_request)
        
        if not has_permission:
            raise HTTPException(status_code=403, detail="Insufficient permissions to access compliance reports")
        
        license_manager = security_manager.license_manager
        
        # Parse dates if provided
        start_dt = None
        end_dt = None
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        # Generate report
        report = await license_manager.generate_compliance_report(
            start_date=start_dt,
            end_date=end_dt
        )
        
        # Audit the report access
        # Audit operation removed - compliance report generated
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate compliance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Management API Endpoints

class MigrationRequest(BaseModel):
    """Request model for migration operations."""
    dry_run: bool = Field(False, description="Perform dry run without making changes")

class EnsureModelsRequest(BaseModel):
    """Request model for ensuring models."""
    models: List[str] = Field(..., description="List of model types to ensure (distilbert, spacy, basic_cls)")

class GarbageCollectionRequest(BaseModel):
    """Request model for garbage collection."""
    max_age_days: Optional[int] = Field(None, description="Remove models older than this many days")
    min_free_space_gb: Optional[float] = Field(None, description="Ensure at least this much free space")
    preserve_pinned: bool = Field(True, description="Preserve pinned models")

class CompatibilityRequest(BaseModel):
    """Request model for compatibility checking."""
    model_id: str = Field(..., description="Model identifier to check compatibility")
    system_info: Optional[Dict[str, Any]] = Field(None, description="System information override")

@router.get("/registry")
async def get_registry(
    current_user = Depends(get_current_user)
):
    """
    Get the current model registry.
    
    Requirements: 9.1, 9.2
    """
    try:
        service = get_orchestrator_service()
        
        # Load registry data
        registry_path = Path(service.registry_path)
        if not registry_path.exists():
            return {"models": {}, "metadata": {"total_models": 0, "total_size_bytes": 0}}
        
        with open(registry_path, 'r') as f:
            registry_data = json.load(f)
        
        # Calculate metadata
        total_models = len(registry_data)
        total_size = sum(model.get("total_size", 0) for model in registry_data.values())
        
        return {
            "models": registry_data,
            "metadata": {
                "total_models": total_models,
                "total_size_bytes": total_size,
                "registry_path": str(registry_path),
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get registry: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/migrate")
async def migrate_layout(
    migration_request: MigrationRequest,
    http_request: Request,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """
    Migrate existing model layout to normalized structure.
    
    Requirements: 9.1, 9.2, 5.6, 4.1, 4.7
    """
    try:
        # Check migration permission
        security_manager = get_security_manager()
        has_permission = await security_manager.check_migration_permission(current_user, http_request)
        
        if not has_permission:
            raise HTTPException(status_code=403, detail="Insufficient permissions to perform model migration")
        
        # Audit the migration request
        await security_manager.audit_model_operation(
            user_id=current_user["user_id"],
            operation="migrate",
            metadata={"dry_run": migration_request.dry_run},
            request=http_request
        )
        
        # Create job for tracking
        job_id = str(uuid.uuid4())
        job = {
            "job_id": job_id,
            "status": "pending",
            "progress": 0.0,
            "message": f"Starting migration (dry_run={migration_request.dry_run})",
            "error": None,
            "result": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        _active_jobs[job_id] = job
        
        # Start migration in background
        background_tasks.add_task(
            _handle_migration,
            job_id,
            migration_request.dry_run,
            current_user
        )
        
        return {"job_id": job_id, "message": "Migration started"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start migration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ensure")
async def ensure_models(
    request: EnsureModelsRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """
    Ensure essential models are installed.
    
    Requirements: 10.6
    """
    try:
        # Create job for tracking
        job_id = str(uuid.uuid4())
        job = {
            "job_id": job_id,
            "status": "pending",
            "progress": 0.0,
            "message": f"Ensuring models: {', '.join(request.models)}",
            "error": None,
            "result": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        _active_jobs[job_id] = job
        # Start ensure operation in background
        background_tasks.add_task(
            _handle_ensure_models,
            job_id,
            request.models,
            current_user
        )
        
        return {"job_id": job_id, "message": "Ensure models started"}
        
    except Exception as e:
        logger.error(f"Failed to start ensure models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/gc")
async def garbage_collect(
    gc_request: GarbageCollectionRequest,
    http_request: Request,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """
    Perform garbage collection on unused models.
    
    Requirements: 13.2, 4.1, 4.7
    """
    try:
        # Check admin permission for GC
        security_manager = get_security_manager()
        has_permission = await security_manager.check_admin_permission(current_user, http_request)
        
        if not has_permission:
            raise HTTPException(status_code=403, detail="Insufficient permissions to perform garbage collection")
        
        # Audit the GC request
        await security_manager.audit_model_operation(
            user_id=current_user["user_id"],
            operation="garbage_collect",
            metadata={
                "max_age_days": gc_request.max_age_days,
                "min_free_space_gb": gc_request.min_free_space_gb,
                "preserve_pinned": gc_request.preserve_pinned
            }
        )
        
        # Create job for tracking
        job_id = str(uuid.uuid4())
        job = {
            "job_id": job_id,
            "status": "pending",
            "progress": 0.0,
            "message": "Starting garbage collection",
            "error": None,
            "result": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        _active_jobs[job_id] = job
        # Start GC in background
        background_tasks.add_task(
            _handle_garbage_collection,
            job_id,
            {
                "max_age_days": gc_request.max_age_days,
                "min_free_space_gb": gc_request.min_free_space_gb,
                "preserve_pinned": gc_request.preserve_pinned
            },
            current_user
        )
        
        return {"job_id": job_id, "message": "Garbage collection started"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start garbage collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/compatibility/{model_id:path}")
async def check_compatibility(
    model_id: str,
    current_user = Depends(get_current_user)
):
    """
    Check system compatibility for a model.
    
    Requirements: 13.2
    """
    try:
        # Basic compatibility check implementation
        # This would be enhanced with actual system detection
        
        import platform
        import psutil
        import shutil
        
        system_info = {
            "platform": platform.system(),
            "architecture": platform.machine(),
            "cpu_count": psutil.cpu_count(),
            "memory_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "disk_free_gb": round(shutil.disk_usage("/").free / (1024**3), 2),
            "python_version": platform.python_version()
        }
        
        # Basic compatibility assessment
        compatibility = {
            "compatible": True,
            "warnings": [],
            "requirements": {
                "min_memory_gb": 4,
                "min_disk_gb": 10,
                "supported_platforms": ["Linux", "Darwin", "Windows"]
            },
            "system_info": system_info
        }
        
        # Check basic requirements
        if system_info["memory_gb"] < compatibility["requirements"]["min_memory_gb"]:
            compatibility["warnings"].append(f"Low memory: {system_info['memory_gb']}GB < {compatibility['requirements']['min_memory_gb']}GB recommended")
        
        if system_info["disk_free_gb"] < compatibility["requirements"]["min_disk_gb"]:
            compatibility["warnings"].append(f"Low disk space: {system_info['disk_free_gb']}GB < {compatibility['requirements']['min_disk_gb']}GB recommended")
        
        if system_info["platform"] not in compatibility["requirements"]["supported_platforms"]:
            compatibility["compatible"] = False
            compatibility["warnings"].append(f"Unsupported platform: {system_info['platform']}")
        
        return {
            "model_id": model_id,
            "compatibility": compatibility,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to check compatibility for {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Additional background task handlers

async def _handle_migration(job_id: str, dry_run: bool, user: Dict[str, Any]):
    """Handle migration operation in background task."""
    job = _active_jobs[job_id]
    
    try:
        job["status"] = "running"
        job["message"] = f"Running migration (dry_run={dry_run})..."
        job["updated_at"] = datetime.now(timezone.utc)
        
        service = get_orchestrator_service()
        result = await service.migrate_layout(dry_run=dry_run)
        
        job["status"] = "completed"
        job["progress"] = 1.0
        job["message"] = f"Migration completed: {result.models_migrated} models migrated"
        job["result"] = {
            "models_migrated": result.models_migrated,
            "files_moved": result.files_moved,
            "corrupt_files_removed": result.corrupt_files_removed,
            "errors": result.errors,
            "duration_seconds": result.duration_seconds,
            "dry_run": result.dry_run
        }
        job["updated_at"] = datetime.now(timezone.utc)
        
        await _emit_job_update(job_id, job)
        
    except Exception as e:
        job["status"] = "failed"
        job["error"] = str(e)
        job["message"] = "Migration failed"
        job["updated_at"] = datetime.now(timezone.utc)
        
        await _emit_job_update(job_id, job)

async def _handle_ensure_models(job_id: str, models: List[str], user: Dict[str, Any]):
    """Handle ensure models operation in background task."""
    job = _active_jobs[job_id]
    
    try:
        job["status"] = "running"
        job["message"] = f"Ensuring models: {', '.join(models)}"
        job["updated_at"] = datetime.now(timezone.utc)
        
        service = get_orchestrator_service()
        result = await service.ensure_models(models)
        
        job["status"] = "completed"
        job["progress"] = 1.0
        job["message"] = f"Ensured {len(result.models_ensured)} models"
        job["result"] = {
            "models_ensured": result.models_ensured,
            "models_skipped": result.models_skipped,
            "errors": result.errors,
            "duration_seconds": result.duration_seconds
        }
        job["updated_at"] = datetime.now(timezone.utc)
        
        await _emit_job_update(job_id, job)
        
    except Exception as e:
        job["status"] = "failed"
        job["error"] = str(e)
        job["message"] = "Ensure models failed"
        job["updated_at"] = datetime.now(timezone.utc)
        
        await _emit_job_update(job_id, job)

async def _handle_garbage_collection(job_id: str, criteria: Dict[str, Any], user: Dict[str, Any]):
    """Handle garbage collection operation in background task."""
    job = _active_jobs[job_id]
    
    try:
        job["status"] = "running"
        job["message"] = "Running garbage collection..."
        job["updated_at"] = datetime.now(timezone.utc)
        
        service = get_orchestrator_service()
        result = await service.garbage_collect(criteria)
        
        job["status"] = "completed"
        job["progress"] = 1.0
        job["message"] = f"GC completed: {len(result.models_removed)} models removed"
        job["result"] = {
            "models_removed": result.models_removed,
            "space_freed_bytes": result.space_freed_bytes,
            "models_preserved": result.models_preserved,
            "duration_seconds": result.duration_seconds
        }
        job["updated_at"] = datetime.now(timezone.utc)
        
        await _emit_job_update(job_id, job)
        
    except Exception as e:
        job["status"] = "failed"
        job["error"] = str(e)
        job["message"] = "Garbage collection failed"
        job["updated_at"] = datetime.now(timezone.utc)
        
        await _emit_job_update(job_id, job)

# Health check endpoints
@router.get("/health")
async def health_check():
    """
    Check health of model orchestrator service.
    
    Requirements: 9.1, 9.2
    """
    try:
        health_checker = get_model_orchestrator_health_checker()
        health = await health_checker.get_health_summary()
        
        return {
            "status": health["status"],
            "timestamp": health["timestamp"],
            "details": health
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e)
        }

@router.get("/health/detailed")
async def detailed_health_check(
    current_user = Depends(get_current_user)
):
    """
    Run detailed health checks for all model orchestrator components.
    
    Requirements: 4.3, 4.6, 7.4, 15.3
    """
    try:
        health_checker = get_model_orchestrator_health_checker()
        health = await health_checker.run_all_health_checks()
        
        return health
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return {
            "overall_status": "critical",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e)
        }

@router.get("/metrics/summary")
async def metrics_summary(
    current_user = Depends(get_current_user)
):
    """
    Get metrics summary for model orchestrator operations.
    
    Requirements: 4.3, 4.6
    """
    try:
        metrics = get_model_orchestrator_metrics()
        summary = metrics.get_metrics_summary()
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": summary
        }
        
    except Exception as e:
        logger.error(f"Failed to get metrics summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/errors/statistics")
async def error_statistics(
    hours: int = Query(24, ge=1, le=168),  # 1 hour to 1 week
    current_user = Depends(get_current_user)
):
    """
    Get error statistics for model orchestrator operations.
    
    Requirements: 15.3
    """
    try:
        error_tracker = get_model_orchestrator_error_tracker()
        stats = error_tracker.get_error_statistics(hours=hours)
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get error statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/errors/trends")
async def error_trends(
    days: int = Query(7, ge=1, le=30),  # 1 day to 30 days
    current_user = Depends(get_current_user)
):
    """
    Get error trends for model orchestrator operations.
    
    Requirements: 15.3
    """
    try:
        error_tracker = get_model_orchestrator_error_tracker()
        trends = error_tracker.get_error_trends(days=days)
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "trends": trends
        }
        
    except Exception as e:
        logger.error(f"Failed to get error trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))