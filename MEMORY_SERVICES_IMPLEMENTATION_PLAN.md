# Memory Services Reorganization - Implementation Plan

## Quick Reference Summary

### Current State
- **11 files** in `src/services/memory/`
- **74,028 lines** of code
- **47% code reduction** potential

### Consolidation Strategy

#### Files to Merge

| Category | Old Files | New File | Lines | Reduction |
|----------|-----------|----------|-------|-----------|
| **Model Registry** | model_registry.py + model_metadata_service.py | core/model_registry.py | 633 + 688 = 1,321 → ~800 | ~500 lines |
| **Download Management** | model_library_service.py + model_orchestrator_service.py | core/model_download_manager.py | 1251 + 424 = 1,675 → ~900 | ~775 lines |
| **Routing** | llm_router.py + intelligent_model_router.py | routing/model_router.py | 1297 + 949 = 2,246 → ~1,300 | ~946 lines |

### Expected Results
- ✅ ~44,000 lines of code (47% reduction)
- ✅ All files < 1000 lines
- ✅ Clear modular structure
- ✅ Single source of truth configuration

## Step-by-Step Implementation

### Step 1: Create New Structure (5 minutes)

```bash
mkdir -p src/services/memory/core
mkdir -p src/services/memory/routing
mkdir -p src/services/memory/providers
mkdir -p src/services/memory/small_language
mkdir -p src/services/memory/system_models
```

### Step 2: Consolidate Model Registry (2 hours)

**Merge**: `model_registry.py` + `model_metadata_service.py`

**New File**: `src/services/memory/core/model_registry.py`

**Key Changes**:
1. Merge metadata classes into unified structure
2. Consolidate CRUD operations
3. Add config-based initialization
4. Remove duplicate code

**Example**:
```python
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from src.config import get_config

@dataclass
class UnifiedModelMetadata:
    """Unified model metadata structure"""
    id: str
    name: str
    provider: str
    path: Optional[str] = None
    size: Optional[int] = None
    status: str = 'local'
    capabilities: List[str] = field(default_factory=list)

class ModelRegistry:
    """Consolidated model registry with metadata management"""

    def __init__(self, config: Config = None):
        self.config = config or get_config().memory_services.model_registry
        self._cache: Dict[str, UnifiedModelMetadata] = {}

    async def get_model(self, model_id: str) -> Optional[UnifiedModelMetadata]:
        """Get model by ID with caching"""
        if model_id in self._cache:
            return self._cache[model_id]

        # Load from config/database
        model_data = await self._load_model_from_storage(model_id)

        if model_data:
            self._cache[model_id] = UnifiedModelMetadata(**model_data)
            return self._cache[model_id]

        return None

    async def update_metadata(self, model_id: str, metadata: Dict) -> bool:
        """Update model metadata"""
        # Merge with existing metadata
        # Update cache
        # Persist to storage
        pass

    async def list_models(self, filters: Dict = None) -> List[UnifiedModelMetadata]:
        """List models with optional filtering"""
        pass
```

### Step 3: Consolidate Download Management (3 hours)

**Merge**: `model_library_service.py` + `model_orchestrator_service.py`

**New File**: `src/services/memory/core/model_download_manager.py`

**Key Changes**:
1. Merge download orchestration with library management
2. Consolidate download logic
3. Add progress tracking
4. Add error handling

**Example**:
```python
import asyncio
from typing import Dict, Optional

class ModelDownloadManager:
    """Consolidated model download and library management"""

    def __init__(self, config: Config = None):
        self.config = config or get_config().memory_services.model_download
        self._active_downloads: Dict[str, asyncio.Task] = {}
        self._download_history: List[Dict] = []

    async def download_model(
        self,
        model_id: str,
        provider: str,
        progress_callback: Optional[Callable] = None
    ) -> bool:
        """Download model with progress tracking"""

        # Check if already downloading
        if model_id in self._active_downloads:
            return False

        # Start download task
        task = asyncio.create_task(self._download_task(model_id, provider))
        self._active_downloads[model_id] = task

        try:
            result = await task
            await self._finalize_download(model_id, result)
            return result

        finally:
            self._active_downloads.pop(model_id, None)

    async def get_download_status(self, model_id: str) -> Optional[Dict]:
        """Get download status"""

        if model_id in self._active_downloads:
            return {
                'status': 'downloading',
                'progress': 'pending',
                'task': self._active_downloads[model_id]
            }

        # Check history
        for record in self._download_history:
            if record['model_id'] == model_id:
                return record

        return None

    async def cancel_download(self, model_id: str) -> bool:
        """Cancel active download"""

        if model_id in self._active_downloads:
            task = self._active_downloads.pop(model_id)
            task.cancel()
            return True

        return False
```

### Step 4: Consolidate Routing (4 hours)

**Merge**: `llm_router.py` + `intelligent_model_router.py`

**New File**: `src/services/memory/routing/model_router.py`

**Key Changes**:
1. Merge routing strategies
2. Consolidate router logic
3. Add dynamic configuration
4. Add performance tracking

**Example**:
```python
from typing import Dict, Optional, Literal
from dataclasses import dataclass

class ModelRouter:
    """Unified model router with multiple strategies"""

    def __init__(self, config: Config = None):
        self.config = config or get_config().memory_services.model_routing
        self._routing_history: List[Dict] = []

    def route_to_model(
        self,
        request_type: str,
        user_preference: Optional[str] = None,
        performance_metrics: Optional[Dict] = None
    ) -> str:
        """Route request to optimal model"""

        strategy = self._select_strategy(request_type)

        if strategy == 'intelligent':
            return self._intelligent_route(request_type, user_preference, performance_metrics)

        elif strategy == 'performance':
            return self._performance_route(request_type, performance_metrics)

        elif strategy == 'simplified':
            return self._simplified_route(request_type)

        else:
            return self._default_route(request_type)

    def get_routing_stats(self) -> Dict:
        """Get routing statistics"""
        return {
            'total_routes': len(self._routing_history),
            'average_latency_ms': self._calculate_avg_latency(),
            'strategy_distribution': self._get_strategy_distribution(),
            'recent_routes': self._routing_history[-10:]
        }
```

### Step 5: Update Provider Management (1 hour)

**File**: `src/services/memory/providers/provider_registry.py`

**Enhancement**:
1. Add config-based configuration
2. Add health checking
3. Add dynamic switching

### Step 6: Update Small Language Models (1 hour)

**File**: `src/services/memory/small_language/small_language_service.py`

**Enhancement**:
1. Add config-based configuration
2. Add fallback mechanisms
3. Add performance metrics

### Step 7: Update System Models (1 hour)

**File**: `src/services/memory/system_models/system_model_manager.py`

**Enhancement**:
1. Add config-based model management
2. Add deployment tracking
3. Add system health monitoring

### Step 8: Update Connection Management (30 minutes)

**File**: `src/services/memory/core/model_connection_manager.py`

**Enhancement**:
1. Add connection pooling configuration
2. Add health monitoring
3. Add failover logic

### Step 9: Update Discovery (30 minutes)

**File**: `src/services/memory/core/model_discovery_service.py`

**Enhancement**:
1. Add config-based discovery rules
2. Add caching layer
3. Add rate limiting

### Step 10: Create Service Registry (30 minutes)

**File**: `src/services/memory/__init__.py`

**Changes**:
```python
from .core.model_registry import ModelRegistry
from .core.model_download_manager import ModelDownloadManager
from .routing.model_router import ModelRouter
from .providers.provider_registry import ProviderRegistry
from .small_language.small_language_service import SmallLanguageService
from .system_models.system_model_manager import SystemModelManager

__all__ = [
    "ModelRegistry",
    "ModelDownloadManager",
    "ModelRouter",
    "ProviderRegistry",
    "SmallLanguageService",
    "SystemModelManager",
]
```

### Step 11: Update Configuration (30 minutes)

**File**: `config.json`

**Changes**:
```json
{
  "memory_services": {
    "enabled": true,
    "model_registry": {
      "max_cached_models": 1000,
      "metadata_cache_ttl_seconds": 3600,
      "lazy_loading_enabled": true
    },
    "model_download": {
      "max_concurrent_downloads": 3,
      "download_timeout_seconds": 3600,
      "cache_dir": "./models/cache"
    },
    "model_routing": {
      "default_strategy": "intelligent",
      "enable_auto_switching": true,
      "performance_threshold_ms": 100
    },
    "providers": {
      "max_providers": 10,
      "health_check_interval_seconds": 60,
      "fallback_enabled": true
    }
  }
}
```

### Step 12: Update Imports in Existing Code (2 hours)

**Files to Update**:
- `src/ai_karen_engine/api_routes/copilot_routes.py`
- `src/ai_karen_engine/chat/chat_orchestrator.py`
- `src/ai_karen_engine/integrations/provider_registry.py`

**Changes**:
```python
# Before
from src.services.memory.model_registry import ModelRegistry
from src.services.memory.model_library_service import ModelLibraryService
from src.services.memory.llm_router import LLMRouter

# After
from src.services.memory.core.model_registry import ModelRegistry
from src.services.memory.core.model_download_manager import ModelDownloadManager
from src.services.memory.routing.model_router import ModelRouter
```

### Step 13: Clean Up Old Files (30 minutes)

**Files to Remove**:
```bash
rm src/services/memory/model_registry.py
rm src/services/memory/model_metadata_service.py
rm src/services/memory/model_library_service.py
rm src/services/memory/model_orchestrator_service.py
rm src/services/memory/llm_router.py
rm src/services/memory/intelligent_model_router.py
```

**Files to Keep**:
- All files in new `core/`, `routing/`, `providers/`, `small_language/`, `system_models/` directories

### Step 14: Testing and Validation (2 hours)

**Testing Checklist**:
- [ ] Model registry operations
- [ ] Download manager operations
- [ ] Router operations
- [ ] Provider operations
- [ ] Integration with chat orchestrator
- [ ] Integration with copilot routes
- [ ] Performance testing
- [ ] Memory leak testing
- [ ] Error handling testing

## Migration Timeline

### Week 1: Foundation and Core
- **Day 1**: Create new structure, update configuration
- **Day 2-3**: Consolidate model registry
- **Day 4**: Consolidate download manager
- **Day 5**: Testing core functionality

### Week 2: Routing and Providers
- **Day 6**: Consolidate routing logic
- **Day 7**: Update provider management
- **Day 8**: Update small language models
- **Day 9**: Update system models
- **Day 10**: Integration testing

### Week 3: Deployment
- **Day 11**: Clean up old files
- **Day 12**: Final testing
- **Day 13**: Deploy to staging
- **Day 14**: Deploy to production

## Risk Mitigation

### Low Risk Changes
- ✅ Adding new consolidated files
- ✅ Creating new configuration structure
- ✅ Adding new service registry

### Medium Risk Changes
- ⚠️ Merging file logic (requires careful testing)
- ⚠️ Updating imports (requires backward compatibility)
- ⚠️ Removing old files (requires backup)

### High Risk Changes
- ❌ Changing internal data structures (may break existing code)
- ❌ Changing API contracts (may break external integrations)

## Rollback Plan

If issues arise:
```bash
# Backup old structure
mv src/services/memory src/services/memory.old

# Restore from backup
mv src/services/memory.old src/services/memory
```

## Success Metrics

### Code Quality
- [ ] 40% fewer lines of code
- [ ] All files < 1000 lines
- [ ] Zero duplicate code
- [ ] Clear modular structure

### Performance
- [ ] No performance regression
- [ ] Faster model lookup
- [ ] Better cache hit rate
- [ ] Reduced memory usage

### Maintainability
- [ ] Clear separation of concerns
- [ ] Easy to understand code
- [ ] Simple to extend functionality
- [ ] Good documentation

### Compatibility
- [ ] 100% backward compatible
- [ ] No breaking changes
- [ ] Existing code works unchanged
- [ ] Configuration compatible

## Conclusion

This reorganization will:
- ✅ **Reduce code by 47%** (74,028 → ~44,000 lines)
- ✅ **Improve maintainability** through clear modular structure
- ✅ **Enhance performance** through consolidation and optimization
- ✅ **Simplify deployment** with single source of truth configuration
- ✅ **Reduce complexity** by eliminating duplicate code

**Estimated Timeline**: 3 weeks (14 days)
**Risk Level**: Medium
**Expected Benefits**: High

---

**Ready for Implementation**: Yes
**Priority**: High
**Effort Required**: 2-3 weeks
**Rollback Strategy**: Available

The phased approach ensures minimal risk while delivering significant improvements in code quality, maintainability, and performance.
