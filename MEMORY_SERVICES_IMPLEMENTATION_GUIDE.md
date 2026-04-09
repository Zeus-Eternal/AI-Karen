# Memory Services Implementation Guide

## Detailed File Mappings and Implementation

### Consolidation Strategy

#### 1. Model Registry Consolidation
**Files to Merge:**
- `model_registry.py` (553 lines)
- `model_metadata_service.py` (688 lines)

**New File:** `core/model_registry.py` (target: ~800 lines)

**Changes:**
1. Merge dataclasses into unified structure
2. Create single metadata management system
3. Integrate with config.json schema
4. Add cache management

**Key Data Structures:**
```python
@dataclass
class UnifiedModelMetadata:
    id: str
    name: str
    provider: str
    path: Optional[str] = None
    size: Optional[int] = None
    status: str  # 'local', 'available', 'downloading', 'error'
    capabilities: List[str]
    metadata: DetailedMetadata
    download_info: Optional[DownloadInfo] = None
    last_updated: float

@dataclass
class DetailedMetadata:
    parameters: str
    quantization: str
    memory_requirement: str
    context_length: int
    license: str
    tags: List[str]
    architecture: Optional[str] = None
    training_data: Optional[str] = None
    performance_metrics: Optional[Dict[str, Any]] = None
```

**API Methods to Preserve:**
- `get_model(model_id)`
- `list_models(filters)`
- `add_model(model)`
- `remove_model(model_id)`
- `search_models(query, filters)`
- `get_model_metadata(model_id)`
- `update_model_status(model_id, status)`

#### 2. Download Manager Consolidation
**Files to Merge:**
- `model_library_service.py` (ModelDownloadManager)
- `model_orchestrator_service.py` (download_model, remove_model)

**New File:** `core/model_downloader.py` (target: ~500 lines)

**Changes:**
1. Merge download logic into single class
2. Unified progress tracking
3. Better error handling
4. Integration with cache manager

**Key Features:**
```python
class UnifiedDownloadManager:
    async def download_model(self, model_id: str) -> DownloadResult
    async def download_with_progress(self, model_id: str, callback) -> DownloadResult
    async def cancel_download(self, download_id: str) -> bool
    async def remove_model(self, model_id: str, delete_files: bool = True) -> RemoveResult
    def get_download_status(self, download_id: str) -> Optional[DownloadTask]
    def cleanup(self)
```

#### 3. Discovery Service
**File to Refactor:** `model_discovery_service.py` (631 lines)

**New File:** `core/model_discovery.py` (target: ~500 lines)

**Changes:**
1. Simplify API
2. Better separation from internal engines
3. Add caching
4. Improved error handling

**Key Features:**
```python
class ModelDiscoveryService:
    async def discover_all() -> List[UnifiedModelMetadata]
    async def discover_models_by_provider(provider: str) -> List[UnifiedModelMetadata]
    async def validate_model(model_id: str) -> ValidationReport
    async def search(query: str, filters: DiscoveryFilters) -> List[UnifiedModelMetadata]
    def get_stats() -> DiscoveryStatistics
```

#### 4. Router Consolidation
**Files to Merge:**
- `llm_router.py` (1297+ lines)
- `intelligent_model_router.py` (949+ lines)

**New File:** `routing/model_router.py` (target: ~1200 lines)

**Changes:**
1. Merge routing strategies
2. Unified performance tracking
3. Better health integration
4. Cleaner API

**Key Features:**
```python
class ModelRouter:
    async def route(request: RoutingRequest) -> RoutingDecision
    async def select_provider(preferences: ProviderPreferences) -> Tuple[str, str]
    async def get_provider_health(provider: str) -> ProviderHealth
    def get_performance_metrics(model_id: str) -> PerformanceMetrics
    async def refresh_discovery() -> DiscoveryProgress
```

**Routing Strategies:**
- Priority-based (local-first)
- Round-robin
- Hybrid
- Capability-based

#### 5. Provider Management
**File to Refactor:** `provider_registry.py` (633 lines)

**New File:** `providers/provider_manager.py` (target: ~500 lines)

**Changes:**
1. Simplify API
2. Better integration with router
3. Cleaner health management
4. Configuration-based setup

**Key Features:**
```python
class ProviderManager:
    def register_provider(provider_class: Type[Provider])
    def get_provider_status(name: str) -> ProviderStatus
    def get_available_providers(capability: Optional[str] = None) -> List[str]
    def select_provider_with_fallback(preferred: str, capability: str) -> Optional[str]
    def get_system_status() -> SystemStatus
    def create_fallback_chain(name: str, primary: str, fallbacks: List[str])
```

#### 6. Small Language Service
**File to Refactor:** `small_language_model_service.py` (1151 lines)

**New File:** `small_language/small_language_service.py` (target: ~600 lines)

**Changes:**
1. Extract scaffolding engine as separate module
2. Better integration with router
3. Improved caching
4. Cleaner API

**Key Features:**
```python
class SmallLanguageService:
    async def generate_scaffold(text: str, type: str) -> ScaffoldResult
    async def generate_outline(text: str, style: str) -> OutlineResult
    async def summarize(text: str, type: str) -> SummaryResult
    def switch_model(model_id: str) -> bool
    def get_health_status() -> ServiceHealthStatus
```

#### 7. System Model Manager
**File to Refactor:** `system_model_manager.py` (786 lines)

**New File:** `system_models/system_manager.py` (target: ~500 lines)

**Changes:**
1. Integrate with unified registry
2. Better configuration validation
3. Simplified API
4. Performance recommendations

**Key Features:**
```python
class SystemModelManager:
    def get_system_models() -> List[SystemModelInfo]
    def get_model_configuration(model_id: str) -> Optional[Dict[str, Any]]
    def update_model_configuration(model_id: str, config: Dict[str, Any]) -> bool
    def get_hardware_recommendations(model_id: str) -> Dict[str, Any]
    def validate_configuration(model_id: str, config: Any) -> ValidationResult
```

#### 8. Connection Pooling
**File to Refactor:** `model_connection_manager.py` (694 lines)

**New File:** `core/model_connection_pool.py` (target: ~500 lines)

**Changes:**
1. Cleaner API
2. Better lifecycle management
3. Improved error handling
4. Reasoning flow integration

**Key Features:**
```python
class ModelConnectionPool:
    async def get_connection(model_id: str, session_id: str) -> Connection
    async def return_connection(connection: Connection)
    async def switch_model(from_id: str, to_id: str, session_id: str) -> bool
    def get_pool_stats() -> PoolStatistics
    async def drain_pool(model_id: str)
    async def close_pool(model_id: str)
```

## Implementation Steps

### Step 1: Setup New Structure (Week 1)
```bash
mkdir -p src/services/memory/core
mkdir -p src/services/memory/routing
mkdir -p src/services/memory/providers
mkdir -p src/services/memory/small_language
mkdir -p src/services/memory/system_models
mkdir -p src/services/memory/internal
```

### Step 2: Create Base Files
1. Create `__init__.py` files for all directories
2. Set up base configuration loader
3. Create base exceptions and logging utilities

### Step 3: Implement Core Services (Priority Order)
1. **Model Registry** - Foundation for everything
2. **Download Manager** - Critical for model availability
3. **Connection Pool** - Essential for performance
4. **Discovery Service** - For finding models

### Step 4: Implement Routing (Week 3-4)
1. **Provider Manager** - Independent of routing
2. **Model Router** - Depends on provider manager
3. **Small Language Service** - Depends on router

### Step 5: System Integration
1. Update factory pattern
2. Update dependency injection
3. Update API routes
4. Add configuration validation

### Step 6: Testing
1. Unit tests for each service
2. Integration tests
3. Performance tests
4. Regression tests

## Configuration Schema Update

### New config.json Structure

```json
{
  "models": {
    "enabled": true,
    "default_provider": "llamacpp",
    "default_model": "Phi-3-mini-4k-instruct-q4.gguf",
    "models_dir": "models",
    "discovery": {
      "enabled": true,
      "scan_interval_seconds": 3600,
      "validation_level": "standard"
    },
    "cache": {
      "enabled": true,
      "ttl_seconds": 300,
      "max_size": 1000
    },
    "download": {
      "max_concurrent": 3,
      "timeout_seconds": 300,
      "retry_attempts": 3
    },
    "models": [
      {
        "id": "default-lightweight-model",
        "name": "Default Lightweight Model",
        "provider": "llamacpp",
        "path": "models/llama-cpp/Qwen3-0.6B-Q4_K_M.gguf",
        "capabilities": ["text-generation", "chat", "local-inference"],
        "metadata": {
          "parameters": "0.6B",
          "quantization": "Q4_K_M",
          "memory_requirement": "~1GB",
          "context_length": 32768,
          "license": "Apache 2.0",
          "tags": ["chat", "small", "efficient"],
          "performance": {
            "inference_speed": "fast",
            "memory_efficiency": "high"
          }
        },
        "download_info": {
          "url": "https://huggingface.co/Qwen/Qwen3-0.6B-GGUF/resolve/main/Qwen3-0.6B-Q4_K_M.gguf",
          "checksum": "sha256:placeholder"
        }
      }
    ]
  },
  "providers": {
    "llamacpp": {
      "enabled": true,
      "config": {
        "quantization": "Q4_K_M",
        "context_length": 2048,
        "gpu_layers": 0,
        "threads": 4,
        "batch_size": 512
      },
      "health_check_interval_seconds": 300
    },
    "openai": {
      "enabled": true,
      "api_key_env": "OPENAI_API_KEY",
      "default_model": "gpt-4o-mini",
      "supports_streaming": true
    },
    "anthropic": {
      "enabled": true,
      "api_key_env": "ANTHROPIC_API_KEY",
      "default_model": "claude-3-5-sonnet-20241022",
      "supports_streaming": true
    },
    "gemini": {
      "enabled": true,
      "api_key_env": "GOOGLE_API_KEY",
      "default_model": "gemini-1.5-flash",
      "supports_streaming": true
    }
  },
  "routing": {
    "policy": "priority",
    "priority_order": ["local", "transformers", "nlp", "lightweight", "remote", "fallback"],
    "health": {
      "enabled": true,
      "check_interval_seconds": 300,
      "max_consecutive_failures": 3,
      "circuit_breaker_timeout_seconds": 60
    },
    "fallback": {
      "enabled": true,
      "chains": {
        "default": ["llamacpp", "openai", "gemini", "deepseek"],
        "code": ["llamacpp", "deepseek"],
        "reasoning": ["llamacpp", "openai"]
      }
    },
    "performance": {
      "tracking_enabled": true,
      "metrics_history_size": 1000
    }
  },
  "small_language": {
    "enabled": true,
    "default_model": "default-lightweight-model",
    "cache": {
      "enabled": true,
      "ttl_seconds": 1800,
      "max_size": 1000
    },
    "scaffolding": {
      "max_tokens": 100,
      "enable_fallback": true
    }
  },
  "system_models": {
    "enabled": true,
    "validate_configuration": true,
    "hardware_recommendations": true
  }
}
```

## Backward Compatibility

### Maintaining Old Imports
```python
# Old import path - still works
from services.memory.model_registry import EnhancedModelRegistry
from services.memory.model_library_service import ModelLibraryService
from services.memory.provider_registry import ProviderRegistryService
from services.memory.llm_router import LLMRouter
from services.memory.intelligent_model_router import ModelRouter
```

### New Import Path
```python
# New import path
from services.memory.core.model_registry import UnifiedModelRegistry
from services.memory.core.model_downloader import UnifiedDownloadManager
from services.memory.providers.provider_manager import ProviderManager
from services.memory.routing.model_router import ModelRouter
from services.memory.small_language.small_language_service import SmallLanguageService
```

### Deprecation Strategy
```python
# Add deprecation warnings in old files
import warnings
warnings.warn(
    "This module is deprecated. Use the new consolidated service from services.memory.core",
    DeprecationWarning,
    stacklevel=2
)
```

## Testing Strategy

### Unit Tests
```python
# tests/unit/test_model_registry.py
def test_model_registry_basic_operations():
    registry = UnifiedModelRegistry()
    model = UnifiedModelMetadata(...)
    registry.add_model(model)
    assert model.id in registry.list_models()

def test_model_registry_search():
    registry = UnifiedModelRegistry()
    # Add models
    results = registry.search("chat", capabilities=["text-generation"])
    assert len(results) > 0

def test_model_registry_caching():
    registry = UnifiedModelRegistry(cache_ttl=300)
    # First call
    model1 = registry.get_model("test")
    # Second call - should use cache
    model2 = registry.get_model("test")
    assert model1 is model2
```

### Integration Tests
```python
# tests/integration/test_model_discovery.py
async def test_discovery_and_routing():
    discovery = ModelDiscoveryService()
    router = ModelRouter()

    # Discover models
    models = await discovery.discover_all()
    assert len(models) > 0

    # Route through router
    decision = await router.route(
        RoutingRequest(
            task_type="chat",
            preferences={"provider": "llamacpp"}
        )
    )
    assert decision.provider in ["llamacpp", "openai", "gemini"]
```

### Performance Tests
```python
# tests/performance/test_router_performance.py
async def test_router_performance():
    router = ModelRouter()
    start = time.time()

    # Perform 1000 routes
    for _ in range(1000):
        await router.route(RoutingRequest(task_type="chat"))

    elapsed = time.time() - start
    assert elapsed < 10.0  # Should be under 10 seconds for 1000 routes
```

## Rollback Plan

If issues arise during migration:

1. **Immediate Rollback**: Use git revert for last commit
2. **Partial Rollback**: Restore only affected services
3. **Gradual Rollback**: Disable new services via configuration

### Rollback Steps
```bash
# Revert last commit
git revert HEAD

# Or selectively restore files
git checkout HEAD~1 -- src/services/memory/core/
git checkout HEAD~1 -- src/services/memory/routing/
```

## Success Criteria

### Code Quality
- [ ] Average file size < 600 lines
- [ ] No files > 1000 lines
- [ ] Consistent naming conventions
- [ ] 100% code coverage (unit tests)

### Performance
- [ ] No performance regression (< 5% difference)
- [ ] Cache hit rate > 80%
- [ ] Router response time < 100ms
- [ ] Discovery time < 5 seconds

### Maintainability
- [ ] Clear separation of concerns
- [ ] Easy to understand code flow
- [ ] Well-documented APIs
- [ ] Comprehensive test suite

### Compatibility
- [ ] No breaking changes
- [ ] All existing tests passing
- [ ] Backward compatibility maintained
- [ ] Configuration migration successful

## Next Steps

1. **Review and Approval**: Get stakeholder approval for the plan
2. **Setup Environment**: Create staging environment
3. **Begin Implementation**: Follow implementation guide
4. **Iterate**: Continuous integration and testing
5. **Deploy**: Gradual rollout with monitoring
6. **Optimize**: Refine based on production feedback
