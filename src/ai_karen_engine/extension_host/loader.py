"""
Extension Loader - Discovers and loads extensions from the extensions directory.

This module handles the discovery, validation, and loading of extensions from the
unified extensions directory structure.
"""

import os
import importlib.util
import sys
from pathlib import Path
from typing import Dict, List, Optional, Type, Any
import json
import logging

from .base import ExtensionBase, ExtensionManifest
from .config import ExtensionConfigManager
from .errors import (
    ExtensionLoadError, 
    ExtensionValidationError, 
    ExtensionManifestError,
    ExtensionNotFoundError
)
from .utils.validation import validate_manifest

logger = logging.getLogger(__name__)


class ExtensionLoader:
    """
    Discovers and loads extensions from the extensions directory.
    
    Handles:
    - Extension discovery in the extensions directory
    - Manifest validation
    - Dynamic import of extension modules
    - Instantiation of extension classes
    - Error isolation during loading
    """
    
    def __init__(self, extensions_dir: str = "src/extensions", config_manager: Optional[ExtensionConfigManager] = None):
        """
        Initialize the extension loader.
        
        Args:
            extensions_dir: Path to the extensions directory
            config_manager: Optional configuration manager for extension settings
        """
        self.extensions_dir = Path(extensions_dir)
        self.config_manager = config_manager or ExtensionConfigManager()
        self._loaded_extensions: Dict[str, ExtensionBase] = {}
        
        # Ensure the extensions directory exists
        if not self.extensions_dir.exists():
            logger.warning(f"Extensions directory {self.extensions_dir} does not exist, creating it")
            self.extensions_dir.mkdir(parents=True, exist_ok=True)
    
    def discover_extensions(self) -> List[str]:
        """
        Discover all extension directories in the extensions directory.
        
        Returns:
            List of extension directory names
        """
        if not self.extensions_dir.exists():
            logger.warning(f"Extensions directory {self.extensions_dir} does not exist")
            return []
        
        extension_dirs = []
        
        for item in self.extensions_dir.iterdir():
            if item.is_dir() and not item.name.startswith('_'):
                # Check if it has a manifest file
                manifest_file = item / "extension_manifest.json"
                if manifest_file.exists():
                    extension_dirs.append(item.name)
                else:
                    logger.warning(f"Extension directory {item.name} has no manifest file, skipping")
        
        logger.info(f"Discovered {len(extension_dirs)} extensions: {extension_dirs}")
        return extension_dirs
    
    def load_manifest(self, extension_name: str) -> ExtensionManifest:
        """
        Load and validate the manifest for an extension.
        
        Args:
            extension_name: Name of the extension
            
        Returns:
            ExtensionManifest object
            
        Raises:
            ExtensionNotFoundError: If extension directory doesn't exist
            ExtensionManifestError: If manifest file is missing or invalid
            ExtensionValidationError: If manifest validation fails
        """
        extension_dir = self.extensions_dir / extension_name
        
        if not extension_dir.exists():
            raise ExtensionNotFoundError(f"Extension directory {extension_dir} does not exist")
        
        manifest_file = extension_dir / "extension_manifest.json"
        
        if not manifest_file.exists():
            raise ExtensionManifestError(f"Manifest file not found for extension {extension_name}")
        
        try:
            with open(manifest_file, 'r', encoding='utf-8') as f:
                manifest_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ExtensionManifestError(f"Invalid JSON in manifest file for extension {extension_name}: {e}")
        except Exception as e:
            raise ExtensionManifestError(f"Error reading manifest file for extension {extension_name}: {e}")
        
        # Validate the manifest
        try:
            validate_manifest(manifest_data)
        except ExtensionValidationError as e:
            raise ExtensionValidationError(f"Manifest validation failed for extension {extension_name}: {e}")
        
        # Create ExtensionManifest object
        try:
            manifest = ExtensionManifest(**manifest_data)
        except Exception as e:
            raise ExtensionManifestError(f"Error creating ExtensionManifest object for {extension_name}: {e}")
        
        return manifest
    
    def load_extension(self, extension_name: str) -> ExtensionBase:
        """
        Load an extension by name.
        
        Args:
            extension_name: Name of the extension to load
            
        Returns:
            ExtensionBase instance
            
        Raises:
            ExtensionNotFoundError: If extension directory doesn't exist
            ExtensionManifestError: If manifest file is missing or invalid
            ExtensionValidationError: If manifest validation fails
            ExtensionLoadError: If extension module or class cannot be loaded
        """
        if extension_name in self._loaded_extensions:
            logger.debug(f"Extension {extension_name} already loaded, returning cached instance")
            return self._loaded_extensions[extension_name]
        
        # Load and validate manifest
        manifest = self.load_manifest(extension_name)
        
        # Load the extension module
        extension_dir = self.extensions_dir / extension_name
        handler_file = extension_dir / "handler.py"
        
        if not handler_file.exists():
            raise ExtensionLoadError(f"Handler file not found for extension {extension_name}")
        
        try:
            # Add the extension directory to Python path
            sys.path.insert(0, str(extension_dir))
            
            # Load the module
            spec = importlib.util.spec_from_file_location(f"{extension_name}_handler", handler_file)
            if spec is None or spec.loader is None:
                raise ExtensionLoadError(f"Could not load module spec for extension {extension_name}")
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Get the extension class
            entrypoint_parts = manifest.entrypoint.split(':')
            if len(entrypoint_parts) != 2:
                raise ExtensionLoadError(f"Invalid entrypoint format: {manifest.entrypoint}")
            
            module_name, class_name = entrypoint_parts
            
            if module_name != "handler":
                raise ExtensionLoadError(f"Entrypoint module must be 'handler', got '{module_name}'")
            
            if not hasattr(module, class_name):
                raise ExtensionLoadError(f"Class {class_name} not found in extension module")
            
            extension_class = getattr(module, class_name)
            
            # Verify it's a subclass of ExtensionBase
            if not issubclass(extension_class, ExtensionBase):
                raise ExtensionLoadError(f"Extension class {class_name} does not inherit from ExtensionBase")
            
            # Get extension-specific configuration
            extension_config = self.config_manager.get_extension_config(extension_name)
            
            # Create the extension instance
            extension_instance = extension_class(manifest, extension_config)
            
            # Store the loaded extension
            self._loaded_extensions[extension_name] = extension_instance
            
            logger.info(f"Successfully loaded extension {extension_name}")
            return extension_instance
            
        except Exception as e:
            if isinstance(e, ExtensionLoadError):
                raise
            raise ExtensionLoadError(f"Error loading extension {extension_name}: {e}")
        finally:
            # Remove the extension directory from Python path
            if str(extension_dir) in sys.path:
                sys.path.remove(str(extension_dir))
    
    def load_all_extensions(self) -> Dict[str, ExtensionBase]:
        """
        Load all discovered extensions.
        
        Returns:
            Dictionary mapping extension names to ExtensionBase instances
            
        Raises:
            ExtensionLoadError: If any extension fails to load
        """
        extensions = {}
        extension_names = self.discover_extensions()
        
        for extension_name in extension_names:
            try:
                extension = self.load_extension(extension_name)
                extensions[extension_name] = extension
            except Exception as e:
                logger.error(f"Failed to load extension {extension_name}: {e}")
                # Continue loading other extensions
        
        return extensions
    
    def reload_extension(self, extension_name: str) -> ExtensionBase:
        """
        Reload an extension that was previously loaded.
        
        Args:
            extension_name: Name of the extension to reload
            
        Returns:
            ExtensionBase instance
            
        Raises:
            ExtensionLoadError: If extension cannot be reloaded
        """
        if extension_name in self._loaded_extensions:
            del self._loaded_extensions[extension_name]
        
        return self.load_extension(extension_name)
    
    def get_loaded_extensions(self) -> Dict[str, ExtensionBase]:
        """
        Get all currently loaded extensions.
        
        Returns:
            Dictionary mapping extension names to ExtensionBase instances
        """
        return self._loaded_extensions.copy()
    
    def is_extension_loaded(self, extension_name: str) -> bool:
        """
        Check if an extension is currently loaded.
        
        Args:
            extension_name: Name of the extension to check
            
        Returns:
            True if extension is loaded, False otherwise
        """
        return extension_name in self._loaded_extensions