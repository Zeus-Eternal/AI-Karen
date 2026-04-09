# Memory Services Reorganization - Quick Reference

## Immediate Actions (Priority Order)

### 1. Consolidate Model Registry ⚠️ HIGH PRIORITY
```python
# OLD: Separate files
model_registry.py (553 lines)
model_metadata_service.py (688 lines)

# NEW: Single file
src/services/memory/core/model_registry.py (~800 lines)
```

**Actions:**
- Merge UnifiedModelMetadata dataclass
- Create single get_model() and list_models() API
- Integrate with config.json models section
- Keep old files with deprecation warnings

**File to Create:** `src/services/memory/core/model_registry.py`

### 2. Consolidate Download Manager ⚠️ HIGH PRIORITY
```python
# OLD: Duplicate logic
model_library_service.py (ModelDownloadManager)
model_orchestrator_service.py (download_model, remove_model)

# NEW: Unified
src/services/memory/core/model_downloader.py (~500 lines)
```

**Actions:**
- Merge download progress tracking
- Create unified download API
- Consolidate retry logic
- Improve error handling

**File to Create:** `src/services/memory/core/model_downloader.py`

### 3. Consolidate Routing ⚠️ HIGH PRIORITY
```python
# OLD: Separate routers
llm_router.py (1297 lines)
intelligent_model_router.py (949 lines)

# NEW: Single router
src/services/memory/routing/model_router.py (~1200 lines)
```

**Actions:**
- Merge routing strategies (priority, round-robin, hybrid)
- Unified performance tracking
- Integrate health monitoring
- Cleaner API

**File to Create:** `src/services/memory/routing/model_router.py`

### 4. Refactor Small Language Service 🟡 MEDIUM PRIORITY
```python
# OLD: Large monolithic
small_language_model_service.py (1151 lines)

# NEW: Split
src/services/memory/small_language/small_language_service.py (~600 lines)
src/services/memory/small_language/scaffolding_engine.py (~400 lines)
```

**Actions:**
- Extract scaffolding engine
- Improve caching
- Better integration with router
- Cleaner API

**Files to Create:**
- `src/services/memory/small_language/small_language_service.py`
- `src/services/memory/small_language/scaffolding_engine.py`

### 5. Simplify Provider Management 🟡 MEDIUM PRIORITY
```python
# OLD: Large service
provider_registry.py (633 lines)

# NEW: Simpler
src/services/memory/providers/provider_manager.py (~500 lines)
```

**Actions:**
- Simplify API
- Better integration with router
- Cleaner health management
- Configuration-based setup

**File to Create:** `src/services/memory/providers/provider_manager.py`

### 6. Refactor System Model Manager 🟡 MEDIUM PRIORITY
```python
# OLD: Large service
system_model_manager.py (786 lines)

# NEW: Simpler
src/services/memory/system_models/system_manager.py (~500 lines)
```

**Actions:**
- Integrate with unified registry
- Better configuration validation
- Simplified API
- Performance recommendations

**File to Create:** `src/services/memory/system_models/system_manager.py`

## Directory Structure

### New Structure
```
src/services/memory/
├── core/                          # Core model services
│   ├── __init__.py
│   ├── model_registry.py          # [NEW] Model registry
│   ├── model_downloader.py        # [NEW] Download manager
│   ├── model_connection_pool.py   # [NEW] Connection pool
│   └── model_discovery.py         # [NEW] Discovery service
├── routing/                       # Routing services
│   ├── __init__.py
│   └── model_router.py            # [NEW] Unified router
├── providers/                     # Provider management
│   ├── __init__.py
│   └── provider_manager.py        # [NEW] Provider manager
├── small_language/                # Small language models
│   ├── __init__.py
│   ├── small_language_service.py  # [NEW] Small LM service
│   └── scaffolding_engine.py      # [NEW] Scaffolding engine
├── system_models/                 # System models
│   ├── __init__.py
│   └── system_manager.py          # [NEW] System model manager
├── internal/                      # Internal utilities
│   ├── __init__.py
│   ├── discovery_engine.py        # [KEEP] Discovery engine
│   ├── validation_system.py       # [KEEP] Validation system
│   └── cache_manager.py           # [NEW] Unified cache
├── old/                           # Old files (for reference)
│   ├── provider_registry.py
│   ├── model_registry.py
│   ├── model_library_service.py
│   ├── model_connection_manager.py
│   ├── model_discovery_service.py
│   ├── model_metadata_service.py
│   ├── model_orchestrator_service.py
│   ├── small_language_model_service.py
│   ├── system_model_manager.py
│   ├── llm_router.py
│   └── intelligent_model_router.py
└── __init__.py
```

## Configuration Updates

### Update `config.json`

```json
{
  "models": {
    "enabled": true,
    "default_provider": "llamacpp",
    "default_model": "Phi-3-mini-4k-instruct-q4.gguf",
    "discovery": {
      "enabled": true,
      "scan_interval_seconds": 3600
    },
    "cache": {
      "ttl_seconds": 300,
      "max_size": 1000
    },
    "download": {
      "max_concurrent": 3,
      "timeout_seconds": 300
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
          "memory_requirement": "~1GB"
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
        "gpu_layers": 0
      }
    }
  },
  "routing": {
    "policy": "priority",
    "priority_order": ["local", "transformers", "nlp", "lightweight", "remote", "fallback"]
  }
}
```

## API Examples

### Before (Old API)
```python
# Old way - separate files
from services.memory.model_registry import EnhancedModelRegistry
registry = EnhancedModelRegistry()

from services.memory.model_library_service import ModelLibraryService
library = ModelLibraryService()

from services.memory.llm_router import LLMRouter
router = LLMRouter()
```

### After (New API)
```python
# New way - consolidated
from services.memory.core.model_registry import UnifiedModelRegistry
registry = UnifiedModelRegistry()

from services.memory.core.model_downloader import UnifiedDownloadManager
downloader = UnifiedDownloadManager()

from services.memory.routing.model_router import ModelRouter
router = ModelRouter()
```

### Backward Compatibility
```python
# Old imports still work (with deprecation warning)
from services.memory.model_registry import EnhancedModelRegistry
# DeprecationWarning: This module is deprecated. Use UnifiedModelRegistry

# Or use compatibility wrapper
from services.memory.core.model_registry import UnifiedModelRegistry as EnhancedModelRegistry
```

## Testing Checklist

### Unit Tests
- [ ] Test model registry operations
- [ ] Test download manager lifecycle
- [ ] Test router routing strategies
- [ ] Test provider management
- [ ] Test small language service
- [ ] Test system model manager

### Integration Tests
- [ ] Test discovery and routing integration
- [ ] Test download and registry integration
- [ ] Test health monitoring integration
- [ ] Test configuration loading

### Performance Tests
- [ ] Test cache hit rates
- [ ] Test connection pooling
- [ ] Test router performance (1000 routes < 10s)
- [ ] Test discovery performance (< 5s)

### Compatibility Tests
- [ ] Test all existing imports work
- [ ] Test backward compatibility
- [ ] Test configuration migration
- [ ] Test factory pattern integration

## Migration Timeline

### Week 1: Foundation
- [ ] Create new directory structure
- [ ] Implement unified configuration schema
- [ ] Implement unified model registry

### Week 2: Core Services
- [ ] Implement download manager
- [ ] Implement connection pool
- [ ] Refactor discovery service

### Week 3: Routing and Providers
- [ ] Consolidate routing logic
- [ ] Refactor provider management
- [ ] Refactor small language service

### Week 4: System Integration
- [ ] Update factory pattern
- [ ] Update API routes
- [ ] Add comprehensive tests

### Week 5: Deployment
- [ ] Staging deployment
- [ ] Production deployment
- [ ] Monitoring and iteration

## Risk Mitigation

### Risk 1: Breaking Changes
**Mitigation:**
- Maintain backward compatibility wrappers
- Add deprecation warnings
- Gradual migration

### Risk 2: Performance Regression
**Mitigation:**
- Comprehensive performance testing
- Cache optimization
- Connection pooling

### Risk 3: Configuration Complexity
**Mitigation:**
- Clear configuration schema
- Validation on load
- Migration helpers

## Success Metrics

### Code Quality
- [ ] Average file size < 600 lines
- [ ] All files < 1000 lines
- [ ] 40% code reduction
- [ ] 100% test coverage

### Performance
- [ ] No regression (< 5%)
- [ ] Cache hit rate > 80%
- [ ] Router response < 100ms
- [ ] Discovery time < 5s

### Maintainability
- [ ] Clear separation of concerns
- [ ] Consistent naming
- [ ] Well-documented APIs
- [ ] Easy to test

## Resources

### Documentation
1. **Reorganization Plan** → `MEMORY_SERVICES_REORGANIZATION_PLAN.md`
2. **Implementation Guide** → `MEMORY_SERVICES_IMPLEMENTATION_GUIDE.md`
3. **Executive Summary** → `MEMORY_SERVICES_EXECUTIVE_SUMMARY.md`

### Key Files to Review
- `config.json` - Current configuration structure
- `src/ai_karen_engine/integrations/factory.py` - Service factory
- `src/ai_karen_engine/integrations/dependencies.py` - Dependency injection
- `src/ai_karen_engine/api_routes/` - API routes using services

### Code Review Focus
- Service boundaries
- Data structure consistency
- Error handling
- Performance impact
- Backward compatibility

## Questions?

### Architecture Questions
- How do services interact?
- What is the single source of truth for configuration?
- How are services initialized?

### Implementation Questions
- What are the dependencies between services?
- How do we handle configuration changes?
- What is the rollback strategy?

### Testing Questions
- What tests are required?
- How do we ensure backward compatibility?
- What is the test coverage target?

## Next Steps

1. **Review** the 3 planning documents
2. **Discuss** with team members
3. **Approve** the approach
4. **Begin** implementation following the guide
5. **Iterate** based on feedback

## Quick Commands

```bash
# Create new structure
mkdir -p src/services/memory/{core,routing,providers,small_language,system_models}

# Move internal files
mv src/services/memory/internal/*.py src/services/memory/internal/

# Create compatibility wrappers
cat > src/services/memory/__init__.py << 'EOF'
# Import new services
from .core.model_registry import UnifiedModelRegistry
from .core.model_downloader import UnifiedDownloadManager
from .routing.model_router import ModelRouter

# Create compatibility wrappers for backward compatibility
import warnings
warnings.warn(
    "This module is deprecated. Use the new consolidated services from core, routing, providers, etc.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = ['UnifiedModelRegistry', 'UnifiedDownloadManager', 'ModelRouter']
EOF

# Run tests
pytest tests/unit/test_model_registry.py
pytest tests/integration/test_routing.py
```

## Conclusion

This reorganization will create a more maintainable, testable, and production-ready memory services architecture. The key is to proceed incrementally, maintain backward compatibility, and thoroughly test at each step.

**Start with**: Unified model registry consolidation (highest impact, lowest risk)
**Complete by**: End of Month 6

--- 

*For detailed information, refer to the comprehensive planning documents in the project root.*
