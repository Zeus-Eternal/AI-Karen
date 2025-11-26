"""
Validator for the legacy extension system.

This module provides backward compatibility with the old extension validator
while migrating to the new two-tier architecture.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from .base import ExtensionManifest


class ExtensionValidator:
    """
    Validator for extension manifests in the legacy system.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("extension.validator")
    
    def validate_manifest_enhanced(
        self, 
        manifest: ExtensionManifest
    ) -> Tuple[bool, List[str], List[str], List[Any]]:
        """
        Validate an extension manifest with enhanced checks.
        
        Args:
            manifest: Extension manifest to validate
            
        Returns:
            Tuple of (is_valid, errors, warnings, field_errors)
        """
        errors = []
        warnings = []
        field_errors = []
        
        # Check required fields
        if not manifest.id:
            errors.append("Extension ID is required")
            
        if not manifest.name:
            errors.append("Extension name is required")
            
        if not manifest.version:
            errors.append("Extension version is required")
            
        if not manifest.entrypoint:
            errors.append("Extension entrypoint is required")
            
        # Check hook points
        if not isinstance(manifest.hook_points, list):
            field_errors.append("hook_points must be a list")
        else:
            valid_hook_points = [
                "pre_intent_detection",
                "pre_memory_retrieval",
                "post_memory_retrieval",
                "pre_llm_prompt",
                "post_llm_result",
                "post_response"
            ]
            for hook_point in manifest.hook_points:
                if hook_point not in valid_hook_points:
                    warnings.append(f"Unknown hook point: {hook_point}")
                    
        # Check prompt files
        if not isinstance(manifest.prompt_files, dict):
            field_errors.append("prompt_files must be a dictionary")
            
        # Check config schema
        if not isinstance(manifest.config_schema, dict):
            field_errors.append("config_schema must be a dictionary")
            
        # Check permissions
        if not isinstance(manifest.permissions, dict):
            field_errors.append("permissions must be a dictionary")
            
        # Check RBAC
        if not isinstance(manifest.rbac, dict):
            field_errors.append("rbac must be a dictionary")
            
        return (len(errors) == 0, errors, warnings, field_errors)
    
    def get_validation_report(self, manifest: ExtensionManifest) -> Dict[str, Any]:
        """
        Get a comprehensive validation report for an extension manifest.
        
        Args:
            manifest: Extension manifest to validate
            
        Returns:
            Dictionary with validation report
        """
        is_valid, errors, warnings, field_errors = self.validate_manifest_enhanced(manifest)
        
        report = {
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "field_errors": field_errors,
            "recommendations": []
        }
        
        # Add recommendations based on validation results
        if not is_valid:
            report["recommendations"].append("Fix all errors before loading the extension")
            
        if warnings:
            report["recommendations"].append("Consider addressing warnings for better compatibility")
            
        if field_errors:
            report["recommendations"].append("Fix field errors to ensure proper functionality")
            
        return report