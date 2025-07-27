"""
AI Karen - Modern Streamlit Interface
Clean, intuitive design with smart navigation and backend integration
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

# Import backend-integrated components
from components.backend_components import (
    render_memory_explorer,
    render_plugin_manager,
    render_system_health,
    render_page_navigator,
    render_analytics_dashboard,
    render_integrated_chat,
)

# Import helpers
from helpers.session import get_user_context
from helpers.icons import ICONS

from helpers.model_loader import (
    ensure_spacy_models,
    ensure_sklearn_installed,
    ensure_distilbert,
    ensure_basic_classifier,
)

# Import pages
from pages.plugins import render_plugins_page
from pages.settings import render_settings_page
from pages.monitoring import render_monitoring_page
from pages.profile import render_profile_page

# Import backend integration
from ai_karen_engine.services.backend_integration import get_backend_service

# Import existing pages with backend integration
try:
    from src.ui_logic.pages.home import home_page
    from src.ui_logic.pages.analytics import analytics_page
    from src.ui_logic.pages.memory import memory_page
    from src.ui_logic.pages.admin import admin_page
    from src.ui_logic.pages.settings import settings_page
    from src.ui_logic.pages.presence import page as presence_page

    BACKEND_AVAILABLE = True
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

    BACKEND_AVAILABLE = False

# Ensure lightweight models for eco mode
ensure_spacy_models()
ensure_sklearn_installed()
ensure_distilbert()
ensure_basic_classifier()

# Configure page with enhanced settings
st.set_page_config(
    page_title="AI Karen - Intelligent Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://docs.ai-karen.com",
        "Report a bug": "https://github.com/ai-karen/issues",
        "About": "AI Karen - Your intelligent AI assistant with advanced capabilities",
    },
)

# Import MirrorSnap dashboard
from pages.mirrorsnap_dashboard import render_mirrorsnap_dashboard


# Enhanced page routing with backend integration
def create_enhanced_pages():
    """Create enhanced pages with backend integration."""
    pages = {
        "Dashboard": {
            "func": home_page,
            "icon": "🏠",
            "desc": "Overview and quick actions",
        },
        "Chat": {
            "func": render_integrated_chat,
            "icon": "💬",
            "desc": "AI conversation with memory",
        },
        "Memory": {
            "func": render_memory_explorer,
            "icon": "🧠",
            "desc": "Explore and search memories",
        },
        "Analytics": {
            "func": render_analytics_dashboard,
            "icon": "📊",
            "desc": "Usage insights and metrics",
        },
        "Plugins": {
            "func": render_plugin_manager,
            "icon": "🧩",
            "desc": "Manage and execute plugins",
        },
        "System Health": {
            "func": render_system_health,
            "icon": "🏥",
            "desc": "Monitor system status",
        },
        "Page Navigator": {
            "func": render_page_navigator,
            "icon": "🧭",
            "desc": "Navigate available pages",
        },
        "Settings": {
            "func": render_settings_page,
            "icon": "⚙️",
            "desc": "Configuration and preferences",
        },
        "Profile": {
            "func": render_profile_page,
            "icon": "👤",
            "desc": "Manage your profile",
        },
        "Admin": {"func": admin_page, "icon": "🛡️", "desc": "System administration"},
    }

    # Add legacy pages if backend is available
    if BACKEND_AVAILABLE:
        pages.update(
            {
                "MirrorSnap": {
                    "func": render_mirrorsnap_dashboard,
                    "icon": "⚡️",
                    "desc": "Operation MirrorSnap monitoring",
                },
                "Monitoring": {
                    "func": render_monitoring_page,
                    "icon": "📊",
                    "desc": "Real-time system monitoring",
                },
                "Presence": {
                    "func": presence_page,
                    "icon": "👥",
                    "desc": "User presence and activity",
                },
            }
        )

        # Add integration test page for debugging
        try:
            from ai_karen_engine.services.integration_test import (
                render_integration_test_page,
            )

            pages["Integration Tests"] = {
                "func": render_integration_test_page,
                "icon": "🧪",
                "desc": "Test backend integration",
            }
        except ImportError:
            pass

    return pages


PAGES = create_enhanced_pages()


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
            if st.session_state.get("show_details_modal", False):
                with st.expander("📊 Detailed Analytics", expanded=True):
                    st.write(
                        "Here are the detailed analytics for your system performance..."
                    )
                    from components.data_utils import generate_sample_data

                    metrics_data, _ = generate_sample_data()
                    st.line_chart(metrics_data.set_index("date")["cpu_usage"])
                    if st.button("Close Details"):
                        st.session_state.show_details_modal = False
                        st.rerun()

            if st.session_state.get("show_alert_modal", False):
                st.error("⚠️ **System Alert**: High CPU usage detected!")
                if st.button("Acknowledge Alert"):
                    st.session_state.show_alert_modal = False
                    st.rerun()

            if st.session_state.get("show_help_modal", False):
                st.info(
                    "ℹ️ **Help**: Use the interactive filters to customize your dashboard view. Enable auto-refresh for real-time monitoring."
                )
                if st.button("Close Help"):
                    st.session_state.show_help_modal = False
                    st.rerun()

            st.markdown("---")
            render_drag_drop_interface()

        else:
            # Render original page content
            page_info = PAGES.get(page_name, PAGES["Dashboard"])
            page_info["func"](user_ctx=user_ctx)

    except Exception as e:
        st.error(f"Error loading {page_name}: {str(e)}")
        st.info("Please try refreshing the page.")


def main():
    """Enhanced main application with comprehensive theming and navigation"""
    # Initialize session and theme system
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Dashboard"

    # Initialize theme system
    from config.theme import get_theme_manager, apply_default_theme

    theme_manager = get_theme_manager()

    # Apply theme early for consistent styling
    apply_default_theme()

    # Initialize backend integration
    if BACKEND_AVAILABLE:
        try:
            from ai_karen_engine.services.data_flow_manager import (
                get_data_flow_manager,
                get_streamlit_bridge,
            )

            # Initialize data flow manager
            dfm = get_data_flow_manager()
            bridge = get_streamlit_bridge()

            # Update backend service with user context
            backend = get_backend_service()
            user_ctx = get_user_context()
            backend.update_user_context(
                user_id=user_ctx.get("user_id", "anonymous"),
                session_id=user_ctx.get("session_id", "default"),
                roles=user_ctx.get("roles", ["user"]),
            )

            st.session_state.backend_integrated = True
        except Exception as e:
            st.warning(f"Backend integration partially available: {e}")
            st.session_state.backend_integrated = False
    else:
        st.session_state.backend_integrated = False

    # Get user context and initialize RBAC
    user_ctx = get_user_context()
    from helpers.rbac import initialize_rbac

    initialize_rbac()

    # Apply enhanced modern styling with theme integration
    inject_modern_css()

    # Store pages config in session state for navigation
    st.session_state.pages_config = PAGES

    # Get current page
    current_page = st.session_state.get("current_page", "Dashboard")

    # Render enhanced sidebar with theme selector and navigation features
    render_enhanced_sidebar(current_page, user_ctx)

    # Show debug information if enabled
    if st.session_state.get("show_debug_info", False):
        render_debug_panel()

    # Render enhanced UI components
    render_header()

    # Add theme selector in main area if requested
    if st.session_state.get("show_theme_settings", False):
        render_theme_settings_modal()

    # Render enhanced navigation
    render_navigation(PAGES)

    # Render current page content
    render_page_content(current_page, user_ctx)

    # Add footer with system information
    render_footer()


def render_enhanced_sidebar(current_page: str, user_ctx: Dict[str, Any]):
    """Render enhanced sidebar with theme controls and navigation features."""
    from components.styling import render_theme_selector
    from components.navigation import (
        render_favorites_menu,
        render_recent_pages,
        render_page_search,
    )
    from helpers.rbac import render_role_badge, get_user_capabilities

    with st.sidebar:
        # User info section
        st.markdown("### 👤 User Info")
        username = user_ctx.get("username", "Anonymous User")
        st.write(f"**Welcome, {username}!**")
        render_role_badge(user_ctx)

        # User capabilities
        capabilities = get_user_capabilities(user_ctx)
        if st.expander("🔐 Your Permissions"):
            for capability, has_access in capabilities.items():
                icon = "✅" if has_access else "❌"
                st.write(f"{icon} {capability.replace('_', ' ').title()}")

        st.markdown("---")

        # Page search
        render_page_search()

        st.markdown("---")

        # Navigation features
        render_favorites_menu()
        render_recent_pages()

        st.markdown("---")

        # Theme selector
        render_theme_selector()

        st.markdown("---")

        # System status
        st.markdown("### 📊 System Status")
        backend_status = (
            "✅ Connected"
            if st.session_state.get("backend_integrated")
            else "⚠️ Limited"
        )
        st.write(f"**Backend:** {backend_status}")

        # Quick settings
        st.markdown("### ⚙️ Quick Settings")

        # Debug mode toggle
        debug_mode = st.checkbox(
            "Debug Mode", value=st.session_state.get("show_debug_info", False)
        )
        st.session_state.show_debug_info = debug_mode

        # Auto-refresh toggle
        auto_refresh = st.checkbox(
            "Auto Refresh", value=st.session_state.get("auto_refresh", False)
        )
        st.session_state.auto_refresh = auto_refresh

        if auto_refresh:
            refresh_interval = st.slider("Refresh Interval (seconds)", 5, 60, 30)
            st.session_state.refresh_interval = refresh_interval

        # Compact mode toggle
        compact_mode = st.checkbox(
            "Compact Mode", value=st.session_state.get("compact_mode", False)
        )
        st.session_state.compact_mode = compact_mode


def render_debug_panel():
    """Render debug information panel."""
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🔧 Debug Info")

        # Backend status
        backend_status = (
            "✅ Connected"
            if st.session_state.get("backend_integrated")
            else "⚠️ Limited"
        )
        st.write(f"**Backend:** {backend_status}")

        # Session state info
        if st.expander("📋 Session State"):
            session_keys = list(st.session_state.keys())
            st.write(f"**Keys:** {len(session_keys)}")
            for key in sorted(session_keys):
                if not key.startswith("_"):  # Hide internal keys
                    value = str(st.session_state[key])[:50]
                    st.write(f"• {key}: {value}...")

        # Theme info
        from config.theme import get_current_theme, get_theme_manager

        current_theme = get_current_theme()
        theme_manager = get_theme_manager()
        theme_config = theme_manager.get_theme_config(current_theme)

        if st.expander("🎨 Theme Info"):
            st.write(f"**Current Theme:** {current_theme}")
            if theme_config:
                st.write(f"**Display Name:** {theme_config.display_name}")
                st.write(f"**Category:** {theme_config.category}")
                st.write(f"**Primary Color:** {theme_config.primary_color}")

        # Data flow status
        if BACKEND_AVAILABLE and st.session_state.get("backend_integrated"):
            try:
                from ai_karen_engine.services.data_flow_manager import (
                    render_data_flow_status,
                )

                render_data_flow_status()
            except ImportError:
                pass


def render_theme_settings_modal():
    """Render theme settings modal."""
    from config.theme import get_theme_manager

    st.markdown("## 🎨 Theme Settings")

    theme_manager = get_theme_manager()

    # Theme selector
    selected_theme = theme_manager.create_theme_selector()

    # Theme customization options
    with st.expander("🛠️ Advanced Theme Options"):
        st.markdown("### Theme Import/Export")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("📤 Export Current Theme"):
                current_theme = theme_manager.get_current_theme()
                theme_data = theme_manager.export_theme(current_theme)
                if theme_data:
                    st.download_button(
                        "Download Theme",
                        data=str(theme_data),
                        file_name=f"{current_theme}_theme.json",
                        mime="application/json",
                    )

        with col2:
            uploaded_file = st.file_uploader("📥 Import Theme", type=["json"])
            if uploaded_file:
                try:
                    import json

                    theme_data = json.load(uploaded_file)
                    if theme_manager.import_theme(theme_data):
                        st.success("Theme imported successfully!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Failed to import theme: {e}")

    # Close button
    if st.button("✖️ Close Theme Settings"):
        st.session_state.show_theme_settings = False
        st.rerun()


def render_footer():
    """Render application footer with system information."""
    from datetime import datetime
    from config.theme import get_current_theme

    current_theme = get_current_theme()
    current_time = datetime.now().strftime("%H:%M:%S")

    footer_html = f"""
    <div style="
        margin-top: 3rem;
        padding: 2rem 0 1rem;
        border-top: 1px solid var(--border, #e2e8f0);
        text-align: center;
        color: var(--secondary, #64748b);
        font-size: 0.85rem;
    ">
        <div style="display: flex; justify-content: center; align-items: center; gap: 2rem; flex-wrap: wrap;">
            <span>🤖 AI Karen v2.0</span>
            <span>🎨 Theme: {current_theme.title()}</span>
            <span>🕒 {current_time}</span>
            <span>💚 System Healthy</span>
        </div>
        <div style="margin-top: 0.5rem; font-size: 0.75rem;">
            Built with ❤️ using Streamlit • Enhanced UI Framework
        </div>
    </div>
    """

    st.markdown(footer_html, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
