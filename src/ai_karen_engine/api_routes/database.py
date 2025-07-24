"""
Database API routes for AI Karen.
Provides REST endpoints for tenant, memory, and conversation management.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body
from pydantic import BaseModel, Field, validator

from ai_karen_engine.database.integration_manager import get_database_manager, DatabaseIntegrationManager
from ai_karen_engine.utils.auth import get_current_user, get_tenant_context

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/database", tags=["database"])


# Pydantic Models
class TenantCreateRequest(BaseModel):
    """Request model for creating a tenant."""
    name: str = Field(..., min_length=1, max_length=255, description="Tenant name")
    slug: str = Field(..., min_length=1, max_length=100, description="Tenant slug")
    admin_email: str = Field(..., description="Admin user email")
    subscription_tier: str = Field("basic", description="Subscription tier")
    settings: Optional[Dict[str, Any]] = Field(None, description="Additional settings")
    
    @validator('slug')
    def validate_slug(cls, v):
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Slug must contain only alphanumeric characters, hyphens, and underscores')
        return v.lower()


class TenantResponse(BaseModel):
    """Response model for tenant information."""
    tenant_id: str
    name: str
    slug: str
    subscription_tier: str
    settings: Dict[str, Any]
    is_active: bool
    created_at: str
    updated_at: str


class TenantStatsResponse(BaseModel):
    """Response model for tenant statistics."""
    tenant_id: str
    user_count: int
    conversation_count: int
    memory_entry_count: int
    plugin_execution_count: int
    storage_used_mb: float
    last_activity: Optional[str]
    created_at: str


class MemoryStoreRequest(BaseModel):
    """Request model for storing memory."""
    content: str = Field(..., min_length=1, description="Memory content")
    user_id: Optional[str] = Field(None, description="User ID")
    session_id: Optional[str] = Field(None, description="Session ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    tags: Optional[List[str]] = Field(None, description="Memory tags")


class MemoryQueryRequest(BaseModel):
    """Request model for querying memories."""
    query_text: str = Field(..., min_length=1, description="Query text")
    user_id: Optional[str] = Field(None, description="User ID filter")
    top_k: int = Field(10, ge=1, le=100, description="Number of results")
    similarity_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Similarity threshold")


class MemoryResponse(BaseModel):
    """Response model for memory entries."""
    id: str
    content: str
    metadata: Dict[str, Any]
    timestamp: float
    ttl: Optional[str]
    user_id: Optional[str]
    session_id: Optional[str]
    tags: List[str]
    similarity_score: Optional[float]


class ConversationCreateRequest(BaseModel):
    """Request model for creating a conversation."""
    user_id: str = Field(..., description="User ID")
    title: Optional[str] = Field(None, max_length=255, description="Conversation title")
    initial_message: Optional[str] = Field(None, description="Initial message")


class MessageAddRequest(BaseModel):
    """Request model for adding a message."""
    role: str = Field(..., description="Message role (user, assistant, system)")
    content: str = Field(..., min_length=1, description="Message content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Message metadata")
    
    @validator('role')
    def validate_role(cls, v):
        valid_roles = ['user', 'assistant', 'system', 'function']
        if v not in valid_roles:
            raise ValueError(f'Role must be one of: {valid_roles}')
        return v


class ConversationResponse(BaseModel):
    """Response model for conversation."""
    id: str
    user_id: str
    title: Optional[str]
    messages: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    is_active: bool
    created_at: str
    updated_at: str
    message_count: int
    last_message_at: Optional[str]


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    timestamp: str
    components: Dict[str, Any]


# Dependency to get database manager
async def get_db_manager() -> DatabaseIntegrationManager:
    """Get database manager dependency."""
    return await get_database_manager()


# Tenant Management Endpoints
@router.post("/tenants", response_model=Dict[str, Any], status_code=201)
async def create_tenant(
    request: TenantCreateRequest,
    db_manager: DatabaseIntegrationManager = Depends(get_db_manager)
):
    """Create a new tenant."""
    try:
        tenant_data = await db_manager.create_tenant(
            name=request.name,
            slug=request.slug,
            admin_email=request.admin_email,
            subscription_tier=request.subscription_tier,
            settings=request.settings
        )
        
        logger.info(f"Created tenant: {tenant_data['tenant_id']}")
        return {
            "success": True,
            "message": "Tenant created successfully",
            "data": tenant_data
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create tenant: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/tenants/{tenant_id}", response_model=Dict[str, Any])
async def get_tenant(
    tenant_id: str = Path(..., description="Tenant ID"),
    db_manager: DatabaseIntegrationManager = Depends(get_db_manager)
):
    """Get tenant information."""
    try:
        tenant_data = await db_manager.get_tenant(tenant_id)
        
        if not tenant_data:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        return {
            "success": True,
            "data": tenant_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/tenants/{tenant_id}/stats", response_model=Dict[str, Any])
async def get_tenant_stats(
    tenant_id: str = Path(..., description="Tenant ID"),
    db_manager: DatabaseIntegrationManager = Depends(get_db_manager)
):
    """Get tenant statistics."""
    try:
        stats_data = await db_manager.get_tenant_stats(tenant_id)
        
        if not stats_data:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        return {
            "success": True,
            "data": stats_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tenant stats {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Memory Management Endpoints
@router.post("/tenants/{tenant_id}/memories", response_model=Dict[str, Any], status_code=201)
async def store_memory(
    tenant_id: str = Path(..., description="Tenant ID"),
    request: MemoryStoreRequest = Body(...),
    db_manager: DatabaseIntegrationManager = Depends(get_db_manager)
):
    """Store a memory entry."""
    try:
        memory_id = await db_manager.store_memory(
            tenant_id=tenant_id,
            content=request.content,
            user_id=request.user_id,
            session_id=request.session_id,
            metadata=request.metadata,
            tags=request.tags
        )
        
        if not memory_id:
            return {
                "success": True,
                "message": "Content not stored (not surprising enough)",
                "data": None
            }
        
        logger.info(f"Stored memory {memory_id} for tenant {tenant_id}")
        return {
            "success": True,
            "message": "Memory stored successfully",
            "data": {"memory_id": memory_id}
        }
        
    except Exception as e:
        logger.error(f"Failed to store memory for tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/tenants/{tenant_id}/memories/query", response_model=Dict[str, Any])
async def query_memories(
    tenant_id: str = Path(..., description="Tenant ID"),
    request: MemoryQueryRequest = Body(...),
    db_manager: DatabaseIntegrationManager = Depends(get_db_manager)
):
    """Query memories with semantic search."""
    try:
        memories = await db_manager.query_memories(
            tenant_id=tenant_id,
            query_text=request.query_text,
            user_id=request.user_id,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold
        )
        
        logger.info(f"Retrieved {len(memories)} memories for tenant {tenant_id}")
        return {
            "success": True,
            "data": {
                "memories": memories,
                "count": len(memories)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to query memories for tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Conversation Management Endpoints
@router.post("/tenants/{tenant_id}/conversations", response_model=Dict[str, Any], status_code=201)
async def create_conversation(
    tenant_id: str = Path(..., description="Tenant ID"),
    request: ConversationCreateRequest = Body(...),
    db_manager: DatabaseIntegrationManager = Depends(get_db_manager)
):
    """Create a new conversation."""
    try:
        conversation_data = await db_manager.create_conversation(
            tenant_id=tenant_id,
            user_id=request.user_id,
            title=request.title,
            initial_message=request.initial_message
        )
        
        logger.info(f"Created conversation {conversation_data['id']} for tenant {tenant_id}")
        return {
            "success": True,
            "message": "Conversation created successfully",
            "data": conversation_data
        }
        
    except Exception as e:
        logger.error(f"Failed to create conversation for tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/tenants/{tenant_id}/conversations/{conversation_id}", response_model=Dict[str, Any])
async def get_conversation(
    tenant_id: str = Path(..., description="Tenant ID"),
    conversation_id: str = Path(..., description="Conversation ID"),
    db_manager: DatabaseIntegrationManager = Depends(get_db_manager)
):
    """Get conversation with context."""
    try:
        conversation_data = await db_manager.get_conversation(
            tenant_id=tenant_id,
            conversation_id=conversation_id
        )
        
        if not conversation_data:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {
            "success": True,
            "data": conversation_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/tenants/{tenant_id}/conversations/{conversation_id}/messages", response_model=Dict[str, Any], status_code=201)
async def add_message(
    tenant_id: str = Path(..., description="Tenant ID"),
    conversation_id: str = Path(..., description="Conversation ID"),
    request: MessageAddRequest = Body(...),
    db_manager: DatabaseIntegrationManager = Depends(get_db_manager)
):
    """Add a message to conversation."""
    try:
        message_data = await db_manager.add_message(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            role=request.role,
            content=request.content,
            metadata=request.metadata
        )
        
        if not message_data:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        logger.info(f"Added message to conversation {conversation_id}")
        return {
            "success": True,
            "message": "Message added successfully",
            "data": message_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add message to conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/tenants/{tenant_id}/users/{user_id}/conversations", response_model=Dict[str, Any])
async def list_conversations(
    tenant_id: str = Path(..., description="Tenant ID"),
    user_id: str = Path(..., description="User ID"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of conversations"),
    db_manager: DatabaseIntegrationManager = Depends(get_db_manager)
):
    """List conversations for a user."""
    try:
        conversations = await db_manager.list_conversations(
            tenant_id=tenant_id,
            user_id=user_id,
            limit=limit
        )
        
        return {
            "success": True,
            "data": {
                "conversations": conversations,
                "count": len(conversations)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to list conversations for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Health and Monitoring Endpoints
@router.get("/health", response_model=Dict[str, Any])
async def health_check(
    db_manager: DatabaseIntegrationManager = Depends(get_db_manager)
):
    """Perform comprehensive health check."""
    try:
        health_data = await db_manager.health_check()
        
        status_code = 200 if health_data["status"] in ["healthy", "degraded"] else 503
        
        return {
            "success": True,
            "data": health_data
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "success": False,
            "data": {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        }


@router.get("/metrics", response_model=Dict[str, Any])
async def get_metrics(
    db_manager: DatabaseIntegrationManager = Depends(get_db_manager)
):
    """Get system metrics."""
    try:
        metrics_data = await db_manager.get_system_metrics()
        
        return {
            "success": True,
            "data": metrics_data
        }
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/maintenance", response_model=Dict[str, Any])
async def run_maintenance(
    db_manager: DatabaseIntegrationManager = Depends(get_db_manager)
):
    """Run maintenance tasks."""
    try:
        maintenance_results = await db_manager.maintenance_tasks()
        
        return {
            "success": True,
            "message": "Maintenance tasks completed",
            "data": maintenance_results
        }
        
    except Exception as e:
        logger.error(f"Maintenance tasks failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Advanced Query Endpoints
@router.get("/tenants/{tenant_id}/analytics", response_model=Dict[str, Any])
async def get_tenant_analytics(
    tenant_id: str = Path(..., description="Tenant ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days for analytics"),
    db_manager: DatabaseIntegrationManager = Depends(get_db_manager)
):
    """Get tenant analytics data."""
    try:
        # This would be implemented with more sophisticated analytics
        # For now, return basic stats
        stats_data = await db_manager.get_tenant_stats(tenant_id)
        
        if not stats_data:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        # Add analytics calculations here
        analytics_data = {
            "tenant_id": tenant_id,
            "period_days": days,
            "basic_stats": stats_data,
            "trends": {
                "memory_growth": "stable",  # Would calculate from historical data
                "conversation_activity": "increasing",
                "user_engagement": "high"
            },
            "recommendations": [
                "Consider upgrading to pro tier for better performance",
                "Enable advanced memory features for better context"
            ]
        }
        
        return {
            "success": True,
            "data": analytics_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analytics for tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/tenants/{tenant_id}/memories/bulk", response_model=Dict[str, Any])
async def bulk_store_memories(
    tenant_id: str = Path(..., description="Tenant ID"),
    memories: List[MemoryStoreRequest] = Body(..., description="List of memories to store"),
    db_manager: DatabaseIntegrationManager = Depends(get_db_manager)
):
    """Bulk store multiple memories."""
    try:
        stored_ids = []
        skipped_count = 0
        
        for memory_request in memories:
            memory_id = await db_manager.store_memory(
                tenant_id=tenant_id,
                content=memory_request.content,
                user_id=memory_request.user_id,
                session_id=memory_request.session_id,
                metadata=memory_request.metadata,
                tags=memory_request.tags
            )
            
            if memory_id:
                stored_ids.append(memory_id)
            else:
                skipped_count += 1
        
        logger.info(f"Bulk stored {len(stored_ids)} memories for tenant {tenant_id}")
        return {
            "success": True,
            "message": f"Bulk storage completed",
            "data": {
                "stored_count": len(stored_ids),
                "skipped_count": skipped_count,
                "stored_ids": stored_ids
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to bulk store memories for tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
