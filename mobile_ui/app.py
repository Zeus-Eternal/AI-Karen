#!/usr/bin/env python3
"""
Kari AI Mobile UI - Enterprise Edition

Core application entry point with enhanced:
- Error handling
- Dependency management
- System monitoring
- Configuration management
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

# 🚀 Initialization before imports to ensure path correctness
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Configure logging before other imports
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(ROOT / 'logs' / 'app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

try:
    # 🧠 Core UI framework
    import streamlit as st
    
    # 🧩 Modular UI panels
    from components.sidebar import render_sidebar
    from components.chat import render_chat
    from components.settings import render_settings
    from components.memory import render_memory
    from components.models import render_models
    from components.diagnostics import EnterpriseDiagnostics
    from utils.model_loader import ensure_spacy_models, ensure_sklearn_installed
    from utils.config import ConfigManager
except ImportError as e:
    logger.critical(f"Import failed: {e}")
    sys.exit(1)

class KariApp:
    def __init__(self):
        self.config = ConfigManager()
        self.start_time = None
        self.session_state = st.session_state
        
        # Initialize session variables
        if 'initialized' not in self.session_state:
            self.session_state.initialized = False
            self.session_state.dependencies_checked = False

    def load_styles(self) -> None:
        """Inject custom CSS with versioning and fallback."""
        css_path = ROOT / "styles" / "styles.css"
        fallback_css = """
        .stButton>button {
            border-radius: 8px;
            border: 1px solid #4CAF50;
        }
        """
        
        try:
            if css_path.exists():
                with open(css_path, "r") as f:
                    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
                    logger.info("Custom CSS loaded successfully")
            else:
                st.markdown(f"<style>{fallback_css}</style>", unsafe_allow_html=True)
                logger.warning("Using fallback CSS - styles.css not found")
        except Exception as e:
            logger.error(f"CSS loading failed: {e}")
            st.markdown(f"<style>{fallback_css}</style>", unsafe_allow_html=True)

    def ensure_dependencies(self) -> bool:
        """Ensure all required dependencies are available."""
        if self.session_state.dependencies_checked:
            return True
            
        try:
            with st.spinner("🔍 Checking system dependencies..."):
                ensure_spacy_models()
                ensure_sklearn_installed()
                
                # Additional enterprise dependencies
                self._check_enterprise_deps()
                
            self.session_state.dependencies_checked = True
            return True
        except Exception as e:
            st.error(f"🚨 Dependency check failed: {e}")
            logger.critical(f"Dependency verification failed: {e}")
            return False

    def _check_enterprise_deps(self) -> None:
        """Check for enterprise-specific dependencies."""
        try:
            import GPUtil  # For GPU monitoring
            import psutil  # For system metrics
        except ImportError as e:
            logger.warning(f"Enterprise dependency missing: {e}")
            raise

    def dispatch_selection(self, selection: str) -> None:
        """Route sidebar selection to appropriate view with error handling."""
        view_mapping = {
            "Chat": render_chat,
            "Settings": render_settings,
            "Models": render_models,
            "Memory": render_memory,
            "Diagnostics": lambda: EnterpriseDiagnostics().render()
        }
        
        try:
            if selection in view_mapping:
                with st.container():
                    view_mapping[selection]()
            else:
                st.error(f"Unknown section: {selection}")
                logger.warning(f"Unknown view requested: {selection}")
        except Exception as e:
            st.error(f"🔥 View rendering failed: {str(e)}")
            logger.exception(f"Failed to render {selection} view")

    def render_footer(self) -> None:
        """Render system footer with diagnostics."""
        st.sidebar.divider()
        st.sidebar.caption(f"🧠 Root Path: `{ROOT}`")
        
        if self.start_time:
            uptime = str(datetime.now() - self.start_time).split('.')[0]
            st.sidebar.caption(f"⏱️ Uptime: {uptime}")
        
        st.sidebar.caption(f"⚙️ Config: {self.config.env_name}")
        st.sidebar.caption(f"🐍 Python: {sys.version.split()[0]}")

    def run(self) -> None:
        """Main application lifecycle."""
        self.start_time = datetime.now()
        
        st.set_page_config(
            layout="wide",
            page_title=f"{self.config.app_name} – Mobile UI",
            page_icon=self.config.app_icon,
            initial_sidebar_state="expanded",
        )
        
        # System initialization sequence
        if not self.session_state.initialized:
            if not self.ensure_dependencies():
                return
            self.session_state.initialized = True
            logger.info("Application initialized successfully")
        
        self.load_styles()
        
        try:
            selection = render_sidebar()
            self.dispatch_selection(selection)
            self.render_footer()
        except KeyboardInterrupt:
            logger.info("Application shutdown requested")
        except Exception as e:
            logger.critical(f"Application crash: {e}")
            st.error("💥 Critical application error - check logs")
            st.exception(e)

if __name__ == "__main__":
    logger.info(f"🚀 Starting application from {ROOT}")
    logger.info(f"Python path: {sys.path[:3]}")
    
    try:
        app = KariApp()
        app.run()
    except Exception as e:
        logger.critical(f"Application bootstrap failed: {e}")
        sys.exit(1)
