"""
Performance tests for extension system scaling.
Tests concurrent operations, load handling, and system limits.
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
import concurrent.futures
import gc

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from ai_karen_engine.extensions.manager import ExtensionManager
from ai_karen_engine.extensions.base import BaseExtension
from ai_karen_engine.extensions.orchestrator import PluginOrchestrator, PluginStep, PluginCall
from ai_karen_engine.extensions.models import ExtensionManifest, ExtensionContext
from ai_karen_engine.plugins.router import PluginRouter


class TestConcurrentOperations:
    """Test concurrent extension operations."""
    
    @pytest.fixture
    def temp_extension_root(self):
        """Create temporary extension root directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_plugin_router(self):
        """Create mock plugin router with realistic delays."""
        router = Mock(spec=PluginRouter)
        
        async def mock_dispatch(intent, params, roles):
            # Simulate realistic plugin execution time
            await asyncio.sleep(0.01)  # 10ms
            return {"intent": intent, "params": params, "result": "success"}
        
        router.dispatch = AsyncMock(side_effect=mock_dispatch)
        router.list_intents = Mock(return_value=["test_plugin", "hello_world", "time_query"])
        return router
    
    @pytest.fixture
    def extension_manager(self, temp_extension_root, mock_plugin_router):
        """Create ExtensionManager instance for testing."""
        return ExtensionManager(
            extension_root=temp_extension_root,
            plugin_router=mock_plugin_router,
            db_session=AsyncMock()
        )
    
    def create_test_extensions(self, temp_dir: Path, count: int, with_delays: bool = False):
        """Create multiple test extensions."""
        extensions = []
        
        for i in range(count):
            manifest_data = {
                "name": f"concurrent-extension-{i}",
                "version": "1.0.0",
                "display_name": f"Concurrent Extension {i}",
                "description": f"Test extension for concurrency testing {i}",
                "author": "Test Author",
                "license": "MIT",
                "api_version": "1.0",
                "kari_min_version": "0.4.0",
                "capabilities": {
                    "provides_ui": False,
                    "provides_api": True,
                    "provides_background_tasks": False,
                    "provides_webhooks": False
                },
                "permissions": {
                    "data_access": ["read", "write"],
                    "plugin_access": ["execute"],
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
            
            # Create __init__.py with optional delays
            init_path = ext_dir / "__init__.py"
            class_name = f"ConcurrentExtension{i}"
            
            delay_code = ""
            if with_delays:
                delay_code = f"""
        import asyncio
        await asyncio.sleep(0.0{i+1})  # Variable delay for testing
"""
            
            init_content = f'''
from ai_karen_engine.extensions.base import BaseExtension
import asyncio
import time

class {class_name}(BaseExtension):
    def __init__(self, manifest, context):
        super().__init__(manifest, context)
        self.extension_id = {i}
        self.operations_count = 0
        self.concurrent_operations = 0
        self.max_concurrent = 0
    
    async def _initialize(self):
        {delay_code}
        self.initialized = True
        self.init_time = time.time()
    
    async def _shutdown(self):
        self.shutdown_called = True
        self.shutdown_time = time.time()
    
    async def perform_operation(self, operation_id):
        """Simulate an operation that can be called concurrently."""
        self.concurrent_operations += 1
        self.max_concurrent = max(self.max_concurrent, self.concurrent_operations)
        
        try:
            # Simulate work
            await asyncio.sleep(0.01)
            self.operations_count += 1
            return f"operation_{operation_id}_completed"
        finally:
            self.concurrent_operations -= 1
    
    def get_stats(self):
        """Get operation statistics."""
        return {{
            "extension_id": self.extension_id,
            "operations_count": self.operations_count,
            "max_concurrent": self.max_concurrent,
            "current_concurrent": self.concurrent_operations
        }}
'''
            with open(init_path, 'w') as f:
                f.write(init_content)
            
            extensions.append(manifest_data["name"])
        
        return extensions
    
    # Test Concurrent Extension Loading
    @pytest.mark.asyncio
    async def test_concurrent_extension_loading(self, extension_manager, temp_extension_root):
        """Test loading multiple extensions concurrently."""
        extension_count = 5
        extensions = self.create_test_extensions(temp_extension_root, extension_count, with_delays=True)
        
        # Load extensions concurrently
        start_time = time.time()
        
        async def load_extension(ext_name):
            return await extension_manager.load_extension(ext_name)
        
        # Create concurrent loading tasks
        tasks = [load_extension(ext_name) for ext_name in extensions]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        concurrent_time = time.time() - start_time
        
        # Verify all extensions loaded successfully
        successful_loads = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_loads) == extension_count
        
        # Concurrent loading should be faster than sequential
        # (Each extension has a delay, so concurrent should be much faster)
        assert concurrent_time < 1.0  # Should complete within 1 second
        
        # Verify all extensions are properly initialized
        for ext_name in extensions:
            record = extension_manager.get_extension_by_name(ext_name)
            assert record is not None
            assert record.instance.initialized is True
    
    @pytest.mark.asyncio
    async def test_concurrent_vs_sequential_loading_performance(self, extension_manager, temp_extension_root):
        """Compare concurrent vs sequential loading performance."""
        extension_count = 3
        extensions = self.create_test_extensions(temp_extension_root, extension_count, with_delays=True)
        
        # Test sequential loading
        start_time = time.time()
        for ext_name in extensions:
            await extension_manager.load_extension(ext_name)
        sequential_time = time.time() - start_time
        
        # Unload all extensions
        for ext_name in extensions:
            await extension_manager.unload_extension(ext_name)
        
        # Test concurrent loading
        start_time = time.time()
        tasks = [extension_manager.load_extension(ext_name) for ext_name in extensions]
        await asyncio.gather(*tasks)
        concurrent_time = time.time() - start_time
        
        # Concurrent should be significantly faster
        assert concurrent_time < sequential_time
        speedup_ratio = sequential_time / concurrent_time
        assert speedup_ratio > 1.5  # At least 50% faster
    
    # Test Concurrent Extension Operations
    @pytest.mark.asyncio
    async def test_concurrent_extension_operations(self, extension_manager, temp_extension_root):
        """Test concurrent operations within extensions."""
        extension_count = 3
        extensions = self.create_test_extensions(temp_extension_root, extension_count)
        
        # Load extensions
        loaded = await extension_manager.load_all_extensions()
        assert len(loaded) == extension_count
        
        # Perform concurrent operations on each extension
        operation_count = 10
        
        async def perform_operations(ext_name):
            record = extension_manager.get_extension_by_name(ext_name)
            tasks = [
                record.instance.perform_operation(f"{ext_name}_op_{i}")
                for i in range(operation_count)
            ]
            return await asyncio.gather(*tasks)
        
        # Run operations concurrently across all extensions
        start_time = time.time()
        extension_tasks = [perform_operations(ext_name) for ext_name in extensions]
        all_results = await asyncio.gather(*extension_tasks)
        operation_time = time.time() - start_time
        
        # Verify all operations completed
        total_operations = sum(len(results) for results in all_results)
        assert total_operations == extension_count * operation_count
        
        # Check operation statistics
        for ext_name in extensions:
            record = extension_manager.get_extension_by_name(ext_name)
            stats = record.instance.get_stats()
            
            assert stats["operations_count"] == operation_count
            assert stats["max_concurrent"] > 1  # Should have had concurrent operations
            assert stats["current_concurrent"] == 0  # All should be complete
        
        # Operations should complete in reasonable time
        assert operation_time < 2.0  # Should complete within 2 seconds
    
    # Test Plugin Orchestration Concurrency
    @pytest.mark.asyncio
    async def test_concurrent_plugin_orchestration(self, mock_plugin_router):
        """Test concurrent plugin orchestration performance."""
        orchestrator = PluginOrchestrator(mock_plugin_router)
        user_context = {"roles": ["user"]}
        
        # Test concurrent single plugin executions
        plugin_count = 20
        
        start_time = time.time()
        tasks = [
            orchestrator.execute_plugin(f"test_plugin", {"id": i}, user_context)
            for i in range(plugin_count)
        ]
        results = await asyncio.gather(*tasks)
        concurrent_plugin_time = time.time() - start_time
        
        assert len(results) == plugin_count
        assert all(result["result"] == "success" for result in results)
        
        # Should complete much faster than sequential execution
        # Sequential would take plugin_count * 0.01 seconds
        expected_sequential_time = plugin_count * 0.01
        assert concurrent_plugin_time < expected_sequential_time * 0.5  # At least 2x faster
    
    @pytest.mark.asyncio
    async def test_concurrent_workflow_execution(self, mock_plugin_router):
        """Test concurrent workflow execution."""
        orchestrator = PluginOrchestrator(mock_plugin_router)
        user_context = {"roles": ["user"]}
        
        # Create multiple workflows
        workflow_count = 5
        steps_per_workflow = 3
        
        workflows = []
        for i in range(workflow_count):
            workflow = [
                PluginStep(intent="test_plugin", params={"workflow": i, "step": j})
                for j in range(steps_per_workflow)
            ]
            workflows.append(workflow)
        
        # Execute workflows concurrently
        start_time = time.time()
        tasks = [
            orchestrator.execute_workflow(workflow, user_context)
            for workflow in workflows
        ]
        results = await asyncio.gather(*tasks)
        concurrent_workflow_time = time.time() - start_time
        
        # Verify all workflows completed successfully
        assert len(results) == workflow_count
        assert all(result.success for result in results)
        assert all(len(result.results) == steps_per_workflow for result in results)
        
        # Should be faster than sequential execution
        expected_sequential_time = workflow_count * steps_per_workflow * 0.01
        assert concurrent_workflow_time < expected_sequential_time * 0.7  # Significant speedup
    
    # Test Parallel Plugin Execution
    @pytest.mark.asyncio
    async def test_parallel_plugin_execution_scaling(self, mock_plugin_router):
        """Test parallel plugin execution scaling."""
        orchestrator = PluginOrchestrator(mock_plugin_router)
        user_context = {"roles": ["user"]}
        
        # Test different parallel execution sizes
        for parallel_count in [5, 10, 20]:
            plugin_calls = [
                PluginCall(intent="test_plugin", params={"id": i}, call_id=f"call_{i}")
                for i in range(parallel_count)
            ]
            
            start_time = time.time()
            results = await orchestrator.execute_parallel(plugin_calls, user_context)
            parallel_time = time.time() - start_time
            
            assert len(results) == parallel_count
            assert all(result["result"] == "success" for result in results)
            
            # Parallel execution should be close to single execution time
            # regardless of the number of parallel calls
            assert parallel_time < 0.1  # Should complete quickly
            
            # Time should not scale linearly with parallel count
            time_per_call = parallel_time / parallel_count
            assert time_per_call < 0.02  # Much less than sequential execution time
    
    # Test Resource Contention
    @pytest.mark.asyncio
    async def test_resource_contention_handling(self, extension_manager, temp_extension_root):
        """Test handling of resource contention between extensions."""
        extension_count = 5
        extensions = self.create_test_extensions(temp_extension_root, extension_count)
        
        # Load all extensions
        loaded = await extension_manager.load_all_extensions()
        assert len(loaded) == extension_count
        
        # Simulate resource contention by having all extensions
        # perform operations simultaneously
        contention_operations = 20
        
        async def stress_extension(ext_name):
            record = extension_manager.get_extension_by_name(ext_name)
            tasks = [
                record.instance.perform_operation(f"stress_{i}")
                for i in range(contention_operations)
            ]
            return await asyncio.gather(*tasks, return_exceptions=True)
        
        # Run stress test on all extensions simultaneously
        start_time = time.time()
        stress_tasks = [stress_extension(ext_name) for ext_name in extensions]
        all_stress_results = await asyncio.gather(*stress_tasks, return_exceptions=True)
        stress_time = time.time() - start_time
        
        # Verify system handled contention gracefully
        successful_extensions = [r for r in all_stress_results if not isinstance(r, Exception)]
        assert len(successful_extensions) == extension_count
        
        # All operations should have completed
        total_successful_ops = 0
        for ext_results in successful_extensions:
            successful_ops = [r for r in ext_results if not isinstance(r, Exception)]
            total_successful_ops += len(successful_ops)
        
        expected_total_ops = extension_count * contention_operations
        assert total_successful_ops == expected_total_ops
        
        # System should remain responsive under load
        assert stress_time < 5.0  # Should complete within reasonable time
    
    # Test Thread Safety
    def test_thread_safety_extension_operations(self, extension_manager, temp_extension_root):
        """Test thread safety of extension operations."""
        extension_count = 2
        extensions = self.create_test_extensions(temp_extension_root, extension_count)
        
        async def setup_and_test():
            # Load extensions
            loaded = await extension_manager.load_all_extensions()
            assert len(loaded) == extension_count
            
            # Test thread safety with concurrent access from multiple threads
            results = []
            errors = []
            
            def thread_worker(thread_id, ext_name):
                """Worker function to run in separate thread."""
                try:
                    # Get extension record
                    record = extension_manager.get_extension_by_name(ext_name)
                    if record:
                        # Access extension properties (should be thread-safe)
                        stats = record.instance.get_stats()
                        results.append((thread_id, ext_name, stats))
                    else:
                        errors.append(f"Thread {thread_id}: Extension {ext_name} not found")
                except Exception as e:
                    errors.append(f"Thread {thread_id}: {str(e)}")
            
            # Create multiple threads accessing extensions
            threads = []
            thread_count = 10
            
            for i in range(thread_count):
                ext_name = extensions[i % len(extensions)]  # Distribute across extensions
                thread = threading.Thread(target=thread_worker, args=(i, ext_name))
                threads.append(thread)
            
            # Start all threads
            for thread in threads:
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join(timeout=5.0)
            
            # Verify thread safety
            assert len(errors) == 0, f"Thread safety errors: {errors}"
            assert len(results) == thread_count
            
            # All threads should have successfully accessed extension data
            for thread_id, ext_name, stats in results:
                assert isinstance(stats, dict)
                assert "extension_id" in stats
        
        # Run the async test
        asyncio.run(setup_and_test())


class TestLoadHandling:
    """Test extension system load handling capabilities."""
    
    @pytest.fixture
    def temp_extension_root(self):
        """Create temporary extension root directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def high_load_plugin_router(self):
        """Create plugin router that simulates high load scenarios."""
        router = Mock(spec=PluginRouter)
        
        # Track call count for load testing
        router.call_count = 0
        router.concurrent_calls = 0
        router.max_concurrent = 0
        
        async def load_test_dispatch(intent, params, roles):
            router.concurrent_calls += 1
            router.max_concurrent = max(router.max_concurrent, router.concurrent_calls)
            router.call_count += 1
            
            try:
                # Simulate variable load based on intent
                if "heavy" in intent:
                    await asyncio.sleep(0.05)  # 50ms for heavy operations
                elif "medium" in intent:
                    await asyncio.sleep(0.02)  # 20ms for medium operations
                else:
                    await asyncio.sleep(0.01)  # 10ms for light operations
                
                return {
                    "intent": intent,
                    "call_id": router.call_count,
                    "concurrent_level": router.concurrent_calls,
                    "result": "success"
                }
            finally:
                router.concurrent_calls -= 1
        
        router.dispatch = AsyncMock(side_effect=load_test_dispatch)
        return router
    
    @pytest.fixture
    def extension_manager(self, temp_extension_root, high_load_plugin_router):
        """Create ExtensionManager for load testing."""
        return ExtensionManager(
            extension_root=temp_extension_root,
            plugin_router=high_load_plugin_router,
            db_session=AsyncMock()
        )
    
    def create_load_test_extension(self, temp_dir: Path, extension_name: str):
        """Create extension optimized for load testing."""
        manifest_data = {
            "name": extension_name,
            "version": "1.0.0",
            "display_name": f"Load Test Extension - {extension_name}",
            "description": "Extension for load testing",
            "author": "Test Author",
            "license": "MIT",
            "api_version": "1.0",
            "kari_min_version": "0.4.0",
            "capabilities": {
                "provides_ui": False,
                "provides_api": True,
                "provides_background_tasks": True,
                "provides_webhooks": False
            },
            "permissions": {
                "data_access": ["read", "write"],
                "plugin_access": ["execute"],
                "system_access": ["metrics"],
                "network_access": []
            }
        }
        
        ext_dir = temp_dir / extension_name
        ext_dir.mkdir(parents=True, exist_ok=True)
        
        # Create manifest
        manifest_path = ext_dir / "extension.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f, indent=2)
        
        # Create load test extension
        init_path = ext_dir / "__init__.py"
        class_name = "LoadTestExtension"
        
        init_content = f'''
from ai_karen_engine.extensions.base import BaseExtension
import asyncio
import time
import threading
from collections import defaultdict

class {class_name}(BaseExtension):
    def __init__(self, manifest, context):
        super().__init__(manifest, context)
        self.request_count = 0
        self.error_count = 0
        self.response_times = []
        self.concurrent_requests = 0
        self.max_concurrent = 0
        self.request_stats = defaultdict(int)
        self._lock = threading.Lock()
    
    async def _initialize(self):
        self.initialized = True
        self.start_time = time.time()
    
    async def _shutdown(self):
        self.shutdown_called = True
        self.end_time = time.time()
    
    async def handle_request(self, request_type="light", request_id=None):
        """Handle different types of requests for load testing."""
        start_time = time.time()
        
        with self._lock:
            self.concurrent_requests += 1
            self.max_concurrent = max(self.max_concurrent, self.concurrent_requests)
            self.request_count += 1
            self.request_stats[request_type] += 1
        
        try:
            # Use plugin orchestrator to simulate real workload
            result = await self.plugin_orchestrator.execute_plugin(
                intent=f"{{request_type}}_plugin",
                params={{"request_id": request_id or self.request_count}},
                user_context={{"roles": ["user"]}}
            )
            
            response_time = time.time() - start_time
            self.response_times.append(response_time)
            
            return {{
                "request_id": request_id or self.request_count,
                "request_type": request_type,
                "response_time": response_time,
                "result": result
            }}
            
        except Exception as e:
            with self._lock:
                self.error_count += 1
            raise
        finally:
            with self._lock:
                self.concurrent_requests -= 1
    
    def get_load_stats(self):
        """Get load testing statistics."""
        with self._lock:
            avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
            return {{
                "request_count": self.request_count,
                "error_count": self.error_count,
                "error_rate": self.error_count / max(self.request_count, 1),
                "avg_response_time": avg_response_time,
                "max_concurrent": self.max_concurrent,
                "current_concurrent": self.concurrent_requests,
                "request_stats": dict(self.request_stats),
                "uptime": time.time() - self.start_time if hasattr(self, 'start_time') else 0
            }}
    
    def reset_stats(self):
        """Reset load testing statistics."""
        with self._lock:
            self.request_count = 0
            self.error_count = 0
            self.response_times.clear()
            self.concurrent_requests = 0
            self.max_concurrent = 0
            self.request_stats.clear()
'''
        
        with open(init_path, 'w') as f:
            f.write(init_content)
        
        return ext_dir
    
    # Test High Load Scenarios
    @pytest.mark.asyncio
    async def test_high_concurrent_load(self, extension_manager, temp_extension_root):
        """Test system behavior under high concurrent load."""
        # Create load test extension
        self.create_load_test_extension(temp_extension_root, "load-test-extension")
        
        # Load extension
        record = await extension_manager.load_extension("load-test-extension")
        extension = record.instance
        
        # Generate high concurrent load
        concurrent_requests = 50
        request_types = ["light", "medium", "heavy"]
        
        async def generate_load():
            tasks = []
            for i in range(concurrent_requests):
                request_type = request_types[i % len(request_types)]
                task = extension.handle_request(request_type, f"req_{i}")
                tasks.append(task)
            
            return await asyncio.gather(*tasks, return_exceptions=True)
        
        # Execute load test
        start_time = time.time()
        results = await generate_load()
        load_test_time = time.time() - start_time
        
        # Analyze results
        successful_requests = [r for r in results if not isinstance(r, Exception)]
        failed_requests = [r for r in results if isinstance(r, Exception)]
        
        stats = extension.get_load_stats()
        
        # Verify system handled load appropriately
        assert len(successful_requests) > concurrent_requests * 0.8  # At least 80% success rate
        assert stats["error_rate"] < 0.2  # Less than 20% error rate
        assert stats["max_concurrent"] > 10  # Should have handled significant concurrency
        
        # Performance should be reasonable
        assert stats["avg_response_time"] < 0.2  # Average response time under 200ms
        assert load_test_time < 5.0  # Total test time under 5 seconds
        
        print(f"Load test results: {stats}")
    
    @pytest.mark.asyncio
    async def test_sustained_load(self, extension_manager, temp_extension_root):
        """Test system behavior under sustained load."""
        # Create load test extension
        self.create_load_test_extension(temp_extension_root, "sustained-load-extension")
        
        # Load extension
        record = await extension_manager.load_extension("sustained-load-extension")
        extension = record.instance
        
        # Generate sustained load over time
        duration_seconds = 2  # Run for 2 seconds
        requests_per_second = 20
        
        async def sustained_load_generator():
            start_time = time.time()
            request_id = 0
            
            while time.time() - start_time < duration_seconds:
                # Generate batch of requests
                batch_size = min(5, requests_per_second // 4)  # 4 batches per second
                
                batch_tasks = []
                for _ in range(batch_size):
                    request_id += 1
                    task = extension.handle_request("medium", f"sustained_{request_id}")
                    batch_tasks.append(task)
                
                # Execute batch
                await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # Wait before next batch
                await asyncio.sleep(0.25)  # 250ms between batches
        
        # Run sustained load test
        await sustained_load_generator()
        
        # Analyze sustained load performance
        stats = extension.get_load_stats()
        
        # System should maintain performance under sustained load
        expected_requests = duration_seconds * requests_per_second
        assert stats["request_count"] >= expected_requests * 0.8  # At least 80% of expected requests
        assert stats["error_rate"] < 0.1  # Less than 10% error rate under sustained load
        assert stats["avg_response_time"] < 0.15  # Maintain good response times
        
        print(f"Sustained load results: {stats}")
    
    @pytest.mark.asyncio
    async def test_burst_load_handling(self, extension_manager, temp_extension_root):
        """Test system behavior under burst load patterns."""
        # Create load test extension
        self.create_load_test_extension(temp_extension_root, "burst-load-extension")
        
        # Load extension
        record = await extension_manager.load_extension("burst-load-extension")
        extension = record.instance
        
        # Generate burst load pattern
        burst_sizes = [10, 25, 50, 25, 10]  # Variable burst sizes
        
        async def execute_burst(burst_size, burst_id):
            tasks = [
                extension.handle_request("light", f"burst_{burst_id}_req_{i}")
                for i in range(burst_size)
            ]
            return await asyncio.gather(*tasks, return_exceptions=True)
        
        # Execute bursts with delays between them
        all_results = []
        for i, burst_size in enumerate(burst_sizes):
            burst_results = await execute_burst(burst_size, i)
            all_results.extend(burst_results)
            
            # Small delay between bursts
            await asyncio.sleep(0.1)
        
        # Analyze burst handling
        stats = extension.get_load_stats()
        successful_requests = [r for r in all_results if not isinstance(r, Exception)]
        
        total_expected = sum(burst_sizes)
        assert len(successful_requests) >= total_expected * 0.9  # 90% success rate
        assert stats["error_rate"] < 0.1  # Low error rate
        assert stats["max_concurrent"] >= max(burst_sizes) * 0.5  # Handled significant concurrency
        
        print(f"Burst load results: {stats}")
    
    # Test Resource Exhaustion Scenarios
    @pytest.mark.asyncio
    async def test_resource_exhaustion_recovery(self, extension_manager, temp_extension_root):
        """Test system recovery from resource exhaustion."""
        # Create multiple extensions to compete for resources
        extension_count = 3
        extensions = []
        
        for i in range(extension_count):
            ext_name = f"resource-competition-{i}"
            self.create_load_test_extension(temp_extension_root, ext_name)
            extensions.append(ext_name)
        
        # Load all extensions
        loaded = await extension_manager.load_all_extensions()
        assert len(loaded) == extension_count
        
        # Generate competing load on all extensions
        async def compete_for_resources(ext_name, load_factor):
            record = extension_manager.get_extension_by_name(ext_name)
            extension = record.instance
            
            # Generate load proportional to load_factor
            request_count = 20 * load_factor
            tasks = [
                extension.handle_request("heavy", f"{ext_name}_req_{i}")
                for i in range(request_count)
            ]
            
            return await asyncio.gather(*tasks, return_exceptions=True)
        
        # Create competing load with different intensities
        load_factors = [1, 2, 3]  # Different load levels
        competition_tasks = [
            compete_for_resources(ext_name, load_factors[i])
            for i, ext_name in enumerate(extensions)
        ]
        
        # Execute competing load
        start_time = time.time()
        competition_results = await asyncio.gather(*competition_tasks, return_exceptions=True)
        competition_time = time.time() - start_time
        
        # Analyze resource competition results
        total_successful = 0
        total_requests = 0
        
        for i, (ext_name, results) in enumerate(zip(extensions, competition_results)):
            if not isinstance(results, Exception):
                successful = [r for r in results if not isinstance(r, Exception)]
                total_successful += len(successful)
                total_requests += len(results)
                
                record = extension_manager.get_extension_by_name(ext_name)
                stats = record.instance.get_load_stats()
                print(f"Extension {ext_name} stats: {stats}")
        
        # System should handle resource competition gracefully
        success_rate = total_successful / total_requests if total_requests > 0 else 0
        assert success_rate > 0.7  # At least 70% success rate under competition
        assert competition_time < 10.0  # Should complete within reasonable time
    
    # Test System Limits
    @pytest.mark.asyncio
    async def test_system_capacity_limits(self, extension_manager, temp_extension_root):
        """Test system behavior at capacity limits."""
        # Create extension for capacity testing
        self.create_load_test_extension(temp_extension_root, "capacity-test-extension")
        
        # Load extension
        record = await extension_manager.load_extension("capacity-test-extension")
        extension = record.instance
        
        # Gradually increase load to find capacity limits
        capacity_results = []
        
        for load_level in [10, 25, 50, 100]:
            # Reset stats for each test
            extension.reset_stats()
            
            # Generate load at current level
            tasks = [
                extension.handle_request("medium", f"capacity_{load_level}_{i}")
                for i in range(load_level)
            ]
            
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            test_time = time.time() - start_time
            
            # Collect capacity metrics
            stats = extension.get_load_stats()
            successful = [r for r in results if not isinstance(r, Exception)]
            
            capacity_results.append({
                "load_level": load_level,
                "success_count": len(successful),
                "success_rate": len(successful) / load_level,
                "avg_response_time": stats["avg_response_time"],
                "max_concurrent": stats["max_concurrent"],
                "test_time": test_time
            })
        
        # Analyze capacity scaling
        for i, result in enumerate(capacity_results):
            print(f"Load level {result['load_level']}: {result}")
            
            # Success rate should remain reasonable
            assert result["success_rate"] > 0.8  # At least 80% success
            
            # Response times should not degrade too much
            if i > 0:
                prev_response_time = capacity_results[i-1]["avg_response_time"]
                current_response_time = result["avg_response_time"]
                
                # Response time should not increase by more than 3x
                if prev_response_time > 0:
                    degradation_factor = current_response_time / prev_response_time
                    assert degradation_factor < 3.0  # Reasonable performance degradation
        
        # System should handle increasing load gracefully
        final_result = capacity_results[-1]
        assert final_result["success_rate"] > 0.7  # Still functional at high load
        assert final_result["avg_response_time"] < 0.5  # Response times under 500ms