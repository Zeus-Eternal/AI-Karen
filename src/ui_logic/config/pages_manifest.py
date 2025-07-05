"""
Kari Pages Manifest – Ultra-Sovereign Navigation Control
- Defines all UI pages, roles, icons, and feature flags.
- Auto-discovers plugin/extension pages at runtime.
- Enforces RBAC and feature flag logic.
"""

import os
from ui_logic.config.feature_flags import get_flag

# --- Core pages manifest ---
PAGES = [
    # Public/Home/Onboarding
    {
        "route": "home",
        "label": "Home",
        "icon": "🏠",
        "import": "ui_logic.pages.home",
        "feature_flag": None,
        "required_roles": [],
        "enabled": True,
    },
    {
        "route": "onboarding",
        "label": "Onboarding",
        "icon": "🧭",
        "import": "ui_logic.pages.onboarding",
        "feature_flag": "enable_onboarding_wizard",
        "required_roles": [],
        "enabled": get_flag("enable_onboarding_wizard"),
    },
    # Chat/Core Interaction
    {
        "route": "chat",
        "label": "Chat",
        "icon": "💬",
        "import": "ui_logic.pages.chat",
        "feature_flag": None,
        "required_roles": ["user", "admin"],
        "enabled": True,
    },
    # Memory/Knowledge
    {
        "route": "memory",
        "label": "Memory",
        "icon": "🧠",
        "import": "ui_logic.pages.memory",
        "feature_flag": "enable_memory_explorer",
        "required_roles": ["user", "admin"],
        "enabled": get_flag("enable_memory_explorer"),
    },
    # Analytics
    {
        "route": "analytics",
        "label": "Analytics",
        "icon": "📊",
        "import": "ui_logic.pages.analytics",
        "feature_flag": "enable_automation",
        "required_roles": ["admin", "analyst", "devops"],
        "enabled": get_flag("enable_automation"),
    },
    # Task/Automation/Autonomous Agents
    {
        "route": "task_manager",
        "label": "Task Manager",
        "icon": "📋",
        "import": "ui_logic.pages.task_manager",
        "feature_flag": "enable_task_manager",
        "required_roles": ["user", "admin", "devops"],
        "enabled": get_flag("enable_task_manager"),
    },
    {
        "route": "autonomous",
        "label": "Autonomous Agents",
        "icon": "🤖",
        "import": "ui_logic.pages.autonomous",
        "feature_flag": "enable_autonomous_agents",
        "required_roles": ["admin", "devops"],
        "enabled": get_flag("enable_autonomous_agents"),
    },
    # Scheduling/Calendar
    {
        "route": "calendar",
        "label": "Calendar",
        "icon": "🗓️",
        "import": "ui_logic.pages.scheduling",
        "feature_flag": "enable_automation",
        "required_roles": ["user", "admin"],
        "enabled": get_flag("enable_automation"),
    },
    # Plugins/Workflow
    {
        "route": "plugins",
        "label": "Plugins",
        "icon": "🧩",
        "import": "ui_logic.pages.plugins",
        "feature_flag": "enable_plugin_hot_reload",
        "required_roles": ["admin", "dev"],
        "enabled": get_flag("enable_plugin_hot_reload"),
    },
    {
        "route": "workflows",
        "label": "Workflows",
        "icon": "🕸️",
        "import": "ui_logic.pages.workflows",
        "feature_flag": "enable_workflows",
        "required_roles": ["admin", "dev"],
        "enabled": get_flag("enable_workflows"),
    },
    # Personas
    {
        "route": "personas",
        "label": "Personas",
        "icon": "🦹‍♂️",
        "import": "ui_logic.pages.personas",
        "feature_flag": "enable_advanced_personas",
        "required_roles": ["user", "admin", "analyst"],
        "enabled": get_flag("enable_advanced_personas"),
    },
    # Files / Code / Vision / Voice
    {
        "route": "files",
        "label": "Files",
        "icon": "📁",
        "import": "ui_logic.pages.files",
        "feature_flag": None,
        "required_roles": ["user", "admin"],
        "enabled": True,
    },
    {
        "route": "code_lab",
        "label": "Code Lab",
        "icon": "🧪",
        "import": "ui_logic.pages.code_lab",
        "feature_flag": "enable_code_lab",
        "required_roles": ["admin", "dev"],
        "enabled": get_flag("enable_code_lab"),
    },
    {
        "route": "vision",
        "label": "Vision",
        "icon": "👁️",
        "import": "ui_logic.pages.vision",
        "feature_flag": "enable_vision",
        "required_roles": ["user", "admin", "analyst"],
        "enabled": get_flag("enable_vision"),
    },
    {
        "route": "voice",
        "label": "Voice",
        "icon": "🎙️",
        "import": "ui_logic.pages.voice",
        "feature_flag": "enable_voice",
        "required_roles": ["user", "admin", "analyst"],
        "enabled": get_flag("enable_voice"),
    },
    # Admin/Security/Diagnostics
    {
        "route": "admin",
        "label": "Admin",
        "icon": "🛡️",
        "import": "ui_logic.pages.admin",
        "feature_flag": "enable_admin_panel",
        "required_roles": ["admin"],
        "enabled": get_flag("enable_admin_panel"),
    },
    {
        "route": "security",
        "label": "Security",
        "icon": "🔒",
        "import": "ui_logic.pages.security",
        "feature_flag": "enable_security_center",
        "required_roles": ["admin"],
        "enabled": get_flag("enable_security_center"),
    },
    {
        "route": "diagnostics",
        "label": "Diagnostics",
        "icon": "🧬",
        "import": "ui_logic.pages.diagnostics",
        "feature_flag": "enable_diagnostics",
        "required_roles": ["admin", "devops"],
        "enabled": get_flag("enable_diagnostics"),
    },
    # Presence/IoT/Integrations
    {
        "route": "presence",
        "label": "Presence",
        "icon": "🌐",
        "import": "ui_logic.pages.presence",
        "feature_flag": "enable_presence",
        "required_roles": ["admin", "user"],
        "enabled": get_flag("enable_presence"),
    },
    {
        "route": "iot",
        "label": "IoT",
        "icon": "🔌",
        "import": "ui_logic.pages.iot",
        "feature_flag": "enable_iot",
        "required_roles": ["admin", "user", "devops"],
        "enabled": get_flag("enable_iot"),
    },
    {
        "route": "integrations",
        "label": "Integrations",
        "icon": "🔗",
        "import": "ui_logic.pages.integrations",
        "feature_flag": None,
        "required_roles": ["admin", "user"],
        "enabled": True,
    },
    # White Label / Branding / EchoCore / Labs
    {
        "route": "white_label",
        "label": "White Label",
        "icon": "🏷️",
        "import": "ui_logic.pages.white_label",
        "feature_flag": "enable_white_label",
        "required_roles": ["admin", "enterprise"],
        "enabled": get_flag("enable_white_label"),
    },
    {
        "route": "labs",
        "label": "Labs",
        "icon": "🔬",
        "import": "ui_logic.pages.labs",
        "feature_flag": "enable_lab_tools",
        "required_roles": ["admin", "dev"],
        "enabled": get_flag("enable_lab_tools"),
    },
    {
        "route": "echo_core",
        "label": "EchoCore",
        "icon": "🗝️",
        "import": "ui_logic.pages.echo_core",
        "feature_flag": "enable_echo_core",
        "required_roles": ["admin"],
        "enabled": get_flag("enable_echo_core"),
    },
    # Context Panel
    {
        "route": "context",
        "label": "Context",
        "icon": "🧩",
        "import": "ui_logic.pages.context",
        "feature_flag": None,
        "required_roles": ["user", "admin"],
        "enabled": True,
    },
    # Settings
    {
        "route": "settings",
        "label": "Settings",
        "icon": "⚙️",
        "import": "ui_logic.pages.settings",
        "feature_flag": None,
        "required_roles": ["user", "admin"],
        "enabled": True,
    },
]

def get_pages(role: str = None) -> list:
    """
    Returns all enabled pages, optionally filtered by role.
    :param role: Filter to pages visible to this role.
    """
    if role is None:
        # Return all enabled pages
        return [p for p in PAGES if p["enabled"]]
    return [
        p for p in PAGES
        if p["enabled"] and (not p["required_roles"] or role in p["required_roles"])
    ]

def get_page_manifest() -> list:
    """Returns the manifest for use by navigation, routing, admin UI."""
    return PAGES

# Dynamic plugin UI injection (plugins can call this at runtime)
def register_plugin_page(page_dict: dict):
    """Register a new plugin or extension page at runtime (MUST follow manifest schema)."""
    PAGES.append(page_dict)

if __name__ == "__main__":
    # Demo: print manifest (evil audit mode)
    import json
    print(json.dumps(get_page_manifest(), indent=2))
