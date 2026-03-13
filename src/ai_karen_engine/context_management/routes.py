"""
Context Management API Routes

FastAPI routes for context management, file uploads, sharing,
versioning, and search functionality.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ai_karen_engine.utils.dependency_checks import import_fastapi
from ai_karen_engine.context_management.models import (
    ContextAccessLevel,
    ContextEntry,
    ContextFileType,
    ContextQuery,
    ContextSearchResult,
    ContextShare,
    ContextStatus,
    ContextType,
)

# Import FastAPI components
APIRouter = import_fastapi("APIRouter")
UploadFile = import_fastapi("UploadFile")
File = import_fastapi("File")
HTTPException = import_fastapi("HTTPException")
status = import_fastapi("status")
Depends = import_fastapi("Depends")
Query = import_fastapi("Query")
Body = import_fastapi("Body")
Path = import_fastapi("Path")

# Create router
router = APIRouter(prefix="/api/context", tags=["context-management"])

logger = logging.getLogger(__name__)


# ============================================================================
-- Dependencies
-- ============================================================================

async def get_context_management_service():
    """Dependency to get context management service."""
    # This would be replaced with actual dependency injection
    from ai_karen_engine.context_management.service import ContextManagementService
    from ai_karen_engine.database.memory_manager import MemoryManager
    
    # Initialize with default values (in production, these would come from config)
    memory_manager = MemoryManager(None, None)  # Placeholder
    service = ContextManagementService(memory_manager)
    return service


async def get_file_upload_handler():
    """Dependency to get file upload handler."""
    from ai_karen_engine.context_management.file_handler import FileUploadHandler
    
    # Initialize with default values (in production, these would come from config)
    handler = FileUploadHandler()
    return handler


async def get_context_preprocessor():
    """Dependency to get context preprocessor."""
    from ai_karen_engine.context_management.preprocessor import ContextPreprocessor
    
    # Initialize with default values
    preprocessor = ContextPreprocessor()
    return preprocessor


# ============================================================================
-- Context CRUD Operations
-- ============================================================================

@router.post("/contexts", response_model=Dict[str, Any])
async def create_context(
    title: str,
    content: str = "",
    context_type: ContextType = ContextType.CUSTOM,
    org_id: Optional[str] = None,
    session_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
    access_level: ContextAccessLevel = ContextAccessLevel.PRIVATE,
    metadata: Optional[Dict[str, Any]] = None,
    tags: Optional[List[str]] = None,
    importance_score: float = 5.0,
    expires_in_days: Optional[int] = None,
    user_id: str = Query(..., description="User ID"),
    context_service = Depends(get_context_management_service),
    preprocessor = Depends(get_context_preprocessor),
):
    """
    Create a new context entry.
    
    Args:
        title: Context title
        content: Context content
        context_type: Type of context
        org_id: Organization ID
        session_id: Session ID
        conversation_id: Conversation ID
        access_level: Access level for context
        metadata: Additional metadata
        tags: List of tags
        importance_score: Importance score (1-10)
        expires_in_days: Days until expiration
        user_id: User ID creating context
        
    Returns:
        Created context information
    """
    try:
        # Validate importance score
        if not 1.0 <= importance_score <= 10.0:
            raise HTTPException(
                status_code=400,
                detail="Importance score must be between 1.0 and 10.0"
            )
        
        # Create context
        context = await context_service.create_context(
            user_id=user_id,
            title=title,
            content=content,
            context_type=context_type,
            org_id=org_id,
            session_id=session_id,
            conversation_id=conversation_id,
            access_level=access_level,
            metadata=metadata,
            tags=tags,
            importance_score=importance_score,
            expires_in_days=expires_in_days,
        )
        
        # Preprocess context
        context = await preprocessor.preprocess_context(context)
        
        return {
            "success": True,
            "context": context.to_dict(),
            "message": "Context created successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to create context: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create context: {str(e)}"
        )


@router.get("/contexts/{context_id}", response_model=Dict[str, Any])
async def get_context(
    context_id: str,
    include_content: bool = True,
    include_files: bool = False,
    user_id: str = Query(..., description="User ID"),
    context_service = Depends(get_context_management_service),
):
    """
    Get a context entry by ID.
    
    Args:
        context_id: Context ID to retrieve
        include_content: Whether to include content
        include_files: Whether to include associated files
        user_id: User ID requesting context
        
    Returns:
        Context information
    """
    try:
        context = await context_service.get_context(
            context_id=context_id,
            user_id=user_id,
            include_content=include_content,
            include_files=include_files,
        )
        
        if not context:
            raise HTTPException(
                status_code=404,
                detail="Context not found or access denied"
            )
        
        return {
            "success": True,
            "context": context.to_dict(include_content=include_content),
            "message": "Context retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get context {context_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get context: {str(e)}"
        )


@router.put("/contexts/{context_id}", response_model=Dict[str, Any])
async def update_context(
    context_id: str,
    title: Optional[str] = None,
    content: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    tags: Optional[List[str]] = None,
    importance_score: Optional[float] = None,
    create_version: bool = True,
    change_summary: Optional[str] = None,
    user_id: str = Query(..., description="User ID"),
    context_service = Depends(get_context_management_service),
    preprocessor = Depends(get_context_preprocessor),
):
    """
    Update a context entry.
    
    Args:
        context_id: Context ID to update
        title: New title
        content: New content
        metadata: New metadata
        tags: New tags
        importance_score: New importance score
        create_version: Whether to create new version
        change_summary: Summary of changes
        user_id: User ID updating context
        
    Returns:
        Updated context information
    """
    try:
        # Validate importance score if provided
        if importance_score is not None and not 1.0 <= importance_score <= 10.0:
            raise HTTPException(
                status_code=400,
                detail="Importance score must be between 1.0 and 10.0"
            )
        
        # Update context
        context = await context_service.update_context(
            context_id=context_id,
            user_id=user_id,
            title=title,
            content=content,
            metadata=metadata,
            tags=tags,
            importance_score=importance_score,
            create_version=create_version,
            change_summary=change_summary,
        )
        
        if not context:
            raise HTTPException(
                status_code=404,
                detail="Context not found or access denied"
            )
        
        # Preprocess updated context
        context = await preprocessor.preprocess_context(context)
        
        return {
            "success": True,
            "context": context.to_dict(),
            "message": "Context updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update context {context_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update context: {str(e)}"
        )


@router.delete("/contexts/{context_id}", response_model=Dict[str, Any])
async def delete_context(
    context_id: str,
    permanent: bool = False,
    user_id: str = Query(..., description="User ID"),
    context_service = Depends(get_context_management_service),
):
    """
    Delete a context entry.
    
    Args:
        context_id: Context ID to delete
        permanent: Whether to permanently delete
        user_id: User ID deleting context
        
    Returns:
        Deletion result
    """
    try:
        success = await context_service.delete_context(
            context_id=context_id,
            user_id=user_id,
            permanent=permanent,
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Context not found or access denied"
            )
        
        return {
            "success": True,
            "message": f"Context {'permanently deleted' if permanent else 'soft deleted'} successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete context {context_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete context: {str(e)}"
        )


# ============================================================================
-- Context Search and Querying
-- ============================================================================

@router.post("/contexts/search", response_model=Dict[str, Any])
async def search_contexts(
    query: ContextQuery,
    user_id: str = Query(..., description="User ID"),
    context_service = Depends(get_context_management_service),
):
    """
    Search for contexts based on query parameters.
    
    Args:
        query: Search query parameters
        user_id: User ID performing search
        
    Returns:
        Search results
    """
    try:
        # Validate query parameters
        if query.top_k <= 0 or query.top_k > 100:
            raise HTTPException(
                status_code=400,
                detail="top_k must be between 1 and 100"
            )
        
        if not 0.0 <= query.similarity_threshold <= 1.0:
            raise HTTPException(
                status_code=400,
                detail="similarity_threshold must be between 0.0 and 1.0"
            )
        
        # Search contexts
        results = await context_service.search_contexts(
            query=query,
            user_id=user_id,
        )
        
        return {
            "success": True,
            "results": [result.to_dict() for result in results],
            "total_results": len(results),
            "query": query.to_dict(),
            "message": "Search completed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to search contexts: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search contexts: {str(e)}"
        )


# ============================================================================
-- File Upload Operations
-- ============================================================================

@router.post("/contexts/{context_id}/files", response_model=Dict[str, Any])
async def upload_file(
    context_id: str,
    file: UploadFile = File(...),
    metadata: Optional[Dict[str, Any]] = None,
    user_id: str = Query(..., description="User ID"),
    file_handler = Depends(get_file_upload_handler),
    context_service = Depends(get_context_management_service),
):
    """
    Upload a file to a context.
    
    Args:
        context_id: Context ID to associate file with
        file: File to upload
        metadata: Additional metadata for file
        user_id: User ID uploading file
        
    Returns:
        Upload result
    """
    try:
        # Check if context exists and user has access
        context = await context_service.get_context(
            context_id=context_id,
            user_id=user_id,
            include_content=False,
        )
        
        if not context:
            raise HTTPException(
                status_code=404,
                detail="Context not found or access denied"
            )
        
        # Read file data
        file_data = await file.read()
        
        # Handle upload
        context_file, error = await file_handler.handle_upload(
            file_data=file_data,
            filename=file.filename,
            context_id=context_id,
            user_id=user_id,
            mime_type=file.content_type,
            metadata=metadata,
        )
        
        if error:
            raise HTTPException(
                status_code=400,
                detail=f"File upload failed: {error}"
            )
        
        return {
            "success": True,
            "file": context_file.to_dict(),
            "message": "File uploaded successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload file: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload file: {str(e)}"
        )


@router.get("/files/{file_id}", response_model=Dict[str, Any])
async def get_file(
    file_id: str,
    user_id: str = Query(..., description="User ID"),
    file_handler = Depends(get_file_upload_handler),
):
    """
    Get file information by ID.
    
    Args:
        file_id: File ID to retrieve
        user_id: User ID requesting file
        
    Returns:
        File information
    """
    try:
        context_file = await file_handler.get_file(
            file_id=file_id,
            user_id=user_id,
            check_access=True,
        )
        
        if not context_file:
            raise HTTPException(
                status_code=404,
                detail="File not found or access denied"
            )
        
        return {
            "success": True,
            "file": context_file.to_dict(),
            "message": "File retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get file {file_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get file: {str(e)}"
        )


@router.delete("/files/{file_id}", response_model=Dict[str, Any])
async def delete_file(
    file_id: str,
    permanent: bool = False,
    user_id: str = Query(..., description="User ID"),
    file_handler = Depends(get_file_upload_handler),
):
    """
    Delete a file.
    
    Args:
        file_id: File ID to delete
        permanent: Whether to permanently delete
        user_id: User ID deleting file
        
    Returns:
        Deletion result
    """
    try:
        success = await file_handler.delete_file(
            file_id=file_id,
            user_id=user_id,
            permanent=permanent,
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="File not found or access denied"
            )
        
        return {
            "success": True,
            "message": f"File {'permanently deleted' if permanent else 'soft deleted'} successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete file {file_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete file: {str(e)}"
        )


# ============================================================================
-- Context Sharing Operations
-- ============================================================================

@router.post("/contexts/{context_id}/share", response_model=Dict[str, Any])
async def share_context(
    context_id: str,
    shared_with: Optional[str] = None,
    access_level: ContextAccessLevel = ContextAccessLevel.SHARED,
    permissions: Optional[List[str]] = None,
    expires_in_days: Optional[int] = None,
    user_id: str = Query(..., description="User ID"),
    context_service = Depends(get_context_management_service),
):
    """
    Share a context with another user or group.
    
    Args:
        context_id: Context ID to share
        shared_with: User ID to share with
        access_level: Access level for share
        permissions: List of permissions
        expires_in_days: Days until share expires
        user_id: User ID sharing context
        
    Returns:
        Share result
    """
    try:
        # Check if context exists and user has access
        context = await context_service.get_context(
            context_id=context_id,
            user_id=user_id,
            include_content=False,
        )
        
        if not context:
            raise HTTPException(
                status_code=404,
                detail="Context not found or access denied"
            )
        
        # Create share
        share = await context_service.share_context(
            context_id=context_id,
            user_id=user_id,
            shared_with=shared_with,
            access_level=access_level,
            permissions=permissions,
            expires_in_days=expires_in_days,
        )
        
        if not share:
            raise HTTPException(
                status_code=500,
                detail="Failed to create share"
            )
        
        return {
            "success": True,
            "share": share.to_dict(),
            "message": "Context shared successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to share context {context_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to share context: {str(e)}"
        )


# ============================================================================
-- Context Versioning Operations
-- ============================================================================

@router.get("/contexts/{context_id}/versions", response_model=Dict[str, Any])
async def get_context_versions(
    context_id: str,
    user_id: str = Query(..., description="User ID"),
    context_service = Depends(get_context_management_service),
):
    """
    Get all versions of a context.
    
    Args:
        context_id: Context ID
        user_id: User ID requesting versions
        
    Returns:
        List of context versions
    """
    try:
        versions = await context_service.get_context_versions(
            context_id=context_id,
            user_id=user_id,
        )
        
        return {
            "success": True,
            "versions": [version.to_dict() for version in versions],
            "total_versions": len(versions),
            "message": "Versions retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to get versions for context {context_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get versions: {str(e)}"
        )


# ============================================================================
-- Statistics and Analytics
-- ============================================================================

@router.get("/contexts/stats", response_model=Dict[str, Any])
async def get_context_stats(
    user_id: str = Query(..., description="User ID"),
    org_id: Optional[str] = None,
    context_service = Depends(get_context_management_service),
):
    """
    Get context statistics for a user or organization.
    
    Args:
        user_id: User ID
        org_id: Organization ID (optional)
        
    Returns:
        Context statistics
    """
    try:
        stats = await context_service.get_context_stats(
            user_id=user_id,
            org_id=org_id,
        )
        
        return {
            "success": True,
            "stats": stats,
            "message": "Statistics retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to get context stats for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get statistics: {str(e)}"
        )


# ============================================================================
-- Utility Endpoints
-- ============================================================================

@router.get("/file-types", response_model=Dict[str, Any])
async def get_supported_file_types(
    file_handler = Depends(get_file_upload_handler),
):
    """
    Get list of supported file types.
    
    Returns:
        List of supported file types
    """
    try:
        file_types = file_handler.get_supported_file_types()
        
        return {
            "success": True,
            "file_types": file_types,
            "message": "File types retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to get supported file types: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get file types: {str(e)}"
        )


@router.get("/context-types", response_model=Dict[str, Any])
async def get_context_types():
    """
    Get list of available context types.
    
    Returns:
        List of context types
    """
    try:
        context_types = [
            {
                "value": ctx_type.value,
                "name": ctx_type.name,
                "description": _get_context_type_description(ctx_type)
            }
            for ctx_type in ContextType
        ]
        
        return {
            "success": True,
            "context_types": context_types,
            "message": "Context types retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to get context types: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get context types: {str(e)}"
        )


def _get_context_type_description(context_type: ContextType) -> str:
    """Get description for context type."""
    descriptions = {
        ContextType.CONVERSATION: "Chat conversation or dialogue",
        ContextType.DOCUMENT: "Document or text file",
        ContextType.CODE: "Source code or script",
        ContextType.IMAGE: "Image or graphic file",
        ContextType.AUDIO: "Audio or sound file",
        ContextType.VIDEO: "Video or multimedia file",
        ContextType.WEB_PAGE: "Web page or online content",
        ContextType.NOTE: "Personal note or memo",
        ContextType.TASK: "Task or action item",
        ContextType.MEMORY: "Memory or recollection",
        ContextType.CUSTOM: "Custom or user-defined type",
    }
    
    return descriptions.get(context_type, "Unknown context type")


# ============================================================================
-- Error Handlers
-- ============================================================================

@router.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return {
        "success": False,
        "error": {
            "status_code": exc.status_code,
            "detail": exc.detail,
            "type": "http_exception"
        }
    }


@router.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception in context management: {exc}")
    return {
        "success": False,
        "error": {
            "status_code": 500,
            "detail": "Internal server error",
            "type": "general_exception"
        }
    }