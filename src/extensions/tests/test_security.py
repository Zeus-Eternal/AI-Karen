"""
Tests for the extension security and sandboxing system.
"""

import pytest
import asyncio
import tempfile
import os
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from ..security import (
    ExtensionSecurityManager,
    ExtensionPermissionManager,
    ResourceLimitEnforcer,
    ExtensionSandbox,
    NetworkAccessController,
    ProcessMonitor,
    ResourceUsage,
    SecurityViolation
)
from ..security_decorators import (
    require_permission,
    require_permissions,
    rate_limit,
    audit_log,
    SecurityContext,
    set_security_manager,
    check_extension_permission
)
from ..models import (
    ExtensionManifest,
    ExtensionPermissions,
    ExtensionResources,
    ExtensionContext,
    ExtensionCapabilities
)


class TestExtensionPermissionManager:
    """Test extension permission management."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.permission_manager = ExtensionPermissionManager()
    
    def test_grant_permissions(self):
        """Test granting permissions to an extension."""
        permissions = ExtensionPermissions(
            data_access=['read', 'write'],
            system_access=['files'],
            network_access=['external']
        )
        
        self.permission_manager.grant_permissions('test-ext', permissions, 'admin')
        
        # Check expanded permissions
        granted = self.permission_manager.get_extension_permissions('test-ext')
        assert 'data:read' in granted
        assert 'data:write' in granted
        assert 'system:files' in granted
        assert 'network:external' in granted
    
    def test_check_permission(self):
        """Test checking individual permissions."""
        permissions = ExtensionPermissions(data_access=['read'])
        self.permission_manager.grant_permissions('test-ext', permissions, 'admin')
        
        assert self.permission_manager.check_permission('test-ext', 'data:read')
        assert not self.permission_manager.check_permission('test-ext', 'data:write')
        assert not self.permission_manager.check_permission('test-ext', 'system:files')
    
    def test_revoke_permissions(self):
        """Test revoking permissions."""
        permissions = ExtensionPermissions(data_access=['read', 'write'])
        self.permission_manager.grant_permissions('test-ext', permissions, 'admin')
        
        # Revoke specific permission
        self.permission_manager.revoke_permissions('test-ext', ['data:write'], 'admin')
        
        assert self.permission_manager.check_permission('test-ext', 'data:read')
        assert not self.permission_manager.check_permission('test-ext', 'data:write')
    
    def test_revoke_all_permissions(self):
        """Test revoking all permissions."""
        permissions = ExtensionPermissions(data_access=['read', 'write'])
        self.permission_manager.grant_permissions('test-ext', permissions, 'admin')
        
        self.permission_manager.revoke_all_permissions('test-ext', 'admin')
        
        assert not self.permission_manager.check_permission('test-ext', 'data:read')
        assert not self.permission_manager.check_permission('test-ext', 'data:write')


class TestResourceLimitEnforcer:
    """Test resource limit enforcement."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.enforcer = ResourceLimitEnforcer()
    
    def test_set_resource_limits(self):
        """Test setting resource limits."""
        limits = ExtensionResources(
            max_memory_mb=512,
            max_cpu_percent=25,
            max_disk_mb=1024
        )
        
        self.enforcer.set_resource_limits('test-ext', limits)
        
        assert 'test-ext' in self.enforcer.resource_limits
        assert self.enforcer.resource_limits['test-ext'].max_memory_mb == 512
    
    @patch('psutil.Process')
    def test_process_monitor(self, mock_process_class):
        """Test process monitoring."""
        # Mock process
        mock_process = Mock()
        mock_process.cpu_percent.return_value = 15.0
        mock_process.memory_info.return_value = Mock(rss=100 * 1024 * 1024)  # 100MB
        mock_process.open_files.return_value = []
        mock_process.io_counters.return_value = Mock(write_bytes=1000, read_bytes=2000)
        mock_process.num_fds.return_value = 10
        mock_process.num_threads.return_value = 5
        mock_process_class.return_value = mock_process
        
        # Create monitor
        limits = ExtensionResources(max_memory_mb=200, max_cpu_percent=50)
        violation_callback = Mock()
        
        monitor = ProcessMonitor('test-ext', 12345, limits, violation_callback)
        
        # Update usage
        monitor._update_usage()
        
        usage = monitor.get_current_usage()
        assert usage.cpu_percent == 15.0
        assert usage.memory_mb == 100.0
        assert usage.network_bytes_sent == 1000
        assert usage.file_descriptors == 10
    
    @patch('psutil.Process')
    def test_resource_violation_detection(self, mock_process_class):
        """Test resource violation detection."""
        # Mock process with high resource usage
        mock_process = Mock()
        mock_process.cpu_percent.return_value = 75.0  # Exceeds 50% limit
        mock_process.memory_info.return_value = Mock(rss=300 * 1024 * 1024)  # 300MB, exceeds 200MB limit
        mock_process.open_files.return_value = []
        mock_process.io_counters.return_value = Mock(write_bytes=0, read_bytes=0)
        mock_process.num_fds.return_value = 0
        mock_process.num_threads.return_value = 1
        mock_process_class.return_value = mock_process
        
        # Create monitor with strict limits
        limits = ExtensionResources(max_memory_mb=200, max_cpu_percent=50)
        violation_callback = Mock()
        
        monitor = ProcessMonitor('test-ext', 12345, limits, violation_callback)
        
        # Update usage and check violations
        monitor._update_usage()
        monitor._check_violations()
        
        # Should have called violation callback twice (CPU and memory)
        assert violation_callback.call_count == 2


class TestExtensionSandbox:
    """Test extension sandboxing."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.sandbox = ExtensionSandbox()
    
    @pytest.mark.asyncio
    async def test_create_sandbox(self):
        """Test sandbox creation."""
        manifest = ExtensionManifest(
            name='test-ext',
            version='1.0.0',
            display_name='Test Extension',
            description='Test',
            author='Test',
            license='MIT',
            category='test',
            resources=ExtensionResources(max_memory_mb=256),
            permissions=ExtensionPermissions(network_access=['external'])
        )
        
        config = await self.sandbox.create_sandbox('test-ext', manifest)
        
        assert config['extension_name'] == 'test-ext'
        assert 'sandbox_directory' in config
        assert 'environment_variables' in config
        assert 'resource_limits' in config
        assert 'network_restrictions' in config
        
        # Check sandbox directory exists
        sandbox_dir = Path(config['sandbox_directory'])
        assert sandbox_dir.exists()
        assert (sandbox_dir / 'data').exists()
        assert (sandbox_dir / 'logs').exists()
        assert (sandbox_dir / 'temp').exists()
        
        # Cleanup
        await self.sandbox.destroy_sandbox('test-ext')
    
    @pytest.mark.asyncio
    async def test_destroy_sandbox(self):
        """Test sandbox destruction."""
        manifest = ExtensionManifest(
            name='test-ext',
            version='1.0.0',
            display_name='Test Extension',
            description='Test',
            author='Test',
            license='MIT',
            category='test'
        )
        
        config = await self.sandbox.create_sandbox('test-ext', manifest)
        sandbox_dir = Path(config['sandbox_directory'])
        
        assert sandbox_dir.exists()
        
        await self.sandbox.destroy_sandbox('test-ext')
        
        assert not sandbox_dir.exists()
        assert 'test-ext' not in self.sandbox.sandbox_directories


class TestNetworkAccessController:
    """Test network access control."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.controller = NetworkAccessController()
    
    def test_set_network_rules(self):
        """Test setting network access rules."""
        rules = {
            'allow_outbound': True,
            'allow_inbound': False,
            'allowed_hosts': ['api.example.com'],
            'allowed_ports': [80, 443],
            'blocked_hosts': ['malicious.com'],
            'blocked_ports': [22]
        }
        
        self.controller.set_network_rules('test-ext', rules)
        
        assert 'test-ext' in self.controller.access_rules
        assert self.controller.access_rules['test-ext'] == rules
    
    def test_check_network_access(self):
        """Test network access checking."""
        rules = {
            'allow_outbound': True,
            'allow_inbound': False,
            'allowed_hosts': ['api.example.com'],
            'allowed_ports': [80, 443],
            'blocked_hosts': ['malicious.com'],
            'blocked_ports': [22]
        }
        
        self.controller.set_network_rules('test-ext', rules)
        
        # Should allow access to allowed host and port
        assert self.controller.check_network_access('test-ext', 'api.example.com', 443, 'outbound')
        
        # Should block access to blocked host
        assert not self.controller.check_network_access('test-ext', 'malicious.com', 80, 'outbound')
        
        # Should block access to blocked port
        assert not self.controller.check_network_access('test-ext', 'api.example.com', 22, 'outbound')
        
        # Should block inbound access
        assert not self.controller.check_network_access('test-ext', 'api.example.com', 80, 'inbound')


class TestExtensionSecurityManager:
    """Test the main security manager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.security_manager = ExtensionSecurityManager()
    
    @pytest.mark.asyncio
    async def test_initialize_extension_security(self):
        """Test extension security initialization."""
        manifest = ExtensionManifest(
            name='test-ext',
            version='1.0.0',
            display_name='Test Extension',
            description='Test',
            author='Test',
            license='MIT',
            category='test',
            permissions=ExtensionPermissions(
                data_access=['read'],
                system_access=['files'],
                network_access=['external']
            ),
            resources=ExtensionResources(max_memory_mb=256)
        )
        
        context = ExtensionContext(extension_name='test-ext')
        
        policy = await self.security_manager.initialize_extension_security(
            'test-ext', manifest, context
        )
        
        assert policy['extension_name'] == 'test-ext'
        assert 'permissions' in policy
        assert 'resource_limits' in policy
        assert 'sandbox_config' in policy
        assert 'network_rules' in policy
        
        # Check permissions were granted
        assert self.security_manager.check_permission('test-ext', 'data:read')
        assert self.security_manager.check_permission('test-ext', 'system:files')
        assert self.security_manager.check_permission('test-ext', 'network:external')
        
        # Cleanup
        await self.security_manager.cleanup_extension_security('test-ext')
    
    @pytest.mark.asyncio
    async def test_cleanup_extension_security(self):
        """Test extension security cleanup."""
        manifest = ExtensionManifest(
            name='test-ext',
            version='1.0.0',
            display_name='Test Extension',
            description='Test',
            author='Test',
            license='MIT',
            category='test',
            permissions=ExtensionPermissions(data_access=['read'])
        )
        
        context = ExtensionContext(extension_name='test-ext')
        
        await self.security_manager.initialize_extension_security(
            'test-ext', manifest, context
        )
        
        # Verify permission exists
        assert self.security_manager.check_permission('test-ext', 'data:read')
        
        await self.security_manager.cleanup_extension_security('test-ext')
        
        # Verify permission was revoked
        assert not self.security_manager.check_permission('test-ext', 'data:read')
    
    def test_get_security_status(self):
        """Test getting security status."""
        # Initialize security for an extension
        manifest = ExtensionManifest(
            name='test-ext',
            version='1.0.0',
            display_name='Test Extension',
            description='Test',
            author='Test',
            license='MIT',
            category='test',
            permissions=ExtensionPermissions(data_access=['read'])
        )
        
        context = ExtensionContext(extension_name='test-ext')
        
        # Grant permissions manually for testing
        self.security_manager.permission_manager.grant_permissions(
            'test-ext', manifest.permissions, 'system'
        )
        
        status = self.security_manager.get_security_status('test-ext')
        
        assert status['extension_name'] == 'test-ext'
        assert 'permissions' in status
        assert 'data:read' in status['permissions']
        assert 'resource_usage' in status
        assert 'recent_violations' in status


class TestSecurityDecorators:
    """Test security decorators."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.security_manager = ExtensionSecurityManager()
        set_security_manager(self.security_manager)
        
        # Grant some permissions for testing
        permissions = ExtensionPermissions(
            data_access=['read', 'write'],
            system_access=['files']
        )
        self.security_manager.permission_manager.grant_permissions(
            'test-ext', permissions, 'system'
        )
    
    def test_require_permission_decorator(self):
        """Test the require_permission decorator."""
        class TestExtension:
            def __init__(self):
                self.manifest = Mock()
                self.manifest.name = 'test-ext'
            
            @require_permission('data:read')
            def read_data(self):
                return "data"
            
            @require_permission('data:admin')
            def admin_operation(self):
                return "admin"
        
        ext = TestExtension()
        
        # Should succeed with granted permission
        result = ext.read_data()
        assert result == "data"
        
        # Should fail with missing permission
        with pytest.raises(PermissionError):
            ext.admin_operation()
    
    def test_require_permissions_decorator(self):
        """Test the require_permissions decorator."""
        class TestExtension:
            def __init__(self):
                self.manifest = Mock()
                self.manifest.name = 'test-ext'
            
            @require_permissions(['data:read', 'system:files'])
            def complex_operation(self):
                return "success"
            
            @require_permissions(['data:read', 'data:admin'])
            def restricted_operation(self):
                return "restricted"
        
        ext = TestExtension()
        
        # Should succeed with all required permissions
        result = ext.complex_operation()
        assert result == "success"
        
        # Should fail with missing permission
        with pytest.raises(PermissionError):
            ext.restricted_operation()
    
    def test_rate_limit_decorator(self):
        """Test the rate_limit decorator."""
        class TestExtension:
            def __init__(self):
                self.manifest = Mock()
                self.manifest.name = 'test-ext'
            
            @rate_limit(calls_per_minute=2)
            def limited_operation(self):
                return "success"
        
        ext = TestExtension()
        
        # First two calls should succeed
        assert ext.limited_operation() == "success"
        assert ext.limited_operation() == "success"
        
        # Third call should fail
        with pytest.raises(RuntimeError):
            ext.limited_operation()
    
    def test_audit_log_decorator(self):
        """Test the audit_log decorator."""
        class TestExtension:
            def __init__(self):
                self.manifest = Mock()
                self.manifest.name = 'test-ext'
                self.context = ExtensionContext(extension_name='test-ext')
            
            @audit_log('test_action', sensitive=True)
            def sensitive_operation(self):
                return "sensitive_data"
        
        ext = TestExtension()
        
        with patch('src.extensions.security_decorators.logger') as mock_logger:
            result = ext.sensitive_operation()
            assert result == "sensitive_data"
            
            # Should have logged the action
            mock_logger.info.assert_called()
    
    def test_security_context(self):
        """Test the SecurityContext context manager."""
        with SecurityContext('test-ext', ['data:read', 'system:files']) as ctx:
            # Should be able to create temp files
            temp_file = ctx.create_temp_file('.txt')
            assert os.path.exists(temp_file)
            
            temp_dir = ctx.create_temp_dir()
            assert os.path.exists(temp_dir)
        
        # Files should be cleaned up after context exit
        assert not os.path.exists(temp_file)
        assert not os.path.exists(temp_dir)
    
    def test_security_context_permission_check(self):
        """Test SecurityContext permission checking."""
        # Should fail with missing permission
        with pytest.raises(PermissionError):
            with SecurityContext('test-ext', ['data:admin']):
                pass
    
    def test_utility_functions(self):
        """Test security utility functions."""
        # Test check_extension_permission
        assert check_extension_permission('test-ext', 'data:read')
        assert not check_extension_permission('test-ext', 'data:admin')
        
        # Test get_extension_permissions
        from ..security_decorators import get_extension_permissions
        permissions = get_extension_permissions('test-ext')
        assert 'data:read' in permissions
        assert 'data:write' in permissions
        assert 'system:files' in permissions


class TestSecurityIntegration:
    """Test security system integration."""
    
    @pytest.mark.asyncio
    async def test_full_security_workflow(self):
        """Test complete security workflow."""
        # Create security manager
        security_manager = ExtensionSecurityManager()
        
        # Create extension manifest
        manifest = ExtensionManifest(
            name='integration-test',
            version='1.0.0',
            display_name='Integration Test Extension',
            description='Test extension for security integration',
            author='Test',
            license='MIT',
            category='test',
            permissions=ExtensionPermissions(
                data_access=['read', 'write'],
                system_access=['files'],
                network_access=['external']
            ),
            resources=ExtensionResources(
                max_memory_mb=256,
                max_cpu_percent=25,
                max_disk_mb=512
            )
        )
        
        context = ExtensionContext(extension_name='integration-test')
        
        # Initialize security
        policy = await security_manager.initialize_extension_security(
            'integration-test', manifest, context
        )
        
        # Verify security policy
        assert policy['extension_name'] == 'integration-test'
        assert 'sandbox_config' in policy
        assert 'network_rules' in policy
        
        # Check permissions
        assert security_manager.check_permission('integration-test', 'data:read')
        assert security_manager.check_permission('integration-test', 'data:write')
        assert security_manager.check_permission('integration-test', 'system:files')
        assert security_manager.check_permission('integration-test', 'network:external')
        
        # Get security status
        status = security_manager.get_security_status('integration-test')
        assert status['extension_name'] == 'integration-test'
        assert len(status['permissions']) > 0
        
        # Cleanup
        await security_manager.cleanup_extension_security('integration-test')
        
        # Verify cleanup
        assert not security_manager.check_permission('integration-test', 'data:read')
    
    @pytest.mark.asyncio
    async def test_security_health_check(self):
        """Test security manager health check."""
        security_manager = ExtensionSecurityManager()
        
        health = await security_manager.health_check()
        
        assert health['status'] == 'healthy'
        assert 'managed_extensions' in health
        assert 'total_violations' in health
        assert 'components' in health


if __name__ == '__main__':
    pytest.main([__file__])