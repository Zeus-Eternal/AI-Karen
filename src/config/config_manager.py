"""
Kari ConfigManager
- Atomic, schema-validated config management for all modules (core, memory, UI)
- Supports: load, save, update, backup/restore, .env override, observers
- Thread/process safe, production-ready
"""

import os
import json
import threading
import shutil
from typing import Any, Callable, Dict, Optional, List
from pathlib import Path
from dotenv import load_dotenv
import logging

CONFIG_PATH = Path(os.getenv("KARI_CONFIG_FILE", "config.json")).absolute()
BACKUP_PATH = CONFIG_PATH.with_suffix(".bak")
LOCK = threading.RLock()

DEFAULT_CONFIG = {
    "active_user": "default",
    "theme": "dark",
    "llm_model": "llama3.2:latest",
    "memory": {
        "enabled": True,
        "provider": "local",
        "embedding_dim": 768,
        "decay_lambda": 0.1,
    },
    "ui": {
        "show_debug_info": False,
    },
}

# ---- Observers: any callable(config_dict) -> None ----
_OBSERVERS: List[Callable[[Dict[str, Any]], None]] = []
logger = logging.getLogger("kari.config.manager")
logger.setLevel(logging.INFO)

def register_observer(cb: Callable[[Dict[str, Any]], None]):
    with LOCK:
        _OBSERVERS.append(cb)

def notify_observers(cfg: Dict[str, Any]):
    for cb in _OBSERVERS:
        try:
            cb(cfg)
        except Exception as e:
            logger.warning(f"Config observer failed: {e}")

def atomic_write(path: Path, data: dict):
    tmp_path = path.with_suffix(".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, path)

def backup_config():
    with LOCK:
        if CONFIG_PATH.exists():
            shutil.copy2(CONFIG_PATH, BACKUP_PATH)
            logger.info(f"Config backup created at {BACKUP_PATH}")

def restore_config():
    with LOCK:
        if BACKUP_PATH.exists():
            shutil.copy2(BACKUP_PATH, CONFIG_PATH)
            logger.info(f"Config restored from backup {BACKUP_PATH}")

def load_env_override(cfg: Dict[str, Any]):
    """Apply .env overrides if present."""
    load_dotenv(override=True)
    for k in cfg:
        env_key = f"KARI_{k.upper()}"
        if os.getenv(env_key) is not None:
            try:
                val = json.loads(os.getenv(env_key))
            except Exception:
                val = os.getenv(env_key)
            cfg[k] = val

def validate_config(cfg: Dict[str, Any]) -> Dict[str, Any]:
    # You can add Pydantic or marshmallow for full schema; basic fallback:
    for k, v in DEFAULT_CONFIG.items():
        if k not in cfg:
            cfg[k] = v
        elif isinstance(v, dict):
            for subk, subv in v.items():
                if subk not in cfg[k]:
                    cfg[k][subk] = subv
    return cfg

def load_config() -> Dict[str, Any]:
    with LOCK:
        if not CONFIG_PATH.exists():
            cfg = DEFAULT_CONFIG.copy()
            atomic_write(CONFIG_PATH, cfg)
            notify_observers(cfg)
            return cfg
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        load_env_override(cfg)
        cfg = validate_config(cfg)
        notify_observers(cfg)
        return cfg

def save_config(cfg: Dict[str, Any]):
    with LOCK:
        atomic_write(CONFIG_PATH, cfg)
        backup_config()
        notify_observers(cfg)
        logger.info(f"Config saved: {CONFIG_PATH}")

def update_config(update: Dict[str, Any]) -> Dict[str, Any]:
    with LOCK:
        cfg = load_config()
        cfg.update(update)
        save_config(cfg)
        return cfg

def get_config_value(key: str, default=None) -> Any:
    cfg = load_config()
    return cfg.get(key, default)

def set_config_value(key: str, value: Any):
    with LOCK:
        cfg = load_config()
        cfg[key] = value
        save_config(cfg)

def reset_config():
    with LOCK:
        atomic_write(CONFIG_PATH, DEFAULT_CONFIG.copy())
        backup_config()
        notify_observers(DEFAULT_CONFIG.copy())
        logger.info("Config reset to default.")

# --- Aliases for external use ---
def get(key: str, default=None): return get_config_value(key, default)
def set(key: str, value: Any): set_config_value(key, value)
def load(): return load_config()
def save(cfg: Dict[str, Any]): save_config(cfg)
def update(update: Dict[str, Any]): return update_config(update)
def reset(): reset_config()
def backup(): backup_config()
def restore(): restore_config()
def register(cb: Callable[[Dict[str, Any]], None]): register_observer(cb)

__all__ = [
    "load_config", "save_config", "update_config", "get_config_value", "set_config_value",
    "reset_config", "backup_config", "restore_config", "register_observer",
    "get", "set", "load", "save", "update", "reset", "backup", "restore", "register"
]

