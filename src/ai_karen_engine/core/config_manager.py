"""
Configuration Management Bridge for AI Karen Engine.
Redirects all requests to the consolidated src/ai_karen_engine/config/config_manager.py.
"""

from ai_karen_engine.config.config_manager import (
    AIKarenConfig,
    LLMConfig,
    DatabaseConfig,
    RedisConfig,
    VectorDBConfig,
    ServiceConfig,
    SecurityConfig,
    MonitoringConfig,
    WebUIConfig,
    Environment,
    get_config,
    load_config,
    save_config,
    update_config,
    get_config_value,
    set_config_value,
    reset_config,
    backup_config,
    restore_config,
    register_observer,
    get_llm_config,
    get_default_model,
    get_default_provider,
    get_provider_defaults,
    get_fallback_chain,
    get_task_assignment,
    config_manager as _config_manager,
    reload as reload_config,
)

# Backward compatibility aliases
get_config_manager = lambda: _config_manager
ConfigManager = _config_manager.__class__
get_config = get_config
get_llm_config = get_llm_config

# Re-exporting for those who still import from core.config_manager
__all__ = [
    "AIKarenConfig", "LLMConfig", "DatabaseConfig", "RedisConfig", 
    "VectorDBConfig", "ServiceConfig", "SecurityConfig", "MonitoringConfig", 
    "WebUIConfig", "Environment", "get_config", "load_config", "save_config", 
    "update_config", "get_config_value", "set_config_value", "reset_config", 
    "backup_config", "restore_config", "register_observer", "get_llm_config", 
    "get_default_model", "get_default_provider", "get_provider_defaults", 
    "get_fallback_chain", "get_task_assignment", "get_config_manager", "ConfigManager",
    "reload_config"
]
