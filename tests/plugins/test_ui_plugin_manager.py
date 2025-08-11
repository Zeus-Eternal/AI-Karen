import json
import json
import logging
import sys
from pathlib import Path

from types import ModuleType

sys.modules.setdefault("streamlit", ModuleType("streamlit"))

from ui_logic.components.plugins.plugin_manager import PluginManager


def create_plugin(tmp_path: Path) -> Path:
    plugin_dir = tmp_path / "test_plugin"
    plugin_dir.mkdir()
    manifest = {
        "name": "test",
        "description": "desc",
        "version": "0.1",
        "prompt_file": "prompt.txt",
        "handler_file": "handler.py",
        "enabled": True,
        "rbac": {},
    }
    (plugin_dir / "plugin_manifest.json").write_text(json.dumps(manifest))
    (plugin_dir / "prompt.txt").write_text("Hello {name}")
    (plugin_dir / "handler.py").write_text(
        "def run(prompt, input_data, context):\n    return prompt.format(**input_data)\n"
    )
    return plugin_dir


def test_plugin_manager_loads_module(tmp_path):
    create_plugin(tmp_path)
    pm = PluginManager(plugin_dir=tmp_path, logger=logging.getLogger("test"))
    plugin = pm.get_plugin("test")
    assert plugin["handler"] is not None
    result = pm.execute_plugin("test", {"name": "Kari"})
    assert result == "Hello Kari"
