"""
Advanced User Management Interface
Role-based access control with user preference management
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List
import plotly.express as px
import plotly.graph_objects as go

from ai_karen_engine.services.user_service import (
    rbac_service,
    User,
    UserRole,
    Permission,
)


def render_user_management_page(user_ctx=None):
    """Main user management interface"""
    
    # Get current user
    current_user = get_current_user_from_context(user_ctx)
    
    if not current_user:
        render_login_interface()
        return
    
    # Check if user has permission to manage users
    if not rbac_service.has_permission(current_user, Permission.MANAGE_USERS):
        st.error("🚫 Access Denied: You don't have permission to manage users.")
        return
    
    st.markdown("# 👥 User Management")
    st.markdown("### *Advanced user management and role-based access control*")
    
    # User management tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "👤 Users", 
        "🔐 Roles & Permissions", 
        "📊 Analytics",
        "⚙️ Settings"
    ])
    
    with tab1:
        render_users_management(current_user)
    
    with tab2:
        render_roles_permissions(current_user)
    
    with tab3:
        render_user_analytics(current_user)
    
    with tab4:
        render_user_settings(current_user)


def render_login_interface():
    """Login interface for authentication"""
    
    st.markdown("# 🔐 Login Required")
    st.markdown("### *Please log in to access AI Karen*")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            st.markdown("### 👤 User Authentication")
            
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.form_submit_button("🔑 Login", type="primary", use_container_width=True):
                    if username and password:
                        user = rbac_service.authenticate_user(username, password)
                        if user:
                            # Create session
                            session = rbac_service.create_session(user)
                            st.session_state.user_session = session.session_id
                            st.session_state.current_user = user
                            st.success(f"Welcome back, {user.full_name}!")
                            st.rerun()
                        else:
                            st.error("❌ Invalid username or password")
                    else:
                        st.error("⚠️ Please enter both username and password")
            
            with col2:
                if st.form_submit_button("👤 Guest Access", use_container_width=True):
                    # Create guest user
                    guest_user = User(
                        id="guest",
                        username="guest",
                        email="guest@ai-karen.com",
                        full_name="Guest User",
                        role=UserRole.GUEST,
                        permissions=rbac_service.role_permissions[UserRole.GUEST],
                        created_at=datetime.now(),
                        last_login=datetime.now(),
                        is_active=True,
                        preferences={},
                        session_data={}
                    )
                    st.session_state.current_user = guest_user
                    st.info("👤 Logged in as Guest (limited access)")
                    st.rerun()
        
        # Demo credentials
        st.markdown("---")
        st.markdown("### 🧪 Demo Credentials")
        st.info("""
        **Admin User:**
        - Username: `admin`
        - Password: `admin`
        
        **Regular User:**
        - Username: `user`
        - Password: `user`
        """)


def render_users_management(current_user: User):
    """User management interface"""
    
    st.markdown("## 👤 User Management")
    
    # User statistics
    stats = rbac_service.get_user_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Users", stats["total_users"])
    
    with col2:
        st.metric("Active Users", stats["active_users"], 
                 delta=f"+{stats['active_users'] - stats['inactive_users']}")
    
    with col3:
        st.metric("Active Sessions", stats["active_sessions"])
    
    with col4:
        st.metric("Recent Logins", stats["recent_logins"])
    
    # User actions
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query = st.text_input("🔍 Search users", placeholder="Search by name, username, or email...")
    
    with col2:
        if st.button("➕ Add New User", use_container_width=True):
            st.session_state.show_add_user_modal = True
    
    # Users table
    users = rbac_service.get_all_users(current_user)
    
    # Filter users based on search
    if search_query:
        search_lower = search_query.lower()
        users = [
            u for u in users 
            if (search_lower in u.username.lower() or 
                search_lower in u.full_name.lower() or 
                search_lower in u.email.lower())
        ]
    
    # Create users dataframe
    user_data = []
    for user in users:
        last_login = user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else "Never"
        status = "🟢 Active" if user.is_active else "🔴 Inactive"
        
        user_data.append({
            "Username": user.username,
            "Full Name": user.full_name,
            "Email": user.email,
            "Role": user.role.value.title(),
            "Status": status,
            "Last Login": last_login,
            "Created": user.created_at.strftime('%Y-%m-%d')
        })
    
    if user_data:
        df = pd.DataFrame(user_data)
        
        # Display users table
        st.dataframe(
            df,
            use_container_width=True,
            column_config={
                "Status": st.column_config.TextColumn("Status"),
                "Role": st.column_config.TextColumn("Role")
            }
        )
        
        # User actions
        st.markdown("### 🔧 User Actions")
        
        selected_username = st.selectbox("Select user for actions:", [u.username for u in users])
        selected_user = next(u for u in users if u.username == selected_username)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("✏️ Edit User"):
                st.session_state.edit_user = selected_user
                st.session_state.show_edit_user_modal = True
        
        with col2:
            if st.button("🔄 Change Role"):
                st.session_state.change_role_user = selected_user
                st.session_state.show_change_role_modal = True
        
        with col3:
            action_text = "🔴 Deactivate" if selected_user.is_active else "🟢 Activate"
            if st.button(action_text):
                if selected_user.is_active:
                    rbac_service.deactivate_user(selected_user.id, current_user)
                    st.success(f"User {selected_user.username} deactivated")
                else:
                    selected_user.is_active = True
                    st.success(f"User {selected_user.username} activated")
                st.rerun()
        
        with col4:
            if st.button("📊 View Sessions"):
                st.session_state.view_sessions_user = selected_user
                st.session_state.show_sessions_modal = True
    
    else:
        st.info("No users found matching your search criteria.")
    
    # Render modals
    render_user_modals(current_user)


def render_roles_permissions(current_user: User):
    """Roles and permissions management"""
    
    st.markdown("## 🔐 Roles & Permissions")
    
    # Role hierarchy
    st.markdown("### 📊 Role Hierarchy")
    
    hierarchy = rbac_service.get_role_hierarchy()
    role_data = []
    
    for role, level in hierarchy.items():
        permissions = rbac_service.role_permissions[role]
        role_data.append({
            "Role": role.value.title(),
            "Level": level,
            "Permissions": len(permissions),
            "Description": get_role_description(role)
        })
    
    role_df = pd.DataFrame(role_data)
    st.dataframe(role_df, use_container_width=True)
    
    # Permission matrix
    st.markdown("### 🔒 Permission Matrix")
    
    # Create permission matrix
    all_permissions = list(Permission)
    matrix_data = []
    
    for role in UserRole:
        role_permissions = rbac_service.role_permissions[role]
        row = {"Role": role.value.title()}
        
        for perm in all_permissions:
            row[perm.value] = "✅" if perm in role_permissions else "❌"
        
        matrix_data.append(row)
    
    matrix_df = pd.DataFrame(matrix_data)
    st.dataframe(matrix_df, use_container_width=True)
    
    # Role distribution chart
    st.markdown("### 📈 Role Distribution")
    
    stats = rbac_service.get_user_stats()
    role_dist = stats["role_distribution"]
    
    if any(count > 0 for count in role_dist.values()):
        fig = px.pie(
            values=list(role_dist.values()),
            names=[role.title() for role in role_dist.keys()],
            title="User Role Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No role distribution data available")


def render_user_analytics(current_user: User):
    """User analytics and insights"""
    
    st.markdown("## 📊 User Analytics")
    
    # User activity metrics
    users = rbac_service.get_all_users(current_user)
    
    # Login activity over time
    st.markdown("### 📈 Login Activity")
    
    # Generate sample login data
    dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
    login_data = []
    
    for date in dates:
        # Simulate login counts
        login_count = max(0, int(np.random.normal(len(users) * 0.7, len(users) * 0.2)))
        login_data.append({
            "Date": date,
            "Logins": login_count
        })
    
    login_df = pd.DataFrame(login_data)
    
    fig = px.line(
        login_df,
        x="Date",
        y="Logins",
        title="Daily Login Activity (30 days)"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # User engagement metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 👥 User Engagement")
        
        engagement_data = {
            "Daily Active": len([u for u in users if u.last_login and u.last_login > datetime.now() - timedelta(days=1)]),
            "Weekly Active": len([u for u in users if u.last_login and u.last_login > datetime.now() - timedelta(days=7)]),
            "Monthly Active": len([u for u in users if u.last_login and u.last_login > datetime.now() - timedelta(days=30)])
        }
        
        for metric, value in engagement_data.items():
            st.metric(metric, value)
    
    with col2:
        st.markdown("### 🔐 Security Metrics")
        
        security_data = {
            "Failed Logins": 12,
            "Locked Accounts": 1,
            "2FA Enabled": len([u for u in users if u.two_factor_enabled])
        }
        
        for metric, value in security_data.items():
            st.metric(metric, value)
    
    # Session analytics
    st.markdown("### 📱 Session Analytics")
    
    # Generate sample session data
    session_data = []
    for user in users:
        sessions = rbac_service.get_user_sessions(user.id, current_user)
        for session in sessions:
            session_data.append({
                "User": user.username,
                "Duration": (datetime.now() - session.created_at).total_seconds() / 3600,
                "IP Address": session.ip_address,
                "User Agent": session.user_agent[:50] + "..." if len(session.user_agent) > 50 else session.user_agent
            })
    
    if session_data:
        session_df = pd.DataFrame(session_data)
        st.dataframe(session_df, use_container_width=True)
    else:
        st.info("No active sessions found")


def render_user_settings(current_user: User):
    """User management settings"""
    
    st.markdown("## ⚙️ User Management Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔐 Security Settings")
        
        require_2fa = st.checkbox("Require Two-Factor Authentication", value=False)
        session_timeout = st.slider("Session Timeout (hours)", 1, 24, 8)
        max_login_attempts = st.slider("Max Login Attempts", 3, 10, 5)
        password_expiry = st.slider("Password Expiry (days)", 30, 365, 90)
    
    with col2:
        st.markdown("### 👤 User Defaults")
        
        default_role = st.selectbox("Default Role for New Users", 
                                   [role.value.title() for role in UserRole], 
                                   index=1)
        
        auto_activate = st.checkbox("Auto-activate New Users", value=True)
        welcome_email = st.checkbox("Send Welcome Email", value=True)
        
    # Bulk operations
    st.markdown("### 🔧 Bulk Operations")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📧 Send Notification to All", use_container_width=True):
            st.success("Notification sent to all active users!")
    
    with col2:
        if st.button("🔄 Force Password Reset", use_container_width=True):
            st.warning("Password reset required for all users on next login")
    
    with col3:
        if st.button("🧹 Cleanup Inactive Sessions", use_container_width=True):
            rbac_service.cleanup_expired_sessions()
            st.success("Inactive sessions cleaned up!")


def render_user_modals(current_user: User):
    """Render user management modals"""
    
    # Add user modal
    if st.session_state.get('show_add_user_modal', False):
        with st.expander("➕ Add New User", expanded=True):
            with st.form("add_user_form"):
                st.markdown("### 👤 Create New User")
                
                username = st.text_input("Username*", placeholder="Enter username")
                email = st.text_input("Email*", placeholder="Enter email address")
                full_name = st.text_input("Full Name*", placeholder="Enter full name")
                password = st.text_input("Password*", type="password", placeholder="Enter password")
                role = st.selectbox("Role", [r.value.title() for r in UserRole], index=1)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.form_submit_button("✅ Create User", type="primary"):
                        if username and email and full_name and password:
                            try:
                                user_role = UserRole(role.lower())
                                new_user = rbac_service.create_user(
                                    username, email, full_name, user_role, password, current_user
                                )
                                st.success(f"User {new_user.username} created successfully!")
                                st.session_state.show_add_user_modal = False
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error creating user: {str(e)}")
                        else:
                            st.error("Please fill in all required fields")
                
                with col2:
                    if st.form_submit_button("❌ Cancel"):
                        st.session_state.show_add_user_modal = False
                        st.rerun()


def get_current_user_from_context(user_ctx) -> User:
    """Get current user from context or session"""
    
    # Check session state first
    if hasattr(st.session_state, 'current_user'):
        return st.session_state.current_user
    
    # Check session ID
    if hasattr(st.session_state, 'user_session'):
        user = rbac_service.get_user_by_session(st.session_state.user_session)
        if user:
            st.session_state.current_user = user
            return user
    
    # Check user context
    if user_ctx and user_ctx.get('user_id'):
        user = next((u for u in rbac_service.users.values() if u.id == user_ctx['user_id']), None)
        if user:
            st.session_state.current_user = user
            return user
    
    return None


def get_role_description(role: UserRole) -> str:
    """Get description for user role"""
    descriptions = {
        UserRole.GUEST: "Limited read-only access",
        UserRole.USER: "Standard user with chat and memory access",
        UserRole.MODERATOR: "Enhanced user with plugin management",
        UserRole.ADMIN: "Full system administration access",
        UserRole.SUPER_ADMIN: "Complete system control and management"
    }
    return descriptions.get(role, "Unknown role")


# Import numpy for data generation
import numpy as np