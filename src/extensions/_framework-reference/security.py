"""
Extension Security and Sandboxing System.

This module provides comprehensive security controls for extensions including:
- Permission management and access control
- Resource limit enforcement (CPU, memory, disk)
- Process isolation and sandboxing
- Network access controls and restrictions
"""

import logging
import asyncio
import psutil
import os
import signal
import subprocess
import tempfile
import shutil
from typing import Dict, List, Optional, Any, Set, Callable
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
import resource
import threading
import time
import json

from .models import (
    ExtensionManifest, 
    ExtensionPermissions, 
    ExtensionResources,
    ExtensionContext
)

logger = logging.getLogger(__name__)


@dataclass
class ResourceUsage:
    """Current resource usage metrics."""
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    disk_mb: float = 0.0
    network_bytes_sent: int = 0
    network_bytes_recv: int = 0
    file_descriptors: int = 0
    threads: int = 0
    uptime_seconds: float = 0.0


@dataclass
class SecurityViolation:
    """Security violation record."""
    extension_name: str
    violation_type: str
    description: str
    timestamp: datetime
    severity: str  # 'low', 'medium', 'high', 'critical'
    action_taken: str
    details: Dict[str, Any] = field(default_factory=dict)


class ExtensionPermissionManager:
    """Manages extension permissions and access control."""
    
    def __init__(self):
        self.granted_permissions: Dict[str, Set[str]] = {}
        self.permission_cache: Dict[str, Dict[str, bool]] = {}
        self.permission_callbacks: Dict[str, List[Callable]] = {}
        self._lock = threading.RLock()
        
        # Define permission hierarchy
        self.permission_hierarchy = {
            'data_access': {
                'read': ['read'],
                'write': ['read', 'write'],
                'admin': ['read', 'write', 'admin']
            },
            'plugin_access': {
                'execute': ['execute'],
                'manage': ['execute', 'manage']
            },
            'system_access': {
                'files': ['files'],
                'network': ['network'],
                'scheduler': ['scheduler'],
                'logs': ['logs'],
                'metrics': ['metrics'],
                'admin': ['files', 'network', 'scheduler', 'logs', 'metrics', 'admin']
            },
            'network_access': {
                'internal': ['internal'],
                'external': ['internal', 'external']
            }
        }
    
    def grant_permissions(
        self, 
        extension_name: str, 
        permissions: ExtensionPermissions,
        granted_by: str
    ) -> None:
        """Grant permissions to an extension."""
        with self._lock:
            if extension_name not in self.granted_permissions:
                self.granted_permissions[extension_name] = set()
            
            # Expand permissions based on hierarchy
            expanded_permissions = self._expand_permissions(permissions)
            self.granted_permissions[extension_name].update(expanded_permissions)
            
            # Clear cache for this extension
            if extension_name in self.permission_cache:
                del self.permission_cache[extension_name]
            
            logger.info(f"Granted permissions to {extension_name}: {expanded_permissions}")
    
    def revoke_permissions(
        self, 
        extension_name: str, 
        permissions: List[str],
        revoked_by: str
    ) -> None:
        """Revoke specific permissions from an extension."""
        with self._lock:
            if extension_name in self.granted_permissions:
                self.granted_permissions[extension_name] -= set(permissions)
                
                # Clear cache for this extension
                if extension_name in self.permission_cache:
                    del self.permission_cache[extension_name]
                
                logger.info(f"Revoked permissions from {extension_name}: {permissions}")
    
    def revoke_all_permissions(self, extension_name: str, revoked_by: str) -> None:
        """Revoke all permissions from an extension."""
        with self._lock:
            if extension_name in self.granted_permissions:
                del self.granted_permissions[extension_name]
            
            if extension_name in self.permission_cache:
                del self.permission_cache[extension_name]
            
            logger.info(f"Revoked all permissions from {extension_name}")
    
    def check_permission(
        self, 
        extension_name: str, 
        permission: str,
        context: Optional[ExtensionContext] = None
    ) -> bool:
        """Check if extension has a specific permission."""
        with self._lock:
            # Check cache first
            cache_key = f"{extension_name}:{permission}"
            if extension_name in self.permission_cache:
                if permission in self.permission_cache[extension_name]:
                    return self.permission_cache[extension_name][permission]
            
            # Check actual permissions
            has_permission = False
            if extension_name in self.granted_permissions:
                has_permission = permission in self.granted_permissions[extension_name]
            
            # Cache result
            if extension_name not in self.permission_cache:
                self.permission_cache[extension_name] = {}
            self.permission_cache[extension_name][permission] = has_permission
            
            return has_permission
    
    def get_extension_permissions(self, extension_name: str) -> Set[str]:
        """Get all permissions for an extension."""
        with self._lock:
            return self.granted_permissions.get(extension_name, set()).copy()
    
    def _expand_permissions(self, permissions: ExtensionPermissions) -> Set[str]:
        """Expand permissions based on hierarchy."""
        expanded = set()
        
        # Data access permissions
        for perm in permissions.data_access:
            if perm in self.permission_hierarchy['data_access']:
                expanded.update(f"data:{p}" for p in self.permission_hierarchy['data_access'][perm])
        
        # Plugin access permissions
        for perm in permissions.plugin_access:
            if perm in self.permission_hierarchy['plugin_access']:
                expanded.update(f"plugin:{p}" for p in self.permission_hierarchy['plugin_access'][perm])
        
        # System access permissions
        for perm in permissions.system_access:
            if perm in self.permission_hierarchy['system_access']:
                expanded.update(f"system:{p}" for p in self.permission_hierarchy['system_access'][perm])
        
        # Network access permissions
        for perm in permissions.network_access:
            if perm in self.permission_hierarchy['network_access']:
                expanded.update(f"network:{p}" for p in self.permission_hierarchy['network_access'][perm])
        
        return expanded


class ResourceLimitEnforcer:
    """Enforces resource limits for extensions."""
    
    def __init__(self):
        self.resource_limits: Dict[str, ExtensionResources] = {}
        self.resource_usage: Dict[str, ResourceUsage] = {}
        self.process_monitors: Dict[str, 'ProcessMonitor'] = {}
        self.violation_callbacks: List[Callable[[str, SecurityViolation], None]] = []
        self._monitoring_enabled = False
        self._monitoring_task: Optional[asyncio.Task] = None
        self._lock = threading.RLock()
    
    def set_resource_limits(
        self, 
        extension_name: str, 
        limits: ExtensionResources
    ) -> None:
        """Set resource limits for an extension."""
        with self._lock:
            self.resource_limits[extension_name] = limits
            logger.info(f"Set resource limits for {extension_name}: {limits}")
    
    def start_monitoring(self, extension_name: str, process_id: int) -> None:
        """Start monitoring resource usage for an extension process."""
        with self._lock:
            if extension_name in self.process_monitors:
                self.process_monitors[extension_name].stop()
            
            monitor = ProcessMonitor(
                extension_name, 
                process_id, 
                self.resource_limits.get(extension_name),
                self._on_resource_violation
            )
            self.process_monitors[extension_name] = monitor
            monitor.start()
            
            logger.info(f"Started resource monitoring for {extension_name} (PID: {process_id})")
    
    def stop_monitoring(self, extension_name: str) -> None:
        """Stop monitoring resource usage for an extension."""
        with self._lock:
            if extension_name in self.process_monitors:
                self.process_monitors[extension_name].stop()
                del self.process_monitors[extension_name]
                logger.info(f"Stopped resource monitoring for {extension_name}")
    
    def get_resource_usage(self, extension_name: str) -> Optional[ResourceUsage]:
        """Get current resource usage for an extension."""
        with self._lock:
            if extension_name in self.process_monitors:
                return self.process_monitors[extension_name].get_current_usage()
            return None
    
    def check_resource_limits(self, extension_name: str) -> Dict[str, bool]:
        """Check if extension is within resource limits."""
        with self._lock:
            if extension_name not in self.process_monitors:
                return {'within_limits': True}
            
            monitor = self.process_monitors[extension_name]
            usage = monitor.get_current_usage()
            limits = self.resource_limits.get(extension_name)
            
            if not limits or not usage:
                return {'within_limits': True}
            
            return {
                'within_limits': (
                    usage.cpu_percent <= limits.max_cpu_percent and
                    usage.memory_mb <= limits.max_memory_mb and
                    usage.disk_mb <= limits.max_disk_mb
                ),
                'cpu_within_limit': usage.cpu_percent <= limits.max_cpu_percent,
                'memory_within_limit': usage.memory_mb <= limits.max_memory_mb,
                'disk_within_limit': usage.disk_mb <= limits.max_disk_mb,
                'current_usage': {
                    'cpu_percent': usage.cpu_percent,
                    'memory_mb': usage.memory_mb,
                    'disk_mb': usage.disk_mb
                },
                'limits': {
                    'max_cpu_percent': limits.max_cpu_percent,
                    'max_memory_mb': limits.max_memory_mb,
                    'max_disk_mb': limits.max_disk_mb
                }
            }
    
    def add_violation_callback(self, callback: Callable[[str, SecurityViolation], None]) -> None:
        """Add callback for resource violations."""
        self.violation_callbacks.append(callback)
    
    def _on_resource_violation(self, extension_name: str, violation: SecurityViolation) -> None:
        """Handle resource violation."""
        logger.warning(f"Resource violation for {extension_name}: {violation.description}")
        
        for callback in self.violation_callbacks:
            try:
                callback(extension_name, violation)
            except Exception as e:
                logger.error(f"Error in violation callback: {e}")


class ProcessMonitor:
    """Monitors resource usage of an extension process."""
    
    def __init__(
        self, 
        extension_name: str, 
        process_id: int,
        limits: Optional[ExtensionResources],
        violation_callback: Callable[[str, SecurityViolation], None]
    ):
        self.extension_name = extension_name
        self.process_id = process_id
        self.limits = limits
        self.violation_callback = violation_callback
        self.start_time = time.time()
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._current_usage = ResourceUsage()
        self._violation_counts: Dict[str, int] = {}
    
    def start(self) -> None:
        """Start monitoring the process."""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
    
    def stop(self) -> None:
        """Stop monitoring the process."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
    
    def get_current_usage(self) -> ResourceUsage:
        """Get current resource usage."""
        return self._current_usage
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self._monitoring:
            try:
                self._update_usage()
                self._check_violations()
                time.sleep(1.0)  # Monitor every second
            except psutil.NoSuchProcess:
                logger.info(f"Process {self.process_id} for {self.extension_name} no longer exists")
                break
            except Exception as e:
                logger.error(f"Error monitoring process {self.process_id}: {e}")
                time.sleep(5.0)  # Wait longer on error
    
    def _update_usage(self) -> None:
        """Update current resource usage."""
        try:
            process = psutil.Process(self.process_id)
            
            # CPU usage
            cpu_percent = process.cpu_percent()
            
            # Memory usage
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            
            # Disk usage (approximate based on open files)
            disk_mb = 0.0
            try:
                open_files = process.open_files()
                for file_info in open_files:
                    try:
                        file_size = os.path.getsize(file_info.path)
                        disk_mb += file_size / (1024 * 1024)
                    except (OSError, FileNotFoundError):
                        pass
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass
            
            # Network usage
            try:
                net_io = process.io_counters()
                network_bytes_sent = net_io.write_bytes
                network_bytes_recv = net_io.read_bytes
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                network_bytes_sent = 0
                network_bytes_recv = 0
            
            # File descriptors and threads
            try:
                file_descriptors = process.num_fds() if hasattr(process, 'num_fds') else 0
                threads = process.num_threads()
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                file_descriptors = 0
                threads = 0
            
            # Update usage
            self._current_usage = ResourceUsage(
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
                disk_mb=disk_mb,
                network_bytes_sent=network_bytes_sent,
                network_bytes_recv=network_bytes_recv,
                file_descriptors=file_descriptors,
                threads=threads,
                uptime_seconds=time.time() - self.start_time
            )
            
        except psutil.NoSuchProcess:
            raise
        except Exception as e:
            logger.error(f"Error updating usage for {self.extension_name}: {e}")
    
    def _check_violations(self) -> None:
        """Check for resource limit violations."""
        if not self.limits:
            return
        
        usage = self._current_usage
        
        # Check CPU limit
        if usage.cpu_percent > self.limits.max_cpu_percent:
            self._handle_violation(
                'cpu_limit_exceeded',
                f"CPU usage {usage.cpu_percent:.1f}% exceeds limit {self.limits.max_cpu_percent}%",
                'medium'
            )
        
        # Check memory limit
        if usage.memory_mb > self.limits.max_memory_mb:
            self._handle_violation(
                'memory_limit_exceeded',
                f"Memory usage {usage.memory_mb:.1f}MB exceeds limit {self.limits.max_memory_mb}MB",
                'high'
            )
        
        # Check disk limit
        if usage.disk_mb > self.limits.max_disk_mb:
            self._handle_violation(
                'disk_limit_exceeded',
                f"Disk usage {usage.disk_mb:.1f}MB exceeds limit {self.limits.max_disk_mb}MB",
                'medium'
            )
    
    def _handle_violation(self, violation_type: str, description: str, severity: str) -> None:
        """Handle a resource violation."""
        # Track violation count
        if violation_type not in self._violation_counts:
            self._violation_counts[violation_type] = 0
        self._violation_counts[violation_type] += 1
        
        # Create violation record
        violation = SecurityViolation(
            extension_name=self.extension_name,
            violation_type=violation_type,
            description=description,
            timestamp=datetime.now(),
            severity=severity,
            action_taken='logged',
            details={
                'process_id': self.process_id,
                'violation_count': self._violation_counts[violation_type],
                'current_usage': {
                    'cpu_percent': self._current_usage.cpu_percent,
                    'memory_mb': self._current_usage.memory_mb,
                    'disk_mb': self._current_usage.disk_mb
                }
            }
        )
        
        # Call violation callback
        self.violation_callback(self.extension_name, violation)


class ExtensionSandbox:
    """Provides process isolation and sandboxing for extensions."""
    
    def __init__(self):
        self.sandboxed_processes: Dict[str, int] = {}
        self.sandbox_directories: Dict[str, Path] = {}
        self.network_restrictions: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
    
    async def create_sandbox(
        self, 
        extension_name: str, 
        manifest: ExtensionManifest
    ) -> Dict[str, Any]:
        """Create a sandboxed environment for an extension."""
        with self._lock:
            try:
                # Create temporary directory for extension
                sandbox_dir = Path(tempfile.mkdtemp(prefix=f"ext_{extension_name}_"))
                self.sandbox_directories[extension_name] = sandbox_dir
                
                # Set up directory structure
                (sandbox_dir / "data").mkdir()
                (sandbox_dir / "logs").mkdir()
                (sandbox_dir / "temp").mkdir()
                
                # Create sandbox configuration
                sandbox_config = {
                    'extension_name': extension_name,
                    'sandbox_directory': str(sandbox_dir),
                    'allowed_paths': [str(sandbox_dir)],
                    'environment_variables': {
                        'EXTENSION_NAME': extension_name,
                        'EXTENSION_SANDBOX_DIR': str(sandbox_dir),
                        'EXTENSION_DATA_DIR': str(sandbox_dir / "data"),
                        'EXTENSION_LOG_DIR': str(sandbox_dir / "logs"),
                        'EXTENSION_TEMP_DIR': str(sandbox_dir / "temp")
                    },
                    'resource_limits': {
                        'max_memory_mb': manifest.resources.max_memory_mb,
                        'max_cpu_percent': manifest.resources.max_cpu_percent,
                        'max_disk_mb': manifest.resources.max_disk_mb
                    },
                    'network_restrictions': self._create_network_restrictions(manifest),
                    'file_permissions': self._create_file_permissions(manifest)
                }
                
                logger.info(f"Created sandbox for {extension_name} at {sandbox_dir}")
                return sandbox_config
                
            except Exception as e:
                logger.error(f"Failed to create sandbox for {extension_name}: {e}")
                raise
    
    async def destroy_sandbox(self, extension_name: str) -> None:
        """Destroy the sandbox for an extension."""
        with self._lock:
            try:
                # Remove sandbox directory
                if extension_name in self.sandbox_directories:
                    sandbox_dir = self.sandbox_directories[extension_name]
                    if sandbox_dir.exists():
                        shutil.rmtree(sandbox_dir)
                    del self.sandbox_directories[extension_name]
                
                # Clean up process tracking
                if extension_name in self.sandboxed_processes:
                    del self.sandboxed_processes[extension_name]
                
                # Clean up network restrictions
                if extension_name in self.network_restrictions:
                    del self.network_restrictions[extension_name]
                
                logger.info(f"Destroyed sandbox for {extension_name}")
                
            except Exception as e:
                logger.error(f"Failed to destroy sandbox for {extension_name}: {e}")
    
    def register_process(self, extension_name: str, process_id: int) -> None:
        """Register a sandboxed process."""
        with self._lock:
            self.sandboxed_processes[extension_name] = process_id
            logger.info(f"Registered sandboxed process {process_id} for {extension_name}")
    
    def get_sandbox_info(self, extension_name: str) -> Optional[Dict[str, Any]]:
        """Get sandbox information for an extension."""
        with self._lock:
            if extension_name not in self.sandbox_directories:
                return None
            
            return {
                'extension_name': extension_name,
                'sandbox_directory': str(self.sandbox_directories[extension_name]),
                'process_id': self.sandboxed_processes.get(extension_name),
                'network_restrictions': self.network_restrictions.get(extension_name, {})
            }
    
    def _create_network_restrictions(self, manifest: ExtensionManifest) -> Dict[str, Any]:
        """Create network restrictions based on manifest permissions."""
        restrictions = {
            'allow_outbound': False,
            'allow_inbound': False,
            'allowed_hosts': [],
            'allowed_ports': [],
            'blocked_hosts': [],
            'blocked_ports': []
        }
        
        # Check network permissions
        if 'external' in manifest.permissions.network_access:
            restrictions['allow_outbound'] = True
            restrictions['allowed_ports'] = [80, 443]  # HTTP/HTTPS by default
        
        if 'internal' in manifest.permissions.network_access:
            restrictions['allow_inbound'] = True
            restrictions['allowed_hosts'] = ['127.0.0.1', 'localhost']
        
        return restrictions
    
    def _create_file_permissions(self, manifest: ExtensionManifest) -> Dict[str, Any]:
        """Create file permissions based on manifest permissions."""
        permissions = {
            'read_only_paths': [],
            'read_write_paths': [],
            'blocked_paths': [
                '/etc/passwd',
                '/etc/shadow',
                '/root',
                '/home',
                '/var/log',
                '/sys',
                '/proc'
            ]
        }
        
        # Check file permissions
        if 'files' in manifest.permissions.system_access:
            # Allow access to extension sandbox directory
            permissions['read_write_paths'].append('/tmp/ext_*')
        
        return permissions


class NetworkAccessController:
    """Controls network access for extensions."""
    
    def __init__(self):
        self.access_rules: Dict[str, Dict[str, Any]] = {}
        self.connection_monitors: Dict[str, 'NetworkMonitor'] = {}
        self._lock = threading.RLock()
    
    def set_network_rules(
        self, 
        extension_name: str, 
        rules: Dict[str, Any]
    ) -> None:
        """Set network access rules for an extension."""
        with self._lock:
            self.access_rules[extension_name] = rules
            logger.info(f"Set network rules for {extension_name}: {rules}")
    
    def check_network_access(
        self, 
        extension_name: str, 
        host: str, 
        port: int,
        direction: str = 'outbound'
    ) -> bool:
        """Check if extension can access a network endpoint."""
        with self._lock:
            if extension_name not in self.access_rules:
                return False
            
            rules = self.access_rules[extension_name]
            
            # Check direction
            if direction == 'outbound' and not rules.get('allow_outbound', False):
                return False
            if direction == 'inbound' and not rules.get('allow_inbound', False):
                return False
            
            # Check blocked hosts
            if host in rules.get('blocked_hosts', []):
                return False
            
            # Check blocked ports
            if port in rules.get('blocked_ports', []):
                return False
            
            # Check allowed hosts (if specified)
            allowed_hosts = rules.get('allowed_hosts', [])
            if allowed_hosts and host not in allowed_hosts:
                return False
            
            # Check allowed ports (if specified)
            allowed_ports = rules.get('allowed_ports', [])
            if allowed_ports and port not in allowed_ports:
                return False
            
            return True
    
    def start_monitoring(self, extension_name: str, process_id: int) -> None:
        """Start monitoring network connections for an extension."""
        with self._lock:
            if extension_name in self.connection_monitors:
                self.connection_monitors[extension_name].stop()
            
            monitor = NetworkMonitor(extension_name, process_id)
            self.connection_monitors[extension_name] = monitor
            monitor.start()
            
            logger.info(f"Started network monitoring for {extension_name}")
    
    def stop_monitoring(self, extension_name: str) -> None:
        """Stop monitoring network connections for an extension."""
        with self._lock:
            if extension_name in self.connection_monitors:
                self.connection_monitors[extension_name].stop()
                del self.connection_monitors[extension_name]
                logger.info(f"Stopped network monitoring for {extension_name}")
    
    def get_network_connections(self, extension_name: str) -> List[Dict[str, Any]]:
        """Get current network connections for an extension."""
        with self._lock:
            if extension_name in self.connection_monitors:
                return self.connection_monitors[extension_name].get_connections()
            return []


class NetworkMonitor:
    """Monitors network connections for an extension process."""
    
    def __init__(self, extension_name: str, process_id: int):
        self.extension_name = extension_name
        self.process_id = process_id
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._connections: List[Dict[str, Any]] = []
        self._lock = threading.RLock()
    
    def start(self) -> None:
        """Start monitoring network connections."""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
    
    def stop(self) -> None:
        """Stop monitoring network connections."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
    
    def get_connections(self) -> List[Dict[str, Any]]:
        """Get current network connections."""
        with self._lock:
            return self._connections.copy()
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self._monitoring:
            try:
                self._update_connections()
                time.sleep(5.0)  # Check every 5 seconds
            except psutil.NoSuchProcess:
                logger.info(f"Process {self.process_id} for {self.extension_name} no longer exists")
                break
            except Exception as e:
                logger.error(f"Error monitoring network for {self.process_id}: {e}")
                time.sleep(10.0)
    
    def _update_connections(self) -> None:
        """Update current network connections."""
        try:
            process = psutil.Process(self.process_id)
            connections = []
            
            for conn in process.connections():
                conn_info = {
                    'family': conn.family.name if hasattr(conn.family, 'name') else str(conn.family),
                    'type': conn.type.name if hasattr(conn.type, 'name') else str(conn.type),
                    'local_address': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                    'remote_address': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                    'status': conn.status,
                    'timestamp': datetime.now().isoformat()
                }
                connections.append(conn_info)
            
            with self._lock:
                self._connections = connections
                
        except psutil.NoSuchProcess:
            raise
        except Exception as e:
            logger.error(f"Error updating connections for {self.extension_name}: {e}")


class ExtensionSecurityManager:
    """Main security manager that coordinates all security components."""
    
    def __init__(self):
        self.permission_manager = ExtensionPermissionManager()
        self.resource_enforcer = ResourceLimitEnforcer()
        self.sandbox = ExtensionSandbox()
        self.network_controller = NetworkAccessController()
        self.security_violations: List[SecurityViolation] = []
        self.security_policies: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        
        # Register violation callback
        self.resource_enforcer.add_violation_callback(self._handle_security_violation)
    
    async def initialize_extension_security(
        self, 
        extension_name: str, 
        manifest: ExtensionManifest,
        context: ExtensionContext
    ) -> Dict[str, Any]:
        """Initialize security for an extension."""
        try:
            logger.info(f"Initializing security for extension: {extension_name}")
            
            # Grant permissions based on manifest
            self.permission_manager.grant_permissions(
                extension_name, 
                manifest.permissions,
                "system"
            )
            
            # Set resource limits
            self.resource_enforcer.set_resource_limits(
                extension_name, 
                manifest.resources
            )
            
            # Create sandbox
            sandbox_config = await self.sandbox.create_sandbox(extension_name, manifest)
            
            # Set network rules
            network_rules = {
                'allow_outbound': 'external' in manifest.permissions.network_access,
                'allow_inbound': 'internal' in manifest.permissions.network_access,
                'allowed_hosts': [],
                'allowed_ports': [80, 443] if 'external' in manifest.permissions.network_access else [],
                'blocked_hosts': [],
                'blocked_ports': []
            }
            self.network_controller.set_network_rules(extension_name, network_rules)
            
            # Create security policy
            security_policy = {
                'extension_name': extension_name,
                'permissions': self.permission_manager.get_extension_permissions(extension_name),
                'resource_limits': manifest.resources.dict(),
                'sandbox_config': sandbox_config,
                'network_rules': network_rules,
                'created_at': datetime.now().isoformat()
            }
            
            with self._lock:
                self.security_policies[extension_name] = security_policy
            
            logger.info(f"Security initialized for {extension_name}")
            return security_policy
            
        except Exception as e:
            logger.error(f"Failed to initialize security for {extension_name}: {e}")
            raise
    
    async def cleanup_extension_security(self, extension_name: str) -> None:
        """Clean up security resources for an extension."""
        try:
            logger.info(f"Cleaning up security for extension: {extension_name}")
            
            # Stop monitoring
            self.resource_enforcer.stop_monitoring(extension_name)
            self.network_controller.stop_monitoring(extension_name)
            
            # Destroy sandbox
            await self.sandbox.destroy_sandbox(extension_name)
            
            # Revoke permissions
            self.permission_manager.revoke_all_permissions(extension_name, "system")
            
            # Remove security policy
            with self._lock:
                if extension_name in self.security_policies:
                    del self.security_policies[extension_name]
            
            logger.info(f"Security cleanup completed for {extension_name}")
            
        except Exception as e:
            logger.error(f"Failed to cleanup security for {extension_name}: {e}")
    
    def start_extension_monitoring(self, extension_name: str, process_id: int) -> None:
        """Start security monitoring for an extension process."""
        try:
            # Start resource monitoring
            self.resource_enforcer.start_monitoring(extension_name, process_id)
            
            # Start network monitoring
            self.network_controller.start_monitoring(extension_name, process_id)
            
            # Register process in sandbox
            self.sandbox.register_process(extension_name, process_id)
            
            logger.info(f"Started security monitoring for {extension_name} (PID: {process_id})")
            
        except Exception as e:
            logger.error(f"Failed to start monitoring for {extension_name}: {e}")
    
    def stop_extension_monitoring(self, extension_name: str) -> None:
        """Stop security monitoring for an extension."""
        try:
            self.resource_enforcer.stop_monitoring(extension_name)
            self.network_controller.stop_monitoring(extension_name)
            logger.info(f"Stopped security monitoring for {extension_name}")
            
        except Exception as e:
            logger.error(f"Failed to stop monitoring for {extension_name}: {e}")
    
    def check_permission(
        self, 
        extension_name: str, 
        permission: str,
        context: Optional[ExtensionContext] = None
    ) -> bool:
        """Check if extension has permission."""
        return self.permission_manager.check_permission(extension_name, permission, context)
    
    def get_security_status(self, extension_name: str) -> Dict[str, Any]:
        """Get comprehensive security status for an extension."""
        try:
            status = {
                'extension_name': extension_name,
                'permissions': list(self.permission_manager.get_extension_permissions(extension_name)),
                'resource_usage': None,
                'resource_limits_check': None,
                'sandbox_info': None,
                'network_connections': [],
                'recent_violations': []
            }
            
            # Resource usage and limits
            usage = self.resource_enforcer.get_resource_usage(extension_name)
            if usage:
                status['resource_usage'] = {
                    'cpu_percent': usage.cpu_percent,
                    'memory_mb': usage.memory_mb,
                    'disk_mb': usage.disk_mb,
                    'uptime_seconds': usage.uptime_seconds
                }
            
            status['resource_limits_check'] = self.resource_enforcer.check_resource_limits(extension_name)
            
            # Sandbox info
            status['sandbox_info'] = self.sandbox.get_sandbox_info(extension_name)
            
            # Network connections
            status['network_connections'] = self.network_controller.get_network_connections(extension_name)
            
            # Recent violations (last 24 hours)
            cutoff_time = datetime.now() - timedelta(hours=24)
            with self._lock:
                status['recent_violations'] = [
                    {
                        'violation_type': v.violation_type,
                        'description': v.description,
                        'timestamp': v.timestamp.isoformat(),
                        'severity': v.severity,
                        'action_taken': v.action_taken
                    }
                    for v in self.security_violations
                    if v.extension_name == extension_name and v.timestamp > cutoff_time
                ]
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get security status for {extension_name}: {e}")
            return {'error': str(e)}
    
    def get_all_security_violations(
        self, 
        extension_name: Optional[str] = None,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get security violations for extensions."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            violations = [
                {
                    'extension_name': v.extension_name,
                    'violation_type': v.violation_type,
                    'description': v.description,
                    'timestamp': v.timestamp.isoformat(),
                    'severity': v.severity,
                    'action_taken': v.action_taken,
                    'details': v.details
                }
                for v in self.security_violations
                if v.timestamp > cutoff_time and (
                    extension_name is None or v.extension_name == extension_name
                )
            ]
        
        return violations
    
    def _handle_security_violation(self, extension_name: str, violation: SecurityViolation) -> None:
        """Handle a security violation."""
        with self._lock:
            self.security_violations.append(violation)
            
            # Keep only recent violations (last 7 days)
            cutoff_time = datetime.now() - timedelta(days=7)
            self.security_violations = [
                v for v in self.security_violations 
                if v.timestamp > cutoff_time
            ]
        
        logger.warning(f"Security violation: {violation.extension_name} - {violation.description}")
        
        # Take action based on severity
        if violation.severity == 'critical':
            # Could implement automatic extension shutdown here
            logger.critical(f"Critical security violation for {extension_name}: {violation.description}")
        elif violation.severity == 'high':
            # Could implement throttling or warnings here
            logger.error(f"High severity security violation for {extension_name}: {violation.description}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Security manager health check."""
        try:
            with self._lock:
                total_violations = len(self.security_violations)
                recent_violations = len([
                    v for v in self.security_violations
                    if v.timestamp > datetime.now() - timedelta(hours=1)
                ])
            
            return {
                'status': 'healthy',
                'managed_extensions': len(self.security_policies),
                'total_violations': total_violations,
                'recent_violations': recent_violations,
                'components': {
                    'permission_manager': 'healthy',
                    'resource_enforcer': 'healthy',
                    'sandbox': 'healthy',
                    'network_controller': 'healthy'
                }
            }
            
        except Exception as e:
            logger.error(f"Security manager health check error: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }