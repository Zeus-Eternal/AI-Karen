"""
Premium Routing Configuration for AI Karen Enhanced UI
- Role-based page access control
- Dynamic navigation based on user permissions
- Page metadata and configuration
"""

from typing import Dict, Any, List, Callable
from helpers.rbac import check_permission

# Import premium page functions
try:
    from pages.premium_dashboard import premium_dashboard_page
    from pages.enhanced_chat import enhanced_chat_page
    from pages.advanced_analytics import advanced_analytics_page
    from pages.plugin_marketplace import plugin_marketplace_page
    from pages.system_monitoring import system_monitoring_page
    from pages.workflow_builder import workflow_builder_page
    from pages.user_management import user_management_page
    from pages.settings_advanced import settings_advanced_page
except ImportError:
    # Fallback functions if imports fail
    def premium_dashboard_page(user_ctx: Dict[str, Any]):
        import streamlit as st
        st.title("🏢 Executive Dashboard")
        st.info("Premium dashboard implementation coming in next task!")

    def enhanced_chat_page(user_ctx: Dict[str, Any]):
        import streamlit as st
        st.title("💬 Enhanced Chat Interface")
        st.info("Enhanced chat implementation coming in next task!")

    def advanced_analytics_page(user_ctx: Dict[str, Any]):
        import streamlit as st
        st.title("📊 Advanced Analytics")
        st.info("Advanced analytics implementation coming in next task!")

    def plugin_marketplace_page(user_ctx: Dict[str, Any]):
        import streamlit as st
        st.title("🧩 Plugin Marketplace")
        st.info("Plugin marketplace implementation coming in next task!")

    def system_monitoring_page(user_ctx: Dict[str, Any]):
        import streamlit as st
        st.title("📡 System Monitoring")
        st.info("System monitoring implementation coming in next task!")

    def workflow_builder_page(user_ctx: Dict[str, Any]):
        import streamlit as st
        st.title("🔄 Workflow Builder")
        st.info("Workflow builder implementation coming in next task!")

    def user_management_page(user_ctx: Dict[str, Any]):
        import streamlit as st
        st.title("👥 User Management")
        st.info("User management implementation coming in next task!")

    def settings_advanced_page(user_ctx: Dict[str, Any]):
        import streamlit as st
        st.title("⚙️ Advanced Settings")
        st.info("Advanced settings implementation coming in next task!")

# Import existing pages from the current system
try:
    from ui_logic.pages.home import home_page
    from ui_logic.pages.chat import chat_page
    from ui_logic.pages.analytics import analytics_page
    from ui_logic.pages.plugins import plugins_page
    from ui_logic.pages.memory import memory_page
    from ui_logic.pages.admin import admin_page
    from ui_logic.pages.settings import settings_page
    from ui_logic.pages.presence import page as presence_page
except ImportError:
    # Fallback functions if imports fail
    def home_page(user_ctx: Dict[str, Any]):
        import streamlit as st
        st.title("🏠 Home")
        st.write("Welcome to AI Karen!")
    
    def chat_page(user_ctx: Dict[str, Any]):
        import streamlit as st
        st.title("💬 Chat")
        st.write("Chat interface")
    
    def analytics_page(user_ctx: Dict[str, Any]):
        import streamlit as st
        st.title("📊 Analytics")
        st.write("Analytics dashboard")
    
    def plugins_page(user_ctx: Dict[str, Any]):
        import streamlit as st
        st.title("🧩 Plugins")
        st.write("Plugin management")
    
    def memory_page(user_ctx: Dict[str, Any]):
        import streamlit as st
        st.title("🧠 Memory")
        st.write("Memory management")
    
    def admin_page(user_ctx: Dict[str, Any]):
        import streamlit as st
        st.title("🛡️ Admin")
        st.write("Administration panel")
    
    def settings_page(user_ctx: Dict[str, Any]):
        import streamlit as st
        st.title("⚙️ Settings")
        st.write("Settings panel")
    
    def presence_page(user_ctx: Dict[str, Any]):
        import streamlit as st
        st.title("👥 Presence")
        st.write("Presence management")

# Premium page configuration with metadata
PREMIUM_PAGES = {
    # Executive Dashboard
    "dashboard": {
        "title": "Executive Dashboard",
        "icon": "📊",
        "description": "High-level KPIs and system overview",
        "category": "executive",
        "roles": ["admin", "executive", "manager"],
        "permissions": ["dashboard.view"],
        "page_function": premium_dashboard_page,
        "new": False,
        "beta": False,
        "order": 1
    },
    
    "reports": {
        "title": "Executive Reports", 
        "icon": "📋",
        "description": "Comprehensive business reports and insights",
        "category": "executive",
        "roles": ["admin", "executive", "manager"],
        "permissions": ["reports.view"],
        "page_function": premium_dashboard_page,  # Placeholder
        "new": False,
        "beta": False,
        "order": 2
    },
    
    "kpis": {
        "title": "KPI Monitoring",
        "icon": "🎯", 
        "description": "Key performance indicators tracking",
        "category": "executive",
        "roles": ["admin", "executive", "analyst"],
        "permissions": ["kpis.view"],
        "page_function": premium_dashboard_page,  # Placeholder
        "new": False,
        "beta": False,
        "order": 3
    },
    
    # Operations
    "chat": {
        "title": "Enhanced Chat",
        "icon": "💬",
        "description": "Advanced AI conversation interface with rich features",
        "category": "operations",
        "roles": ["user", "admin", "operator"],
        "permissions": ["chat.access"],
        "page_function": enhanced_chat_page,
        "new": True,
        "beta": False,
        "order": 10
    },
    
    "memory": {
        "title": "Memory Management",
        "icon": "🧠",
        "description": "AI memory and context management system",
        "category": "operations", 
        "roles": ["user", "admin", "operator"],
        "permissions": ["memory.access"],
        "page_function": memory_page,
        "new": False,
        "beta": False,
        "order": 11
    },
    
    "workflows": {
        "title": "Workflow Builder",
        "icon": "🔄",
        "description": "Visual workflow creation and automation",
        "category": "operations",
        "roles": ["admin", "developer", "operator"],
        "permissions": ["workflows.manage"],
        "page_function": workflow_builder_page,
        "new": False,
        "beta": True,
        "order": 12
    },
    
    "automation": {
        "title": "Automation Hub",
        "icon": "🤖",
        "description": "Automated task management and scheduling",
        "category": "operations",
        "roles": ["admin", "operator"],
        "permissions": ["automation.access"],
        "page_function": workflow_builder_page,  # Placeholder
        "new": False,
        "beta": False,
        "order": 13
    },
    
    "presence": {
        "title": "Presence Management",
        "icon": "👥",
        "description": "User presence and collaboration tools",
        "category": "operations",
        "roles": ["user", "admin", "operator"],
        "permissions": ["presence.access"],
        "page_function": presence_page,
        "new": False,
        "beta": False,
        "order": 14
    },
    
    # Development
    "plugins": {
        "title": "Plugin Marketplace",
        "icon": "🧩",
        "description": "Browse, install, and manage plugins",
        "category": "development",
        "roles": ["admin", "developer"],
        "permissions": ["plugins.manage"],
        "page_function": plugin_marketplace_page,
        "new": False,
        "beta": False,
        "order": 20
    },
    
    "api": {
        "title": "API Explorer",
        "icon": "🔌",
        "description": "API testing and documentation interface",
        "category": "development",
        "roles": ["admin", "developer"],
        "permissions": ["api.access"],
        "page_function": plugin_marketplace_page,  # Placeholder
        "new": False,
        "beta": True,
        "order": 21
    },
    
    "debugging": {
        "title": "Debug Console",
        "icon": "🐛",
        "description": "System debugging and diagnostics tools",
        "category": "development",
        "roles": ["admin", "developer"],
        "permissions": ["debug.access"],
        "page_function": system_monitoring_page,
        "new": False,
        "beta": False,
        "order": 22
    },
    
    # Administration
    "users": {
        "title": "User Management",
        "icon": "👥",
        "description": "Manage users, roles, and permissions",
        "category": "administration",
        "roles": ["admin"],
        "permissions": ["users.manage"],
        "page_function": user_management_page,
        "new": False,
        "beta": False,
        "order": 30
    },
    
    "security": {
        "title": "Security Center",
        "icon": "🔒",
        "description": "Security settings and audit logs",
        "category": "administration",
        "roles": ["admin", "security"],
        "permissions": ["security.manage"],
        "page_function": user_management_page,  # Placeholder
        "new": False,
        "beta": False,
        "order": 31
    },
    
    "monitoring": {
        "title": "System Monitoring",
        "icon": "📡",
        "description": "Real-time system health and performance monitoring",
        "category": "administration",
        "roles": ["admin", "operator"],
        "permissions": ["monitoring.view"],
        "page_function": system_monitoring_page,
        "new": False,
        "beta": False,
        "order": 32
    },
    
    "settings": {
        "title": "Advanced Settings",
        "icon": "⚙️",
        "description": "System configuration and user preferences",
        "category": "administration",
        "roles": ["admin", "user"],
        "permissions": ["settings.access"],
        "page_function": settings_advanced_page,
        "new": False,
        "beta": False,
        "order": 33
    },
    
    "admin": {
        "title": "System Administration",
        "icon": "🛡️",
        "description": "Advanced system administration tools",
        "category": "administration",
        "roles": ["admin"],
        "permissions": ["admin.access"],
        "page_function": admin_page,
        "new": False,
        "beta": False,
        "order": 34
    },
    
    # Analytics
    "analytics": {
        "title": "Advanced Analytics",
        "icon": "📈",
        "description": "Comprehensive data analysis and reporting",
        "category": "analytics",
        "roles": ["admin", "analyst", "manager"],
        "permissions": ["analytics.view"],
        "page_function": advanced_analytics_page,
        "new": False,
        "beta": False,
        "order": 40
    },
    
    "insights": {
        "title": "AI Insights",
        "icon": "🔍",
        "description": "AI-powered business insights and recommendations",
        "category": "analytics",
        "roles": ["admin", "analyst", "executive"],
        "permissions": ["insights.view"],
        "page_function": advanced_analytics_page,  # Placeholder
        "new": True,
        "beta": False,
        "order": 41
    },
    
    "performance": {
        "title": "Performance Analytics",
        "icon": "⚡",
        "description": "System and user performance metrics",
        "category": "analytics",
        "roles": ["admin", "analyst"],
        "permissions": ["performance.view"],
        "page_function": advanced_analytics_page,  # Placeholder
        "new": False,
        "beta": False,
        "order": 42
    },
    
    # Legacy/Compatibility pages
    "home": {
        "title": "Home",
        "icon": "🏠",
        "description": "Welcome page and quick overview",
        "category": "general",
        "roles": ["user", "admin"],
        "permissions": [],
        "page_function": home_page,
        "new": False,
        "beta": False,
        "order": 0
    }
}

# Create the page map for routing
PREMIUM_PAGE_MAP = {
    page_key: page_config["page_function"]
    for page_key, page_config in PREMIUM_PAGES.items()
}

def get_user_pages(user_ctx: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Get pages accessible to the current user based on roles and permissions."""
    accessible_pages = {}
    user_roles = user_ctx.get('roles', ['user'])
    
    for page_key, page_config in PREMIUM_PAGES.items():
        # Check role-based access
        has_role = any(role in user_roles for role in page_config['roles'])
        
        # Check permission-based access
        has_permission = True
        if page_config['permissions']:
            has_permission = any(
                check_permission(user_ctx, perm) for perm in page_config['permissions']
            )
        
        if has_role and has_permission:
            accessible_pages[page_key] = page_config
    
    return accessible_pages

def get_pages_by_category(user_ctx: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """Get pages grouped by category for the current user."""
    accessible_pages = get_user_pages(user_ctx)
    categories = {}
    
    for page_key, page_config in accessible_pages.items():
        category = page_config['category']
        if category not in categories:
            categories[category] = []
        
        # Add page key to config for reference
        page_with_key = {**page_config, 'key': page_key}
        categories[category].append(page_with_key)
    
    # Sort pages within each category by order
    for category in categories:
        categories[category].sort(key=lambda x: x['order'])
    
    return categories

def get_page_config(page_key: str) -> Dict[str, Any]:
    """Get configuration for a specific page."""
    return PREMIUM_PAGES.get(page_key, {})

def is_page_accessible(page_key: str, user_ctx: Dict[str, Any]) -> bool:
    """Check if a page is accessible to the current user."""
    if page_key not in PREMIUM_PAGES:
        return False
    
    page_config = PREMIUM_PAGES[page_key]
    user_roles = user_ctx.get('roles', ['user'])
    
    # Check role-based access
    has_role = any(role in user_roles for role in page_config['roles'])
    
    # Check permission-based access
    has_permission = True
    if page_config['permissions']:
        has_permission = any(
            check_permission(user_ctx, perm) for perm in page_config['permissions']
        )
    
    return has_role and has_permission

def get_default_page(user_ctx: Dict[str, Any]) -> str:
    """Get the default page for the current user."""
    accessible_pages = get_user_pages(user_ctx)
    
    # Priority order for default page selection
    preferred_defaults = ['dashboard', 'home', 'chat', 'analytics']
    
    for page_key in preferred_defaults:
        if page_key in accessible_pages:
            return page_key
    
    # If none of the preferred pages are accessible, return the first available page
    if accessible_pages:
        return min(accessible_pages.keys(), key=lambda x: accessible_pages[x]['order'])
    
    return 'home'  # Ultimate fallback

def get_navigation_breadcrumbs(page_key: str) -> List[Dict[str, str]]:
    """Get breadcrumb navigation for a page."""
    if page_key not in PREMIUM_PAGES:
        return []
    
    page_config = PREMIUM_PAGES[page_key]
    category = page_config['category']
    
    # Category display names
    category_names = {
        'executive': 'Executive',
        'operations': 'Operations', 
        'development': 'Development',
        'administration': 'Administration',
        'analytics': 'Analytics',
        'general': 'General'
    }
    
    breadcrumbs = [
        {'title': 'Home', 'key': 'home'},
        {'title': category_names.get(category, category.title()), 'key': category},
        {'title': page_config['title'], 'key': page_key}
    ]
    
    return breadcrumbs

# Export the main routing components
__all__ = [
    'PREMIUM_PAGE_MAP',
    'PREMIUM_PAGES',
    'get_user_pages',
    'get_pages_by_category',
    'get_page_config',
    'is_page_accessible',
    'get_default_page',
    'get_navigation_breadcrumbs'
]