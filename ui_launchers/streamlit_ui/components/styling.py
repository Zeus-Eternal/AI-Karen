"""
Enhanced Styling and CSS Components for AI Karen Streamlit UI
Provides comprehensive styling with theme integration, animations, and responsive design.
"""

import streamlit as st
from typing import Dict, Any, Optional
from config.theme import get_theme_manager, get_current_theme


def inject_foundation_css():
    """Inject foundational CSS that works with all themes."""
    foundation_css = """
    <style>
    /* Hide Streamlit branding and clean up interface */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    
    /* Import modern fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Base reset and typography */
    * {
        box-sizing: border-box;
    }
    
    html, body {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }
    
    /* Main container enhancements */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 1400px;
        margin: 0 auto;
    }
    
    /* Streamlit component overrides */
    .stApp {
        transition: all 0.3s ease;
    }
    
    /* Enhanced sidebar */
    .stSidebar {
        transition: all 0.3s ease;
    }
    
    .stSidebar .sidebar-content {
        padding-top: 2rem;
    }
    
    /* Button enhancements */
    .stButton > button {
        font-weight: 500;
        border-radius: var(--border-radius, 8px);
        transition: all 0.2s ease;
        border: none;
        box-shadow: var(--shadow, 0 1px 3px rgba(0,0,0,0.1));
        font-family: inherit;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* Input field enhancements */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select,
    .stNumberInput > div > div > input {
        border-radius: var(--border-radius, 8px);
        transition: all 0.2s ease;
        font-family: inherit;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus,
    .stNumberInput > div > div > input:focus {
        box-shadow: 0 0 0 2px var(--primary, #2563eb);
        border-color: var(--primary, #2563eb);
    }
    
    /* Metric enhancements */
    .stMetric {
        background: var(--surface, #ffffff);
        padding: 1.5rem;
        border-radius: var(--border-radius, 8px);
        border: 1px solid var(--border, #e2e8f0);
        box-shadow: var(--shadow, 0 1px 3px rgba(0,0,0,0.1));
        transition: all 0.2s ease;
    }
    
    .stMetric:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    /* Tab enhancements */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: var(--surface, #ffffff);
        padding: 0.5rem;
        border-radius: var(--border-radius, 8px);
        border: 1px solid var(--border, #e2e8f0);
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: calc(var(--border-radius, 8px) - 2px);
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--primary, #2563eb);
        color: white;
    }
    
    /* Expander enhancements */
    .streamlit-expanderHeader {
        background: var(--surface, #ffffff);
        border: 1px solid var(--border, #e2e8f0);
        border-radius: var(--border-radius, 8px);
        transition: all 0.2s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background: var(--background, #f8fafc);
    }
    
    /* Alert enhancements */
    .stAlert {
        border-radius: var(--border-radius, 8px);
        border: none;
        box-shadow: var(--shadow, 0 1px 3px rgba(0,0,0,0.1));
    }
    
    /* Progress bar enhancements */
    .stProgress > div > div > div {
        background: var(--primary, #2563eb);
        border-radius: var(--border-radius, 8px);
    }
    
    /* Spinner enhancements */
    .stSpinner > div {
        border-top-color: var(--primary, #2563eb);
    }
    
    /* Animation classes */
    .fade-in {
        animation: fadeIn 0.3s ease-out;
    }
    
    .slide-in-up {
        animation: slideInUp 0.3s ease-out;
    }
    
    .scale-in {
        animation: scaleIn 0.2s ease-out;
    }
    
    .bounce-in {
        animation: bounceIn 0.5s ease-out;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes slideInUp {
        from { 
            opacity: 0; 
            transform: translateY(20px); 
        }
        to { 
            opacity: 1; 
            transform: translateY(0); 
        }
    }
    
    @keyframes scaleIn {
        from { 
            opacity: 0; 
            transform: scale(0.9); 
        }
        to { 
            opacity: 1; 
            transform: scale(1); 
        }
    }
    
    @keyframes bounceIn {
        0% { 
            opacity: 0; 
            transform: scale(0.3); 
        }
        50% { 
            opacity: 1; 
            transform: scale(1.05); 
        }
        70% { 
            transform: scale(0.9); 
        }
        100% { 
            opacity: 1; 
            transform: scale(1); 
        }
    }
    
    /* Utility classes */
    .glass-effect {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .shadow-sm { box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
    .shadow { box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    .shadow-md { box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .shadow-lg { box-shadow: 0 10px 15px rgba(0,0,0,0.1); }
    .shadow-xl { box-shadow: 0 20px 25px rgba(0,0,0,0.1); }
    
    .rounded-sm { border-radius: 2px; }
    .rounded { border-radius: 4px; }
    .rounded-md { border-radius: 6px; }
    .rounded-lg { border-radius: 8px; }
    .rounded-xl { border-radius: 12px; }
    .rounded-2xl { border-radius: 16px; }
    .rounded-full { border-radius: 9999px; }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
        
        .stButton > button {
            width: 100%;
        }
        
        .stMetric {
            padding: 1rem;
        }
    }
    
    @media (max-width: 480px) {
        .main .block-container {
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }
    }
    </style>
    """
    
    st.markdown(foundation_css, unsafe_allow_html=True)


def inject_modern_css():
    """Enhanced modern styling with theme integration."""
    # Apply foundation CSS first
    inject_foundation_css()
    
    # Apply current theme
    theme_manager = get_theme_manager()
    current_theme = get_current_theme()
    theme_manager.apply_theme(current_theme)
    
    # Add component-specific styling
    component_css = """
    <style>
    /* Navigation enhancements */
    .nav-container {
        background: var(--surface, #ffffff);
        padding: 1rem 2rem;
        border-radius: 12px;
        box-shadow: var(--shadow, 0 1px 3px rgba(0,0,0,0.1));
        margin-bottom: 2rem;
        border: 1px solid var(--border, #e2e8f0);
        backdrop-filter: blur(10px);
    }
    
    .nav-pills {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
        justify-content: center;
        align-items: center;
    }
    
    .nav-pill {
        padding: 0.75rem 1.5rem;
        border-radius: var(--border-radius, 8px);
        border: 1px solid var(--border, #e2e8f0);
        background: var(--surface, #ffffff);
        color: var(--text, #1e293b);
        text-decoration: none;
        font-weight: 500;
        transition: all 0.2s ease;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.9rem;
        position: relative;
        overflow: hidden;
    }
    
    .nav-pill::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        transition: left 0.5s;
    }
    
    .nav-pill:hover::before {
        left: 100%;
    }
    
    .nav-pill:hover {
        background: var(--primary, #2563eb);
        color: white;
        border-color: var(--primary, #2563eb);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
    }
    
    .nav-pill.active {
        background: var(--primary, #2563eb);
        color: white;
        border-color: var(--primary, #2563eb);
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.3);
    }
    
    /* Header enhancements */
    .app-header {
        text-align: center;
        margin-bottom: 2rem;
        padding: 2rem 0;
        position: relative;
    }
    
    .app-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--text, #1e293b);
        margin: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1rem;
        background: linear-gradient(135deg, var(--primary, #2563eb), var(--accent, #10b981));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .app-subtitle {
        color: var(--secondary, #64748b);
        font-size: 1.1rem;
        margin-top: 0.5rem;
        font-weight: 400;
    }
    
    /* Status badge enhancements */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: rgba(16, 185, 129, 0.1);
        color: var(--success, #059669);
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
        margin-left: 1rem;
        border: 1px solid rgba(16, 185, 129, 0.2);
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
    }
    
    .status-indicator {
        width: 8px;
        height: 8px;
        background: var(--success, #10b981);
        border-radius: 50%;
        animation: blink 1.5s infinite;
    }
    
    @keyframes blink {
        0%, 50% { opacity: 1; }
        51%, 100% { opacity: 0.3; }
    }
    
    /* Content area enhancements */
    .content-area {
        background: var(--surface, #ffffff);
        border-radius: 12px;
        box-shadow: var(--shadow, 0 1px 3px rgba(0,0,0,0.1));
        border: 1px solid var(--border, #e2e8f0);
        min-height: 500px;
        position: relative;
        overflow: hidden;
    }
    
    .content-area::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--primary, #2563eb), transparent);
    }
    
    /* Card components */
    .card {
        background: var(--surface, #ffffff);
        border-radius: var(--border-radius, 8px);
        border: 1px solid var(--border, #e2e8f0);
        box-shadow: var(--shadow, 0 1px 3px rgba(0,0,0,0.1));
        transition: all 0.2s ease;
        overflow: hidden;
    }
    
    .card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    }
    
    .card-header {
        padding: 1.5rem 1.5rem 0;
        border-bottom: 1px solid var(--border, #e2e8f0);
    }
    
    .card-body {
        padding: 1.5rem;
    }
    
    .card-footer {
        padding: 0 1.5rem 1.5rem;
        border-top: 1px solid var(--border, #e2e8f0);
    }
    
    /* Theme selector enhancements */
    .theme-selector {
        position: fixed;
        top: 1rem;
        right: 1rem;
        z-index: 1000;
        background: var(--surface, #ffffff);
        border-radius: var(--border-radius, 8px);
        border: 1px solid var(--border, #e2e8f0);
        box-shadow: var(--shadow-lg, 0 10px 15px rgba(0,0,0,0.1));
        padding: 0.5rem;
    }
    
    .theme-toggle {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        border: none;
        background: var(--primary, #2563eb);
        color: white;
        cursor: pointer;
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
    }
    
    .theme-toggle:hover {
        transform: scale(1.1);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
    }
    
    /* Loading states */
    .loading-skeleton {
        background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
        background-size: 200% 100%;
        animation: loading 1.5s infinite;
    }
    
    @keyframes loading {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }
    
    /* Mobile responsive enhancements */
    @media (max-width: 768px) {
        .nav-pills {
            justify-content: flex-start;
            overflow-x: auto;
            padding-bottom: 0.5rem;
            scrollbar-width: none;
            -ms-overflow-style: none;
        }
        
        .nav-pills::-webkit-scrollbar {
            display: none;
        }
        
        .nav-pill {
            flex-shrink: 0;
            min-width: fit-content;
        }
        
        .app-title {
            font-size: 2rem;
            flex-direction: column;
            gap: 0.5rem;
        }
        
        .status-badge {
            margin-left: 0;
        }
        
        .theme-selector {
            position: relative;
            top: auto;
            right: auto;
            margin-bottom: 1rem;
        }
    }
    
    @media (max-width: 480px) {
        .nav-container {
            padding: 1rem;
        }
        
        .app-title {
            font-size: 1.75rem;
        }
        
        .card-body {
            padding: 1rem;
        }
    }
    </style>
    """
    
    st.markdown(component_css, unsafe_allow_html=True)


def render_header():
    """Enhanced header with theme integration and animations."""
    theme_manager = get_theme_manager()
    current_theme_name = get_current_theme()
    current_theme = theme_manager.get_theme_config(current_theme_name)
    
    # Determine status based on theme and system state
    status_color = current_theme.success_color if current_theme else "#10b981"
    
    header_html = f"""
    <div class="app-header fade-in">
        <h1 class="app-title">
            🤖 AI Karen
            <span class="status-badge">
                <span class="status-indicator"></span>
                Online
            </span>
        </h1>
        <p class="app-subtitle">Your intelligent AI assistant powered by advanced AI</p>
    </div>
    """
    
    st.markdown(header_html, unsafe_allow_html=True)


def render_theme_selector():
    """Render a floating theme selector."""
    theme_manager = get_theme_manager()
    
    with st.sidebar:
        st.markdown("---")
        selected_theme = theme_manager.create_theme_selector()
        
        if selected_theme != get_current_theme():
            theme_manager.apply_theme(selected_theme)
            st.rerun()


def create_card(title: str, content: str, footer: str = None, animation: str = "fade-in") -> None:
    """Create a styled card component."""
    footer_html = f'<div class="card-footer">{footer}</div>' if footer else ''
    
    card_html = f"""
    <div class="card {animation}">
        <div class="card-header">
            <h3>{title}</h3>
        </div>
        <div class="card-body">
            {content}
        </div>
        {footer_html}
    </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)


def create_metric_card(label: str, value: str, delta: str = None, icon: str = None) -> None:
    """Create an enhanced metric card."""
    icon_html = f'<span style="font-size: 1.5rem; margin-right: 0.5rem;">{icon}</span>' if icon else ''
    delta_html = f'<div style="color: var(--success); font-size: 0.9rem; margin-top: 0.25rem;">{delta}</div>' if delta else ''
    
    metric_html = f"""
    <div class="card scale-in" style="text-align: center;">
        <div class="card-body">
            {icon_html}
            <div style="font-size: 0.9rem; color: var(--secondary); margin-bottom: 0.5rem;">{label}</div>
            <div style="font-size: 2rem; font-weight: 700; color: var(--text);">{value}</div>
            {delta_html}
        </div>
    </div>
    """
    
    st.markdown(metric_html, unsafe_allow_html=True)


def show_loading_skeleton(height: str = "100px", count: int = 1):
    """Show loading skeleton animation."""
    for i in range(count):
        skeleton_html = f"""
        <div class="loading-skeleton" style="height: {height}; border-radius: var(--border-radius); margin-bottom: 1rem;"></div>
        """
        st.markdown(skeleton_html, unsafe_allow_html=True)


def apply_animation(element_class: str, animation: str = "fade-in"):
    """Apply animation to elements."""
    animation_css = f"""
    <style>
    .{element_class} {{
        animation: {animation} 0.3s ease-out;
    }}
    </style>
    """
    st.markdown(animation_css, unsafe_allow_html=True)