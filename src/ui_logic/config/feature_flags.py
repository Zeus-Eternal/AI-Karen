"""
Kari Feature Flags – Quantum-Grade Configuration
- All feature toggles for UI, logic, and experimental features
- Supports env var overrides and runtime injection
- Never allow unsafe features without ADVANCED_MODE=true
"""

import os

# === Hardcoded, documented defaults (can be extended at runtime) ===
FEATURE_FLAGS = {
    # --- Core UX ---
    "enable_multimodal_chat": True,
    "enable_advanced_personas": True,
    "enable_memory_explorer": True,
    "enable_voice": True,
    "enable_vision": False,
    "enable_presence": False,
    "enable_iot": False,

    # --- AI & Automation ---
    "enable_autonomous_agents": False,
    "enable_automation": True,
    "enable_task_manager": True,
    "enable_code_lab": True,
    "enable_lab_tools": False,  # for experimental lab/AI tools

    # --- Plugin/Extension System ---
    "enable_plugin_hot_reload": True,
    "enable_plugin_ui_injection": True,
    "enable_workflows": True,

    # --- Diagnostics/Admin ---
    "enable_admin_panel": True,
    "enable_diagnostics": True,
    "enable_prometheus_metrics": True,
    "enable_guardrails": False,

    # --- Security/Privacy ---
    "enable_security_center": True,
    "enable_privacy_console": True,
    "enable_encrypted_vault": True,

    # --- White Label/Branding ---
    "enable_white_label": False,
    "enable_branding_center": False,

    # --- Onboarding ---
    "enable_onboarding_wizard": True,

    # --- Experimental/ADVANCED_MODE ---
    "enable_echo_core": bool(os.getenv("ADVANCED_MODE", "false").lower() == "true"),
    "enable_self_refactor": bool(os.getenv("ADVANCED_MODE", "false").lower() == "true"),
}

def get_flag(flag: str) -> bool:
    """
    Get the value of a feature flag, supporting env overrides.
    - ENV: KARI_FEATURE_<FLAGNAME>
    - Example: KARI_FEATURE_ENABLE_AUTOMATION=true
    """
    env_key = f"KARI_FEATURE_{flag.upper()}"
    if env_key in os.environ:
        val = os.environ[env_key].lower()
        return val in ("1", "true", "yes", "on")
    return FEATURE_FLAGS.get(flag, False)

def set_flag(flag: str, value: bool):
    """Set or update a feature flag at runtime (dangerous; audit when used)."""
    FEATURE_FLAGS[flag] = bool(value)

def all_flags() -> dict:
    """Return the full feature flag dictionary (for UI or admin display)."""
    return {flag: get_flag(flag) for flag in FEATURE_FLAGS}

# Example extension: allow plugins to register custom flags
def register_plugin_flag(flag: str, default: bool = False):
    """Register a new plugin/extension feature flag."""
    if flag not in FEATURE_FLAGS:
        FEATURE_FLAGS[flag] = default

def is_feature_enabled(key: str, custom_path: str | None = None) -> bool:
    """Return ``True`` if the feature flag ``key`` is enabled."""
    return bool(get_flag(key))

# === Public API ===
__all__ = [
    "get_flag",
    "set_flag",
    "all_flags",
    "register_plugin_flag",
    "is_feature_enabled",
]
