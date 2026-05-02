from __future__ import annotations

import os
from dataclasses import dataclass

@dataclass(slots=True)
class LoggingSettings:
    level: str = os.getenv("KARI_LOG_LEVEL", "INFO")
    format: str = os.getenv("KARI_LOG_FORMAT", "json")
    include_stack: bool = os.getenv("KARI_LOG_INCLUDE_STACK", "false").lower() == "true"
    redact_secrets: bool = os.getenv("KARI_LOG_REDACT_SECRETS", "true").lower() == "true"
    sample_debug: bool = os.getenv("KARI_LOG_SAMPLE_DEBUG", "false").lower() == "true"
    file_enabled: bool = os.getenv("KARI_LOG_FILE_ENABLED", "false").lower() == "true"
    file_path: str = os.getenv("KARI_LOG_FILE_PATH", "logs/kari-runtime.jsonl")
    console_enabled: bool = os.getenv("KARI_LOG_CONSOLE_ENABLED", "true").lower() == "true"
    audit_forwarding: bool = os.getenv("KARI_LOG_AUDIT_FORWARDING", "true").lower() == "true"
    otel_enabled: bool = os.getenv("KARI_LOG_OTEL_ENABLED", "false").lower() == "true"

_SETTINGS = LoggingSettings()

def get_logging_settings() -> LoggingSettings:
    return _SETTINGS
