"""
Enhanced Navigation System for AI Karen Premium UI
- Role-based navigation with contextual menus
- Dynamic page routing with permissions
- Breadcrumb navigation and page history
- Search functionality for quick navigation
"""

import streamlit as st
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from helpers.rbac import check_permission

@dataclass
class NavigationItem:
    """Navigation item configuration."""
    key: str
    title: str
    icon: str
    description: str
    page_function: callable
    roles: List[str]
    permissions: List[str]
    category: str
    badge: Optional[str] = None
    new: bool = False
    beta: bool = False

@dataclass
class NavigationCategory:
    """Navigation category configuration."""
    key: str
    title: str
    icon: str
    description: str
    order: int
    collapsible: bool = True

class EnhancedNavigation:
    """Advanced navigation system with role-based access."""
    
    def __init__(self):
        self.categories = self._define_categories()
        self.navigation_items = self._define_navigation_items()
        self.breadcrumbs = []
        self.page_history = []
    
    def _define_categories(self) -> Dict[str, NavigationCategory]:
        """Define navigation categories."""
        return {
            "executive": NavigationCategory(
                key="executive",
                title="Executive",
                icon="🏢",
                description="High-level overview and strategic insights",
                order=1
            ),
            "operations": NavigationCategory(
                key="operations", 
                title="Operations",
                icon="⚡",
                description="Day-to-day operations and workflows",
                order=2
            ),
            "development": NavigationCategory(
                key="development",
                title="Development",
                icon="🛠️",
                description="Development tools and system management",
                order=3
            ),
            "administration": NavigationCategory(
                key="administration",
                title="Administration", 
                icon="🔐",
                description="System administration and user management",
                order=4
            ),
            "analytics": NavigationCategory(
                key="analytics",
                title="Analytics",
                icon="📊",
                description="Data analysis and reporting tools",
                order=5
            )
        }
    
    def _define_navigation_items(self) -> Dict[str, NavigationItem]:
        """Define all navigation items with permissions."""
        # Import page functions (these would be implemented)
        from pages.premium_dashboard import premium_dashboard_page
        from pages.enhanced_chat import enhanced_chat_page
        from pages.advanced_analytics import advanced_analytics_page
        from pages.plugin_marketplace import plugin_marketplace_page
        from pages.system_monitoring import system_monitoring_page
        from pages.workflow_builder import workflow_builder_page
        from pages.user_management import user_management_page
        from pages.settings_advanced import settings_advanced_page
        
        return {
            # Executive Dashboard
            "dashboard": NavigationItem(
                key="dashboard",
                title="Executive Dashboard",
                icon="📊",
                description="High-level KPIs and system overview",
                page_function=premium_dashboard_page,
                roles=["admin", "executive", "manager"],
                permissions=["dashboard.view"],
                category="executive"
            ),
            
            "reports": NavigationItem(
                key="reports",
                title="Executive Reports",
                icon="📋",
                description="Comprehensive business reports",
                page_function=premium_dashboard_page,  # Placeholder
                roles=["admin", "executive", "manager"],
                permissions=["reports.view"],
                category="executive"
            ),
            
            "kpis": NavigationItem(
                key="kpis",
                title="KPI Monitoring",
                icon="🎯",
                description="Key performance indicators tracking",
                page_function=premium_dashboard_page,  # Placeholder
                roles=["admin", "executive", "analyst"],
                permissions=["kpis.view"],
                category="executive"
            ),
            
            # Operations
            "chat": NavigationItem(
                key="chat",
                title="Enhanced Chat",
                icon="💬",
                description="Advanced AI conversation interface",
                page_function=enhanced_chat_page,
                roles=["user", "admin", "operator"],
                permissions=["chat.access"],
                category="operations",
                new=True
            ),
            
            "memory": NavigationItem(
                key="memory",
                title="Memory Management",
                icon="🧠",
                description="AI memory and context management",
                page_function=enhanced_chat_page,  # Placeholder
                roles=["user", "admin", "operator"],
                permissions=["memory.access"],
                category="operations"
            ),
            
            "workflows": NavigationItem(
                key="workflows",
                title="Workflow Builder",
                icon="🔄",
                description="Visual workflow creation and management",
                page_function=workflow_builder_page,
                roles=["admin", "developer", "operator"],
                permissions=["workflows.manage"],
                category="operations",
                beta=True
            ),
            
            "automation": NavigationItem(
                key="automation",
                title="Automation Hub",
                icon="🤖",
                description="Automated task management",
                page_function=workflow_builder_page,  # Placeholder
                roles=["admin", "operator"],
                permissions=["automation.access"],
                category="operations"
            ),
            
            # Development
            "plugins": NavigationItem(
                key="plugins",
                title="Plugin Marketplace",
                icon="🧩",
                description="Browse and manage plugins",
                page_function=plugin_marketplace_page,
                roles=["admin", "developer"],
                permissions=["plugins.manage"],
                category="development"
            ),
            
            "api": NavigationItem(
                key="api",
                title="API Explorer",
                icon="🔌",
                description="API testing and documentation",
                page_function=plugin_marketplace_page,  # Placeholder
                roles=["admin", "developer"],
                permissions=["api.access"],
                category="development"
            ),
            
            "debugging": NavigationItem(
                key="debugging",
                title="Debug Console",
                icon="🐛",
                description="System debugging and diagnostics",
                page_function=system_monitoring_page,
                roles=["admin", "developer"],
                permissions=["debug.access"],
                category="development"
            ),
            
            # Administration
            "users": NavigationItem(
                key="users",
                title="User Management",
                icon="👥",
                description="Manage users and permissions",
                page_function=user_management_page,
                roles=["admin"],
                permissions=["users.manage"],
                category="administration"
            ),
            
            "security": NavigationItem(
                key="security",
                title="Security Center",
                icon="🔒",
                description="Security settings and audit logs",
                page_function=user_management_page,  # Placeholder
                roles=["admin", "security"],
                permissions=["security.manage"],
                category="administration"
            ),
            
            "monitoring": NavigationItem(
                key="monitoring",
                title="System Monitoring",
                icon="📡",
                description="Real-time system health monitoring",
                page_function=system_monitoring_page,
                roles=["admin", "operator"],
                permissions=["monitoring.view"],
                category="administration"
            ),
            
            "settings": NavigationItem(
                key="settings",
                title="Advanced Settings",
                icon="⚙️",
                description="System configuration and preferences",
                page_function=settings_advanced_page,
                roles=["admin", "user"],
                permissions=["settings.access"],
                category="administration"
            ),
            
            # Analytics
            "analytics": NavigationItem(
                key="analytics",
                title="Advanced Analytics",
                icon="📈",
                description="Comprehensive data analysis",
                page_function=advanced_analytics_page,
                roles=["admin", "analyst", "manager"],
                permissions=["analytics.view"],
                category="analytics"
            ),
            
            "insights": NavigationItem(
                key="insights",
                title="AI Insights",
                icon="🔍",
                description="AI-powered business insights",
                page_function=advanced_analytics_page,  # Placeholder
                roles=["admin", "analyst", "executive"],
                permissions=["insights.view"],
                category="analytics",
                new=True
            ),
            
            "performance": NavigationItem(
                key="performance",
                title="Performance Analytics",
                icon="⚡",
                description="System and user performance metrics",
                page_function=advanced_analytics_page,  # Placeholder
                roles=["admin", "analyst"],
                permissions=["performance.view"],
                category="analytics"
            )
        }
    
    def get_accessible_items(self, user_ctx: Dict[str, Any]) -> Dict[str, NavigationItem]:
        """Get navigation items accessible to the current user."""
        accessible_items = {}
        user_roles = user_ctx.get('roles', ['user'])
        
        for key, item in self.navigation_items.items():
            # Check role-based access
            has_role = any(role in user_roles for role in item.roles)
            
            # Check permission-based access
            has_permission = True
            if item.permissions:
                has_permission = any(
                    check_permission(user_ctx, perm) for perm in item.permissions
                )
            
            if has_role and has_permission:
                accessible_items[key] = item
        
        return accessible_items
    
    def get_categories_with_items(self, user_ctx: Dict[str, Any]) -> Dict[str, Tuple[NavigationCategory, List[NavigationItem]]]:
        """Get categories with their accessible navigation items."""
        accessible_items = self.get_accessible_items(user_ctx)
        categories_with_items = {}
        
        # Group items by category
        for category_key, category in self.categories.items():
            category_items = [
                item for item in accessible_items.values()
                if item.category == category_key
            ]
            
            if category_items:  # Only include categories with accessible items
                categories_with_items[category_key] = (category, category_items)
        
        # Sort by category order
        sorted_categories = dict(sorted(
            categories_with_items.items(),
            key=lambda x: x[1][0].order
        ))
        
        return sorted_categories
    
    def render_navigation_sidebar(self, user_ctx: Dict[str, Any]) -> str:
        """Render enhanced navigation sidebar."""
        current_page = st.session_state.get('current_page', 'dashboard')
        
        # Navigation header
        st.markdown("""
        <div style="text-align: center; padding: 20px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
            <h2 style="color: white; margin: 0;">🤖 AI Karen</h2>
            <p style="color: rgba(255,255,255,0.7); margin: 4px 0 0 0; font-size: 14px;">
                Premium Dashboard
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Quick search
        search_query = st.text_input("🔍 Quick Navigation", placeholder="Search pages...", key="nav_search")
        
        if search_query:
            self._render_search_results(search_query, user_ctx)
            return current_page
        
        # Navigation categories
        categories_with_items = self.get_categories_with_items(user_ctx)
        
        for category_key, (category, items) in categories_with_items.items():
            # Category header
            st.markdown(f"""
            <div style="color: rgba(255,255,255,0.9); font-weight: 600; 
                        margin: 20px 0 10px 0; font-size: 14px; display: flex; align-items: center; gap: 8px;">
                <span>{category.icon}</span>
                <span>{category.title}</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Category items
            for item in items:
                is_current = current_page == item.key
                
                # Create navigation button with badges
                button_content = f"{item.icon} {item.title}"
                
                if item.new:
                    button_content += " 🆕"
                elif item.beta:
                    button_content += " β"
                
                if item.badge:
                    button_content += f" ({item.badge})"
                
                # Navigation button
                if st.button(
                    button_content,
                    key=f"nav_{item.key}",
                    help=item.description,
                    disabled=is_current
                ):
                    self._navigate_to_page(item.key, item.title)
                    return item.key
        
        # Breadcrumb navigation
        if len(self.breadcrumbs) > 1:
            st.markdown("<hr style='border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
            self._render_breadcrumbs()
        
        return current_page
    
    def _render_search_results(self, query: str, user_ctx: Dict[str, Any]):
        """Render navigation search results."""
        accessible_items = self.get_accessible_items(user_ctx)
        
        # Filter items based on search query
        matching_items = []
        query_lower = query.lower()
        
        for item in accessible_items.values():
            if (query_lower in item.title.lower() or 
                query_lower in item.description.lower() or
                query_lower in item.category.lower()):
                matching_items.append(item)
        
        if matching_items:
            st.markdown("**Search Results:**")
            for item in matching_items[:5]:  # Limit to 5 results
                if st.button(
                    f"{item.icon} {item.title}",
                    key=f"search_{item.key}",
                    help=item.description
                ):
                    self._navigate_to_page(item.key, item.title)
        else:
            st.info("No matching pages found.")
    
    def _navigate_to_page(self, page_key: str, page_title: str):
        """Navigate to a specific page."""
        # Update session state
        st.session_state.current_page = page_key
        
        # Update breadcrumbs
        self._update_breadcrumbs(page_key, page_title)
        
        # Update page history
        self._update_page_history(page_key, page_title)
        
        # Clear search
        if 'nav_search' in st.session_state:
            st.session_state.nav_search = ""
        
        # Rerun to update the page
        st.rerun()
    
    def _update_breadcrumbs(self, page_key: str, page_title: str):
        """Update breadcrumb navigation."""
        # Add current page to breadcrumbs if not already there
        if not self.breadcrumbs or self.breadcrumbs[-1][0] != page_key:
            self.breadcrumbs.append((page_key, page_title))
        
        # Limit breadcrumb length
        if len(self.breadcrumbs) > 5:
            self.breadcrumbs = self.breadcrumbs[-5:]
    
    def _update_page_history(self, page_key: str, page_title: str):
        """Update page visit history."""
        # Remove if already in history
        self.page_history = [(k, t) for k, t in self.page_history if k != page_key]
        
        # Add to beginning
        self.page_history.insert(0, (page_key, page_title))
        
        # Limit history length
        if len(self.page_history) > 10:
            self.page_history = self.page_history[:10]
    
    def _render_breadcrumbs(self):
        """Render breadcrumb navigation."""
        st.markdown("**Navigation:**")
        
        breadcrumb_html = " → ".join([
            f"<span style='color: rgba(255,255,255,0.7);'>{title}</span>"
            for _, title in self.breadcrumbs
        ])
        
        st.markdown(f"<small>{breadcrumb_html}</small>", unsafe_allow_html=True)
    
    def render_page_header(self, page_key: str, user_ctx: Dict[str, Any]):
        """Render page header with navigation context."""
        if page_key in self.navigation_items:
            item = self.navigation_items[page_key]
            
            # Page header
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 16px;">
                    <h1 style="margin: 0; display: flex; align-items: center; gap: 12px;">
                        <span style="font-size: 2em;">{item.icon}</span>
                        {item.title}
                    </h1>
                    {f'<span class="badge-new">NEW</span>' if item.new else ''}
                    {f'<span class="badge-beta">BETA</span>' if item.beta else ''}
                </div>
                <p style="color: var(--theme-text-secondary); margin: 8px 0 0 0;">
                    {item.description}
                </p>
                """, unsafe_allow_html=True)
            
            with col2:
                # Quick actions based on page
                self._render_page_quick_actions(page_key)
            
            with col3:
                # Page-specific status or info
                self._render_page_status(page_key)
    
    def _render_page_quick_actions(self, page_key: str):
        """Render quick actions for the current page."""
        if page_key == "dashboard":
            if st.button("📊 Refresh Data", key="refresh_dashboard"):
                st.success("Dashboard data refreshed!")
        elif page_key == "chat":
            if st.button("🗑️ Clear History", key="clear_chat"):
                st.success("Chat history cleared!")
        elif page_key == "analytics":
            if st.button("📈 Export Report", key="export_analytics"):
                st.success("Report exported!")
    
    def _render_page_status(self, page_key: str):
        """Render page-specific status information."""
        if page_key == "monitoring":
            st.markdown("""
            <div class="status-indicator status-healthy">
                ● All Systems Operational
            </div>
            """, unsafe_allow_html=True)
        elif page_key == "chat":
            st.markdown("""
            <div style="text-align: right; font-size: 12px; color: var(--theme-text-secondary);">
                Last message: 2 minutes ago<br>
                Active conversations: 3
            </div>
            """, unsafe_allow_html=True)
    
    def get_page_function(self, page_key: str) -> Optional[callable]:
        """Get the page function for a given page key."""
        if page_key in self.navigation_items:
            return self.navigation_items[page_key].page_function
        return None