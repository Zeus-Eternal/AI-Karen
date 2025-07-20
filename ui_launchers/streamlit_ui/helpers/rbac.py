"""
Role-Based Access Control (RBAC) Helper
Provides user access control and permission management for AI Karen UI.
"""

import streamlit as st
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from enum import Enum


class Permission(Enum):
    """System permissions."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    EXECUTE = "execute"
    CONFIGURE = "configure"


class Role(Enum):
    """System roles."""
    GUEST = "guest"
    USER = "user"
    ANALYST = "analyst"
    DEVELOPER = "dev"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


@dataclass
class RoleDefinition:
    """Definition of a role with its permissions."""
    name: str
    display_name: str
    description: str
    permissions: Set[Permission]
    inherits_from: Optional[str] = None


class RBACManager:
    """Role-Based Access Control Manager."""
    
    def __init__(self):
        self.roles = self._initialize_default_roles()
        self.user_roles = {}  # user_id -> set of roles
        self.custom_permissions = {}  # user_id -> set of custom permissions
    
    def _initialize_default_roles(self) -> Dict[str, RoleDefinition]:
        """Initialize default system roles."""
        return {
            Role.GUEST.value: RoleDefinition(
                name=Role.GUEST.value,
                display_name="Guest",
                description="Limited read-only access",
                permissions={Permission.READ}
            ),
            Role.USER.value: RoleDefinition(
                name=Role.USER.value,
                display_name="User",
                description="Standard user with basic functionality",
                permissions={Permission.READ, Permission.WRITE},
                inherits_from=Role.GUEST.value
            ),
            Role.ANALYST.value: RoleDefinition(
                name=Role.ANALYST.value,
                display_name="Analyst",
                description="Data analyst with analytics access",
                permissions={Permission.READ, Permission.WRITE, Permission.EXECUTE},
                inherits_from=Role.USER.value
            ),
            Role.DEVELOPER.value: RoleDefinition(
                name=Role.DEVELOPER.value,
                display_name="Developer",
                description="Developer with plugin and configuration access",
                permissions={Permission.READ, Permission.WRITE, Permission.EXECUTE, Permission.CONFIGURE},
                inherits_from=Role.USER.value
            ),
            Role.ADMIN.value: RoleDefinition(
                name=Role.ADMIN.value,
                display_name="Administrator",
                description="System administrator with full access",
                permissions={Permission.READ, Permission.WRITE, Permission.DELETE, Permission.EXECUTE, Permission.CONFIGURE, Permission.ADMIN},
                inherits_from=Role.DEVELOPER.value
            ),
            Role.SUPER_ADMIN.value: RoleDefinition(
                name=Role.SUPER_ADMIN.value,
                display_name="Super Administrator",
                description="Full system access including user management",
                permissions={Permission.READ, Permission.WRITE, Permission.DELETE, Permission.EXECUTE, Permission.CONFIGURE, Permission.ADMIN},
                inherits_from=Role.ADMIN.value
            )
        }
    
    def get_user_roles(self, user_id: str) -> Set[str]:
        """Get roles for a user."""
        return self.user_roles.get(user_id, {Role.GUEST.value})
    
    def assign_role(self, user_id: str, role: str) -> bool:
        """Assign a role to a user."""
        if role in self.roles:
            if user_id not in self.user_roles:
                self.user_roles[user_id] = set()
            self.user_roles[user_id].add(role)
            return True
        return False
    
    def remove_role(self, user_id: str, role: str) -> bool:
        """Remove a role from a user."""
        if user_id in self.user_roles and role in self.user_roles[user_id]:
            self.user_roles[user_id].remove(role)
            if not self.user_roles[user_id]:
                self.user_roles[user_id] = {Role.GUEST.value}
            return True
        return False
    
    def get_user_permissions(self, user_id: str) -> Set[Permission]:
        """Get all permissions for a user."""
        user_roles = self.get_user_roles(user_id)
        permissions = set()
        
        for role_name in user_roles:
            role = self.roles.get(role_name)
            if role:
                permissions.update(role.permissions)
                
                # Add inherited permissions
                if role.inherits_from:
                    inherited_role = self.roles.get(role.inherits_from)
                    if inherited_role:
                        permissions.update(inherited_role.permissions)
        
        # Add custom permissions
        custom_perms = self.custom_permissions.get(user_id, set())
        permissions.update(custom_perms)
        
        return permissions
    
    def has_permission(self, user_id: str, permission: Permission) -> bool:
        """Check if user has a specific permission."""
        user_permissions = self.get_user_permissions(user_id)
        return permission in user_permissions
    
    def has_role(self, user_id: str, role: str) -> bool:
        """Check if user has a specific role."""
        user_roles = self.get_user_roles(user_id)
        return role in user_roles
    
    def has_any_role(self, user_id: str, roles: List[str]) -> bool:
        """Check if user has any of the specified roles."""
        user_roles = self.get_user_roles(user_id)
        return bool(user_roles.intersection(set(roles)))
    
    def is_admin(self, user_id: str) -> bool:
        """Check if user is an administrator."""
        return self.has_role(user_id, Role.ADMIN.value) or self.has_role(user_id, Role.SUPER_ADMIN.value)
    
    def can_access_page(self, user_id: str, required_roles: List[str]) -> bool:
        """Check if user can access a page with required roles."""
        if not required_roles:
            return True
        
        return self.has_any_role(user_id, required_roles)
    
    def get_accessible_features(self, user_id: str) -> Dict[str, bool]:
        """Get dictionary of accessible features for a user."""
        permissions = self.get_user_permissions(user_id)
        roles = self.get_user_roles(user_id)
        
        return {
            "can_read": Permission.READ in permissions,
            "can_write": Permission.WRITE in permissions,
            "can_delete": Permission.DELETE in permissions,
            "can_execute": Permission.EXECUTE in permissions,
            "can_configure": Permission.CONFIGURE in permissions,
            "is_admin": Permission.ADMIN in permissions,
            "is_analyst": Role.ANALYST.value in roles,
            "is_developer": Role.DEVELOPER.value in roles,
            "can_manage_users": self.has_role(user_id, Role.SUPER_ADMIN.value),
            "can_view_analytics": Role.ANALYST.value in roles or Permission.ADMIN in permissions,
            "can_manage_plugins": Role.DEVELOPER.value in roles or Permission.ADMIN in permissions,
            "can_access_admin": Permission.ADMIN in permissions
        }


# Global RBAC manager instance
_rbac_manager: Optional[RBACManager] = None


def get_rbac_manager() -> RBACManager:
    """Get or create global RBAC manager instance."""
    global _rbac_manager
    if _rbac_manager is None:
        _rbac_manager = RBACManager()
    return _rbac_manager


def check_user_access(user_context: Dict[str, Any], required_roles: List[str]) -> bool:
    """Check if user has access based on required roles."""
    if not required_roles:
        return True
    
    user_roles = user_context.get("roles", [])
    if not user_roles:
        return False
    
    # Check if user has any of the required roles
    return bool(set(user_roles).intersection(set(required_roles)))


def has_permission(user_context: Dict[str, Any], permission: str) -> bool:
    """Check if user has a specific permission."""
    rbac = get_rbac_manager()
    user_id = user_context.get("user_id", "anonymous")
    
    try:
        perm = Permission(permission)
        return rbac.has_permission(user_id, perm)
    except ValueError:
        return False


def is_admin(user_context: Dict[str, Any]) -> bool:
    """Check if user is an administrator."""
    user_roles = user_context.get("roles", [])
    return "admin" in user_roles or "super_admin" in user_roles


def get_user_capabilities(user_context: Dict[str, Any]) -> Dict[str, bool]:
    """Get user capabilities based on roles and permissions."""
    rbac = get_rbac_manager()
    user_id = user_context.get("user_id", "anonymous")
    
    # Initialize user roles if not already done
    user_roles = user_context.get("roles", ["guest"])
    for role in user_roles:
        rbac.assign_role(user_id, role)
    
    return rbac.get_accessible_features(user_id)


def require_role(required_roles: List[str]):
    """Decorator to require specific roles for a function."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            user_context = st.session_state.get("user_context", {})
            if not check_user_access(user_context, required_roles):
                st.error(f"Access denied. Required roles: {', '.join(required_roles)}")
                st.stop()
            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_permission(permission: str):
    """Decorator to require specific permission for a function."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            user_context = st.session_state.get("user_context", {})
            if not has_permission(user_context, permission):
                st.error(f"Access denied. Required permission: {permission}")
                st.stop()
            return func(*args, **kwargs)
        return wrapper
    return decorator


def render_access_denied(required_roles: List[str] = None, required_permission: str = None):
    """Render access denied message."""
    st.error("🚫 Access Denied")
    
    if required_roles:
        st.write(f"**Required roles:** {', '.join(required_roles)}")
    
    if required_permission:
        st.write(f"**Required permission:** {required_permission}")
    
    user_context = st.session_state.get("user_context", {})
    current_roles = user_context.get("roles", ["guest"])
    st.write(f"**Your current roles:** {', '.join(current_roles)}")
    
    st.info("Please contact your administrator if you believe you should have access to this feature.")


def render_role_badge(user_context: Dict[str, Any]):
    """Render user role badge."""
    user_roles = user_context.get("roles", ["guest"])
    primary_role = user_roles[0] if user_roles else "guest"
    
    role_colors = {
        "guest": "#6b7280",
        "user": "#3b82f6",
        "analyst": "#8b5cf6",
        "dev": "#10b981",
        "admin": "#ef4444",
        "super_admin": "#dc2626"
    }
    
    color = role_colors.get(primary_role, "#6b7280")
    
    badge_html = f"""
    <span style="
        background: {color};
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    ">
        {primary_role}
    </span>
    """
    
    st.markdown(badge_html, unsafe_allow_html=True)


# Initialize RBAC system
def initialize_rbac():
    """Initialize RBAC system with default settings."""
    if 'rbac_initialized' not in st.session_state:
        rbac = get_rbac_manager()
        
        # Set up default user if not exists
        user_context = st.session_state.get("user_context", {})
        user_id = user_context.get("user_id", "anonymous")
        user_roles = user_context.get("roles", ["user"])
        
        for role in user_roles:
            rbac.assign_role(user_id, role)
        
        st.session_state.rbac_initialized = True


# Auto-initialize RBAC
initialize_rbac()