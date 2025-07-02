#!/usr/bin/env python3
"""
Kari AI Mobile UI - Production Grade

Features:
- Atomic startup sequence
- Health checks with circuit breakers
- Async-safe logging
- Resource monitoring
- Graceful degradation
"""

import sys
import logging
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, NoReturn
import signal
import psutil
import platform
import time

# === Atomic Initialization === #
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# === Logging Setup === #
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"app_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('kari.prod')


class SignalHandler:
    """Handle graceful shutdown signals."""

    def __init__(self):
        self.should_exit = False
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum, frame):
        logger.warning(f"Received shutdown signal {signum}")
        self.should_exit = True


class HealthMonitor:
    """Simple system health checks with circuit breaker."""

    def __init__(self):
        self.start_time = datetime.now()
        self.circuit_breaker = False

    def system_check(self) -> bool:
        try:
            mem = psutil.virtual_memory()
            if mem.available < 100 * 1024 * 1024:
                logger.error("Insufficient memory available")
                return False

            load = psutil.getloadavg()[0] / psutil.cpu_count()
            if load > 3.0:
                logger.error(f"High system load: {load:.2f}")
                return False
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def uptime(self) -> str:
        return str(datetime.now() - self.start_time).split('.')[0]


class KariApp:
    """Core application controller."""

    def __init__(self):
        self.signal_handler = SignalHandler()
        self.health = HealthMonitor()
        self._load_config()
        self._init_session()
        self._verify_environment()

    def _load_config(self) -> None:
        try:
            from utils.config import ConfigManager
            self.config = ConfigManager()
        except Exception as e:
            logger.critical(f"Config load failed: {e}")
            raise RuntimeError("Configuration unavailable")

    def _init_session(self) -> None:
        import streamlit as st
        self.st = st
        if not hasattr(st.session_state, 'init_time'):
            st.session_state.init_time = datetime.now()
            st.session_state.health_checks = 0

    def _verify_environment(self) -> None:
        self._check_dependencies()
        self._verify_directories()
        self._verify_ports()

    def _check_dependencies(self) -> None:
        deps: Dict[str, tuple[str, Optional[str]]] = {
            'streamlit': ('1.28.0', None),
            'numpy': ('1.21.0', None),
            'transformers': ('4.30.0', None)
        }
        missing = []
        for pkg, (min_ver, max_ver) in deps.items():
            try:
                mod = __import__(pkg)
                if min_ver and mod.__version__ < min_ver:
                    raise ImportError(f"Version {mod.__version__} < {min_ver}")
                if max_ver and mod.__version__ > max_ver:
                    raise ImportError(f"Version {mod.__version__} > {max_ver}")
            except ImportError as e:
                missing.append(f"{pkg} ({str(e)})")
        if missing:
            logger.critical(f"Missing dependencies: {', '.join(missing)}")
            raise RuntimeError("Dependency check failed")

    def _verify_directories(self) -> None:
        required_dirs = [
            ROOT / "styles",
            ROOT / "models",
            ROOT / "cache",
            ROOT / "logs"
        ]
        for dir_path in required_dirs:
            try:
                dir_path.mkdir(exist_ok=True, mode=0o755)
            except Exception as e:
                logger.error(f"Directory check failed: {dir_path} - {e}")
                raise RuntimeError("Filesystem verification failed")

    def _verify_ports(self) -> None:
        required_ports = {8501: 'Streamlit', 8000: 'API'}
        for port, service in required_ports.items():
            if self._is_port_in_use(port):
                logger.warning(f"Port {port} ({service}) already in use")

    def _is_port_in_use(self, port: int) -> bool:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0

    def _load_styles(self) -> None:
        css_paths = [
            ROOT / "styles" / "styles.css",
            Path(__file__).parent / "default_styles.css"
        ]
        for css_path in css_paths:
            try:
                if css_path.exists():
                    with open(css_path, "r") as f:
                        self.st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
                        logger.info(f"Loaded CSS from {css_path}")
                        return
            except Exception as e:
                logger.warning(f"CSS load attempt failed: {css_path} - {e}")
        self.st.markdown(
            """
        <style>
            .stButton>button {
                border-radius: 8px !important;
                transition: all 0.3s ease !important;
            }
            .stButton>button:hover {
                transform: scale(1.02) !important;
            }
        </style>
        """,
            unsafe_allow_html=True,
        )

    def _render_system_status(self) -> None:
        with self.st.sidebar.expander("System Status", expanded=False):
            cols = self.st.columns(2)
            with cols[0]:
                self.st.metric("CPU", f"{psutil.cpu_percent()}%")
                mem = psutil.virtual_memory()
                self.st.metric("Memory", f"{mem.percent}%")
            with cols[1]:
                disk = psutil.disk_usage('/')
                self.st.metric("Disk", f"{disk.percent}%")
                net = psutil.net_io_counters()
                self.st.metric("Network", f"▲{net.bytes_sent/1e6:.1f}MB ▼{net.bytes_recv/1e6:.1f}MB")
            self.st.caption(f"Uptime: {self.health.uptime()}")

    def _safe_render(self, component: callable) -> None:
        try:
            component()
        except Exception as e:
            logger.error(f"Component failed: {component.__name__} - {e}")
            self.st.error(f"Component error: {component.__name__}")
            self.st.code(traceback.format_exc())

    def run(self) -> NoReturn:
        self.st.set_page_config(
            layout="wide",
            page_title=f"{self.config.app_name} | v{self.config.version}",
            page_icon=self.config.app_icon,
            initial_sidebar_state="expanded",
        )

        self._load_styles()

        while not self.signal_handler.should_exit:
            try:
                if not self.health.system_check():
                    if self.health.circuit_breaker:
                        raise RuntimeError("Critical health check failure")
                    self.health.circuit_breaker = True
                    self.st.error("System health degraded")
                    logger.error("Entered degraded state")

                selection = render_sidebar()
                self.dispatch_selection(selection)
                self._render_system_status()
                time.sleep(0.1)
            except Exception as e:
                logger.critical(f"Runtime failure: {e}")
                self.st.error("Application error occurred")
                if not self._handle_failure(e):
                    break
        logger.info("Application shutdown complete")

    def _handle_failure(self, error: Exception) -> bool:
        if isinstance(error, (MemoryError, KeyboardInterrupt)):
            return False
        return True

    def dispatch_selection(self, selection: str) -> None:
        view_map = {
            "Chat": lambda: self._safe_render(render_chat),
            "Settings": lambda: self._safe_render(render_settings),
            "Models": lambda: self._safe_render(render_models),
            "Memory": lambda: self._safe_render(render_memory),
            "Diagnostics": lambda: self._safe_render(EnterpriseDiagnostics().render),
        }
        if selection in view_map:
            view_map[selection]()
        else:
            self.st.warning(f"Unknown view: {selection}")
            logger.warning(f"Invalid selection: {selection}")


if __name__ == "__main__":
    logger.info(f"Starting Kari AI on {platform.node()}")
    logger.info(f"Python {sys.version}")
    logger.info(f"Root directory: {ROOT}")
    try:
        from components.sidebar import render_sidebar
        from components.chat import render_chat
        from components.settings import render_settings
        from components.memory import render_memory
        from components.models import render_models
        from mobile_ui.pages.diagnostics import EnterpriseDiagnostics

        app = KariApp()
        app.run()
    except Exception as e:
        logger.critical(f"Bootstrap failed: {e}")
        sys.exit(1)
