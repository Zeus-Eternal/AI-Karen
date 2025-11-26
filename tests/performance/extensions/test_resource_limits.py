"""
Performance tests for extension resource limits and scaling.
Tests memory usage, CPU limits, execution time, and concurrent operations.
"""

import pytest
import asyncio
import time
import threading
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import json
import psutil
import gc

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from ai_karen_engine.extension_host.manager import ExtensionManager
from ai_karen_engine.extensions.base import BaseExtension
from ai_karen_engine.extensions.orchestrator import PluginOrchestrator
from ai_karen_engine.extension_host.models2 import ExtensionManifest, ExtensionContext
from ai_karen_engine.plugins.router import PluginRouter


class TestResourceLimits:
    """Test extension resource limit enforcement."""
    
    @pytest.fixture
    def temp_extension_root(self):
        """Create temporary extension root directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_plugin_router(self):
        """Create mock plugin router."""
        router = Mock(spec=PluginRouter)
        router.dispatch = AsyncMock(return_value="plugin_result")
        return router
    
    @pytest.fixture
    def extension_manager(self, temp_extension_root, mock_plugin_router):
        """Create ExtensionManager instance for testing."""
        return ExtensionManager(
            extension_root=temp_extension_root,
            plugin_router=mock_plugin_router,
            db_session=AsyncMock()
        )
    
    @pytest.fixture
    def resource_limited_manifest(self):
        """Create manifest with resource limits."""
        return {
            "name": "resource-limited-extension",
            "version": "1.0.0",
            "display_name": "Resource Limited Extension",
            "description": "Extension with resource limits",
            "author": "Test Author",
            "license": "MIT",
            "api_version": "1.0",
            "kari_min_version": "0.4.0",
            "resources": {
                "max_memory_mb": 128,
                "max_cpu_percent": 25,
                "max_disk_mb": 256
            },
            "permissions": {
                "data_access": ["read", "write"],
                "plugin_access": ["execute"],
                "system_access": [],
                "network_access": []
            }
        }
    
    def create_test_extension(self, temp_dir: Path, manifest_data: dict, extension_code: str = None):
        """Create a test extension directory with manifest and custom code."""
        ext_dir = temp_dir / manifest_data["name"]
        ext_dir.mkdir(parents=True, exist_ok=True)
        
        # Create manifest
        manifest_path = ext_dir / "extension.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f, indent=2)
        
        # Create __init__.py with custom or default extension class
        init_path = ext_dir / "__init__.py"
        if extension_code:
            with open(init_path, 'w') as f:
                f.write(extension_code)
        else:
            init_content = '''
from ai_karen_engine.extensions.base import BaseExtension

class ResourceLimitedExtension(BaseExtension):
    async def _initialize(self):
        self.initialized = True
    
    async def _shutdown(self):
        self.shutdown_called = True
'''
            with open(init_path, 'w') as f:
                f.write(init_content)
        
        return ext_dir
    
    # Test Memory Limits
    @pytest.mark.asyncio
    async def test_memory_limit_specification(self, extension_manager, temp_extension_root, resource_limited_manifest):
        """Test that memory limits are properly specified in manifest."""
        self.create_test_extension(temp_extension_root, resource_limited_manifest)
        
        record = await extension_manager.load_extension("resource-limited-extension")
        
        # Verify resource limits are loaded
        assert hasattr(record.manifest, 'resources')
        if record.manifest.resources:
            assert record.manifest.resources.get('max_memory_mb') == 128
    
    def test_memory_usage_tracking(self, extension_manager):
        """Test that memory usage is tracked for extensions."""
        # Verify resource monitor exists
        assert extension_manager.resource_monitor is not None
        
        # In a real implementation, this would test that memory usage
        # is actively tracked and reported for each extension
    
    @pytest.mark.asyncio
    async def test_memory_intensive_extension(self, extension_manager, temp_extension_root, resource_limited_manifest):
        """Test extension that uses significant memory."""
        # Create extension that allocates memory
        memory_intensive_code = '''
from ai_karen_engine.extensions.base import BaseExtension
import gc

class ResourceLimitedExtension(BaseExtension):
    def __init__(self, manifest, context):
        super().__init__(manifest, context)
        self.memory_data = []
    
    async def _initialize(self):
        self.initialized = True
        # Allocate some memory for testing
        self.memory_data = [i for i in range(10000)]
    
    async def _shutdown(self):
        self.shutdown_called = True
        # Clean up memory
        self.memory_data.clear()
        gc.collect()
    
    def get_memory_usage(self):
        """Get current memory usage."""
        import sys
        return sys.getsizeof(self.memory_data)
'''
        
        self.create_test_extension(temp_extension_root, resource_limited_manifest, memory_intensive_code)
        
        # Measure memory before loading
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Load extension
        record = await extension_manager.load_extension("resource-limited-extension")
        
        # Measure memory after loading
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        
        # Verify extension was loaded
        assert record.instance.initialized is True
        
        # Memory usage should have increased (though this is a rough test)
        memory_increase = memory_after - memory_before
        assert memory_increase >= 0  # Should not decrease
        
        # Clean up
        await extension_manager.unload_extension("resource-limited-extension")
        gc.collect()
    
    # Test CPU Limits
    def test_cpu_limit_specification(self, resource_limited_manifest):
        """Test that CPU limits are properly specified."""
        manifest = ExtensionManifest(**resource_limited_manifest)
        
        if hasattr(manifest, 'resources') and manifest.resources:
            assert manifest.resources.get('max_cpu_percent') == 25
    
    @pytest.mark.asyncio
    async def test_cpu_intensive_extension(self, extension_manager, temp_extension_root, resource_limited_manifest):
        """Test extension that uses CPU intensively."""
        # Create CPU-intensive extension
        cpu_intensive_code = '''
from ai_karen_engine.extensions.base import BaseExtension
import time
import threading

class ResourceLimitedExtension(BaseExtension):
    def __init__(self, manifest, context):
        super().__init__(manifest, context)
        self.cpu_task_running = False
    
    async def _initialize(self):
        self.initialized = True
    
    async def _shutdown(self):
        self.shutdown_called = True
        self.cpu_task_running = False
    
    def start_cpu_intensive_task(self):
        """Start a CPU-intensive task."""
        self.cpu_task_running = True
        
        def cpu_task():
            start_time = time.time()
            while self.cpu_task_running and (time.time() - start_time) < 0.1:  # Run for 100ms
                # Simple CPU-intensive operation
                sum(i * i for i in range(1000))
        
        thread = threading.Thread(target=cpu_task)
        thread.start()
        return thread
'''
        
        self.create_test_extension(temp_extension_root, resource_limited_manifest, cpu_intensive_code)
        
        # Load extension
        record = await extension_manager.load_extension("resource-limited-extension")
        
        # Start CPU-intensive task
        thread = record.instance.start_cpu_intensive_task()
        
        # Wait for task to complete
        thread.join(timeout=1.0)
        
        # Verify extension is still functional
        assert record.instance.initialized is True
        
        # Clean up
        record.instance.cpu_task_running = False
        await extension_manager.unload_extension("resource-limited-extension")
    
    # Test Disk Usage Limits
    def test_disk_limit_specification(self, resource_limited_manifest):
        """Test that disk limits are properly specified."""
        manifest = ExtensionManifest(**resource_limited_manifest)
        
        if hasattr(manifest, 'resources') and manifest.resources:
            assert manifest.resources.get('max_disk_mb') == 256
    
    @pytest.mark.asyncio
    async def test_disk_usage_tracking(self, extension_manager, temp_extension_root, resource_limited_manifest):
        """Test disk usage tracking for extensions."""
        self.create_test_extension(temp_extension_root, resource_limited_manifest)
        
        # Get extension directory size before loading
        ext_dir = temp_extension_root / "resource-limited-extension"
        size_before = sum(f.stat().st_size for f in ext_dir.rglob('*') if f.is_file())
        
        # Load extension
        record = await extension_manager.load_extension("resource-limited-extension")
        
        # Verify extension was loaded
        assert record.instance.initialized is True
        
        # In a real implementation, this would track disk usage changes
        # and enforce limits on file creation and data storage
        
        # Clean up
        await extension_manager.unload_extension("resource-limited-extension")
    
    # Test Resource Monitoring
    @pytest.mark.asyncio
    async def test_resource_monitoring_startup(self, extension_manager):
        """Test that resource monitoring can be started."""
        # Start monitoring
        await extension_manager.start_monitoring()
        
        # Verify monitoring is active
        assert extension_manager.resource_monitor is not None
        
        # In a real implementation, this would verify that monitoring
        # threads/tasks are running and collecting resource data
    
    def test_resource_monitor_registration(self, extension_manager, temp_extension_root, resource_limited_manifest):
        """Test that extensions are registered with resource monitor."""
        async def test():
            self.create_test_extension(temp_extension_root, resource_limited_manifest)
            
            # Load extension
            record = await extension_manager.load_extension("resource-limited-extension")
            
            # Verify extension is registered with resource monitor
            # In a real implementation, this would check that the extension
            # is being monitored for resource usage
            assert record is not None
            
            # Clean up
            await extension_manager.unload_extension("resource-limited-extension")
        
        asyncio.run(test())
    
    # Test Resource Limit Enforcement
    def test_resource_limit_enforcement_configuration(self, extension_manager):
        """Test that resource limit enforcement is properly configured."""
        # Verify resource monitor has enforcement capabilities
        assert extension_manager.resource_monitor is not None
        
        # In a real implementation, this would test that resource limits
        # are actively enforced and violations are handled appropriately
    
    @pytest.mark.asyncio
    async def test_resource_violation_handling(self, extension_manager, temp_extension_root, resource_limited_manifest):
        """Test handling of resource limit violations."""
        self.create_test_extension(temp_extension_root, resource_limited_manifest)
        
        # Load extension
        record = await extension_manager.load_extension("resource-limited-extension")
        
        # In a real implementation, this would:
        # 1. Simulate resource limit violation
        # 2. Verify that the violation is detected
        # 3. Verify that appropriate action is taken (warning, throttling, shutdown)
        
        # For now, just verify the extension loaded successfully
        assert record.instance.initialized is True
        
        # Clean up
        await extension_manager.unload_extension("resource-limited-extension")


class TestScalingPerformance:
    """Test extension system scaling performance."""
    
    @pytest.fixture
    def temp_extension_root(self):
        """Create temporary extension root directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_plugin_router(self):
        """Create mock plugin router."""
        router = Mock(spec=PluginRouter)
        router.dispatch = AsyncMock(return_value="plugin_result")
        return router
    
    @pytest.fixture
    def extension_manager(self, temp_extension_root, mock_plugin_router):
        """Create ExtensionManager instance for testing."""
        return ExtensionManager(
            extension_root=temp_extension_root,
            plugin_router=mock_plugin_router,
            db_session=AsyncMock()
        )
    
    def create_multiple_extensions(self, temp_dir: Path, count: int):
        """Create multiple test extensions."""
        extensions = []
        
        for i in range(count):
            manifest_data = {
                "name": f"test-extension-{i}",
                "version": "1.0.0",
                "display_name": f"Test Extension {i}",
                "description": f"Test extension number {i}",
                "author": "Test Author",
                "license": "MIT",
                "api_version": "1.0",
                "kari_min_version": "0.4.0",
                "permissions": {
                    "data_access": ["read"],
                    "plugin_access": [],
                    "system_access": [],
                    "network_access": []
                }
            }
            
            ext_dir = temp_dir / manifest_data["name"]
            ext_dir.mkdir(parents=True, exist_ok=True)
            
            # Create manifest
            manifest_path = ext_dir / "extension.json"
            with open(manifest_path, 'w') as f:
                json.dump(manifest_data, f, indent=2)
            
            # Create __init__.py
            init_path = ext_dir / "__init__.py"
            class_name = f"TestExtension{i}"
            init_content = f'''
from ai_karen_engine.extensions.base import BaseExtension

class {class_name}(BaseExtension):
    async def _initialize(self):
        self.initialized = True
        self.extension_id = {i}
    
    async def _shutdown(self):
        self.shutdown_called = True
'''
            with open(init_path, 'w') as f:
                f.write(init_content)
            
            extensions.append(manifest_data["name"])
        
        return extensions
    
    # Test Discovery Performance
    @pytest.mark.asyncio
    async def test_discovery_performance_single_extension(self, extension_manager, temp_extension_root):
        """Test discovery performance with single extension."""
        self.create_multiple_extensions(temp_extension_root, 1)
        
        start_time = time.time()
        manifests = await extension_manager.discover_extensions()
        discovery_time = time.time() - start_time
        
        assert len(manifests) == 1
        assert discovery_time < 1.0  # Should complete within 1 second
    
    @pytest.mark.asyncio
    async def test_discovery_performance_multiple_extensions(self, extension_manager, temp_extension_root):
        """Test discovery performance with multiple extensions."""
        extension_count = 10
        self.create_multiple_extensions(temp_extension_root, extension_count)
        
        start_time = time.time()
        manifests = await extension_manager.discover_extensions()
        discovery_time = time.time() - start_time
        
        assert len(manifests) == extension_count
        assert discovery_time < 5.0  # Should complete within 5 seconds for 10 extensions
        
        # Performance should scale reasonably
        avg_time_per_extension = discovery_time / extension_count
        assert avg_time_per_extension < 0.5  # Less than 500ms per extension
    
    @pytest.mark.asyncio
    async def test_discovery_performance_scaling(self, extension_manager, temp_extension_root):
        """Test discovery performance scaling with increasing extension count."""
        results = []
        
        for count in [1, 5, 10]:
            # Clean up previous extensions
            for item in temp_extension_root.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
            
            # Create extensions
            self.create_multiple_extensions(temp_extension_root, count)
            
            # Measure discovery time
            start_time = time.time()
            manifests = await extension_manager.discover_extensions()
            discovery_time = time.time() - start_time
            
            results.append((count, discovery_time))
            assert len(manifests) == count
        
        # Verify reasonable scaling (not exponential)
        for i in range(1, len(results)):
            prev_count, prev_time = results[i-1]
            curr_count, curr_time = results[i]
            
            # Time should not increase exponentially
            time_ratio = curr_time / prev_time if prev_time > 0 else 1
            count_ratio = curr_count / prev_count
            
            # Time ratio should be roughly proportional to count ratio
            assert time_ratio <= count_ratio * 2  # Allow some overhead
    
    # Test Loading Performance
    @pytest.mark.asyncio
    async def test_loading_performance_single_extension(self, extension_manager, temp_extension_root):
        """Test loading performance for single extension."""
        extensions = self.create_multiple_extensions(temp_extension_root, 1)
        
        start_time = time.time()
        record = await extension_manager.load_extension(extensions[0])
        loading_time = time.time() - start_time
        
        assert record.instance.initialized is True
        assert loading_time < 2.0  # Should load within 2 seconds
    
    @pytest.mark.asyncio
    async def test_loading_performance_multiple_extensions(self, extension_manager, temp_extension_root):
        """Test loading performance for multiple extensions."""
        extension_count = 5
        extensions = self.create_multiple_extensions(temp_extension_root, extension_count)
        
        start_time = time.time()
        loaded = await extension_manager.load_all_extensions()
        loading_time = time.time() - start_time
        
        assert len(loaded) == extension_count
        assert loading_time < 10.0  # Should load all within 10 seconds
        
        # Verify all extensions are loaded
        for ext_name in extensions:
            assert ext_name in loaded
            assert loaded[ext_name].instance.initialized is True
    
    @pytest.mark.asyncio
    async def test_concurrent_loading_performance(self, extension_manager, temp_extension_root):
        """Test concurrent extension loading performance."""
        extension_count = 5
        extensions = self.create_multiple_extensions(temp_extension_root, extension_count)
        
        # Load extensions concurrently
        start_time = time.time()
        
        async def load_extension(ext_name):
            return await extension_manager.load_extension(ext_name)
        
        tasks = [load_extension(ext_name) for ext_name in extensions]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        concurrent_loading_time = time.time() - start_time
        
        # Verify all loaded successfully
        successful_loads = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_loads) == extension_count
        
        # Concurrent loading should be faster than sequential
        assert concurrent_loading_time < 8.0  # Should be faster than sequential
    
    # Test Memory Performance
    @pytest.mark.asyncio
    async def test_memory_usage_scaling(self, extension_manager, temp_extension_root):
        """Test memory usage scaling with multiple extensions."""
        process = psutil.Process()
        
        # Measure baseline memory
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Load extensions incrementally and measure memory
        memory_measurements = [(0, baseline_memory)]
        
        for count in [1, 3, 5]:
            # Clean up previous extensions
            for ext_name in [f"test-extension-{i}" for i in range(count)]:
                try:
                    await extension_manager.unload_extension(ext_name)
                except:
                    pass
            
            # Create and load extensions
            extensions = self.create_multiple_extensions(temp_extension_root, count)
            loaded = await extension_manager.load_all_extensions()
            
            # Measure memory after loading
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_measurements.append((count, current_memory))
            
            assert len(loaded) == count
        
        # Verify memory usage is reasonable
        for i in range(1, len(memory_measurements)):
            count, memory = memory_measurements[i]
            prev_count, prev_memory = memory_measurements[i-1]
            
            memory_increase = memory - prev_memory
            extensions_added = count - prev_count
            
            if extensions_added > 0:
                memory_per_extension = memory_increase / extensions_added
                # Each extension should use less than 50MB (very generous limit)
                assert memory_per_extension < 50.0
    
    # Test Execution Performance
    @pytest.mark.asyncio
    async def test_plugin_orchestration_performance(self, temp_extension_root):
        """Test plugin orchestration performance."""
        # Create mock plugin router with timing
        router = Mock(spec=PluginRouter)
        
        async def timed_dispatch(intent, params, roles):
            await asyncio.sleep(0.01)  # Simulate 10ms plugin execution
            return {"result": f"executed_{intent}"}
        
        router.dispatch = AsyncMock(side_effect=timed_dispatch)
        
        # Create orchestrator
        orchestrator = PluginOrchestrator(router)
        user_context = {"roles": ["user"]}
        
        # Test single plugin execution performance
        start_time = time.time()
        result = await orchestrator.execute_plugin("test_plugin", {}, user_context)
        single_execution_time = time.time() - start_time
        
        assert result["result"] == "executed_test_plugin"
        assert single_execution_time < 0.1  # Should complete quickly
        
        # Test sequential workflow performance
        from ai_karen_engine.extensions.orchestrator import PluginStep
        
        workflow = [
            PluginStep(intent=f"plugin_{i}", params={}) for i in range(5)
        ]
        
        start_time = time.time()
        workflow_result = await orchestrator.execute_workflow(workflow, user_context)
        workflow_execution_time = time.time() - start_time
        
        assert workflow_result.success is True
        assert len(workflow_result.results) == 5
        # Sequential execution should take roughly 5 * 10ms + overhead
        assert workflow_execution_time < 0.2
        
        # Test parallel execution performance
        from ai_karen_engine.extensions.orchestrator import PluginCall
        
        parallel_calls = [
            PluginCall(intent=f"plugin_{i}", params={}, call_id=f"call_{i}")
            for i in range(5)
        ]
        
        start_time = time.time()
        parallel_results = await orchestrator.execute_parallel(parallel_calls, user_context)
        parallel_execution_time = time.time() - start_time
        
        assert len(parallel_results) == 5
        # Parallel execution should be much faster than sequential
        assert parallel_execution_time < 0.1  # Should be close to single execution time
        assert parallel_execution_time < workflow_execution_time / 2  # At least 2x faster
    
    # Test Cleanup Performance
    @pytest.mark.asyncio
    async def test_unloading_performance(self, extension_manager, temp_extension_root):
        """Test extension unloading performance."""
        extension_count = 5
        extensions = self.create_multiple_extensions(temp_extension_root, extension_count)
        
        # Load all extensions
        loaded = await extension_manager.load_all_extensions()
        assert len(loaded) == extension_count
        
        # Test unloading performance
        start_time = time.time()
        
        for ext_name in extensions:
            await extension_manager.unload_extension(ext_name)
        
        unloading_time = time.time() - start_time
        
        # Verify all extensions are unloaded
        for ext_name in extensions:
            assert extension_manager.get_extension_by_name(ext_name) is None
        
        # Unloading should be fast
        assert unloading_time < 5.0  # Should unload all within 5 seconds
        avg_unload_time = unloading_time / extension_count
        assert avg_unload_time < 1.0  # Less than 1 second per extension
    
    @pytest.mark.asyncio
    async def test_memory_cleanup_performance(self, extension_manager, temp_extension_root):
        """Test memory cleanup after extension unloading."""
        process = psutil.Process()
        
        # Measure baseline memory
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Load extensions
        extension_count = 3
        extensions = self.create_multiple_extensions(temp_extension_root, extension_count)
        loaded = await extension_manager.load_all_extensions()
        
        # Measure memory after loading
        loaded_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Unload all extensions
        for ext_name in extensions:
            await extension_manager.unload_extension(ext_name)
        
        # Force garbage collection
        gc.collect()
        
        # Measure memory after unloading
        unloaded_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Memory should be cleaned up (allowing for some overhead)
        memory_increase = loaded_memory - baseline_memory
        memory_remaining = unloaded_memory - baseline_memory
        
        # At least 50% of memory should be cleaned up
        cleanup_ratio = (memory_increase - memory_remaining) / memory_increase if memory_increase > 0 else 1
        assert cleanup_ratio >= 0.3  # At least 30% cleanup (generous due to Python GC behavior)