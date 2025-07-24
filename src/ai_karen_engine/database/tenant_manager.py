"""
Production-grade tenant management system for AI Karen.
Handles tenant lifecycle, schema management, and data isolation.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

from sqlalchemy import text, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from ai_karen_engine.database.client import MultiTenantPostgresClient
from ai_karen_engine.database.models import (
    Tenant,
    User,
    TenantConversation,
    TenantMemoryEntry,
)
from ai_karen_engine.core.milvus_client import MilvusClient
from ai_karen_engine.core.embedding_manager import EmbeddingManager

logger = logging.getLogger(__name__)


@dataclass
class TenantConfig:
    """Configuration for a tenant."""
    name: str
    slug: str
    subscription_tier: str = "basic"
    settings: Dict[str, Any] = field(default_factory=dict)
    features: List[str] = field(default_factory=list)
    limits: Dict[str, int] = field(default_factory=dict)
    
    def __post_init__(self):
        """Set default limits based on subscription tier."""
        if not self.limits:
            self.limits = self._get_default_limits()
    
    def _get_default_limits(self) -> Dict[str, int]:
        """Get default limits based on subscription tier."""
        limits_map = {
            "basic": {
                "max_users": 5,
                "max_conversations": 100,
                "max_memory_entries": 1000,
                "max_plugins": 10,
                "storage_mb": 100
            },
            "pro": {
                "max_users": 50,
                "max_conversations": 1000,
                "max_memory_entries": 10000,
                "max_plugins": 50,
                "storage_mb": 1000
            },
            "enterprise": {
                "max_users": -1,  # unlimited
                "max_conversations": -1,
                "max_memory_entries": -1,
                "max_plugins": -1,
                "storage_mb": -1
            }
        }
        return limits_map.get(self.subscription_tier, limits_map["basic"])


@dataclass
class TenantStats:
    """Statistics for a tenant."""
    tenant_id: str
    user_count: int
    conversation_count: int
    memory_entry_count: int
    plugin_execution_count: int
    storage_used_mb: float
    last_activity: Optional[datetime]
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tenant_id": self.tenant_id,
            "user_count": self.user_count,
            "conversation_count": self.conversation_count,
            "memory_entry_count": self.memory_entry_count,
            "plugin_execution_count": self.plugin_execution_count,
            "storage_used_mb": self.storage_used_mb,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "created_at": self.created_at.isoformat()
        }


class TenantManager:
    """Production-grade tenant management system."""
    
    def __init__(
        self,
        db_client: MultiTenantPostgresClient,
        milvus_client: Optional[MilvusClient] = None,
        embedding_manager: Optional[EmbeddingManager] = None
    ):
        """Initialize tenant manager.
        
        Args:
            db_client: Database client
            milvus_client: Milvus vector database client
            embedding_manager: Embedding manager for vector operations
        """
        self.db_client = db_client
        self.milvus_client = milvus_client
        self.embedding_manager = embedding_manager
        self._tenant_cache: Dict[str, Tenant] = {}
        self._stats_cache: Dict[str, TenantStats] = {}
        self._cache_ttl = timedelta(minutes=5)
        self._last_cache_update: Dict[str, datetime] = {}
    
    async def create_tenant(
        self,
        config: TenantConfig,
        admin_email: str,
        admin_roles: Optional[List[str]] = None
    ) -> Tenant:
        """Create a new tenant with complete setup.
        
        Args:
            config: Tenant configuration
            admin_email: Admin user email
            admin_roles: Admin user roles
            
        Returns:
            Created tenant
        """
        if admin_roles is None:
            admin_roles = ["admin", "user"]
        
        logger.info(f"Creating tenant: {config.name} ({config.slug})")
        
        try:
            async with self.db_client.get_async_session() as session:
                # Create tenant record
                tenant = Tenant(
                    name=config.name,
                    slug=config.slug,
                    subscription_tier=config.subscription_tier,
                    settings={
                        **config.settings,
                        "features": config.features,
                        "limits": config.limits
                    }
                )
                
                session.add(tenant)
                await session.flush()  # Get the tenant ID
                
                # Create tenant schema
                schema_created = self.db_client.create_tenant_schema(tenant.id)
                if not schema_created:
                    raise RuntimeError(f"Failed to create schema for tenant {tenant.id}")
                
                # Create admin user
                admin_user = User(
                    tenant_id=tenant.id,
                    email=admin_email,
                    roles=admin_roles,
                    preferences={"is_admin": True}
                )
                
                session.add(admin_user)
                await session.commit()
                
                # Initialize vector collections if Milvus is available
                if self.milvus_client:
                    await self._initialize_tenant_vectors(tenant.id)
                
                # Cache the tenant
                self._tenant_cache[str(tenant.id)] = tenant
                
                logger.info(f"Successfully created tenant {tenant.id} with admin user {admin_user.id}")
                return tenant
                
        except IntegrityError as e:
            logger.error(f"Tenant creation failed - integrity error: {e}")
            raise ValueError(f"Tenant with slug '{config.slug}' already exists")
        except Exception as e:
            logger.error(f"Failed to create tenant: {e}")
            # Cleanup on failure
            if 'tenant' in locals():
                await self._cleanup_failed_tenant(tenant.id)
            raise
    
    async def get_tenant(self, tenant_id: Union[str, uuid.UUID]) -> Optional[Tenant]:
        """Get tenant by ID with caching.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Tenant if found
        """
        tenant_id_str = str(tenant_id)
        
        # Check cache first
        if tenant_id_str in self._tenant_cache:
            cache_time = self._last_cache_update.get(tenant_id_str)
            if cache_time and datetime.utcnow() - cache_time < self._cache_ttl:
                return self._tenant_cache[tenant_id_str]
        
        try:
            async with self.db_client.get_async_session() as session:
                result = await session.execute(
                    select(Tenant).where(Tenant.id == tenant_id)
                )
                tenant = result.scalar_one_or_none()
                
                if tenant:
                    self._tenant_cache[tenant_id_str] = tenant
                    self._last_cache_update[tenant_id_str] = datetime.utcnow()
                
                return tenant
                
        except Exception as e:
            logger.error(f"Failed to get tenant {tenant_id}: {e}")
            return None
    
    async def get_tenant_by_slug(self, slug: str) -> Optional[Tenant]:
        """Get tenant by slug.
        
        Args:
            slug: Tenant slug
            
        Returns:
            Tenant if found
        """
        try:
            async with self.db_client.get_async_session() as session:
                result = await session.execute(
                    select(Tenant).where(Tenant.slug == slug)
                )
                return result.scalar_one_or_none()
                
        except Exception as e:
            logger.error(f"Failed to get tenant by slug {slug}: {e}")
            return None
    
    async def update_tenant(
        self,
        tenant_id: Union[str, uuid.UUID],
        updates: Dict[str, Any]
    ) -> bool:
        """Update tenant configuration.
        
        Args:
            tenant_id: Tenant ID
            updates: Fields to update
            
        Returns:
            True if successful
        """
        try:
            async with self.db_client.get_async_session() as session:
                await session.execute(
                    update(Tenant)
                    .where(Tenant.id == tenant_id)
                    .values(**updates, updated_at=datetime.utcnow())
                )
                await session.commit()
                
                # Invalidate cache
                self._tenant_cache.pop(str(tenant_id), None)
                
                logger.info(f"Updated tenant {tenant_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update tenant {tenant_id}: {e}")
            return False
    
    async def delete_tenant(self, tenant_id: Union[str, uuid.UUID]) -> bool:
        """Delete tenant and all associated data.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            True if successful
        """
        logger.warning(f"Deleting tenant {tenant_id} and ALL associated data")
        
        try:
            async with self.db_client.get_async_session() as session:
                # Get tenant first
                tenant = await self.get_tenant(tenant_id)
                if not tenant:
                    logger.warning(f"Tenant {tenant_id} not found")
                    return False
                
                # Delete vector collections
                if self.milvus_client:
                    await self._cleanup_tenant_vectors(tenant_id)
                
                # Drop tenant schema (cascades to all tenant data)
                schema_dropped = self.db_client.drop_tenant_schema(tenant_id)
                if not schema_dropped:
                    logger.error(f"Failed to drop schema for tenant {tenant_id}")
                
                # Delete tenant record
                await session.execute(
                    delete(Tenant).where(Tenant.id == tenant_id)
                )
                await session.commit()
                
                # Clear caches
                self._tenant_cache.pop(str(tenant_id), None)
                self._stats_cache.pop(str(tenant_id), None)
                self._last_cache_update.pop(str(tenant_id), None)
                
                logger.info(f"Successfully deleted tenant {tenant_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete tenant {tenant_id}: {e}")
            return False
    
    async def get_tenant_stats(self, tenant_id: Union[str, uuid.UUID]) -> Optional[TenantStats]:
        """Get comprehensive tenant statistics.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Tenant statistics
        """
        tenant_id_str = str(tenant_id)
        
        # Check cache
        if tenant_id_str in self._stats_cache:
            cache_time = self._last_cache_update.get(f"stats_{tenant_id_str}")
            if cache_time and datetime.utcnow() - cache_time < self._cache_ttl:
                return self._stats_cache[tenant_id_str]
        
        try:
            tenant = await self.get_tenant(tenant_id)
            if not tenant:
                return None
            
            async with self.db_client.get_async_session() as session:
                schema_name = self.db_client.get_tenant_schema_name(tenant_id)
                
                # Get counts from tenant tables
                queries = {
                    "user_count": f"SELECT COUNT(*) FROM users WHERE tenant_id = '{tenant_id}'",
                    "conversation_count": f"SELECT COUNT(*) FROM {schema_name}.conversations",
                    "memory_entry_count": f"SELECT COUNT(*) FROM {schema_name}.memory_entries",
                    "plugin_execution_count": f"SELECT COUNT(*) FROM {schema_name}.plugin_executions"
                }
                
                stats_data = {}
                for key, query in queries.items():
                    result = await session.execute(text(query))
                    stats_data[key] = result.scalar() or 0
                
                # Get storage usage
                storage_query = text(f"""
                    SELECT COALESCE(
                        SUM(pg_total_relation_size(schemaname||'.'||tablename))::bigint / (1024*1024), 
                        0
                    )
                    FROM pg_tables WHERE schemaname = :schema_name
                """)
                result = await session.execute(storage_query, {"schema_name": schema_name})
                storage_used_mb = float(result.scalar() or 0)
                
                # Get last activity
                activity_query = text(f"""
                    SELECT MAX(created_at) FROM (
                        SELECT created_at FROM {schema_name}.conversations
                        UNION ALL
                        SELECT created_at FROM {schema_name}.memory_entries
                        UNION ALL
                        SELECT created_at FROM {schema_name}.plugin_executions
                    ) activities
                """)
                result = await session.execute(activity_query)
                last_activity = result.scalar()
                
                stats = TenantStats(
                    tenant_id=tenant_id_str,
                    user_count=stats_data["user_count"],
                    conversation_count=stats_data["conversation_count"],
                    memory_entry_count=stats_data["memory_entry_count"],
                    plugin_execution_count=stats_data["plugin_execution_count"],
                    storage_used_mb=storage_used_mb,
                    last_activity=last_activity,
                    created_at=tenant.created_at
                )
                
                # Cache the stats
                self._stats_cache[tenant_id_str] = stats
                self._last_cache_update[f"stats_{tenant_id_str}"] = datetime.utcnow()
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get tenant stats for {tenant_id}: {e}")
            return None
    
    async def list_tenants(
        self,
        active_only: bool = True,
        limit: int = 100,
        offset: int = 0
    ) -> List[Tenant]:
        """List tenants with pagination.
        
        Args:
            active_only: Only return active tenants
            limit: Maximum number of tenants to return
            offset: Number of tenants to skip
            
        Returns:
            List of tenants
        """
        try:
            async with self.db_client.get_async_session() as session:
                query = select(Tenant).order_by(Tenant.created_at.desc())
                
                if active_only:
                    query = query.where(Tenant.is_active == True)
                
                query = query.limit(limit).offset(offset)
                
                result = await session.execute(query)
                return result.scalars().all()
                
        except Exception as e:
            logger.error(f"Failed to list tenants: {e}")
            return []
    
    async def check_tenant_limits(
        self,
        tenant_id: Union[str, uuid.UUID],
        resource_type: str
    ) -> Dict[str, Any]:
        """Check if tenant is within resource limits.
        
        Args:
            tenant_id: Tenant ID
            resource_type: Type of resource to check
            
        Returns:
            Limit check results
        """
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return {"error": "Tenant not found"}
        
        stats = await self.get_tenant_stats(tenant_id)
        if not stats:
            return {"error": "Could not get tenant stats"}
        
        limits = tenant.settings.get("limits", {})
        
        # Map resource types to stats and limits
        resource_map = {
            "users": ("user_count", "max_users"),
            "conversations": ("conversation_count", "max_conversations"),
            "memory_entries": ("memory_entry_count", "max_memory_entries"),
            "storage": ("storage_used_mb", "storage_mb")
        }
        
        if resource_type not in resource_map:
            return {"error": f"Unknown resource type: {resource_type}"}
        
        stat_key, limit_key = resource_map[resource_type]
        current_usage = getattr(stats, stat_key, 0)
        limit = limits.get(limit_key, 0)
        
        # -1 means unlimited
        if limit == -1:
            return {
                "resource_type": resource_type,
                "current_usage": current_usage,
                "limit": "unlimited",
                "within_limit": True,
                "usage_percentage": 0
            }
        
        within_limit = current_usage < limit
        usage_percentage = (current_usage / limit * 100) if limit > 0 else 100
        
        return {
            "resource_type": resource_type,
            "current_usage": current_usage,
            "limit": limit,
            "within_limit": within_limit,
            "usage_percentage": usage_percentage,
            "remaining": max(0, limit - current_usage)
        }
    
    async def _initialize_tenant_vectors(self, tenant_id: Union[str, uuid.UUID]):
        """Initialize vector collections for tenant."""
        if not self.milvus_client:
            return
        
        try:
            collection_name = f"tenant_{str(tenant_id).replace('-', '_')}"
            
            # Create collection for tenant memories
            await self.milvus_client.create_collection(
                collection_name=collection_name,
                dimension=384,  # Default embedding dimension
                description=f"Memory vectors for tenant {tenant_id}"
            )
            
            logger.info(f"Initialized vector collection for tenant {tenant_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize vectors for tenant {tenant_id}: {e}")
    
    async def _cleanup_tenant_vectors(self, tenant_id: Union[str, uuid.UUID]):
        """Cleanup vector collections for tenant."""
        if not self.milvus_client:
            return
        
        try:
            collection_name = f"tenant_{str(tenant_id).replace('-', '_')}"
            await self.milvus_client.drop_collection(collection_name)
            logger.info(f"Cleaned up vector collection for tenant {tenant_id}")
            
        except Exception as e:
            logger.error(f"Failed to cleanup vectors for tenant {tenant_id}: {e}")
    
    async def _cleanup_failed_tenant(self, tenant_id: Union[str, uuid.UUID]):
        """Cleanup after failed tenant creation."""
        try:
            # Drop schema if it was created
            self.db_client.drop_tenant_schema(tenant_id)
            
            # Cleanup vectors if they were created
            if self.milvus_client:
                await self._cleanup_tenant_vectors(tenant_id)
            
            logger.info(f"Cleaned up failed tenant creation for {tenant_id}")
            
        except Exception as e:
            logger.error(f"Failed to cleanup failed tenant {tenant_id}: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on tenant management system.
        
        Returns:
            Health check results
        """
        try:
            # Check database connectivity
            db_health = self.db_client.health_check()
            
            # Check tenant count
            tenants = await self.list_tenants(limit=1)
            tenant_count = len(tenants)
            
            # Check vector database if available
            vector_health = None
            if self.milvus_client:
                try:
                    vector_health = await self.milvus_client.health_check()
                except Exception as e:
                    vector_health = {"status": "unhealthy", "error": str(e)}
            
            return {
                "status": "healthy" if db_health["status"] == "healthy" else "unhealthy",
                "database": db_health,
                "vector_database": vector_health,
                "tenant_count": tenant_count,
                "cache_size": len(self._tenant_cache),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }