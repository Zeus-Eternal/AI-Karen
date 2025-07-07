"""Kari Pages Manifest -- Ultra-Sovereign Navigation Control

Defines all built-in UI pages along with RBAC roles and feature flag gating.
Each page entry uses the following keys:
    - ``route``: page identifier and import name under ``ui_logic.pages``
    - ``label``: human readable name for navigation
    - ``icon``: short emoji label used in menus
    - ``import``: dotted module path for dynamic loading
    - ``feature_flag``: key from :mod:`ui_logic.config.feature_flags` controlling visibility
    - ``roles``: list of roles allowed to access the page
    - ``enabled``: boolean derived from ``feature_flag`` at load time

Plugins may append additional entries at runtime via :func:`register_plugin_page`.
"""

import os
from src.ui_logic.config.feature_flags import get_flag


def _flag_enabled(flag: str | None) -> bool:
    """Return ``True`` if ``flag`` is enabled or not specified."""
    if not flag:
        return True
    return bool(get_flag(flag))


# --- Core pages manifest ----------------------------------------------------
PAGES = [
    # Public/Home
    {
        "route": "home",
        "label": "Home",
        "icon": "🏠",
        "import": "src.ui_logic.pages.home",
        "feature_flag": None,
        "roles": [],
        "enabled": _flag_enabled(None),
    },
    {
        "route": "onboarding",
        "label": "Onboarding",
        "icon": "🧭",
        "import": "src.ui_logic.pages.onboarding",
        "feature_flag": "enable_onboarding_wizard",
        "roles": [],
        "enabled": _flag_enabled("enable_onboarding_wizard"),
    },
    # Chat/Core Interaction
    {
        "route": "chat",
        "label": "Chat",
        "icon": "💬",
        "import": "src.ui_logic.pages.chat",
        "feature_flag": None,
        "roles": ["user", "admin"],
        "enabled": _flag_enabled(None),
    },
    # Memory/Knowledge
    {
        "route": "memory",
        "label": "Memory",
        "icon": "🧠",
        "import": "src.ui_logic.pages.memory",
        "feature_flag": "enable_memory_explorer",
        "roles": ["user", "admin"],
        "enabled": _flag_enabled("enable_memory_explorer"),
    },
    # Analytics
    {
        "route": "analytics",
        "label": "Analytics",
        "icon": "📊",
        "import": "src.ui_logic.pages.analytics",
        "feature_flag": "enable_automation",
        "roles": ["admin", "analyst", "devops"],
        "enabled": _flag_enabled("enable_automation"),
    },
    # Automation/Task management
    {
        "route": "automation",
        "label": "Automation",
        "icon": "🛠️",
        "import": "src.ui_logic.pages.automation",
        "feature_flag": "enable_workflows",
        "roles": ["user", "admin"],
        "enabled": _flag_enabled("enable_workflows"),
    },
    {
        "route": "task_manager",
        "label": "Task Manager",
        "icon": "📋",
        "import": "src.ui_logic.pages.task_manager",
        "feature_flag": "enable_task_manager",
        "roles": ["user", "admin", "devops"],
        "enabled": _flag_enabled("enable_task_manager"),
    },
    {
        "route": "autonomous",
        "label": "Autonomous Agents",
        "icon": "🤖",
        "import": "src.ui_logic.pages.autonomous",
        "feature_flag": "enable_autonomous_agents",
        "roles": ["admin", "devops"],
        "enabled": _flag_enabled("enable_autonomous_agents"),
    },
    # Plugins/Workflow
    {
        "route": "plugins",
        "label": "Plugins",
        "icon": "🧩",
        "import": "src.ui_logic.pages.plugins",
        "feature_flag": "enable_plugin_hot_reload",
        "roles": ["admin", "dev"],
        "enabled": _flag_enabled("enable_plugin_hot_reload"),
    },
    {
        "route": "workflows",
        "label": "Workflows",
        "icon": "🕸️",
        "import": "src.ui_logic.pages.workflows",
        "feature_flag": "enable_workflows",
        "roles": ["admin", "dev"],
        "enabled": _flag_enabled("enable_workflows"),
    },
    # Personas
    {
        "route": "personas",
        "label": "Personas",
        "icon": "🦹‍♂️",
        "import": "src.ui_logic.pages.personas",
        "feature_flag": "enable_advanced_personas",
        "roles": ["user", "admin", "analyst"],
        "enabled": _flag_enabled("enable_advanced_personas"),
    },
    # Files / Code / Vision / Voice
    {
        "route": "files",
        "label": "Files",
        "icon": "📁",
        "import": "src.ui_logic.pages.files",
        "feature_flag": None,
        "roles": ["user", "admin"],
        "enabled": _flag_enabled(None),
    },
    {
        "route": "code_lab",
        "label": "Code Lab",
        "icon": "🧪",
        "import": "src.ui_logic.pages.code_lab",
        "feature_flag": "enable_code_lab",
        "roles": ["admin", "dev"],
        "enabled": _flag_enabled("enable_code_lab"),
    },
    {
        "route": "vision",
        "label": "Vision",
        "icon": "👁️",
        "import": "src.ui_logic.pages.vision",
        "feature_flag": "enable_vision",
        "roles": ["user", "admin", "analyst"],
        "enabled": _flag_enabled("enable_vision"),
    },
    {
        "route": "voice",
        "label": "Voice",
        "icon": "🎙️",
        "import": "src.ui_logic.pages.voice",
        "feature_flag": "enable_voice",
        "roles": ["user", "admin", "analyst"],
        "enabled": _flag_enabled("enable_voice"),
    },
    # Admin/Security/Diagnostics
    {
        "route": "admin",
        "label": "Admin",
        "icon": "🛡️",
        "import": "src.ui_logic.pages.admin",
        "feature_flag": "enable_admin_panel",
        "roles": ["admin"],
        "enabled": _flag_enabled("enable_admin_panel"),
    },
    {
        "route": "security",
        "label": "Security",
        "icon": "🔒",
        "import": "src.ui_logic.pages.security",
        "feature_flag": "enable_security_center",
        "roles": ["admin"],
        "enabled": _flag_enabled("enable_security_center"),
    },
    {
        "route": "diagnostics",
        "label": "Diagnostics",
        "icon": "🧬",
        "import": "src.ui_logic.pages.diagnostics",
        "feature_flag": "enable_diagnostics",
        "roles": ["admin", "devops"],
        "enabled": _flag_enabled("enable_diagnostics"),
    },
    # Presence/IoT/Integrations
    {
        "route": "presence",
        "label": "Presence",
        "icon": "🌐",
        "import": "src.ui_logic.pages.presence",
        "feature_flag": "enable_presence",
        "roles": ["admin", "user"],
        "enabled": _flag_enabled("enable_presence"),
    },
    {
        "route": "iot",
        "label": "IoT",
        "icon": "🔌",
        "import": "src.ui_logic.pages.iot",
        "feature_flag": "enable_iot",
        "roles": ["admin", "user", "devops"],
        "enabled": _flag_enabled("enable_iot"),
    },
    {
        "route": "integrations",
        "label": "Integrations",
        "icon": "🔗",
        "import": "src.ui_logic.pages.integrations",
        "feature_flag": None,
        "roles": ["admin", "user"],
        "enabled": _flag_enabled(None),
    },
    # White Label / Branding / EchoCore / Labs
    {
        "route": "white_label",
        "label": "White Label",
        "icon": "🏷️",
        "import": "src.ui_logic.pages.white_label",
        "feature_flag": "enable_white_label",
        "roles": ["admin", "enterprise"],
        "enabled": _flag_enabled("enable_white_label"),
    },
    {
        "route": "labs",
        "label": "Labs",
        "icon": "🔬",
        "import": "src.ui_logic.pages.labs",
        "feature_flag": "enable_lab_tools",
        "roles": ["admin", "dev"],
        "enabled": _flag_enabled("enable_lab_tools"),
    },
    {
        "route": "echo_core",
        "label": "EchoCore",
        "icon": "🗝️",
        "import": "src.ui_logic.pages.echo_core",
        "feature_flag": "enable_echo_core",
        "roles": ["admin"],
        "enabled": _flag_enabled("enable_echo_core"),
    },
    # Context Panel
    {
        "route": "context",
        "label": "Context",
        "icon": "🧩",
        "import": "src.ui_logic.pages.context",
        "feature_flag": None,
        "roles": ["user", "admin"],
        "enabled": _flag_enabled(None),
    },
    # Settings
    {
        "route": "settings",
        "label": "Settings",
        "icon": "⚙️",
        "import": "src.ui_logic.pages.settings",
        "feature_flag": None,
        "roles": ["user", "admin"],
        "enabled": _flag_enabled(None),
    },
]


def get_pages(role: str | None = None) -> list:
    """Return enabled pages, optionally filtered by ``role``."""
    if role is None:
        return [p for p in PAGES if p["enabled"]]
    return [p for p in PAGES if p["enabled"] and (not p["roles"] or role in p["roles"])]


def get_page_manifest() -> list:
    """Return the raw page manifest."""
    return PAGES


# Dynamic plugin UI injection -------------------------------------------------
def register_plugin_page(page_dict: dict) -> None:
    """Register a plugin or extension page at runtime."""
    page_dict.setdefault("enabled", _flag_enabled(page_dict.get("feature_flag")))
    page_dict.setdefault("roles", [])
    PAGES.append(page_dict)


if __name__ == "__main__":
    import json

    print(json.dumps(get_page_manifest(), indent=2))
