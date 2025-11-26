"""
Configuration management for the llama.cpp server.

The cfg loader supports:
- JSON config file
- env var overrides (LLAMA_SERVER__SECTION__KEY)
- sane defaults
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


def _env_override(key: str, default: Any) -> Any:
    env_key = key.upper().replace(".", "__")
    val = os.getenv(f"LLAMA_SERVER__{env_key}")
    if val is None:
        return default
    if isinstance(default, bool):
        return val.lower() in {"1", "true", "yes", "on"}
    if isinstance(default, int):
        try:
            return int(val)
        except ValueError:
            return default
    return val


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged: Dict[str, Any] = dict(base)
    for k, v in override.items():
        if k in merged and isinstance(merged[k], dict) and isinstance(v, dict):
            merged[k] = _merge(merged[k], v)
        else:
            merged[k] = v
    return merged


@dataclass
class ServerConfig:
    config_path: Path = Path("config.json")
    data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Optional[str] = None) -> "ServerConfig":
        cfg_path = Path(path) if path else Path("config.json")
        defaults: Dict[str, Any] = {
            "server": {
                "host": "0.0.0.0",
                "port": 8080,
                "log_level": "info",
                "use_tls": False,
                "certfile": None,
                "keyfile": None,
                "cors_allow_origins": ["*"],
                "rate_limit_per_min": 120,
                "auth_token": None,
            },
            "models": {
                "directory": "../models/llama-cpp",
                "default_model": None,
                "auto_load_default": True,
                "max_loaded_models": 2,
                "max_cache_gb": 8,
            },
            "performance": {
                "optimize_for": "balanced",  # memory|speed|loading|balanced
                "enable_gpu": True,
                "num_threads": max(1, os.cpu_count() or 1),
                "batch_size": 128,
                "context_window": 4096,
                "low_vram": False,
            },
            "backend": {
                "type": "auto",  # auto|local|remote|stub
                "local": {
                    "n_ctx": 4096,  # Context window size
                    "n_threads": max(1, os.cpu_count() or 1),
                    "n_batch": 512,  # Batch size for prompt processing
                    "use_mmap": True,  # Use memory mapping
                    "use_mlock": False,  # Lock memory in RAM
                    "embedding": False,  # Enable embedding mode
                    "low_mem": False,  # Low memory mode
                    "verbose": False  # Verbose output
                },
                "remote": {
                    "url": "http://localhost:8000",
                    "timeout": 30,
                    "auth_token": None
                }
            },
            "observability": {
                "enable_prometheus": False,
                "prometheus_port": 9090,
                "enable_tracing": False,
            },
            "karen": {
                "integration_enabled": True,
                "endpoint": "http://localhost:8000",
                "health_timeout_s": 2,
            },
        }

        file_data = _read_json(cfg_path)
        merged = _merge(defaults, file_data)

        # env overrides
        merged["server"]["host"] = _env_override("server.host", merged["server"]["host"])
        merged["server"]["port"] = _env_override("server.port", merged["server"]["port"])
        merged["server"]["log_level"] = _env_override("server.log_level", merged["server"]["log_level"])
        merged["server"]["auth_token"] = _env_override("server.auth_token", merged["server"]["auth_token"])
        merged["models"]["directory"] = _env_override("models.directory", merged["models"]["directory"])
        merged["backend"]["type"] = _env_override("backend.type", merged["backend"]["type"])
        merged["backend"]["local"]["n_ctx"] = _env_override("backend.local.n_ctx", merged["backend"]["local"]["n_ctx"])
        merged["backend"]["local"]["n_threads"] = _env_override("backend.local.n_threads", merged["backend"]["local"]["n_threads"])
        merged["backend"]["local"]["low_mem"] = _env_override("backend.local.low_mem", merged["backend"]["local"]["low_mem"])

        return cls(config_path=cfg_path, data=merged)

    def get(self, dotted: str, default: Any = None) -> Any:
        cur: Any = self.data
        for part in dotted.split("."):
            if not isinstance(cur, dict) or part not in cur:
                return default
            cur = cur[part]
        return cur

    def save(self) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with self.config_path.open("w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

