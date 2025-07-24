"""
Web UI compatibility router for API endpoint mapping.

This router provides compatibility endpoints that map web UI API calls
to the correct backend services with proper request/response transformation.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from ..models.web_ui_types import (
    ChatProcessRequest,
    ChatProcessResponse,
    WebUIMemoryQuery,
    WebUIMemoryQueryResponse,
    WebUIMemoryStoreRequest,
    WebUIMemoryStoreResponse,
    WebUIPluginExecuteRequest,
    WebUIPluginExecuteResponse,
    WebUISystemMetrics,
    WebUIUsageAnalytics,
    WebUIHealthCheck
)
from ..models.web_api_error_responses import (
    WebAPIErrorCode,
    WebAPIErrorResponse,
    ValidationErrorDetail,
    create_validation_error_response,
    create_database_error_response,
    create_service_error_response,
    create_generic_error_response,
    get_http_status_for_error_code
)
from ..database.schema_validator import validate_and_migrate_schema
from ..services.web_ui_compatibility import WebUITransformationService
from ..services.ai_orchestrator import AIOrchestrator
from ..services.memory_service import WebUIMemoryService
from ..core.dependencies import (
    get_ai_orchestrator_service,
    get_memory_service,
    get_plugin_service
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["web-ui-compatibility"])


def get_request_id(request: Request) -> str:
    """Get or generate request ID for tracking."""
    return getattr(request.state, 'trace_id', str(uuid.uuid4()))


def handle_service_error(
    error: Exception,
    error_code: WebAPIErrorCode,
    user_message: str,
    request_id: str,
    additional_details: Optional[Dict[str, Any]] = None
) -> HTTPException:
    """Handle service errors and return appropriate HTTP exception using new WebAPI error models."""
    logger.error(f"[{request_id}] Service error: {error}", exc_info=True)
    
    # Create service error response using the new models
    error_response = create_service_error_response(
        service_name="web_api",
        error=error,
        error_code=error_code,
        user_message=user_message,
        request_id=request_id
    )
    
    # Add additional details if provided
    if additional_details:
        if error_response.details:
            error_response.details.update(additional_details)
        else:
            error_response.details = additional_details
    
    # Get appropriate HTTP status code
    status_code = get_http_status_for_error_code(error_code)
    
    return HTTPException(
        status_code=status_code,
        detail=error_response.dict()
    )


def create_fallback_chat_response(
    request_id: str,
    fallback_message: str = "I'm having trouble processing your message right now. Please try again in a moment."
) -> ChatProcessResponse:
    """Create a fallback chat response when processing fails."""
    logger.info(f"[{request_id}] Creating fallback chat response")
    
    return ChatProcessResponse(
        finalResponse=fallback_message,
        acknowledgement="Message received",
        ai_data_for_final_response=None,
        suggested_new_facts=None,
        proactive_suggestion="You might want to try rephrasing your question or check back in a few minutes.",
        summary_was_generated=False
    )


@router.post("/chat/process", response_model=ChatProcessResponse)
async def chat_process_compatibility(
    request: ChatProcessRequest,
    http_request: Request,
    ai_orchestrator: AIOrchestrator = Depends(get_ai_orchestrator_service)
):
    """
    Compatibility endpoint that maps /api/chat/process to /api/ai/conversation-processing.
    
    This endpoint accepts the web UI chat format and transforms it to work with
    the backend AI orchestrator service.
    """
    request_id = get_request_id(http_request)
    
    try:
        logger.info(f"[{request_id}] Processing chat request for user: {request.user_id}")
        
        # Enhanced request validation
        validation_errors = []
        
        # Validate message content
        if not request.message or not request.message.strip():
            validation_errors.append({
                "field": "message",
                "message": "Message cannot be empty or contain only whitespace",
                "invalid_value": request.message
            })
        
        # Validate message length (prevent extremely long messages)
        if request.message and len(request.message) > 10000:
            validation_errors.append({
                "field": "message",
                "message": "Message is too long (maximum 10,000 characters)",
                "invalid_value": f"Length: {len(request.message)}"
            })
        
        # Validate conversation history format
        if request.conversation_history:
            for i, msg in enumerate(request.conversation_history):
                if not isinstance(msg, dict):
                    validation_errors.append({
                        "field": f"conversation_history[{i}]",
                        "message": "Conversation history entries must be objects",
                        "invalid_value": type(msg).__name__
                    })
                elif "role" not in msg or "content" not in msg:
                    validation_errors.append({
                        "field": f"conversation_history[{i}]",
                        "message": "Conversation history entries must have 'role' and 'content' fields",
                        "invalid_value": list(msg.keys()) if isinstance(msg, dict) else str(msg)
                    })
        
        # Validate user settings format
        if request.user_settings and not isinstance(request.user_settings, dict):
            validation_errors.append({
                "field": "user_settings",
                "message": "User settings must be an object",
                "invalid_value": type(request.user_settings).__name__
            })
        
        # If validation errors exist, return them
        if validation_errors:
            logger.warning(f"[{request_id}] Request validation failed: {validation_errors}")
            raise HTTPException(
                status_code=400,
                detail=create_web_ui_error_response(
                    WebUIErrorCode.VALIDATION_ERROR,
                    "Request validation failed",
                    {"validation_errors": validation_errors},
                    user_message="Please check your request format and try again.",
                    request_id=request_id
                ).dict()
            )
        
        # Transform request to backend format with error handling
        try:
            backend_request, flow_input = WebUITransformationService.transform_chat_request_to_backend(request)
        except Exception as e:
            logger.error(f"[{request_id}] Request transformation failed: {e}")
            raise HTTPException(
                status_code=400,
                detail=create_web_ui_error_response(
                    WebUIErrorCode.VALIDATION_ERROR,
                    f"Request transformation failed: {str(e)}",
                    {"transformation_error": str(e)},
                    user_message="Invalid request format. Please check your data and try again.",
                    request_id=request_id
                ).dict()
            )
        
        # Call AI orchestrator service with timeout and retry logic
        start_time = datetime.utcnow()
        max_retries = 2
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                # Add timeout to prevent hanging requests
                import asyncio
                result = await asyncio.wait_for(
                    ai_orchestrator.conversation_processing_flow(flow_input),
                    timeout=30.0  # 30 second timeout
                )
                break
                
            except asyncio.TimeoutError:
                logger.warning(f"[{request_id}] Chat processing timeout (attempt {retry_count + 1})")
                if retry_count >= max_retries:
                    raise HTTPException(
                        status_code=504,
                        detail=create_web_ui_error_response(
                            WebUIErrorCode.SERVICE_UNAVAILABLE,
                            "Chat processing timed out",
                            {"timeout_seconds": 30, "retry_count": retry_count},
                            user_message="The AI is taking too long to respond. Please try again with a shorter message.",
                            request_id=request_id
                        ).dict()
                    )
                retry_count += 1
                await asyncio.sleep(1)  # Brief delay before retry
                
            except ConnectionError as e:
                logger.error(f"[{request_id}] AI orchestrator connection error (attempt {retry_count + 1}): {e}")
                if retry_count >= max_retries:
                    raise HTTPException(
                        status_code=503,
                        detail=create_web_ui_error_response(
                            WebUIErrorCode.SERVICE_UNAVAILABLE,
                            "AI service is temporarily unavailable",
                            {"connection_error": str(e), "retry_count": retry_count},
                            user_message="I'm having trouble connecting to my AI services. Please try again in a moment.",
                            request_id=request_id
                        ).dict()
                    )
                retry_count += 1
                await asyncio.sleep(2)  # Longer delay for connection issues
                
            except Exception as e:
                # Check if it's a known service error
                error_str = str(e).lower()
                if "rate limit" in error_str or "quota" in error_str:
                    logger.warning(f"[{request_id}] Rate limit exceeded: {e}")
                    raise HTTPException(
                        status_code=429,
                        detail=create_web_ui_error_response(
                            WebUIErrorCode.SERVICE_UNAVAILABLE,
                            "Rate limit exceeded",
                            {"rate_limit_error": str(e)},
                            user_message="I'm receiving too many requests right now. Please wait a moment and try again.",
                            request_id=request_id
                        ).dict()
                    )
                elif "authentication" in error_str or "unauthorized" in error_str:
                    logger.error(f"[{request_id}] Authentication error: {e}")
                    raise HTTPException(
                        status_code=401,
                        detail=create_web_ui_error_response(
                            WebUIErrorCode.AUTHENTICATION_ERROR,
                            "Authentication failed",
                            {"auth_error": str(e)},
                            user_message="Authentication failed. Please refresh the page and try again.",
                            request_id=request_id
                        ).dict()
                    )
                else:
                    # Unknown error, don't retry
                    logger.error(f"[{request_id}] AI orchestrator error: {e}")
                    raise
        
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.info(f"[{request_id}] Chat processing completed in {processing_time:.2f}ms")
        
        # Transform response to web UI format with error handling
        try:
            response = WebUITransformationService.transform_backend_response_to_chat(result)
        except Exception as e:
            logger.error(f"[{request_id}] Response transformation failed: {e}")
            # Return a fallback response instead of failing completely
            response = ChatProcessResponse(
                finalResponse="I processed your message but had trouble formatting the response. Please try again.",
                acknowledgement="Message received",
                ai_data_for_final_response=None,
                suggested_new_facts=None,
                proactive_suggestion=None,
                summary_was_generated=False
            )
        
        # Validate response before returning
        if not response.finalResponse or not response.finalResponse.strip():
            logger.warning(f"[{request_id}] Empty response generated, providing fallback")
            response.finalResponse = "I received your message but couldn't generate a proper response. Please try rephrasing your question."
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions (these are already properly formatted)
        raise
        
    except ValidationError as e:
        logger.warning(f"[{request_id}] Pydantic validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail=create_validation_error_response(e.errors(), request_id).dict()
        )
        
    except ValueError as e:
        logger.error(f"[{request_id}] Value error in chat processing: {e}")
        raise HTTPException(
            status_code=400,
            detail=create_web_ui_error_response(
                WebUIErrorCode.VALIDATION_ERROR,
                str(e),
                {"value_error": str(e)},
                user_message="Invalid request format. Please check your data and try again.",
                request_id=request_id
            ).dict()
        )
        
    except Exception as e:
        logger.error(f"[{request_id}] Unexpected error in chat processing: {e}", exc_info=True)
        # Provide a user-friendly fallback response
        raise HTTPException(
            status_code=500,
            detail=create_web_ui_error_response(
                WebUIErrorCode.CHAT_PROCESSING_ERROR,
                str(e),
                {"error_type": type(e).__name__},
                user_message="I'm having trouble processing your message right now. Please try again in a moment.",
                request_id=request_id
            ).dict()
        )


@router.post("/memory/query", response_model=WebUIMemoryQueryResponse)
async def memory_query_compatibility(
    request: WebUIMemoryQuery,
    http_request: Request,
    memory_service: WebUIMemoryService = Depends(get_memory_service)
):
    """
    Compatibility endpoint for memory queries with web UI format and enhanced validation.
    
    This endpoint accepts web UI memory query format, validates the request thoroughly,
    and returns results in the format expected by the frontend.
    """
    request_id = get_request_id(http_request)
    
    try:
        logger.info(f"[{request_id}] Processing memory query: {request.text[:50]}...")
        
        # Enhanced request validation using transformation service
        validation_errors = WebUITransformationService.validate_memory_query_request(request)
        if validation_errors:
            logger.warning(f"[{request_id}] Memory query validation failed: {validation_errors}")
            raise HTTPException(
                status_code=400,
                detail=create_web_ui_error_response(
                    WebUIErrorCode.VALIDATION_ERROR,
                    "Memory query validation failed",
                    {"validation_errors": [{"field": "general", "message": error, "invalid_value": None} for error in validation_errors]},
                    user_message="Please check your query parameters and try again.",
                    request_id=request_id
                ).dict()
            )
        
        # Additional business logic validation
        if request.text and len(request.text.strip()) < 2:
            logger.warning(f"[{request_id}] Query text too short: '{request.text}'")
            raise HTTPException(
                status_code=400,
                detail=create_web_ui_error_response(
                    WebUIErrorCode.VALIDATION_ERROR,
                    "Query text too short",
                    {"field": "text", "min_length": 2, "actual_length": len(request.text.strip())},
                    user_message="Please provide a query with at least 2 characters.",
                    request_id=request_id
                ).dict()
            )
        
        # Transform request to backend format with enhanced error handling
        try:
            backend_request = WebUITransformationService.transform_web_ui_memory_query(request)
        except ValueError as e:
            logger.error(f"[{request_id}] Memory query transformation failed: {e}")
            raise HTTPException(
                status_code=400,
                detail=create_web_ui_error_response(
                    WebUIErrorCode.VALIDATION_ERROR,
                    f"Query transformation failed: {str(e)}",
                    {"transformation_error": str(e)},
                    user_message="Invalid query format. Please check your parameters and try again.",
                    request_id=request_id
                ).dict()
            )
        
        # Query memories with timeout and retry logic
        start_time = datetime.utcnow()
        max_retries = 2
        retry_count = 0
        memories = []
        
        while retry_count <= max_retries:
            try:
                # Add timeout to prevent hanging requests
                import asyncio
                memories = await asyncio.wait_for(
                    memory_service.query_memories("default", backend_request),
                    timeout=15.0  # 15 second timeout for memory queries
                )
                break
                
            except asyncio.TimeoutError:
                logger.warning(f"[{request_id}] Memory query timeout (attempt {retry_count + 1})")
                if retry_count >= max_retries:
                    raise HTTPException(
                        status_code=504,
                        detail=create_web_ui_error_response(
                            WebUIErrorCode.SERVICE_UNAVAILABLE,
                            "Memory query timed out",
                            {"timeout_seconds": 15, "retry_count": retry_count},
                            user_message="The memory search is taking too long. Please try a more specific query.",
                            request_id=request_id
                        ).dict()
                    )
                retry_count += 1
                await asyncio.sleep(0.5)  # Brief delay before retry
                
            except ConnectionError as e:
                logger.error(f"[{request_id}] Memory service connection error (attempt {retry_count + 1}): {e}")
                if retry_count >= max_retries:
                    raise HTTPException(
                        status_code=503,
                        detail=create_web_ui_error_response(
                            WebUIErrorCode.SERVICE_UNAVAILABLE,
                            "Memory service is temporarily unavailable",
                            {"connection_error": str(e), "retry_count": retry_count},
                            user_message="Memory search is temporarily unavailable. Please try again in a moment.",
                            request_id=request_id
                        ).dict()
                    )
                retry_count += 1
                await asyncio.sleep(1)  # Longer delay for connection issues
                
            except Exception as e:
                # Check for specific error types
                error_str = str(e).lower()
                if "index" in error_str or "vector" in error_str:
                    logger.error(f"[{request_id}] Vector search error: {e}")
                    raise HTTPException(
                        status_code=500,
                        detail=create_web_ui_error_response(
                            WebUIErrorCode.MEMORY_ERROR,
                            "Memory search index error",
                            {"search_error": str(e)},
                            user_message="There's an issue with the memory search system. Please try again later.",
                            request_id=request_id
                        ).dict()
                    )
                else:
                    # Unknown error, don't retry
                    logger.error(f"[{request_id}] Memory service error: {e}")
                    raise
        
        query_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.info(f"[{request_id}] Memory query completed in {query_time:.2f}ms, found {len(memories)} memories")
        
        # Transform response to web UI format with error handling
        try:
            response = WebUITransformationService.transform_memory_entries_to_web_ui(memories, query_time)
        except Exception as e:
            logger.error(f"[{request_id}] Memory response transformation failed: {e}")
            # Return empty response instead of failing completely
            response = WebUIMemoryQueryResponse(
                memories=[],
                total_count=0,
                query_time_ms=query_time
            )
        
        # Ensure we always return an array, even if empty
        if response.memories is None:
            response.memories = []
        
        # Log successful query for analytics
        logger.info(f"[{request_id}] Memory query successful: {len(response.memories)} results, {query_time:.2f}ms")
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions (these are already properly formatted)
        raise
        
    except ValidationError as e:
        logger.warning(f"[{request_id}] Pydantic validation error in memory query: {e}")
        raise HTTPException(
            status_code=400,
            detail=create_validation_error_response(e.errors(), request_id).dict()
        )
        
    except ValueError as e:
        logger.error(f"[{request_id}] Value error in memory query: {e}")
        raise HTTPException(
            status_code=400,
            detail=create_web_ui_error_response(
                WebUIErrorCode.VALIDATION_ERROR,
                str(e),
                {"value_error": str(e)},
                user_message="Invalid query format. Please check your parameters and try again.",
                request_id=request_id
            ).dict()
        )
        
    except Exception as e:
        logger.error(f"[{request_id}] Unexpected error in memory query: {e}", exc_info=True)
        # Provide a user-friendly fallback response
        raise HTTPException(
            status_code=500,
            detail=create_web_ui_error_response(
                WebUIErrorCode.MEMORY_ERROR,
                str(e),
                {"error_type": type(e).__name__},
                user_message="Memory search failed. Please try again with a different query.",
                request_id=request_id
            ).dict()
        )


@router.post("/memory/store", response_model=WebUIMemoryStoreResponse)
async def memory_store_compatibility(
    request: WebUIMemoryStoreRequest,
    http_request: Request,
    memory_service: WebUIMemoryService = Depends(get_memory_service)
):
    """
    Compatibility endpoint for storing memories with web UI format and database schema validation.
    """
    request_id = get_request_id(http_request)
    
    try:
        logger.info(f"[{request_id}] Storing memory for user: {request.user_id}")
        
        # Enhanced request validation
        validation_errors = []
        
        # Validate content
        if not request.content or not request.content.strip():
            validation_errors.append(ValidationErrorDetail(
                field="content",
                message="Content cannot be empty or contain only whitespace",
                invalid_value=request.content
            ))
        
        # Validate content length
        if request.content and len(request.content) > 50000:
            validation_errors.append(ValidationErrorDetail(
                field="content",
                message="Content is too long (maximum 50,000 characters)",
                invalid_value=f"Length: {len(request.content)}",
                constraint="max_length: 50000"
            ))
        
        # Validate tags format
        if request.tags:
            if not isinstance(request.tags, list):
                validation_errors.append(ValidationErrorDetail(
                    field="tags",
                    message="Tags must be an array",
                    invalid_value=type(request.tags).__name__,
                    expected_type="array"
                ))
            else:
                for i, tag in enumerate(request.tags):
                    if not isinstance(tag, str):
                        validation_errors.append(ValidationErrorDetail(
                            field=f"tags[{i}]",
                            message="Tag must be a string",
                            invalid_value=type(tag).__name__,
                            expected_type="string"
                        ))
                    elif len(tag.strip()) == 0:
                        validation_errors.append(ValidationErrorDetail(
                            field=f"tags[{i}]",
                            message="Tag cannot be empty",
                            invalid_value=tag
                        ))
        
        # If validation errors exist, return them
        if validation_errors:
            logger.warning(f"[{request_id}] Memory store validation failed: {len(validation_errors)} errors")
            error_response = create_validation_error_response(
                validation_errors,
                user_message="Please check your memory data and try again.",
                request_id=request_id
            )
            raise HTTPException(
                status_code=get_http_status_for_error_code(error_response.type),
                detail=error_response.dict()
            )
        
        # Database schema validation - check if memory_entries table exists
        try:
            from ..database.dependencies import get_postgres_session
            async with get_postgres_session() as session:
                schema_error = await validate_and_migrate_schema(session)
                if schema_error:
                    logger.error(f"[{request_id}] Database schema validation failed: {schema_error.message}")
                    raise HTTPException(
                        status_code=get_http_status_for_error_code(schema_error.type),
                        detail=schema_error.dict()
                    )
        except ImportError:
            logger.warning(f"[{request_id}] Database session dependency not available, skipping schema validation")
        except Exception as db_error:
            logger.error(f"[{request_id}] Database schema validation error: {db_error}")
            error_response = create_database_error_response(
                error=db_error,
                operation="schema_validation",
                user_message="Database validation failed. Please try again.",
                request_id=request_id
            )
            raise HTTPException(
                status_code=get_http_status_for_error_code(error_response.type),
                detail=error_response.dict()
            )
        
        # Transform request to backend format
        try:
            backend_request = WebUITransformationService.transform_web_ui_memory_store_request(request)
        except Exception as e:
            logger.error(f"[{request_id}] Memory store request transformation failed: {e}")
            error_response = create_generic_error_response(
                error_code=WebAPIErrorCode.VALIDATION_ERROR,
                message=f"Request transformation failed: {str(e)}",
                user_message="Invalid memory store request format",
                details={"transformation_error": str(e)},
                request_id=request_id
            )
            raise HTTPException(
                status_code=get_http_status_for_error_code(error_response.type),
                detail=error_response.dict()
            )
        
        # Validate user ID - store anonymously if not a valid UUID
        user_id = request.user_id
        if user_id:
            try:
                uuid.UUID(str(user_id))
            except (ValueError, AttributeError, TypeError):
                logger.warning(
                    f"[{request_id}] Invalid user ID '{user_id}' provided, storing anonymously"
                )
                user_id = None

        # Store memory with enhanced error handling
        start_time = datetime.utcnow()
        memory_id = None
        
        try:
            memory_id = await memory_service.store_web_ui_memory(
                tenant_id="default",
                content=backend_request.content,
                user_id=user_id,
                ui_source=backend_request.ui_source,
                session_id=backend_request.session_id,
                memory_type=backend_request.memory_type,
                tags=backend_request.tags,
                metadata=backend_request.metadata,
                ai_generated=backend_request.ai_generated,
            )
        except Exception as e:
            error_str = str(e).lower()
            
            # Handle specific database errors
            if "relation" in error_str and "does not exist" in error_str:
                logger.error(f"[{request_id}] Database table missing: {e}")
                error_response = create_database_error_response(
                    error=e,
                    operation="memory_store",
                    user_message="Database tables are missing. System needs initialization.",
                    request_id=request_id
                )
            elif "connection" in error_str or "connect" in error_str:
                logger.error(f"[{request_id}] Database connection error: {e}")
                error_response = create_database_error_response(
                    error=e,
                    operation="memory_store",
                    user_message="Database connection failed. Please try again later.",
                    request_id=request_id
                )
            elif "constraint" in error_str or "violation" in error_str:
                logger.error(f"[{request_id}] Database constraint violation: {e}")
                error_response = create_database_error_response(
                    error=e,
                    operation="memory_store",
                    user_message="Data validation failed. Please check your input.",
                    request_id=request_id
                )
            else:
                logger.error(f"[{request_id}] Memory service error: {e}")
                error_response = create_service_error_response(
                    service_name="memory",
                    error=e,
                    error_code=WebAPIErrorCode.MEMORY_ERROR,
                    user_message="Memory storage failed. Please try again.",
                    request_id=request_id
                )
            
            raise HTTPException(
                status_code=get_http_status_for_error_code(error_response.type),
                detail=error_response.dict()
            )
        
        storage_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Transform response to web UI format
        try:
            backend_response = {
                "success": memory_id is not None,
                "memory_id": memory_id,
                "message": "Memory stored successfully" if memory_id else "Memory not stored (not surprising enough)"
            }
            
            response = WebUITransformationService.transform_memory_store_response_to_web_ui(backend_response)
        except Exception as e:
            logger.error(f"[{request_id}] Memory store response transformation failed: {e}")
            # Create a fallback response
            response = WebUIMemoryStoreResponse(
                success=memory_id is not None,
                memory_id=memory_id,
                message="Memory stored successfully" if memory_id else "Memory not stored"
            )
        
        logger.info(f"[{request_id}] Memory storage completed: {response.success} in {storage_time:.2f}ms")
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions (these are already properly formatted)
        raise
        
    except ValidationError as e:
        logger.warning(f"[{request_id}] Pydantic validation error in memory store: {e}")
        validation_details = [
            ValidationErrorDetail(
                field=error.get("loc", ["unknown"])[-1],
                message=error.get("msg", "Validation failed"),
                invalid_value=error.get("input"),
                expected_type=error.get("type")
            )
            for error in e.errors()
        ]
        error_response = create_validation_error_response(
            validation_details,
            user_message="Request validation failed. Please check your data format.",
            request_id=request_id
        )
        raise HTTPException(
            status_code=get_http_status_for_error_code(error_response.type),
            detail=error_response.dict()
        )
        
    except ValueError as e:
        logger.error(f"[{request_id}] Value error in memory store: {e}")
        error_response = create_generic_error_response(
            error_code=WebAPIErrorCode.VALIDATION_ERROR,
            message=str(e),
            user_message="Invalid memory store request format",
            details={"value_error": str(e)},
            request_id=request_id
        )
        raise HTTPException(
            status_code=get_http_status_for_error_code(error_response.type),
            detail=error_response.dict()
        )
        
    except Exception as e:
        logger.error(f"[{request_id}] Unexpected error in memory store: {e}", exc_info=True)
        error_response = create_service_error_response(
            service_name="memory",
            error=e,
            error_code=WebAPIErrorCode.MEMORY_ERROR,
            user_message="Memory storage failed. Please try again.",
            request_id=request_id
        )
        raise HTTPException(
            status_code=get_http_status_for_error_code(error_response.type),
            detail=error_response.dict()
        )


@router.get("/plugins", response_model=List[Dict[str, Any]])
async def list_plugins_compatibility(
    http_request: Request,
    plugin_service = Depends(get_plugin_service)
):
    """
    Compatibility endpoint for listing available plugins.
    """
    request_id = get_request_id(http_request)
    
    try:
        logger.info(f"[{request_id}] Listing available plugins")
        
        # Get plugins from plugin service
        plugins = await plugin_service.list_plugins() if hasattr(plugin_service, 'list_plugins') else []
        
        # Transform to web UI format
        web_ui_plugins = WebUITransformationService.transform_plugin_info_to_web_ui(plugins)
        
        logger.info(f"[{request_id}] Found {len(web_ui_plugins)} plugins")
        
        return [plugin.dict() for plugin in web_ui_plugins]
        
    except Exception as e:
        raise handle_service_error(e, WebUIErrorCode.PLUGIN_ERROR,
                                 "Failed to list plugins", request_id)


@router.post("/plugins/execute", response_model=WebUIPluginExecuteResponse)
async def execute_plugin_compatibility(
    request: WebUIPluginExecuteRequest,
    http_request: Request,
    plugin_service = Depends(get_plugin_service)
):
    """
    Compatibility endpoint for executing plugins.
    """
    request_id = get_request_id(http_request)
    
    try:
        logger.info(f"[{request_id}] Executing plugin: {request.plugin_name}")
        
        # Execute plugin
        start_time = datetime.utcnow()
        result = await plugin_service.execute_plugin(
            request.plugin_name,
            request.parameters,
            user_id=request.user_id,
            session_id=request.session_id
        ) if hasattr(plugin_service, 'execute_plugin') else {"error": "Plugin service not available"}
        
        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Create response
        response = WebUIPluginExecuteResponse(
            success="error" not in result,
            result=result if "error" not in result else None,
            error=result.get("error"),
            execution_time_ms=execution_time
        )
        
        logger.info(f"[{request_id}] Plugin execution completed in {execution_time:.2f}ms")
        
        return response
        
    except ValidationError as e:
        logger.warning(f"[{request_id}] Validation error in plugin execution: {e}")
        raise HTTPException(
            status_code=400,
            detail=create_validation_error_response(e.errors(), request_id).dict()
        )
    except Exception as e:
        raise handle_service_error(e, WebUIErrorCode.PLUGIN_ERROR,
                                 "Plugin execution failed", request_id)


@router.get("/analytics/system", response_model=WebUISystemMetrics)
async def get_system_metrics_compatibility(
    http_request: Request
):
    """
    Compatibility endpoint for system metrics.
    """
    request_id = get_request_id(http_request)
    
    try:
        logger.info(f"[{request_id}] Getting system metrics")
        
        # Mock system metrics for now - replace with actual metrics service
        backend_metrics = {
            "cpu_usage": 45.2,
            "memory_usage": 67.8,
            "disk_usage": 23.1,
            "active_sessions": 12,
            "total_requests": 1547,
            "error_rate": 2.3
        }
        
        # Transform to web UI format
        response = WebUITransformationService.transform_system_metrics_to_web_ui(backend_metrics)
        
        return response
        
    except Exception as e:
        raise handle_service_error(e, WebUIErrorCode.INTERNAL_ERROR,
                                 "Failed to get system metrics", request_id)


@router.get("/analytics/usage", response_model=WebUIUsageAnalytics)
async def get_usage_analytics_compatibility(
    http_request: Request
):
    """
    Compatibility endpoint for usage analytics.
    """
    request_id = get_request_id(http_request)
    
    try:
        logger.info(f"[{request_id}] Getting usage analytics")
        
        # Mock usage analytics for now - replace with actual analytics service
        backend_analytics = {
            "total_conversations": 234,
            "total_messages": 1876,
            "average_session_duration": 15.7,
            "most_used_features": [
                {"name": "Chat", "usage_count": 1234},
                {"name": "Memory Query", "usage_count": 567},
                {"name": "Plugin Execution", "usage_count": 234}
            ],
            "user_activity": {
                "daily_active_users": 45,
                "weekly_active_users": 123,
                "monthly_active_users": 456
            }
        }
        
        # Transform to web UI format
        response = WebUITransformationService.transform_usage_analytics_to_web_ui(backend_analytics)
        
        return response
        
    except Exception as e:
        raise handle_service_error(e, WebUIErrorCode.INTERNAL_ERROR,
                                 "Failed to get usage analytics", request_id)


@router.get("/health", response_model=WebUIHealthCheck)
async def health_check_compatibility(
    http_request: Request
):
    """
    Compatibility endpoint for health checks that returns web UI expected format.
    """
    request_id = get_request_id(http_request)
    
    try:
        logger.info(f"[{request_id}] Performing health check")
        
        # Get health status from health monitor
        try:
            from ..core.health_monitor import get_health_monitor
            health_monitor = get_health_monitor()
            health_summary = health_monitor.get_health_summary()
            
            backend_health = {
                "status": health_summary["overall_status"],
                "services": {
                    service: {
                        "status": "healthy" if service in health_summary.get("healthy_services", []) else "unhealthy",
                        "last_check": health_summary["last_check"]
                    }
                    for service in health_summary.get("services", {})
                },
                "timestamp": health_summary["last_check"],
                "uptime": health_summary.get("average_uptime", 0.0)
            }
        except Exception as e:
            logger.warning(f"[{request_id}] Health monitor not available: {e}")
            backend_health = {
                "status": "healthy",
                "services": {
                    "ai_orchestrator": {"status": "healthy", "last_check": datetime.utcnow().isoformat()},
                    "memory_service": {"status": "healthy", "last_check": datetime.utcnow().isoformat()},
                    "plugin_service": {"status": "healthy", "last_check": datetime.utcnow().isoformat()}
                },
                "timestamp": datetime.utcnow().isoformat(),
                "uptime": 3600.0
            }
        
        # Transform to web UI format
        response = WebUITransformationService.transform_health_check_to_web_ui(backend_health)
        
        return response
        
    except Exception as e:
        raise handle_service_error(e, WebUIErrorCode.INTERNAL_ERROR,
                                 "Health check failed", request_id)


# Note: Exception handlers are handled within individual endpoints
# since APIRouter doesn't support exception_handler decorator