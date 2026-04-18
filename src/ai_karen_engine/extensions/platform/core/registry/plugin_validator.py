"""
Plugin Validator: Strict Prompt-First Validation Utility.
Use this to verify plugin packages against the AI Karen manifest schema.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import jsonschema

# Standard paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
SCHEMA_PATH = Path(__file__).resolve().parent / "plugin_manifest.schema.json"

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("plugin_validator")

class PluginValidationError(Exception):
    def __init__(self, message: str, errors: Optional[List[str]] = None):
        super().__init__(message)
        self.errors = errors or []

def validate_plugin_package(package_path: str) -> Dict[str, Any]:
    """
    Validates a plugin directory against the Prompt-First modular platform standards.
    Returns the loaded manifest if successful.
    """
    path = Path(package_path)
    if not path.is_dir():
        raise PluginValidationError(f"Path is not a directory: {package_path}")

    # 1. Manifest Existence
    manifest_path = path / "plugin_manifest.json"
    if not manifest_path.exists():
        raise PluginValidationError(f"Missing required manifest: {manifest_path}")

    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
    except json.JSONDecodeError as e:
        raise PluginValidationError(f"Manifest contains invalid JSON: {e}")

    # 2. Schema Validation
    if SCHEMA_PATH.exists():
        try:
            with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            jsonschema.validate(instance=manifest, schema=schema)
        except jsonschema.ValidationError as e:
            raise PluginValidationError(f"Schema validation failed: {e.message}", [str(err) for err in e.context] if e.context else [])
    else:
        logger.warning("Manifest schema not found at %s. Skipping JSON Schema check.", SCHEMA_PATH)

    # 3. Prompt-First Asset Check
    prompt_path = path / "prompt.txt"
    if not prompt_path.exists():
        logger.warning("No prompt.txt found for plugin '%s'. Prompt-First AI orchestration might be limited.", manifest.get('name'))

    # 4. Logic Integrity Check
    handler_path = path / "handler.py"
    if not handler_path.exists():
        logger.info("No handler.py found. Plugin will be treated as prompt-only or static asset.")

    # 4. Requirements Check (Optional but recommended)
    req_file = path / "requirements.txt"
    if req_file.exists():
        logger.info(f"Checking dependencies in {req_file.name}...")
        with open(req_file, "r") as f:
            manifest["_requirements"] = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    else:
        manifest["_requirements"] = []

    return manifest

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python plugin_validator.py <plugin_directory>")
        sys.exit(1)

    target = sys.argv[1]
    try:
        manifest = validate_plugin_package(target)
        print(f"\u2705 SUCCESS: Plugin '{manifest['name']}' (v{manifest['version']}) is valid.")
        print(f"   Intent: {manifest['intent']}")
        print(f"   Capabilities: {list(manifest.get('capabilities', {}).keys())}")
    except PluginValidationError as e:
        print(f"\u274c FAILED: {e}")
        for err in e.errors:
            print(f"   - {err}")
        sys.exit(1)
    except Exception as e:
        print(f"\u274c UNEXPECTED ERROR: {e}")
        sys.exit(1)
