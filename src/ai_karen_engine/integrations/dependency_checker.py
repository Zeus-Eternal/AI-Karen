"""
Dependency Checker and Installation Guidance

This module provides comprehensive dependency checking for each provider type,
missing dependency detection, installation guidance generation, and fallback
provider suggestions when dependencies are missing.
"""

import importlib
import logging
import os
import platform
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


@dataclass
class DependencyInfo:
    """Information about a dependency."""
    name: str
    import_name: str
    version_required: Optional[str] = None
    version_installed: Optional[str] = None
    is_available: bool = False
    install_command: str = ""
    alternative_packages: List[str] = field(default_factory=list)
    description: str = ""
    optional: bool = False


@dataclass
class ProviderDependencyStatus:
    """Dependency status for a provider."""
    provider_name: str
    all_dependencies_met: bool
    required_dependencies: List[DependencyInfo] = field(default_factory=list)
    optional_dependencies: List[DependencyInfo] = field(default_factory=list)
    missing_required: List[str] = field(default_factory=list)
    missing_optional: List[str] = field(default_factory=list)
    installation_guide: str = ""
    fallback_suggestions: List[str] = field(default_factory=list)


@dataclass
class SystemDependencyReport:
    """System-wide dependency report."""
    overall_status: str  # complete, partial, minimal, none
    provider_status: Dict[str, ProviderDependencyStatus] = field(default_factory=dict)
    system_info: Dict[str, Any] = field(default_factory=dict)
    global_recommendations: List[str] = field(default_factory=list)
    quick_setup_commands: List[str] = field(default_factory=list)


class DependencyChecker:
    """Comprehensive dependency checker for provider system."""
    
    def __init__(self, registry=None):
        """Initialize dependency checker."""
        self.registry = registry
        self._dependency_cache: Dict[str, DependencyInfo] = {}
        
        # Provider dependency specifications
        self._provider_dependencies = {
            "openai": {
                "required": [
                    DependencyInfo(
                        name="openai",
                        import_name="openai",
                        version_required=">=1.0.0",
                        install_command="pip install openai",
                        description="OpenAI Python client library"
                    ),
                    DependencyInfo(
                        name="requests",
                        import_name="requests",
                        install_command="pip install requests",
                        description="HTTP library for API calls"
                    ),
                ],
                "optional": [
                    DependencyInfo(
                        name="tiktoken",
                        import_name="tiktoken",
                        install_command="pip install tiktoken",
                        description="Token counting for OpenAI models",
                        optional=True
                    ),
                ]
            },
            "gemini": {
                "required": [
                    DependencyInfo(
                        name="google-generativeai",
                        import_name="google.generativeai",
                        version_required=">=0.3.0",
                        install_command="pip install google-generativeai",
                        description="Google Generative AI Python client"
                    ),
                ],
                "optional": []
            },
            "deepseek": {
                "required": [
                    DependencyInfo(
                        name="openai",
                        import_name="openai",
                        version_required=">=1.0.0",
                        install_command="pip install openai",
                        description="OpenAI-compatible client for DeepSeek API"
                    ),
                ],
                "optional": []
            },
            "huggingface": {
                "required": [
                    DependencyInfo(
                        name="transformers",
                        import_name="transformers",
                        version_required=">=4.20.0",
                        install_command="pip install transformers",
                        description="HuggingFace Transformers library"
                    ),
                    DependencyInfo(
                        name="torch",
                        import_name="torch",
                        version_required=">=1.9.0",
                        install_command="pip install torch",
                        alternative_packages=["torch-cpu", "torch-cuda"],
                        description="PyTorch deep learning framework"
                    ),
                ],
                "optional": [
                    DependencyInfo(
                        name="accelerate",
                        import_name="accelerate",
                        install_command="pip install accelerate",
                        description="Accelerated training and inference",
                        optional=True
                    ),
                    DependencyInfo(
                        name="bitsandbytes",
                        import_name="bitsandbytes",
                        install_command="pip install bitsandbytes",
                        description="8-bit and 4-bit quantization",
                        optional=True
                    ),
                ]
            },
            "local": {
                "required": [
                    DependencyInfo(
                        name="llama-cpp-python",
                        import_name="llama_cpp",
                        version_required=">=0.2.0",
                        install_command="pip install llama-cpp-python",
                        description="Python bindings for llama.cpp"
                    ),
                ],
                "optional": [
                    DependencyInfo(
                        name="numpy",
                        import_name="numpy",
                        install_command="pip install numpy",
                        description="Numerical computing library",
                        optional=True
                    ),
                ]
            },
            "superkent": {
                "required": [
                    DependencyInfo(
                        name="requests",
                        import_name="requests",
                        install_command="pip install requests",
                        description="HTTP client for SuperKent server"
                    ),
                ],
                "optional": []
            },
        }
        
        # Fallback provider hierarchy
        self._fallback_hierarchy = {
            "openai": ["gemini", "deepseek", "huggingface", "local"],
            "gemini": ["openai", "deepseek", "huggingface", "local"],
            "deepseek": ["openai", "gemini", "huggingface", "local"],
            "huggingface": ["local", "superkent"],
            "local": ["superkent", "huggingface"],
            "superkent": ["local", "huggingface"],
        }
    
    def check_all_dependencies(self) -> SystemDependencyReport:
        """Check dependencies for all providers and generate comprehensive report."""
        logger.info("Starting comprehensive dependency check...")
        
        report = SystemDependencyReport(overall_status="none")
        report.system_info = self._get_system_info()
        
        if not self.registry:
            report.global_recommendations.append("No registry available for dependency checking")
            return report
        
        # Check each provider
        providers = self.registry.list_providers()
        fully_ready_count = 0
        partially_ready_count = 0
        
        for provider_name in providers:
            try:
                status = self.check_provider_dependencies(provider_name)
                report.provider_status[provider_name] = status
                
                if status.all_dependencies_met:
                    fully_ready_count += 1
                elif len(status.missing_required) < len(status.required_dependencies):
                    partially_ready_count += 1
                    
            except Exception as e:
                logger.error(f"Error checking dependencies for {provider_name}: {e}")
                report.provider_status[provider_name] = ProviderDependencyStatus(
                    provider_name=provider_name,
                    all_dependencies_met=False,
                    installation_guide=f"Error checking dependencies: {str(e)}"
                )
        
        # Determine overall status
        total_providers = len(providers)
        if fully_ready_count >= 2:
            report.overall_status = "complete"
        elif fully_ready_count >= 1 or partially_ready_count >= 2:
            report.overall_status = "partial"
        elif partially_ready_count >= 1:
            report.overall_status = "minimal"
        else:
            report.overall_status = "none"
        
        # Generate global recommendations
        report.global_recommendations = self._generate_global_recommendations(report)
        report.quick_setup_commands = self._generate_quick_setup_commands(report)
        
        logger.info(f"Dependency check complete: {report.overall_status} ({fully_ready_count}/{total_providers} providers ready)")
        return report
    
    def check_provider_dependencies(self, provider_name: str) -> ProviderDependencyStatus:
        """Check dependencies for a specific provider."""
        status = ProviderDependencyStatus(
            provider_name=provider_name,
            all_dependencies_met=False
        )
        
        # Get provider dependency specification
        provider_deps = self._provider_dependencies.get(provider_name, {"required": [], "optional": []})
        
        # Check required dependencies
        for dep_info in provider_deps["required"]:
            checked_dep = self._check_dependency_detailed(dep_info)
            status.required_dependencies.append(checked_dep)
            
            if not checked_dep.is_available:
                status.missing_required.append(checked_dep.name)
        
        # Check optional dependencies
        for dep_info in provider_deps["optional"]:
            checked_dep = self._check_dependency_detailed(dep_info)
            status.optional_dependencies.append(checked_dep)
            
            if not checked_dep.is_available:
                status.missing_optional.append(checked_dep.name)
        
        # Determine if all required dependencies are met
        status.all_dependencies_met = len(status.missing_required) == 0
        
        # Generate installation guide
        status.installation_guide = self._generate_installation_guide(status)
        
        # Generate fallback suggestions
        status.fallback_suggestions = self._generate_fallback_suggestions(provider_name, status)
        
        return status
    
    def _check_dependency_detailed(self, dep_info: DependencyInfo) -> DependencyInfo:
        """Check a dependency and return detailed information."""
        # Use cache if available
        cache_key = f"{dep_info.name}:{dep_info.import_name}"
        if cache_key in self._dependency_cache:
            return self._dependency_cache[cache_key]
        
        # Create a copy to avoid modifying the original
        result = DependencyInfo(
            name=dep_info.name,
            import_name=dep_info.import_name,
            version_required=dep_info.version_required,
            install_command=dep_info.install_command,
            alternative_packages=dep_info.alternative_packages,
            description=dep_info.description,
            optional=dep_info.optional
        )
        
        try:
            # Try to import the module
            module = importlib.import_module(dep_info.import_name)
            result.is_available = True
            
            # Try to get version
            result.version_installed = self._get_package_version(dep_info.name, module)
            
        except ImportError:
            result.is_available = False
            result.version_installed = None
        
        # Cache the result
        self._dependency_cache[cache_key] = result
        return result
    
    def _get_package_version(self, package_name: str, module=None) -> str:
        """Get version of an installed package."""
        try:
            import pkg_resources
            return pkg_resources.get_distribution(package_name).version
        except Exception:
            if module:
                return getattr(module, '__version__', 'unknown')
            return 'unknown'
    
    def _generate_installation_guide(self, status: ProviderDependencyStatus) -> str:
        """Generate installation guide for a provider."""
        if status.all_dependencies_met:
            return f"✓ All dependencies for {status.provider_name} are satisfied."
        
        guide_lines = [f"Installation guide for {status.provider_name}:"]
        
        if status.missing_required:
            guide_lines.append("\nRequired dependencies:")
            for dep in status.required_dependencies:
                if not dep.is_available:
                    guide_lines.append(f"  • {dep.name}: {dep.description}")
                    guide_lines.append(f"    Install: {dep.install_command}")
                    if dep.alternative_packages:
                        guide_lines.append(f"    Alternatives: {', '.join(dep.alternative_packages)}")
        
        if status.missing_optional:
            guide_lines.append("\nOptional dependencies (recommended):")
            for dep in status.optional_dependencies:
                if not dep.is_available:
                    guide_lines.append(f"  • {dep.name}: {dep.description}")
                    guide_lines.append(f"    Install: {dep.install_command}")
        
        # Add system-specific notes
        system_notes = self._get_system_specific_notes(status.provider_name)
        if system_notes:
            guide_lines.append(f"\nSystem-specific notes:")
            guide_lines.extend([f"  • {note}" for note in system_notes])
        
        return "\n".join(guide_lines)
    
    def _generate_fallback_suggestions(self, provider_name: str, status: ProviderDependencyStatus) -> List[str]:
        """Generate fallback provider suggestions when dependencies are missing."""
        if status.all_dependencies_met:
            return []
        
        suggestions = []
        fallback_providers = self._fallback_hierarchy.get(provider_name, [])
        
        for fallback in fallback_providers:
            if self.registry and fallback in self.registry.list_providers():
                fallback_status = self.check_provider_dependencies(fallback)
                if fallback_status.all_dependencies_met:
                    suggestions.append(f"Use {fallback} as alternative (dependencies satisfied)")
                elif len(fallback_status.missing_required) < len(status.missing_required):
                    suggestions.append(f"Consider {fallback} (fewer missing dependencies)")
        
        if not suggestions:
            suggestions.append("Consider using local providers or installing missing dependencies")
        
        return suggestions
    
    def _get_system_specific_notes(self, provider_name: str) -> List[str]:
        """Get system-specific installation notes."""
        notes = []
        system = platform.system().lower()
        
        if provider_name == "huggingface":
            if system == "darwin":  # macOS
                notes.append("On macOS, you may need: pip install torch torchvision torchaudio")
            elif system == "linux":
                notes.append("On Linux with CUDA: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
            elif system == "windows":
                notes.append("On Windows: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
        
        elif provider_name == "local":
            if system == "darwin":
                notes.append("On macOS with Apple Silicon: CMAKE_ARGS='-DLLAMA_METAL=on' pip install llama-cpp-python")
            elif system == "linux":
                notes.append("On Linux with CUDA: CMAKE_ARGS='-DLLAMA_CUBLAS=on' pip install llama-cpp-python")
        
        return notes
    
    def _generate_global_recommendations(self, report: SystemDependencyReport) -> List[str]:
        """Generate global recommendations based on dependency report."""
        recommendations = []
        
        if report.overall_status == "none":
            recommendations.extend([
                "No providers have their dependencies satisfied",
                "Start by installing dependencies for at least one provider",
                "Recommended: Set up OpenAI (easiest) or local provider (most private)"
            ])
        
        elif report.overall_status == "minimal":
            recommendations.extend([
                "Only basic functionality available",
                "Install dependencies for additional providers to improve reliability",
                "Consider setting up both cloud and local providers for redundancy"
            ])
        
        elif report.overall_status == "partial":
            recommendations.extend([
                "Good provider coverage, but some providers unavailable",
                "Install remaining dependencies for full functionality",
                "Current setup should handle most use cases"
            ])
        
        # Provider-specific recommendations
        cloud_providers = ["openai", "gemini", "deepseek"]
        local_providers = ["huggingface", "local", "superkent"]
        
        ready_cloud = sum(1 for p in cloud_providers if report.provider_status.get(p, {}).all_dependencies_met)
        ready_local = sum(1 for p in local_providers if report.provider_status.get(p, {}).all_dependencies_met)
        
        if ready_cloud == 0:
            recommendations.append("Consider setting up at least one cloud provider for best performance")
        
        if ready_local == 0:
            recommendations.append("Consider setting up local providers for privacy and offline usage")
        
        return recommendations
    
    def _generate_quick_setup_commands(self, report: SystemDependencyReport) -> List[str]:
        """Generate quick setup commands for common scenarios."""
        commands = []
        
        # Find the provider with fewest missing dependencies
        best_provider = None
        min_missing = float('inf')
        
        for provider_name, status in report.provider_status.items():
            if not status.all_dependencies_met:
                missing_count = len(status.missing_required)
                if missing_count < min_missing:
                    min_missing = missing_count
                    best_provider = provider_name
        
        if best_provider and min_missing < 3:
            status = report.provider_status[best_provider]
            install_commands = []
            for dep in status.required_dependencies:
                if not dep.is_available:
                    install_commands.append(dep.install_command)
            
            if install_commands:
                commands.append(f"# Quick setup for {best_provider}:")
                commands.extend(install_commands)
        
        # Add common setup scenarios
        commands.extend([
            "",
            "# Common setup scenarios:",
            "# For OpenAI only:",
            "pip install openai",
            "",
            "# For local models:",
            "pip install llama-cpp-python",
            "",
            "# For HuggingFace models:",
            "pip install transformers torch",
            "",
            "# For comprehensive setup:",
            "pip install openai google-generativeai transformers torch llama-cpp-python"
        ])
        
        return commands
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information relevant to dependency installation."""
        return {
            "platform": platform.platform(),
            "python_version": sys.version,
            "architecture": platform.architecture()[0],
            "processor": platform.processor(),
            "system": platform.system(),
            "pip_version": self._get_pip_version(),
        }
    
    def _get_pip_version(self) -> str:
        """Get pip version."""
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "--version"], 
                                  capture_output=True, text=True, timeout=5)
            return result.stdout.strip() if result.returncode == 0 else "unknown"
        except Exception:
            return "unknown"
    
    def install_missing_dependencies(self, provider_name: str, include_optional: bool = False) -> bool:
        """Attempt to install missing dependencies for a provider."""
        logger.info(f"Attempting to install dependencies for {provider_name}...")
        
        status = self.check_provider_dependencies(provider_name)
        
        dependencies_to_install = []
        for dep in status.required_dependencies:
            if not dep.is_available:
                dependencies_to_install.append(dep)
        
        if include_optional:
            for dep in status.optional_dependencies:
                if not dep.is_available:
                    dependencies_to_install.append(dep)
        
        if not dependencies_to_install:
            logger.info(f"All dependencies for {provider_name} are already satisfied")
            return True
        
        success = True
        for dep in dependencies_to_install:
            try:
                logger.info(f"Installing {dep.name}...")
                result = subprocess.run(
                    dep.install_command.split(),
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                
                if result.returncode == 0:
                    logger.info(f"✓ Successfully installed {dep.name}")
                    # Clear cache for this dependency
                    cache_key = f"{dep.name}:{dep.import_name}"
                    self._dependency_cache.pop(cache_key, None)
                else:
                    logger.error(f"✗ Failed to install {dep.name}: {result.stderr}")
                    success = False
                    
            except subprocess.TimeoutExpired:
                logger.error(f"✗ Timeout installing {dep.name}")
                success = False
            except Exception as e:
                logger.error(f"✗ Error installing {dep.name}: {e}")
                success = False
        
        return success


def check_system_dependencies(registry=None) -> SystemDependencyReport:
    """Convenience function to check all system dependencies."""
    checker = DependencyChecker(registry)
    return checker.check_all_dependencies()


def check_provider_dependencies(provider_name: str, registry=None) -> ProviderDependencyStatus:
    """Convenience function to check dependencies for a specific provider."""
    checker = DependencyChecker(registry)
    return checker.check_provider_dependencies(provider_name)


def install_provider_dependencies(provider_name: str, registry=None, include_optional: bool = False) -> bool:
    """Convenience function to install dependencies for a provider."""
    checker = DependencyChecker(registry)
    return checker.install_missing_dependencies(provider_name, include_optional)


__all__ = [
    "DependencyChecker",
    "DependencyInfo",
    "ProviderDependencyStatus",
    "SystemDependencyReport",
    "check_system_dependencies",
    "check_provider_dependencies",
    "install_provider_dependencies",
]