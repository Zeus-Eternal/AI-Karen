"""
Package command for extension packaging and distribution.
"""

import argparse
import json
import shutil
import tarfile
import zipfile
from pathlib import Path
from typing import Dict, Any, List, Set

from .base import BaseCommand


class PackageCommand(BaseCommand):
    """Command to package extensions for distribution."""
    
    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser) -> None:
        """Add package command arguments."""
        parser.add_argument(
            "path",
            type=Path,
            help="Path to extension directory"
        )
        parser.add_argument(
            "--output", "-o",
            type=Path,
            help="Output file path (default: auto-generated)"
        )
        parser.add_argument(
            "--format", "-f",
            choices=["zip", "tar.gz", "tar.bz2"],
            default="zip",
            help="Package format (default: zip)"
        )
        parser.add_argument(
            "--exclude",
            action="append",
            default=[],
            help="Exclude patterns (can be used multiple times)"
        )
        parser.add_argument(
            "--include-dev",
            action="store_true",
            help="Include development files (tests, docs, etc.)"
        )
        parser.add_argument(
            "--validate",
            action="store_true",
            default=True,
            help="Validate extension before packaging"
        )
        parser.add_argument(
            "--sign",
            action="store_true",
            help="Sign the package (requires signing key)"
        )
        parser.add_argument(
            "--metadata-only",
            action="store_true",
            help="Generate only metadata files"
        )
    
    @staticmethod
    def execute(args: argparse.Namespace) -> int:
        """Execute the package command."""
        extension_path = args.path
        
        if not extension_path.exists():
            PackageCommand.print_error(f"Extension path '{extension_path}' does not exist")
            return 1
        
        if not extension_path.is_dir():
            PackageCommand.print_error(f"Extension path '{extension_path}' is not a directory")
            return 1
        
        try:
            # Validate extension if requested
            if args.validate:
                if not PackageCommand._validate_for_packaging(extension_path):
                    return 1
            
            # Load manifest
            manifest = PackageCommand._load_manifest(extension_path)
            if not manifest:
                return 1
            
            # Generate package metadata
            metadata = PackageCommand._generate_package_metadata(extension_path, manifest)
            
            if args.metadata_only:
                # Only generate metadata files
                PackageCommand._write_metadata_files(extension_path, metadata)
                PackageCommand.print_success("Package metadata generated successfully")
                return 0
            
            # Create package
            output_path = args.output or PackageCommand._generate_output_path(
                extension_path, manifest, args.format
            )
            
            PackageCommand._create_package(
                extension_path, 
                output_path, 
                args.format,
                args.exclude,
                args.include_dev,
                metadata
            )
            
            # Sign package if requested
            if args.sign:
                PackageCommand._sign_package(output_path)
            
            PackageCommand.print_success(f"Extension packaged successfully: {output_path}")
            PackageCommand._print_package_info(output_path, metadata)
            
            return 0
            
        except Exception as e:
            PackageCommand.print_error(f"Packaging failed: {e}")
            return 1
    
    @staticmethod
    def _validate_for_packaging(extension_path: Path) -> bool:
        """Validate extension is ready for packaging."""
        from .validate import ValidateCommand
        
        PackageCommand.print_info("Validating extension for packaging...")
        
        # Run validation
        results = ValidateCommand._validate_extension(extension_path, strict=False)
        
        if results["errors"]:
            PackageCommand.print_error("Extension has validation errors:")
            for error in results["errors"]:
                print(f"  • {error}")
            return False
        
        if results["warnings"]:
            PackageCommand.print_warning("Extension has validation warnings:")
            for warning in results["warnings"]:
                print(f"  • {warning}")
        
        return True
    
    @staticmethod
    def _load_manifest(extension_path: Path) -> Dict[str, Any]:
        """Load and validate extension manifest."""
        manifest_path = extension_path / "extension.json"
        
        if not manifest_path.exists():
            PackageCommand.print_error("Missing extension.json manifest file")
            return None
        
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            return manifest
        except json.JSONDecodeError as e:
            PackageCommand.print_error(f"Invalid JSON in manifest: {e}")
            return None
        except Exception as e:
            PackageCommand.print_error(f"Error reading manifest: {e}")
            return None
    
    @staticmethod
    def _generate_package_metadata(extension_path: Path, manifest: Dict[str, Any]) -> Dict[str, Any]:
        """Generate package metadata."""
        import hashlib
        import time
        from datetime import datetime
        
        # Calculate package hash
        package_hash = PackageCommand._calculate_directory_hash(extension_path)
        
        metadata = {
            "package_info": {
                "name": manifest.get("name"),
                "version": manifest.get("version"),
                "display_name": manifest.get("display_name"),
                "description": manifest.get("description"),
                "author": manifest.get("author"),
                "license": manifest.get("license"),
                "category": manifest.get("category"),
                "tags": manifest.get("tags", [])
            },
            "build_info": {
                "build_time": datetime.utcnow().isoformat() + "Z",
                "build_hash": package_hash,
                "kari_version": manifest.get("kari_min_version"),
                "api_version": manifest.get("api_version")
            },
            "capabilities": manifest.get("capabilities", {}),
            "dependencies": manifest.get("dependencies", {}),
            "permissions": manifest.get("permissions", {}),
            "resources": manifest.get("resources", {}),
            "marketplace": manifest.get("marketplace", {})
        }
        
        return metadata
    
    @staticmethod
    def _generate_output_path(extension_path: Path, manifest: Dict[str, Any], format: str) -> Path:
        """Generate output path for the package."""
        name = manifest.get("name", extension_path.name)
        version = manifest.get("version", "1.0.0")
        
        if format == "zip":
            extension = ".zip"
        elif format == "tar.gz":
            extension = ".tar.gz"
        elif format == "tar.bz2":
            extension = ".tar.bz2"
        else:
            extension = ".zip"
        
        filename = f"{name}-{version}{extension}"
        return extension_path.parent / filename
    
    @staticmethod
    def _create_package(
        extension_path: Path,
        output_path: Path,
        format: str,
        exclude_patterns: List[str],
        include_dev: bool,
        metadata: Dict[str, Any]
    ) -> None:
        """Create the package file."""
        
        # Default exclude patterns
        default_excludes = [
            "__pycache__",
            "*.pyc",
            "*.pyo",
            ".git",
            ".gitignore",
            ".DS_Store",
            "Thumbs.db",
            "*.tmp",
            "*.temp"
        ]
        
        if not include_dev:
            default_excludes.extend([
                "tests",
                "docs",
                "examples",
                "*.md",
                "*.rst",
                ".pytest_cache",
                "htmlcov",
                "coverage.xml",
                ".coverage"
            ])
        
        all_excludes = default_excludes + exclude_patterns
        
        # Write metadata file
        metadata_path = extension_path / ".package_metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        
        try:
            if format == "zip":
                PackageCommand._create_zip_package(extension_path, output_path, all_excludes)
            elif format in ["tar.gz", "tar.bz2"]:
                PackageCommand._create_tar_package(extension_path, output_path, format, all_excludes)
        finally:
            # Clean up metadata file
            if metadata_path.exists():
                metadata_path.unlink()
    
    @staticmethod
    def _create_zip_package(extension_path: Path, output_path: Path, excludes: List[str]) -> None:
        """Create a ZIP package."""
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in extension_path.rglob("*"):
                if file_path.is_file():
                    relative_path = file_path.relative_to(extension_path)
                    
                    if not PackageCommand._should_exclude(relative_path, excludes):
                        zf.write(file_path, relative_path)
    
    @staticmethod
    def _create_tar_package(extension_path: Path, output_path: Path, format: str, excludes: List[str]) -> None:
        """Create a TAR package."""
        mode = "w:gz" if format == "tar.gz" else "w:bz2"
        
        with tarfile.open(output_path, mode) as tf:
            for file_path in extension_path.rglob("*"):
                if file_path.is_file():
                    relative_path = file_path.relative_to(extension_path)
                    
                    if not PackageCommand._should_exclude(relative_path, excludes):
                        tf.add(file_path, relative_path)
    
    @staticmethod
    def _should_exclude(file_path: Path, exclude_patterns: List[str]) -> bool:
        """Check if a file should be excluded based on patterns."""
        import fnmatch
        
        path_str = str(file_path)
        
        for pattern in exclude_patterns:
            if fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(file_path.name, pattern):
                return True
            
            # Check if any parent directory matches
            for parent in file_path.parents:
                if fnmatch.fnmatch(parent.name, pattern):
                    return True
        
        return False
    
    @staticmethod
    def _calculate_directory_hash(directory: Path) -> str:
        """Calculate hash of directory contents."""
        import hashlib
        
        hash_obj = hashlib.sha256()
        
        for file_path in sorted(directory.rglob("*")):
            if file_path.is_file():
                # Add file path to hash
                hash_obj.update(str(file_path.relative_to(directory)).encode())
                
                # Add file content to hash
                try:
                    with open(file_path, "rb") as f:
                        for chunk in iter(lambda: f.read(4096), b""):
                            hash_obj.update(chunk)
                except Exception:
                    # Skip files that can't be read
                    pass
        
        return hash_obj.hexdigest()
    
    @staticmethod
    def _write_metadata_files(extension_path: Path, metadata: Dict[str, Any]) -> None:
        """Write package metadata files."""
        # Write package metadata
        metadata_path = extension_path / "package_metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        
        # Write package info
        info_path = extension_path / "PACKAGE_INFO.txt"
        with open(info_path, "w", encoding="utf-8") as f:
            f.write(f"Package: {metadata['package_info']['name']}\n")
            f.write(f"Version: {metadata['package_info']['version']}\n")
            f.write(f"Author: {metadata['package_info']['author']}\n")
            f.write(f"License: {metadata['package_info']['license']}\n")
            f.write(f"Build Time: {metadata['build_info']['build_time']}\n")
            f.write(f"Build Hash: {metadata['build_info']['build_hash']}\n")
    
    @staticmethod
    def _sign_package(package_path: Path) -> None:
        """Sign the package (placeholder for future implementation)."""
        PackageCommand.print_warning("Package signing not yet implemented")
        # TODO: Implement package signing with GPG or similar
    
    @staticmethod
    def _print_package_info(package_path: Path, metadata: Dict[str, Any]) -> None:
        """Print package information."""
        import os
        
        size = os.path.getsize(package_path)
        size_mb = size / (1024 * 1024)
        
        print(f"\n📦 Package Information:")
        print(f"   Name: {metadata['package_info']['name']}")
        print(f"   Version: {metadata['package_info']['version']}")
        print(f"   Size: {size_mb:.2f} MB")
        print(f"   Hash: {metadata['build_info']['build_hash'][:16]}...")
        print(f"   File: {package_path}")
        
        if metadata.get("capabilities"):
            caps = metadata["capabilities"]
            enabled_caps = [k for k, v in caps.items() if v]
            if enabled_caps:
                print(f"   Capabilities: {', '.join(enabled_caps)}")
        
        print(f"\n✅ Package ready for distribution!")