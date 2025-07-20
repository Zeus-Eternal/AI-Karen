"""
Enhanced Navigation Components for AI Karen Streamlit UI
Provides role-based navigation with contextual menus and theme integration.
"""

import streamlit as st
from typing import Dict, Any, List, Optional
from helpers.session import get_user_context
from helpers.rbac import check_user_access


class NavigationManager:
    """Manages navigation state and role-based access."""
    
    def __init__(self):
        self.current_page = st.session_state.get('current_page', 'Dashboard')
        self.user_context = get_user_context()
        self.navigation_history = st.session_state.get('navigation_history', [])
        self.favorites = st.session_state.get('favorite_pages', [])
        self.recent_pages = st.session_state.get('recent_pages', [])
    
    def navigate_to(self, page_name: str):
        """Navigate to a specific page with history tracking."""
        if page_name != self.current_page:
            # Add to history
            if self.current_page not in self.navigation_history:
                self.navigation_history.append(self.current_page)
            
            # Add to recent pages
            if page_name in self.recent_pages:
                self.recent_pages.remove(page_name)
            self.recent_pages.insert(0, page_name)
            self.recent_pages = self.recent_pages[:5]  # Keep only 5 recent
            
            # Update session state
            st.session_state.current_page = page_name
            st.session_state.navigation_history = self.navigation_history
            st.session_state.recent_pages = self.recent_pages
            
            st.rerun()
    
    def go_back(self):
        """Navigate back to previous page."""
        if self.navigation_history:
            previous_page = self.navigation_history.pop()
            st.session_state.current_page = previous_page
            st.session_state.navigation_history = self.navigation_history
            st.rerun()
    
    def toggle_favorite(self, page_name: str):
        """Toggle page favorite status."""
        if page_name in self.favorites:
            self.favorites.remove(page_name)
        else:
            self.favorites.append(page_name)
        
        st.session_state.favorite_pages = self.favorites
    
    def is_favorite(self, page_name: str) -> bool:
        """Check if page is favorited."""
        return page_name in self.favorites
    
    def has_access(self, page_config: Dict[str, Any]) -> bool:
        """Check if user has access to a page."""
        required_roles = page_config.get('required_roles', [])
        if not required_roles:
            return True
        
        return check_user_access(self.user_context, required_roles)
    
    def filter_accessible_pages(self, pages_config: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Filter pages based on user access."""
        accessible_pages = {}
        for page_name, page_config in pages_config.items():
            if self.has_access(page_config):
                accessible_pages[page_name] = page_config
        return accessible_pages


def render_breadcrumb_navigation():
    """Render breadcrumb navigation."""
    nav_manager = NavigationManager()
    
    if nav_manager.navigation_history:
        breadcrumb_html = """
        <div style="
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 0;
            font-size: 0.9rem;
            color: var(--secondary, #64748b);
            margin-bottom: 1rem;
        ">
        """
        
        # Add home link
        breadcrumb_html += """
        <span style="cursor: pointer; color: var(--primary, #2563eb);" onclick="window.location.reload()">
            🏠 Home
        </span>
        """
        
        # Add breadcrumb trail
        for i, page in enumerate(nav_manager.navigation_history[-3:]):  # Show last 3
            breadcrumb_html += f"""
            <span>›</span>
            <span style="cursor: pointer; color: var(--primary, #2563eb);">
                {page}
            </span>
            """
        
        # Add current page
        breadcrumb_html += f"""
        <span>›</span>
        <span style="font-weight: 500; color: var(--text, #1e293b);">
            {nav_manager.current_page}
        </span>
        </div>
        """
        
        st.markdown(breadcrumb_html, unsafe_allow_html=True)


def render_quick_actions():
    """Render quick action buttons."""
    nav_manager = NavigationManager()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("⬅️ Back", disabled=not nav_manager.navigation_history):
            nav_manager.go_back()
    
    with col2:
        if st.button("🏠 Home"):
            nav_manager.navigate_to("Dashboard")
    
    with col3:
        if st.button("🔄 Refresh"):
            st.rerun()
    
    with col4:
        if st.button("⚙️ Settings"):
            nav_manager.navigate_to("Settings")


def render_favorites_menu():
    """Render favorites menu in sidebar."""
    nav_manager = NavigationManager()
    
    if nav_manager.favorites:
        st.sidebar.markdown("### ⭐ Favorites")
        for page_name in nav_manager.favorites:
            if st.sidebar.button(f"⭐ {page_name}", key=f"fav_{page_name}"):
                nav_manager.navigate_to(page_name)


def render_recent_pages():
    """Render recent pages menu in sidebar."""
    nav_manager = NavigationManager()
    
    if nav_manager.recent_pages:
        st.sidebar.markdown("### 🕒 Recent")
        for page_name in nav_manager.recent_pages:
            if st.sidebar.button(f"🕒 {page_name}", key=f"recent_{page_name}"):
                nav_manager.navigate_to(page_name)


def render_contextual_menu(page_name: str, page_config: Dict[str, Any]):
    """Render contextual menu for a page."""
    nav_manager = NavigationManager()
    
    with st.popover("⋮", help="Page options"):
        # Favorite toggle
        fav_icon = "⭐" if nav_manager.is_favorite(page_name) else "☆"
        if st.button(f"{fav_icon} {'Remove from' if nav_manager.is_favorite(page_name) else 'Add to'} favorites"):
            nav_manager.toggle_favorite(page_name)
            st.rerun()
        
        # Page info
        st.markdown(f"**Description:** {page_config.get('desc', 'No description')}")
        
        # Additional actions based on page type
        if page_name == "Settings":
            if st.button("🎨 Theme Settings"):
                st.session_state.show_theme_settings = True
                st.rerun()
        
        elif page_name == "Dashboard":
            if st.button("📊 Customize Dashboard"):
                st.session_state.show_dashboard_customization = True
                st.rerun()


def render_navigation(pages_config: Dict[str, Dict[str, Any]]):
    """Enhanced navigation with role-based access and contextual features."""
    nav_manager = NavigationManager()
    
    # Filter pages based on user access
    accessible_pages = nav_manager.filter_accessible_pages(pages_config)
    
    if not accessible_pages:
        st.error("No accessible pages found. Please contact your administrator.")
        return
    
    # Render breadcrumb navigation
    render_breadcrumb_navigation()
    
    # Group pages by category for better organization
    categorized_pages = {}
    for page_name, page_config in accessible_pages.items():
        category = page_config.get('category', 'General')
        if category not in categorized_pages:
            categorized_pages[category] = {}
        categorized_pages[category][page_name] = page_config
    
    # Render navigation container
    st.markdown("""
    <div class="nav-container fade-in">
        <div class="nav-pills">
    """, unsafe_allow_html=True)
    
    # Create navigation pills
    current_page = nav_manager.current_page
    
    # Calculate columns based on number of pages
    max_cols = min(len(accessible_pages), 6)  # Max 6 columns
    cols = st.columns(max_cols)
    
    for i, (page_name, page_config) in enumerate(accessible_pages.items()):
        col_index = i % max_cols
        
        with cols[col_index]:
            # Create navigation button with enhanced styling
            is_active = current_page == page_name
            button_class = "nav-pill active" if is_active else "nav-pill"
            
            # Create button with contextual menu
            button_col, menu_col = st.columns([4, 1])
            
            with button_col:
                button_type = "primary" if is_active else "secondary"
                if st.button(
                    f"{page_config['icon']} {page_name}",
                    key=f"nav_{page_name}",
                    help=page_config['desc'],
                    use_container_width=True,
                    type=button_type
                ):
                    nav_manager.navigate_to(page_name)
            
            with menu_col:
                render_contextual_menu(page_name, page_config)
    
    st.markdown("""
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Render quick actions
    with st.expander("🚀 Quick Actions", expanded=False):
        render_quick_actions()
    
    # Show page statistics
    if st.session_state.get('show_debug_info', False):
        with st.expander("📊 Navigation Stats", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Pages", len(pages_config))
            
            with col2:
                st.metric("Accessible Pages", len(accessible_pages))
            
            with col3:
                st.metric("Favorites", len(nav_manager.favorites))
            
            if nav_manager.recent_pages:
                st.markdown("**Recent Pages:**")
                for page in nav_manager.recent_pages:
                    st.write(f"• {page}")


def render_mobile_navigation(pages_config: Dict[str, Dict[str, Any]]):
    """Render mobile-optimized navigation."""
    nav_manager = NavigationManager()
    accessible_pages = nav_manager.filter_accessible_pages(pages_config)
    
    # Mobile navigation with dropdown
    page_options = list(accessible_pages.keys())
    current_index = page_options.index(nav_manager.current_page) if nav_manager.current_page in page_options else 0
    
    selected_page = st.selectbox(
        "Navigate to:",
        options=page_options,
        index=current_index,
        format_func=lambda x: f"{accessible_pages[x]['icon']} {x}",
        key="mobile_nav"
    )
    
    if selected_page != nav_manager.current_page:
        nav_manager.navigate_to(selected_page)


def render_page_search():
    """Render page search functionality."""
    nav_manager = NavigationManager()
    
    search_query = st.text_input("🔍 Search pages...", placeholder="Type to search pages")
    
    if search_query:
        # Filter pages based on search query
        matching_pages = {}
        for page_name, page_config in nav_manager.filter_accessible_pages(st.session_state.get('pages_config', {})).items():
            if (search_query.lower() in page_name.lower() or 
                search_query.lower() in page_config.get('desc', '').lower()):
                matching_pages[page_name] = page_config
        
        if matching_pages:
            st.markdown("**Search Results:**")
            for page_name, page_config in matching_pages.items():
                if st.button(f"{page_config['icon']} {page_name}", key=f"search_{page_name}"):
                    nav_manager.navigate_to(page_name)
        else:
            st.info("No pages found matching your search.")


def initialize_navigation():
    """Initialize navigation system."""
    if 'navigation_initialized' not in st.session_state:
        st.session_state.navigation_initialized = True
        st.session_state.current_page = st.session_state.get('current_page', 'Dashboard')
        st.session_state.navigation_history = []
        st.session_state.favorite_pages = []
        st.session_state.recent_pages = []


# Auto-initialize navigation
initialize_navigation()