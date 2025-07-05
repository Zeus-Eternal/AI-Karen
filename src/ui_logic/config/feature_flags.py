"""
Kari UI Feature Flags (Production)
- Centralized, config/ENV-driven flag control for UI & business logic.
- Powers A/B tests, premium unlocks, plugin rollouts, enterprise features.
- No UI logic—pure state/config.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

# === Default Feature Flags (lowest privilege, never delete) ===
DEFAULT_FLAGS = {
    "enable_plugins": True,
    "enable_workflows": True,
    "enable_voice_io": False,
    "enable_multimodal": False,
    "enable_memory_graph": True,
    "enable_rbac": True,
    "enable_premium": False,
    "enable_enterprise": False,
    "enable_admin_panel": True,
    "allow_cloud_models": False,    # Only local LLMs unless explicitly unlocked
    "show_experimental": False,
    "force_safe_mode": False,       # RBAC/guardrails override
    "show_branding_controls": False,
    "enable_api_tokens": False,
    "allow_shell_exec": False,      # Security-critical
}

def load_feature_flags(custom_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load feature flags from a config JSON, ENV, or fall back to defaults.
    Priority: custom_path > $KARI_FEATURE_FLAGS > defaults
    """
    path = custom_path or os.getenv("KARI_FEATURE_FLAGS")
    if path:
        path_obj = Path(path)
        if path_obj.exists():
            try:
                with open(path_obj, "r") as f:
                    cfg = json.load(f)
                    out = DEFAULT_FLAGS.copy()
                    out.update(cfg)
                    return out
            except Exception:
                return DEFAULT_FLAGS
    return DEFAULT_FLAGS

def get_flag(key: str, custom_path: Optional[str] = None) -> Any:
    """Get a feature flag value."""
    flags = load_feature_flags(custom_path)
    return flags.get(key, None)

def set_flag(key: str, value: Any, custom_path: Optional[str] = None):
    """
    Dynamically update a feature flag config file (for admin UI).
    If no custom_path, raises (feature flag admin UI should handle persistence).
    """
    path = custom_path or os.getenv("KARI_FEATURE_FLAGS")
    if not path:
        raise RuntimeError("No custom feature flag config path set")
    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Feature flags config {path} does not exist")
    with open(path_obj, "r+") as f:
        data = json.load(f)
        data[key] = value
        f.seek(0)
        json.dump(data, f, indent=2)
        f.truncate()

def list_flags(custom_path: Optional[str] = None) -> Dict[str, Any]:
    """Get all flags (resolved from config, ENV, or defaults)."""
    return load_feature_flags(custom_path)


def is_feature_enabled(key: str, custom_path: str | None = None) -> bool:
    """Return ``True`` if the feature flag ``key`` is enabled."""
    return bool(get_flag(key, custom_path))

# === Public API ===
__all__ = [
    "get_flag",
    "set_flag",
    "list_flags",
    "load_feature_flags",
    "is_feature_enabled",
    "DEFAULT_FLAGS",
]
