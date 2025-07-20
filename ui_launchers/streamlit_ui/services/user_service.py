"""
Advanced User Management and RBAC Service
Role-based access control with user preference management
"""

import os
import json
import hashlib
import secrets
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import streamlit as st


class UserRole(Enum):
    """User roles with hierarchical permissions"""
    GUEST = "guest"
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class Permission(Enum):
    """System permissions"""
    # Basic permissions
    READ_DASHBOARD = "read_dashboard"
    USE_CHAT = "use_chat"
    VIEW_MEMORY = "view_memory"
    
    # Advanced permissions
    MANAGE_PLUGINS = "manage_plugins"
    VIEW_ANALYTICS = "view_analytics"
    CONFIGURE_SYSTEM = "configure_system"
    
    # Admin permissions
    MANAGE_USERS = "manage_users"
    VIEW_LOGS = "view_logs"
    SYSTEM_ADMIN = "system_admin"
    
    # Super admin permissions
    FULL_ACCESS = "full_access"


@dataclass
class User:
    """User data structure"""
    id: str
    username: str
    email: str
    full_name: str
    role: UserRole
    permissions: Set[Permission]
    created_at: datetime
    last_login: Optional[datetime]
    is_active: bool
    preferences: Dict[str, Any]
    session_data: Dict[str, Any]
    password_hash: Optional[str] = None
    api_key: Optional[str] = None
    two_factor_enabled: bool = False


@dataclass
class UserSession:
    """User session tracking"""
    session_id: str
    user_id: str
    created_at: datetime
    last_activity: datetime
    ip_address: str
    user_agent: str
    is_active: bool


class RBACService:
    """Role-Based Access Control Service"""
    
    def __init__(self):
        # Role-permission mapping
        self.role_permissions = {
            UserRole.GUEST: {
                Permission.READ_DASHBOARD,
            },
            UserRole.USER: {
                Permission.READ_DASHBOARD,
                Permission.USE_CHAT,
                Permission.VIEW_MEMORY,
            },
            UserRole.MODERATOR: {
                Permission.READ_DASHBOARD,
                Permission.USE_CHAT,
                Permission.VIEW_MEMORY,
                Permission.MANAGE_PLUGINS,
                Permission.VIEW_ANALYTICS,
            },
            UserRole.ADMIN: {
                Permission.READ_DASHBOARD,
                Permission.USE_CHAT,
                Permission.VIEW_MEMORY,
                Permission.MANAGE_PLUGINS,
                Permission.VIEW_ANALYTICS,
                Permission.CONFIGURE_SYSTEM,
                Permission.MANAGE_USERS,
                Permission.VIEW_LOGS,
            },
            UserRole.SUPER_ADMIN: {
                Permission.FULL_ACCESS,
                Permission.SYSTEM_ADMIN,
                Permission.MANAGE_USERS,
                Permission.VIEW_LOGS,
                Permission.CONFIGURE_SYSTEM,
                Permission.MANAGE_PLUGINS,
                Permission.VIEW_ANALYTICS,
                Permission.VIEW_MEMORY,
                Permission.USE_CHAT,
                Permission.READ_DASHBOARD,
            }
        }
        
        # In-memory user store (would be database in production)
        self.users: Dict[str, User] = {}
        self.sessions: Dict[str, UserSession] = {}
        
        # Initialize with default admin user
        self._create_default_users()
    
    def _create_default_users(self):
        """Create default system users"""
        # Default admin user
        admin_user = User(
            id="admin_001",
            username="admin",
            email="admin@ai-karen.com",
            full_name="System Administrator",
            role=UserRole.ADMIN,
            permissions=self.role_permissions[UserRole.ADMIN],
            created_at=datetime.now(),
            last_login=None,
            is_active=True,
            preferences={
                "theme": "dark",
                "language": "en",
                "notifications": True,
                "auto_refresh": True
            },
            session_data={},
            password_hash=self._hash_password("admin123"),
            api_key=self._generate_api_key()
        )
        
        # Default user
        regular_user = User(
            id="user_001",
            username="user",
            email="user@ai-karen.com",
            full_name="Regular User",
            role=UserRole.USER,
            permissions=self.role_permissions[UserRole.USER],
            created_at=datetime.now(),
            last_login=None,
            is_active=True,
            preferences={
                "theme": "light",
                "language": "en",
                "notifications": True,
                "auto_refresh": False
            },
            session_data={},
            password_hash=self._hash_password("user123"),
            api_key=self._generate_api_key()
        )
        
        self.users[admin_user.id] = admin_user
        self.users[regular_user.id] = regular_user
    
    def _hash_password(self, password: str) -> str:
        """Hash password with salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}:{password_hash.hex()}"
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        try:
            salt, hash_hex = password_hash.split(':')
            password_hash_check = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return password_hash_check.hex() == hash_hex
        except:
            return False
    
    def _generate_api_key(self) -> str:
        """Generate API key for user"""
        return f"ak_{secrets.token_urlsafe(32)}"
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username/password"""
        user = next((u for u in self.users.values() if u.username == username), None)
        
        if user and user.is_active and user.password_hash:
            if self._verify_password(password, user.password_hash):
                user.last_login = datetime.now()
                return user
        
        return None
    
    def create_session(self, user: User, ip_address: str = "127.0.0.1", 
                      user_agent: str = "Unknown") -> UserSession:
        """Create user session"""
        session = UserSession(
            session_id=secrets.token_urlsafe(32),
            user_id=user.id,
            created_at=datetime.now(),
            last_activity=datetime.now(),
            ip_address=ip_address,
            user_agent=user_agent,
            is_active=True
        )
        
        self.sessions[session.session_id] = session
        return session
    
    def get_user_by_session(self, session_id: str) -> Optional[User]:
        """Get user by session ID"""
        session = self.sessions.get(session_id)
        if session and session.is_active:
            # Update last activity
            session.last_activity = datetime.now()
            return self.users.get(session.user_id)
        return None
    
    def has_permission(self, user: User, permission: Permission) -> bool:
        """Check if user has specific permission"""
        if not user.is_active:
            return False
        
        # Super admin has all permissions
        if Permission.FULL_ACCESS in user.permissions:
            return True
        
        return permission in user.permissions
    
    def require_permission(self, user: User, permission: Permission) -> bool:
        """Require permission or raise exception"""
        if not self.has_permission(user, permission):
            raise PermissionError(f"User {user.username} lacks permission: {permission.value}")
        return True
    
    def create_user(self, username: str, email: str, full_name: str, 
                   role: UserRole, password: str, created_by: User) -> User:
        """Create new user (requires MANAGE_USERS permission)"""
        self.require_permission(created_by, Permission.MANAGE_USERS)
        
        # Check if username/email already exists
        if any(u.username == username or u.email == email for u in self.users.values()):
            raise ValueError("Username or email already exists")
        
        user = User(
            id=f"user_{len(self.users) + 1:03d}",
            username=username,
            email=email,
            full_name=full_name,
            role=role,
            permissions=self.role_permissions[role],
            created_at=datetime.now(),
            last_login=None,
            is_active=True,
            preferences={
                "theme": "light",
                "language": "en",
                "notifications": True,
                "auto_refresh": False
            },
            session_data={},
            password_hash=self._hash_password(password),
            api_key=self._generate_api_key()
        )
        
        self.users[user.id] = user
        return user
    
    def update_user_role(self, user_id: str, new_role: UserRole, updated_by: User) -> bool:
        """Update user role (requires MANAGE_USERS permission)"""
        self.require_permission(updated_by, Permission.MANAGE_USERS)
        
        user = self.users.get(user_id)
        if not user:
            return False
        
        user.role = new_role
        user.permissions = self.role_permissions[new_role]
        return True
    
    def deactivate_user(self, user_id: str, deactivated_by: User) -> bool:
        """Deactivate user (requires MANAGE_USERS permission)"""
        self.require_permission(deactivated_by, Permission.MANAGE_USERS)
        
        user = self.users.get(user_id)
        if not user:
            return False
        
        user.is_active = False
        
        # Deactivate all user sessions
        for session in self.sessions.values():
            if session.user_id == user_id:
                session.is_active = False
        
        return True
    
    def get_all_users(self, requested_by: User) -> List[User]:
        """Get all users (requires MANAGE_USERS permission)"""
        self.require_permission(requested_by, Permission.MANAGE_USERS)
        return list(self.users.values())
    
    def update_user_preferences(self, user: User, preferences: Dict[str, Any]) -> bool:
        """Update user preferences"""
        user.preferences.update(preferences)
        return True
    
    def get_user_sessions(self, user_id: str, requested_by: User) -> List[UserSession]:
        """Get user sessions (requires MANAGE_USERS permission or own sessions)"""
        if user_id != requested_by.id:
            self.require_permission(requested_by, Permission.MANAGE_USERS)
        
        return [s for s in self.sessions.values() if s.user_id == user_id and s.is_active]
    
    def revoke_session(self, session_id: str, revoked_by: User) -> bool:
        """Revoke user session"""
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        # Users can revoke their own sessions, admins can revoke any
        if session.user_id != revoked_by.id:
            self.require_permission(revoked_by, Permission.MANAGE_USERS)
        
        session.is_active = False
        return True
    
    def cleanup_expired_sessions(self, max_age_hours: int = 24):
        """Clean up expired sessions"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        for session in self.sessions.values():
            if session.last_activity < cutoff_time:
                session.is_active = False
    
    def get_role_hierarchy(self) -> Dict[UserRole, int]:
        """Get role hierarchy levels"""
        return {
            UserRole.GUEST: 0,
            UserRole.USER: 1,
            UserRole.MODERATOR: 2,
            UserRole.ADMIN: 3,
            UserRole.SUPER_ADMIN: 4
        }
    
    def can_manage_user(self, manager: User, target_user: User) -> bool:
        """Check if manager can manage target user"""
        if not self.has_permission(manager, Permission.MANAGE_USERS):
            return False
        
        hierarchy = self.get_role_hierarchy()
        return hierarchy[manager.role] > hierarchy[target_user.role]
    
    def get_user_stats(self) -> Dict[str, Any]:
        """Get user management statistics"""
        active_users = [u for u in self.users.values() if u.is_active]
        active_sessions = [s for s in self.sessions.values() if s.is_active]
        
        role_counts = {}
        for role in UserRole:
            role_counts[role.value] = len([u for u in active_users if u.role == role])
        
        return {
            "total_users": len(self.users),
            "active_users": len(active_users),
            "inactive_users": len(self.users) - len(active_users),
            "active_sessions": len(active_sessions),
            "role_distribution": role_counts,
            "recent_logins": len([u for u in active_users if u.last_login and u.last_login > datetime.now() - timedelta(days=7)])
        }


# Create singleton instance
rbac_service = RBACService()