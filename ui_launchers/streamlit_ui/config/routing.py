"""
Streamlit UI Routing Table (no business logic)
Maps display names to page launchers.
"""
from ui_logic.pages.home import home_page
from ui_logic.pages.chat import chat_page
from ui_logic.pages.analytics import analytics_page
from ui_logic.pages.plugins import plugins_page
from ui_logic.pages.iot import iot_page
from ui_logic.pages.memory import memory_page
from ui_logic.pages.admin import admin_page
from ui_logic.pages.settings import settings_page

PAGE_MAP = {
    "Home": home_page,
    "Chat": chat_page,
    "Analytics": analytics_page,
    "Plugins": plugins_page,
    "IoT": iot_page,
    "Memory": memory_page,
    "Admin": admin_page,
    "Settings": settings_page,
}

DEFAULT_PAGE = "Home"
