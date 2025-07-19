"""
User Management Page
- User account management and role assignment
- Permission management and access control
- User activity monitoring
"""

import streamlit as st
from typing import Dict, Any

def user_management_page(user_ctx: Dict[str, Any]):
    """Render the user management interface."""
    
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <h1 style="display: flex; align-items: center; gap: 1rem; margin: 0;">
            👥 User Management
        </h1>
        <p style="color: #64748b; margin: 0.5rem 0 0 0;">
            Manage users, roles, and permissions
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.info("🚧 User management implementation coming in task 9!")
    st.markdown("""
    **Planned Features:**
    - User account creation and management
    - Role-based access control (RBAC)
    - Permission assignment and management
    - User activity monitoring and audit logs
    - Bulk user operations and CSV import/export
    """)
    
    # Placeholder user list
    st.subheader("Active Users")
    users = [
        {"name": "John Doe", "email": "john@company.com", "role": "Admin", "last_active": "5 minutes ago"},
        {"name": "Jane Smith", "email": "jane@company.com", "role": "User", "last_active": "1 hour ago"},
        {"name": "Bob Wilson", "email": "bob@company.com", "role": "Analyst", "last_active": "2 hours ago"}
    ]
    
    for user in users:
        col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
        with col1:
            st.write(f"**{user['name']}**")
        with col2:
            st.write(user['email'])
        with col3:
            st.write(user['role'])
        with col4:
            st.write(user['last_active'])