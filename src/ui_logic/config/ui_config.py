"""
Kari UI Config – Supreme Source of UI Settings & Policy
- Unifies UI settings, defaults, providers, onboarding, RBAC, and dynamic plugin configs.
- NO hardcoded secrets, never store API keys here.
- All feature toggles live in feature_flags.py.
- All RBAC logic resolved at runtime.
- All settings can be overridden by ENV, .env, or external secrets.
"""

import os

# === UI Theming Defaults ===
THEME_DEFAULTS = {
    "theme": os.getenv("KARI_UI_THEME", "dark"),
    "accent": os.getenv("KARI_UI_ACCENT", "#bb00ff"),
    "background": os.getenv("KARI_UI_BG", "#161625"),
    "high_contrast": bool(int(os.getenv("KARI_UI_CONTRAST", "0"))),
    "font": os.getenv("KARI_UI_FONT", "Inter,Segoe UI,sans-serif"),
}

# === RBAC Policy for UI Panels ===
RBAC_UI = {
    "admin_only_panels": [
        "admin", "diagnostics", "security", "white_label", "echo_core"
    ],
    "user_panels": [
        "chat", "memory", "files", "settings", "context", "personas", "task_manager"
    ],
    "analyst_panels": [
        "analytics", "memory", "vision", "voice"
    ],
    "dev_panels": [
        "plugins", "workflows", "labs", "code_lab"
    ],
    "enterprise_panels": [
        "white_label", "branding_center"
    ],
}

# === Provider/Model Registry ===
PROVIDERS = {
    "llama-cpp": {
        "enabled": True,
        "label": "LLaMA-CPP (Local)",
        "default_models": ["tinyllama-1.1b-chat", "llama-2-7b-chat", "llama-2-13b-chat"],
        "api_key_required": False,
    },
    "gemini": {
        "enabled": True,
        "label": "Gemini",
        "default_models": ["gemini-pro", "gemini-vision"],
        "api_key_required": True,
    },
    "openai": {
        "enabled": True,
        "label": "OpenAI",
        "default_models": ["gpt-4o", "gpt-4", "gpt-3.5-turbo"],
        "api_key_required": True,
    },
    "anthropic": {
        "enabled": True,
        "label": "Anthropic",
        "default_models": ["claude-3-opus", "claude-3-sonnet"],
        "api_key_required": True,
    },
}

def get_enabled_providers():
    """Returns enabled providers only."""
    return {k: v for k, v in PROVIDERS.items() if v["enabled"]}

def get_default_model(provider: str) -> str:
    """Fetches default model for a given provider."""
    p = PROVIDERS.get(provider)
    return p["default_models"][0] if p and p["default_models"] else None

# === API Vault (NO KEYS STORED HERE) ===
def get_api_keys(user_ctx):
    """Fetch masked API keys for user (from secure store)."""
    # Should integrate with encrypted DB or keyvault, not local config
    from ui_logic.utils.api import fetch_api_keys
    return fetch_api_keys(user_ctx)

def save_api_key(user_ctx, api_name, api_value):
    """Persist encrypted API key (NEVER in plaintext config)."""
    from ui_logic.utils.api import store_api_key
    return store_api_key(user_ctx, api_name, api_value)

def delete_api_key(user_ctx, api_name):
    """Delete stored API key."""
    from ui_logic.utils.api import remove_api_key
    return remove_api_key(user_ctx, api_name)

# === Onboarding/Welcome UX ===
ONBOARDING = {
    "enable_wizard": bool(int(os.getenv("KARI_ENABLE_ONBOARDING", "1"))),
    "steps": [
        {"label": "Login/Register", "required_roles": []},
        {"label": "Profile & Consent", "required_roles": ["user"]},
        {"label": "Preferences", "required_roles": ["user"]},
        {"label": "Memory & Data Settings", "required_roles": ["user"]},
    ],
}

# === Branding/White-label (configurable at runtime) ===
def get_branding():
    from ui_logic.config.branding import get_branding_config
    return get_branding_config()

def save_branding(config, user_id=None):
    from ui_logic.config.branding import save_branding_config
    return save_branding_config(config, user_id)

# === Panel Registry for Extensible UI ===
def get_panel_config(panel_name):
    """Dynamic panel config; panels can self-register via plugin."""
    from pages_manifest import get_page_manifest
    for panel in get_page_manifest():
        if panel["route"] == panel_name:
            return panel
    return None

# === Misc UI Controls ===
UI_CONTROLS = {
    "max_sidebar_width": int(os.getenv("KARI_SIDEBAR_WIDTH", "340")),
    "show_beta_warning": bool(int(os.getenv("KARI_UI_BETA", "1"))),
    "support_email": os.getenv("KARI_SUPPORT_EMAIL", "support@kari.ai"),
}

# === Main entry ===
__all__ = [
    "THEME_DEFAULTS",
    "RBAC_UI",
    "PROVIDERS",
    "get_enabled_providers",
    "get_default_model",
    "get_api_keys",
    "save_api_key",
    "delete_api_key",
    "ONBOARDING",
    "get_branding",
    "save_branding",
    "get_panel_config",
    "UI_CONTROLS",
]
