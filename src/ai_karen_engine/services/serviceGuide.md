# 🧠 Services Architecture & DRY Guide

**Scope:**
This document defines how to **design, name, organize, and wire services** inside the `services/` package so the system stays **DRY, predictable, and production-ready** as it grows.

It’s the **single source of truth** for:

* How to add new services
* How to refactor existing ones
* How other layers (API, UI, workers) are allowed to talk to `services/`

---

## 1. Core Principles

All service work in this repo must follow these principles:

1. **Facade-first design**

   * Each major concern (memory, models, plugins, auditing, etc.) exposes **one primary facade module**.
   * All external callers (API routes, workers, UI adapters) must talk to the **facade**, not internal helpers.

2. **No synonyms / duplicates**

   * If two modules sound like they do the same thing (`integrated_memory_service.py`, `enhanced_memory_service.py`, `optimized_memory_service.py`), there should be **one canonical service** and the rest are either:

     * merged into it as internal strategies, or
     * removed.

3. **Dependency rules**

   * No direct calls to raw infrastructure (DB, Redis, LLM clients) outside of:

     * `database_connection_manager`,
     * `redis_connection_manager`,
     * `model_connection_manager`.
   * No module should route models or memory on its own; model routing goes through model facades, memory operations go through memory facades.

4. **DRY error handling & monitoring**

   * Retry, fallback, graceful degradation, and metrics are centralized in dedicated services.
   * No “homegrown retries” or logging scattered across random services.

5. **Stable public surface**

   * The set of modules that other packages are allowed to import from `services/` is **small, explicit, and versionable**.
   * Everything else is internal and can be refactored freely.

---

## 2. Folder & Layer Overview

`services/` is a **logic & orchestration layer**, not a dumping ground.

High-level areas:

* `services/ai_orchestrator/` – orchestration, flow, decision logic
* `services/cognitive/` – working & episodic memory primitives
* `services/knowledge/` – connectors, indexing, retrieval
* `services/tools/` – tools registry and execution contracts
* Top-level `services/*.py` – facades and shared systems

Each concern generally has:

1. **Facade module** → public entry point
2. **Internal strategies/helpers** → implementation detail
3. **Tests in `services/__tests__/`** → one test file per facade

---

## 3. Public vs Internal Modules

### 3.1 What counts as a “public” service?

A **public service** is a module that:

* Is **imported from outside** the `services` package (e.g., by API, UI, background workers).
* Exposes **high-level methods** for a domain: e.g., “run conversation”, “store memory”, “execute plugin”.
* Encapsulates infra, routing, retries, and metrics within it.

Examples of intended **public facades** (non-exhaustive but canonical):

**Infra & configuration**

* `services.settings_manager`
* `services.secret_manager`
* `services.dependencies`

**Models & providers**

* `services.provider_registry`
* `services.model_registry`
* `services.model_orchestrator_service`
* `services.intelligent_model_router`
* `services.system_model_manager`
* `services.model_library_service`

**Memory & knowledge**

* `services.unified_memory_service`
* `services.neurovault_integration_service`
* `services.knowledge.index_hub`
* `services.knowledge.query_fusion_retriever`

**Orchestration & conversation**

* `services.ai_orchestrator.ai_orchestrator`
* `services.ai_orchestrator.flow_manager`
* `services.ai_orchestrator.prompt_manager`
* `services.ai_orchestrator.context_manager`
* `services.conversation_service`
* `services.conversation_tracker`
* `services.web_ui_api`

**Tools & plugins**

* `services.tools.registry`
* `services.tools.core_tools`
* `services.tools.copilot_tools`
* `services.tool_service`
* `services.plugin_registry`
* `services.plugin_service`

**Security & auth**

* `services.auth_service`
* `services.auth_utils`
* `services.tenant_isolation`
* `services.privacy_compliance`

**Observability & usage**

* `services.structured_logging_service`
* `services.metrics_service`
* `services.production_monitoring_service`
* `services.usage_service`
* `services.user_satisfaction_tracker`

**Audit & compliance**

* `services.audit_logger`
* `services.training_audit_logger`
* `services.auth_data_cleanup_service`

> **Rule:**
> Only these “public surface” modules should be imported by other packages. If you need something not listed here, either:
>
> * extend an existing facade, or
> * propose a new facade and update this guide.

---

### 3.2 What is “internal” and how to treat it?

**Internal services** are implementation details. Examples:

* `services.integrated_memory_service`
* `services.optimized_memory_service`
* `services.enhanced_memory_service`
* `services.llm_optimization`
* `services.vector_optimization`
* `services.error_aggregation_service`
* `services.streaming_interruption_handler`
* `services.audit_cleanup`
* `services.audit_deduplication`

Rules for internal modules:

* They are imported **only** by facades or other internal services within the same concern.
* They can be refactored or renamed without breaking external code.
* They must not be used directly by API layers, UI code, or external packages.

---

## 4. Service Design Patterns per Domain

### 4.1 Memory & Cognitive Services

**Goal:** One memory facade, multiple strategies.

* **Facade:** `unified_memory_service`

  * Handles all read/write/query operations for memory.
  * Wraps:

    * working memory (`cognitive/working_memory`)
    * episodic memory (`cognitive/episodic_memory`)
    * external stores (Redis, Milvus, etc.)
    * policy (`memory_policy`)
    * writeback (`memory_writeback`)

* **Internal / strategy modules:**

  * `integrated_memory_service`
  * `optimized_memory_service`
  * `enhanced_memory_service`
  * `memory_service`
  * `memory_service_tenant_wrapper`
  * `memory_exhaustion_handler`
  * `memory_transformation_utils`
  * `memory_compatibility`

**Future rule:**

> Any new memory feature (e.g., compression, sharding, tiering, vector reranking) must be implemented as:
>
> * a strategy/helper in `unified_memory_service`, **or**
> * a clearly named helper module used only by `unified_memory_service`.

No other module should write directly to memory backends.

---

### 4.2 Models, Providers & Routing

**Goal:** All model interactions via a single orchestrated path.

* **Facade hierarchy:**

  * `model_orchestrator_service`
    → primary interface for “run this task on a model”
  * `intelligent_model_router`
    → decides which model/provider to use
  * `llm_router`
    → low-level execution router (used by orchestrator & router)
  * `provider_registry`, `model_registry`
    → metadata and registrations
  * `system_model_manager`
    → default & system-level model policies

* **Internal helpers:**

  * `model_discovery_engine`, `model_discovery_service`
  * `model_library_cache_service`
  * `model_metadata_service`
  * `llm_optimization`, `cuda_acceleration_engine`
  * model-specific adapters: `tinyllama_service`, `small_language_model_service`, `distilbert_service`, `spacy_service`, `enhanced_huggingface_service`

**Future rule:**

> No service outside this group should instantiate or call model clients directly.
> All model calls flow:
> `caller` → `model_orchestrator_service` → `intelligent_model_router` → `llm_router`.

---

### 4.3 Infrastructure (DB, Cache, Connections)

**Goal:** One set of connection managers, no raw client chaos.

* **Facades:**

  * `database_connection_manager`
  * `redis_connection_manager`
  * `model_connection_manager`
  * `integrated_cache_system`
  * `smart_cache_manager`
  * `database_query_cache_service`
  * `database_optimization_service`
  * `database_health_monitor`
  * `database_consistency_validator`
  * `connection_health_manager`

**Internal / merge candidates:**

* `database_health_checker` → logic belongs inside `database_health_monitor`.

**Future rule:**

> Any new DB/cache feature (e.g., a query cache, read replica routing, eviction policy) must sit behind these facades. No raw client access in feature services.

---

### 4.4 Observability, Metrics & Performance

**Goal:** Centralized logging, metrics, and monitoring.

* **Facades:**

  * `structured_logging_service`
  * `metrics_service`
  * `response_performance_metrics`
  * `integrated_performance_monitoring`
  * `slo_monitoring`
  * `production_monitoring_service`
  * `performance_benchmarking`
  * `performance_monitor`
  * `usage_service`
  * `user_satisfaction_tracker`
  * `correlation_service`

* **Internal helpers:**

  * `structured_logging` (helper only, not imported directly)

**Future rule:**

> Any new timing, metrics, or trace logic must either:
>
> * reuse `response_performance_metrics`, or
> * extend `metrics_service` / `integrated_performance_monitoring`.

No hand-rolled logging or timers in random services.

---

### 4.5 Audit, Privacy & Compliance

**Goal:** One audit logger, specialized helpers.

* **Facades:**

  * `audit_logger`
  * `training_audit_logger` (wraps `audit_logger` for ML)
  * `privacy_compliance`
  * `auth_data_cleanup_service`

* **Internal helpers:**

  * `audit_logging`
  * `audit`
  * `audit_cleanup`
  * `audit_deduplication`

**Future rule:**

> Any audit-related event must go through `audit_logger` (or `training_audit_logger` for ML).
> Cleanup/deduplication jobs are triggered via `job_manager` calling these helpers, not by arbitrary services.

---

### 4.6 Orchestration, Conversation, Tools & Plugins

**Goal:** Centralized orchestration path for conversation, tools, and plugins.

#### Orchestration

* **Facades:**

  * `ai_orchestrator.ai_orchestrator`
  * `ai_orchestrator.flow_manager`
  * `ai_orchestrator.decision_engine`
  * `ai_orchestrator.prompt_manager`
  * `ai_orchestrator.context_manager`
  * `intelligent_response_controller`
  * `progressive_response_streamer`
  * `orchestration_agent`

> All “end-to-end reasoning” flows **must** go through the orchestrator or flow manager.

#### Conversation & UI

* **Facades:**

  * `conversation_service`
  * `conversation_tracker`
  * `web_ui_api`
  * `ag_ui_memory_interface`
  * `user_service`
  * `auth_service`
  * `auth_utils`
  * `usage_service`
  * `webhook_service`

> External HTTP APIs talk:
> API route → `web_ui_api` → `conversation_service` → `ai_orchestrator`.

#### Tools & Plugins

* **Facades:**

  * `tools.registry`
  * `tools.core_tools`
  * `tools.copilot_tools`
  * `tools.contracts`
  * `tool_service`
  * `plugin_registry`
  * `plugin_service`
  * `plugin_execution`
  * `copilot_capabilities`
  * `copilot_extension_integration`
  * `resource_allocation_system`

> Tool execution:
> `ai_orchestrator` / `flow_manager` → `tool_service` → `tools.registry` → actual tool.

> Plugin lifecycle:
> Plugin discovery/management lives in `plugin_registry` + `plugin_service`, which **register tools into `tools.registry`**, not parallel registries.

---

### 4.7 Optimization, Priority & Resilience

**Goal:** One unified resilience/optimization control plane.

* **Facades:**

  * `optimization_configuration_manager`
  * `optimization_integration_orchestrator`
  * `priority_processing_system`
  * `resource_allocation_system`
  * `graceful_degradation_coordinator`
  * `fallback_provider`
  * `error_recovery_system`
  * `error_response_service`
  * `timeout_performance_handler`

* **Internal helpers:**

  * `optimization_recommendation_engine`
  * `vector_optimization`
  * `e2e_optimization`
  * `error_aggregation_service`
  * `streaming_interruption_handler`

**Future rule:**

> Any new retry/fallback/degradation logic must be implemented via `error_recovery_system`, `graceful_degradation_coordinator`, or `fallback_provider`.
> No ad-hoc retries in feature services.

---

## 5. Adding a New Service – Checklist

When you add a new service, follow this checklist:

1. **Define the domain & question:**

   * What is this service’s domain? (memory, models, observability, plugins, etc.)
   * Does this domain already have a facade?

2. **Check for existing equivalents:**

   * Search for modules that sound similar.
   * If there is overlap, extend/merge instead of creating a new “sibling” file.

3. **Choose the right location:**

   * If it’s a primary entry point → becomes/extends a **facade**.
   * If it’s an implementation detail → lives as an **internal helper** under the existing facade’s concern.

4. **Define a minimal, stable API:**

   * Small surface: clearly named methods, typed arguments and returns.
   * No leaking infra types (raw DB cursors, bare Redis connections, raw model clients).

5. **Wire dependencies properly:**

   * For DB: use `database_connection_manager`.
   * For cache: use `integrated_cache_system` or `smart_cache_manager`.
   * For LLMs: use `model_orchestrator_service` / routers.
   * For memory: use `unified_memory_service`.
   * For metrics/logging: use `structured_logging_service` and `metrics_service`.

6. **Integrate observability & errors:**

   * Emit metrics via `metrics_service`.
   * Log via `structured_logging_service`.
   * Use `error_recovery_system` / `fallback_provider` for resilience when applicable.

7. **Write tests in `services/__tests__/`:**

   * `test_<service_name>.py` mirroring the facade’s filename.
   * Cover success, error, and degraded conditions when applicable.

8. **Update this guide if:**

   * You introduce a new **facade**.
   * You deprecate or merge a facade.

---

## 6. Refactoring & Deprecation Rules

When cleaning up or consolidating services:

1. **Prefer merging over renaming-only**

   * If two services overlap, merge their internals into a single facade and remove the duplicate.

2. **Deprecate carefully**

   * If you must keep a module for compatibility:

     * Mark it clearly as **deprecated** at top-of-file.
     * Make it a thin wrapper around the new facade.
     * Add a task in the production audit to remove it in the next major iteration.

3. **Update imports**

   * Replace imports in other packages to use the **new facade**.
   * Only after that should you remove old modules.

4. **Keep tests green**

   * Update or consolidate test files to align with new facades.
   * No orphan tests for removed services.

---

## 7. Quick Reference: “Can I Create This File?”

Before adding a new service file under `services/`, ask:

1. **Is there already a related facade?**

   * Yes → extend that system as an internal helper.
   * No → you might be defining a new domain; propose it as a facade and add it to this guide.

2. **Is this name a synonym?**

   * If the name could be confused with existing modules, don’t add it.
   * Find the canonical wording and extend that instead.

3. **Can this be a strategy object instead of a top-level service?**

   * Prefer strategies/classes inside existing facades over new top-level modules whenever possible.

---

This gives your future devs a **clear contract**:

* What to import
* Where to put new logic
* How to avoid re-creating the redundancy you just cleaned up
