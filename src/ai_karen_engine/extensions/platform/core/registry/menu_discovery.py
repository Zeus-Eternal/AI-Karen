"""Menu contribution discovery for extensions and plugins."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

ALLOWED_ICON_EXTENSIONS = {".svg", ".png", ".jpg", ".jpeg", ".webp", ".ico"}

PLACEMENT_ALIASES: Dict[str, Dict[str, Any]] = {
    "sidebar": {"zone": "sidebar.plugins", "subzones": None},
    "sidebar-plugins": {"zone": "sidebar.plugins", "subzones": None},
    "sidebar-settings": {"zone": "sidebar.settings", "subzones": None},
    "sidebar-admin": {"zone": "sidebar.admin", "subzones": None},
    "sidebar-communications": {"zone": "sidebar.communications", "subzones": None},
    "communications-center": {
        "zone": "page.communications.tabs",
        "subzones": {"channels", "automation"},
    },
    "application-settings": {
        "zone": "page.settings.sections",
        "subzones": {"personal", "privacy", "models"},
    },
    "admin-settings": {
        "zone": "page.admin.sections",
        "subzones": {"plugins", "security", "observability"},
    },
    "plugin-overview": {"zone": "page.plugins.overview", "subzones": None},
    "dashboard": {"zone": "page.dashboard.sections", "subzones": None},
}

ICON_DISCOVERY_RE = re.compile(
    r"^(?P<plugin_id>[a-z0-9][a-z0-9-]*)---"
    r"(?P<placement>[a-z0-9-]+)"
    r"(?P<subzones>(?:--[a-z0-9-]+)*)"
    r"(?:_(?P<order>\d{2}))?$"
)


def default_menu_label(plugin_id: str) -> str:
    return " ".join(part.capitalize() for part in plugin_id.replace("_", "-").split("-") if part)


def discover_menu_contributions(
    *,
    plugin_id: str,
    display_name: Optional[str],
    extension_dir: Path,
    manifest_data: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Build normalized menu contributions from manifest data and icon conventions."""
    explicit_entries = _extract_explicit_menu_entries(manifest_data)
    if explicit_entries:
        normalized = []
        for index, entry in enumerate(explicit_entries):
            item = _normalize_manifest_menu_entry(
                plugin_id=plugin_id,
                display_name=display_name,
                extension_dir=extension_dir,
                entry=entry,
                index=index,
            )
            if item:
                normalized.append(item)
        return normalized

    normalized = []
    for asset in sorted(extension_dir.iterdir(), key=lambda item: item.name.lower()):
        if not asset.is_file() or asset.suffix.lower() not in ALLOWED_ICON_EXTENSIONS:
            continue
        entry = _normalize_icon_menu_entry(
            plugin_id=plugin_id,
            display_name=display_name,
            extension_dir=extension_dir,
            asset=asset,
        )
        if entry:
            normalized.append(entry)
    return normalized


def _extract_explicit_menu_entries(manifest_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    ui_config = manifest_data.get("ui") or {}
    if isinstance(ui_config, dict):
        entries = ui_config.get("menu") or ui_config.get("menu_entries")
        if isinstance(entries, list):
            return [entry for entry in entries if isinstance(entry, dict)]

    entries = manifest_data.get("menu") or manifest_data.get("menu_entries")
    if isinstance(entries, list):
        return [entry for entry in entries if isinstance(entry, dict)]
    return []


def _normalize_manifest_menu_entry(
    *,
    plugin_id: str,
    display_name: Optional[str],
    extension_dir: Path,
    entry: Dict[str, Any],
    index: int,
) -> Optional[Dict[str, Any]]:
    placement_alias = str(entry.get("placement") or entry.get("alias") or "").strip().lower()
    mapping = PLACEMENT_ALIASES.get(placement_alias)
    if not mapping:
        return None

    subzone = entry.get("subzone")
    if subzone is not None:
        subzone = str(subzone).strip().lower()
        valid_subzones = mapping.get("subzones")
        if valid_subzones and subzone not in valid_subzones:
            return None
    else:
        subzone = None

    icon_path = entry.get("icon")
    if icon_path:
        icon_rel = str(icon_path)
    else:
        icon_rel = ""

    order = entry.get("order")
    auto_order = order in (None, 0, "0", "00")
    normalized_order = None if auto_order else int(order)
    label = str(entry.get("label") or display_name or default_menu_label(plugin_id))
    entry_id = _build_entry_id(plugin_id, mapping["zone"], subzone, index)
    return {
        "plugin_id": plugin_id,
        "entry_id": entry_id,
        "label": label,
        "zone": mapping["zone"],
        "subzone": subzone,
        "order": normalized_order,
        "auto_order": auto_order,
        "icon_path": icon_rel,
        "source": "manifest",
        "placement_alias": placement_alias,
    }


def _normalize_icon_menu_entry(
    *,
    plugin_id: str,
    display_name: Optional[str],
    extension_dir: Path,
    asset: Path,
) -> Optional[Dict[str, Any]]:
    match = ICON_DISCOVERY_RE.match(asset.stem)
    if not match:
        return None
    if match.group("plugin_id") != plugin_id:
        return None

    placement_alias = match.group("placement")
    mapping = PLACEMENT_ALIASES.get(placement_alias)
    if not mapping:
        return None

    raw_subzones = match.group("subzones") or ""
    subzone_parts = [part for part in raw_subzones.split("--") if part]
    subzone = "--".join(subzone_parts) if subzone_parts else None
    valid_subzones = mapping.get("subzones")
    if valid_subzones and subzone not in valid_subzones:
        return None
    if not valid_subzones:
        subzone = None

    raw_order = match.group("order")
    auto_order = raw_order in (None, "00")
    order = None if auto_order else int(raw_order)
    entry_id = _build_entry_id(plugin_id, mapping["zone"], subzone, 0)
    return {
        "plugin_id": plugin_id,
        "entry_id": entry_id,
        "label": display_name or default_menu_label(plugin_id),
        "zone": mapping["zone"],
        "subzone": subzone,
        "order": order,
        "auto_order": auto_order,
        "icon_path": asset.relative_to(extension_dir).as_posix(),
        "source": "icon-discovery",
        "placement_alias": placement_alias,
    }


def _build_entry_id(plugin_id: str, zone: str, subzone: Optional[str], index: int) -> str:
    zone_id = zone.replace("page.", "").replace("sidebar.", "sidebar-").replace(".", "-")
    if subzone:
        return f"{plugin_id}.{zone_id}.{subzone}.{index}"
    return f"{plugin_id}.{zone_id}.{index}"
