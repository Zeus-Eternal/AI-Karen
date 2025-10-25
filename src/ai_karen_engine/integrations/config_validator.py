"""
Configuration Validator for Provider System

This module provides comprehensive validation of provider configurations at startup,
including environment variable checking, dependency verification, and API endpoint testing.
"""

import asyncio
import importlib
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import requests
import socket
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


@dataclass
class SystemValidationResult:
    """Result of system-wide validation."""
    overall_status: str  # healthy, degraded, critical
    provider_results: Dict[str, 'ProviderValidationResult'] = field(default_factory=dict)
    critical_issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    validation_time: float = 0.0


@dataclass
class ProviderValidationResult:
    """Result of provider-specific validation."""
    provider_name: str
    valid: bool
    env_var_status: 'EnvVarCheckResult'
    dependency_status: 'DependencyCheckResult'
    endpoint_status: 'EndpointTestResult'
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class EnvVarCheckResult:
    """Result of environment variable checking."""
    all_present: bool
    missing_vars: List[str] = field(default_factory=list)
    present_vars: List[str] = field(default_factory=list)
    invalid_vars: Dict[str, str] = field(default_factory=dict)  # var -> reason


@dataclass
class DependencyCheckResult:
    """Result of dependency checking."""
    all_available: bool
    missing_dependencies: List[str] = field(default_factory=list)
    available_dependencies: List[str] = field(default_factory=list)
    version_info: Dict[str, str] = field(default_factory=dict)
    installation_commands: Dict[str, str] = field(default_factory=dict)


@dataclass
class EndpointTestResult:
    """Result of API endpoint testing."""
    reachable: bool
    response_time: Optional[float] = None
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    ssl_valid: bool = True
    dns_resolved: bool = True
    network_accessible: bool = True


class ConfigurationValidator:
    """Comprehensive configuration validator for provider system."""
    
    def __init__(self, registry=None):
        """Initialize validator with optional registry reference."""
        self.registry = registry
        self._dependency_cache: Dict[str, bool] = {}
        self._endpoint_cache: Dict[str, EndpointTestResult] = {}
        
        # Common API endpoints for providers
        self._provider_endpoints = {
            "openai": "https://api.openai.com/v1/models",
            "gemini": "https://generativelanguage.googleapis.com/v1/models",
            "deepseek": "https://api.deepseek.com/v1/models",
            "huggingface": "https://huggingface.co/api/models",
        }
        
        # Installation commands for common dependencies
        self._install_commands = {
            "openai": "pip install openai",
            "google-generativeai": "pip install google-generativeai",
            "transformers": "pip install transformers",
            "torch": "pip install torch",
            "llama-cpp-python": "pip install llama-cpp-python",
            "requests": "pip install requests",
            "numpy": "pip install numpy",
            "scipy": "pip install scipy",
            "scikit-learn": "pip install scikit-learn",
        }
    
    def validate_all_configurations(self) -> SystemValidationResult:
        """Validate all provider configurations at startup."""
        logger.info("Starting comprehensive system configuration validation...")
        start_time = time.time()
        
        result = SystemValidationResult(overall_status="healthy")
        
        if not self.registry:
            result.overall_status = "critical"
            result.critical_issues.append("No registry provided for validation")
            return result
        
        # Validate each provider
        providers = self.registry.list_providers()
        healthy_count = 0
        
        for provider_name in providers:
            try:
                provider_result = self.validate_provider_config(provider_name)
                result.provider_results[provider_name] = provider_result
                
                if provider_result.valid:
                    healthy_count += 1
                else:
                    result.critical_issues.extend([
                        f"{provider_name}: {issue}" for issue in provider_result.issues
                    ])
                    result.warnings.extend([
                        f"{provider_name}: {warning}" for warning in provider_result.warnings
                    ])
                    result.recommendations.extend([
                        f"{provider_name}: {rec}" for rec in provider_result.recommendations
                    ])
                    
            except Exception as e:
                logger.error(f"Error validating provider {provider_name}: {e}")
                result.critical_issues.append(f"Validation error for {provider_name}: {str(e)}")
        
        # Determine overall status
        if healthy_count == 0:
            result.overall_status = "critical"
            result.critical_issues.append("No providers are properly configured")
        elif healthy_count < len(providers) / 2:
            result.overall_status = "degraded"
            result.warnings.append(f"Only {healthy_count}/{len(providers)} providers are healthy")
        else:
            result.overall_status = "healthy"
        
        result.validation_time = time.time() - start_time
        
        # Add system-level recommendations
        if result.overall_status != "healthy":
            result.recommendations.extend(self._generate_system_recommendations(result))
        
        logger.info(f"Configuration validation complete in {result.validation_time:.2f}s: {result.overall_status}")
        return result
    
    def validate_provider_config(self, provider_name: str) -> ProviderValidationResult:
        """Validate configuration for a specific provider."""
        if not self.registry:
            return ProviderValidationResult(
                provider_name=provider_name,
                valid=False,
                env_var_status=EnvVarCheckResult(all_present=False),
                dependency_status=DependencyCheckResult(all_available=False),
                endpoint_status=EndpointTestResult(reachable=False),
                issues=["No registry available for validation"]
            )
        
        spec = self.registry.get_provider_spec(provider_name)
        if not spec:
            return ProviderValidationResult(
                provider_name=provider_name,
                valid=False,
                env_var_status=EnvVarCheckResult(all_present=False),
                dependency_status=DependencyCheckResult(all_available=False),
                endpoint_status=EndpointTestResult(reachable=False),
                issues=[f"Provider '{provider_name}' not found in registry"]
            )
        
        logger.debug(f"Validating configuration for provider: {provider_name}")
        
        # Check environment variables
        env_result = self.check_environment_variables(provider_name)
        
        # Check dependencies
        dep_result = self.verify_dependencies(provider_name)
        
        # Test API endpoints
        endpoint_result = self.test_api_endpoints(provider_name)
        
        # Determine overall validity
        valid = env_result.all_present and dep_result.all_available
        
        # Collect issues and warnings
        issues = []
        warnings = []
        recommendations = []
        
        if not env_result.all_present:
            issues.extend([f"Missing environment variable: {var}" for var in env_result.missing_vars])
            recommendations.extend([f"Set environment variable: {var}" for var in env_result.missing_vars])
        
        if not dep_result.all_available:
            issues.extend([f"Missing dependency: {dep}" for dep in dep_result.missing_dependencies])
            recommendations.extend([
                f"Install dependency: {dep_result.installation_commands.get(dep, f'pip install {dep}')}"
                for dep in dep_result.missing_dependencies
            ])
        
        if not endpoint_result.reachable and spec.requires_api_key:
            warnings.append(f"API endpoint not reachable: {endpoint_result.error_message}")
            if not endpoint_result.dns_resolved:
                recommendations.append("Check DNS resolution and internet connectivity")
            elif not endpoint_result.network_accessible:
                recommendations.append("Check firewall and proxy settings")
        
        return ProviderValidationResult(
            provider_name=provider_name,
            valid=valid,
            env_var_status=env_result,
            dependency_status=dep_result,
            endpoint_status=endpoint_result,
            issues=issues,
            warnings=warnings,
            recommendations=recommendations
        )
    
    def check_environment_variables(self, provider_name: str) -> EnvVarCheckResult:
        """Check required environment variables for a provider."""
        if not self.registry:
            return EnvVarCheckResult(all_present=False)
        
        spec = self.registry.get_provider_spec(provider_name)
        if not spec:
            return EnvVarCheckResult(all_present=False)
        
        missing_vars = []
        present_vars = []
        invalid_vars = {}
        
        for env_var in spec.required_env_vars:
            value = os.getenv(env_var)
            if not value:
                missing_vars.append(env_var)
            else:
                present_vars.append(env_var)
                
                # Validate API key format
                if "api_key" in env_var.lower() or "key" in env_var.lower():
                    validation_error = self._validate_api_key_format(provider_name, value)
                    if validation_error:
                        invalid_vars[env_var] = validation_error
        
        return EnvVarCheckResult(
            all_present=len(missing_vars) == 0,
            missing_vars=missing_vars,
            present_vars=present_vars,
            invalid_vars=invalid_vars
        )
    
    def verify_dependencies(self, provider_name: str) -> DependencyCheckResult:
        """Verify all required dependencies are available."""
        if not self.registry:
            return DependencyCheckResult(all_available=False)
        
        spec = self.registry.get_provider_spec(provider_name)
        if not spec:
            return DependencyCheckResult(all_available=False)
        
        missing_deps = []
        available_deps = []
        version_info = {}
        install_commands = {}
        
        for dep in spec.required_dependencies:
            if dep in self._dependency_cache:
                is_available = self._dependency_cache[dep]
            else:
                is_available = self._check_dependency(dep)
                self._dependency_cache[dep] = is_available
            
            if is_available:
                available_deps.append(dep)
                version_info[dep] = self._get_package_version(dep)
            else:
                missing_deps.append(dep)
                install_commands[dep] = self._install_commands.get(dep, f"pip install {dep}")
        
        return DependencyCheckResult(
            all_available=len(missing_deps) == 0,
            missing_dependencies=missing_deps,
            available_dependencies=available_deps,
            version_info=version_info,
            installation_commands=install_commands
        )
    
    def test_api_endpoints(self, provider_name: str) -> EndpointTestResult:
        """Test API endpoint connectivity and authentication."""
        endpoint_url = self._provider_endpoints.get(provider_name)
        if not endpoint_url:
            return EndpointTestResult(reachable=True)  # No endpoint to test
        
        # Check cache first
        if endpoint_url in self._endpoint_cache:
            cached_result = self._endpoint_cache[endpoint_url]
            # Use cached result if it's less than 5 minutes old
            if hasattr(cached_result, 'timestamp') and time.time() - cached_result.timestamp < 300:
                return cached_result
        
        logger.debug(f"Testing API endpoint for {provider_name}: {endpoint_url}")
        
        result = EndpointTestResult(reachable=False)
        start_time = time.time()
        
        try:
            # Parse URL for DNS testing
            parsed_url = urlparse(endpoint_url)
            hostname = parsed_url.hostname
            
            # Test DNS resolution
            try:
                socket.gethostbyname(hostname)
                result.dns_resolved = True
            except socket.gaierror:
                result.dns_resolved = False
                result.error_message = f"DNS resolution failed for {hostname}"
                result.network_accessible = False
                return result
            
            # Test network connectivity
            try:
                response = requests.get(
                    endpoint_url,
                    timeout=10,
                    headers={"User-Agent": "AI-Karen-Config-Validator/1.0"}
                )
                result.network_accessible = True
                result.status_code = response.status_code
                result.response_time = time.time() - start_time
                
                # Consider 2xx, 401, 403 as "reachable" (endpoint exists)
                if response.status_code in [200, 401, 403]:
                    result.reachable = True
                else:
                    result.error_message = f"HTTP {response.status_code}"
                    
            except requests.exceptions.SSLError as e:
                result.ssl_valid = False
                result.error_message = f"SSL error: {str(e)}"
                result.network_accessible = True
                
            except requests.exceptions.ConnectionError as e:
                result.network_accessible = False
                result.error_message = f"Connection error: {str(e)}"
                
            except requests.exceptions.Timeout:
                result.network_accessible = True
                result.error_message = "Request timeout"
                
            except requests.exceptions.RequestException as e:
                result.error_message = f"Request error: {str(e)}"
        
        except Exception as e:
            result.error_message = f"Unexpected error: {str(e)}"
        
        # Cache result
        result.timestamp = time.time()
        self._endpoint_cache[endpoint_url] = result
        
        return result
    
    def _check_dependency(self, dependency: str) -> bool:
        """Check if a dependency is available."""
        try:
            importlib.import_module(dependency)
            return True
        except ImportError:
            # Try alternative import names
            alt_names = {
                "google-generativeai": "google.generativeai",
                "llama-cpp-python": "llama_cpp",
                "scikit-learn": "sklearn",
            }
            
            alt_name = alt_names.get(dependency)
            if alt_name:
                try:
                    importlib.import_module(alt_name)
                    return True
                except ImportError:
                    pass
            
            return False
    
    def _get_package_version(self, package: str) -> str:
        """Get version of an installed package."""
        try:
            import pkg_resources
            return pkg_resources.get_distribution(package).version
        except Exception:
            try:
                module = importlib.import_module(package)
                return getattr(module, '__version__', 'unknown')
            except Exception:
                return 'unknown'
    
    def _validate_api_key_format(self, provider_name: str, api_key: str) -> Optional[str]:
        """Validate API key format for specific providers."""
        if not api_key:
            return "API key is empty"
        
        if provider_name == "openai":
            if not api_key.startswith("sk-"):
                return "OpenAI API keys should start with 'sk-'"
            if len(api_key) < 20:
                return "OpenAI API key appears too short"
        
        elif provider_name == "gemini":
            if len(api_key) < 20:
                return "Gemini API key appears too short"
        
        elif provider_name == "deepseek":
            if len(api_key) < 20:
                return "DeepSeek API key appears too short"
        
        elif provider_name == "huggingface":
            if api_key and not api_key.startswith("hf_"):
                return "HuggingFace tokens should start with 'hf_'"
        
        return None
    
    def _generate_system_recommendations(self, result: SystemValidationResult) -> List[str]:
        """Generate system-level recommendations based on validation results."""
        recommendations = []
        
        # Count issues by type
        missing_deps = set()
        missing_env_vars = set()
        
        for provider_result in result.provider_results.values():
            missing_deps.update(provider_result.dependency_status.missing_dependencies)
            missing_env_vars.update(provider_result.env_var_status.missing_vars)
        
        if missing_deps:
            recommendations.append(f"Install missing dependencies: {', '.join(sorted(missing_deps))}")
        
        if missing_env_vars:
            recommendations.append(f"Set missing environment variables: {', '.join(sorted(missing_env_vars))}")
        
        # Provider-specific recommendations
        healthy_providers = [name for name, res in result.provider_results.items() if res.valid]
        if not healthy_providers:
            recommendations.append("Consider setting up at least one cloud provider (OpenAI, Gemini, or DeepSeek)")
            recommendations.append("Alternatively, set up local providers (HuggingFace, local models)")
        
        return recommendations


def validate_system_configuration(registry=None) -> SystemValidationResult:
    """Convenience function to validate system configuration."""
    validator = ConfigurationValidator(registry)
    return validator.validate_all_configurations()


def validate_provider_configuration(provider_name: str, registry=None) -> ProviderValidationResult:
    """Convenience function to validate a specific provider."""
    validator = ConfigurationValidator(registry)
    return validator.validate_provider_config(provider_name)


__all__ = [
    "ConfigurationValidator",
    "SystemValidationResult",
    "ProviderValidationResult",
    "EnvVarCheckResult",
    "DependencyCheckResult",
    "EndpointTestResult",
    "validate_system_configuration",
    "validate_provider_configuration",
]