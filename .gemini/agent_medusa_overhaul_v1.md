# AI-Karen Runtime Overhaul

## Full Developer Instruction

### Kiro-Style Execution Board

### AgentMedusa + LangGraph Cutover

---

## 1. Mission

This is a **clean overhaul of the runtime**, not a compatibility-preserving refactor.

We are replacing the legacy runtime centered around `ChatOrchestrator` with:

* `LangGraphOrchestrator` as the **sole production runtime authority**
* `AgentMedusa` as Karen’s **custom governed multi-agent execution runtime**
* existing canonical domains reused where they already exist:

  * `extensions/`
  * `auth/`
  * `memory/`
  * `database/`

We are removing:

* legacy orchestration
* duplicate provider/tool/memory/auth paths
* dead files
* unused folders
* stale adapters
* redundant extension runtime/platform duplication
* any file or layer that no longer adds real value

---

## 2. Current Status Snapshot

Use this as the authoritative starting context for the team.

### Phase 1: Research & Mapping

**Completed**

* audited `src/ai_karen_engine/core/`
* audited `src/ai_karen_engine/chat/`
* audited `src/ai_karen_engine/extensions/`
* mapped target structure to actual repo reality

### Phase 2: Foundation & AgentMedusa

**In Progress**

* create `src/ai_karen_engine/agent_medusa/`
* define `DeepExecutionPlan`
* define runtime contracts
* implement initial adapters for Extensions and Memory

### Phase 3: Extraction & Collapse

**Pending**

* extract reusable logic from `src/ai_karen_engine/chat/`
* collapse redundant extension platform/runtime modules
* standardize Auth/Memory domain consumption

### Phase 4: Cutover & Validation

**Pending**

* update `api_routes/chat_runtime.py` to LangGraph
* verify AgentMedusa specialist coordination
* delete legacy `ChatOrchestrator`

### Current task

Initialize `agent_medusa` directory and contracts.

### Resume rule

* if `agent_medusa/contracts/` exists, continue with coordinator + adapters
* if not, create contracts first

---

## 3. Canonical Architectural Decision

### Final runtime spine

```text
Ingress (HTTP / WS)
  -> LangGraphOrchestrator
  -> AgentMedusa Coordinator
  -> [Auth -> Safety -> Memory -> Planning -> Routing -> Execution -> Arbitration -> Synthesis -> Persistence]
  -> Response
```

### Runtime authority

`LangGraphOrchestrator` is the only production runtime authority.

### AgentMedusa identity

AgentMedusa is Karen’s custom LangGraph-based, governed, observable, multi-agent execution runtime.

### Explicit naming rule

Do **not** call this:

* DeepAgent
* DeepAgents
* LangChain DeepAgents

---

## 4. Non-Negotiables

### Do

* keep one runtime authority
* keep one provider/model routing authority
* keep one tool/plugin execution authority
* keep one persistence authority
* reuse canonical repo domains
* delete dead or redundant runtime structure
* ensure one correlation trace spans the whole request

### Avoid

* dual runtime authority
* route-level orchestration logic
* duplicated plugin subsystem
* duplicated memory subsystem
* duplicated auth subsystem
* compatibility wrappers without explicit removal plan
* preserving dead folders because they “might help later”

### Proof of completion

* runtime tree is smaller, clearer, and single-path
* every remaining runtime file has a clear owner
* no legacy orchestration remains in core production path

---

## 5. Repo-Aligned Domain Rules

This section matters. Do not invent a new architecture that ignores the repo.

---

## `core/`

### Keep

* `core/langgraph_orchestrator.py` as the primary brain
* `chat_runtime_control_plane.py` only if it still aligns cleanly with runtime gating

### Do

Promote `core/langgraph_orchestrator.py` into the canonical runtime engine.

### Avoid

Creating a second orchestration brain anywhere else.

---

## `agent_medusa/`

### New and required

This is the new Karen-native runtime layer.

### Owns

* coordinator
* specialists
* arbitration
* planning
* execution policy
* runtime contracts
* runtime adapters
* runtime telemetry schemas

### Do

Create only logic that is genuinely new and runtime-specific.

### Avoid

Copying domain logic from `auth/`, `memory/`, or `extensions/` into `agent_medusa/`.

---

## `extensions/`

### Canonical plugin/extension platform

The extension system already exists and is rich enough to be the real substrate for plugin execution.

### Do

Treat `extensions/` as the authoritative plugin/extension subsystem.

### Reuse

* `extensions/platform/core/host/*`
* `extensions/platform/core/integration/*`
* `extensions/platform/core/registry/*`
* active `extensions/runtime/*`
* `extensions/plugins/*`

### Avoid

Do **not** create a new `plugin_service`.

### Runtime integration rule

AgentMedusa must use a **thin adapter** into the extension system, not a parallel plugin subsystem.

---

## `auth/`

### Canonical auth domain

### Do

Use existing auth domain for:

* session validation
* cookie/token handling
* user context
* RBAC foundations

### Avoid

Do not create a duplicate `services/auth_service/` architecture.

---

## `memory/`

### Canonical memory domain

### Do

Use existing memory domain for:

* conversational memory
* vector memory
* structured memory
* profile and context building

### Avoid

Do not clone memory into AgentMedusa or create a parallel `memory_service` hierarchy.

---

## `database/`

### Canonical persistence domain

### Do

Use existing DB/persistence domain for:

* conversation history
* execution trace storage
* audit storage

### Avoid

Do not bury database concerns inside orchestration logic.

---

## `services/`

### Prune aggressively

### Do

Keep only true shared services that still earn their place, for example:

* `llm_router.py`
* canonical `tool_service.py`
* response policy/formatting services if still used

### Avoid

Do not let `services/` remain a junk drawer for duplicate domain logic.

---

## `chat/`

### Demolition zone

### Do

Extract reusable logic only if it still has value in the new runtime.

### Delete

* `chat/chat_orchestrator.py`
* `chat/ChatOrchestrator/*`
* mixin-based orchestration
* any old bridge logic once parity exists

### Avoid

Do not preserve `chat/` as a hidden second runtime.

---

## 6. Existing LangGraph-Related Areas That Must Be Audited

The team must not assume LangGraph only exists in one file.

Already identified LangGraph-related or LangGraph-adjacent areas include:

* `core/langgraph_orchestrator.py` 
* `session_state/langgraph_integration.py` 
* `agents/adapters/langgraph_adapter.py` 
* broader `agents/` subsystem with integration and lifecycle files 
* `copilotkit/` thread/session/agent UI surfaces and implementation summary    
* legacy chat bridge `chat/ChatOrchestrator/mixins/agent_mixin.py` 

### Do

Audit these before rebuilding equivalent logic.

### Reuse

Promote the strongest existing LangGraph-native logic into AgentMedusa where it still fits.

### Avoid

Do not re-implement capabilities that already exist in:

* `agents/`
* `session_state/`
* `copilotkit/`
* `core/`

without first deciding whether they should be merged, moved, or deleted.

---

## 7. Folder/Module Classification Rule

Every runtime-adjacent file or folder must be marked as one of:

* **KEEP**
* **MOVE**
* **COLLAPSE**
* **TEMP BRIDGE**
* **DELETE**

No file stays in “maybe.”

Every PR must include for touched modules:

### Do

What this becomes in the new runtime.

### Reuse

What logic is worth preserving.

### Avoid

What legacy responsibility must not survive.

### Proof

How the team knows it can stay, move, collapse, or die.

---

## 8. Target Folder Tree

This is the target shape the team should move toward.

```text
src/ai_karen_engine/
├── core/                                      [KEEP / COLLAPSE]
│   ├── langgraph_orchestrator.py              [KEEP]
│   ├── chat_runtime_control_plane.py          [KEEP if aligned]
│   └── ...
│
├── agent_medusa/                              [NEW / KEEP]
│   ├── __init__.py
│   ├── contracts/
│   │   ├── runtime_request.py
│   │   ├── runtime_response.py
│   │   ├── deep_execution_plan.py
│   │   ├── execution_action.py
│   │   ├── subagent_contract.py
│   │   ├── arbitration_contract.py
│   │   └── policy_contract.py
│   ├── coordinator/
│   ├── specialists/
│   ├── arbitration/
│   ├── planning/
│   ├── execution/
│   ├── policy/
│   ├── telemetry/
│   └── adapters/
│       ├── extension_runtime_adapter.py
│       ├── memory_runtime_adapter.py
│       ├── auth_context_adapter.py
│       └── persistence_adapter.py
│
├── api_routes/                                [KEEP / COLLAPSE]
│   ├── chat_runtime.py
│   ├── websocket_routes.py
│   └── auth_routes.py
│
├── extensions/                                [KEEP / COLLAPSE]
│   ├── platform/
│   ├── runtime/
│   ├── plugins/
│   └── system_extensions/
│
├── auth/                                      [KEEP / COLLAPSE]
├── memory/                                    [KEEP / COLLAPSE]
├── services/                                  [COLLAPSE / KEEP selective]
├── database/                                  [KEEP]
├── session_state/                             [AUDIT / MERGE]
├── agents/                                    [AUDIT / MERGE / DELETE selectively]
├── copilotkit/                                [AUDIT / MERGE / DELETE selectively]
└── chat/                                      [DELETE / EXTRACT / COLLAPSE]
```

---

## 9. Mandatory Missing Artifacts To Implement

The following deliverables must exist:

1. `DeepExecutionPlan`
2. runtime-scoped permission + sandbox policy contract
3. runtime request contract
4. runtime response contract
5. execution action schema
6. specialist registry
7. subagent dispatch contract
8. arbitration contract and scorer
9. node telemetry schema
10. persistence mapping for:

* conversation history
* execution trace
* audit log

---

## 10. AgentMedusa Node Plan

Each node is a governed execution checkpoint.

### Node 1. Auth + RBAC Gate

* validate user/session/tenant
* inject runtime-scoped permissions
* compute allowed tools/plugins/filesystem scope

### Node 2. Safety / Policy Gate

* content safety
* action safety
* plugin/tool policy risk
* escalate to approval when required

### Node 3. Memory Layer

* short-term/session memory
* long-term vector memory
* structured DB memory
* filesystem artifact context
* audit references

### Node 4. Planning

Generate `DeepExecutionPlan`:

* steps
* tools
* plugins
* permissions
* risk
* approval requirement
* specialist assignments
* parallelization

### Node 5. Routing

Choose:

* provider/model
* specialist agents
* direct vs multi-step
* sequential vs parallel
* degraded mode strategy

### Node 6. Execution Engine

Support:

* bounded tool loops
* retries
* timeouts
* extension execution
* code execution
* filesystem actions
* sandbox requirements

### Node 7. Subagent Dispatcher

* spawn subagents
* apply scoped context
* enforce budgets
* collect traces

### Node 8. Arbitration

* compare outputs
* detect contradictions
* rerank by confidence, policy, cost, consistency
* rerun or escalate

### Node 9. Response Synthesis

* consume winning output
* merge tool results and memory context
* enforce response policy

### Node 10. Observability + Audit

* node latency
* decisions
* provider/model
* tools/plugins used
* fallback path
* correlation IDs
* parent-child agent linkage

### Node 11. Persistence

Persist:

* user input
* plan
* assignments
* actions
* selected output
* final response
* audit trail

---

## 11. File-by-File Execution Board

## `api_routes/chat_runtime.py`

### Do

* cut over to LangGraph runtime
* normalize requests into runtime contract
* preserve client-facing metadata shape

### Reuse

* validation
* control-plane gate
* correlation/session/request IDs

### Avoid

* route-side provider logic
* route-side fallback logic
* route-side orchestration

### Proof

* no primary import/use of ChatOrchestrator remains

---

## `chat/factory.py`

### Do

* rewrite factory to compose LangGraph runtime
* inject shared canonical services
* stop composing ChatOrchestrator as live runtime

### Avoid

* rebuilding ChatOrchestrator semantics in a wrapper

### Proof

* factory’s production orchestrator is LangGraph-based

---

## `core/langgraph_orchestrator.py`

### Do

* promote to canonical engine
* implement AgentMedusa coordinator responsibilities
* support deeper planning, execution policy, subagents, arbitration, persistence

### Reuse

* existing graph nodes
* runtime status
* dry-run analysis where useful

### Avoid

* permissive auth fallback unless explicitly allowed

### Proof

* powers live chat and agent execution end-to-end

---

## `chat/ChatOrchestrator/mixins/agent_mixin.py`

### Do

* extract useful semantics only
* remove production authority
* delete once parity is achieved

### Avoid

* continuing bridge logic

### Proof

* no production path depends on it

---

## `extensions/`

### Do

* keep as canonical plugin/extension system
* collapse duplicate platform/runtime layers
* expose a thin AgentMedusa adapter

### Avoid

* creating `plugin_service`

### Proof

* one extension execution substrate remains

---

## `auth/`

### Do

* centralize session and user resolution
* remove request-time auth service initialization from hot paths
* standardize token/cookie contract

### Proof

* one canonical authenticated user context enters runtime

---

## `memory/`

### Do

* use canonical memory domain
* define runtime read/write policy by agent/result type

### Avoid

* duplicate memory orchestration in chat layer or AgentMedusa

### Proof

* one memory system of record remains

---

## `agents/`

### Do

* audit for existing LangGraph-related reusable logic
* keep/merge only what aligns with AgentMedusa
* delete stale or overlapping agent systems

### Proof

* no parallel agent runtime remains

---

## `session_state/`

### Do

* audit LangGraph-related session integration
* merge session continuity into final runtime plan where useful

### Proof

* session continuity is not duplicated elsewhere

---

## `copilotkit/`

### Do

* audit for thread/session/agent UI logic that still adds value
* merge or delete based on whether it fits the new runtime and active UI surfaces

### Proof

* CopilotKit does not contain hidden competing runtime behavior

---

## `chat/`

### Do

* extract only genuinely reusable shared components
* delete orchestration authority and dead support logic

### Proof

* no legacy runtime remains in `chat/`

---

## 12. Cleanup Rule

This is a clean overhaul.

### Keep a file only if it:

1. is required by AgentMedusa + LangGraph runtime
2. provides reusable logic that cleanly fits a canonical domain
3. is required for an active non-runtime surface that still exists
4. is a temporary bridge with an explicit removal milestone

Otherwise:
**Delete it.**

---

## 13. Production Cleanup Order

1. create `agent_medusa/contracts/`
2. define runtime request/response + `DeepExecutionPlan`
3. implement extension/memory/auth/persistence adapters
4. rewrite factory to compose LangGraph runtime
5. cut over HTTP route
6. cut over stream semantics
7. merge agent execution into LangGraph runtime
8. finish persistence parity
9. finish degraded/fallback parity
10. cut over websocket path
11. delete ChatOrchestrator and legacy mixins
12. collapse duplicate extension/runtime/auth/memory logic
13. delete dead folders and unused files

---

## 14. Acceptance Criteria

Do not call this overhaul complete unless all are true:

* LangGraph is the sole runtime authority
* AgentMedusa coordinator/specialist/arbitration model is implemented
* no production route depends on ChatOrchestrator
* no duplicate provider selection remains
* no duplicate tool/plugin execution path remains
* no duplicate memory/persistence path remains
* no duplicate auth/session shaping remains
* extension system is canonical and not duplicated
* runtime folder tree reflects the new architecture
* dead files and unused folders tied to the old runtime are removed

---

## 15. Bottom Line

This is a **runtime replacement and structural cleanup**.

The team is not allowed to merely make the new runtime work alongside the old one.

The team must leave the repo:

* smaller
* clearer
* single-path
* easier to reason about
* free of dead runtime structure
