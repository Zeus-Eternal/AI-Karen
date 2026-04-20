import os
import json
import threading
from typing import Dict, Any, List

class TimeQueryStateStore:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(TimeQueryStateStore, cls).__new__(cls)
                cls._instance._init_paths()
                cls._instance.stopwatch_state = cls._instance._load("stopwatch", {})
                cls._instance.alarm_state = cls._instance._load("alarm", [])
                cls._instance.clock_state = cls._instance._load("clocks", ["UTC", "America/New_York"])
        return cls._instance

    def _init_paths(self):
        self.storage_dir = os.path.join(os.path.dirname(__file__), "..", "storage")
        os.makedirs(self.storage_dir, exist_ok=True)

    def _get_path(self, key: str) -> str:
        return os.path.join(self.storage_dir, f"{key}_state.json")

    def _load(self, key: str, default: Any) -> Any:
        try:
            with open(self._get_path(key), "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return default

    def _save(self, key: str, data: Any):
        with open(self._get_path(key), "w") as f:
            json.dump(data, f)

    # Scoped accessors
    
    def get_stopwatch(self) -> Dict[str, Any]:
        return self.stopwatch_state

    def save_stopwatch(self, data: Dict[str, Any]):
        self.stopwatch_state = data
        self._save("stopwatch", data)

    def get_alarms(self) -> List[Dict[str, Any]]:
        return self.alarm_state
        
    def save_alarms(self, data: List[Dict[str, Any]]):
        self.alarm_state = data
        self._save("alarm", data)
        
    def get_clocks(self) -> List[str]:
        return self.clock_state
        
    def save_clocks(self, data: List[str]):
        self.clock_state = data
        self._save("clocks", data)
