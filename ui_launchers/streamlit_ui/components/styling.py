"""
Styling and CSS components for the Streamlit UI
"""

import streamlit as st


def inject_modern_css():
    """Modern, clean styling"""
    st.markdown("""
    <style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Modern color scheme */
    :root {
        --primary: #2563eb;
        --primary-light: #3b82f6;
        --secondary: #64748b;
        --accent: #10b981;
        --background: #f8fafc;
        --surface: #ffffff;
        --text: #1e293b;
        --text-light: #64748b;
        --border: #e2e8f0;
        --shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        max-width: 1200px;
    }
    
    /* Navigation pills */
    .nav-container {
        background: white;
        padding: 1rem 2rem;
        border-radius: 12px;
        box-shadow: var(--shadow);
        margin-bottom: 2rem;
        border: 1px solid var(--border);
    }
    
    .nav-pills {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
        justify-content: center;
    }
    
    .nav-pill {
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        border: 1px solid var(--border);
        background: white;
        color: var(--text);
        text-decoration: none;
        font-weight: 500;
        transition: all 0.2s ease;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.9rem;
    }
    
    .nav-pill:hover {
        background: var(--primary);
        color: white;
        border-color: var(--primary);
        transform: translateY(-1px);
        box-shadow: var(--shadow);
    }
    
    .nav-pill.active {
        background: var(--primary);
        color: white;
        border-color: var(--primary);
        box-shadow: var(--shadow);
    }
    
    /* Header */
    .app-header {
        text-align: center;
        margin-bottom: 2rem;
        padding: 2rem 0;
    }
    
    .app-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--text);
        margin: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1rem;
    }
    
    .app-subtitle {
        color: var(--text-light);
        font-size: 1.1rem;
        margin-top: 0.5rem;
    }
    
    /* Status indicator */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: rgba(16, 185, 129, 0.1);
        color: #059669;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
        margin-left: 1rem;
    }
    
    /* Content area */
    .content-area {
        background: white;
        border-radius: 12px;
        box-shadow: var(--shadow);
        border: 1px solid var(--border);
        min-height: 500px;
    }
    
    /* Buttons */
    .stButton > button {
        background: var(--primary);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        background: var(--primary-light);
        transform: translateY(-1px);
        box-shadow: var(--shadow);
    }
    
    /* Metrics */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid var(--border);
        box-shadow: var(--shadow);
    }
    
    /* Animations */
    .fade-in {
        animation: fadeIn 0.3s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Mobile responsive */
    @media (max-width: 768px) {
        .nav-pills {
            justify-content: flex-start;
            overflow-x: auto;
            padding-bottom: 0.5rem;
        }
        
        .nav-pill {
            flex-shrink: 0;
        }
        
        .app-title {
            font-size: 2rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)


def render_header():
    """Clean, modern header"""
    st.markdown("""
    <div class="app-header">
        <h1 class="app-title">
            🤖 AI Karen
            <span class="status-badge">● Online</span>
        </h1>
        <p class="app-subtitle">Your intelligent AI assistant</p>
    </div>
    """, unsafe_allow_html=True)