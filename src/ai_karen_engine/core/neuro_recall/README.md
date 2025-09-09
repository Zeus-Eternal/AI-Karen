# AI-Karen Neuro-Recall Integration

This module contains the integrated neuro-recall components that have been refactored and incorporated into AI-Karen's core architecture. The original neuro-recall system has been transformed into AI-Karen's case-memory learning system and modular tools architecture.

## Integration Status

### ✅ Completed Integrations

**Case-Memory Learning System** (`src/ai_karen_engine/learning/case_memory/`)
- Core case-memory learning module with types, admission policy, and storage
- Dual-stage retrieval system (vector search + cross-encoder reranking)
- Planner hooks for pre-plan context injection and case admission
- Comprehensive observability and metrics system

**Tools System** (`src/ai_karen_engine/tools/`)
- **Interpreters**: Python, Docker, Subprocess, IPython interpreters with security controls
- **Search Tools**: Privacy-respecting web search via SearxNG integration
- **Document Tools**: Multi-format document processing (PDF, DOCX, HTML, etc.)
- **Server Tools**: Dedicated tools for prompt-first architecture

**Recalls System** (`src/ai_karen_engine/core/recalls/`)
- Memory management with semantic search capabilities
- JSONL storage with embedding-based retrieval
- Async operations with configurable models

**Agent Client System** (`src/ai_karen_engine/core/agent_client/`)
- Multi-agent coordination with tool management
- Case-based reasoning agent with memory integration

**Unified Plugin System** (`/plugins/`)
- Consolidated plugin architecture
- SearxNG plugin with Docker management
- Search plugin integration

### 🔄 Architectural Changes

**Database Integration**
- Postgres migration for case_memory_cases table
- Milvus migrations for vector storage
- Redis integration for caching

**System Integration**
- Patched AgentPlanner with case-memory hints
- Patched ExecutionPipeline with case admission
- Metrics and observability hooks throughout

### 📁 Remaining Components

**Legacy Data** (`data/`, `memory/`)
- Historical case data (deepresearcher.jsonl, dummy_memo.jsonl)
- Memory processing utilities (np_memory.py)

**Client Components** (`client/`)
- Original agent implementations
- CBR algorithms and local server components

**Research Assets** (`Figure/`)
- Research figures and documentation

## Usage in AI-Karen

The neuro-recall capabilities are now deeply integrated into AI-Karen:

```python
# Case-memory learning is automatically enabled in planner/executor
from ai_karen_engine.learning.case_memory import get_observer
from ai_karen_engine.core.recalls import RecallManager
from ai_karen_engine.tools.interpreters import PythonInterpreter

# Observability
observer = get_observer()
metrics = observer.get_metrics_snapshot()

# Recalls system
recall_manager = RecallManager()
await recall_manager.initialize()

# Tools and interpreters
interpreter = PythonInterpreter()
result = await interpreter.run("print('Hello')", "python")
```

## Configuration

Configure via AI-Karen's main configuration system:

```yaml
# config/memory.yml
case_memory:
  enabled: true
  admission_threshold: 0.3
  retrieval_top_k: 5

# config/tools.yml
interpreters:
  python:
    enabled: true
    security_level: high
```

This integration maintains the core neuro-recall capabilities while adapting them to AI-Karen's architecture, security model, and operational requirements.
