"""
Streamlit UI Routing Table (no business logic)
Maps display names to page launchers.
"""
from pages.home import home_page
from pages.chat import chat_page
from pages.analytics import analytics_page
from pages.plugins import plugins_page
from pages.iot import iot_page
from pages.memory import memory_page
from pages.admin import admin_page
from pages.settings import settings_page

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
