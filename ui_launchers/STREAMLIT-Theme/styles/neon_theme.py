"""
Neon Theme Styles for Kari AI Streamlit Console
"""

def load_neon_theme():
    """Load and apply the neon theme CSS"""
    neon_css = """
    <style>
    :root {
        --primary-neon: #00FFFF;
        --secondary-neon: #FF00FF;
        --background-dark: #0F0F1B;
        --background-panel: #1A1A2E;
        --background-sidebar: #16161A;
        --text-primary: #FFFFFF;
        --text-secondary: #00FFFF;
        --text-accent: #FF00FF;
        --border-color: rgba(0, 255, 255, 0.3);
    }
    
    body {
        background-color: var(--background-dark);
        color: var(--text-primary);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    .stApp {
        background-color: var(--background-dark);
    }
    
    /* Main container styling */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        background-color: var(--background-dark);
    }
    
    /* Right sidebar styling (Streamlit default) */
    .css-1d391kg {
        background-color: var(--background-panel);
        border-right: 1px solid var(--border-color);
    }
    
    /* Left sidebar styling */
    .left-sidebar {
        background-color: var(--background-sidebar);
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border: 1px solid var(--border-color);
    }
    
    /* Left sidebar button styling */
    .left-sidebar button {
        width: 100%;
        text-align: left;
        background-color: transparent;
        color: var(--text-primary);
        border: 1px solid var(--border-color);
        border-radius: 4px;
        padding: 0.5rem;
        margin-bottom: 0.5rem;
        transition: all 0.3s ease;
    }
    
    .left-sidebar button:hover {
        background-color: rgba(0, 255, 255, 0.2);
        border-color: var(--primary-neon);
        color: var(--primary-neon);
        box-shadow: 0 0 8px rgba(0, 255, 255, 0.4);
    }
    
    /* Left sidebar heading styling */
    .left-sidebar h3 {
        color: var(--text-secondary);
        font-size: 1rem;
        margin-bottom: 0.5rem;
        margin-top: 1rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .left-sidebar h4 {
        color: var(--text-accent);
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
        margin-top: 1rem;
    }
    
    /* Left sidebar selectbox styling */
    .left-sidebar div[data-baseweb="select"] > div {
        background-color: rgba(26, 26, 46, 0.8);
        border: 1px solid var(--border-color);
        border-radius: 4px;
        margin-bottom: 0.5rem;
        color: var(--text-primary);
    }
    
    /* Left sidebar checkbox styling */
    .left-sidebar .stCheckbox {
        margin-bottom: 0.3rem;
        color: var(--text-primary);
    }
    
    .left-sidebar .stCheckbox label {
        color: var(--text-primary);
    }
    
    /* Button styling with neon effect */
    div.stButton > button:first-child {
        background-color: transparent;
        color: var(--text-primary);
        border: 1px solid var(--primary-neon);
        border-radius: 4px;
        box-shadow: 0 0 5px rgba(0, 255, 255, 0.5);
        transition: all 0.3s ease;
        font-weight: 500;
    }
    
    div.stButton > button:first-child:hover {
        background-color: rgba(0, 255, 255, 0.2);
        border-color: var(--primary-neon);
        color: var(--primary-neon);
        box-shadow: 0 0 10px rgba(0, 255, 255, 0.8);
    }
    
    /* Input field styling */
    div[data-baseweb="input"] {
        background-color: rgba(26, 26, 46, 0.8);
        border: 1px solid var(--border-color);
        border-radius: 4px;
    }
    
    div[data-baseweb="input"] input {
        color: var(--text-primary);
        font-weight: 400;
    }
    
    div[data-baseweb="textarea"] textarea {
        color: var(--text-primary);
        font-weight: 400;
    }
    
    /* Enhanced chat message styling */
    .enhanced-chat-container {
        display: flex;
        flex-direction: column;
        gap: 1rem;
        padding: 1rem;
        max-height: calc(100vh - 200px);
        overflow-y: auto;
    }
    
    .enhanced-message {
        display: flex;
        margin-bottom: 1.5rem;
        animation: fadeIn 0.3s ease-in-out;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .message-avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 1rem;
        flex-shrink: 0;
        font-weight: bold;
        font-size: 1.2rem;
    }
    
    .user-avatar {
        background: linear-gradient(135deg, var(--primary-neon), rgba(0, 255, 255, 0.2));
        box-shadow: 0 0 10px rgba(0, 255, 255, 0.3);
    }
    
    .assistant-avatar {
        background: linear-gradient(135deg, var(--secondary-neon), rgba(255, 0, 255, 0.2));
        box-shadow: 0 0 10px rgba(255, 0, 255, 0.3);
    }
    
    .message-content {
        flex: 1;
        min-width: 0;
    }
    
    .message-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
    }
    
    .message-info {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .message-author {
        font-weight: 600;
        font-size: 0.9rem;
    }
    
    .message-timestamp {
        font-size: 0.8rem;
        color: var(--text-secondary);
        opacity: 0.8;
    }
    
    .message-body {
        background-color: rgba(26, 26, 46, 0.6);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.5rem;
        border-left: 3px solid transparent;
        position: relative;
        overflow: hidden;
    }
    
    .user-message .message-body {
        border-left-color: var(--primary-neon);
        background-color: rgba(0, 255, 255, 0.1);
    }
    
    .assistant-message .message-body {
        border-left-color: var(--secondary-neon);
        background-color: rgba(255, 0, 255, 0.1);
    }
    
    .message-body::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, var(--border-color), transparent);
        opacity: 0.5;
    }
    
    .message-actions {
        display: flex;
        gap: 0.5rem;
        margin-top: 0.5rem;
        opacity: 0;
        transition: opacity 0.2s ease;
    }
    
    .enhanced-message:hover .message-actions {
        opacity: 1;
    }
    
    .message-action-button {
        background: transparent;
        border: 1px solid var(--border-color);
        border-radius: 4px;
        color: var(--text-secondary);
        padding: 0.25rem 0.5rem;
        font-size: 0.8rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .message-action-button:hover {
        background-color: rgba(0, 255, 255, 0.1);
        border-color: var(--primary-neon);
        color: var(--primary-neon);
    }
    
    .message-metadata {
        margin-top: 0.5rem;
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
    }
    
    .metadata-badge {
        background-color: rgba(26, 26, 46, 0.8);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 0.25rem 0.75rem;
        font-size: 0.75rem;
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        white-space: nowrap;
    }
    
    .metadata-badge.model {
        background-color: rgba(0, 255, 255, 0.1);
        border-color: var(--primary-neon);
        color: var(--primary-neon);
    }
    
    .metadata-badge.plugin {
        background-color: rgba(255, 0, 255, 0.1);
        border-color: var(--secondary-neon);
        color: var(--secondary-neon);
    }
    
    .metadata-badge.time {
        background-color: rgba(255, 255, 0, 0.1);
        border-color: #FFFF00;
        color: #FFFF00;
    }
    
    .streaming-message {
        position: relative;
    }
    
    .streaming-cursor {
        display: inline-block;
        width: 8px;
        height: 1.2em;
        background-color: var(--primary-neon);
        animation: blink 1s infinite;
        margin-left: 2px;
        vertical-align: text-bottom;
    }
    
    @keyframes blink {
        0%, 50% { opacity: 1; }
        51%, 100% { opacity: 0; }
    }
    
    .streaming-controls {
        display: flex;
        gap: 0.5rem;
        margin-top: 0.5rem;
        opacity: 0;
        transition: opacity 0.2s ease;
    }
    
    .streaming-message:hover .streaming-controls {
        opacity: 1;
    }
    
    .streaming-control-button {
        background: transparent;
        border: 1px solid var(--border-color);
        border-radius: 4px;
        color: var(--text-secondary);
        padding: 0.25rem 0.5rem;
        font-size: 0.8rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .streaming-control-button:hover {
        background-color: rgba(0, 255, 255, 0.1);
        border-color: var(--primary-neon);
        color: var(--primary-neon);
    }
    
    .enhanced-input-area {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        padding: 1rem;
        background-color: rgba(26, 26, 46, 0.4);
        border-radius: 8px;
        border: 1px solid var(--border-color);
    }
    
    .input-toolbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid var(--border-color);
    }
    
    .input-formatting {
        display: flex;
        gap: 0.5rem;
    }
    
    .formatting-button {
        background: transparent;
        border: none;
        color: var(--text-secondary);
        padding: 0.25rem;
        cursor: pointer;
        border-radius: 4px;
        transition: all 0.2s ease;
    }
    
    .formatting-button:hover {
        background-color: rgba(0, 255, 255, 0.1);
        color: var(--primary-neon);
    }
    
    .input-options {
        display: flex;
        gap: 0.5rem;
        align-items: center;
    }
    
    .input-textarea {
        background-color: rgba(15, 15, 27, 0.8);
        border: 1px solid var(--border-color);
        border-radius: 4px;
        color: var(--text-primary);
        padding: 0.75rem;
        resize: vertical;
        min-height: 100px;
        max-height: 300px;
        font-family: inherit;
        font-size: 0.95rem;
        transition: border-color 0.2s ease;
    }
    
    .input-textarea:focus {
        outline: none;
        border-color: var(--primary-neon);
        box-shadow: 0 0 0 2px rgba(0, 255, 255, 0.2);
    }
    
    .input-actions {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-top: 0.5rem;
    }
    
    .input-actions-left {
        display: flex;
        gap: 0.5rem;
    }
    
    .input-actions-right {
        display: flex;
        gap: 0.5rem;
    }
    
    .input-hint {
        font-size: 0.8rem;
        color: var(--text-secondary);
        opacity: 0.8;
    }
    
    .message-status {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        font-size: 0.75rem;
        color: var(--text-secondary);
        margin-left: 0.5rem;
    }
    
    .status-indicator-small {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        display: inline-block;
    }
    
    .status-success {
        background-color: #00FF00;
        box-shadow: 0 0 4px rgba(0, 255, 0, 0.6);
    }
    
    .status-error {
        background-color: #FF0000;
        box-shadow: 0 0 4px rgba(255, 0, 0, 0.6);
    }
    
    .status-pending {
        background-color: #FFFF00;
        box-shadow: 0 0 4px rgba(255, 255, 0, 0.6);
        animation: pulse 1.5s infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.2); opacity: 0.7; }
        100% { transform: scale(1); opacity: 1; }
    }
    
    /* Status indicators */
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 5px;
    }
    
    .status-online {
        background-color: #00FF00;
        box-shadow: 0 0 5px rgba(0, 255, 0, 0.8);
    }
    
    .status-offline {
        background-color: #FF0000;
        box-shadow: 0 0 5px rgba(255, 0, 0, 0.8);
    }
    
    .status-warning {
        background-color: #FFFF00;
        box-shadow: 0 0 5px rgba(255, 255, 0, 0.8);
    }
    
    /* Plugin toggle styling */
    .plugin-toggle {
        display: flex;
        align-items: center;
        margin-bottom: 0.5rem;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: var(--background-panel);
        border-radius: 8px 8px 0 0;
        padding: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: var(--text-secondary);
        font-weight: 500;
        padding: 0.5rem 1rem;
    }
    
    .stTabs [data-baseweb="tab-active"] {
        color: var(--primary-neon);
        border-bottom: 2px solid var(--primary-neon);
    }
    
    /* Selectbox styling */
    div[data-baseweb="select"] > div {
        background-color: rgba(26, 26, 46, 0.8);
        border: 1px solid var(--border-color);
        color: var(--text-primary);
    }
    
    /* Metrics styling */
    .metric-container {
        background-color: rgba(26, 26, 46, 0.8);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .metric-value {
        font-size: 1.5rem;
        font-weight: bold;
        color: var(--primary-neon);
        text-shadow: 0 0 5px rgba(0, 255, 255, 0.5);
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Form styling */
    .stForm {
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1rem;
        background-color: rgba(26, 26, 46, 0.3);
    }
    
    /* Caption styling */
    .stCaption {
        color: var(--text-secondary);
        font-size: 0.8rem;
    }
    
    /* Header styling */
    h1, h2, h3 {
        color: var(--text-primary);
        font-weight: 600;
    }
    
    h4, h5, h6 {
        color: var(--text-secondary);
        font-weight: 500;
    }
    </style>
    """
    return neon_css