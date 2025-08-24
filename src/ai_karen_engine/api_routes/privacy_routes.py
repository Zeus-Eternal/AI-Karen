"""
Privacy Compliance API Routes - Phase 4.1.c
Provides endpoints for data export, erasure, and privacy compliance features.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

try:
    from fastapi import APIRouter, HTTPException, Request, Depends
    from fastapi.responses import JSONResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    # Graceful fallback for environments without FastAPI
    APIRouter = None
    HTTPException = None
    Request = None
    Depends = None
    JSONResponse = None
    FASTAPI_AVAILABLE = False

from pydantic import BaseModel, ConfigDict, Field

from ai_karen_engine.services.privacy_compliance import (
    PrivacyComplianceService,
    DataExportFormat,
    ErasureType,
    PrivacyRequestStatus,
    get_privacy_compliance_service
)
from ai_karen_engine.api_routes.unified_schemas import (
    ErrorHandler,
    ErrorType,
    SuccessResponse
)
from ai_karen_engine.middleware.rbac import require_scopes, check_scope

logger = logging.getLogger(__name__)

# Request/Response Models
class DataExportRequest(BaseModel):
    """Request for data export"""
    user_id: str = Field(..., min_length=1, description="User ID for data export")
    tenant_id: Optional[str] = Field(None, description="Tenant ID (optional)")
    data_types: List[str] = Field(
        default=["all"], 
        description="Types of data to export: memories, conversations, analytics, audit_logs, or all"
    )
    export_format: DataExportFormat = Field(
        default=DataExportFormat.JSON,
        description="Export format: json, csv, or xml"
    )
    include_pii: bool = Field(
        default=False,
        description="Whether to include PII in export (requires additional verification)"
    )

class DataErasureRequest(BaseModel):
    """Request for data erasure"""
    user_id: str = Field(..., min_length=1, description="User ID for data erasure")
    tenant_id: Optional[str] = Field(None, description="Tenant ID (optional)")
    erasure_type: ErasureType = Field(
        default=ErasureType.SOFT_DELETE,
        description="Type of erasure: soft_delete, hard_delete, or anonymize"
    )
    data_types: List[str] = Field(
        default=["all"],
        description="Types of data to erase: memories, conversations, embeddings, cache, or all"
    )
    confirmation_token: str = Field(
        ...,
        description="Confirmation token to verify erasure request"
    )

class PrivacyRequestResponse(BaseModel):
    """Response for privacy request creation"""
    request_id: str = Field(..., description="Unique request ID")
    status: PrivacyRequestStatus = Field(..., description="Request status")
    verification_token: str = Field(..., description="Token for request verification")
    estimated_completion: str = Field(..., description="Estimated completion time")
    next_steps: str = Field(..., description="Instructions for next steps")

class PrivacyRequestStatusResponse(BaseModel):
    """Response for privacy request status"""
    request_id: str
    status: PrivacyRequestStatus
    created_at: str
    completed_at: Optional[str] = None
    progress: Dict[str, Any] = Field(default_factory=dict)

# Create router if FastAPI is available
if FASTAPI_AVAILABLE:
    router = APIRouter(tags=["privacy"], prefix="/privacy")
    
    def get_correlation_id(request: Request) -> str:
        """Extract or generate correlation ID for request tracking"""
        return request.headers.get("X-Correlation-Id", str(uuid.uuid4()))
    
    def get_privacy_service() -> PrivacyComplianceService:
        """Dependency to get privacy compliance service"""
        return get_privacy_compliance_service()
    
    @router.post("/export/request", response_model=PrivacyRequestResponse)
    async def request_data_export(
        request_data: DataExportRequest,
        http_request: Request,
        privacy_service: PrivacyComplianceService = Depends(get_privacy_service)
    ):
        """
        Request data export for a user.
        
        Creates a privacy request for data export. The actual export will be processed
        asynchronously and can be retrieved using the request ID.
        """
        correlation_id = get_correlation_id(http_request)
        
        # Check RBAC permissions
        if not await check_scope(http_request, "admin:read"):
            error_response = ErrorHandler.create_authorization_error_response(
                correlation_id=correlation_id,
                path=str(http_request.url.path),
                message="Insufficient permissions for data export"
            )
            raise HTTPException(status_code=403, detail=error_response.model_dump(mode="json"))
        
        try:
            # Create privacy request
            privacy_request = privacy_service.create_privacy_request(
                request_type="export",
                user_id=request_data.user_id,
                tenant_id=request_data.tenant_id,
                data_types=request_data.data_types,
                export_format=request_data.export_format
            )
            
            return PrivacyRequestResponse(
                request_id=privacy_request.request_id,
                status=privacy_request.status,
                verification_token=privacy_request.verification_token,
                estimated_completion="24-48 hours",
                next_steps="Use the request ID to check status and retrieve export when ready"
            )
            
        except Exception as e:
            logger.error(f"Failed to create export request: {e}")
            error_response = ErrorHandler.create_internal_error_response(
                correlation_id=correlation_id,
                path=str(http_request.url.path),
                error=e
            )
            raise HTTPException(status_code=500, detail=error_response.model_dump(mode="json"))
    
    @router.post("/erasure/request", response_model=PrivacyRequestResponse)
    async def request_data_erasure(
        request_data: DataErasureRequest,
        http_request: Request,
        privacy_service: PrivacyComplianceService = Depends(get_privacy_service)
    ):
        """
        Request data erasure for a user.
        
        Creates a privacy request for data erasure. This is a sensitive operation
        that requires additional verification and appropriate permissions.
        """
        correlation_id = get_correlation_id(http_request)
        
        # Check RBAC permissions - erasure requires admin:write
        if not await check_scope(http_request, "admin:write"):
            error_response = ErrorHandler.create_authorization_error_response(
                correlation_id=correlation_id,
                path=str(http_request.url.path),
                message="Insufficient permissions for data erasure"
            )
            raise HTTPException(status_code=403, detail=error_response.model_dump(mode="json"))
        
        try:
            # Create privacy request
            privacy_request = privacy_service.create_privacy_request(
                request_type="erasure",
                user_id=request_data.user_id,
                tenant_id=request_data.tenant_id,
                data_types=request_data.data_types,
                erasure_type=request_data.erasure_type
            )
            
            warning_message = "Data erasure is irreversible"
            if request_data.erasure_type == ErasureType.HARD_DELETE:
                warning_message += " and will permanently remove all data"
            
            return PrivacyRequestResponse(
                request_id=privacy_request.request_id,
                status=privacy_request.status,
                verification_token=privacy_request.verification_token,
                estimated_completion="24-48 hours",
                next_steps=f"WARNING: {warning_message}. Use verification token to confirm."
            )
            
        except Exception as e:
            logger.error(f"Failed to create erasure request: {e}")
            error_response = ErrorHandler.create_internal_error_response(
                correlation_id=correlation_id,
                path=str(http_request.url.path),
                error=e
            )
            raise HTTPException(status_code=500, detail=error_response.model_dump(mode="json"))
    
    @router.get("/request/{request_id}/status", response_model=PrivacyRequestStatusResponse)
    async def get_privacy_request_status(
        request_id: str,
        http_request: Request,
        privacy_service: PrivacyComplianceService = Depends(get_privacy_service)
    ):
        """
        Get the status of a privacy request.
        
        Returns the current status and progress of a data export or erasure request.
        """
        correlation_id = get_correlation_id(http_request)
        
        # Check RBAC permissions
        if not await check_scope(http_request, "admin:read"):
            error_response = ErrorHandler.create_authorization_error_response(
                correlation_id=correlation_id,
                path=str(http_request.url.path),
                message="Insufficient permissions to view privacy requests"
            )
            raise HTTPException(status_code=403, detail=error_response.model_dump(mode="json"))
        
        try:
            privacy_request = privacy_service.get_privacy_request_status(request_id)
            
            if not privacy_request:
                error_response = ErrorHandler.create_not_found_error_response(
                    correlation_id=correlation_id,
                    path=str(http_request.url.path),
                    resource="Privacy request"
                )
                raise HTTPException(status_code=404, detail=error_response.model_dump(mode="json"))
            
            return PrivacyRequestStatusResponse(
                request_id=privacy_request.request_id,
                status=privacy_request.status,
                created_at=privacy_request.created_at.isoformat(),
                completed_at=privacy_request.completed_at.isoformat() if privacy_request.completed_at else None,
                progress={
                    "request_type": privacy_request.request_type,
                    "data_types": privacy_request.data_types,
                    "user_id": privacy_request.user_id,
                    "tenant_id": privacy_request.tenant_id
                }
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get request status: {e}")
            error_response = ErrorHandler.create_internal_error_response(
                correlation_id=correlation_id,
                path=str(http_request.url.path),
                error=e
            )
            raise HTTPException(status_code=500, detail=error_response.model_dump(mode="json"))
    
    @router.post("/request/{request_id}/process")
    async def process_privacy_request(
        request_id: str,
        verification_token: str,
        http_request: Request,
        privacy_service: PrivacyComplianceService = Depends(get_privacy_service)
    ):
        """
        Process a privacy request after verification.
        
        Executes the actual data export or erasure after proper verification.
        """
        correlation_id = get_correlation_id(http_request)
        
        # Check RBAC permissions
        if not await check_scope(http_request, "admin:write"):
            error_response = ErrorHandler.create_authorization_error_response(
                correlation_id=correlation_id,
                path=str(http_request.url.path),
                message="Insufficient permissions to process privacy requests"
            )
            raise HTTPException(status_code=403, detail=error_response.model_dump(mode="json"))
        
        try:
            privacy_request = privacy_service.get_privacy_request_status(request_id)
            
            if not privacy_request:
                error_response = ErrorHandler.create_not_found_error_response(
                    correlation_id=correlation_id,
                    path=str(http_request.url.path),
                    resource="Privacy request"
                )
                raise HTTPException(status_code=404, detail=error_response.model_dump(mode="json"))
            
            # Verify token
            if privacy_request.verification_token != verification_token:
                error_response = ErrorHandler.create_authorization_error_response(
                    correlation_id=correlation_id,
                    path=str(http_request.url.path),
                    message="Invalid verification token"
                )
                raise HTTPException(status_code=403, detail=error_response.model_dump(mode="json"))
            
            # Process based on request type
            if privacy_request.request_type == "export":
                result = await privacy_service.process_data_export_request(
                    request_id=request_id,
                    include_pii=False  # Default to no PII for security
                )
                
                return SuccessResponse(
                    data=result,
                    message="Data export completed successfully",
                    correlation_id=correlation_id,
                    timestamp=datetime.utcnow()
                )
                
            elif privacy_request.request_type == "erasure":
                result = await privacy_service.process_data_erasure_request(
                    request_id=request_id,
                    correlation_id=correlation_id
                )
                
                return SuccessResponse(
                    data=result,
                    message="Data erasure completed successfully",
                    correlation_id=correlation_id,
                    timestamp=datetime.utcnow()
                )
            
            else:
                raise ValueError(f"Unknown request type: {privacy_request.request_type}")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to process privacy request: {e}")
            error_response = ErrorHandler.create_internal_error_response(
                correlation_id=correlation_id,
                path=str(http_request.url.path),
                error=e
            )
            raise HTTPException(status_code=500, detail=error_response.model_dump(mode="json"))
    
    @router.post("/content/sanitize")
    async def sanitize_content(
        content: str,
        max_length: int = 100,
        http_request: Request,
        privacy_service: PrivacyComplianceService = Depends(get_privacy_service)
    ):
        """
        Sanitize content for UI display by removing PII and creating safe previews.
        
        This endpoint helps ensure that UI components never display raw PII.
        """
        correlation_id = get_correlation_id(http_request)
        
        # Check RBAC permissions
        if not await check_scope(http_request, "memory:read"):
            error_response = ErrorHandler.create_authorization_error_response(
                correlation_id=correlation_id,
                path=str(http_request.url.path),
                message="Insufficient permissions to sanitize content"
            )
            raise HTTPException(status_code=403, detail=error_response.model_dump(mode="json"))
        
        try:
            safe_preview = privacy_service.create_safe_content_preview(content)
            
            return SuccessResponse(
                data=safe_preview,
                message="Content sanitized successfully",
                correlation_id=correlation_id,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Failed to sanitize content: {e}")
            error_response = ErrorHandler.create_internal_error_response(
                correlation_id=correlation_id,
                path=str(http_request.url.path),
                error=e
            )
            raise HTTPException(status_code=500, detail=error_response.model_dump(mode="json"))
    
    @router.get("/health")
    async def privacy_health_check():
        """Health check for privacy compliance service"""
        return {
            "status": "healthy",
            "service": "privacy_compliance",
            "features": {
                "data_export": True,
                "data_erasure": True,
                "pii_detection": True,
                "content_sanitization": True
            },
            "timestamp": datetime.utcnow().isoformat()
        }

else:
    # Fallback when FastAPI is not available
    router = None
    logger.warning("FastAPI not available, privacy routes disabled")

# Export router for inclusion in main FastAPI app
__all__ = ["router"] if FASTAPI_AVAILABLE else []