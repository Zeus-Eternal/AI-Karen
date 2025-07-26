"""
Extension dependency resolution and loading order determination.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Set

from ai_karen_engine.extensions.models import ExtensionManifest


class DependencyError(Exception):
    """Dependency resolution error."""
    pass


class CircularDependencyError(DependencyError):
    """Circular dependency detected."""
    pass


class MissingDependencyError(DependencyError):
    """Required dependency is missing."""
    pass


class DependencyResolver:
    """
    Resolves extension dependencies and determines loading order.
    
    Uses topological sorting to ensure extensions are loaded in the correct
    order based on their dependencies.
    """
    
    def __init__(self):
        """Initialize the dependency resolver."""
        self.logger = logging.getLogger("extension.dependency_resolver")
    
    def resolve_loading_order(
        self, 
        manifests: Dict[str, ExtensionManifest]
    ) -> List[str]:
        """
        Resolve the loading order for extensions based on dependencies.
        
        Args:
            manifests: Dictionary mapping extension names to their manifests
            
        Returns:
            List of extension names in loading order
            
        Raises:
            CircularDependencyError: If circular dependencies are detected
            MissingDependencyError: If required dependencies are missing
        """
        self.logger.info(f"Resolving loading order for {len(manifests)} extensions")
        
        # Build dependency graph
        dependency_graph = self._build_dependency_graph(manifests)
        
        # Check for missing dependencies
        self._check_missing_dependencies(dependency_graph, manifests)
        
        # Perform topological sort
        loading_order = self._topological_sort(dependency_graph)
        
        self.logger.info(f"Resolved loading order: {loading_order}")
        return loading_order
    
    def _build_dependency_graph(
        self, 
        manifests: Dict[str, ExtensionManifest]
    ) -> Dict[str, Set[str]]:
        """
        Build a dependency graph from extension manifests.
        
        Args:
            manifests: Dictionary mapping extension names to their manifests
            
        Returns:
            Dictionary mapping extension names to their dependencies
        """
        graph = {}
        
        for name, manifest in manifests.items():
            dependencies = set()
            
            # Add extension dependencies
            for dep in manifest.dependencies.extensions:
                # Parse dependency specification (e.g., "extension@^1.0.0")
                if '@' in dep:
                    dep_name, version_spec = dep.split('@', 1)
                else:
                    dep_name = dep
                
                dependencies.add(dep_name)
            
            graph[name] = dependencies
        
        return graph
    
    def _check_missing_dependencies(
        self, 
        dependency_graph: Dict[str, Set[str]], 
        manifests: Dict[str, ExtensionManifest]
    ) -> None:
        """
        Check for missing dependencies.
        
        Args:
            dependency_graph: Dependency graph
            manifests: Available extension manifests
            
        Raises:
            MissingDependencyError: If required dependencies are missing
        """
        available_extensions = set(manifests.keys())
        missing_deps = []
        
        for extension, dependencies in dependency_graph.items():
            for dep in dependencies:
                if dep not in available_extensions:
                    missing_deps.append(f"{extension} requires {dep}")
        
        if missing_deps:
            raise MissingDependencyError(
                f"Missing dependencies: {', '.join(missing_deps)}"
            )
    
    def _topological_sort(self, graph: Dict[str, Set[str]]) -> List[str]:
        """
        Perform topological sort using Kahn's algorithm.
        
        Args:
            graph: Dependency graph
            
        Returns:
            List of nodes in topological order
            
        Raises:
            CircularDependencyError: If circular dependencies are detected
        """
        # Calculate in-degrees
        in_degree = {node: 0 for node in graph}
        for node in graph:
            for dependency in graph[node]:
                if dependency in in_degree:
                    in_degree[dependency] += 1
        
        # Find nodes with no incoming edges
        queue = [node for node, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            # Remove node with no incoming edges
            current = queue.pop(0)
            result.append(current)
            
            # Remove edges from current node
            for dependency in graph[current]:
                if dependency in in_degree:
                    in_degree[dependency] -= 1
                    if in_degree[dependency] == 0:
                        queue.append(dependency)
        
        # Check for circular dependencies
        if len(result) != len(graph):
            remaining_nodes = [node for node in graph if node not in result]
            raise CircularDependencyError(
                f"Circular dependency detected involving: {', '.join(remaining_nodes)}"
            )
        
        return result
    
    def check_version_compatibility(
        self, 
        manifests: Dict[str, ExtensionManifest]
    ) -> List[str]:
        """
        Check version compatibility between extensions.
        
        Args:
            manifests: Dictionary mapping extension names to their manifests
            
        Returns:
            List of compatibility warnings
        """
        warnings = []
        
        for name, manifest in manifests.items():
            for dep in manifest.dependencies.extensions:
                if '@' in dep:
                    dep_name, version_spec = dep.split('@', 1)
                    
                    if dep_name in manifests:
                        dep_version = manifests[dep_name].version
                        
                        # Basic version compatibility check
                        if not self._is_version_compatible(dep_version, version_spec):
                            warnings.append(
                                f"{name} requires {dep_name} {version_spec}, "
                                f"but version {dep_version} is available"
                            )
        
        return warnings
    
    def _is_version_compatible(self, available_version: str, required_spec: str) -> bool:
        """
        Check if available version satisfies the required specification.
        
        This is a simplified implementation. In production, you'd want to use
        a proper semantic versioning library.
        
        Args:
            available_version: Available version (e.g., "1.2.3")
            required_spec: Required version specification (e.g., "^1.0.0")
            
        Returns:
            True if compatible, False otherwise
        """
        # Remove leading ^ or ~ if present
        if required_spec.startswith(('^', '~')):
            required_version = required_spec[1:]
        else:
            required_version = required_spec
        
        try:
            # Parse versions
            available_parts = [int(x) for x in available_version.split('.')]
            required_parts = [int(x) for x in required_version.split('.')]
            
            # Pad with zeros if needed
            max_len = max(len(available_parts), len(required_parts))
            available_parts.extend([0] * (max_len - len(available_parts)))
            required_parts.extend([0] * (max_len - len(required_parts)))
            
            # For ^1.0.0, compatible if major version matches and minor.patch >= required
            if required_spec.startswith('^'):
                return (available_parts[0] == required_parts[0] and 
                        available_parts >= required_parts)
            
            # For ~1.0.0, compatible if major.minor matches and patch >= required
            elif required_spec.startswith('~'):
                return (available_parts[0] == required_parts[0] and
                        available_parts[1] == required_parts[1] and
                        available_parts[2] >= required_parts[2])
            
            # Exact match
            else:
                return available_parts == required_parts
                
        except (ValueError, IndexError):
            # If version parsing fails, assume incompatible
            return False
    
    def get_dependency_tree(
        self, 
        manifests: Dict[str, ExtensionManifest]
    ) -> Dict[str, Dict[str, any]]:
        """
        Get a detailed dependency tree for visualization.
        
        Args:
            manifests: Dictionary mapping extension names to their manifests
            
        Returns:
            Dictionary representing the dependency tree
        """
        tree = {}
        
        for name, manifest in manifests.items():
            tree[name] = {
                "version": manifest.version,
                "dependencies": {
                    "extensions": [],
                    "plugins": manifest.dependencies.plugins.copy(),
                    "system_services": manifest.dependencies.system_services.copy()
                }
            }
            
            # Process extension dependencies
            for dep in manifest.dependencies.extensions:
                if '@' in dep:
                    dep_name, version_spec = dep.split('@', 1)
                else:
                    dep_name = dep
                    version_spec = "*"
                
                tree[name]["dependencies"]["extensions"].append({
                    "name": dep_name,
                    "version_spec": version_spec,
                    "available": dep_name in manifests,
                    "available_version": manifests[dep_name].version if dep_name in manifests else None
                })
        
        return tree


__all__ = [
    "DependencyResolver",
    "DependencyError", 
    "CircularDependencyError",
    "MissingDependencyError"
]