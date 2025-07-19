"""
AI Karen - Modern Streamlit Interface
Clean, intuitive design with smart navigation
"""

import streamlit as st
from typing import Dict, Any

# Import components
from components.styling import inject_modern_css, render_header
from components.navigation import render_navigation
from components.sidebar import render_global_sidebar
from components.modals import render_modal_dialog, render_drag_drop_interface
from pages.dashboard import render_interactive_dashboard
from pages.chat import render_enhanced_chat_interface

# Import helpers
from helpers.session import get_user_context
from helpers.icons import ICONS

# Import pages
from pages.plugins import render_plugins_page
from pages.settings import render_settings_page
from pages.monitoring import render_monitoring_page

# Import existing pages - with fallback functions
try:
    from src.ui_logic.pages.home import home_page
    from src.ui_logic.pages.analytics import analytics_page
    from src.ui_logic.pages.memory import memory_page
    from src.ui_logic.pages.admin import admin_page
    from src.ui_logic.pages.settings import settings_page
    from src.ui_logic.pages.presence import page as presence_page
except ImportError:
    # Fallback functions if pages don't exist
    def home_page(user_ctx=None):
        st.write("🏠 Home page - Coming soon!")
    
    def analytics_page(user_ctx=None):
        st.write("📊 Analytics page - Coming soon!")
    
    def memory_page(user_ctx=None):
        st.write("🧠 Memory page - Coming soon!")
    
    def admin_page(user_ctx=None):
        st.write("🛡️ Admin page - Coming soon!")
    
    def settings_page(user_ctx=None):
        st.write("⚙️ Settings page - Coming soon!")
    
    def presence_page(user_ctx=None):
        st.write("👥 Presence page - Coming soon!")

# Configure page
st.set_page_config(
    page_title="AI Karen",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import MirrorSnap dashboard
from pages.mirrorsnap_dashboard import render_mirrorsnap_dashboard

# Page routing
PAGES = {
    "Dashboard": {"func": home_page, "icon": "🏠", "desc": "Overview and quick actions"},
    "Chat": {"func": render_enhanced_chat_interface, "icon": "💬", "desc": "AI conversation interface"},
    "MirrorSnap": {"func": render_mirrorsnap_dashboard, "icon": "⚡️", "desc": "Operation MirrorSnap monitoring"},
    "Memory": {"func": memory_page, "icon": "🧠", "desc": "Knowledge and context management"},
    "Analytics": {"func": analytics_page, "icon": "📊", "desc": "Usage insights and metrics"},
    "Plugins": {"func": render_plugins_page, "icon": "🧩", "desc": "Extend functionality"},
    "Monitoring": {"func": render_monitoring_page, "icon": "📊", "desc": "Real-time system monitoring"},
    "Settings": {"func": render_settings_page, "icon": "⚙️", "desc": "Configuration and preferences"},
    "Admin": {"func": admin_page, "icon": "🛡️", "desc": "System administration"}
}


def render_page_content(page_name: str, user_ctx: Dict[str, Any]):
    """Render the selected page content"""
    try:
        # Enhanced Dashboard with interactive components
        if page_name == "Dashboard":
            render_interactive_dashboard()
            
            st.markdown("---")
            
            # Modal dialog demo
            st.subheader("💬 Modal Dialogs")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📊 View Details"):
                    st.session_state.show_details_modal = True
            
            with col2:
                if st.button("⚠️ Show Alert"):
                    st.session_state.show_alert_modal = True
            
            with col3:
                if st.button("ℹ️ Help Info"):
                    st.session_state.show_help_modal = True
            
            # Render modals
            if st.session_state.get('show_details_modal', False):
                with st.expander("📊 Detailed Analytics", expanded=True):
                    st.write("Here are the detailed analytics for your system performance...")
                    from components.data_utils import generate_sample_data
                    metrics_data, _ = generate_sample_data()
                    st.line_chart(metrics_data.set_index('date')['cpu_usage'])
                    if st.button("Close Details"):
                        st.session_state.show_details_modal = False
                        st.rerun()
            
            if st.session_state.get('show_alert_modal', False):
                st.error("⚠️ **System Alert**: High CPU usage detected!")
                if st.button("Acknowledge Alert"):
                    st.session_state.show_alert_modal = False
                    st.rerun()
            
            if st.session_state.get('show_help_modal', False):
                st.info("ℹ️ **Help**: Use the interactive filters to customize your dashboard view. Enable auto-refresh for real-time monitoring.")
                if st.button("Close Help"):
                    st.session_state.show_help_modal = False
                    st.rerun()
            
            st.markdown("---")
            render_drag_drop_interface()
            
        else:
            # Render original page content
            page_info = PAGES.get(page_name, PAGES['Dashboard'])
            page_info['func'](user_ctx=user_ctx)
            
    except Exception as e:
        st.error(f"Error loading {page_name}: {str(e)}")
        st.info("Please try refreshing the page.")


def main():
    """Main application"""
    # Initialize session
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'Dashboard'
    
    # Get user context
    user_ctx = get_user_context()
    
    # Apply modern styling
    inject_modern_css()
    
    # Get current page
    current_page = st.session_state.get('current_page', 'Dashboard')
    
    # Render global sidebar
    render_global_sidebar(current_page, user_ctx)
    
    # Render UI
    render_header()
    render_navigation(PAGES)
    
    # Render current page
    render_page_content(current_page, user_ctx)


if __name__ == "__main__":
    main()