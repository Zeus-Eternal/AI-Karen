"""
Extension Version Management

This module provides utilities for managing extension versions and dependency resolution.
"""

import logging
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum

import semver
from sqlalchemy.orm import Session

from .models import ExtensionVersion, ExtensionDependency, ExtensionInstallation, ExtensionListing

logger = logging.getLogger(__name__)


class DependencyType(str, Enum):
    """Types of dependencies."""
    EXTENSION = "extension"
    PLUGIN = "plugin"
    SYSTEM_SERVICE = "system_service"


@dataclass
class ResolvedDependency:
    """A resolved dependency with version information."""
    name: str
    dependency_type: DependencyType
    version: Optional[str]
    constraint: Optional[str]
    is_optional: bool
    is_satisfied: bool
    conflict_reason: Optional[str] = None


@dataclass
class DependencyGraph:
    """Dependency graph for extension resolution."""
    nodes: Dict[str, 'DependencyNode']
    edges: List[Tuple[str, str]]  # (from, to) relationships
    
    def __post_init__(self):
        if not hasattr(self, 'nodes'):
            self.nodes = {}
        if not hasattr(self, 'edges'):
            self.edges = []


@dataclass
class DependencyNode:
    """Node in the dependency graph."""
    name: str
    version: Optional[str]
    dependency_type: DependencyType
    is_root: bool = False
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class VersionManager:
    """Manages extension versions and dependency resolution."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def parse_version(self, version_string: str) -> semver.VersionInfo:
        """Parse a semantic version string."""
        try:
            return semver.VersionInfo.parse(version_string)
        except ValueError as e:
            raise ValueError(f"Invalid semantic version '{version_string}': {e}")
    
    def satisfies_constraint(self, version: str, constraint: str) -> bool:
        """Check if a version satisfies a constraint."""
        try:
            return semver.match(version, constraint)
        except Exception as e:
            logger.warning(f"Error checking version constraint '{version}' against '{constraint}': {e}")
            return False
    
    def find_compatible_version(
        self,
        extension_name: str,
        constraint: Optional[str] = None,
        prefer_stable: bool = True
    ) -> Optional[ExtensionVersion]:
        """Find a compatible version for an extension."""
        # Get extension listing
        listing = self.db.query(ExtensionListing).filter(
            ExtensionListing.name == extension_name
        ).first()
        
        if not listing:
            return None
        
        # Get all versions
        versions_query = self.db.query(ExtensionVersion).filter(
            ExtensionVersion.listing_id == listing.id
        )
        
        if prefer_stable:
            versions_query = versions_query.filter(ExtensionVersion.is_stable == True)
        
        versions = versions_query.order_by(ExtensionVersion.created_at.desc()).all()
        
        if not constraint:
            # Return latest version
            return versions[0] if versions else None
        
        # Find version that satisfies constraint
        for version in versions:
            if self.satisfies_constraint(version.version, constraint):
                return version
        
        return None
    
    def get_latest_version(self, extension_name: str) -> Optional[ExtensionVersion]:
        """Get the latest stable version of an extension."""
        return self.find_compatible_version(extension_name, prefer_stable=True)
    
    def compare_versions(self, version1: str, version2: str) -> int:
        """Compare two versions. Returns -1, 0, or 1."""
        try:
            v1 = semver.VersionInfo.parse(version1)
            v2 = semver.VersionInfo.parse(version2)
            return v1.compare(v2)
        except ValueError:
            # Fallback to string comparison
            if version1 < version2:
                return -1
            elif version1 > version2:
                return 1
            else:
                return 0
    
    def is_upgrade(self, current_version: str, target_version: str) -> bool:
        """Check if target version is an upgrade from current version."""
        return self.compare_versions(current_version, target_version) < 0
    
    def is_compatible_upgrade(
        self,
        current_version: str,
        target_version: str,
        allow_major: bool = False
    ) -> bool:
        """Check if target version is a compatible upgrade."""
        try:
            current = semver.VersionInfo.parse(current_version)
            target = semver.VersionInfo.parse(target_version)
            
            if not self.is_upgrade(current_version, target_version):
                return False
            
            if allow_major:
                return True
            
            # Only allow minor and patch upgrades
            return current.major == target.major
            
        except ValueError:
            return False
    
    def resolve_dependencies(
        self,
        extension_name: str,
        version: str,
        tenant_id: str,
        installed_extensions: Optional[Dict[str, str]] = None
    ) -> Tuple[bool, List[ResolvedDependency], List[str]]:
        """
        Resolve dependencies for an extension.
        
        Returns:
            - success: Whether resolution was successful
            - resolved_deps: List of resolved dependencies
            - errors: List of error messages
        """
        if installed_extensions is None:
            installed_extensions = self._get_installed_extensions(tenant_id)
        
        # Get extension version
        extension_version = self.db.query(ExtensionVersion).join(ExtensionListing).filter(
            ExtensionListing.name == extension_name,
            ExtensionVersion.version == version
        ).first()
        
        if not extension_version:
            return False, [], [f"Extension version {extension_name}@{version} not found"]
        
        # Build dependency graph
        graph = self._build_dependency_graph(extension_version, installed_extensions)
        
        # Check for circular dependencies
        if self._has_circular_dependencies(graph):
            return False, [], ["Circular dependency detected"]
        
        # Resolve each dependency
        resolved_deps = []
        errors = []
        
        for dep_name, node in graph.nodes.items():
            if node.is_root:
                continue  # Skip the root extension
            
            resolved_dep = self._resolve_single_dependency(
                node,
                installed_extensions,
                tenant_id
            )
            
            resolved_deps.append(resolved_dep)
            
            if not resolved_dep.is_satisfied and not resolved_dep.is_optional:
                errors.append(
                    f"Required dependency '{dep_name}' could not be satisfied: {resolved_dep.conflict_reason}"
                )
        
        success = len(errors) == 0
        return success, resolved_deps, errors
    
    def _get_installed_extensions(self, tenant_id: str) -> Dict[str, str]:
        """Get currently installed extensions for a tenant."""
        installations = self.db.query(ExtensionInstallation).join(
            ExtensionListing
        ).join(
            ExtensionVersion
        ).filter(
            ExtensionInstallation.tenant_id == tenant_id,
            ExtensionInstallation.status == "installed"
        ).all()
        
        return {
            installation.listing.name: installation.version.version
            for installation in installations
        }
    
    def _build_dependency_graph(
        self,
        root_version: ExtensionVersion,
        installed_extensions: Dict[str, str]
    ) -> DependencyGraph:
        """Build a dependency graph for an extension version."""
        graph = DependencyGraph(nodes={}, edges=[])
        visited = set()
        
        # Add root node
        root_name = root_version.listing.name
        graph.nodes[root_name] = DependencyNode(
            name=root_name,
            version=root_version.version,
            dependency_type=DependencyType.EXTENSION,
            is_root=True
        )
        
        # Recursively build graph
        self._build_dependency_graph_recursive(
            root_version,
            graph,
            visited,
            installed_extensions
        )
        
        return graph
    
    def _build_dependency_graph_recursive(
        self,
        version: ExtensionVersion,
        graph: DependencyGraph,
        visited: Set[str],
        installed_extensions: Dict[str, str]
    ):
        """Recursively build dependency graph."""
        version_key = f"{version.listing.name}@{version.version}"
        
        if version_key in visited:
            return
        
        visited.add(version_key)
        
        # Get dependencies for this version
        dependencies = self.db.query(ExtensionDependency).filter(
            ExtensionDependency.version_id == version.id
        ).all()
        
        for dep in dependencies:
            dep_name = dep.dependency_name
            
            # Add dependency node if not exists
            if dep_name not in graph.nodes:
                graph.nodes[dep_name] = DependencyNode(
                    name=dep_name,
                    version=None,  # Will be resolved later
                    dependency_type=DependencyType(dep.dependency_type)
                )
            
            # Add edge
            graph.edges.append((version.listing.name, dep_name))
            
            # Add to parent's dependencies
            if version.listing.name in graph.nodes:
                graph.nodes[version.listing.name].dependencies.append(dep_name)
            
            # If it's an extension dependency, recurse
            if dep.dependency_type == DependencyType.EXTENSION:
                # Find compatible version
                compatible_version = self.find_compatible_version(
                    dep_name,
                    dep.version_constraint
                )
                
                if compatible_version:
                    graph.nodes[dep_name].version = compatible_version.version
                    self._build_dependency_graph_recursive(
                        compatible_version,
                        graph,
                        visited,
                        installed_extensions
                    )
    
    def _has_circular_dependencies(self, graph: DependencyGraph) -> bool:
        """Check if the dependency graph has circular dependencies."""
        visited = set()
        rec_stack = set()
        
        def dfs(node_name: str) -> bool:
            visited.add(node_name)
            rec_stack.add(node_name)
            
            if node_name in graph.nodes:
                for dep_name in graph.nodes[node_name].dependencies:
                    if dep_name not in visited:
                        if dfs(dep_name):
                            return True
                    elif dep_name in rec_stack:
                        return True
            
            rec_stack.remove(node_name)
            return False
        
        for node_name in graph.nodes:
            if node_name not in visited:
                if dfs(node_name):
                    return True
        
        return False
    
    def _resolve_single_dependency(
        self,
        node: DependencyNode,
        installed_extensions: Dict[str, str],
        tenant_id: str
    ) -> ResolvedDependency:
        """Resolve a single dependency."""
        if node.dependency_type == DependencyType.EXTENSION:
            return self._resolve_extension_dependency(node, installed_extensions)
        elif node.dependency_type == DependencyType.PLUGIN:
            return self._resolve_plugin_dependency(node)
        elif node.dependency_type == DependencyType.SYSTEM_SERVICE:
            return self._resolve_system_service_dependency(node)
        else:
            return ResolvedDependency(
                name=node.name,
                dependency_type=node.dependency_type,
                version=None,
                constraint=None,
                is_optional=False,
                is_satisfied=False,
                conflict_reason="Unknown dependency type"
            )
    
    def _resolve_extension_dependency(
        self,
        node: DependencyNode,
        installed_extensions: Dict[str, str]
    ) -> ResolvedDependency:
        """Resolve an extension dependency."""
        # Check if already installed
        if node.name in installed_extensions:
            installed_version = installed_extensions[node.name]
            
            # If no constraint, any installed version is fine
            if not node.version:
                return ResolvedDependency(
                    name=node.name,
                    dependency_type=node.dependency_type,
                    version=installed_version,
                    constraint=None,
                    is_optional=False,
                    is_satisfied=True
                )
            
            # Check if installed version satisfies constraint
            # For now, we'll do exact version matching
            if installed_version == node.version:
                return ResolvedDependency(
                    name=node.name,
                    dependency_type=node.dependency_type,
                    version=installed_version,
                    constraint=node.version,
                    is_optional=False,
                    is_satisfied=True
                )
            else:
                return ResolvedDependency(
                    name=node.name,
                    dependency_type=node.dependency_type,
                    version=installed_version,
                    constraint=node.version,
                    is_optional=False,
                    is_satisfied=False,
                    conflict_reason=f"Installed version {installed_version} does not match required {node.version}"
                )
        
        # Extension not installed - check if available
        available_version = self.find_compatible_version(node.name, node.version)
        
        if available_version:
            return ResolvedDependency(
                name=node.name,
                dependency_type=node.dependency_type,
                version=available_version.version,
                constraint=node.version,
                is_optional=False,
                is_satisfied=True
            )
        else:
            return ResolvedDependency(
                name=node.name,
                dependency_type=node.dependency_type,
                version=None,
                constraint=node.version,
                is_optional=False,
                is_satisfied=False,
                conflict_reason=f"No compatible version found for constraint {node.version}"
            )
    
    def _resolve_plugin_dependency(self, node: DependencyNode) -> ResolvedDependency:
        """Resolve a plugin dependency."""
        # For now, assume all plugins are available
        # In a real implementation, this would check the plugin registry
        return ResolvedDependency(
            name=node.name,
            dependency_type=node.dependency_type,
            version=None,
            constraint=None,
            is_optional=False,
            is_satisfied=True
        )
    
    def _resolve_system_service_dependency(self, node: DependencyNode) -> ResolvedDependency:
        """Resolve a system service dependency."""
        # For now, assume all system services are available
        # In a real implementation, this would check service availability
        return ResolvedDependency(
            name=node.name,
            dependency_type=node.dependency_type,
            version=None,
            constraint=None,
            is_optional=False,
            is_satisfied=True
        )
    
    def get_update_candidates(
        self,
        tenant_id: str,
        include_prereleases: bool = False
    ) -> List[Tuple[str, str, str]]:
        """
        Get extensions that have available updates.
        
        Returns list of (extension_name, current_version, latest_version) tuples.
        """
        installed_extensions = self._get_installed_extensions(tenant_id)
        update_candidates = []
        
        for ext_name, current_version in installed_extensions.items():
            latest_version = self.find_compatible_version(
                ext_name,
                prefer_stable=not include_prereleases
            )
            
            if latest_version and self.is_upgrade(current_version, latest_version.version):
                update_candidates.append((ext_name, current_version, latest_version.version))
        
        return update_candidates
    
    def validate_manifest_version(self, manifest: Dict) -> List[str]:
        """Validate version information in an extension manifest."""
        errors = []
        
        # Check required version field
        if 'version' not in manifest:
            errors.append("Missing 'version' field in manifest")
        else:
            try:
                self.parse_version(manifest['version'])
            except ValueError as e:
                errors.append(f"Invalid version format: {e}")
        
        # Check API version compatibility
        if 'api_version' not in manifest:
            errors.append("Missing 'api_version' field in manifest")
        
        # Check Kari version constraints
        if 'kari_min_version' in manifest:
            try:
                self.parse_version(manifest['kari_min_version'])
            except ValueError as e:
                errors.append(f"Invalid kari_min_version format: {e}")
        
        if 'kari_max_version' in manifest:
            try:
                self.parse_version(manifest['kari_max_version'])
            except ValueError as e:
                errors.append(f"Invalid kari_max_version format: {e}")
        
        return errors