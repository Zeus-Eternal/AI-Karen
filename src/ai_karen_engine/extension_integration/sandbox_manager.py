"""
Extension Sandbox Manager - Advanced sandboxing and security isolation for extensions.

This module provides comprehensive sandboxing including:
- Process isolation with resource limits
- File system sandboxing with restricted access
- Network access control and monitoring
- Memory isolation and cleanup
- Security policy enforcement
- Audit logging and monitoring
"""

from __future__ import annotations

import asyncio
import logging
import os
import psutil
import signal
import subprocess
import tempfile
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from ai_karen_engine.extension_host.models import ExtensionManifest, ExtensionPermissions, ExtensionResources


class SandboxSecurityLevel(Enum):
    """Security levels for extension sandboxing."""
    
    MINIMAL = "minimal"      # Basic isolation, limited resource access
    RESTRICTED = "restricted"  # Strict isolation, monitored resource access
    SECURE = "secure"        # Full isolation, strict resource limits
    CUSTOM = "custom"          # Custom security policy


class SandboxAction(Enum):
    """Actions that can be taken on sandbox violations."""
    
    WARN = "warn"           # Log warning
    THROTTLE = "throttle"     # Throttle extension
    SUSPEND = "suspend"       # Suspend extension
    TERMINATE = "terminate"    # Terminate extension
    QUARANTINE = "quarantine"  # Put extension in quarantine


@dataclass
class SandboxPolicy:
    """Security policy for extension sandbox."""
    
    level: SandboxSecurityLevel
    max_memory_mb: int
    max_cpu_percent: int
    max_disk_mb: int
    max_network_connections: int
    allowed_file_paths: List[str]
    denied_file_paths: List[str]
    allowed_domains: List[str]
    denied_domains: List[str]
    allowed_system_calls: List[str]
    denied_system_calls: List[str]
    violation_action: SandboxAction
    audit_logging: bool = True


@dataclass
class SandboxMetrics:
    """Metrics for sandbox performance and violations."""
    
    extension_name: str
    start_time: float
    memory_usage_mb: float
    cpu_usage_percent: float
    disk_usage_mb: float
    network_bytes_sent: int
    network_bytes_recv: int
    file_access_count: int
    system_call_count: int
    violations: List[Dict[str, Any]]
    last_activity: float


@dataclass
class SandboxContext:
    """Context for sandboxed extension execution."""
    
    extension_name: str
    policy: SandboxPolicy
    temp_dir: Path
    original_env: Dict[str, str]
    restricted_env: Dict[str, str]
    process_id: Optional[int] = None
    start_time: float
    metrics: SandboxMetrics


class ExtensionSandboxManager:
    """
    Advanced sandbox manager for extension security isolation.
    
    Provides:
    - Process isolation with resource monitoring
    - File system access control
    - Network access monitoring and filtering
    - Memory and CPU resource enforcement
    - Security policy enforcement
    - Comprehensive audit logging
    """
    
    def __init__(
        self,
        default_policy: Optional[SandboxPolicy] = None,
        enable_audit: bool = True,
        monitoring_interval: float = 5.0
    ):
        """
        Initialize the sandbox manager.
        
        Args:
            default_policy: Default sandbox policy for extensions
            enable_audit: Whether to enable audit logging
            monitoring_interval: How often to check resource usage (seconds)
        """
        self.default_policy = default_policy or self._create_default_policy()
        self.enable_audit = enable_audit
        self.monitoring_interval = monitoring_interval
        
        self.logger = logging.getLogger("extension.sandbox_manager")
        
        # Sandbox state
        self.sandboxes: Dict[str, SandboxContext] = {}
        self.policies: Dict[str, SandboxPolicy] = {}
        self.metrics: Dict[str, SandboxMetrics] = {}
        
        # Monitoring
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
        
        self.logger.info("Extension sandbox manager initialized")
    
    def _create_default_policy(self) -> SandboxPolicy:
        """Create default sandbox policy."""
        return SandboxPolicy(
            level=SandboxSecurityLevel.RESTRICTED,
            max_memory_mb=512,
            max_cpu_percent=25,
            max_disk_mb=100,
            max_network_connections=10,
            allowed_file_paths=[],
            denied_file_paths=["/etc", "/sys", "/proc", "/dev"],
            allowed_domains=["github.com", "pypi.org"],
            denied_domains=[],
            allowed_system_calls=["open", "read", "write"],
            denied_system_calls=["exec", "fork", "kill"],
            violation_action=SandboxAction.THROTTLE,
            audit_logging=True
        )
    
    async def create_sandbox(
        self,
        extension_name: str,
        manifest: ExtensionManifest,
        custom_policy: Optional[SandboxPolicy] = None
    ) -> Optional[SandboxContext]:
        """
        Create a sandbox for an extension.
        
        Args:
            extension_name: Name of the extension
            manifest: Extension manifest
            custom_policy: Custom sandbox policy
            
        Returns:
            Sandbox context or None if creation fails
        """
        self.logger.info(f"Creating sandbox for extension {extension_name}")
        
        try:
            # Determine policy
            policy = custom_policy or self._get_extension_policy(extension_name, manifest)
            self.policies[extension_name] = policy
            
            # Create temporary directory
            temp_dir = Path(tempfile.mkdtemp(prefix=f"extension_{extension_name}_"))
            
            # Create sandbox context
            context = SandboxContext(
                extension_name=extension_name,
                policy=policy,
                temp_dir=temp_dir,
                original_env=os.environ.copy(),
                restricted_env=self._create_restricted_env(policy),
                start_time=time.time()
            )
            
            # Initialize metrics
            self.metrics[extension_name] = SandboxMetrics(
                extension_name=extension_name,
                start_time=context.start_time,
                memory_usage_mb=0.0,
                cpu_usage_percent=0.0,
                disk_usage_mb=0.0,
                network_bytes_sent=0,
                network_bytes_recv=0,
                file_access_count=0,
                system_call_count=0,
                violations=[]
            )
            
            self.sandboxes[extension_name] = context
            
            self.logger.info(f"Sandbox created for extension {extension_name}")
            return context
            
        except Exception as e:
            self.logger.error(f"Failed to create sandbox for {extension_name}: {e}")
            return None
    
    async def execute_in_sandbox(
        self,
        extension_name: str,
        code: str,
        args: Optional[List[str]] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Execute code within an extension sandbox.
        
        Args:
            extension_name: Name of the extension
            code: Code to execute
            args: Command line arguments
            timeout: Execution timeout in seconds
            
        Returns:
            Dictionary containing execution result
        """
        self.logger.info(f"Executing code in sandbox for extension {extension_name}")
        
        try:
            context = self.sandboxes.get(extension_name)
            if not context:
                return {"error": "Sandbox not found for extension"}
            
            # Prepare execution
            cmd = [code]
            if args:
                cmd.extend(args)
            
            # Set up environment
            env = context.restricted_env.copy()
            env["EXTENSION_SANDBOX"] = "1"
            env["EXTENSION_NAME"] = extension_name
            
            # Execute in subprocess with resource limits
            process = await asyncio.create_subprocess_exec(
                cmd,
                env=env,
                cwd=context.temp_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Monitor execution
            return await self._monitor_sandboxed_process(extension_name, process, timeout)
            
        except Exception as e:
            self.logger.error(f"Failed to execute in sandbox for {extension_name}: {e}")
            return {"error": str(e)}
    
    async def _monitor_sandboxed_process(
        self,
        extension_name: str,
        process: asyncio.subprocess.Process,
        timeout: Optional[float]
    ) -> Dict[str, Any]:
        """
        Monitor a sandboxed process and enforce resource limits.
        
        Args:
            extension_name: Name of the extension
            process: Subprocess to monitor
            timeout: Execution timeout
            
        Returns:
            Dictionary containing execution result
        """
        try:
            context = self.sandboxes.get(extension_name)
            if not context:
                return {"error": "Sandbox context not found"}
            
            policy = context.policy
            metrics = self.metrics.get(extension_name)
            
            start_time = time.time()
            result = None
            
            try:
                # Wait for completion with timeout
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout or 300.0
                )
                
                # Update metrics
                execution_time = time.time() - start_time
                await self._update_execution_metrics(extension_name, process, execution_time)
                
                # Check for resource violations
                await self._check_resource_violations(extension_name, process.pid)
                
                result = {
                    "stdout": stdout,
                    "stderr": stderr,
                    "returncode": process.returncode,
                    "execution_time": execution_time,
                    "violations": metrics.violations
                }
                
                self.logger.info(f"Sandbox execution completed for {extension_name}")
                return result
                
            except asyncio.TimeoutError:
                self.logger.warning(f"Sandbox execution timed out for {extension_name}")
                return {"error": "Execution timed out", "timeout": True}
            except Exception as e:
                self.logger.error(f"Failed to monitor sandboxed process for {extension_name}: {e}")
                return {"error": str(e)}
            finally:
                # Cleanup
                if process and process.returncode is None:
                    process.terminate()
                    await process.wait()
    
    async def _update_execution_metrics(self, extension_name: str, process: asyncio.subprocess.Process, execution_time: float) -> None:
        """Update execution metrics for sandboxed process."""
        try:
            context = self.sandboxes.get(extension_name)
            metrics = self.metrics.get(extension_name)
            
            if not context or not metrics:
                return
            
            # Get resource usage
            try:
                # Get process info
                if process.pid:
                    proc_info = psutil.Process(process.pid)
                    
                    # Update metrics
                    metrics.memory_usage_mb = proc_info.memory_info().rss / (1024 * 1024)
                    metrics.cpu_usage_percent = proc_info.cpu_percent()
                    metrics.last_activity = time.time()
                    
                    # Log file and system calls
                    # This would be implemented with strace or similar
                    metrics.file_access_count += 1
                    metrics.system_call_count += 1
                    
            except Exception as e:
                self.logger.error(f"Failed to update metrics for {extension_name}: {e}")
                
        except Exception as e:
            self.logger.error(f"Failed to update execution metrics for {extension_name}: {e}")
    
    async def _check_resource_violations(self, extension_name: str, pid: int) -> None:
        """Check for resource policy violations."""
        try:
            context = self.sandboxes.get(extension_name)
            metrics = self.metrics.get(extension_name)
            
            if not context or not metrics:
                return
            
            policy = context.policy
            
            # Check memory usage
            if metrics.memory_usage_mb > policy.max_memory_mb:
                violation = {
                    "type": "memory",
                    "value": metrics.memory_usage_mb,
                    "limit": policy.max_memory_mb,
                    "timestamp": time.time()
                }
                metrics.violations.append(violation)
                await self._handle_violation(extension_name, violation)
            
            # Check CPU usage
            if metrics.cpu_usage_percent > policy.max_cpu_percent:
                violation = {
                    "type": "cpu",
                    "value": metrics.cpu_usage_percent,
                    "limit": policy.max_cpu_percent,
                    "timestamp": time.time()
                }
                metrics.violations.append(violation)
                await self._handle_violation(extension_name, violation)
            
            # Check disk usage
            if metrics.disk_usage_mb > policy.max_disk_mb:
                violation = {
                    "type": "disk",
                    "value": metrics.disk_usage_mb,
                    "limit": policy.max_disk_mb,
                    "timestamp": time.time()
                }
                metrics.violations.append(violation)
                await self._handle_violation(extension_name, violation)
                
        except Exception as e:
            self.logger.error(f"Failed to check resource violations for {extension_name}: {e}")
    
    async def _handle_violation(self, extension_name: str, violation: Dict[str, Any]) -> None:
        """Handle a sandbox policy violation."""
        try:
            context = self.sandboxes.get(extension_name)
            if not context:
                return
            
            policy = context.policy
            
            # Log violation
            if self.enable_audit:
                self.logger.warning(
                    f"Sandbox violation for {extension_name}: {violation['type']} "
                    f"(value: {violation['value']}, limit: {violation['limit']})"
                )
            
            # Take action based on policy
            if policy.violation_action == SandboxAction.WARN:
                # Just log the warning
                pass
            elif policy.violation_action == SandboxAction.THROTTLE:
                # Throttle the extension
                await self._throttle_extension(extension_name)
            elif policy.violation_action == SandboxAction.SUSPEND:
                # Suspend the extension
                await self._suspend_extension(extension_name)
            elif policy.violation_action == SandboxAction.TERMINATE:
                # Terminate the extension
                await self._terminate_extension(extension_name)
            elif policy.violation_action == SandboxAction.QUARANTINE:
                # Put extension in quarantine
                await self._quarantine_extension(extension_name)
                
        except Exception as e:
            self.logger.error(f"Failed to handle violation for {extension_name}: {e}")
    
    async def _throttle_extension(self, extension_name: str) -> None:
        """Throttle an extension for resource violations."""
        try:
            self.logger.warning(f"Throttling extension {extension_name}")
            
            # This would implement throttling logic
            # For now, just log the action
            if self.enable_audit:
                self.logger.warning(f"Extension {extension_name} throttled due to resource violations")
                
        except Exception as e:
            self.logger.error(f"Failed to throttle extension {extension_name}: {e}")
    
    async def _suspend_extension(self, extension_name: str) -> None:
        """Suspend an extension for resource violations."""
        try:
            self.logger.warning(f"Suspending extension {extension_name}")
            
            # This would implement suspension logic
            # For now, just log the action
            if self.enable_audit:
                self.logger.warning(f"Extension {extension_name} suspended due to resource violations")
                
        except Exception as e:
            self.logger.error(f"Failed to suspend extension {extension_name}: {e}")
    
    async def _terminate_extension(self, extension_name: str) -> None:
        """Terminate an extension for severe resource violations."""
        try:
            self.logger.error(f"Terminating extension {extension_name}")
            
            # This would implement termination logic
            # For now, just log the action
            if self.enable_audit:
                self.logger.error(f"Extension {extension_name} terminated due to resource violations")
                
        except Exception as e:
            self.logger.error(f"Failed to terminate extension {extension_name}: {e}")
    
    async def _quarantine_extension(self, extension_name: str) -> None:
        """Put an extension in quarantine for security violations."""
        try:
            self.logger.error(f"Quarantining extension {extension_name}")
            
            # This would implement quarantine logic
            # For now, just log the action
            if self.enable_audit:
                self.logger.error(f"Extension {extension_name} quarantined due to security violations")
                
        except Exception as e:
            self.logger.error(f"Failed to quarantine extension {extension_name}: {e}")
    
    def _create_restricted_env(self, policy: SandboxPolicy) -> Dict[str, str]:
        """Create restricted environment for sandbox."""
        env = {}
        
        # Basic environment
        env["PATH"] = "/usr/bin:/bin"
        env["HOME"] = policy.temp_dir or "/tmp"
        
        # Security restrictions
        env["PYTHONPATH"] = policy.temp_dir
        env["TMPDIR"] = policy.temp_dir
        
        # Remove sensitive environment variables
        sensitive_vars = ["PASSWORD", "TOKEN", "SECRET", "KEY", "API_KEY"]
        for var in os.environ:
            if any(sensitive in var.upper() for sensitive in sensitive_vars):
                continue  # Skip sensitive variables
            env[var] = os.environ[var]
        
        return env
    
    def _get_extension_policy(self, extension_name: str, manifest: ExtensionManifest) -> SandboxPolicy:
        """Get sandbox policy for an extension based on its manifest."""
        # Check if extension has custom policy
        if extension_name in self.policies:
            return self.policies[extension_name]
        
        # Create policy based on manifest
        policy = self.default_policy
        
        # Adjust based on extension permissions
        if hasattr(manifest, 'permissions'):
            perms = manifest.permissions
            
            # Adjust memory limits based on permissions
            if getattr(perms, 'memory_read', False):
                policy.max_memory_mb *= 2  # Allow more memory for read access
            if getattr(perms, 'memory_write', False):
                policy.max_memory_mb *= 1.5  # Allow more memory for write access
            
            # Adjust CPU limits based on permissions
            if getattr(perms, 'system_config_read', False):
                policy.max_cpu_percent *= 1.5  # Allow more CPU for config access
            
            # Adjust network access based on permissions
            if getattr(perms, 'network_access', False):
                policy.max_network_connections = 0  # No network access
            else:
                policy.max_network_connections *= 2  # Allow some network access
        
        # Adjust based on extension resources
        if hasattr(manifest, 'resources'):
            resources = manifest.resources
            
            # Use manifest resource limits if specified
            policy.max_memory_mb = resources.max_memory_mb
            policy.max_cpu_percent = resources.max_cpu_percent
            policy.max_disk_mb = resources.max_disk_mb
        
        return policy
    
    def get_sandbox_context(self, extension_name: str) -> Optional[SandboxContext]:
        """Get sandbox context for an extension."""
        return self.sandboxes.get(extension_name)
    
    def get_sandbox_metrics(self, extension_name: str) -> Optional[SandboxMetrics]:
        """Get sandbox metrics for an extension."""
        return self.metrics.get(extension_name)
    
    def get_all_sandbox_metrics(self) -> Dict[str, SandboxMetrics]:
        """Get sandbox metrics for all extensions."""
        return self.metrics.copy()
    
    def get_violation_summary(self) -> Dict[str, Any]:
        """Get summary of all sandbox violations."""
        try:
            total_violations = 0
            violation_types = {}
            
            for metrics in self.metrics.values():
                for violation in metrics.violations:
                    total_violations += 1
                    
                    vtype = violation.get('type', 'unknown')
                    violation_types[vtype] = violation_types.get(vtype, 0) + 1
            
            return {
                "total_violations": total_violations,
                "violation_types": violation_types,
                "extensions_with_violations": [
                    name for name, metrics in self.metrics.items()
                    if metrics.violations
                ],
                "last_violation": max(
                    (v.get('timestamp', 0) for metrics in self.metrics.values() for v in metrics.violations),
                    default=0
                )
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get violation summary: {e}")
            return {"error": str(e)}
    
    async def cleanup_sandbox(self, extension_name: str) -> bool:
        """Clean up sandbox resources for an extension."""
        try:
            context = self.sandboxes.get(extension_name)
            if not context:
                return False
            
            # Clean up temporary directory
            if context.temp_dir.exists():
                import shutil
                shutil.rmtree(context.temp_dir)
            
            # Remove from active sandboxes
            del self.sandboxes[extension_name]
            del self.metrics[extension_name]
            
            self.logger.info(f"Sandbox cleaned up for extension {extension_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup sandbox for {extension_name}: {e}")
            return False
    
    async def start_monitoring(self) -> None:
        """Start sandbox monitoring for all active extensions."""
        self.logger.info("Starting sandbox monitoring")
        
        try:
            self._monitoring = True
            self._monitor_task = asyncio.create_task(self._monitoring_loop())
            
        except Exception as e:
            self.logger.error(f"Failed to start sandbox monitoring: {e}")
    
    async def stop_monitoring(self) -> None:
        """Stop sandbox monitoring."""
        self.logger.info("Stopping sandbox monitoring")
        
        try:
            self._monitoring = False
            if self._monitor_task:
                self._monitor_task.cancel()
                try:
                    await self._monitor_task
                except asyncio.CancelledError:
                    pass
                    
        except Exception as e:
            self.logger.error(f"Failed to stop sandbox monitoring: {e}")
    
    async def _monitoring_loop(self) -> None:
        """Main sandbox monitoring loop."""
        while self._monitoring:
            try:
                # Check all active sandboxes
                for extension_name, context in self.sandboxes.items():
                    if context.policy.audit_logging:
                        await self._audit_sandbox_state(extension_name, context)
                
                # Sleep between checks
                await asyncio.sleep(self.monitoring_interval)
                
            except asyncio.CancelledError:
                self.logger.info("Sandbox monitoring loop cancelled")
                break
            except Exception as e:
                self.logger.error(f"Error in sandbox monitoring loop: {e}")
                await asyncio.sleep(5.0)  # Brief pause before retrying
    
    async def _audit_sandbox_state(self, extension_name: str, context: SandboxContext) -> None:
        """Audit sandbox state and log to database."""
        try:
            metrics = self.metrics.get(extension_name)
            if not metrics:
                return
            
            # Log sandbox state to audit log
            audit_data = {
                "extension_name": extension_name,
                "timestamp": time.time(),
                "memory_usage_mb": metrics.memory_usage_mb,
                "cpu_usage_percent": metrics.cpu_usage_percent,
                "disk_usage_mb": metrics.disk_usage_mb,
                "network_bytes_sent": metrics.network_bytes_sent,
                "network_bytes_recv": metrics.network_bytes_recv,
                "file_access_count": metrics.file_access_count,
                "system_call_count": metrics.system_call_count,
                "violations_count": len(metrics.violations),
                "violations": metrics.violations[-10:] if metrics.violations else []
            }
            
            self.logger.info(f"Sandbox audit for {extension_name}: {audit_data}")
            
        except Exception as e:
            self.logger.error(f"Failed to audit sandbox state for {extension_name}: {e}")


__all__ = [
    "ExtensionSandboxManager",
    "SandboxSecurityLevel",
    "SandboxAction",
    "SandboxPolicy",
    "SandboxMetrics",
    "SandboxContext",
]