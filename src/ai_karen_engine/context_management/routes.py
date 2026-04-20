"""
Context Management API Routes

FastAPI routes for context management, file uploads, sharing,
versioning, and search functionality.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from ai_karen_engine.context_management.models import (
    ContextAccessLevel,
    ContextQuery,
    ContextType,
)

router = APIRouter(tags=["context-management"])

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------

def _get_integration():
    """Return the initialized context-management integration singleton."""
    from ai_karen_engine.context_management.integration import (
        get_context_management_integration,
    )

    integration = get_context_management_integration()
    if integration is None:
        raise HTTPException(
            status_code=503,
            detail="Context management is not initialized",
        )
    return integration


async def get_context_management_service():
    """Dependency to get the shared context management service."""
    integration = _get_integration()
    if integration.context_service is None:
        raise HTTPException(
            status_code=503,
            detail="Context management service is unavailable",
        )
    return integration.context_service


async def get_file_upload_handler():
    """Dependency to get the shared file upload handler."""
    integration = _get_integration()
    if integration.file_handler is None:
        raise HTTPException(
            status_code=503,
            detail="Context file handler is unavailable",
        )
    return integration.file_handler


async def get_context_preprocessor():
    """Dependency to get the shared context preprocessor."""
    integration = _get_integration()
    if integration.preprocessor is None:
        raise HTTPException(
            status_code=503,
            detail="Context preprocessor is unavailable",
        )
    return integration.preprocessor


# ---------------------------------------------------------------------------
# Context CRUD Operations
# ---------------------------------------------------------------------------

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
    tags: Optional[list[str]] = None,
    importance_score: float = 5.0,
    expires_in_days: Optional[int] = None,
    user_id: str = Query(..., description="User ID"),
    context_service=Depends(get_context_management_service),
    preprocessor=Depends(get_context_preprocessor),
):
    """
    Create a new context entry.
    """
    try:
        if not title or not title.strip():
            raise HTTPException(
                status_code=400,
                detail="Title is required",
            )

        if not 1.0 <= importance_score <= 10.0:
            raise HTTPException(
                status_code=400,
                detail="Importance score must be between 1.0 and 10.0",
            )

        context = await context_service.create_context(
            user_id=user_id,
            title=title.strip(),
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

        context = await preprocessor.preprocess_context(context)

        return {
            "success": True,
            "context": context.to_dict(),
            "message": "Context created successfully",
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to create context: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create context: {str(exc)}",
        )


@router.get("/contexts/{context_id}", response_model=Dict[str, Any])
async def get_context(
    context_id: str,
    include_content: bool = True,
    include_files: bool = False,
    user_id: str = Query(..., description="User ID"),
    context_service=Depends(get_context_management_service),
):
    """
    Get a context entry by ID.
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
                detail="Context not found or access denied",
            )

        response = {
            "success": True,
            "context": context.to_dict(include_content=include_content),
            "message": "Context retrieved successfully",
        }

        if include_files:
            files = await context_service.list_context_files(
                context_id=context_id,
                user_id=user_id,
            )
            response["files"] = [file.to_dict() for file in files]

        return response

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to get context %s: %s", context_id, exc)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get context: {str(exc)}",
        )


@router.put("/contexts/{context_id}", response_model=Dict[str, Any])
async def update_context(
    context_id: str,
    title: Optional[str] = None,
    content: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    tags: Optional[list[str]] = None,
    importance_score: Optional[float] = None,
    create_version: bool = True,
    change_summary: Optional[str] = None,
    user_id: str = Query(..., description="User ID"),
    context_service=Depends(get_context_management_service),
    preprocessor=Depends(get_context_preprocessor),
):
    """
    Update a context entry.
    """
    try:
        if importance_score is not None and not 1.0 <= importance_score <= 10.0:
            raise HTTPException(
                status_code=400,
                detail="Importance score must be between 1.0 and 10.0",
            )

        normalized_title = title.strip() if isinstance(title, str) else title
        if normalized_title is not None and not normalized_title:
            raise HTTPException(
                status_code=400,
                detail="Title cannot be empty",
            )

        context = await context_service.update_context(
            context_id=context_id,
            user_id=user_id,
            title=normalized_title,
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
                detail="Context not found or access denied",
            )

        context = await preprocessor.preprocess_context(context)

        return {
            "success": True,
            "context": context.to_dict(),
            "message": "Context updated successfully",
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to update context %s: %s", context_id, exc)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update context: {str(exc)}",
        )


@router.delete("/contexts/{context_id}", response_model=Dict[str, Any])
async def delete_context(
    context_id: str,
    permanent: bool = False,
    user_id: str = Query(..., description="User ID"),
    context_service=Depends(get_context_management_service),
):
    """
    Delete a context entry.
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
                detail="Context not found or access denied",
            )

        return {
            "success": True,
            "message": f"Context {'permanently deleted' if permanent else 'soft deleted'} successfully",
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to delete context %s: %s", context_id, exc)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete context: {str(exc)}",
        )


# ---------------------------------------------------------------------------
# Context Search and Querying
# ---------------------------------------------------------------------------

@router.post("/contexts/search", response_model=Dict[str, Any])
async def search_contexts(
    query: ContextQuery,
    user_id: str = Query(..., description="User ID"),
    context_service=Depends(get_context_management_service),
):
    """
    Search for contexts based on query parameters.
    """
    try:
        if query.top_k <= 0 or query.top_k > 100:
            raise HTTPException(
                status_code=400,
                detail="top_k must be between 1 and 100",
            )

        if not 0.0 <= query.similarity_threshold <= 1.0:
            raise HTTPException(
                status_code=400,
                detail="similarity_threshold must be between 0.0 and 1.0",
            )

        results = await context_service.search_contexts(
            query=query,
            user_id=user_id,
        )

        return {
            "success": True,
            "results": [result.to_dict() for result in results],
            "total_results": len(results),
            "query": query.to_dict(),
            "message": "Search completed successfully",
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to search contexts: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search contexts: {str(exc)}",
        )


# ---------------------------------------------------------------------------
# File Upload Operations
# ---------------------------------------------------------------------------

@router.post("/contexts/{context_id}/files", response_model=Dict[str, Any])
async def upload_file(
    context_id: str,
    file: UploadFile = File(...),
    metadata: Optional[Dict[str, Any]] = None,
    user_id: str = Query(..., description="User ID"),
    file_handler=Depends(get_file_upload_handler),
    context_service=Depends(get_context_management_service),
):
    """
    Upload a file to a context.
    """
    try:
        context = await context_service.get_context(
            context_id=context_id,
            user_id=user_id,
            include_content=False,
        )

        if not context:
            raise HTTPException(
                status_code=404,
                detail="Context not found or access denied",
            )

        if file is None:
            raise HTTPException(
                status_code=400,
                detail="File is required",
            )

        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file must have a filename",
            )

        file_data = await file.read()
        if not file_data:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty",
            )

        context_file, handler_message = await file_handler.handle_upload(
            file_data=file_data,
            filename=file.filename,
            context_id=context_id,
            user_id=user_id,
            mime_type=file.content_type,
            metadata=metadata,
        )

        if context_file is None:
            raise HTTPException(
                status_code=400,
                detail=f"File upload failed: {handler_message or 'unknown error'}",
            )

        await context_service.add_file_reference(context_id, context_file.file_id)

        return {
            "success": True,
            "file": context_file.to_dict(),
            "message": handler_message or "File uploaded successfully",
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to upload file: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload file: {str(exc)}",
        )


@router.get("/files/{file_id}", response_model=Dict[str, Any])
async def get_file(
    file_id: str,
    user_id: str = Query(..., description="User ID"),
    file_handler=Depends(get_file_upload_handler),
):
    """
    Get file information by ID.
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
                detail="File not found or access denied",
            )

        return {
            "success": True,
            "file": context_file.to_dict(),
            "message": "File retrieved successfully",
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to get file %s: %s", file_id, exc)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get file: {str(exc)}",
        )


@router.delete("/files/{file_id}", response_model=Dict[str, Any])
async def delete_file(
    file_id: str,
    permanent: bool = False,
    user_id: str = Query(..., description="User ID"),
    file_handler=Depends(get_file_upload_handler),
    context_service=Depends(get_context_management_service),
):
    """
    Delete a file.
    """
    try:
        existing_file = await file_handler.get_file(
            file_id=file_id,
            user_id=user_id,
            check_access=True,
        )
        if not existing_file:
            raise HTTPException(
                status_code=404,
                detail="File not found or access denied",
            )

        success = await file_handler.delete_file(
            file_id=file_id,
            user_id=user_id,
            permanent=permanent,
        )

        if not success:
            raise HTTPException(
                status_code=404,
                detail="File not found or access denied",
            )

        await context_service.remove_file_reference(existing_file.context_id, file_id)

        return {
            "success": True,
            "message": f"File {'permanently deleted' if permanent else 'soft deleted'} successfully",
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to delete file %s: %s", file_id, exc)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete file: {str(exc)}",
        )


# ---------------------------------------------------------------------------
# Context Sharing Operations
# ---------------------------------------------------------------------------

@router.post("/contexts/{context_id}/share", response_model=Dict[str, Any])
async def share_context(
    context_id: str,
    shared_with: Optional[str] = None,
    access_level: ContextAccessLevel = ContextAccessLevel.SHARED,
    permissions: Optional[list[str]] = None,
    expires_in_days: Optional[int] = None,
    user_id: str = Query(..., description="User ID"),
    context_service=Depends(get_context_management_service),
):
    """
    Share a context with another user or group.
    """
    try:
        context = await context_service.get_context(
            context_id=context_id,
            user_id=user_id,
            include_content=False,
        )

        if not context:
            raise HTTPException(
                status_code=404,
                detail="Context not found or access denied",
            )

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
                detail="Failed to create share",
            )

        return {
            "success": True,
            "share": share.to_dict(),
            "message": "Context shared successfully",
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to share context %s: %s", context_id, exc)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to share context: {str(exc)}",
        )


# ---------------------------------------------------------------------------
# Context Versioning Operations
# ---------------------------------------------------------------------------

@router.get("/contexts/{context_id}/versions", response_model=Dict[str, Any])
async def get_context_versions(
    context_id: str,
    user_id: str = Query(..., description="User ID"),
    context_service=Depends(get_context_management_service),
):
    """
    Get all versions of a context.
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
            "message": "Versions retrieved successfully",
        }

    except Exception as exc:
        logger.error("Failed to get versions for context %s: %s", context_id, exc)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get versions: {str(exc)}",
        )


# ---------------------------------------------------------------------------
# Statistics and Analytics
# ---------------------------------------------------------------------------

@router.get("/contexts/stats", response_model=Dict[str, Any])
async def get_context_stats(
    user_id: str = Query(..., description="User ID"),
    org_id: Optional[str] = None,
    context_service=Depends(get_context_management_service),
):
    """
    Get context statistics for a user or organization.
    """
    try:
        stats = await context_service.get_context_stats(
            user_id=user_id,
            org_id=org_id,
        )

        return {
            "success": True,
            "stats": stats,
            "message": "Statistics retrieved successfully",
        }

    except Exception as exc:
        logger.error("Failed to get context stats for user %s: %s", user_id, exc)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get statistics: {str(exc)}",
        )


# ---------------------------------------------------------------------------
# Utility Endpoints
# ---------------------------------------------------------------------------

@router.get("/file-types", response_model=Dict[str, Any])
async def get_supported_file_types(
    file_handler=Depends(get_file_upload_handler),
):
    """
    Get list of supported file types.
    """
    try:
        file_types = file_handler.get_supported_file_types()

        return {
            "success": True,
            "file_types": file_types,
            "message": "File types retrieved successfully",
        }

    except Exception as exc:
        logger.error("Failed to get supported file types: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get file types: {str(exc)}",
        )


@router.get("/context-types", response_model=Dict[str, Any])
async def get_context_types():
    """
    Get list of available context types.
    """
    try:
        context_types = [
            {
                "value": ctx_type.value,
                "name": ctx_type.name,
                "description": _get_context_type_description(ctx_type),
            }
            for ctx_type in ContextType
        ]

        return {
            "success": True,
            "context_types": context_types,
            "message": "Context types retrieved successfully",
        }

    except Exception as exc:
        logger.error("Failed to get context types: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get context types: {str(exc)}",
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