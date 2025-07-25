"""
Backend Integration Service Adapters
Provides seamless integration between Streamlit UI and existing AI Karen backend services.
"""

import asyncio
import logging
import uuid
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import streamlit as st

# Import existing backend services
try:
    from src.ai_karen_engine.database.memory_manager import MemoryManager, MemoryQuery, MemoryEntry
    from src.ai_karen_engine.plugin_manager import PluginManager, get_plugin_manager
    from src.ai_karen_engine.database.tenant_manager import TenantManager
    from src.ai_karen_engine.database.conversation_manager import ConversationManager
    from src.ui_logic.ui_core_logic import get_page_manifest, dispatch_page
    from src.ui_logic.config.pages_manifest import PAGES
    from src.ui_logic.config.feature_flags import get_flag
    from src.ui_logic.hooks.rbac import check_rbac
except ImportError as e:
    logging.warning(f"Backend service import failed: {e}")
    # Create mock classes for development
    class MemoryManager:
        def __init__(self, *args, **kwargs): pass
        async def query_memories(self, *args, **kwargs): return []
        async def store_memory(self, *args, **kwargs): return "mock-id"
        async def get_memory_stats(self, *args, **kwargs): return {}
    
    class PluginManager:
        def __init__(self, *args, **kwargs): pass
        async def run_plugin(self, *args, **kwargs): return "mock-result", "", ""
    
    def get_plugin_manager(): return PluginManager()
    def get_page_manifest(*args, **kwargs): return []
    def dispatch_page(*args, **kwargs): return lambda: None
    PAGES = []
    def get_flag(flag): return True
    def check_rbac(ctx, roles): return True

logger = logging.getLogger(__name__)


@dataclass
class ServiceConfig:
    """Configuration for backend services."""
    tenant_id: str = "default"
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    enable_caching: bool = True
    cache_ttl: int = 300  # 5 minutes


class BackendServiceAdapter:
    """Base adapter for backend services with common functionality."""
    
    def __init__(self, config: ServiceConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def get_user_context(self) -> Dict[str, Any]:
        """Get user context from session state."""
        return {
            "user_id": self.config.user_id or st.session_state.get("user_id", "anonymous"),
            "tenant_id": self.config.tenant_id,
            "session_id": self.config.session_id or st.session_state.get("session_id"),
            "roles": st.session_state.get("roles", ["user"]),
            "permissions": st.session_state.get("permissions", {}),
            "username": st.session_state.get("username", "User")
        }
    
    def handle_error(self, error: Exception, operation: str) -> None:
        """Handle and log errors consistently."""
        self.logger.error(f"Error in {operation}: {error}")
        st.error(f"❌ {operation} failed: {str(error)}")


class MemoryServiceAdapter(BackendServiceAdapter):
    """Adapter for memory management services."""
    
    def __init__(self, config: ServiceConfig, memory_manager: Optional[MemoryManager] = None):
        super().__init__(config)
        self.memory_manager = memory_manager
        self._cache = {}
    
    async def store_memory(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> Optional[str]:
        """Store a memory entry."""
        try:
            if not self.memory_manager:
                self.logger.warning("Memory manager not available")
                return None
            
            user_ctx = self.get_user_context()
            
            memory_id = await self.memory_manager.store_memory(
                tenant_id=self.config.tenant_id,
                content=content,
                user_id=user_ctx["user_id"],
                session_id=user_ctx["session_id"],
                metadata=metadata,
                tags=tags
            )
            
            # Clear cache
            if self.config.enable_caching:
                self._cache.clear()
            
            return memory_id
            
        except Exception as e:
            self.handle_error(e, "store memory")
            return None
    
    async def query_memories(
        self,
        query_text: str,
        top_k: int = 10,
        similarity_threshold: float = 0.7,
        tags: Optional[List[str]] = None,
        time_range: Optional[tuple] = None
    ) -> List[Dict[str, Any]]:
        """Query memories with semantic search."""
        try:
            if not self.memory_manager:
                return []
            
            # Check cache
            cache_key = f"query:{hash(query_text)}:{top_k}:{similarity_threshold}"
            if self.config.enable_caching and cache_key in self._cache:
                cached_result, timestamp = self._cache[cache_key]
                if datetime.now().timestamp() - timestamp < self.config.cache_ttl:
                    return cached_result
            
            user_ctx = self.get_user_context()
            
            query = MemoryQuery(
                text=query_text,
                user_id=user_ctx["user_id"],
                session_id=user_ctx["session_id"],
                tags=tags or [],
                top_k=top_k,
                similarity_threshold=similarity_threshold,
                time_range=time_range
            )
            
            memories = await self.memory_manager.query_memories(
                tenant_id=self.config.tenant_id,
                query=query
            )
            
            # Convert to dict format for UI
            result = [
                {
                    "id": memory.id,
                    "content": memory.content,
                    "metadata": memory.metadata,
                    "timestamp": memory.timestamp,
                    "similarity_score": memory.similarity_score,
                    "tags": memory.tags,
                    "user_id": memory.user_id,
                    "session_id": memory.session_id
                }
                for memory in memories
            ]
            
            # Cache result
            if self.config.enable_caching:
                self._cache[cache_key] = (result, datetime.now().timestamp())
            
            return result
            
        except Exception as e:
            self.handle_error(e, "query memories")
            return []
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        try:
            if not self.memory_manager:
                return {"error": "Memory manager not available"}
            
            stats = await self.memory_manager.get_memory_stats(self.config.tenant_id)
            return stats
            
        except Exception as e:
            self.handle_error(e, "get memory stats")
            return {"error": str(e)}
    
    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory entry."""
        try:
            if not self.memory_manager:
                return False
            
            success = await self.memory_manager.delete_memory(
                tenant_id=self.config.tenant_id,
                memory_id=memory_id
            )
            
            # Clear cache
            if self.config.enable_caching:
                self._cache.clear()
            
            return success
            
        except Exception as e:
            self.handle_error(e, "delete memory")
            return False


class PluginServiceAdapter(BackendServiceAdapter):
    """Adapter for plugin management services."""
    
    def __init__(self, config: ServiceConfig, plugin_manager: Optional[PluginManager] = None):
        super().__init__(config)
        self.plugin_manager = plugin_manager or get_plugin_manager()
    
    async def run_plugin(
        self,
        plugin_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a plugin with parameters."""
        try:
            user_ctx = self.get_user_context()
            
            result, stdout, stderr = await self.plugin_manager.run_plugin(
                name=plugin_name,
                params=parameters,
                user_ctx=user_ctx
            )
            
            return {
                "success": True,
                "result": result,
                "stdout": stdout,
                "stderr": stderr,
                "plugin_name": plugin_name,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.handle_error(e, f"run plugin {plugin_name}")
            return {
                "success": False,
                "error": str(e),
                "plugin_name": plugin_name,
                "timestamp": datetime.now().isoformat()
            }
    
    def get_available_plugins(self) -> List[Dict[str, Any]]:
        """Get list of available plugins."""
        try:
            # This would typically come from the plugin registry
            # For now, return a mock list
            return [
                {
                    "name": "hello-world",
                    "description": "Simple hello world plugin",
                    "category": "examples",
                    "enabled": True,
                    "version": "1.0.0"
                },
                {
                    "name": "autonomous-task-handler",
                    "description": "Handle autonomous tasks",
                    "category": "automation",
                    "enabled": True,
                    "version": "1.0.0"
                },
                {
                    "name": "git-merge-safe",
                    "description": "Safe git merge operations",
                    "category": "automation",
                    "enabled": True,
                    "version": "1.0.0"
                }
            ]
            
        except Exception as e:
            self.handle_error(e, "get available plugins")
            return []


class PageServiceAdapter(BackendServiceAdapter):
    """Adapter for UI page management services."""
    
    def __init__(self, config: ServiceConfig):
        super().__init__(config)
    
    def get_available_pages(self) -> List[Dict[str, Any]]:
        """Get list of available pages based on user context."""
        try:
            user_ctx = self.get_user_context()
            pages = get_page_manifest(user_ctx)
            
            # Convert to UI-friendly format
            ui_pages = []
            for page in pages:
                if page.get("enabled", True):
                    ui_pages.append({
                        "route": page.get("route", ""),
                        "label": page.get("label", ""),
                        "icon": page.get("icon", "📄"),
                        "description": page.get("description", ""),
                        "category": page.get("category", "general"),
                        "roles": page.get("roles", []),
                        "feature_flag": page.get("feature_flag")
                    })
            
            return ui_pages
            
        except Exception as e:
            self.handle_error(e, "get available pages")
            return []
    
    def render_page(self, page_route: str) -> Any:
        """Render a specific page."""
        try:
            user_ctx = self.get_user_context()
            handler = dispatch_page(page_route, user_ctx)
            
            if handler:
                return handler(user_ctx=user_ctx)
            else:
                st.warning(f"Page handler not found for: {page_route}")
                return None
                
        except Exception as e:
            self.handle_error(e, f"render page {page_route}")
            return None
    
    def check_page_access(self, page_route: str) -> bool:
        """Check if user has access to a specific page."""
        try:
            user_ctx = self.get_user_context()
            
            # Find page in manifest
            page_info = next((p for p in PAGES if p.get("route") == page_route), None)
            if not page_info:
                return False
            
            # Check feature flag
            feature_flag = page_info.get("feature_flag")
            if feature_flag and not get_flag(feature_flag):
                return False
            
            # Check RBAC
            required_roles = page_info.get("roles", [])
            if required_roles and not check_rbac(user_ctx, required_roles):
                return False
            
            return True
            
        except Exception as e:
            self.handle_error(e, f"check page access {page_route}")
            return False


class AnalyticsServiceAdapter(BackendServiceAdapter):
    """Adapter for analytics and monitoring services."""
    
    def __init__(self, config: ServiceConfig):
        super().__init__(config)
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics."""
        try:
            # Mock system metrics - in production this would come from monitoring services
            return {
                "cpu_usage": 45.2,
                "memory_usage": 68.5,
                "disk_usage": 32.1,
                "active_sessions": 12,
                "total_requests": 1547,
                "error_rate": 0.02,
                "response_time_avg": 0.3,
                "uptime_hours": 168.5,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.handle_error(e, "get system metrics")
            return {}
    
    async def get_usage_analytics(self, time_range: str = "24h") -> Dict[str, Any]:
        """Get usage analytics data."""
        try:
            # Mock analytics data
            return {
                "total_interactions": 234,
                "unique_users": 18,
                "popular_features": [
                    {"name": "Chat", "usage_count": 156},
                    {"name": "Memory", "usage_count": 89},
                    {"name": "Plugins", "usage_count": 67}
                ],
                "peak_hours": [9, 14, 16, 20],
                "user_satisfaction": 4.2,
                "time_range": time_range,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.handle_error(e, "get usage analytics")
            return {}


class IntegratedBackendService:
    """Main service that coordinates all backend adapters."""
    
    def __init__(self, tenant_id: str = "default"):
        self.config = ServiceConfig(tenant_id=tenant_id)
        
        # Initialize service adapters
        self.memory = MemoryServiceAdapter(self.config)
        self.plugins = PluginServiceAdapter(self.config)
        self.pages = PageServiceAdapter(self.config)
        self.analytics = AnalyticsServiceAdapter(self.config)
        
        self.logger = logging.getLogger(__name__)
    
    def update_user_context(self, user_id: str, session_id: str, roles: List[str]):
        """Update user context across all services."""
        self.config.user_id = user_id
        self.config.session_id = session_id
        
        # Update session state
        st.session_state.update({
            "user_id": user_id,
            "session_id": session_id,
            "roles": roles
        })
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all backend services."""
        health_status = {
            "overall": "healthy",
            "services": {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Check memory service
        try:
            memory_stats = await self.memory.get_memory_stats()
            health_status["services"]["memory"] = {
                "status": "healthy" if "error" not in memory_stats else "error",
                "details": memory_stats
            }
        except Exception as e:
            health_status["services"]["memory"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Check plugin service
        try:
            plugins = self.plugins.get_available_plugins()
            health_status["services"]["plugins"] = {
                "status": "healthy",
                "plugin_count": len(plugins)
            }
        except Exception as e:
            health_status["services"]["plugins"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Check page service
        try:
            pages = self.pages.get_available_pages()
            health_status["services"]["pages"] = {
                "status": "healthy",
                "page_count": len(pages)
            }
        except Exception as e:
            health_status["services"]["pages"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Determine overall health
        service_statuses = [s["status"] for s in health_status["services"].values()]
        if "error" in service_statuses:
            health_status["overall"] = "degraded" if "healthy" in service_statuses else "error"
        
        return health_status


# Global service instance
_backend_service: Optional[IntegratedBackendService] = None


def get_backend_service(tenant_id: str = "default") -> IntegratedBackendService:
    """Get or create the global backend service instance."""
    global _backend_service
    if _backend_service is None or _backend_service.config.tenant_id != tenant_id:
        _backend_service = IntegratedBackendService(tenant_id)
    return _backend_service


# Utility functions for Streamlit components
def run_async(coro):
    """Run async function in Streamlit context without leaking threads."""
    try:
        loop = asyncio.get_event_loop()
        new_loop = False
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        new_loop = True

    try:
        return loop.run_until_complete(coro)
    finally:
        if new_loop:
            # Ensure all executor threads from the loop are cleaned up
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()


@st.cache_data(ttl=300)  # Cache for 5 minutes
def cached_backend_call(service_method: str, *args, **kwargs):
    """Cache backend service calls to improve performance."""
    backend = get_backend_service()
    method = getattr(backend, service_method)
    
    if asyncio.iscoroutinefunction(method):
        return run_async(method(*args, **kwargs))
    else:
        return method(*args, **kwargs)