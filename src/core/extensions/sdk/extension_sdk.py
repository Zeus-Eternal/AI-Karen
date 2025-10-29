"""
Main Extension SDK class that provides the complete development environment.
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .development_tools import DevelopmentTools
from .templates import ExtensionTemplates
from .validator import ExtensionValidator
from .publisher import ExtensionPublisher


@dataclass
class SDKConfig:
    """SDK configuration settings."""
    workspace_path: Path
    marketplace_url: str = "https://extensions.kari.ai"
    registry_url: str = "https://registry.kari.ai"
    docs_url: str = "https://docs.kari.ai/extensions"
    community_url: str = "https://community.kari.ai"


class ExtensionSDK:
    """
    Main SDK class providing all tools needed for extension development.
    
    This class orchestrates all SDK components and provides a unified interface
    for extension developers.
    """
    
    def __init__(self, config: Optional[SDKConfig] = None):
        self.config = config or self._load_default_config()
        
        # Initialize SDK components
        self.dev_tools = DevelopmentTools(self.config)
        self.templates = ExtensionTemplates(self.config)
        self.validator = ExtensionValidator(self.config)
        self.publisher = ExtensionPublisher(self.config)
        
        # Ensure workspace exists
        self.config.workspace_path.mkdir(parents=True, exist_ok=True)
    
    def _load_default_config(self) -> SDKConfig:
        """Load default SDK configuration."""
        workspace = Path.cwd() / "kari-extensions"
        return SDKConfig(workspace_path=workspace)
    
    def create_extension(
        self, 
        name: str, 
        template: str = "basic",
        **kwargs
    ) -> Path:
        """
        Create a new extension from template.
        
        Args:
            name: Extension name
            template: Template type (basic, api, ui, automation)
            **kwargs: Additional template parameters
            
        Returns:
            Path to created extension directory
        """
        extension_path = self.config.workspace_path / name
        
        if extension_path.exists():
            raise ValueError(f"Extension '{name}' already exists at {extension_path}")
        
        # Create extension from template
        self.templates.create_from_template(
            template_name=template,
            extension_name=name,
            output_path=extension_path,
            **kwargs
        )
        
        print(f"✅ Created extension '{name}' at {extension_path}")
        print(f"📖 Next steps:")
        print(f"   cd {extension_path}")
        print(f"   kari-ext dev --watch")
        
        return extension_path
    
    def validate_extension(self, extension_path: Path) -> Dict[str, Any]:
        """
        Validate an extension for compliance and best practices.
        
        Args:
            extension_path: Path to extension directory
            
        Returns:
            Validation results
        """
        return self.validator.validate_extension(extension_path)
    
    def test_extension(self, extension_path: Path) -> Dict[str, Any]:
        """
        Run comprehensive tests on an extension.
        
        Args:
            extension_path: Path to extension directory
            
        Returns:
            Test results
        """
        return self.dev_tools.run_tests(extension_path)
    
    def package_extension(self, extension_path: Path) -> Path:
        """
        Package extension for distribution.
        
        Args:
            extension_path: Path to extension directory
            
        Returns:
            Path to packaged extension file
        """
        # Validate before packaging
        validation_result = self.validate_extension(extension_path)
        if not validation_result.get("valid", False):
            raise ValueError(f"Extension validation failed: {validation_result}")
        
        return self.publisher.package_extension(extension_path)
    
    def publish_extension(
        self, 
        extension_path: Path,
        marketplace_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Publish extension to marketplace.
        
        Args:
            extension_path: Path to extension directory
            marketplace_token: Authentication token for marketplace
            
        Returns:
            Publication results
        """
        # Package extension first
        package_path = self.package_extension(extension_path)
        
        # Publish to marketplace
        return self.publisher.publish_to_marketplace(
            package_path=package_path,
            token=marketplace_token
        )
    
    def start_dev_server(
        self, 
        extension_path: Path,
        watch: bool = True,
        port: int = 8000
    ) -> None:
        """
        Start development server for extension testing.
        
        Args:
            extension_path: Path to extension directory
            watch: Enable file watching for hot reload
            port: Development server port
        """
        self.dev_tools.start_dev_server(
            extension_path=extension_path,
            watch=watch,
            port=port
        )
    
    def get_marketplace_info(self) -> Dict[str, Any]:
        """Get information about the extension marketplace."""
        return {
            "marketplace_url": self.config.marketplace_url,
            "registry_url": self.config.registry_url,
            "docs_url": self.config.docs_url,
            "community_url": self.config.community_url,
            "sdk_version": "1.0.0"
        }
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """List available extension templates."""
        return self.templates.list_templates()
    
    def get_extension_info(self, extension_path: Path) -> Dict[str, Any]:
        """Get information about an extension."""
        manifest_path = extension_path / "extension.json"
        if not manifest_path.exists():
            raise ValueError(f"No extension manifest found at {manifest_path}")
        
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        return {
            "name": manifest.get("name"),
            "version": manifest.get("version"),
            "description": manifest.get("description"),
            "author": manifest.get("author"),
            "path": str(extension_path),
            "manifest": manifest
        }
    
    def update_extension_dependencies(self, extension_path: Path) -> None:
        """Update extension dependencies to latest versions."""
        self.dev_tools.update_dependencies(extension_path)
    
    def generate_docs(self, extension_path: Path) -> Path:
        """Generate documentation for an extension."""
        return self.dev_tools.generate_documentation(extension_path)