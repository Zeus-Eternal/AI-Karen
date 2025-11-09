"""
Tests for Extension Performance Optimization

Tests all performance optimization components including caching, lazy loading,
resource optimization, scaling, and monitoring.
"""

import asyncio
import json
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import pytest

from .cache_manager import ExtensionCacheManager, CacheStats
from .lazy_loader import ExtensionLazyLoader, LoadingStrategy
from .resource_optimizer import ExtensionResourceOptimizer, ResourceLimits
from .scaling_manager import ExtensionScalingManager, ScalingRule, ScalingTrigger
from .performance_monitor import ExtensionPerformanceMonitor
from .integration import PerformanceIntegration
from .config import PerformanceConfig, ExtensionPerformanceConfig
from ..models import ExtensionManifest


class TestExtensionCacheManager:
    """Test extension cache manager functionality."""
    
    @pytest.fixture
    async def cache_manager(self):
        """Create a cache manager for testing."""
        manager = ExtensionCacheManager(max_size_mb=1, max_entries=10)
        await manager.start()
        yield manager
        await manager.stop()
    
    async def test_basic_cache_operations(self, cache_manager):
        """Test basic cache get/set operations."""
        # Test set and get
        await cache_manager.set("test_key", "test_value")
        value = await cache_manager.get("test_key")
        assert value == "test_value"
        
        # Test non-existent key
        value = await cache_manager.get("non_existent")
        assert value is None
    
    async def test_cache_ttl_expiration(self, cache_manager):
        """Test cache TTL expiration."""
        # Set with short TTL
        await cache_manager.set("ttl_key", "ttl_value", ttl=0.1)
        
        # Should be available immediately
        value = await cache_manager.get("ttl_key")
        assert value == "ttl_value"
        
        # Wait for expiration
        await asyncio.sleep(0.2)
        value = await cache_manager.get("ttl_key")
        assert value is None
    
    async def test_cache_size_limits(self, cache_manager):
        """Test cache size and entry limits."""
        # Fill cache beyond limits
        for i in range(15):  # More than max_entries (10)
            await cache_manager.set(f"key_{i}", f"value_{i}")
        
        stats = await cache_manager.get_stats()
        assert stats.entry_count <= 10  # Should not exceed max_entries
    
    async def test_cache_stats(self, cache_manager):
        """Test cache statistics tracking."""
        # Generate some cache activity
        await cache_manager.set("stats_key", "stats_value")
        await cache_manager.get("stats_key")  # Hit
        await cache_manager.get("non_existent")  # Miss
        
        stats = await cache_manager.get_stats()
        assert stats.hits >= 1
        assert stats.misses >= 1
        assert stats.hit_rate > 0


class TestExtensionLazyLoader:
    """Test extension lazy loader functionality."""
    
    @pytest.fixture
    def temp_extension_root(self):
        """Create temporary extension root directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    async def lazy_loader(self, temp_extension_root):
        """Create a lazy loader for testing."""
        cache_manager = ExtensionCacheManager(max_size_mb=1)
        await cache_manager.start()
        
        loader = ExtensionLazyLoader(
            extension_root=temp_extension_root,
            cache_manager=cache_manager,
            max_concurrent_loads=2
        )
        
        yield loader
        
        await loader.shutdown()
        await cache_manager.stop()
    
    def test_loading_strategy_configuration(self, lazy_loader):
        """Test loading strategy configuration."""
        asyncio.run(lazy_loader.configure_loading_strategy(
            extension_name="test_ext",
            strategy=LoadingStrategy.EAGER,
            priority=50,
            dependencies=["dep1", "dep2"]
        ))
        
        priority = lazy_loader._loading_priorities.get("test_ext")
        assert priority is not None
        assert priority.strategy == LoadingStrategy.EAGER
        assert priority.priority == 50
        assert priority.dependencies == ["dep1", "dep2"]
    
    async def test_extension_proxy_creation(self, lazy_loader):
        """Test extension proxy creation for lazy loading."""
        manifest = ExtensionManifest(
            name="test_ext",
            version="1.0.0",
            capabilities={"provides_ui": True}
        )
        
        manifests = {"test_ext": manifest}
        
        # Configure as lazy loading
        await lazy_loader.configure_loading_strategy(
            "test_ext", LoadingStrategy.LAZY
        )
        
        # Load extensions (should create proxy)
        result = await lazy_loader.load_extensions(manifests)
        
        assert "test_ext" in result
        # Should be a proxy, not the actual extension
        assert hasattr(result["test_ext"], '_loader')


class TestExtensionResourceOptimizer:
    """Test extension resource optimizer functionality."""
    
    @pytest.fixture
    async def resource_optimizer(self):
        """Create a resource optimizer for testing."""
        optimizer = ExtensionResourceOptimizer(
            monitoring_interval=0.1,  # Fast for testing
            optimization_interval=0.2
        )
        await optimizer.start()
        yield optimizer
        await optimizer.stop()
    
    @patch('psutil.Process')
    async def test_extension_registration(self, mock_process, resource_optimizer):
        """Test extension registration for monitoring."""
        mock_process.return_value.is_running.return_value = True
        
        limits = ResourceLimits(max_memory_mb=512, max_cpu_percent=50)
        
        await resource_optimizer.register_extension(
            extension_name="test_ext",
            process_id=12345,
            limits=limits
        )
        
        assert "test_ext" in resource_optimizer._extension_processes
        assert "test_ext" in resource_optimizer._resource_limits
    
    async def test_system_resource_usage(self, resource_optimizer):
        """Test system resource usage collection."""
        usage = await resource_optimizer.get_system_resource_usage()
        
        assert isinstance(usage, dict)
        assert 'memory_percent' in usage
        assert 'cpu_percent' in usage
    
    async def test_optimization_recommendations(self, resource_optimizer):
        """Test optimization recommendations generation."""
        # Add some mock resource usage history
        from .resource_optimizer import ResourceUsage
        
        usage_history = [
            ResourceUsage(
                extension_name="test_ext",
                timestamp=time.time(),
                memory_mb=100 + i * 50,  # Increasing memory usage
                cpu_percent=50 + i * 10,  # Increasing CPU usage
                disk_read_mb=0,
                disk_write_mb=0,
                network_sent_mb=0,
                network_recv_mb=0,
                file_handles=10,
                threads=5
            )
            for i in range(10)
        ]
        
        resource_optimizer._resource_usage_history["test_ext"] = usage_history
        
        recommendations = await resource_optimizer.get_optimization_recommendations()
        
        assert isinstance(recommendations, list)
        # Should have recommendations due to increasing resource usage
        assert len(recommendations) > 0


class TestExtensionScalingManager:
    """Test extension scaling manager functionality."""
    
    @pytest.fixture
    async def scaling_manager(self):
        """Create a scaling manager for testing."""
        resource_optimizer = Mock()
        resource_optimizer.get_resource_usage = AsyncMock(return_value=[])
        
        manager = ExtensionScalingManager(
            resource_optimizer=resource_optimizer,
            metrics_collection_interval=0.1,
            scaling_evaluation_interval=0.2
        )
        await manager.start()
        yield manager
        await manager.stop()
    
    async def test_scaling_configuration(self, scaling_manager):
        """Test scaling configuration."""
        from .scaling_manager import ScalingStrategy
        
        rules = [
            ScalingRule(
                trigger=ScalingTrigger.CPU_USAGE,
                threshold_up=70,
                threshold_down=30,
                cooldown_seconds=60,
                min_instances=1,
                max_instances=5,
                scale_up_step=1,
                scale_down_step=1
            )
        ]
        
        await scaling_manager.configure_scaling(
            extension_name="test_ext",
            strategy=ScalingStrategy.AUTO,
            rules=rules
        )
        
        assert "test_ext" in scaling_manager._scaling_rules
        assert len(scaling_manager._scaling_rules["test_ext"]) == 1
    
    async def test_instance_registration(self, scaling_manager):
        """Test extension instance registration."""
        instance = await scaling_manager.register_instance(
            extension_name="test_ext",
            instance_id="test_instance_1",
            process_id=12345
        )
        
        assert instance.extension_name == "test_ext"
        assert instance.instance_id == "test_instance_1"
        assert instance.process_id == 12345
        assert instance.status == "starting"
    
    async def test_load_balancing(self, scaling_manager):
        """Test load balancing across instances."""
        # Register multiple instances
        await scaling_manager.register_instance(
            "test_ext", "instance_1", 12345
        )
        await scaling_manager.register_instance(
            "test_ext", "instance_2", 12346
        )
        
        # Set instances to running status
        for instance in scaling_manager._extension_instances["test_ext"]:
            instance.status = "running"
        
        # Test round-robin load balancing
        instance1 = await scaling_manager.get_instance_for_request("test_ext")
        instance2 = await scaling_manager.get_instance_for_request("test_ext")
        
        assert instance1 is not None
        assert instance2 is not None
        assert instance1.instance_id != instance2.instance_id


class TestExtensionPerformanceMonitor:
    """Test extension performance monitor functionality."""
    
    @pytest.fixture
    async def performance_monitor(self):
        """Create a performance monitor for testing."""
        cache_manager = Mock()
        cache_manager.get_stats = AsyncMock(return_value=CacheStats())
        
        resource_optimizer = Mock()
        resource_optimizer.get_resource_usage = AsyncMock(return_value=[])
        
        scaling_manager = Mock()
        scaling_manager.get_scaling_metrics = AsyncMock(return_value=[])
        
        monitor = ExtensionPerformanceMonitor(
            cache_manager=cache_manager,
            resource_optimizer=resource_optimizer,
            scaling_manager=scaling_manager,
            monitoring_interval=0.1,
            alert_check_interval=0.2
        )
        await monitor.start()
        yield monitor
        await monitor.stop()
    
    async def test_threshold_configuration(self, performance_monitor):
        """Test performance threshold configuration."""
        thresholds = {
            'cpu_usage_percent': 80,
            'memory_usage_mb': 512,
            'average_response_time_ms': 1000
        }
        
        await performance_monitor.configure_thresholds(
            extension_name="test_ext",
            thresholds=thresholds
        )
        
        assert "test_ext" in performance_monitor._performance_thresholds
        assert performance_monitor._performance_thresholds["test_ext"] == thresholds
    
    async def test_custom_metric_collector(self, performance_monitor):
        """Test custom metric collector registration."""
        async def custom_collector():
            return {"custom_metric": 42.0}
        
        await performance_monitor.register_custom_metric_collector(
            extension_name="test_ext",
            collector=custom_collector
        )
        
        assert "test_ext" in performance_monitor._custom_metric_collectors
    
    async def test_performance_summary_generation(self, performance_monitor):
        """Test performance summary generation."""
        # Add mock performance metrics
        from .performance_monitor import PerformanceMetrics
        
        metrics = [
            PerformanceMetrics(
                extension_name="test_ext",
                timestamp=time.time() - i * 60,  # 1 minute intervals
                load_time_seconds=1.0,
                initialization_time_seconds=0.5,
                startup_memory_mb=100,
                cpu_usage_percent=50 + i * 5,
                memory_usage_mb=200 + i * 10,
                disk_io_mb_per_sec=1.0,
                network_io_mb_per_sec=0.5,
                requests_per_second=10.0,
                average_response_time_ms=100 + i * 10,
                error_rate_percent=1.0,
                cache_hit_rate=0.8,
                cache_size_mb=50,
                active_instances=1,
                scaling_events=0,
                custom_metrics={}
            )
            for i in range(10)
        ]
        
        performance_monitor._performance_metrics["test_ext"] = metrics
        
        summary = await performance_monitor.get_performance_summary(
            extension_name="test_ext",
            time_period_hours=1.0
        )
        
        assert summary is not None
        assert summary.extension_name == "test_ext"
        assert summary.avg_cpu_usage > 0
        assert summary.avg_memory_usage > 0
        assert len(summary.recommendations) >= 0


class TestPerformanceIntegration:
    """Test performance integration functionality."""
    
    @pytest.fixture
    def temp_extension_root(self):
        """Create temporary extension root directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    async def performance_integration(self, temp_extension_root):
        """Create a performance integration for testing."""
        integration = PerformanceIntegration(
            extension_root=temp_extension_root,
            cache_size_mb=1,
            max_concurrent_loads=2,
            enable_scaling=False,  # Disable for simpler testing
            enable_monitoring=False
        )
        await integration.start()
        yield integration
        await integration.stop()
    
    async def test_extension_configuration(self, performance_integration):
        """Test extension performance configuration."""
        manifest = ExtensionManifest(
            name="test_ext",
            version="1.0.0",
            capabilities={"provides_ui": True}
        )
        
        config = {
            'loading_strategy': 'eager',
            'loading_priority': 50,
            'resource_limits': {
                'max_memory_mb': 512,
                'max_cpu_percent': 70
            }
        }
        
        await performance_integration.configure_extension_performance(
            extension_name="test_ext",
            manifest=manifest,
            config=config
        )
        
        # Verify configuration was applied
        priority = performance_integration.lazy_loader._loading_priorities.get("test_ext")
        assert priority is not None
        assert priority.strategy.value == 'eager'
        assert priority.priority == 50
    
    async def test_performance_status(self, performance_integration):
        """Test performance status retrieval."""
        status = await performance_integration.get_performance_status()
        
        assert isinstance(status, dict)
        assert 'cache_stats' in status
        assert 'system_resources' in status
        assert 'loading_metrics' in status


class TestPerformanceConfig:
    """Test performance configuration functionality."""
    
    def test_default_config_creation(self):
        """Test default configuration creation."""
        from .config import create_default_config
        
        config = create_default_config()
        
        assert isinstance(config, PerformanceConfig)
        assert len(config.extension_configs) > 0
        assert 'security' in config.extension_configs
        assert 'auth' in config.extension_configs
    
    def test_config_serialization(self):
        """Test configuration serialization to/from dict."""
        config = PerformanceConfig()
        config.cache.max_size_mb = 512
        config.monitoring.enable_monitoring = False
        
        # Test to_dict
        config_dict = config.to_dict()
        assert config_dict['cache']['max_size_mb'] == 512
        assert config_dict['monitoring']['enable_monitoring'] is False
        
        # Test from_dict
        new_config = PerformanceConfig.from_dict(config_dict)
        assert new_config.cache.max_size_mb == 512
        assert new_config.monitoring.enable_monitoring is False
    
    def test_config_file_operations(self):
        """Test configuration file save/load operations."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = Path(f.name)
        
        try:
            # Create and save config
            config = PerformanceConfig()
            config.cache.max_size_mb = 1024
            config.save_to_file(config_path)
            
            # Load config
            loaded_config = PerformanceConfig.from_file(config_path)
            assert loaded_config.cache.max_size_mb == 1024
            
        finally:
            config_path.unlink(missing_ok=True)
    
    def test_extension_config_management(self):
        """Test extension-specific configuration management."""
        config = PerformanceConfig()
        
        # Test get_extension_config (creates if not exists)
        ext_config = config.get_extension_config("new_ext")
        assert ext_config.extension_name == "new_ext"
        assert "new_ext" in config.extension_configs
        
        # Test set_extension_config
        custom_config = ExtensionPerformanceConfig(
            extension_name="custom_ext",
            loading_strategy="eager",
            max_memory_mb=256
        )
        config.set_extension_config("custom_ext", custom_config)
        
        retrieved_config = config.get_extension_config("custom_ext")
        assert retrieved_config.loading_strategy == "eager"
        assert retrieved_config.max_memory_mb == 256


# Integration tests
class TestPerformanceIntegrationE2E:
    """End-to-end integration tests for performance optimization."""
    
    @pytest.fixture
    def temp_extension_root(self):
        """Create temporary extension root with mock extensions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            
            # Create mock extension directories
            for ext_name in ['test_ext_1', 'test_ext_2']:
                ext_dir = root / ext_name
                ext_dir.mkdir()
                
                # Create extension manifest
                manifest = {
                    "name": ext_name,
                    "version": "1.0.0",
                    "capabilities": {"provides_ui": True}
                }
                
                with open(ext_dir / "extension.json", 'w') as f:
                    json.dump(manifest, f)
                
                # Create extension module
                with open(ext_dir / "__init__.py", 'w') as f:
                    f.write(f"""
class Extension:
    def __init__(self, manifest):
        self.manifest = manifest
        self.name = "{ext_name}"
    
    async def initialize(self):
        pass
    
    async def shutdown(self):
        pass
""")
            
            yield root
    
    @pytest.fixture
    async def full_performance_system(self, temp_extension_root):
        """Create a full performance system for testing."""
        integration = PerformanceIntegration(
            extension_root=temp_extension_root,
            cache_size_mb=10,
            max_concurrent_loads=3,
            enable_scaling=True,
            enable_monitoring=True
        )
        await integration.start()
        yield integration
        await integration.stop()
    
    async def test_full_extension_loading_cycle(self, full_performance_system, temp_extension_root):
        """Test complete extension loading cycle with performance optimization."""
        # Create manifests for test extensions
        manifests = {}
        for ext_name in ['test_ext_1', 'test_ext_2']:
            manifest_path = temp_extension_root / ext_name / "extension.json"
            with open(manifest_path, 'r') as f:
                manifest_data = json.load(f)
            manifests[ext_name] = ExtensionManifest(**manifest_data)
        
        # Configure performance settings
        for ext_name in manifests.keys():
            await full_performance_system.configure_extension_performance(
                extension_name=ext_name,
                manifest=manifests[ext_name],
                config={
                    'loading_strategy': 'lazy',
                    'resource_limits': {'max_memory_mb': 256},
                    'monitoring': {'thresholds': {'cpu_usage_percent': 80}}
                }
            )
        
        # Load extensions with optimization
        loaded_extensions = await full_performance_system.load_extensions_optimized(manifests)
        
        assert len(loaded_extensions) == 2
        assert 'test_ext_1' in loaded_extensions
        assert 'test_ext_2' in loaded_extensions
        
        # Check performance status
        status = await full_performance_system.get_performance_status()
        assert 'cache_stats' in status
        assert 'system_resources' in status


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])