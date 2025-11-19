"""
Authentication Components for Kari AI Streamlit Console
"""

import streamlit as st
import json
import os
from datetime import datetime
import hashlib

def render_user_auth():
    """Render user authentication or selection interface"""
    st.markdown("## User Authentication")
    
    # Check if users are already defined
    if 'users' not in st.session_state:
        initialize_default_users()
    
    # Check if user is already logged in
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    
    # If user is logged in, show user info and logout option
    if st.session_state.current_user:
        render_user_profile()
    else:
        render_login_form()

def initialize_default_users():
    """Initialize default users for the application"""
    default_users = {
        "admin": {
            "name": "Administrator",
            "email": "admin@kari.ai",
            "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
            "role": "admin",
            "preferences": {
                "language": "English",
                "timezone": "UTC",
                "theme": "Dark Neon",
                "notification_level": "All"
            },
            "account_type": "Premium",
            "member_since": "Jan 2023"
        },
        "creator": {
            "name": "Creator",
            "email": "creator@kari.ai",
            "password_hash": hashlib.sha256("creator123".encode()).hexdigest(),
            "role": "creator",
            "preferences": {
                "language": "English",
                "timezone": "UTC",
                "theme": "Dark Neon",
                "notification_level": "Important"
            },
            "account_type": "Premium",
            "member_since": "Jan 2023"
        },
        "user": {
            "name": "Demo User",
            "email": "user@kari.ai",
            "password_hash": hashlib.sha256("user123".encode()).hexdigest(),
            "role": "user",
            "preferences": {
                "language": "English",
                "timezone": "UTC",
                "theme": "Dark Neon",
                "notification_level": "Important"
            },
            "account_type": "Standard",
            "member_since": "Nov 2023"
        }
    }
    
    st.session_state.users = default_users

def render_login_form():
    """Render login form for user authentication"""
    st.markdown("### Login to Kari AI")
    
    # Create tabs for login and user selection
    login_tab, select_tab = st.tabs(["Login", "Quick Select"])
    
    with login_tab:
        with st.form("login_form"):
            st.markdown("#### Enter your credentials")
            
            # Username/Email input
            username = st.text_input("Username or Email", key="login_username")
            
            # Password input
            password = st.text_input("Password", type="password", key="login_password")
            
            # Submit button
            submitted = st.form_submit_button("Login")
            
            if submitted:
                if authenticate_user(username, password):
                    st.success(f"Welcome back, {st.session_state.current_user['name']}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password. Please try again.")
    
    with select_tab:
        st.markdown("#### Select a user profile")
        
        # Display user cards for quick selection
        users = st.session_state.users
        
        # Create columns for user cards
        if len(users) <= 2:
            cols = st.columns(len(users))
        else:
            cols = st.columns(3)
        
        for i, (username, user_data) in enumerate(users.items()):
            with cols[i % 3]:
                render_user_card(username, user_data)

def render_user_card(username, user_data):
    """Render a user card for quick selection"""
    # Card container
    with st.container():
        # User info
        st.markdown(f"**{user_data['name']}**")
        st.markdown(f"*{user_data['role'].capitalize()}*")
        st.markdown(f"Account: {user_data['account_type']}")
        
        # Select button
        if st.button(f"Select {username}", key=f"select_{username}"):
            # Set as current user without password
            st.session_state.current_user = user_data
            st.session_state.user_id = username
            st.success(f"Logged in as {user_data['name']}")
            st.rerun()
        
        st.markdown("---")

def authenticate_user(username, password):
    """Authenticate user with provided credentials"""
    users = st.session_state.users
    
    # Find user by username or email
    user = None
    user_key = None
    
    for key, user_data in users.items():
        if key == username or user_data.get('email') == username:
            user = user_data
            user_key = key
            break
    
    if not user:
        return False
    
    # Check password
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if password_hash == user['password_hash']:
        st.session_state.current_user = user
        st.session_state.user_id = user_key
        return True
    
    return False

def render_user_profile():
    """Render current user profile with logout option"""
    user = st.session_state.current_user
    
    st.markdown(f"### Welcome, {user['name']}!")
    
    # User info in columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Account Information**")
        st.markdown(f"**Username:** {st.session_state.user_id}")
        st.markdown(f"**Email:** {user.get('email', 'N/A')}")
        st.markdown(f"**Role:** {user['role'].capitalize()}")
        st.markdown(f"**Account Type:** {user['account_type']}")
        st.markdown(f"**Member Since:** {user['member_since']}")
    
    with col2:
        st.markdown("**Preferences**")
        if 'preferences' in user:
            preferences = user['preferences']
            st.markdown(f"**Language:** {preferences.get('language', 'English')}")
            st.markdown(f"**Timezone:** {preferences.get('timezone', 'UTC')}")
            st.markdown(f"**Theme:** {preferences.get('theme', 'Dark Neon')}")
            st.markdown(f"**Notifications:** {preferences.get('notification_level', 'All')}")
    
    # Logout button
    if st.button("Logout", key="logout_button"):
        st.session_state.current_user = None
        st.session_state.user_id = "dev_user"  # Reset to default
        st.success("You have been logged out successfully.")
        st.rerun()
    
    st.markdown("---")

def render_user_management():
    """Render user management interface (admin only)"""
    if not st.session_state.current_user or st.session_state.current_user.get('role') != 'admin':
        st.info("You need to be an administrator to access this page.")
        return
    
    st.markdown("## User Management")
    
    # Add new user form
    with st.expander("Add New User", expanded=False):
        with st.form("add_user_form"):
            st.markdown("#### Create a new user account")
            
            col1, col2 = st.columns(2)
            
            with col1:
                new_username = st.text_input("Username", key="new_username")
                new_name = st.text_input("Full Name", key="new_name")
                new_email = st.text_input("Email", key="new_email")
            
            with col2:
                new_password = st.text_input("Password", type="password", key="new_password")
                new_role = st.selectbox("Role", ["user", "creator", "admin"], key="new_role")
                new_account_type = st.selectbox("Account Type", ["Standard", "Premium"], key="new_account_type")
            
            submitted = st.form_submit_button("Create User")
            
            if submitted:
                if create_user(new_username, new_name, new_email, new_password, new_role, new_account_type):
                    st.success(f"User {new_username} created successfully!")
                    st.rerun()
                else:
                    st.error("Failed to create user. Please check your inputs.")
    
    # Display existing users
    st.markdown("### Existing Users")
    
    users = st.session_state.users
    for username, user_data in users.items():
        with st.expander(f"{user_data['name']} ({username})"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**User Information**")
                st.markdown(f"**Username:** {username}")
                st.markdown(f"**Name:** {user_data['name']}")
                st.markdown(f"**Email:** {user_data.get('email', 'N/A')}")
                st.markdown(f"**Role:** {user_data['role']}")
                st.markdown(f"**Account Type:** {user_data['account_type']}")
            
            with col2:
                st.markdown("**Account Details**")
                st.markdown(f"**Member Since:** {user_data['member_since']}")
                if 'preferences' in user_data:
                    prefs = user_data['preferences']
                    st.markdown(f"**Language:** {prefs.get('language', 'English')}")
                    st.markdown(f"**Timezone:** {prefs.get('timezone', 'UTC')}")
                    st.markdown(f"**Theme:** {prefs.get('theme', 'Dark Neon')}")
            
            # Delete button (except for current user)
            if username != st.session_state.user_id:
                if st.button(f"Delete {username}", key=f"delete_{username}"):
                    delete_user(username)
                    st.success(f"User {username} deleted successfully.")
                    st.rerun()

def create_user(username, name, email, password, role, account_type):
    """Create a new user account"""
    if not username or not name or not email or not password:
        return False
    
    # Check if username already exists
    if username in st.session_state.users:
        st.error("Username already exists.")
        return False
    
    # Create new user
    new_user = {
        "name": name,
        "email": email,
        "password_hash": hashlib.sha256(password.encode()).hexdigest(),
        "role": role,
        "preferences": {
            "language": "English",
            "timezone": "UTC",
            "theme": "Dark Neon",
            "notification_level": "Important"
        },
        "account_type": account_type,
        "member_since": datetime.now().strftime("%b %Y")
    }
    
    # Add to users
    st.session_state.users[username] = new_user
    return True

def delete_user(username):
    """Delete a user account"""
    if username in st.session_state.users:
        del st.session_state.users[username]
        return True
    return False