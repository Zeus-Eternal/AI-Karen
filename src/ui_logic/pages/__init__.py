"""
Kari UI Page Loader
- Hot-swappable, dynamic, plug-and-play
- All page modules imported and registered for central routing
"""

from .admin import *
from .analytics import *
from .automation import *
from .autonomous import *
from .calendar import *
from .chat import *
from .code_lab import *
from .context import *
from .diagnostics import *
from .echo_core import *
from .files import *
from .home import *
from .integrations import *
from .iot import *
from .labs import *
from .memory import *
from .personas import *
from .plugins import *
from .presence import *
from .security import *
from .settings import *
from .task_manager import *
from .vision import *
from .voice import *
from .white_label import *
from .workflows import *

# Registry for dynamic UI routers
PAGES = {
    "admin": "Admin Dashboard",
    "analytics": "Analytics & Data",
    "automation": "Automation",
    "autonomous": "Autonomous Ops",
    "calendar": "Calendar",
    "chat": "Conversational Intelligence",
    "code_lab": "Code Lab",
    "context": "Context Explorer",
    "diagnostics": "Diagnostics",
    "echo_core": "Echo Core",
    "files": "File Manager",
    "home": "Home",
    "integrations": "Integrations",
    "iot": "IoT & Devices",
    "labs": "Labs",
    "memory": "Memory & Knowledge",
    "personas": "Personas",
    "plugins": "Plugins & Workflows",
    "presence": "Presence",
    "security": "Security",
    "settings": "Settings & Privacy",
    "task_manager": "Task Manager",
    "vision": "Vision",
    "voice": "Voice",
    "white_label": "White Label",
    "workflows": "Workflows",
}


def list_pages():
    """List all available top-level UI pages for navigation."""
    return list(PAGES.keys())


def get_page_label(page: str) -> str:
    """Get the pretty label for any page route."""
    return PAGES.get(page, page.title())

__all__ = [
    "PAGES",
    "list_pages",
    "get_page_label",
]
