"""
Startup Validation Service

This module provides comprehensive startup validation for LLM providers with:
- Authentication validation on startup
- Provider health checks
- Configuration validation
- User feedback for authentication issues
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from ai_karen_engine.config.llm_provider_config import get_provider_config_manager
from ai_karen_engine.config.runtime_provider_manager import get_runtime_provider_manager
from ai_karen_engine.config.provider_authentication import get_provider_auth_manager

logger = logging.getLogger(__name__)


class StartupValidationService:
    """
    Service for validating LLM provider configurations and authentication on startup.
    
    Features:
    - Comprehensive provider validation
    - Authentication checks
    - Health monitoring setup
    - User-friendly error reporting
    """
    
    def __init__(self):
        self.config_manager = get_provider_config_manager()
        self.runtime_manager = get_runtime_provider_manager()
        self.auth_manager = get_provider_auth_manager()
    
    async def validate_startup(self) -> Dict[str, Any]:
        """
        Perform comprehensive startup validation.
        
        Returns:
            Validation results with status and recommendations
        """
        logger.info("Starting LLM provider validation...")
        
        validation_results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "unknown",
            "provider_count": 0,
            "enabled_count": 0,
            "healthy_count": 0,
            "authenticated_count": 0,
            "issues": [],
            "recommendations": [],
            "providers": {}
        }
        
        try:
            # Step 1: Validate configurations
            config_results = await self._validate_configurations()
            validation_results.update(config_results)
            
            # Step 2: Validate authentication
            auth_results = await self._validate_authentication()
            validation_results["authentication"] = auth_results
            
            # Step 3: Check provider health
            health_results = await self._check_provider_health()
            validation_results["health"] = health_results
            
            # Step 4: Generate recommendations
            recommendations = self._generate_recommendations(validation_results)
            validation_results["recommendations"] = recommendations
            
            # Step 5: Determine overall status
            overall_status = self._determine_overall_status(validation_results)
            validation_results["overall_status"] = overall_status
            
            # Step 6: Start health monitoring if providers are available
            if validation_results["healthy_count"] > 0:
                await self.runtime_manager.start_health_monitoring()
                logger.info("Started background health monitoring")
            
            logger.info(f"Startup validation completed with status: {overall_status}")
            return validation_results
            
        except Exception as e:
            logger.error(f"Startup validation failed: {e}")
            validation_results["overall_status"] = "error"
            validation_results["issues"].append(f"Validation failed: {str(e)}")
            return validation_results
    
    async def _validate_configurations(self) -> Dict[str, Any]:
        """Validate provider configurations"""
        logger.info("Validating provider configurations...")
        
        providers = self.config_manager.list_providers()
        enabled_providers = self.config_manager.list_providers(enabled_only=True)
        
        config_issues = []
        provider_details = {}
        
        # Validate each provider configuration
        for provider in providers:
            provider_issues = []
            
            # Check basic configuration
            if not provider.is_valid:
                provider_issues.extend(provider.validation_errors)
            
            # Check authentication configuration
            if provider.authentication.api_key_env_var:
                import os
                if not os.getenv(provider.authentication.api_key_env_var):
                    stored_key = self.auth_manager.get_api_key(provider.name)
                    if not stored_key:
                        provider_issues.append(f"API key not configured (env var: {provider.authentication.api_key_env_var})")
            
            # Check endpoint configuration for remote providers
            if provider.provider_type.value in ["remote", "hybrid"]:
                if not provider.endpoint or not provider.endpoint.base_url:
                    provider_issues.append("Endpoint configuration missing for remote provider")
            
            provider_details[provider.name] = {
                "enabled": provider.enabled,
                "type": provider.provider_type.value,
                "auth_type": provider.authentication.type.value,
                "model_count": len(provider.models),
                "default_model": provider.default_model,
                "issues": provider_issues,
                "is_valid": len(provider_issues) == 0
            }
            
            config_issues.extend([f"{provider.name}: {issue}" for issue in provider_issues])
        
        return {
            "provider_count": len(providers),
            "enabled_count": len(enabled_providers),
            "configuration_issues": config_issues,
            "providers": provider_details
        }
    
    async def _validate_authentication(self) -> Dict[str, Any]:
        """Validate provider authentication"""
        logger.info("Validating provider authentication...")
        
        auth_results = await self.auth_manager.validate_all_providers()
        
        auth_summary = {
            "total_checked": len(auth_results),
            "valid_count": 0,
            "invalid_count": 0,
            "error_count": 0,
            "providers": {}
        }
        
        for provider_name, result in auth_results.items():
            if result.is_valid:
                auth_summary["valid_count"] += 1
            elif result.status.value == "invalid":
                auth_summary["invalid_count"] += 1
            else:
                auth_summary["error_count"] += 1
            
            auth_summary["providers"][provider_name] = {
                "status": result.status.value,
                "message": result.message,
                "validated_at": result.validated_at.isoformat(),
                "permissions": list(result.permissions) if result.permissions else [],
                "user_info": result.user_info or {}
            }
        
        return auth_summary
    
    async def _check_provider_health(self) -> Dict[str, Any]:
        """Check provider health status"""
        logger.info("Checking provider health...")
        
        enabled_providers = self.config_manager.get_provider_names(enabled_only=True)
        
        health_results = {}
        healthy_count = 0
        
        # Check health for each enabled provider
        for provider_name in enabled_providers:
            health_status = self.runtime_manager.check_provider_health(provider_name)
            
            if health_status.is_healthy:
                healthy_count += 1
            
            health_results[provider_name] = {
                "status": health_status.status.value,
                "message": health_status.error_message or "Healthy",
                "response_time": health_status.response_time,
                "last_check": health_status.last_check.isoformat(),
                "consecutive_failures": health_status.consecutive_failures,
                "capabilities_verified": list(health_status.capabilities_verified)
            }
        
        return {
            "total_checked": len(enabled_providers),
            "healthy_count": healthy_count,
            "providers": health_results
        }
    
    def _generate_recommendations(self, validation_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        # No providers configured
        if validation_results["provider_count"] == 0:
            recommendations.append("No LLM providers configured. Add at least one provider to enable AI features.")
            return recommendations
        
        # No enabled providers
        if validation_results["enabled_count"] == 0:
            recommendations.append("No LLM providers are enabled. Enable at least one provider in the configuration.")
        
        # No healthy providers
        elif validation_results.get("healthy_count", 0) == 0:
            recommendations.append("No healthy LLM providers found. Check provider configurations and network connectivity.")
        
        # Authentication issues
        auth_results = validation_results.get("authentication", {})
        if auth_results.get("invalid_count", 0) > 0:
            recommendations.append("Some providers have invalid authentication. Check API keys and permissions.")
        
        # Configuration issues
        config_issues = validation_results.get("configuration_issues", [])
        if config_issues:
            recommendations.append("Configuration issues found. Review provider settings and fix validation errors.")
        
        # Provider-specific recommendations
        for provider_name, provider_info in validation_results.get("providers", {}).items():
            if not provider_info.get("is_valid", True):
                issues = provider_info.get("issues", [])
                for issue in issues:
                    if "API key not configured" in issue:
                        recommendations.append(f"Configure API key for {provider_name} provider.")
                    elif "Endpoint configuration missing" in issue:
                        recommendations.append(f"Configure endpoint settings for {provider_name} provider.")
        
        # Health-specific recommendations
        health_results = validation_results.get("health", {})
        for provider_name, health_info in health_results.get("providers", {}).items():
            status = health_info.get("status", "unknown")
            if status == "unavailable":
                recommendations.append(f"Provider {provider_name} is unavailable. Check if the service is running.")
            elif status == "unhealthy":
                recommendations.append(f"Provider {provider_name} is unhealthy. Check network connectivity and service status.")
        
        # Positive recommendations
        if validation_results.get("healthy_count", 0) > 0:
            if not recommendations:
                recommendations.append("All providers are configured correctly and healthy.")
            else:
                recommendations.append(f"{validation_results['healthy_count']} provider(s) are healthy and ready to use.")
        
        return recommendations
    
    def _determine_overall_status(self, validation_results: Dict[str, Any]) -> str:
        """Determine overall validation status"""
        
        # Critical issues
        if validation_results["provider_count"] == 0:
            return "no_providers"
        
        if validation_results["enabled_count"] == 0:
            return "no_enabled_providers"
        
        healthy_count = validation_results.get("healthy_count", 0)
        if healthy_count == 0:
            return "no_healthy_providers"
        
        # Check for authentication issues
        auth_results = validation_results.get("authentication", {})
        invalid_count = auth_results.get("invalid_count", 0)
        error_count = auth_results.get("error_count", 0)
        
        # Check for configuration issues
        config_issues = validation_results.get("configuration_issues", [])
        
        # Determine status based on issues
        if invalid_count > 0 or len(config_issues) > 0:
            if healthy_count >= validation_results["enabled_count"] // 2:
                return "degraded"  # Some issues but majority working
            else:
                return "unhealthy"  # Major issues
        
        if error_count > 0:
            return "degraded"  # Network/validation errors but providers may work
        
        if healthy_count == validation_results["enabled_count"]:
            return "healthy"  # All providers healthy
        else:
            return "degraded"  # Some providers not healthy
    
    def get_user_friendly_status_message(self, validation_results: Dict[str, Any]) -> str:
        """Get user-friendly status message"""
        status = validation_results["overall_status"]
        
        status_messages = {
            "healthy": "All LLM providers are configured and working correctly.",
            "degraded": "Some LLM providers have issues but the system is functional.",
            "unhealthy": "Multiple LLM providers have issues. AI features may be limited.",
            "no_healthy_providers": "No LLM providers are currently available. AI features are disabled.",
            "no_enabled_providers": "No LLM providers are enabled. Enable providers to use AI features.",
            "no_providers": "No LLM providers are configured. Add providers to enable AI features.",
            "error": "An error occurred during validation. Check logs for details."
        }
        
        return status_messages.get(status, "Unknown status")
    
    def get_setup_instructions(self, validation_results: Dict[str, Any]) -> List[str]:
        """Get setup instructions based on validation results"""
        status = validation_results["overall_status"]
        
        if status == "no_providers":
            return [
                "1. Configure at least one LLM provider (OpenAI, Gemini, DeepSeek, etc.)",
                "2. Set up API keys for external providers",
                "3. Enable the provider in configuration",
                "4. Restart the application"
            ]
        
        elif status == "no_enabled_providers":
            return [
                "1. Enable at least one LLM provider in the configuration",
                "2. Ensure API keys are configured for external providers",
                "3. Restart the application or reload configuration"
            ]
        
        elif status in ["no_healthy_providers", "unhealthy"]:
            instructions = ["Check the following issues:"]
            
            # Add specific issues from recommendations
            recommendations = validation_results.get("recommendations", [])
            for i, rec in enumerate(recommendations[:5], 1):  # Limit to 5 recommendations
                instructions.append(f"{i}. {rec}")
            
            return instructions
        
        elif status == "degraded":
            return [
                "Some providers have issues but the system is functional:",
                "1. Review the recommendations below",
                "2. Fix authentication or configuration issues",
                "3. Check network connectivity for failing providers"
            ]
        
        else:  # healthy
            return [
                "System is configured correctly!",
                "All LLM providers are healthy and ready to use."
            ]


# Global instance
_startup_validation_service: Optional[StartupValidationService] = None


def get_startup_validation_service() -> StartupValidationService:
    """Get the global startup validation service instance"""
    global _startup_validation_service
    if _startup_validation_service is None:
        _startup_validation_service = StartupValidationService()
    return _startup_validation_service


async def validate_providers_on_startup() -> Dict[str, Any]:
    """Convenience function to run startup validation"""
    service = get_startup_validation_service()
    return await service.validate_startup()