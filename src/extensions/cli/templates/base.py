"""
Base template class for extension scaffolding.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any


class BaseTemplate(ABC):
    """Base class for extension templates."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Template name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Template description."""
        pass
    
    @abstractmethod
    def get_manifest_template(self, extension_name: str, author: str, description: str = None) -> Dict[str, Any]:
        """Get manifest template for this extension type."""
        pass
    
    @abstractmethod
    def get_file_templates(self, extension_name: str) -> Dict[str, str]:
        """Get file templates for this extension type."""
        pass
    
    @abstractmethod
    def get_directory_structure(self) -> Dict[str, Any]:
        """Get directory structure for this extension type."""
        pass
    
    def create_extension(self, extension_path: Path, extension_name: str, author: str, description: str = None) -> None:
        """Create extension from template."""
        # Create directory structure
        structure = self.get_directory_structure()
        self._create_structure(extension_path, structure)
        
        # Create manifest
        manifest = self.get_manifest_template(extension_name, author, description)
        self._write_json_file(extension_path / "extension.json", manifest)
        
        # Create files from templates
        file_templates = self.get_file_templates(extension_name)
        for file_path, content in file_templates.items():
            full_path = extension_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
    
    def _create_structure(self, base_path: Path, structure: Dict[str, Any]) -> None:
        """Create directory structure."""
        for name, content in structure.items():
            path = base_path / name
            if isinstance(content, dict):
                path.mkdir(parents=True, exist_ok=True)
                self._create_structure(path, content)
            else:
                path.mkdir(parents=True, exist_ok=True)
    
    def _write_json_file(self, file_path: Path, data: Dict[str, Any]) -> None:
        """Write JSON data to file."""
        import json
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    
    def _get_class_name(self, extension_name: str) -> str:
        """Convert extension name to class name."""
        return "".join(word.capitalize() for word in extension_name.split("-"))
    
    def _get_display_name(self, extension_name: str) -> str:
        """Convert extension name to display name."""
        return extension_name.replace("-", " ").title()