"""
Plugin Marketplace and Management Service
Visual plugin discovery, installation, and configuration
"""

import os
import json
import requests
import subprocess
import shutil
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import streamlit as st


@dataclass
class PluginInfo:
    """Plugin information structure"""
    id: str
    name: str
    description: str
    version: str
    author: str
    category: str
    tags: List[str]
    dependencies: List[str]
    install_size: str
    rating: float
    downloads: int
    last_updated: datetime
    icon: str
    screenshots: List[str]
    documentation_url: str
    source_url: str
    license: str
    installed: bool = False
    enabled: bool = False
    config_required: bool = False


@dataclass
class PluginInstallation:
    """Plugin installation tracking"""
    plugin_id: str
    status: str  # 'installing', 'installed', 'failed', 'updating'
    progress: float
    message: str
    timestamp: datetime
    error_details: Optional[str] = None


class PluginMarketplaceService:
    """
    Plugin Marketplace and Management Service
    Handles plugin discovery, installation, configuration, and lifecycle
    """
    
    def __init__(self):
        self.api_url = os.getenv("KARI_API_URL", "http://localhost:8001")
        self.plugins_dir = Path("plugins")
        self.extensions_dir = Path("extensions")
        self.session = requests.Session()
        
        # Plugin registry
        self.available_plugins: List[PluginInfo] = []
        self.installed_plugins: Dict[str, PluginInfo] = {}
        self.installation_queue: List[PluginInstallation] = []
        
        # Load plugin data
        self._load_marketplace_data()
        self._scan_installed_plugins()
    
    def _load_marketplace_data(self):
        """Load available plugins from marketplace"""
        # Simulate marketplace data (would come from API in production)
        marketplace_plugins = [
            {
                "id": "ai-llm-services",
                "name": "AI LLM Services",
                "description": "Advanced LLM integration with multiple providers (OpenAI, Anthropic, Cohere)",
                "version": "2.1.0",
                "author": "AI Karen Team",
                "category": "AI Services",
                "tags": ["llm", "ai", "chat", "generation"],
                "dependencies": ["openai>=1.0.0", "anthropic>=0.8.0"],
                "install_size": "15.2 MB",
                "rating": 4.8,
                "downloads": 12500,
                "last_updated": datetime(2024, 7, 15),
                "icon": "🤖",
                "screenshots": ["llm_config.png", "chat_interface.png"],
                "documentation_url": "https://docs.ai-karen.com/plugins/llm-services",
                "source_url": "https://github.com/ai-karen/plugin-llm-services",
                "license": "MIT",
                "config_required": True
            },
            {
                "id": "automation-workflows",
                "name": "Automation Workflows",
                "description": "Visual workflow builder with drag-and-drop interface for task automation",
                "version": "1.5.2",
                "author": "Automation Labs",
                "category": "Automation",
                "tags": ["workflow", "automation", "tasks", "scheduling"],
                "dependencies": ["celery>=5.0.0", "redis>=4.0.0"],
                "install_size": "8.7 MB",
                "rating": 4.6,
                "downloads": 8900,
                "last_updated": datetime(2024, 7, 10),
                "icon": "⚡",
                "screenshots": ["workflow_builder.png", "task_monitor.png"],
                "documentation_url": "https://docs.ai-karen.com/plugins/automation",
                "source_url": "https://github.com/ai-karen/plugin-automation",
                "license": "Apache-2.0",
                "config_required": True
            },
            {
                "id": "data-analytics",
                "name": "Advanced Data Analytics",
                "description": "Comprehensive data analysis tools with ML capabilities and visualization",
                "version": "3.0.1",
                "author": "DataViz Pro",
                "category": "Analytics",
                "tags": ["analytics", "data", "ml", "visualization"],
                "dependencies": ["pandas>=2.0.0", "scikit-learn>=1.3.0", "plotly>=5.0.0"],
                "install_size": "45.8 MB",
                "rating": 4.9,
                "downloads": 15600,
                "last_updated": datetime(2024, 7, 18),
                "icon": "📊",
                "screenshots": ["analytics_dashboard.png", "ml_models.png"],
                "documentation_url": "https://docs.ai-karen.com/plugins/analytics",
                "source_url": "https://github.com/ai-karen/plugin-analytics",
                "license": "MIT",
                "config_required": False
            },
            {
                "id": "security-scanner",
                "name": "Security Scanner",
                "description": "Automated security scanning and vulnerability assessment tools",
                "version": "1.2.3",
                "author": "SecureAI",
                "category": "Security",
                "tags": ["security", "scanning", "vulnerability", "audit"],
                "dependencies": ["nmap-python>=1.5.0", "requests>=2.28.0"],
                "install_size": "12.4 MB",
                "rating": 4.7,
                "downloads": 6700,
                "last_updated": datetime(2024, 7, 12),
                "icon": "🛡️",
                "screenshots": ["security_scan.png", "vulnerability_report.png"],
                "documentation_url": "https://docs.ai-karen.com/plugins/security",
                "source_url": "https://github.com/ai-karen/plugin-security",
                "license": "GPL-3.0",
                "config_required": True
            },
            {
                "id": "integration-hub",
                "name": "Integration Hub",
                "description": "Connect with external services: Slack, Discord, Telegram, webhooks",
                "version": "2.3.0",
                "author": "Integration Team",
                "category": "Integrations",
                "tags": ["integration", "api", "webhooks", "notifications"],
                "dependencies": ["slack-sdk>=3.0.0", "discord.py>=2.0.0"],
                "install_size": "18.9 MB",
                "rating": 4.5,
                "downloads": 9800,
                "last_updated": datetime(2024, 7, 16),
                "icon": "🔗",
                "screenshots": ["integrations_list.png", "webhook_config.png"],
                "documentation_url": "https://docs.ai-karen.com/plugins/integrations",
                "source_url": "https://github.com/ai-karen/plugin-integrations",
                "license": "MIT",
                "config_required": True
            },
            {
                "id": "voice-assistant",
                "name": "Voice Assistant",
                "description": "Speech-to-text and text-to-speech capabilities with voice commands",
                "version": "1.8.0",
                "author": "Voice Tech",
                "category": "AI Services",
                "tags": ["voice", "speech", "tts", "stt", "commands"],
                "dependencies": ["speechrecognition>=3.10.0", "pyttsx3>=2.90"],
                "install_size": "32.1 MB",
                "rating": 4.4,
                "downloads": 7200,
                "last_updated": datetime(2024, 7, 8),
                "icon": "🎤",
                "screenshots": ["voice_config.png", "command_setup.png"],
                "documentation_url": "https://docs.ai-karen.com/plugins/voice",
                "source_url": "https://github.com/ai-karen/plugin-voice",
                "license": "MIT",
                "config_required": True
            }
        ]
        
        self.available_plugins = [PluginInfo(**plugin) for plugin in marketplace_plugins]
    
    def _scan_installed_plugins(self):
        """Scan for installed plugins"""
        # Scan plugins directory
        if self.plugins_dir.exists():
            for plugin_dir in self.plugins_dir.iterdir():
                if plugin_dir.is_dir() and (plugin_dir / "plugin_manifest.json").exists():
                    try:
                        with open(plugin_dir / "plugin_manifest.json") as f:
                            manifest = json.load(f)
                        
                        plugin_info = PluginInfo(
                            id=manifest.get("id", plugin_dir.name),
                            name=manifest.get("name", plugin_dir.name),
                            description=manifest.get("description", ""),
                            version=manifest.get("version", "1.0.0"),
                            author=manifest.get("author", "Unknown"),
                            category=manifest.get("category", "Other"),
                            tags=manifest.get("tags", []),
                            dependencies=manifest.get("dependencies", []),
                            install_size="Unknown",
                            rating=0.0,
                            downloads=0,
                            last_updated=datetime.now(),
                            icon=manifest.get("icon", "🧩"),
                            screenshots=[],
                            documentation_url="",
                            source_url="",
                            license=manifest.get("license", "Unknown"),
                            installed=True,
                            enabled=manifest.get("enabled", False)
                        )
                        
                        self.installed_plugins[plugin_info.id] = plugin_info
                        
                        # Update marketplace entry if exists
                        for i, marketplace_plugin in enumerate(self.available_plugins):
                            if marketplace_plugin.id == plugin_info.id:
                                self.available_plugins[i].installed = True
                                self.available_plugins[i].enabled = plugin_info.enabled
                                break
                                
                    except Exception as e:
                        st.error(f"Error loading plugin {plugin_dir.name}: {e}")
    
    def get_available_plugins(self, category: Optional[str] = None, 
                            search_query: Optional[str] = None) -> List[PluginInfo]:
        """Get available plugins with optional filtering"""
        plugins = self.available_plugins.copy()
        
        # Filter by category
        if category and category != "All":
            plugins = [p for p in plugins if p.category == category]
        
        # Filter by search query
        if search_query:
            query_lower = search_query.lower()
            plugins = [
                p for p in plugins 
                if (query_lower in p.name.lower() or 
                    query_lower in p.description.lower() or
                    any(query_lower in tag.lower() for tag in p.tags))
            ]
        
        return plugins
    
    def get_plugin_categories(self) -> List[str]:
        """Get all available plugin categories"""
        categories = set(plugin.category for plugin in self.available_plugins)
        return ["All"] + sorted(list(categories))
    
    def install_plugin(self, plugin_id: str) -> PluginInstallation:
        """Install a plugin"""
        plugin = next((p for p in self.available_plugins if p.id == plugin_id), None)
        if not plugin:
            raise ValueError(f"Plugin {plugin_id} not found")
        
        installation = PluginInstallation(
            plugin_id=plugin_id,
            status="installing",
            progress=0.0,
            message="Starting installation...",
            timestamp=datetime.now()
        )
        
        self.installation_queue.append(installation)
        
        try:
            # Simulate installation process
            installation.progress = 0.2
            installation.message = "Downloading plugin..."
            
            # Check dependencies
            installation.progress = 0.4
            installation.message = "Checking dependencies..."
            
            # Install dependencies
            installation.progress = 0.6
            installation.message = "Installing dependencies..."
            
            # Configure plugin
            installation.progress = 0.8
            installation.message = "Configuring plugin..."
            
            # Complete installation
            installation.progress = 1.0
            installation.status = "installed"
            installation.message = "Installation completed successfully!"
            
            # Update plugin status
            plugin.installed = True
            if plugin_id not in self.installed_plugins:
                self.installed_plugins[plugin_id] = plugin
            
        except Exception as e:
            installation.status = "failed"
            installation.error_details = str(e)
            installation.message = f"Installation failed: {e}"
        
        return installation
    
    def uninstall_plugin(self, plugin_id: str) -> bool:
        """Uninstall a plugin"""
        try:
            if plugin_id in self.installed_plugins:
                # Remove from installed plugins
                del self.installed_plugins[plugin_id]
                
                # Update marketplace entry
                for plugin in self.available_plugins:
                    if plugin.id == plugin_id:
                        plugin.installed = False
                        plugin.enabled = False
                        break
                
                return True
        except Exception as e:
            st.error(f"Error uninstalling plugin: {e}")
        
        return False
    
    def enable_plugin(self, plugin_id: str) -> bool:
        """Enable an installed plugin"""
        if plugin_id in self.installed_plugins:
            self.installed_plugins[plugin_id].enabled = True
            
            # Update marketplace entry
            for plugin in self.available_plugins:
                if plugin.id == plugin_id:
                    plugin.enabled = True
                    break
            
            return True
        return False
    
    def disable_plugin(self, plugin_id: str) -> bool:
        """Disable an installed plugin"""
        if plugin_id in self.installed_plugins:
            self.installed_plugins[plugin_id].enabled = False
            
            # Update marketplace entry
            for plugin in self.available_plugins:
                if plugin.id == plugin_id:
                    plugin.enabled = False
                    break
            
            return True
        return False
    
    def get_plugin_config_schema(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Get plugin configuration schema"""
        # This would load the actual config schema from the plugin
        schemas = {
            "ai-llm-services": {
                "openai_api_key": {"type": "string", "required": True, "description": "OpenAI API Key"},
                "anthropic_api_key": {"type": "string", "required": False, "description": "Anthropic API Key"},
                "default_model": {"type": "select", "options": ["gpt-4", "gpt-3.5-turbo", "claude-3"], "default": "gpt-3.5-turbo"},
                "max_tokens": {"type": "number", "default": 2048, "min": 1, "max": 8192}
            },
            "automation-workflows": {
                "redis_url": {"type": "string", "required": True, "description": "Redis connection URL"},
                "max_concurrent_tasks": {"type": "number", "default": 10, "min": 1, "max": 100},
                "enable_scheduling": {"type": "boolean", "default": True}
            },
            "security-scanner": {
                "scan_timeout": {"type": "number", "default": 300, "description": "Scan timeout in seconds"},
                "enable_deep_scan": {"type": "boolean", "default": False},
                "notification_webhook": {"type": "string", "required": False}
            }
        }
        
        return schemas.get(plugin_id)
    
    def save_plugin_config(self, plugin_id: str, config: Dict[str, Any]) -> bool:
        """Save plugin configuration"""
        try:
            # This would save to the actual plugin config file
            config_path = self.plugins_dir / plugin_id / "config.json"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            return True
        except Exception as e:
            st.error(f"Error saving plugin config: {e}")
            return False
    
    def get_installation_status(self, plugin_id: str) -> Optional[PluginInstallation]:
        """Get installation status for a plugin"""
        return next((inst for inst in self.installation_queue if inst.plugin_id == plugin_id), None)
    
    def get_plugin_metrics(self) -> Dict[str, Any]:
        """Get plugin system metrics"""
        return {
            "total_available": len(self.available_plugins),
            "total_installed": len(self.installed_plugins),
            "total_enabled": sum(1 for p in self.installed_plugins.values() if p.enabled),
            "categories": len(set(p.category for p in self.available_plugins)),
            "pending_installations": len([i for i in self.installation_queue if i.status == "installing"]),
            "failed_installations": len([i for i in self.installation_queue if i.status == "failed"])
        }


# Create singleton instance
plugin_service = PluginMarketplaceService()