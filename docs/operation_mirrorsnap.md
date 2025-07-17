## Operation MirrorSnap: Technical Specification

### 1. Executive Summary

**Objective:** Elevate Kari AI’s memory subsystem by integrating advanced dual-embedding recall, tool-memory linkage, schema-aware document storage, Prometheus observability, tunable LLM profiles, and MCP interoperability. Deliver a robust, self-optimizing, vendor-agnostic memory platform for enterprise stakeholders.

### 2. Architecture Overview

```
                  +---------------------+
                  |     User Session    |
                  +----------+----------+
                             |
                             v
                       [CORTEX Context]
                             |
             +---------------+----------------+
             |                                |
       [PluginManager]                  [MCP Layer]
 Plugin hooks & RBAC/audit                |
   tool-memory linkage         <---->   External/Internal MCP Services
             |                                |
             +---------------+----------------+
                             |
                    [Memory Orchestrator]
                             |
       +------+------+------+------+-------+
       |             |            |         |
[NeuroVault] [Document Layer] [Profiles] [Prometheus]
  Dual-embed    Schema-chunk     LLM      Metrics & Alerts
```

### 3. Component Breakdown

#### 3.1 NeuroVault Memory

* **Fast ANN Engine:** Use FAISS/Milvus for approximate nearest-neighbor search on MPNet embeddings.
* **Reranker Module:** Custom BERT-based re-scorer incorporating sentiment, intent, and session context.
* **Data Flow:** Index incoming embeddings → run ANN search → rerank top-K → return top results.
* **Prometheus Metrics:** `memory_recall_latency`, `rerank_time`, `recall_hit_rate`.

#### 3.2 PluginManager & Tool-Memory Linkage

* **Execution Hooks:** Wrap each plugin call to log inputs, outputs, success state.
* **Embedding Vectorization:** After tool result, generate an embedding of `(tool_name + result_summary + user_context)`.
* **Memory Write:** Persist vector + metadata (timestamp, plugin_id, session_id) to NeuroVault.
* **Prometheus Metrics:** `plugin_calls_total`, `plugin_failure_rate`, `memory_writes_total`.

#### 3.3 Schema-Aware Document Layer

* **Preprocessor:** PDF/Doc ingest → chunk by headings/semantic boundaries via NLP (spaCy).
* **Metadata Tags:** Title, author, timestamp, keywords, document type.
* **Storage:** Each chunk + metadata + embedding stored in Milvus + Postgres (metadata table).
* **Query:** Hybrid search: SQL filter on metadata → vector recall on embeddings.
* **Metrics:** `doc_chunks_indexed`, `doc_search_latency`, `metadata_hit_rate`.

#### 3.4 Prometheus Observability

* **Endpoints:** Expose `/metrics` for all subsystems.
* **Dashboards:** Grafana panels for memory latency, recall quality, plugin health, decay rates.
* **Alerts:** Threshold-based alerts (e.g., recall latency > 200ms, failure_rate > 5%).

#### 3.5 Tunable LLM Profiles

* **Profile Definitions:** YAML config with profiles: `fast_local`, `precise_factual`, `dark_empath`, etc.
* **Router Logic:** Inspect `task_intent + profile` → select model endpoint (Ollama, Gemini, EchoCore).
* **Fallback Stack:** If primary unavailable, automatically degrade to next model in chain.
* **Metrics:** `model_invocations_total`, `fallback_rate`, `avg_response_time`.

#### 3.6 MCP Integration

* **Client Implementation:** gRPC/JSON-RPC client to discover and invoke external MCP servers.
* **Server Implementation:** Wrap internal Kari plugins (memory, tools) as MCP services.
* **Registry:** Dynamic service registry stored in Redis, discoverable per session.
* **Security:** Token-based auth, per-scope consent prompts, RBAC enforced on each call.
* **Metrics:** `mcp_calls_total`, `mcp_auth_failures`, `mcp_latency`.

### 4. Implementation Plan & Timeline

| Phase | Duration | Deliverables                                           |
| ----- | -------- | ------------------------------------------------------ |
| 1     | 3 weeks  | NeuroVault dual-embedding search + Prometheus metrics  |
| 2     | 2 weeks  | PluginManager hooks + tool-memory linkage              |
| 3     | 3 weeks  | Document layer ingest, metadata tagging, hybrid search |
| 4     | 2 weeks  | Prometheus dashboards & alert configurations           |
| 5     | 2 weeks  | LLM profile router + fallback logic                    |
| 6     | 4 weeks  | MCP client/server + registry + security enforcement    |

### 5. Improvement & Risk Analysis

* **Potential Bottleneck:** Reranker latency—mitigate via model distillation or GPU acceleration.
* **Storage Costs:** Milvus index size—implement chunk expiration policies and TTL.
* **Security Risks:** MCP external calls—enforce strict RBAC and input validation.
* **Scalability:** Shard vector index across nodes; use autoscaling for microservices.

### 6. Stakeholder Benefits

* **Control & Sovereignty:** Self-hosted, no vendor lock-in.
* **Performance:** <50ms average recall; <150ms rerank.
* **Audit & Compliance:** Full traceability of memory and tool use.
* **Extensibility:** Hot-swappable modules and protocols.

---

**Next Steps:** Review architecture with DevOps, finalize resource allocation (GPU vs CPU), and begin Phase 1-6 sprint planning.

