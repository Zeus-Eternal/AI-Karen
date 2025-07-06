"""
Kari UI Branding Config (Enterprise Production)
- Centralized color/logo/branding state for all UI layers.
- White-label and multi-tenant: ENV, file, or admin dynamic.
- Includes get_branding_config alias for legacy compatibility.
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path
import json

# === Default Branding (env-driven, never hardcoded in UI) ===
DEFAULT_BRANDING = {
    "product_name": os.getenv("KARI_PRODUCT_NAME", "Kari AI"),
    "primary_color": os.getenv("KARI_BRAND_PRIMARY", "#bb00ff"),
    "accent_color": os.getenv("KARI_BRAND_ACCENT", "#ffef32"),
    "secondary_color": os.getenv("KARI_BRAND_SECONDARY", "#0a1931"),
    "text_color": os.getenv("KARI_BRAND_TEXT", "#181818"),
    "background_color": os.getenv("KARI_BRAND_BG", "#f8f8fb"),
    "logo_path": os.getenv("KARI_BRAND_LOGO", "/static/kari_logo.svg"),
    "favicon_path": os.getenv("KARI_BRAND_FAVICON", "/static/favicon.ico"),
    "footer_text": os.getenv("KARI_BRAND_FOOTER", "© 2025 God Zeus. All rights reserved."),
    "powered_by": os.getenv("KARI_BRAND_POWERED", "Powered by Kari AI"),
    "theme": os.getenv("KARI_UI_THEME", "auto"),  # auto/dark/light
}

def load_branding_config(custom_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load branding config from a file or return defaults.
    Priority: custom_path > $KARI_BRAND_CONFIG > defaults
    """
    path = custom_path or os.getenv("KARI_BRAND_CONFIG")
    if path:
        path_obj = Path(path)
        if path_obj.exists():
            with open(path_obj, "r") as f:
                try:
                    cfg = json.load(f)
                    out = DEFAULT_BRANDING.copy()
                    out.update(cfg)
                    return out
                except Exception:
                    # Fallback to defaults on parse error
                    return DEFAULT_BRANDING
    return DEFAULT_BRANDING

def get_branding(key: Optional[str] = None, custom_path: Optional[str] = None) -> Any:
    """
    Get the branding dictionary or a single key.
    """
    config = load_branding_config(custom_path)
    if key is None:
        return config
    return config.get(key, None)

# --- Legacy/compat import for zero-downtime upgrades ---
def get_branding_config(*args, **kwargs):
    """Alias for get_branding (legacy code, do not remove)."""
    return get_branding(*args, **kwargs)

def set_branding_value(key: str, value: Any, custom_path: Optional[str] = None):
    """
    Dynamically update branding config file (if supported).
    If no custom_path, raises (UI/admin tool should handle).
    """
    path = custom_path or os.getenv("KARI_BRAND_CONFIG")
    if not path:
        raise RuntimeError("No custom branding config path set")
    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Branding config {path} does not exist")
    with open(path_obj, "r+") as f:
        data = json.load(f)
        data[key] = value
        f.seek(0)
        json.dump(data, f, indent=2)
        f.truncate()

__all__ = [
    "get_branding",
    "get_branding_config",   # For legacy/compatibility
    "set_branding_value",
    "load_branding_config",
    "DEFAULT_BRANDING"
]
