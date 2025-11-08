"""
Extension publisher for packaging and marketplace distribution.
"""

import os
import json
import tarfile
import hashlib
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import tempfile
import shutil


class ExtensionPublisher:
    """Handles extension packaging and marketplace publishing."""
    
    def __init__(self, config):
        self.config = config
        self.marketplace_url = config.marketplace_url
        self.registry_url = config.registry_url
    
    def package_extension(self, extension_path: Path) -> Path:
        """
        Package extension for distribution.
        
        Args:
            extension_path: Path to extension directory
            
        Returns:
            Path to packaged extension file
        """
        # Load manifest
        manifest_path = extension_path / "extension.json"
        if not manifest_path.exists():
            raise ValueError("extension.json not found")
        
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        extension_name = manifest["name"]
        version = manifest["version"]
        
        # Create package filename
        package_name = f"{extension_name}-{version}.kext"
        package_path = extension_path.parent / package_name
        
        # Create package
        self._create_package(extension_path, package_path, manifest)
        
        print(f"📦 Extension packaged: {package_path}")
        return package_path
    
    def _create_package(self, extension_path: Path, package_path: Path, manifest: Dict[str, Any]) -> None:
        """Create extension package file."""
        with tarfile.open(package_path, "w:gz") as tar:
            # Add all extension files
            for item in extension_path.rglob("*"):
                if item.is_file() and not self._should_exclude_file(item, extension_path):
                    arcname = item.relative_to(extension_path)
                    tar.add(item, arcname=arcname)
            
            # Add package metadata
            metadata = self._create_package_metadata(extension_path, manifest)
            metadata_json = json.dumps(metadata, indent=2)
            
            # Create temporary metadata file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                f.write(metadata_json)
                temp_metadata_path = f.name
            
            try:
                tar.add(temp_metadata_path, arcname=".kext-metadata.json")
            finally:
                os.unlink(temp_metadata_path)
    
    def _should_exclude_file(self, file_path: Path, extension_path: Path) -> bool:
        """Check if file should be excluded from package."""
        relative_path = file_path.relative_to(extension_path)
        
        # Exclude patterns
        exclude_patterns = [
            "__pycache__",
            "*.pyc",
            "*.pyo",
            ".git",
            ".gitignore",
            "node_modules",
            ".env",
            "*.log",
            "test-results.json",
            "coverage.json",
            ".pytest_cache",
            "*.kext"  # Don't include other packages
        ]
        
        for pattern in exclude_patterns:
            if pattern in str(relative_path) or relative_path.match(pattern):
                return True
        
        return False
    
    def _create_package_metadata(self, extension_path: Path, manifest: Dict[str, Any]) -> Dict[str, Any]:
        """Create package metadata."""
        # Calculate package hash
        package_hash = self._calculate_directory_hash(extension_path)
        
        # Get file list
        files = []
        for item in extension_path.rglob("*"):
            if item.is_file() and not self._should_exclude_file(item, extension_path):
                relative_path = item.relative_to(extension_path)
                files.append({
                    "path": str(relative_path),
                    "size": item.stat().st_size,
                    "hash": self._calculate_file_hash(item)
                })
        
        return {
            "package_version": "1.0",
            "created_at": datetime.utcnow().isoformat(),
            "extension": manifest,
            "package_hash": package_hash,
            "files": files,
            "total_size": sum(f["size"] for f in files),
            "file_count": len(files)
        }
    
    def _calculate_directory_hash(self, directory: Path) -> str:
        """Calculate hash of directory contents."""
        hasher = hashlib.sha256()
        
        for item in sorted(directory.rglob("*")):
            if item.is_file() and not self._should_exclude_file(item, directory):
                hasher.update(str(item.relative_to(directory)).encode())
                hasher.update(self._calculate_file_hash(item).encode())
        
        return hasher.hexdigest()
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate hash of a single file."""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def publish_to_marketplace(
        self, 
        package_path: Path,
        token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Publish extension package to marketplace.
        
        Args:
            package_path: Path to packaged extension
            token: Authentication token for marketplace
            
        Returns:
            Publication results
        """
        if not token:
            token = os.getenv("KARI_MARKETPLACE_TOKEN")
            if not token:
                raise ValueError("Marketplace token required. Set KARI_MARKETPLACE_TOKEN or pass token parameter")
        
        # Extract package metadata
        metadata = self._extract_package_metadata(package_path)
        extension_name = metadata["extension"]["name"]
        version = metadata["extension"]["version"]
        
        print(f"🚀 Publishing {extension_name} v{version} to marketplace...")
        
        try:
            # Upload package
            upload_result = self._upload_package(package_path, token)
            
            # Register in marketplace
            registration_result = self._register_extension(metadata, token)
            
            result = {
                "success": True,
                "extension_name": extension_name,
                "version": version,
                "package_url": upload_result.get("url"),
                "marketplace_url": f"{self.marketplace_url}/extensions/{extension_name}",
                "published_at": datetime.utcnow().isoformat()
            }
            
            print(f"✅ Extension published successfully!")
            print(f"📍 Marketplace URL: {result['marketplace_url']}")
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "extension_name": extension_name,
                "version": version
            }
    
    def _extract_package_metadata(self, package_path: Path) -> Dict[str, Any]:
        """Extract metadata from package file."""
        with tarfile.open(package_path, "r:gz") as tar:
            try:
                metadata_file = tar.extractfile(".kext-metadata.json")
                if metadata_file:
                    return json.loads(metadata_file.read().decode())
                else:
                    raise ValueError("Package metadata not found")
            except KeyError:
                raise ValueError("Invalid package format - metadata missing")
    
    def _upload_package(self, package_path: Path, token: str) -> Dict[str, Any]:
        """Upload package file to registry."""
        upload_url = f"{self.registry_url}/upload"
        
        with open(package_path, 'rb') as f:
            files = {'package': f}
            headers = {'Authorization': f'Bearer {token}'}
            
            response = requests.post(upload_url, files=files, headers=headers)
            response.raise_for_status()
            
            return response.json()
    
    def _register_extension(self, metadata: Dict[str, Any], token: str) -> Dict[str, Any]:
        """Register extension in marketplace."""
        register_url = f"{self.marketplace_url}/api/extensions"
        
        extension_data = {
            "manifest": metadata["extension"],
            "package_metadata": {
                "package_hash": metadata["package_hash"],
                "total_size": metadata["total_size"],
                "file_count": metadata["file_count"]
            }
        }
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(register_url, json=extension_data, headers=headers)
        response.raise_for_status()
        
        return response.json()
    
    def check_marketplace_status(self, extension_name: str, token: Optional[str] = None) -> Dict[str, Any]:
        """Check extension status in marketplace."""
        if not token:
            token = os.getenv("KARI_MARKETPLACE_TOKEN")
        
        status_url = f"{self.marketplace_url}/api/extensions/{extension_name}/status"
        headers = {'Authorization': f'Bearer {token}'} if token else {}
        
        try:
            response = requests.get(status_url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e), "available": False}
    
    def update_extension_metadata(
        self, 
        extension_name: str, 
        metadata: Dict[str, Any],
        token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update extension metadata in marketplace."""
        if not token:
            token = os.getenv("KARI_MARKETPLACE_TOKEN")
            if not token:
                raise ValueError("Marketplace token required")
        
        update_url = f"{self.marketplace_url}/api/extensions/{extension_name}"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.patch(update_url, json=metadata, headers=headers)
        response.raise_for_status()
        
        return response.json()
    
    def unpublish_extension(
        self, 
        extension_name: str, 
        version: Optional[str] = None,
        token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Unpublish extension from marketplace."""
        if not token:
            token = os.getenv("KARI_MARKETPLACE_TOKEN")
            if not token:
                raise ValueError("Marketplace token required")
        
        url = f"{self.marketplace_url}/api/extensions/{extension_name}"
        if version:
            url += f"/versions/{version}"
        
        headers = {'Authorization': f'Bearer {token}'}
        
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        
        return response.json()