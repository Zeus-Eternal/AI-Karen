"""
Comprehensive Test Configuration
Shared fixtures and configuration for all comprehensive tests.
"""

import pytest
import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock
from typing import Dict, List, Any, Optional

# Add src directory to Python path for imports
src_path = Path(__file__).parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration settings."""
    return {
        "models_directory": "models",
        "cache_directory": "tests/comprehensive/cache",
        "results_directory": "tests/comprehensive/results",
        "timeout_seconds": 30,
        "performance_targets": {
            "response_time_reduction": 0.6,  # 60%
            "cpu_usage_limit": 5.0,  # 5%
            "cache_hit_rate_target": 0.6,  # 60%
            "gpu_acceleration_gain": 0.3  # 30%
        }
    }


@pytest.fixture(scope="session")
def mock_environment():
    """Set up mock environment variables for testing."""
    original_env = os.environ.copy()
    
    # Set test environment variables
    test_env = {
        "CUDA_VISIBLE_DEVICES": "0,1",
        "PYTORCH_CUDA_ALLOC_CONF": "max_split_size_mb:512",
        "TOKENIZERS_PARALLELISM": "false",
        "TRANSFORMERS_CACHE": "tests/comprehensive/cache/transformers",
        "HF_HOME": "tests/comprehensive/cache/huggingface"
    }
    
    for key, value in test_env.items():
        os.environ[key] = value
    
    yield test_env
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_torch():
    """Mock PyTorch for tests that don't require actual GPU operations."""
    torch_mock = Mock()
    torch_mock.cuda.is_available.return_value = True
    torch_mock.cuda.device_count.return_value = 2
    torch_mock.cuda.get_device_properties.return_value = Mock(
        name="NVIDIA GeForce RTX 3080",
        major=8, minor=6,
        total_memory=10737418240
    )
    torch_mock.cuda.mem_get_info.return_value = (8589934592, 10737418240)  # 8GB free, 10GB total
    torch_mock.cuda.set_device = Mock()
    torch_mock.cuda.empty_cache = Mock()
    
    return torch_mock


@pytest.fixture
def mock_psutil():
    """Mock psutil for system resource monitoring tests."""
    psutil_mock = Mock()
    
    # Mock process
    process_mock = Mock()
    process_mock.cpu_percent.return_value = 2.5  # 2.5% CPU usage
    process_mock.memory_info.return_value = Mock(rss=1073741824)  # 1GB RSS
    psutil_mock.Process.return_value = process_mock
    
    # Mock system info
    psutil_mock.cpu_count.return_value = 8
    psutil_mock.virtual_memory.return_value = Mock(total=17179869184)  # 16GB total
    psutil_mock.disk_usage.return_value = Mock(free=107374182400)  # 100GB free
    
    return psutil_mock


@pytest.fixture
async def mock_model_registry():
    """Provide a mock model registry for testing."""
    models = [
        {
            "id": "llama-2-7b",
            "name": "Llama 2 7B",
            "type": "LLAMA_CPP",
            "path": "/models/llama-cpp/llama-2-7b.gguf",
            "size": 7000000000,
            "modalities": ["TEXT"],
            "capabilities": ["CHAT", "REASONING"],
            "status": "AVAILABLE"
        },
        {
            "id": "gpt-3.5-turbo",
            "name": "GPT-3.5 Turbo",
            "type": "OPENAI",
            "path": "gpt-3.5-turbo",
            "size": 0,
            "modalities": ["TEXT"],
            "capabilities": ["CHAT", "CODE", "REASONING"],
            "status": "AVAILABLE"
        },
        {
            "id": "stable-diffusion-xl",
            "name": "Stable Diffusion XL",
            "type": "VISION",
            "path": "/models/vision/stable-diffusion-xl",
            "size": 6000000000,
            "modalities": ["TEXT", "IMAGE"],
            "capabilities": ["IMAGE_GENERATION"],
            "status": "AVAILABLE"
        },
        {
            "id": "whisper-large",
            "name": "Whisper Large",
            "type": "AUDIO",
            "path": "/models/audio/whisper-large",
            "size": 3000000000,
            "modalities": ["AUDIO", "TEXT"],
            "capabilities": ["SPEECH_TO_TEXT"],
            "status": "AVAILABLE"
        }
    ]
    
    return models


@pytest.fixture
def sample_queries():
    """Provide sample queries for testing."""
    return [
        {
            "query": "What is machine learning?",
            "complexity": "SIMPLE",
            "expected_response_time": 1.0,
            "modalities": ["TEXT"]
        },
        {
            "query": "Explain neural networks with code examples in Python",
            "complexity": "MODERATE", 
            "expected_response_time": 3.0,
            "modalities": ["TEXT"]
        },
        {
            "query": "Create a comprehensive web application using React and Node.js with authentication, database integration, and deployment instructions",
            "complexity": "COMPLEX",
            "expected_response_time": 8.0,
            "modalities": ["TEXT"]
        },
        {
            "query": "Generate an image of a sunset over mountains",
            "complexity": "MODERATE",
            "expected_response_time": 5.0,
            "modalities": ["TEXT", "IMAGE"]
        },
        {
            "query": "Transcribe this audio file and summarize the content",
            "complexity": "MODERATE",
            "expected_response_time": 4.0,
            "modalities": ["AUDIO", "TEXT"]
        }
    ]


@pytest.fixture
def performance_baseline():
    """Provide performance baseline measurements for comparison."""
    return {
        "response_times": {
            "simple_query": 2.0,  # seconds
            "moderate_query": 5.0,
            "complex_query": 10.0
        },
        "resource_usage": {
            "cpu_percent": 22.9,  # Current high CPU usage
            "memory_mb": 2048,
            "gpu_utilization": 0.0  # No GPU acceleration currently
        },
        "cache_performance": {
            "hit_rate": 0.2,  # 20% current hit rate
            "memory_usage_mb": 512
        }
    }


@pytest.fixture
def create_temp_models_dir(tmp_path):
    """Create a temporary models directory structure for testing."""
    def _create_models_dir():
        models_dir = tmp_path / "models"
        models_dir.mkdir()
        
        # Create subdirectories for different model types
        (models_dir / "llama-cpp").mkdir()
        (models_dir / "huggingface").mkdir()
        (models_dir / "transformers").mkdir()
        (models_dir / "vision").mkdir()
        (models_dir / "audio").mkdir()
        
        # Create sample model files
        (models_dir / "llama-cpp" / "llama-2-7b.gguf").touch()
        (models_dir / "huggingface" / "bert-base").mkdir()
        (models_dir / "huggingface" / "bert-base" / "config.json").write_text('{"model_type": "bert"}')
        
        return str(models_dir)
    
    return _create_models_dir


@pytest.fixture
def mock_cuda_devices():
    """Provide mock CUDA device information."""
    return [
        {
            "id": 0,
            "name": "NVIDIA GeForce RTX 4090",
            "memory_total": 24576,  # 24GB
            "memory_free": 20480,   # 20GB
            "compute_capability": "8.9"
        },
        {
            "id": 1,
            "name": "NVIDIA GeForce RTX 3080",
            "memory_total": 10240,  # 10GB
            "memory_free": 8192,    # 8GB
            "compute_capability": "8.6"
        }
    ]


@pytest.fixture(autouse=True)
def setup_test_directories(tmp_path):
    """Automatically set up test directories for each test."""
    # Create necessary directories
    cache_dir = tmp_path / "cache"
    results_dir = tmp_path / "results"
    logs_dir = tmp_path / "logs"
    
    cache_dir.mkdir()
    results_dir.mkdir()
    logs_dir.mkdir()
    
    # Set environment variables to use temp directories
    os.environ["TEST_CACHE_DIR"] = str(cache_dir)
    os.environ["TEST_RESULTS_DIR"] = str(results_dir)
    os.environ["TEST_LOGS_DIR"] = str(logs_dir)
    
    yield {
        "cache_dir": cache_dir,
        "results_dir": results_dir,
        "logs_dir": logs_dir
    }


# Pytest hooks for custom behavior
def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Register custom markers
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "gpu: mark test as requiring GPU")
    config.addinivalue_line("markers", "integration: mark test as integration test")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Add markers based on test file names
        if "gpu" in item.nodeid:
            item.add_marker(pytest.mark.gpu)
        if "performance" in item.nodeid:
            item.add_marker(pytest.mark.slow)
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)


def pytest_runtest_setup(item):
    """Set up individual tests."""
    # Skip GPU tests if no GPU available (in CI/CD environments)
    if "gpu" in item.keywords:
        try:
            import torch
            if not torch.cuda.is_available():
                pytest.skip("GPU not available")
        except ImportError:
            pytest.skip("PyTorch not available")


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up the test environment once per session."""
    print("\n🔧 Setting up comprehensive test environment...")
    
    # Create results directory
    results_dir = Path("tests/comprehensive/results")
    results_dir.mkdir(exist_ok=True)
    
    # Clear any existing test artifacts
    for file in results_dir.glob("*"):
        if file.is_file():
            file.unlink()
    
    yield
    
    print("\n🧹 Cleaning up test environment...")


# Custom assertions for comprehensive testing
class ComprehensiveAssertions:
    """Custom assertions for comprehensive testing."""
    
    @staticmethod
    def assert_performance_improvement(baseline: float, optimized: float, target_improvement: float):
        """Assert that performance improvement meets target."""
        improvement = (baseline - optimized) / baseline
        assert improvement >= target_improvement, (
            f"Performance improvement {improvement:.2%} does not meet target {target_improvement:.2%}"
        )
    
    @staticmethod
    def assert_resource_usage_within_limits(usage: float, limit: float, resource_type: str):
        """Assert that resource usage is within specified limits."""
        assert usage <= limit, (
            f"{resource_type} usage {usage} exceeds limit {limit}"
        )
    
    @staticmethod
    def assert_cache_efficiency(hit_rate: float, target_rate: float):
        """Assert that cache hit rate meets efficiency target."""
        assert hit_rate >= target_rate, (
            f"Cache hit rate {hit_rate:.2%} does not meet target {target_rate:.2%}"
        )


@pytest.fixture
def comprehensive_assertions():
    """Provide comprehensive assertion helpers."""
    return ComprehensiveAssertions()