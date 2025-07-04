"""
Kari UI: Global UI Configuration (Production)
- Central config hub for all UI apps (desktop, mobile, admin)
- Theme, branding, endpoint, layout, and RBAC rules
- ENV/config driven; all config changes live here.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

# === Default UI Config ===
DEFAULT_UI_CONFIG = {
    # --- Branding ---
    "app_name": "Kari AI",
    "logo_url": "/static/logo.svg",
    "footer": "© 2025 God Zeus. All diabolical rights reserved.",

    # --- Theme ---
    "theme": "dark",  # or "light", "enterprise", etc
    "accent_color": "#bb00ff",
    "background_color": "#161622",
    "font": "Inter, system-ui, sans-serif",
    "brand_palette": {
        "primary": "#bb00ff",
        "secondary": "#0dc3ff",
        "danger": "#d90036",
        "success": "#01bf71",
        "warning": "#ffad1f"
    },

    # --- Layout ---
    "sidebar_position": "left",  # or "right"
    "default_page": "chat",
    "show_branding": True,
    "compact_mode": False,
    "sidebar_width": 340,
    "max_content_width": 1240,

    # --- API/Backend ---
    "api_base_url": os.getenv("KARI_API_BASE_URL", "http://localhost:8000"),
    "enable_websocket": True,
    "websocket_url": os.getenv("KARI_WS_URL", "ws://localhost:8000/ws"),

    # --- RBAC/Permissions ---
    "enable_rbac": True,
    "role_map": {
        "admin": ["all"],
        "devops": ["diagnostics", "plugins", "analytics"],
        "user": ["chat", "profile", "plugins"],
        "guest": ["chat"]
    },

    # --- Misc ---
    "date_format": "%Y-%m-%d",
    "enable_notifications": True,
    "language": "en",
    "supported_languages": ["en", "es", "fr", "de"],
    "default_avatar": "/static/avatar_kari.png"
}

def load_ui_config(custom_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load UI config from file or ENV.
    Priority: custom_path > $KARI_UI_CONFIG > defaults
    """
    path = custom_path or os.getenv("KARI_UI_CONFIG")
    if path:
        path_obj = Path(path)
        if path_obj.exists():
            try:
                with open(path_obj, "r") as f:
                    cfg = json.load(f)
                    out = DEFAULT_UI_CONFIG.copy()
                    out.update(cfg)
                    return out
            except Exception:
                return DEFAULT_UI_CONFIG
    return DEFAULT_UI_CONFIG

def get_ui_config_value(key: str, custom_path: Optional[str] = None) -> Any:
    """Get a config value for key (from loaded UI config)."""
    cfg = load_ui_config(custom_path)
    return cfg.get(key, None)

def set_ui_config_value(key: str, value: Any, custom_path: Optional[str] = None):
    """
    Dynamically update a UI config file (for admin UI).
    If no custom_path, raises.
    """
    path = custom_path or os.getenv("KARI_UI_CONFIG")
    if not path:
        raise RuntimeError("No custom UI config file path set")
    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(f"UI config {path} does not exist")
    with open(path_obj, "r+") as f:
        data = json.load(f)
        data[key] = value
        f.seek(0)
        json.dump(data, f, indent=2)
        f.truncate()

def list_ui_config(custom_path: Optional[str] = None) -> Dict[str, Any]:
    """Return all loaded UI config values."""
    return load_ui_config(custom_path)

# === Public API ===
__all__ = [
    "get_ui_config_value",
    "set_ui_config_value",
    "list_ui_config",
    "load_ui_config",
    "DEFAULT_UI_CONFIG",
]
