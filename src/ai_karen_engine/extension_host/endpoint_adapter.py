"""
Extension endpoint adapter for unified API integration.
Provides compatibility layer for extensions to work with new unified endpoints.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass

from ai_karen_engine.extension_host.models2 import ExtensionManifest


@dataclass
class EndpointMapping:
    """Mapping between legacy and unified endpoints."""
    legacy_path: str
    unified_path: str
    required_scopes: List[str]
    migration_notes: str


class ExtensionEndpointAdapter:
    """
    Adapter to help extensions integrate with unified API endpoints.
    Provides migration guidance and compatibility checks.
    """
    
    # Endpoint mappings from legacy to unified
    ENDPOINT_MAPPINGS = [
        EndpointMapping(
            legacy_path="/ag_ui/memory",
            unified_path="/memory/search",
            required_scopes=["memory:read"],
            migration_notes="Use POST /memory/search with MemQuery schema"
        ),
        EndpointMapping(
            legacy_path="/memory_ag_ui",
            unified_path="/memory/commit",
            required_scopes=["memory:write"],
            migration_notes="Use POST /memory/commit with MemCommit schema"
        ),
        EndpointMapping(
            legacy_path="/chat_memory",
            unified_path="/copilot/assist",
            required_scopes=["chat:write"],
            migration_notes="Use POST /copilot/assist with AssistRequest schema"
        ),
        EndpointMapping(
            legacy_path="/legacy",
            unified_path="/copilot/assist",
            required_scopes=["chat:write"],
            migration_notes="Migrate to unified copilot interface"
        )
    ]
    
    def __init__(self):
        """Initialize the endpoint adapter."""
        self.logger = logging.getLogger("extension.endpoint_adapter")
    
    def analyze_extension_endpoints(self, manifest: ExtensionManifest) -> Dict[str, Any]:
        """
        Analyze extension endpoints and provide migration recommendations.
        
        Args:
            manifest: Extension manifest to analyze
            
        Returns:
            Analysis report with migration recommendations
        """
        analysis = {
            "extension_name": manifest.name,
            "total_endpoints": len(manifest.api.endpoints),
            "legacy_endpoints": [],
            "unified_endpoints": [],
            "migration_required": False,
            "missing_scopes": [],
            "recommendations": []
        }
        
        # Analyze each endpoint
        for endpoint in manifest.api.endpoints:
            if isinstance(endpoint, dict) and 'path' in endpoint:
                path = endpoint['path']
                
                # Check if it's a legacy endpoint
                legacy_mapping = self._find_legacy_mapping(path)
                if legacy_mapping:
                    analysis["legacy_endpoints"].append({
                        "path": path,
                        "mapping": legacy_mapping,
                        "methods": endpoint.get('methods', [])
                    })
                    analysis["migration_required"] = True
                
                # Check if it's already using unified endpoints
                elif any(unified in path for unified in ["/copilot/assist", "/memory/search", "/memory/commit"]):
                    analysis["unified_endpoints"].append({
                        "path": path,
                        "methods": endpoint.get('methods', [])
                    })
        
        # Check for missing RBAC scopes
        analysis["missing_scopes"] = self._check_missing_scopes(manifest, analysis["unified_endpoints"])
        
        # Generate recommendations
        analysis["recommendations"] = self._generate_recommendations(analysis)
        
        return analysis
    
    def _find_legacy_mapping(self, path: str) -> Optional[EndpointMapping]:
        """Find legacy endpoint mapping for a given path."""
        for mapping in self.ENDPOINT_MAPPINGS:
            if mapping.legacy_path in path:
                return mapping
        return None
    
    def _check_missing_scopes(self, manifest: ExtensionManifest, unified_endpoints: List[Dict[str, Any]]) -> List[str]:
        """Check for missing RBAC scopes based on unified endpoints used."""
        required_scopes = set()
        
        # Determine required scopes based on endpoints
        for endpoint in unified_endpoints:
            path = endpoint['path']
            if '/copilot/assist' in path:
                required_scopes.add('chat:write')
            if '/memory/search' in path:
                required_scopes.add('memory:read')
            if '/memory/commit' in path:
                required_scopes.add('memory:write')
        
        # Check declared permissions
        declared_scopes = set()
        if manifest.permissions:
            declared_scopes.update(manifest.permissions.system_access or [])
            declared_scopes.update(manifest.permissions.data_access or [])
        
        # Find missing scopes
        missing_scopes = required_scopes - declared_scopes
        return list(missing_scopes)
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate migration and improvement recommendations."""
        recommendations = []
        
        # Legacy endpoint recommendations
        if analysis["legacy_endpoints"]:
            recommendations.append(
                f"Migrate {len(analysis['legacy_endpoints'])} legacy endpoints to unified API. "
                f"This will improve performance and ensure future compatibility."
            )
            
            for legacy_ep in analysis["legacy_endpoints"]:
                mapping = legacy_ep["mapping"]
                recommendations.append(
                    f"Replace '{legacy_ep['path']}' with '{mapping.unified_path}'. "
                    f"Required scopes: {', '.join(mapping.required_scopes)}. "
                    f"Migration: {mapping.migration_notes}"
                )
        
        # Missing scope recommendations
        if analysis["missing_scopes"]:
            recommendations.append(
                f"Add missing RBAC scopes to permissions: {', '.join(analysis['missing_scopes'])}. "
                f"Add these to permissions.system_access or permissions.data_access in manifest."
            )
        
        # Best practices recommendations
        if analysis["unified_endpoints"]:
            recommendations.append(
                f"Extension uses {len(analysis['unified_endpoints'])} unified endpoints. "
                f"Ensure proper error handling and correlation ID propagation."
            )
        
        # Performance recommendations
        if analysis["total_endpoints"] > 5:
            recommendations.append(
                f"Extension defines {analysis['total_endpoints']} endpoints. "
                f"Consider consolidating related endpoints for better maintainability."
            )
        
        return recommendations
    
    def generate_migration_guide(self, manifest: ExtensionManifest) -> str:
        """
        Generate a comprehensive migration guide for an extension.
        
        Args:
            manifest: Extension manifest to generate guide for
            
        Returns:
            Markdown-formatted migration guide
        """
        analysis = self.analyze_extension_endpoints(manifest)
        
        guide = f"""# Migration Guide for {manifest.name}

## Overview
This guide helps migrate your extension to use the unified API endpoints from Phase 4.1.a.

## Current Status
- Total endpoints: {analysis['total_endpoints']}
- Legacy endpoints: {len(analysis['legacy_endpoints'])}
- Unified endpoints: {len(analysis['unified_endpoints'])}
- Migration required: {'Yes' if analysis['migration_required'] else 'No'}

"""
        
        if analysis["legacy_endpoints"]:
            guide += """## Legacy Endpoint Migration

The following endpoints need to be updated:

"""
            for legacy_ep in analysis["legacy_endpoints"]:
                mapping = legacy_ep["mapping"]
                guide += f"""### {legacy_ep['path']}
- **Replace with**: `{mapping.unified_path}`
- **Required scopes**: {', '.join(mapping.required_scopes)}
- **Migration notes**: {mapping.migration_notes}
- **Current methods**: {', '.join(legacy_ep['methods'])}

"""
        
        if analysis["missing_scopes"]:
            guide += f"""## Required Permission Updates

Add the following scopes to your extension manifest:

```json
{{
  "permissions": {{
    "system_access": {analysis['missing_scopes']},
    "data_access": ["memory:read", "memory:write"]
  }}
}}
```

"""
        
        if analysis["recommendations"]:
            guide += """## Recommendations

"""
            for i, rec in enumerate(analysis["recommendations"], 1):
                guide += f"{i}. {rec}\n"
        
        guide += """
## Testing Your Migration

1. Update your extension manifest with new endpoints and permissions
2. Test with the unified API endpoints
3. Verify RBAC scope enforcement works correctly
4. Check correlation ID propagation in logs
5. Validate tenant isolation if using data operations

## Support

For migration assistance, refer to the extension developer documentation or contact the development team.
"""
        
        return guide
    
    def validate_endpoint_compatibility(self, manifest: ExtensionManifest) -> Dict[str, Any]:
        """
        Validate extension endpoint compatibility with unified API.
        
        Args:
            manifest: Extension manifest to validate
            
        Returns:
            Compatibility validation report
        """
        analysis = self.analyze_extension_endpoints(manifest)
        
        compatibility = {
            "is_compatible": True,
            "compatibility_score": 100,
            "issues": [],
            "warnings": [],
            "migration_required": analysis["migration_required"]
        }
        
        # Check for blocking issues
        if analysis["legacy_endpoints"]:
            compatibility["is_compatible"] = False
            compatibility["compatibility_score"] -= 30
            compatibility["issues"].append(
                f"Extension uses {len(analysis['legacy_endpoints'])} legacy endpoints that will be removed"
            )
        
        # Check for warnings
        if analysis["missing_scopes"]:
            compatibility["compatibility_score"] -= 20
            compatibility["warnings"].append(
                f"Missing required RBAC scopes: {', '.join(analysis['missing_scopes'])}"
            )
        
        # Check for best practices
        if not analysis["unified_endpoints"] and analysis["total_endpoints"] > 0:
            compatibility["compatibility_score"] -= 10
            compatibility["warnings"].append(
                "Extension doesn't use any unified endpoints - consider integration opportunities"
            )
        
        return compatibility


# Convenience functions for extension developers
def analyze_extension(manifest: Union[ExtensionManifest, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze an extension for endpoint compatibility.
    
    Args:
        manifest: Extension manifest (object or dict)
        
    Returns:
        Analysis report
    """
    if isinstance(manifest, dict):
        manifest = ExtensionManifest.from_dict(manifest)
    
    adapter = ExtensionEndpointAdapter()
    return adapter.analyze_extension_endpoints(manifest)


def generate_migration_guide(manifest: Union[ExtensionManifest, Dict[str, Any]]) -> str:
    """
    Generate migration guide for an extension.
    
    Args:
        manifest: Extension manifest (object or dict)
        
    Returns:
        Markdown migration guide
    """
    if isinstance(manifest, dict):
        manifest = ExtensionManifest.from_dict(manifest)
    
    adapter = ExtensionEndpointAdapter()
    return adapter.generate_migration_guide(manifest)


__all__ = [
    "EndpointMapping",
    "ExtensionEndpointAdapter", 
    "analyze_extension",
    "generate_migration_guide"
]