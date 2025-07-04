"""
Kari UI Page Loader
- Hot-swappable, dynamic, plug-and-play
- All page modules imported and registered for central routing
"""

from .admin import *
from .analytics import *
from .chat import *
from .home import *
from .iot import *
from .memory import *
from .plugins import *
from .settings import *

# Registry for dynamic UI routers
PAGES = {
    "admin": "Admin Dashboard",
    "analytics": "Analytics & Data",
    "chat": "Conversational Intelligence",
    "home": "Home",
    "iot": "IoT & Devices",
    "memory": "Memory & Knowledge",
    "plugins": "Plugins & Workflows",
    "settings": "Settings & Privacy",
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
