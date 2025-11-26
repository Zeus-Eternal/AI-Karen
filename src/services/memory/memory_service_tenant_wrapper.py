"""
Memory Service Tenant Isolation Wrapper - Phase 4.1.c
Wraps existing memory service with multi-tenant data isolation capabilities.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from src.services.memory_service import WebUIMemoryService, WebUIMemoryQuery, WebUIMemoryEntry
from src.services.tenant_isolation import (
    TenantIsolationService,
    TenantContext,
    TenantAccessLevel,
    SecurityIncidentType,
    get_tenant_isolation_service,
    create_tenant_context
)
from src.services.audit_logger import (
    AuditLogger,
    AuditContext,
    get_audit_logger,
    create_audit_context
)

logger = logging.getLogger(__name__)

class TenantIsolatedMemoryService:
    """Memory service with tenant isolation capabilities"""
    
    def __init__(self, base_memory_service: WebUIMemoryService):
        self.base_service = base_memory_service
        self.tenant_service = get_tenant_isolation_service()
        self.audit_logger = get_audit_logger()
        self.logger = logging.getLogger(f"{__name__}.TenantIsolatedMemoryService")
    
    def _create_tenant_context_from_request(
        self,
        tenant_id: str,
        user_id: str,
        org_id: Optional[str] = None,
        access_level: TenantAccessLevel = TenantAccessLevel.STRICT
    ) -> TenantContext:
        """Create tenant context from request parameters"""
        return create_tenant_context(
            tenant_id=tenant_id,
            user_id=user_id,
            org_id=org_id,
            access_level=access_level
        )
    
    def _validate_tenant_access(
        self,
        context: TenantContext,
        target_tenant_id: str,
        correlation_id: Optional[str] = None
    ) -> bool:
        """Validate tenant access with security incident logging"""
        return self.tenant_service.validate_data_access(
            context=context,
            target_tenant_id=target_tenant_id,
            resource_type="memory_data",
            correlation_id=correlation_id
        )
    
    def _filter_memories_by_tenant(
        self,
        memories: List[WebUIMemoryEntry],
        context: TenantContext,
        correlation_id: Optional[str] = None
    ) -> List[WebUIMemoryEntry]:
        """Filter memories to ensure tenant isolation"""
        filtered_memories = []
        
        for memory in memories:
            # Extract tenant information from memory
            memory_tenant_id = getattr(memory, 'tenant_id', None)
            memory_user_id = getattr(memory, 'user_id', None)
            
            # If no tenant info in memory, use metadata
            if not memory_tenant_id and memory.metadata:
                memory_tenant_id = memory.metadata.get('tenant_id')
                memory_user_id = memory.metadata.get('user_id')
            
            # Skip memories without tenant information
            if not memory_tenant_id:
                self.logger.warning(f"Memory {memory.id} has no tenant information, skipping")
                continue
            
            # Validate access
            if self._validate_tenant_access(context, memory_tenant_id, correlation_id):
                # Additional user-level check for strict isolation
                if context.access_level == TenantAccessLevel.STRICT:
                    if memory_user_id != context.user_id:
                        self.logger.debug(f"Filtering out memory {memory.id} - different user")
                        continue
                
                filtered_memories.append(memory)
            else:
                # Log potential security incident
                self.tenant_service.log_security_incident(
                    incident_type=SecurityIncidentType.CROSS_TENANT_ACCESS_ATTEMPT,
                    context=context,
                    attempted_access={
                        "memory_id": memory.id,
                        "memory_tenant_id": memory_tenant_id,
                        "memory_user_id": memory_user_id,
                        "operation": "memory_query"
                    },
                    correlation_id=correlation_id
                )
        
        return filtered_memories
    
    async def store_web_ui_memory(
        self,
        tenant_id: Union[str, uuid.UUID],
        content: str,
        user_id: str,
        ui_source,
        session_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        memory_type=None,
        tags: Optional[List[str]] = None,
        importance_score: int = None,
        ai_generated: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
        ttl_hours: Optional[int] = None,
        tenant_filters: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        access_level: TenantAccessLevel = TenantAccessLevel.STRICT
    ) -> Optional[str]:
        """Store memory with tenant isolation"""
        start_time = datetime.utcnow()
        
        # Create audit context
        audit_context = create_audit_context(
            user_id=user_id,
            tenant_id=str(tenant_id),
            session_id=session_id,
            correlation_id=correlation_id
        )

        try:
            # Verify tenant filters
            allowed_tenant_id = None
            if tenant_filters:
                allowed_tenant_id = tenant_filters.get("org_id") or tenant_filters.get("user_id")
            if allowed_tenant_id and str(tenant_id) != str(allowed_tenant_id):
                context = self._create_tenant_context_from_request(
                    tenant_id=str(allowed_tenant_id),
                    user_id=user_id,
                    org_id=tenant_filters.get("org_id") if tenant_filters else None,
                    access_level=access_level
                )
                self.tenant_service.log_security_incident(
                    incident_type=SecurityIncidentType.CROSS_TENANT_ACCESS_ATTEMPT,
                    context=context,
                    attempted_access={
                        "target_tenant_id": str(tenant_id),
                        "operation": "memory_commit",
                        "user_id": user_id
                    },
                    correlation_id=correlation_id
                )
                raise PermissionError(f"Access denied for tenant {tenant_id}")

            # Create tenant context
            context = self._create_tenant_context_from_request(
                tenant_id=str(tenant_id),
                user_id=user_id,
                access_level=access_level
            )

            # Validate tenant access (user should be able to write to their own tenant)
            if not self._validate_tenant_access(context, str(tenant_id), correlation_id):
                # Log audit event for failed access
                duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                self.audit_logger.log_memory_create(
                    context=audit_context,
                    memory_content=content,
                    metadata=metadata,
                    duration_ms=duration_ms,
                    outcome="failure",
                    error_message=f"Access denied for tenant {tenant_id}"
                )
                raise PermissionError(f"Access denied for tenant {tenant_id}")
            
            # Add tenant isolation metadata
            tenant_metadata = metadata or {}
            tenant_metadata.update({
                "tenant_id": str(tenant_id),
                "user_id": user_id,
                "access_level": access_level.value,
                "isolation_timestamp": datetime.utcnow().isoformat()
            })
            
            # Store using base service
            memory_id = await self.base_service.store_web_ui_memory(
                tenant_id=tenant_id,
                content=content,
                user_id=user_id,
                ui_source=ui_source,
                session_id=session_id,
                conversation_id=conversation_id,
                memory_type=memory_type,
                tags=tags,
                importance_score=importance_score,
                ai_generated=ai_generated,
                metadata=tenant_metadata,
                ttl_hours=ttl_hours,
                tenant_filters=tenant_filters
            )
            
            # Log successful audit event
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.audit_logger.log_memory_create(
                context=audit_context,
                memory_content=content,
                memory_id=memory_id,
                metadata=tenant_metadata,
                duration_ms=duration_ms,
                outcome="success"
            )
            
            self.logger.info(
                f"Stored memory {memory_id} for tenant {tenant_id}",
                extra={
                    "tenant_id": str(tenant_id),
                    "user_id": user_id,
                    "memory_id": memory_id,
                    "correlation_id": correlation_id
                }
            )
            
            return memory_id
            
        except Exception as e:
            # Log failed audit event
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.audit_logger.log_memory_create(
                context=audit_context,
                memory_content=content,
                metadata=metadata,
                duration_ms=duration_ms,
                outcome="failure",
                error_message=str(e)
            )
            
            self.logger.error(
                f"Failed to store memory for tenant {tenant_id}: {e}",
                extra={
                    "tenant_id": str(tenant_id),
                    "user_id": user_id,
                    "correlation_id": correlation_id
                }
            )
            raise
    
    async def query_memories(
        self,
        tenant_id: Union[str, uuid.UUID],
        query: WebUIMemoryQuery,
        tenant_filters: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        access_level: TenantAccessLevel = TenantAccessLevel.STRICT
    ) -> List[WebUIMemoryEntry]:
        """Query memories with tenant isolation"""
        start_time = datetime.utcnow()
        
        # Create audit context
        audit_context = create_audit_context(
            user_id=query.user_id or "unknown",
            tenant_id=str(tenant_id),
            correlation_id=correlation_id
        )
        
        try:
            # Verify tenant filters
            allowed_tenant_id = None
            if tenant_filters:
                allowed_tenant_id = tenant_filters.get("org_id") or tenant_filters.get("user_id")
            if allowed_tenant_id and str(tenant_id) != str(allowed_tenant_id):
                context = self._create_tenant_context_from_request(
                    tenant_id=str(allowed_tenant_id),
                    user_id=query.user_id or "unknown",
                    org_id=tenant_filters.get("org_id") if tenant_filters else None,
                    access_level=access_level
                )
                self.tenant_service.log_security_incident(
                    incident_type=SecurityIncidentType.CROSS_TENANT_ACCESS_ATTEMPT,
                    context=context,
                    attempted_access={
                        "target_tenant_id": str(tenant_id),
                        "operation": "memory_query",
                        "query": query.text
                    },
                    correlation_id=correlation_id
                )
                duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                self.audit_logger.log_memory_read(
                    context=audit_context,
                    query=query.text,
                    results_count=0,
                    duration_ms=duration_ms,
                    outcome="failure",
                    error_message=f"Access denied for tenant {tenant_id}"
                )
                self.logger.warning(
                    f"Access denied for tenant {tenant_id} query",
                    extra={
                        "tenant_id": str(tenant_id),
                        "user_id": query.user_id,
                        "correlation_id": correlation_id
                    }
                )
                return []

            # Create tenant context
            context = self._create_tenant_context_from_request(
                tenant_id=str(tenant_id),
                user_id=query.user_id or "unknown",
                access_level=access_level
            )

            # Validate tenant access
            if not self._validate_tenant_access(context, str(tenant_id), correlation_id):
                # Log audit event for failed access
                duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                self.audit_logger.log_memory_read(
                    context=audit_context,
                    query=query.text,
                    results_count=0,
                    duration_ms=duration_ms,
                    outcome="failure",
                    error_message=f"Access denied for tenant {tenant_id}"
                )

                self.logger.warning(
                    f"Access denied for tenant {tenant_id} query",
                    extra={
                        "tenant_id": str(tenant_id),
                        "user_id": query.user_id,
                        "correlation_id": correlation_id
                    }
                )
                return []
            
            # Add tenant filtering to query metadata
            if not hasattr(query, 'metadata_filter') or query.metadata_filter is None:
                query.metadata_filter = {}
            
            # Apply tenant filtering at query level
            query.metadata_filter.update({
                "tenant_id": str(tenant_id),
                "user_id": query.user_id
            })
            
            # Query using base service
            memories = await self.base_service.query_memories(
                tenant_id, query, tenant_filters=tenant_filters
            )
            
            # Apply additional tenant filtering to results
            filtered_memories = self._filter_memories_by_tenant(
                memories, context, correlation_id
            )
            
            # Log successful audit event
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            memory_ids = [memory.id for memory in filtered_memories]
            self.audit_logger.log_memory_read(
                context=audit_context,
                query=query.text,
                results_count=len(filtered_memories),
                memory_ids=memory_ids,
                duration_ms=duration_ms,
                outcome="success"
            )
            
            self.logger.info(
                f"Queried {len(filtered_memories)} memories for tenant {tenant_id}",
                extra={
                    "tenant_id": str(tenant_id),
                    "user_id": query.user_id,
                    "original_count": len(memories),
                    "filtered_count": len(filtered_memories),
                    "correlation_id": correlation_id
                }
            )
            
            return filtered_memories
            
        except Exception as e:
            # Log failed audit event
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.audit_logger.log_memory_read(
                context=audit_context,
                query=query.text,
                results_count=0,
                duration_ms=duration_ms,
                outcome="failure",
                error_message=str(e)
            )
            
            self.logger.error(
                f"Failed to query memories for tenant {tenant_id}: {e}",
                extra={
                    "tenant_id": str(tenant_id),
                    "user_id": query.user_id,
                    "correlation_id": correlation_id
                }
            )
            raise
    
    async def build_conversation_context(
        self,
        tenant_id: Union[str, uuid.UUID],
        query: str,
        user_id: str,
        session_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        access_level: TenantAccessLevel = TenantAccessLevel.STRICT
    ) -> Dict[str, Any]:
        """Build conversation context with tenant isolation"""
        try:
            # Create tenant context
            context = self._create_tenant_context_from_request(
                tenant_id=str(tenant_id),
                user_id=user_id,
                access_level=access_level
            )
            
            # Validate tenant access
            if not self._validate_tenant_access(context, str(tenant_id), correlation_id):
                return {
                    "memories": [],
                    "total_memories": 0,
                    "memory_types_found": [],
                    "conversation_context": None,
                    "error": "Access denied"
                }
            
            # Build context using base service
            context_data = await self.base_service.build_conversation_context(
                tenant_id=tenant_id,
                query=query,
                user_id=user_id,
                session_id=session_id,
                conversation_id=conversation_id
            )
            
            # Add tenant isolation metadata
            if "context_metadata" not in context_data:
                context_data["context_metadata"] = {}
            
            context_data["context_metadata"].update({
                "tenant_id": str(tenant_id),
                "access_level": access_level.value,
                "isolation_applied": True,
                "correlation_id": correlation_id
            })
            
            return context_data
            
        except Exception as e:
            self.logger.error(
                f"Failed to build context for tenant {tenant_id}: {e}",
                extra={
                    "tenant_id": str(tenant_id),
                    "user_id": user_id,
                    "correlation_id": correlation_id
                }
            )
            return {
                "memories": [],
                "total_memories": 0,
                "memory_types_found": [],
                "conversation_context": None,
                "error": str(e)
            }
    
    async def confirm_memory(
        self,
        tenant_id: Union[str, uuid.UUID],
        memory_id: str,
        user_id: str,
        confirmed: bool = True,
        correlation_id: Optional[str] = None,
        access_level: TenantAccessLevel = TenantAccessLevel.STRICT
    ) -> bool:
        """Confirm memory with tenant isolation"""
        try:
            # Create tenant context
            context = self._create_tenant_context_from_request(
                tenant_id=str(tenant_id),
                user_id=user_id,
                access_level=access_level
            )
            
            # Validate tenant access
            if not self._validate_tenant_access(context, str(tenant_id), correlation_id):
                self.logger.warning(
                    f"Access denied for memory confirmation: {memory_id}",
                    extra={
                        "tenant_id": str(tenant_id),
                        "user_id": user_id,
                        "memory_id": memory_id,
                        "correlation_id": correlation_id
                    }
                )
                return False
            
            # Confirm using base service
            result = await self.base_service.confirm_memory(tenant_id, memory_id, confirmed)
            
            self.logger.info(
                f"Memory {memory_id} confirmation: {confirmed}",
                extra={
                    "tenant_id": str(tenant_id),
                    "user_id": user_id,
                    "memory_id": memory_id,
                    "confirmed": confirmed,
                    "correlation_id": correlation_id
                }
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                f"Failed to confirm memory {memory_id}: {e}",
                extra={
                    "tenant_id": str(tenant_id),
                    "user_id": user_id,
                    "memory_id": memory_id,
                    "correlation_id": correlation_id
                }
            )
            return False
    
    async def get_memory_analytics(
        self,
        tenant_id: Union[str, uuid.UUID],
        user_id: str,
        time_range=None,
        correlation_id: Optional[str] = None,
        access_level: TenantAccessLevel = TenantAccessLevel.STRICT
    ) -> Dict[str, Any]:
        """Get memory analytics with tenant isolation"""
        try:
            # Create tenant context
            context = self._create_tenant_context_from_request(
                tenant_id=str(tenant_id),
                user_id=user_id,
                access_level=access_level
            )
            
            # Validate tenant access
            if not self._validate_tenant_access(context, str(tenant_id), correlation_id):
                return {"error": "Access denied"}
            
            # Get analytics using base service
            analytics = await self.base_service.get_memory_analytics(
                tenant_id=tenant_id,
                user_id=user_id,
                time_range=time_range
            )
            
            # Add tenant isolation metadata
            analytics["tenant_isolation"] = {
                "tenant_id": str(tenant_id),
                "access_level": access_level.value,
                "isolation_applied": True,
                "correlation_id": correlation_id
            }
            
            return analytics
            
        except Exception as e:
            self.logger.error(
                f"Failed to get analytics for tenant {tenant_id}: {e}",
                extra={
                    "tenant_id": str(tenant_id),
                    "user_id": user_id,
                    "correlation_id": correlation_id
                }
            )
            return {"error": str(e)}

# Factory function to create tenant-isolated memory service
def create_tenant_isolated_memory_service(
    base_memory_service: WebUIMemoryService
) -> TenantIsolatedMemoryService:
    """Create tenant-isolated memory service wrapper"""
    return TenantIsolatedMemoryService(base_memory_service)

# Export public interface
__all__ = [
    "TenantIsolatedMemoryService",
    "create_tenant_isolated_memory_service"
]