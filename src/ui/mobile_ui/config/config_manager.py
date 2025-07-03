# ui/mobile_ui/config/config_manager.py
import os
import json
from .config_ui import ConfigUI

config = ConfigUI.load_from_env()
class ConfigManager:
    def __init__(self):
        self.app_name = "Kari AI"
        self.settings_path = os.path.join(os.path.dirname(__file__), "settings.json")
        self.settings = self._load_settings()

    def _load_settings(self):
        if os.path.exists(self.settings_path):
            with open(self.settings_path, "r") as f:
                return json.load(f)
        return {}

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value
        self._save_settings()

    def _save_settings(self):
        with open(self.settings_path, "w") as f:
            json.dump(self.settings, f, indent=2)
