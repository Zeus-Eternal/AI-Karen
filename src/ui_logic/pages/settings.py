"""
Kari Settings Page
- Orchestrates: settings panel, privacy console, API vault, theme switcher
"""

from ui_logic.components.settings.api_vault import render_api_vault
from ui_logic.components.settings.privacy_console import render_privacy_console
from ui_logic.components.settings.settings_panel import render_settings_panel
from ui_logic.components.settings.theme_switcher import render_theme_switcher


def settings_page(user_ctx=None):
    render_settings_panel(user_ctx=user_ctx)
    render_theme_switcher(user_ctx=user_ctx)
    render_api_vault(user_ctx=user_ctx)
    render_privacy_console(user_ctx=user_ctx)
