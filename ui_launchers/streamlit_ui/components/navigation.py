"""
Navigation components for the Streamlit UI
"""

import streamlit as st


def render_navigation(pages_config):
    """Modern pill navigation using Streamlit components"""
    current_page = st.session_state.get('current_page', 'Dashboard')
    
    # Navigation section with title
    st.markdown("### 🧭 Navigation")
    
    # Streamlit navigation with improved styling
    cols = st.columns(len(pages_config))
    for i, (page_name, page_info) in enumerate(pages_config.items()):
        with cols[i]:
            # Use different button style for active page
            button_type = "primary" if current_page == page_name else "secondary"
            if st.button(f"{page_info['icon']} {page_name}", 
                        key=f"nav_{page_name}",
                        help=page_info['desc'],
                        use_container_width=True,
                        type=button_type):
                st.session_state.current_page = page_name
                st.rerun()
    
    # Add some spacing after navigation
    st.markdown("---")