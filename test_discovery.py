#!/usr/bin/env python3
"""
Test plugin discovery simulation.
"""

import json
import logging
from pathlib import Path

# Set up logging to see debug messages
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def simulate_discovery():
    """Simulate the discovery process for the web-search plugin."""
    print("Simulating Web-Search Plugin Discovery")
    print("=" * 50)

    # Path to extensions directory
    extensions_dir = Path("src/ai_karen_engine/extensions/plugins")

    if not extensions_dir.exists():
        print(f"✗ Extensions directory not found: {extensions_dir}")
        return

    print(f"Scanning extensions directory: {extensions_dir}")

    # Simulate the discovery process
    discovered_plugins = {}

    # Look for plugin directories
    for item in extensions_dir.rglob("*"):
        if not item.is_dir() or item.name.startswith("_"):
            continue

        # Check if this directory has a manifest file
        manifest_file = find_manifest_file(item)
        if manifest_file:
            print(f"\nFound plugin directory: {item.name}")
            print(f"Manifest file: {manifest_file}")

            try:
                # Load and validate manifest
                with open(manifest_file, "r", encoding="utf-8") as f:
                    manifest_data = json.load(f)

                print(f"Plugin name: {manifest_data.get('name', 'Unknown')}")
                print(f"Plugin version: {manifest_data.get('version', 'Unknown')}")
                print(f"Display name: {manifest_data.get('display_name', 'Unknown')}")

                # Check for required fields
                required_fields = [
                    "name",
                    "version",
                    "display_name",
                    "description",
                    "author",
                    "license",
                    "category",
                ]
                missing_fields = [
                    field for field in required_fields if field not in manifest_data
                ]

                if missing_fields:
                    print(f"✗ Missing required fields: {missing_fields}")
                else:
                    print(f"✓ All required fields present")

                # Check entrypoint
                entrypoint = manifest_data.get("entrypoint")
                if entrypoint:
                    print(f"Entrypoint: {entrypoint}")
                    if ":" not in entrypoint:
                        print(f"✗ Invalid entrypoint format")
                    else:
                        print(f"✓ Valid entrypoint format")
                else:
                    print(f"⚠ No entrypoint specified")

                # Check handler file
                handler_file = item / "handler.py"
                if handler_file.exists():
                    print(f"✓ Handler file found: {handler_file}")
                else:
                    print(f"✗ Handler file missing: {handler_file}")

                # Check for MainExtension class
                if handler_file.exists():
                    with open(handler_file, "r", encoding="utf-8") as f:
                        handler_content = f.read()

                    if "class MainExtension" in handler_content:
                        print(f"✓ MainExtension class found")
                    else:
                        print(f"✗ MainExtension class not found")

                discovered_plugins[item.name] = {
                    "manifest_file": str(manifest_file),
                    "handler_file": str(handler_file)
                    if handler_file.exists()
                    else None,
                    "valid": len(missing_fields) == 0,
                    "has_entrypoint": bool(entrypoint and ":" in entrypoint),
                    "has_main_extension": "class MainExtension" in handler_content
                    if handler_file.exists()
                    else False,
                }

            except Exception as e:
                print(f"✗ Error processing manifest: {e}")

    print(f"\n{'=' * 50}")
    print("DISCOVERY SUMMARY")
    print(f"{'=' * 50}")
    print(f"Total plugins discovered: {len(discovered_plugins)}")

    for plugin_name, info in discovered_plugins.items():
        print(f"\nPlugin: {plugin_name}")
        print(f"  - Valid: {info['valid']}")
        print(f"  - Has entrypoint: {info['has_entrypoint']}")
        print(f"  - Has MainExtension: {info['has_main_extension']}")
        print(f"  - Handler file: {info['handler_file']}")

        if plugin_name == "web-search":
            if not info["valid"]:
                print(f"  ✗ Web-search plugin is invalid")
            elif not info["has_entrypoint"]:
                print(f"  ✗ Web-search plugin missing valid entrypoint")
            elif not info["has_main_extension"]:
                print(f"  ✗ Web-search plugin missing MainExtension class")
            else:
                print(f"  ✓ Web-search plugin is valid and should be discoverable")


def find_manifest_file(extension_dir: Path) -> Path:
    """Find the manifest file in an extension directory."""
    manifest_names = [
        "plugin_manifest.json",
        "extension_manifest.json",
        "extension.json",
        "manifest.json",
    ]

    for manifest_name in manifest_names:
        manifest_file = extension_dir / manifest_name
        if manifest_file.exists():
            return manifest_file

    return None


if __name__ == "__main__":
    simulate_discovery()
