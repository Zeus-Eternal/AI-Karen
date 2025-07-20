"""
Global sidebar components for the Streamlit UI
"""

import streamlit as st
from datetime import datetime


def render_global_sidebar(current_page: str, user_ctx: dict):
    """Render global sidebar with page-specific content"""
    
    with st.sidebar:
        # User info section
        st.markdown("### 👤 User Info")
        if user_ctx.get('user_id'):
            st.write(f"**User:** {user_ctx['user_id']}")
            st.write(f"**Roles:** {', '.join(user_ctx.get('roles', ['Guest']))}")
        else:
            st.write("**Status:** Guest User")
            if st.button("🔐 Login", use_container_width=True):
                st.info("Login functionality would be implemented here")
        
        st.markdown("---")
        
        # Page-specific sidebar content
        if current_page == "Chat":
            render_chat_sidebar()
        elif current_page == "Dashboard":
            render_dashboard_sidebar()
        elif current_page == "Analytics":
            render_analytics_sidebar()
        else:
            render_default_sidebar(current_page)


def render_chat_sidebar():
    """Chat-specific sidebar content"""
    # Model selection
    st.markdown("### 🤖 AI Model Selection")
    
    # Get available models
    try:
        from services.chat_service import chat_service
        models = chat_service.get_available_models()
        
        if models:
            model_names = [model.get("name", "Unknown") for model in models if model.get("name")]
            if model_names:
                selected_model = st.selectbox(
                    "Choose AI Model",
                    model_names,
                    key="selected_model",
                    help="Select which AI model to use for conversations"
                )
                
                if st.button("🔄 Switch Model", use_container_width=True):
                    if chat_service.select_model(selected_model):
                        st.success(f"✅ Switched to {selected_model}")
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to switch to {selected_model}")
            else:
                st.warning("No named models available")
        else:
            st.warning("No models available from backend")
            
        # System health indicator
        health = chat_service.get_system_health()
        if health.get("status") == "ok":
            st.success("🟢 Backend Connected")
        else:
            st.error(f"🔴 Backend Issue: {health.get('message', 'Unknown error')}")
            
    except Exception as e:
        st.error(f"⚠️ Model service unavailable: {str(e)}")
    
    st.markdown("---")
    
    st.markdown("### 📚 Conversation History")
    
    # Search conversations
    search_query = st.text_input("🔍 Search conversations", placeholder="Search messages...", key="sidebar_chat_search")
    
    # Conversation list
    conversations = [
        {"id": 1, "title": "System Setup Help", "date": "2024-07-19", "messages": 15},
        {"id": 2, "title": "Plugin Configuration", "date": "2024-07-18", "messages": 8},
        {"id": 3, "title": "Performance Optimization", "date": "2024-07-17", "messages": 22},
        {"id": 4, "title": "Database Migration", "date": "2024-07-16", "messages": 12},
    ]
    
    for conv in conversations:
        if not search_query or search_query.lower() in conv["title"].lower():
            with st.expander(f"💬 {conv['title']}", expanded=False):
                st.write(f"📅 {conv['date']}")
                st.write(f"💬 {conv['messages']} messages")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📂 Load", key=f"load_{conv['id']}"):
                        st.session_state.current_conversation = conv['id']
                        st.rerun()
                with col2:
                    if st.button("🗑️ Delete", key=f"del_{conv['id']}"):
                        st.session_state.delete_conversation = conv['id']
                        st.rerun()
    
    st.markdown("---")
    if st.button("➕ New Conversation", use_container_width=True):
        st.session_state.chat_messages = [
            {"role": "assistant", "content": "Hello! I'm AI Karen, your intelligent assistant. How can I help you today?", "timestamp": datetime.now(), "attachments": []},
        ]
        st.rerun()


def render_dashboard_sidebar():
    """Dashboard-specific sidebar content"""
    st.markdown("### ⚙️ Dashboard Settings")
    
    # Dashboard preferences
    auto_refresh = st.checkbox("🔄 Auto-refresh", value=True)
    refresh_interval = st.selectbox("Refresh Interval", [5, 10, 30, 60], index=2)
    
    st.markdown("### 📊 Quick Stats")
    st.metric("System Health", "94%", "2%")
    st.metric("Active Users", "342", "12")
    st.metric("CPU Usage", "45%", "-3%")
    
    st.markdown("### 🔗 Quick Links")
    if st.button("📈 View Full Analytics", use_container_width=True):
        st.session_state.current_page = 'Analytics'
        st.rerun()
    
    if st.button("💬 Open Chat", use_container_width=True):
        st.session_state.current_page = 'Chat'
        st.rerun()


def render_analytics_sidebar():
    """Analytics-specific sidebar content"""
    st.markdown("### 📊 Analytics Filters")
    
    # Time range selector
    time_range = st.selectbox("Time Range", ["Last 24 hours", "Last 7 days", "Last 30 days", "Last 90 days"])
    
    # Metric selector
    metrics = st.multiselect("Metrics", ["CPU", "Memory", "Network", "Requests", "Errors"], default=["CPU", "Memory"])
    
    # Export options
    st.markdown("### 📤 Export")
    if st.button("📊 Export Charts", use_container_width=True):
        st.info("Export functionality would be implemented here")
    
    if st.button("📋 Export Data", use_container_width=True):
        st.info("Data export functionality would be implemented here")


def render_default_sidebar(page_name: str):
    """Default sidebar content for other pages"""
    st.markdown(f"### 📄 {page_name} Tools")
    
    st.markdown("### 🔧 Quick Actions")
    if st.button("🏠 Go to Dashboard", use_container_width=True):
        st.session_state.current_page = 'Dashboard'
        st.rerun()
    
    if st.button("💬 Open Chat", use_container_width=True):
        st.session_state.current_page = 'Chat'
        st.rerun()
    
    st.markdown("### ℹ️ Help")
    st.info(f"You are currently on the {page_name} page. Use the navigation buttons above to switch between different sections of AI Karen.")