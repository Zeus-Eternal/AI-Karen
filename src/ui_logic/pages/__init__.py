"""
Kari UI Page Loader
- Hot-swappable, dynamic, plug-and-play
- All page modules imported and registered for central routing
"""

from ui_logic.pages.admin import admin_page
from ui_logic.pages.analytics import analytics_page
from ui_logic.pages.chat import chat_logic, get_chat_page
from ui_logic.pages.home import home_page
from ui_logic.pages.iot import iot_page
from ui_logic.pages.memory import memory_page
from ui_logic.pages.plugins import plugins_page
from ui_logic.pages.settings import settings_page

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
    "admin_page",
    "analytics_page",
    "chat_logic",
    "get_chat_page",
    "home_page",
    "iot_page",
    "memory_page",
    "plugins_page",
    "settings_page",
    "PAGES",
    "list_pages",
    "get_page_label",
]
