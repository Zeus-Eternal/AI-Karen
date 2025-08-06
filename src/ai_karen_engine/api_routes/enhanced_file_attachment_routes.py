"""
Enhanced FastAPI routes for file attachment with AG-UI and hook integration.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from ai_karen_engine.chat.file_attachment_service import (
    FileType,
    FileUploadRequest,
    FileUploadResponse,
    ProcessingStatus,
)
from ai_karen_engine.chat.hook_enabled_file_service import get_hook_enabled_file_service
from ai_karen_engine.chat.multimedia_service import (
    MediaProcessingRequest,
    MediaProcessingResponse,
    MediaType,
    MultimediaService,
    ProcessingCapability,
)
from ai_karen_engine.core.logging import get_logger
from ai_karen_engine.models.web_api_error_responses import (
    WebAPIErrorCode,
    create_service_error_response,
    create_validation_error_response,
    get_http_status_for_error_code,
)
from ai_karen_engine.utils.dependency_checks import import_fastapi, import_pydantic

APIRouter, File, Form, HTTPException, Query, UploadFile, responses = import_fastapi(
    "APIRouter", "File", "Form", "HTTPException", "Query", "UploadFile", "responses"
)
JSONResponse = responses.JSONResponse
BaseModel, Field = import_pydantic("BaseModel", "Field")

logger = get_logger(__name__)

router = APIRouter(tags=["enhanced-file-attachments"])

# Initialize enhanced services
file_service = get_hook_enabled_file_service()
multimedia_service = MultimediaService()


# Enhanced Request/Response Models
class EnhancedFileUploadMetadata(BaseModel):
    """Enhanced metadata for file upload with AG-UI support."""

    conversation_id: str = Field(..., description="Conversation ID")
    user_id: str = Field(..., description="User ID")
    description: Optional[str] = Field(None, description="File description")
    tags: List[str] = Field(default_factory=list, description="File tags")
    enable_hooks: bool = Field(True, description="Enable hook processing")
    processing_options: Dict[str, Any] = Field(
        default_factory=dict, description="Processing options"
    )
    ui_context: Optional[Dict[str, Any]] = Field(
        None, description="UI context for AG-UI integration"
    )


class EnhancedFileListResponse(BaseModel):
    """Enhanced response for file listing with AG-UI grid data."""

    files: List[Dict[str, Any]] = Field(
        ..., description="List of files with enhanced metadata"
    )
    total_count: int = Field(..., description="Total number of files")
    has_more: bool = Field(..., description="Whether there are more files")
    grid_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="AG-Grid metadata"
    )
    statistics: Dict[str, Any] = Field(
        default_factory=dict, description="File statistics"
    )


class FileAnalysisResponse(BaseModel):
    """Response for comprehensive file analysis."""

    file_id: str = Field(..., description="File identifier")
    analysis_complete: bool = Field(..., description="Whether analysis is complete")
    hook_results: Dict[str, Any] = Field(
        default_factory=dict, description="Hook execution results"
    )
    multimedia_analysis: Optional[Dict[str, Any]] = Field(
        None, description="Multimedia analysis results"
    )
    security_analysis: Optional[Dict[str, Any]] = Field(
        None, description="Security analysis results"
    )
    plugin_results: Dict[str, Any] = Field(
        default_factory=dict, description="Plugin processing results"
    )
    extension_results: Dict[str, Any] = Field(
        default_factory=dict, description="Extension processing results"
    )


class MultimediaProcessingRequest(BaseModel):
    """Enhanced request for multimedia processing."""

    capabilities: List[ProcessingCapability] = Field(
        ..., description="Requested processing capabilities"
    )
    options: Dict[str, Any] = Field(
        default_factory=dict, description="Processing options"
    )
    priority: int = Field(1, ge=1, le=5, description="Processing priority")
    enable_hooks: bool = Field(True, description="Enable hook processing")
    ui_integration: bool = Field(True, description="Enable UI integration features")


@router.post("/upload", response_model=FileUploadResponse)
async def enhanced_upload_file(
    file: UploadFile = File(...),
    metadata: str = Form(...),  # JSON string of EnhancedFileUploadMetadata
):
    """Enhanced file upload with hook integration and AG-UI support."""
    try:
        # Parse enhanced metadata
        try:
            metadata_dict = json.loads(metadata)
            file_metadata = EnhancedFileUploadMetadata(**metadata_dict)
        except (json.JSONDecodeError, ValueError) as e:
            error_response = create_validation_error_response(
                field="metadata",
                message="Invalid enhanced metadata format",
                details={"error": str(e)},
            )
            raise HTTPException(
                status_code=get_http_status_for_error_code(
                    WebAPIErrorCode.VALIDATION_ERROR
                ),
                detail=error_response.dict(),
            )

        # Read file content
        file_content = await file.read()

        # Create enhanced upload request
        upload_request = FileUploadRequest(
            conversation_id=file_metadata.conversation_id,
            user_id=file_metadata.user_id,
            filename=file.filename or "unknown",
            content_type=file.content_type or "application/octet-stream",
            file_size=len(file_content),
            description=file_metadata.description,
            metadata={
                "tags": file_metadata.tags,
                "enable_hooks": file_metadata.enable_hooks,
                "processing_options": file_metadata.processing_options,
                "ui_context": file_metadata.ui_context or {},
            },
        )

        # Upload file with hook integration
        result = await file_service.upload_file(upload_request, file_content)

        if not result.success:
            error_response = create_service_error_response(
                service_name="enhanced_file_attachment",
                error=Exception(result.message),
                error_code=WebAPIErrorCode.INTERNAL_SERVER_ERROR,
                user_message=result.message,
            )
            raise HTTPException(
                status_code=get_http_status_for_error_code(
                    WebAPIErrorCode.INTERNAL_SERVER_ERROR
                ),
                detail=error_response.dict(),
            )

        # Enhance response with UI metadata
        enhanced_result = result.dict()
        enhanced_result["ui_metadata"] = {
            "grid_row_data": {
                "file_id": result.file_id,
                "filename": result.metadata.filename,
                "file_size": result.metadata.file_size,
                "mime_type": result.metadata.mime_type,
                "file_type": result.metadata.file_type.value,
                "processing_status": result.metadata.processing_status.value,
                "upload_timestamp": result.metadata.upload_timestamp.isoformat(),
                "has_thumbnail": result.metadata.thumbnail_path is not None,
                "preview_available": result.metadata.preview_available,
                "extracted_content_available": result.metadata.extracted_content
                is not None,
                "tags": file_metadata.tags,
                "security_scan_result": result.metadata.security_scan_result.value
                if result.metadata.security_scan_result
                else None,
            },
            "chart_data": {
                "upload_time": datetime.utcnow().isoformat(),
                "file_size_mb": round(result.metadata.file_size / (1024 * 1024), 2),
                "file_type": result.metadata.file_type.value,
            },
        }

        return JSONResponse(content=enhanced_result)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Enhanced file upload failed", error=str(e))
        error_response = create_service_error_response(
            service_name="enhanced_file_attachment",
            error=e,
            error_code=WebAPIErrorCode.INTERNAL_SERVER_ERROR,
            user_message="Enhanced file upload failed. Please try again.",
        )
        raise HTTPException(
            status_code=get_http_status_for_error_code(
                WebAPIErrorCode.INTERNAL_SERVER_ERROR
            ),
            detail=error_response.dict(),
        )


@router.get("/", response_model=EnhancedFileListResponse)
async def enhanced_list_files(
    conversation_id: Optional[str] = Query(
        None, description="Filter by conversation ID"
    ),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    file_type: Optional[FileType] = Query(None, description="Filter by file type"),
    processing_status: Optional[ProcessingStatus] = Query(
        None, description="Filter by processing status"
    ),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    security_status: Optional[str] = Query(
        None, description="Filter by security status"
    ),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of files"),
    offset: int = Query(0, ge=0, description="Number of files to skip"),
    include_analysis: bool = Query(False, description="Include analysis results"),
    ag_grid_format: bool = Query(True, description="Format for AG-Grid compatibility"),
):
    """Enhanced file listing with AG-UI grid support and comprehensive metadata."""
    try:
        # Get all files from service
        all_files = []

        for file_id, metadata in file_service._file_metadata.items():
            # Apply filters
            if file_type and metadata.file_type != file_type:
                continue
            if processing_status and metadata.processing_status != processing_status:
                continue
            if security_status and (
                not metadata.security_scan_result
                or metadata.security_scan_result.value != security_status
            ):
                continue

            # Tag filtering
            if tags:
                requested_tags = [tag.strip() for tag in tags.split(",")]
                file_tags = metadata.analysis_results.get("tags", [])
                if not any(tag in file_tags for tag in requested_tags):
                    continue

            # Build enhanced file info
            file_info = {
                "file_id": file_id,
                "filename": metadata.original_filename,
                "file_size": metadata.file_size,
                "mime_type": metadata.mime_type,
                "file_type": metadata.file_type.value,
                "processing_status": metadata.processing_status.value,
                "upload_timestamp": metadata.upload_timestamp.isoformat(),
                "has_thumbnail": metadata.thumbnail_path is not None,
                "preview_available": metadata.preview_available,
                "extracted_content_available": metadata.extracted_content is not None,
                "security_scan_result": metadata.security_scan_result.value
                if metadata.security_scan_result
                else None,
                "tags": metadata.analysis_results.get("tags", []),
            }

            # Add analysis results if requested
            if include_analysis:
                file_info["analysis_results"] = metadata.analysis_results
                file_info["extracted_content"] = metadata.extracted_content

            # AG-Grid specific formatting
            if ag_grid_format:
                file_info["ag_grid_metadata"] = {
                    "rowId": file_id,
                    "selectable": True,
                    "draggable": False,
                    "cssClass": _get_file_css_class(metadata),
                    "tooltip": f"{metadata.original_filename} ({metadata.file_type.value})",
                }

            all_files.append(file_info)

        # Sort by upload timestamp (newest first)
        all_files.sort(key=lambda x: x["upload_timestamp"], reverse=True)

        # Apply pagination
        paginated_files = all_files[offset : offset + limit]

        # Calculate statistics
        statistics = _calculate_file_statistics(all_files)

        # AG-Grid metadata
        grid_metadata = (
            {
                "columnDefs": _get_ag_grid_column_definitions(),
                "defaultColDef": {
                    "sortable": True,
                    "filter": True,
                    "resizable": True,
                    "floatingFilter": True,
                },
                "rowSelection": "multiple",
                "animateRows": True,
                "enableCellTextSelection": True,
            }
            if ag_grid_format
            else {}
        )

        return EnhancedFileListResponse(
            files=paginated_files,
            total_count=len(all_files),
            has_more=len(all_files) > offset + limit,
            grid_metadata=grid_metadata,
            statistics=statistics,
        )

    except Exception as e:
        logger.exception("Enhanced file listing failed", error=str(e))
        error_response = create_service_error_response(
            service_name="enhanced_file_attachment",
            error=e,
            error_code=WebAPIErrorCode.INTERNAL_SERVER_ERROR,
            user_message="Enhanced file listing failed. Please try again.",
        )
        raise HTTPException(
            status_code=get_http_status_for_error_code(
                WebAPIErrorCode.INTERNAL_SERVER_ERROR
            ),
            detail=error_response.dict(),
        )


@router.get("/{file_id}/analysis", response_model=FileAnalysisResponse)
async def get_file_analysis(file_id: str):
    """Get comprehensive file analysis including hook and plugin results."""
    try:
        analysis = await file_service.get_file_analysis(file_id)

        if not analysis:
            error_response = create_service_error_response(
                service_name="enhanced_file_attachment",
                error=Exception("File not found"),
                error_code=WebAPIErrorCode.NOT_FOUND,
                user_message="The requested file could not be found.",
            )
            raise HTTPException(
                status_code=get_http_status_for_error_code(WebAPIErrorCode.NOT_FOUND),
                detail=error_response.dict(),
            )

        # Extract specific analysis components
        hook_results = analysis.get("hook_results", {})
        multimedia_analysis = hook_results.get("multimedia_analysis")
        security_analysis = hook_results.get("security_analysis")
        plugin_results = hook_results.get("plugin_processing", {})
        extension_results = hook_results.get("extension_processing", {})

        return FileAnalysisResponse(
            file_id=file_id,
            analysis_complete=analysis.get("processing_complete", False),
            hook_results=hook_results,
            multimedia_analysis=multimedia_analysis,
            security_analysis=security_analysis,
            plugin_results=plugin_results,
            extension_results=extension_results,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get file analysis", error=str(e))
        error_response = create_service_error_response(
            service_name="enhanced_file_attachment",
            error=e,
            error_code=WebAPIErrorCode.INTERNAL_SERVER_ERROR,
            user_message="Failed to get file analysis. Please try again.",
        )
        raise HTTPException(
            status_code=get_http_status_for_error_code(
                WebAPIErrorCode.INTERNAL_SERVER_ERROR
            ),
            detail=error_response.dict(),
        )


@router.post("/{file_id}/process", response_model=MediaProcessingResponse)
async def enhanced_process_multimedia(
    file_id: str, request: MultimediaProcessingRequest
):
    """Enhanced multimedia processing with hook integration."""
    try:
        # Get file info
        file_info = await file_service.get_file_info(file_id)
        if not file_info:
            error_response = create_service_error_response(
                service_name="enhanced_multimedia",
                error=Exception("File not found"),
                error_code=WebAPIErrorCode.NOT_FOUND,
                user_message="The requested file could not be found.",
            )
            raise HTTPException(
                status_code=get_http_status_for_error_code(WebAPIErrorCode.NOT_FOUND),
                detail=error_response.dict(),
            )

        # Get file metadata to determine media type
        metadata = file_service._file_metadata.get(file_id)
        if not metadata:
            error_response = create_service_error_response(
                service_name="enhanced_multimedia",
                error=Exception("File metadata not available"),
                error_code=WebAPIErrorCode.INTERNAL_SERVER_ERROR,
                user_message="File metadata is not available.",
            )
            raise HTTPException(
                status_code=get_http_status_for_error_code(
                    WebAPIErrorCode.INTERNAL_SERVER_ERROR
                ),
                detail=error_response.dict(),
            )

        # Determine media type
        media_type = None
        if metadata.file_type.value == "image":
            media_type = MediaType.IMAGE
        elif metadata.file_type.value == "audio":
            media_type = MediaType.AUDIO
        elif metadata.file_type.value == "video":
            media_type = MediaType.VIDEO
        else:
            error_response = create_validation_error_response(
                field="file_type",
                message="File type not supported for multimedia processing",
                details={"file_type": metadata.file_type.value},
            )
            raise HTTPException(
                status_code=get_http_status_for_error_code(
                    WebAPIErrorCode.VALIDATION_ERROR
                ),
                detail=error_response.dict(),
            )

        # Create enhanced processing request
        processing_request = MediaProcessingRequest(
            file_id=file_id,
            media_type=media_type,
            capabilities=request.capabilities,
            options={
                **request.options,
                "enable_hooks": request.enable_hooks,
                "ui_integration": request.ui_integration,
            },
            priority=request.priority,
        )

        # Get file path
        file_path = file_service.storage_path / "files" / metadata.filename

        # Process multimedia with enhanced service
        result = await multimedia_service.process_media(processing_request, file_path)

        # Enhance result with UI-specific data
        if request.ui_integration and result.status == "completed":
            # Add AG-Charts compatible data
            result.results["chart_data"] = _format_analysis_for_charts(result.results)

            # Add AG-Grid compatible metadata
            result.results["grid_data"] = _format_analysis_for_grid(result.results)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Enhanced multimedia processing failed", error=str(e))
        error_response = create_service_error_response(
            service_name="enhanced_multimedia",
            error=e,
            error_code=WebAPIErrorCode.INTERNAL_SERVER_ERROR,
            user_message="Enhanced multimedia processing failed. Please try again.",
        )
        raise HTTPException(
            status_code=get_http_status_for_error_code(
                WebAPIErrorCode.INTERNAL_SERVER_ERROR
            ),
            detail=error_response.dict(),
        )


@router.get("/statistics/dashboard")
async def get_file_statistics_dashboard():
    """Get comprehensive file statistics for AG-UI dashboard."""
    try:
        # Get storage stats
        storage_stats = file_service.get_storage_stats()

        # Calculate additional statistics
        all_files = list(file_service._file_metadata.values())

        # Processing status distribution
        status_distribution = {}
        for file_metadata in all_files:
            status = file_metadata.processing_status.value
            status_distribution[status] = status_distribution.get(status, 0) + 1

        # Security status distribution
        security_distribution = {}
        for file_metadata in all_files:
            if file_metadata.security_scan_result:
                status = file_metadata.security_scan_result.value
                security_distribution[status] = security_distribution.get(status, 0) + 1

        # Upload trends (last 30 days)
        upload_trends = _calculate_upload_trends(all_files)

        # File type analysis
        type_analysis = _calculate_type_analysis(all_files)

        return {
            "storage_stats": storage_stats,
            "processing_distribution": status_distribution,
            "security_distribution": security_distribution,
            "upload_trends": upload_trends,
            "type_analysis": type_analysis,
            "chart_data": {
                "processing_status": [
                    {"status": k, "count": v} for k, v in status_distribution.items()
                ],
                "security_status": [
                    {"status": k, "count": v} for k, v in security_distribution.items()
                ],
                "file_types": [
                    {"type": k, "count": v}
                    for k, v in storage_stats.get("files_by_type", {}).items()
                ],
            },
        }

    except Exception as e:
        logger.exception("Failed to get file statistics dashboard", error=str(e))
        error_response = create_service_error_response(
            service_name="enhanced_file_attachment",
            error=e,
            error_code=WebAPIErrorCode.INTERNAL_SERVER_ERROR,
            user_message="Failed to get file statistics. Please try again.",
        )
        raise HTTPException(
            status_code=get_http_status_for_error_code(
                WebAPIErrorCode.INTERNAL_SERVER_ERROR
            ),
            detail=error_response.dict(),
        )


# Helper functions
def _get_file_css_class(metadata) -> str:
    """Get CSS class for file based on its properties."""
    classes = []

    if metadata.security_scan_result:
        if metadata.security_scan_result.value == "malicious":
            classes.append("file-malicious")
        elif metadata.security_scan_result.value == "suspicious":
            classes.append("file-suspicious")
        else:
            classes.append("file-safe")

    if metadata.processing_status.value == "failed":
        classes.append("file-failed")
    elif metadata.processing_status.value == "processing":
        classes.append("file-processing")
    elif metadata.processing_status.value == "completed":
        classes.append("file-completed")

    return " ".join(classes)


def _get_ag_grid_column_definitions() -> List[Dict[str, Any]]:
    """Get AG-Grid column definitions for file metadata."""
    return [
        {
            "headerName": "File",
            "field": "filename",
            "flex": 2,
            "minWidth": 200,
            "cellRenderer": "fileIconRenderer",
            "filter": "agTextColumnFilter",
        },
        {
            "headerName": "Type",
            "field": "file_type",
            "width": 100,
            "filter": "agSetColumnFilter",
        },
        {
            "headerName": "Size",
            "field": "file_size",
            "width": 100,
            "filter": "agNumberColumnFilter",
            "cellRenderer": "fileSizeRenderer",
        },
        {
            "headerName": "Status",
            "field": "processing_status",
            "width": 120,
            "filter": "agSetColumnFilter",
            "cellRenderer": "statusRenderer",
        },
        {
            "headerName": "Security",
            "field": "security_scan_result",
            "width": 100,
            "filter": "agSetColumnFilter",
            "cellRenderer": "securityRenderer",
        },
        {
            "headerName": "Uploaded",
            "field": "upload_timestamp",
            "width": 150,
            "filter": "agDateColumnFilter",
            "cellRenderer": "dateRenderer",
            "sort": "desc",
        },
        {
            "headerName": "Actions",
            "field": "actions",
            "width": 80,
            "sortable": False,
            "filter": False,
            "pinned": "right",
            "cellRenderer": "actionsRenderer",
        },
    ]


def _calculate_file_statistics(files: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate comprehensive file statistics."""
    if not files:
        return {}

    total_size = sum(file["file_size"] for file in files)

    type_counts = {}
    status_counts = {}
    security_counts = {}

    for file in files:
        # Type distribution
        file_type = file["file_type"]
        type_counts[file_type] = type_counts.get(file_type, 0) + 1

        # Status distribution
        status = file["processing_status"]
        status_counts[status] = status_counts.get(status, 0) + 1

        # Security distribution
        security = file.get("security_scan_result")
        if security:
            security_counts[security] = security_counts.get(security, 0) + 1

    return {
        "total_files": len(files),
        "total_size": total_size,
        "total_size_formatted": _format_file_size(total_size),
        "type_distribution": type_counts,
        "status_distribution": status_counts,
        "security_distribution": security_counts,
        "average_file_size": total_size / len(files) if files else 0,
    }


def _format_file_size(bytes_size: int) -> str:
    """Format file size in human-readable format."""
    if bytes_size == 0:
        return "0 B"

    sizes = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while bytes_size >= 1024 and i < len(sizes) - 1:
        bytes_size /= 1024
        i += 1

    return f"{bytes_size:.2f} {sizes[i]}"


def _format_analysis_for_charts(analysis_results: Dict[str, Any]) -> Dict[str, Any]:
    """Format analysis results for AG-Charts compatibility."""
    chart_data = {}

    # Image analysis charts
    if "image_analysis" in analysis_results:
        image_analysis = analysis_results["image_analysis"]

        # Confidence scores chart
        if "confidence_scores" in image_analysis:
            chart_data["confidence_scores"] = [
                {"category": k.replace("_", " ").title(), "confidence": v * 100}
                for k, v in image_analysis["confidence_scores"].items()
            ]

        # Color distribution
        if "dominant_colors" in image_analysis:
            chart_data["color_distribution"] = [
                {"color": color, "count": 1}
                for color in image_analysis["dominant_colors"]
            ]

    # Audio analysis charts
    if "audio_analysis" in analysis_results:
        audio_analysis = analysis_results["audio_analysis"]

        # Sentiment analysis
        if "sentiment_analysis" in audio_analysis:
            sentiment = audio_analysis["sentiment_analysis"]
            chart_data["sentiment"] = [
                {
                    "sentiment": sentiment.get("overall", "neutral"),
                    "confidence": sentiment.get("confidence", 0) * 100,
                }
            ]

    return chart_data


def _format_analysis_for_grid(analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Format analysis results for AG-Grid compatibility."""
    grid_data = []

    # Extract key-value pairs from analysis
    for category, data in analysis_results.items():
        if isinstance(data, dict):
            for key, value in data.items():
                grid_data.append(
                    {
                        "category": category,
                        "property": key,
                        "value": str(value),
                        "type": type(value).__name__,
                    }
                )

    return grid_data


def _calculate_upload_trends(files: List[Any]) -> List[Dict[str, Any]]:
    """Calculate upload trends for the last 30 days."""
    from collections import defaultdict
    from datetime import datetime, timedelta

    # Group uploads by date
    daily_uploads = defaultdict(int)

    for file_metadata in files:
        upload_date = file_metadata.upload_timestamp.date()
        daily_uploads[upload_date] += 1

    # Generate trend data for last 30 days
    trends = []
    today = datetime.now().date()

    for i in range(30):
        date = today - timedelta(days=i)
        trends.append({"date": date.isoformat(), "uploads": daily_uploads.get(date, 0)})

    return list(reversed(trends))


def _calculate_type_analysis(files: List[Any]) -> Dict[str, Any]:
    """Calculate detailed file type analysis."""
    type_stats = {}

    for file_metadata in files:
        file_type = file_metadata.file_type.value

        if file_type not in type_stats:
            type_stats[file_type] = {
                "count": 0,
                "total_size": 0,
                "avg_size": 0,
                "processing_success_rate": 0,
                "security_issues": 0,
            }

        stats = type_stats[file_type]
        stats["count"] += 1
        stats["total_size"] += file_metadata.file_size

        if file_metadata.processing_status.value == "completed":
            stats["processing_success_rate"] += 1

        if (
            file_metadata.security_scan_result
            and file_metadata.security_scan_result.value in ["suspicious", "malicious"]
        ):
            stats["security_issues"] += 1

    # Calculate averages and rates
    for file_type, stats in type_stats.items():
        if stats["count"] > 0:
            stats["avg_size"] = stats["total_size"] / stats["count"]
            stats["processing_success_rate"] = (
                stats["processing_success_rate"] / stats["count"]
            ) * 100

    return type_stats
