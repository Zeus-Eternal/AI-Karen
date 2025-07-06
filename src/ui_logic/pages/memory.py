"""
Kari Memory Page - Production Version
- Central hub for all memory-related components
- Features:
  * RBAC-aware component rendering
  * Session context management
  * Error boundaries for each component
  * Performance monitoring
  * Unified state management
"""

import streamlit as st
from typing import Dict, Any, Optional, List
import time
import traceback
import logging
from functools import wraps

# --- Configure logging ---
logger = logging.getLogger("kari.ui.memory_page")
logger.setLevel(logging.INFO)

# --- Import all panel components with error handling ---
try:
    from ui_logic.components.memory.knowledge_graph import render_knowledge_graph
    from ui_logic.components.memory.memory_analytics import render_memory_analytics
    from ui_logic.components.memory.profile_panel import render_profile_panel
    from ui_logic.components.memory.session_explorer import render_session_explorer
    from ui_logic.components.memory.memory_manager import render_memory_manager
except ImportError as e:
    logger.error(f"Component import failed: {str(e)}")
    raise

class MemoryPageError(Exception):
    """Base exception for memory page errors"""
    pass

class ComponentRenderError(MemoryPageError):
    """Raised when a component fails to render"""
    pass

def log_performance(func):
    """Decorator to log component render performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"Component {func.__name__} rendered in {duration:.2f}s")
            return result
        except Exception as e:
            logger.error(f"Component {func.__name__} failed after {time.time()-start_time:.2f}s: {e}")
            raise
    return wrapper

def with_error_boundary(func):
    """Decorator to provide error boundaries for components"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"Component {func.__name__} failed: {str(e)}\n{tb}")
            st.error(f"⚠️ {func.__name__} failed to load. Technical details have been logged.")
            if st.session_state.get("show_debug_info", False):
                with st.expander("Error Details (Debug)"):
                    st.code(tb)
            return None
    return wrapper

def get_user_context() -> Dict[str, Any]:
    """
    Get and validate user context from session state
    Returns:
        Dictionary containing:
        - user_id: str
        - roles: List[str]
        - permissions: Dict[str, bool]
        - session_id: str or None
    Raises:
        MemoryPageError: If session state is invalid
    """
    try:
        ctx = {
            "user_id": st.session_state.get("user_id", "anonymous"),
            "roles": st.session_state.get("roles", ["guest"]),
            "permissions": st.session_state.get("permissions", {}),
            "session_id": st.session_state.get("session_id"),
        }
        # Validate context
        if not isinstance(ctx["roles"], list):
            raise MemoryPageError("Invalid roles format in session context")
        return ctx
    except Exception as e:
        logger.error(f"Failed to get user context: {str(e)}")
        raise MemoryPageError("Session context validation failed") from e

def check_access(required_roles: List[str], user_ctx: Dict[str, Any]) -> bool:
    """
    Check if user has required roles/permissions
    Args:
        required_roles: List of roles that can access
        user_ctx: User context dictionary
    Returns:
        bool: True if access granted
    """
    if "admin" in user_ctx.get("roles", []):
        return True
    return any(role in user_ctx.get("roles", []) for role in required_roles)

@log_performance
@with_error_boundary
def render_component(component_func, user_ctx: Dict[str, Any], *args, **kwargs):
    """
    Safely render a component with context and error handling
    Args:
        component_func: Component render function
        user_ctx: User context dictionary
    """
    return component_func(user_ctx=user_ctx, *args, **kwargs)

def memory_page(user_ctx: Optional[Dict[str, Any]] = None):
    """
    Main memory page renderer
    Args:
        user_ctx: Optional pre-loaded user context
    """
    try:
        # Get or validate user context
        ctx = user_ctx if user_ctx else get_user_context()

        # Page header
        st.title("🧠 Kari Memory Center")
        st.markdown("""
            <style>
            .memory-header {
                font-size: 0.9em;
                color: #666;
                margin-bottom: 2em;
            }
            </style>
            <div class="memory-header">
            Central hub for Kari's memory systems – knowledge graph, session explorer,
            memory analytics, and profile management.
            </div>
            """, unsafe_allow_html=True)

        # Tab navigation
        tabs = st.tabs([
            "🗺️ Knowledge Graph", 
            "📊 Memory Analytics",
            "👤 Profile",
            "⏱️ Session Explorer",
            "⚙️ Memory Manager"
        ])

        # Knowledge Graph Tab
        with tabs[0]:
            if check_access(["user", "analyst", "admin"], ctx):
                render_component(render_knowledge_graph, ctx)
            else:
                st.warning("🔒 You don't have access to the Knowledge Graph.")

        # Memory Analytics Tab
        with tabs[1]:
            if check_access(["analyst", "admin"], ctx):
                render_component(render_memory_analytics, ctx)
            else:
                st.warning("🔒 Requires analyst or admin privileges.")

        # Profile Tab
        with tabs[2]:
            render_component(render_profile_panel, ctx)

        # Session Explorer Tab
        with tabs[3]:
            render_component(render_session_explorer, ctx)

        # Memory Manager Tab (Admin only)
        with tabs[4]:
            if check_access(["admin"], ctx):
                render_component(render_memory_manager, ctx)
            else:
                st.warning("🔒 Admin access required for Memory Manager.")

    except Exception as e:
        logger.critical(f"Memory page render failed: {str(e)}")
        st.error("🚨 The memory page encountered a critical error. Please try again later.")
        if st.session_state.get("show_debug_info", False):
            with st.expander("Technical Details"):
                st.code(traceback.format_exc())

# Example usage for dev/demo
if __name__ == "__main__":
    if "user_id" not in st.session_state:
        st.session_state.update({
            "user_id": "demo_user",
            "roles": ["user", "analyst"],
            "permissions": {
                "view_analytics": True,
                "edit_memory": False
            }
        })
    memory_page()
