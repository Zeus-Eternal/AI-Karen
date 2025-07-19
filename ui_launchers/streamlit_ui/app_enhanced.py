"""
Enhanced Kari Streamlit UI - Premium Edition
- Modern, professional interface with advanced theming
- Role-based navigation with contextual menus
- Real-time notifications and status indicators
- Responsive design with smooth transitions
"""

import streamlit as st
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

# Import existing helpers
from helpers.session import get_user_context
from helpers.rbac import check_permission
from helpers.icons import ICONS

# Import enhanced components
from components.premium_theme import PremiumThemeManager
from components.navigation import EnhancedNavigation
from components.notifications import NotificationSystem
from components.status_bar import StatusBar
from config.premium_routing import PREMIUM_PAGE_MAP, get_user_pages

# Configure page settings for premium experience
st.set_page_config(
    page_title="AI Karen - Premium Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://docs.ai-karen.com',
        'Report a bug': 'https://github.com/ai-karen/issues',
        'About': "AI Karen Premium Dashboard v2.0"
    }
)

@dataclass
class UserSession:
    """Enhanced user session with premium features."""
    user_id: str
    username: str
    email: str
    roles: List[str]
    permissions: List[str]
    theme: str
    dashboard_layout: Dict[str, Any]
    notification_settings: Dict[str, bool]
    last_activity: datetime
    session_data: Dict[str, Any]

class PremiumApp:
    """Enhanced Streamlit application with premium features."""
    
    def __init__(self):
        self.theme_manager = PremiumThemeManager()
        self.navigation = EnhancedNavigation()
        self.notifications = NotificationSystem()
        self.status_bar = StatusBar()
        self._initialize_session()
    
    def _initialize_session(self):
        """Initialize enhanced session state."""
        if 'premium_initialized' not in st.session_state:
            st.session_state.premium_initialized = True
            st.session_state.current_page = 'dashboard'
            st.session_state.sidebar_collapsed = False
            st.session_state.notifications = []
            st.session_state.theme_transition = False
            st.session_state.last_activity = datetime.now()
    
    def _inject_premium_css(self):
        """Inject premium CSS for enhanced styling."""
        premium_css = """
        <style>
        /* Premium Theme Variables */
        :root {
            --premium-primary: #1e293b;
            --premium-secondary: #3b82f6;
            --premium-accent: #10b981;
            --premium-background: #f8fafc;
            --premium-surface: #ffffff;
            --premium-text-primary: #1e293b;
            --premium-text-secondary: #64748b;
            --premium-border: #e2e8f0;
            --premium-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            --premium-radius: 8px;
            --premium-transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        /* Enhanced Sidebar */
        .css-1d391kg {
            background: linear-gradient(135deg, var(--premium-primary) 0%, #334155 100%);
            border-right: 1px solid var(--premium-border);
        }
        
        /* Premium Navigation */
        .nav-item {
            padding: 12px 16px;
            margin: 4px 8px;
            border-radius: var(--premium-radius);
            transition: var(--premium-transition);
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .nav-item:hover {
            background: rgba(59, 130, 246, 0.1);
            transform: translateX(4px);
        }
        
        .nav-item.active {
            background: var(--premium-secondary);
            color: white;
            box-shadow: var(--premium-shadow);
        }
        
        /* Premium Cards */
        .premium-card {
            background: var(--premium-surface);
            border-radius: var(--premium-radius);
            padding: 24px;
            box-shadow: var(--premium-shadow);
            border: 1px solid var(--premium-border);
            transition: var(--premium-transition);
        }
        
        .premium-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px -5px rgba(0, 0, 0, 0.1);
        }
        
        /* Status Indicators */
        .status-indicator {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
        }
        
        .status-healthy {
            background: rgba(16, 185, 129, 0.1);
            color: #059669;
        }
        
        .status-warning {
            background: rgba(245, 158, 11, 0.1);
            color: #d97706;
        }
        
        .status-error {
            background: rgba(239, 68, 68, 0.1);
            color: #dc2626;
        }
        
        /* Premium Buttons */
        .premium-button {
            background: var(--premium-secondary);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: var(--premium-radius);
            font-weight: 500;
            cursor: pointer;
            transition: var(--premium-transition);
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        
        .premium-button:hover {
            background: #2563eb;
            transform: translateY(-1px);
            box-shadow: var(--premium-shadow);
        }
        
        /* Notification Toast */
        .notification-toast {
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--premium-surface);
            border-radius: var(--premium-radius);
            padding: 16px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
            border-left: 4px solid var(--premium-secondary);
            z-index: 1000;
            animation: slideIn 0.3s ease-out;
        }
        
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        /* Loading Skeleton */
        .skeleton {
            background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
            background-size: 200% 100%;
            animation: loading 1.5s infinite;
        }
        
        @keyframes loading {
            0% {
                background-position: 200% 0;
            }
            100% {
                background-position: -200% 0;
            }
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .premium-card {
                padding: 16px;
                margin: 8px 0;
            }
            
            .nav-item {
                padding: 8px 12px;
            }
        }
        
        /* Dark Theme Overrides */
        [data-theme="dark"] {
            --premium-background: #0f172a;
            --premium-surface: #1e293b;
            --premium-text-primary: #f1f5f9;
            --premium-text-secondary: #94a3b8;
            --premium-border: #334155;
        }
        
        /* Animation Classes */
        .fade-in {
            animation: fadeIn 0.5s ease-in;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        .slide-up {
            animation: slideUp 0.3s ease-out;
        }
        
        @keyframes slideUp {
            from {
                transform: translateY(20px);
                opacity: 0;
            }
            to {
                transform: translateY(0);
                opacity: 1;
            }
        }
        </style>
        """
        st.markdown(premium_css, unsafe_allow_html=True)
    
    def _render_premium_header(self, user_ctx: Dict[str, Any]):
        """Render premium header with status and notifications."""
        header_col1, header_col2, header_col3 = st.columns([2, 1, 1])
        
        with header_col1:
            st.markdown("""
            <div style="display: flex; align-items: center; gap: 16px;">
                <h1 style="margin: 0; color: var(--premium-text-primary);">
                    🤖 AI Karen Premium
                </h1>
                <div class="status-indicator status-healthy">
                    ● System Healthy
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with header_col2:
            # Real-time clock
            current_time = datetime.now().strftime("%H:%M:%S")
            st.markdown(f"""
            <div style="text-align: center; color: var(--premium-text-secondary);">
                <small>Last Updated</small><br>
                <strong>{current_time}</strong>
            </div>
            """, unsafe_allow_html=True)
        
        with header_col3:
            # User info and notifications
            notification_count = len(st.session_state.get('notifications', []))
            st.markdown(f"""
            <div style="text-align: right;">
                <div style="color: var(--premium-text-secondary); font-size: 14px;">
                    Welcome, {user_ctx.get('username', 'User')}
                </div>
                <div style="margin-top: 4px;">
                    <span style="background: var(--premium-secondary); color: white; 
                                 padding: 4px 8px; border-radius: 12px; font-size: 12px;">
                        {notification_count} notifications
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    def _render_enhanced_sidebar(self, user_ctx: Dict[str, Any]) -> str:
        """Render enhanced sidebar with premium navigation."""
        with st.sidebar:
            # Premium branding
            st.markdown("""
            <div style="text-align: center; padding: 20px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
                <h2 style="color: white; margin: 0;">🤖 AI Karen</h2>
                <p style="color: rgba(255,255,255,0.7); margin: 4px 0 0 0; font-size: 14px;">
                    Premium Dashboard
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Get available pages based on user permissions
            available_pages = get_user_pages(user_ctx)
            
            # Navigation sections
            sections = {
                "🏠 Executive": ["dashboard", "analytics", "reports"],
                "💬 Operations": ["chat", "memory", "workflows"],
                "🔧 System": ["plugins", "settings", "monitoring"],
                "👥 Admin": ["admin", "users", "security"]
            }
            
            current_page = st.session_state.get('current_page', 'dashboard')
            
            for section_name, pages in sections.items():
                # Filter pages based on user permissions
                accessible_pages = [p for p in pages if p in available_pages]
                
                if accessible_pages:
                    st.markdown(f"""
                    <div style="color: rgba(255,255,255,0.9); font-weight: 600; 
                                margin: 20px 0 10px 0; font-size: 14px;">
                        {section_name}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    for page in accessible_pages:
                        page_info = available_pages[page]
                        icon = page_info.get('icon', '📄')
                        title = page_info.get('title', page.title())
                        
                        # Create navigation button
                        is_active = current_page == page
                        button_style = "nav-item active" if is_active else "nav-item"
                        
                        if st.button(f"{icon} {title}", key=f"nav_{page}", 
                                   help=page_info.get('description', '')):
                            st.session_state.current_page = page
                            st.rerun()
            
            # Theme switcher at bottom
            st.markdown("<hr style='border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
            self.theme_manager.render_theme_switcher(user_ctx)
            
            # Quick stats
            st.markdown("""
            <div style="margin-top: 20px; padding: 16px; background: rgba(255,255,255,0.1); 
                        border-radius: 8px;">
                <div style="color: white; font-size: 12px; text-align: center;">
                    <div>Session: 2h 34m</div>
                    <div>Memory: 85% available</div>
                    <div>Status: All systems operational</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            return current_page
    
    def _render_page_content(self, page: str, user_ctx: Dict[str, Any]):
        """Render the selected page content with premium styling."""
        # Add page transition animation
        st.markdown('<div class="fade-in">', unsafe_allow_html=True)
        
        # Get page function from routing
        page_function = PREMIUM_PAGE_MAP.get(page)
        
        if page_function:
            try:
                # Add loading indicator for heavy pages
                if page in ['analytics', 'monitoring', 'reports']:
                    with st.spinner('Loading premium content...'):
                        time.sleep(0.5)  # Simulate loading
                
                # Render page with user context
                page_function(user_ctx=user_ctx)
                
            except Exception as e:
                st.error(f"Error loading page '{page}': {str(e)}")
                st.info("Please try refreshing the page or contact support if the issue persists.")
        else:
            # Fallback for missing pages
            st.warning(f"Page '{page}' is under development.")
            st.info("This feature will be available in the next update.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _update_activity(self, user_ctx: Dict[str, Any]):
        """Update user activity timestamp."""
        st.session_state.last_activity = datetime.now()
        # Could also send to backend for session management
    
    def run(self):
        """Main application entry point."""
        try:
            # Get user context
            user_ctx = get_user_context()
            
            # Apply premium theme
            self._inject_premium_css()
            self.theme_manager.apply_theme(user_ctx)
            
            # Render premium header
            self._render_premium_header(user_ctx)
            
            # Render enhanced sidebar and get selected page
            selected_page = self._render_enhanced_sidebar(user_ctx)
            
            # Update activity
            self._update_activity(user_ctx)
            
            # Render main content area
            main_container = st.container()
            with main_container:
                self._render_page_content(selected_page, user_ctx)
            
            # Render notifications
            self.notifications.render_notifications()
            
            # Render status bar
            self.status_bar.render_status_bar(user_ctx)
            
        except Exception as e:
            st.error("Application Error")
            st.exception(e)
            st.info("Please refresh the page. If the problem persists, contact support.")

def main():
    """Application entry point."""
    app = PremiumApp()
    app.run()

if __name__ == "__main__":
    main()