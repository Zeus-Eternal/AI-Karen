#!/usr/bin/env python3
"""
Documentation Analysis and Validation Utilities

This script analyzes the current codebase and extracts accurate system information
to validate README files against the actual implementation.
"""

import os
import json
import re
import ast
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import importlib.util

try:
    import toml
except ImportError:
    toml = None

try:
    import yaml
except ImportError:
    yaml = None


@dataclass
class SystemInfo:
    """Container for extracted system information"""
    python_dependencies: Dict[str, str]
    node_dependencies: Dict[str, Dict[str, str]]  # UI -> dependencies
    rust_dependencies: Dict[str, str]
    ui_components: List[str]
    database_services: List[str]
    api_endpoints: List[str]
    plugin_structure: Dict[str, Any]
    extension_structure: Dict[str, Any]
    docker_services: List[str]
    architecture_components: List[str]


class CodebaseAnalyzer:
    """Analyzes the current codebase to extract accurate system information"""
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path).resolve()
        
    def analyze_python_dependencies(self) -> Dict[str, str]:
        """Extract Python dependencies from requirements.txt and pyproject.toml"""
        dependencies = {}
        
        # Parse requirements.txt
        req_file = self.root_path / "requirements.txt"
        if req_file.exists():
            with open(req_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Handle version specifications
                        if '==' in line:
                            name, version = line.split('==', 1)
                            dependencies[name.strip()] = version.strip()
                        elif '>=' in line:
                            name, version = line.split('>=', 1)
                            dependencies[name.strip()] = f">={version.strip()}"
                        else:
                            dependencies[line.strip()] = "latest"
        
        # Parse pyproject.toml if exists
        pyproject_file = self.root_path / "pyproject.toml"
        if pyproject_file.exists():
            try:
                with open(pyproject_file, 'r') as f:
                    pyproject_data = toml.load(f)
                    
                # Extract dependencies from pyproject.toml
                if 'project' in pyproject_data and 'dependencies' in pyproject_data['project']:
                    for dep in pyproject_data['project']['dependencies']:
                        if '==' in dep:
                            name, version = dep.split('==', 1)
                            dependencies[name.strip()] = version.strip()
                        else:
                            dependencies[dep.strip()] = "latest"
            except Exception as e:
                print(f"Warning: Could not parse pyproject.toml: {e}")
        
        return dependencies
    
    def analyze_node_dependencies(self) -> Dict[str, Dict[str, str]]:
        """Extract Node.js dependencies from package.json files"""
        node_deps = {}
        
        # Find all package.json files
        for package_json in self.root_path.rglob("package.json"):
            try:
                with open(package_json, 'r') as f:
                    data = json.load(f)
                
                # Get relative path for identification
                rel_path = package_json.parent.relative_to(self.root_path)
                ui_name = str(rel_path)
                
                deps = {}
                if 'dependencies' in data:
                    deps.update(data['dependencies'])
                if 'devDependencies' in data:
                    deps.update(data['devDependencies'])
                
                if deps:
                    node_deps[ui_name] = deps
                    
            except Exception as e:
                print(f"Warning: Could not parse {package_json}: {e}")
        
        return node_deps
    
    def analyze_rust_dependencies(self) -> Dict[str, str]:
        """Extract Rust dependencies from Cargo.toml files"""
        rust_deps = {}
        
        for cargo_toml in self.root_path.rglob("Cargo.toml"):
            try:
                with open(cargo_toml, 'r') as f:
                    data = toml.load(f)
                
                if 'dependencies' in data:
                    rust_deps.update(data['dependencies'])
                    
            except Exception as e:
                print(f"Warning: Could not parse {cargo_toml}: {e}")
        
        return rust_deps
    
    def analyze_ui_components(self) -> List[str]:
        """Identify UI components and launchers"""
        ui_components = []
        
        ui_launchers_path = self.root_path / "ui_launchers"
        if ui_launchers_path.exists():
            for item in ui_launchers_path.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    ui_components.append(item.name)
        
        return ui_components
    
    def analyze_database_services(self) -> List[str]:
        """Identify database services from docker-compose files"""
        services = []
        
        # Check docker-compose files
        for compose_file in self.root_path.rglob("docker-compose*.yml"):
            try:
                if yaml is None:
                    print("Warning: PyYAML not installed, skipping docker-compose analysis")
                    continue
                with open(compose_file, 'r') as f:
                    data = yaml.safe_load(f)
                
                if 'services' in data:
                    for service_name, service_config in data['services'].items():
                        if 'image' in service_config:
                            image = service_config['image']
                            # Identify database services by image name
                            if any(db in image.lower() for db in ['postgres', 'redis', 'milvus', 'elasticsearch', 'duckdb']):
                                services.append(service_name)
                                
            except Exception as e:
                print(f"Warning: Could not parse {compose_file}: {e}")
        
        return list(set(services))
    
    def analyze_api_endpoints(self) -> List[str]:
        """Extract API endpoints from FastAPI application"""
        endpoints = []
        
        # Look for FastAPI route definitions
        for py_file in self.root_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find FastAPI route decorators
                route_patterns = [
                    r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
                    r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
                ]
                
                for pattern in route_patterns:
                    matches = re.findall(pattern, content)
                    for method, path in matches:
                        endpoints.append(f"{method.upper()} {path}")
                        
            except Exception as e:
                continue  # Skip files that can't be read
        
        return list(set(endpoints))
    
    def analyze_plugin_structure(self) -> Dict[str, Any]:
        """Analyze plugin system structure"""
        plugin_info = {
            "plugin_directories": [],
            "example_plugins": [],
            "plugin_manifests": []
        }
        
        # Find plugin directories
        plugin_paths = [
            self.root_path / "src" / "ai_karen_engine" / "plugins",
            self.root_path / "plugin_marketplace"
        ]
        
        for plugin_path in plugin_paths:
            if plugin_path.exists():
                plugin_info["plugin_directories"].append(str(plugin_path.relative_to(self.root_path)))
                
                # Find individual plugins
                for item in plugin_path.rglob("*"):
                    if item.is_dir():
                        manifest_file = item / "plugin_manifest.json"
                        if manifest_file.exists():
                            try:
                                with open(manifest_file, 'r') as f:
                                    manifest = json.load(f)
                                plugin_info["plugin_manifests"].append({
                                    "path": str(item.relative_to(self.root_path)),
                                    "name": manifest.get("name", item.name),
                                    "description": manifest.get("description", "")
                                })
                            except Exception:
                                pass
        
        return plugin_info
    
    def analyze_extension_structure(self) -> Dict[str, Any]:
        """Analyze extension system structure"""
        extension_info = {
            "extension_directories": [],
            "extension_manifests": []
        }
        
        extensions_path = self.root_path / "extensions"
        if extensions_path.exists():
            extension_info["extension_directories"].append(str(extensions_path.relative_to(self.root_path)))
            
            # Find extension manifests
            for manifest_file in extensions_path.rglob("extension.json"):
                try:
                    with open(manifest_file, 'r') as f:
                        manifest = json.load(f)
                    extension_info["extension_manifests"].append({
                        "path": str(manifest_file.parent.relative_to(self.root_path)),
                        "name": manifest.get("name", manifest_file.parent.name),
                        "description": manifest.get("description", "")
                    })
                except Exception:
                    pass
        
        return extension_info
    
    def analyze_docker_services(self) -> List[str]:
        """Identify all Docker services"""
        services = []
        
        for compose_file in self.root_path.rglob("docker-compose*.yml"):
            try:
                if yaml is None:
                    print("Warning: PyYAML not installed, skipping docker-compose analysis")
                    continue
                with open(compose_file, 'r') as f:
                    data = yaml.safe_load(f)
                
                if 'services' in data:
                    services.extend(data['services'].keys())
                    
            except Exception as e:
                print(f"Warning: Could not parse {compose_file}: {e}")
        
        return list(set(services))
    
    def analyze_architecture_components(self) -> List[str]:
        """Identify main architecture components"""
        components = []
        
        # Look for main source directories
        src_path = self.root_path / "src"
        if src_path.exists():
            for item in src_path.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    components.append(item.name)
        
        # Add other key directories
        key_dirs = ["ui_launchers", "extensions", "plugin_marketplace", "docker", "scripts"]
        for dir_name in key_dirs:
            if (self.root_path / dir_name).exists():
                components.append(dir_name)
        
        return components
    
    def analyze_system(self) -> SystemInfo:
        """Perform complete system analysis"""
        print("Analyzing codebase...")
        
        return SystemInfo(
            python_dependencies=self.analyze_python_dependencies(),
            node_dependencies=self.analyze_node_dependencies(),
            rust_dependencies=self.analyze_rust_dependencies(),
            ui_components=self.analyze_ui_components(),
            database_services=self.analyze_database_services(),
            api_endpoints=self.analyze_api_endpoints(),
            plugin_structure=self.analyze_plugin_structure(),
            extension_structure=self.analyze_extension_structure(),
            docker_services=self.analyze_docker_services(),
            architecture_components=self.analyze_architecture_components()
        )


def main():
    """Main entry point for codebase analysis"""
    analyzer = CodebaseAnalyzer()
    system_info = analyzer.analyze_system()
    
    # Output results
    print("\n=== SYSTEM ANALYSIS RESULTS ===\n")
    
    print("Python Dependencies:")
    for name, version in sorted(system_info.python_dependencies.items()):
        print(f"  {name}: {version}")
    
    print(f"\nNode.js Dependencies ({len(system_info.node_dependencies)} UIs):")
    for ui_name, deps in system_info.node_dependencies.items():
        print(f"  {ui_name}: {len(deps)} dependencies")
    
    print(f"\nUI Components: {', '.join(system_info.ui_components)}")
    print(f"Database Services: {', '.join(system_info.database_services)}")
    print(f"Docker Services: {', '.join(system_info.docker_services)}")
    print(f"Architecture Components: {', '.join(system_info.architecture_components)}")
    
    print(f"\nAPI Endpoints ({len(system_info.api_endpoints)}):")
    for endpoint in sorted(system_info.api_endpoints)[:10]:  # Show first 10
        print(f"  {endpoint}")
    if len(system_info.api_endpoints) > 10:
        print(f"  ... and {len(system_info.api_endpoints) - 10} more")
    
    print(f"\nPlugins: {len(system_info.plugin_structure['plugin_manifests'])} found")
    print(f"Extensions: {len(system_info.extension_structure['extension_manifests'])} found")
    
    # Save to JSON for other tools
    output_file = "system_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(asdict(system_info), f, indent=2)
    
    print(f"\nDetailed analysis saved to: {output_file}")


if __name__ == "__main__":
    main()