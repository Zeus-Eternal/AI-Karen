#!/usr/bin/env python3
"""
Verification script for the extension security and sandboxing system.

This script tests the security features to ensure they work correctly.
"""

import asyncio
import sys
import os
import tempfile
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.extensions.security import (
    ExtensionSecurityManager,
    ExtensionPermissionManager,
    ResourceLimitEnforcer,
    ExtensionSandbox,
    NetworkAccessController
)
from src.extensions.security_decorators import (
    require_permission,
    SecurityContext,
    set_security_manager,
    check_extension_permission
)
from src.extensions.models import (
    ExtensionManifest,
    ExtensionPermissions,
    ExtensionResources,
    ExtensionContext,
    ExtensionCapabilities
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecurityVerificationTests:
    """Test suite for security system verification."""
    
    def __init__(self):
        self.security_manager = ExtensionSecurityManager()
        set_security_manager(self.security_manager)
        self.test_results = []
    
    def run_test(self, test_name: str, test_func):
        """Run a test and record the result."""
        try:
            logger.info(f"Running test: {test_name}")
            test_func()
            self.test_results.append((test_name, True, None))
            logger.info(f"✅ {test_name} PASSED")
        except Exception as e:
            self.test_results.append((test_name, False, str(e)))
            logger.error(f"❌ {test_name} FAILED: {e}")
    
    async def run_async_test(self, test_name: str, test_func):
        """Run an async test and record the result."""
        try:
            logger.info(f"Running async test: {test_name}")
            await test_func()
            self.test_results.append((test_name, True, None))
            logger.info(f"✅ {test_name} PASSED")
        except Exception as e:
            self.test_results.append((test_name, False, str(e)))
            logger.error(f"❌ {test_name} FAILED: {e}")
    
    def test_permission_manager(self):
        """Test the permission manager."""
        pm = ExtensionPermissionManager()
        
        # Test granting permissions
        permissions = ExtensionPermissions(
            data_access=['read', 'write'],
            system_access=['files'],
            network_access=['external']
        )
        pm.grant_permissions('test-ext', permissions, 'admin')
        
        # Test checking permissions
        assert pm.check_permission('test-ext', 'data:read'), "Should have data:read permission"
        assert pm.check_permission('test-ext', 'data:write'), "Should have data:write permission"
        assert pm.check_permission('test-ext', 'system:files'), "Should have system:files permission"
        assert pm.check_permission('test-ext', 'network:external'), "Should have network:external permission"
        assert not pm.check_permission('test-ext', 'data:admin'), "Should not have data:admin permission"
        
        # Test revoking permissions
        pm.revoke_permissions('test-ext', ['data:write'], 'admin')
        assert pm.check_permission('test-ext', 'data:read'), "Should still have data:read permission"
        assert not pm.check_permission('test-ext', 'data:write'), "Should not have data:write permission after revoke"
        
        # Test revoking all permissions
        pm.revoke_all_permissions('test-ext', 'admin')
        assert not pm.check_permission('test-ext', 'data:read'), "Should not have any permissions after revoke all"
    
    def test_resource_limit_enforcer(self):
        """Test the resource limit enforcer."""
        enforcer = ResourceLimitEnforcer()
        
        # Test setting limits
        limits = ExtensionResources(
            max_memory_mb=512,
            max_cpu_percent=25,
            max_disk_mb=1024
        )
        enforcer.set_resource_limits('test-ext', limits)
        
        assert 'test-ext' in enforcer.resource_limits
        assert enforcer.resource_limits['test-ext'].max_memory_mb == 512
    
    async def test_extension_sandbox(self):
        """Test the extension sandbox."""
        sandbox = ExtensionSandbox()
        
        # Create test manifest
        manifest = ExtensionManifest(
            name='sandbox-test',
            version='1.0.0',
            display_name='Sandbox Test',
            description='Test extension for sandbox',
            author='Test',
            license='MIT',
            category='test',
            permissions=ExtensionPermissions(network_access=['external']),
            resources=ExtensionResources(max_memory_mb=256)
        )
        
        # Create sandbox
        config = await sandbox.create_sandbox('sandbox-test', manifest)
        
        assert config['extension_name'] == 'sandbox-test'
        assert 'sandbox_directory' in config
        assert 'environment_variables' in config
        
        # Check sandbox directory exists
        sandbox_dir = Path(config['sandbox_directory'])
        assert sandbox_dir.exists(), "Sandbox directory should exist"
        assert (sandbox_dir / 'data').exists(), "Data directory should exist"
        assert (sandbox_dir / 'logs').exists(), "Logs directory should exist"
        assert (sandbox_dir / 'temp').exists(), "Temp directory should exist"
        
        # Test sandbox info
        info = sandbox.get_sandbox_info('sandbox-test')
        assert info is not None
        assert info['extension_name'] == 'sandbox-test'
        
        # Destroy sandbox
        await sandbox.destroy_sandbox('sandbox-test')
        assert not sandbox_dir.exists(), "Sandbox directory should be cleaned up"
    
    def test_network_access_controller(self):
        """Test the network access controller."""
        controller = NetworkAccessController()
        
        # Set network rules
        rules = {
            'allow_outbound': True,
            'allow_inbound': False,
            'allowed_hosts': ['api.example.com'],
            'allowed_ports': [80, 443],
            'blocked_hosts': ['malicious.com'],
            'blocked_ports': [22]
        }
        controller.set_network_rules('test-ext', rules)
        
        # Test access checks
        assert controller.check_network_access('test-ext', 'api.example.com', 443, 'outbound'), "Should allow access to allowed host/port"
        assert not controller.check_network_access('test-ext', 'malicious.com', 80, 'outbound'), "Should block access to blocked host"
        assert not controller.check_network_access('test-ext', 'api.example.com', 22, 'outbound'), "Should block access to blocked port"
        assert not controller.check_network_access('test-ext', 'api.example.com', 80, 'inbound'), "Should block inbound access"
    
    async def test_security_manager_integration(self):
        """Test the main security manager integration."""
        # Create test manifest
        manifest = ExtensionManifest(
            name='integration-test',
            version='1.0.0',
            display_name='Integration Test',
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
        policy = await self.security_manager.initialize_extension_security(
            'integration-test', manifest, context
        )
        
        assert policy['extension_name'] == 'integration-test'
        assert 'sandbox_config' in policy
        assert 'network_rules' in policy
        
        # Check permissions
        assert self.security_manager.check_permission('integration-test', 'data:read')
        assert self.security_manager.check_permission('integration-test', 'data:write')
        assert self.security_manager.check_permission('integration-test', 'system:files')
        assert self.security_manager.check_permission('integration-test', 'network:external')
        
        # Get security status
        status = self.security_manager.get_security_status('integration-test')
        assert status['extension_name'] == 'integration-test'
        assert len(status['permissions']) > 0
        
        # Test health check
        health = await self.security_manager.health_check()
        assert health['status'] == 'healthy'
        
        # Cleanup
        await self.security_manager.cleanup_extension_security('integration-test')
        
        # Verify cleanup
        assert not self.security_manager.check_permission('integration-test', 'data:read')
    
    def test_security_decorators(self):
        """Test security decorators."""
        # Grant permissions for testing
        permissions = ExtensionPermissions(
            data_access=['read', 'write'],
            system_access=['files']
        )
        self.security_manager.permission_manager.grant_permissions(
            'decorator-test', permissions, 'system'
        )
        
        class TestExtension:
            def __init__(self):
                self.manifest = type('Manifest', (), {'name': 'decorator-test'})()
            
            @require_permission('data:read')
            def read_data(self):
                return "data"
            
            @require_permission('data:admin')
            def admin_operation(self):
                return "admin"
        
        ext = TestExtension()
        
        # Should succeed with granted permission
        result = ext.read_data()
        assert result == "data", "Should succeed with granted permission"
        
        # Should fail with missing permission
        try:
            ext.admin_operation()
            assert False, "Should have raised PermissionError"
        except PermissionError:
            pass  # Expected
    
    def test_security_context(self):
        """Test security context manager."""
        # Grant permissions for testing
        permissions = ExtensionPermissions(
            data_access=['read', 'write'],
            system_access=['files']
        )
        self.security_manager.permission_manager.grant_permissions(
            'context-test', permissions, 'system'
        )
        
        # Test successful context
        with SecurityContext('context-test', ['data:read', 'system:files']) as ctx:
            temp_file = ctx.create_temp_file('.txt')
            assert os.path.exists(temp_file), "Temp file should be created"
            
            temp_dir = ctx.create_temp_dir()
            assert os.path.exists(temp_dir), "Temp dir should be created"
        
        # Files should be cleaned up
        assert not os.path.exists(temp_file), "Temp file should be cleaned up"
        assert not os.path.exists(temp_dir), "Temp dir should be cleaned up"
        
        # Test permission failure
        try:
            with SecurityContext('context-test', ['data:admin']):
                pass
            assert False, "Should have raised PermissionError"
        except PermissionError:
            pass  # Expected
    
    def test_utility_functions(self):
        """Test security utility functions."""
        # Grant permissions for testing
        permissions = ExtensionPermissions(
            data_access=['read', 'write'],
            system_access=['files']
        )
        self.security_manager.permission_manager.grant_permissions(
            'utility-test', permissions, 'system'
        )
        
        # Test check_extension_permission
        assert check_extension_permission('utility-test', 'data:read')
        assert not check_extension_permission('utility-test', 'data:admin')
        
        # Test get_extension_permissions
        from src.extensions.security_decorators import get_extension_permissions
        perms = get_extension_permissions('utility-test')
        assert 'data:read' in perms
        assert 'data:write' in perms
        assert 'system:files' in perms
    
    def print_results(self):
        """Print test results summary."""
        passed = sum(1 for _, success, _ in self.test_results if success)
        total = len(self.test_results)
        
        print(f"\n{'='*60}")
        print(f"SECURITY SYSTEM VERIFICATION RESULTS")
        print(f"{'='*60}")
        print(f"Tests passed: {passed}/{total}")
        print(f"Success rate: {passed/total*100:.1f}%")
        print(f"{'='*60}")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! Security system is working correctly.")
        else:
            print("❌ Some tests failed. Check the logs above for details.")
            print("\nFailed tests:")
            for name, success, error in self.test_results:
                if not success:
                    print(f"  - {name}: {error}")
        
        return passed == total


async def main():
    """Run all security verification tests."""
    print("🔒 Starting Extension Security System Verification")
    print("="*60)
    
    tests = SecurityVerificationTests()
    
    # Run synchronous tests
    tests.run_test("Permission Manager", tests.test_permission_manager)
    tests.run_test("Resource Limit Enforcer", tests.test_resource_limit_enforcer)
    tests.run_test("Network Access Controller", tests.test_network_access_controller)
    tests.run_test("Security Decorators", tests.test_security_decorators)
    tests.run_test("Security Context", tests.test_security_context)
    tests.run_test("Utility Functions", tests.test_utility_functions)
    
    # Run asynchronous tests
    await tests.run_async_test("Extension Sandbox", tests.test_extension_sandbox)
    await tests.run_async_test("Security Manager Integration", tests.test_security_manager_integration)
    
    # Print results
    success = tests.print_results()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)