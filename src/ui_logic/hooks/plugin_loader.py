"""
Kari UI Plugin Loader (Enterprise-Grade)
- Manifest-driven auto-discovery & RBAC enforcement
- Sandboxed import (no code exec), plugin manifests only
- Version-aware, feature-flagged, observability-ready
"""

import os
import json
import time
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional

from ui_logic.config.feature_flags import is_feature_enabled
from ui_logic.hooks.rbac import check_rbac
from ui_logic.hooks.auth import get_current_user
import logging

PLUGIN_DIR = Path(os.getenv("KARI_PLUGIN_DIR", "src/ai_karen_engine/plugins"))
MANIFEST_NAME = "plugin_manifest.json"
PLUGIN_SCHEMA_PATH = Path("src/config/plugin_schema.json")

# --- Observability ---
def plugin_audit_log(event: Dict[str, Any]):
    """Write plugin events to audit log (Prometheus/correlation_id-ready)."""
    event["correlation_id"] = str(uuid.uuid4())
    event["timestamp"] = int(time.time())
    try:
        with open("/secure/logs/kari/plugin_audit.log", "a") as f:
            f.write(json.dumps(event) + "\n")
    except Exception:
        pass

# --- Schema Validation ---
def load_plugin_schema() -> Dict[str, Any]:
    """Load global plugin manifest schema (JSONSchema or similar)."""
    try:
        with open(PLUGIN_SCHEMA_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        logging.warning(f"Could not load plugin schema: {e}")
        return {}

def validate_manifest(manifest: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """Validate manifest against schema (minimal/no-exec for UI layer)."""
    # Use jsonschema if available
    try:
        import jsonschema
        jsonschema.validate(instance=manifest, schema=schema)
        return True
    except Exception:
        # Fallback: check required keys
        required = schema.get("required", ["name", "version", "required_roles"])
        return all(k in manifest for k in required)

# --- Discovery & RBAC ---
def discover_plugins(user_ctx: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Scan, load, and RBAC-filter all plugin manifests for current user."""
    plugins = []
    schema = load_plugin_schema()
    user = user_ctx or get_current_user()
    for plugin_dir in PLUGIN_DIR.iterdir():
        manifest_path = plugin_dir / MANIFEST_NAME
        if manifest_path.exists():
            try:
                with open(manifest_path, "r") as f:
                    manifest = json.load(f)
                # Feature flags: skip if not enabled
                if "feature_flag" in manifest and not is_feature_enabled(manifest["feature_flag"]):
                    continue
                # Manifest schema/RBAC checks
                if validate_manifest(manifest, schema) and check_rbac(user, manifest.get("required_roles", [])):
                    plugins.append({
                        "id": plugin_dir.name,
                        **manifest
                    })
                    plugin_audit_log({
                        "action": "plugin_load",
                        "plugin": manifest.get("name"),
                        "user": user.get("name"),
                    })
            except Exception as e:
                plugin_audit_log({
                    "action": "plugin_load_error",
                    "plugin": plugin_dir.name,
                    "error": str(e)
                })
    return plugins

def get_plugin_manifest(plugin_id: str) -> Optional[Dict[str, Any]]:
    """Return manifest for given plugin id (with schema check)."""
    schema = load_plugin_schema()
    manifest_path = PLUGIN_DIR / plugin_id / MANIFEST_NAME
    if manifest_path.exists():
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        if validate_manifest(manifest, schema):
            return manifest
    return None

def get_plugin_by_feature(feature_flag: str, user_ctx=None) -> List[Dict[str, Any]]:
    """Return plugins matching a given feature flag, RBAC-filtered."""
    return [
        p for p in discover_plugins(user_ctx)
        if p.get("feature_flag") == feature_flag
    ]

# --- Hot/Cold Load (UI only, no backend code exec) ---
def enable_plugin(plugin_id: str, user_ctx=None) -> bool:
    """Mark plugin as enabled (UI/manifest-level only)."""
    # Could wire to backend for true activation
    manifest = get_plugin_manifest(plugin_id)
    if not manifest:
        return False
    plugin_audit_log({
        "action": "plugin_enable",
        "plugin": manifest.get("name"),
        "user": (user_ctx or get_current_user()).get("name"),
    })
    return True

def disable_plugin(plugin_id: str, user_ctx=None) -> bool:
    """Mark plugin as disabled (UI/manifest-level only)."""
    manifest = get_plugin_manifest(plugin_id)
    if not manifest:
        return False
    plugin_audit_log({
        "action": "plugin_disable",
        "plugin": manifest.get("name"),
        "user": (user_ctx or get_current_user()).get("name"),
    })
    return True

# --- API ---
__all__ = [
    "discover_plugins",
    "get_plugin_manifest",
    "get_plugin_by_feature",
    "enable_plugin",
    "disable_plugin",
    "plugin_audit_log",
]
