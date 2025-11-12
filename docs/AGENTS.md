# Kari AI Agent Playbook

This guide orients human contributors and automated agents that generate patches for the Kari AI platform. Use it as your first stop before touching code—everything here reflects the current production architecture and workflow expectations.

---

## 1. Mission & Scope

- **Primary objective:** maintain a modular, production-grade AI platform that powers FastAPI services, multi-LLM orchestration, and rich desktop/launcher experiences.
- **Key pillars:** deterministic routing (KIRE/KRO), NeuroVault-style memory services, in-process llama.cpp inference, security-first authentication, and observability baked into every layer.
- **Expectations for every change:** keep runtime modules composable, keep UI launchers decoupled, and protect the contract-level APIs consumed by automation and external integrators.

---

## 2. Repository Layout (2025)

### Backend: `src/ai_karen_engine/`
The backend is a single Python package with absolute imports only (`from ai_karen_engine.<module>`). Major areas include:

| Path | Purpose |
| ---- | ------- |
| `core/` | Request lifecycle, orchestration primitives, and platform bootstrap. |
| `routing/` & `llm_orchestrator.py` | KIRE router, KRO orchestrator, policy enforcement, and provider coordination. |
| `agents/`, `automation_manager/`, `capsules/` | Declarative workflows, task agents, and capsule execution runtime. |
| `echocore/`, `doc_store/`, `learning/` | Persona/memory services, retrieval stores, and adaptive learning loops. |
| `inference/`, `integrations/`, `clients/` | llama.cpp runtime, external LLM/API adapters, and transport clients. |
| `plugins/`, `community_plugins/`, `plugin_manager.py`, `plugin_router.py`, `plugin_orchestrator.py` | First-party plugins, registry definitions, and dynamic loading. |
| `services/`, `api_routes/`, `server/`, `middleware/` | FastAPI routers, background workers, middleware, and startup surfaces. |
| `database/`, `auth/`, `health/`, `monitoring/`, `audit/` | Persistence, authentication, health probes, telemetry, and compliance logging. |
| `event_bus/`, `hooks/`, `extensions/`, `tools/`, `utils/` | Cross-cutting events, extension hooks, CLI/tooling, and helper utilities. |
| `logging/`, `guardrails/`, `error_tracking/`, `compatibility.py` | Reliability, safety, compatibility shims, and error handling. |
| `chat/`, `copilotkit/`, `mcp/` | Conversational surfaces, Copilot integrations, and Model Context Protocol support. |
| `tests/` | Contract/regression tests covering routing, memory, and plugin behaviors. |

### Shared Packages under `src/`
- `auth/`, `extensions/`, `plugins/`, and `theme/` expose reusable packages for launchers and external tools.
- `config/` and `dotenv.py` centralize configuration loading.
- `cachetools/` and `test/` provide supporting utilities and stubs for deterministic testing.

### UI Launchers: `ui_launchers/`
- `desktop_ui/` (Tauri) remains the primary packaged interface.
- `backend/` exposes lightweight developer tooling APIs for launcher builds.
- `common/` and `KAREN-Theme-Default/` hold shared UI assets.
- The legacy web launcher has been retired; any new UI must live in a dedicated subdirectory here.

### Tooling & Operations
- `docker/`, `docker-compose.yml`, and scripts like `start.py`/`start_backend_with_cors.sh` define runtime flows.
- `monitoring/` and top-level `reports/*.md` document production readiness, audits, and incident learnings.
- `models/llama-cpp/` is the canonical location for bundled GGUF models.

---

## 3. Coding Doctrine

1. **Absolute imports only.** Never modify `sys.path`—every module under `src` must be importable via the package root.
2. **Modularity over monolith.** Design new subsystems so they can be extracted into independent packages without refactoring callers.
3. **UI/backend isolation.** Backend logic stays inside `src/ai_karen_engine/` (or sibling packages); UI launchers interact through public APIs.
4. **Config discipline.** Runtime toggles live in config modules or `.env` files—never hardcode environment-specific values.
5. **Pydantic & typing.** Leverage Pydantic models for IO contracts and keep strict typing to protect agent-generated patches.
6. **Documentation-first.** Significant architectural changes require updating the relevant report/README so downstream agents inherit context.
7. **Respect dual licensing.** All code must comply with the MPL 2.0 + commercial licensing terms that govern Kari AI.

---

## 4. Working Agreement for Agents

- **Before implementing:** inspect existing modules, reuse service abstractions, and prefer extending registries over introducing new global state.
- **When adding integrations or plugins:** include an `__init__.py`, follow the plugin manager contracts, and document activation steps.
- **When touching KIRE/KRO or memory systems:** update related simulation tests under `src/ai_karen_engine/tests/` and maintain fallbacks.
- **Testing expectation:** run targeted pytest modules or FastAPI integration checks when feasible; document skipped tests if infrastructure is unavailable.
- **Pull requests:** summarize subsystem changes (routing, memory, auth, etc.) and mention any migration or config follow-up required by operators.

---

## 5. Quick Orientation Checklist

1. Read `README.md` for release highlights and operational modes.
2. Review `src/ai_karen_engine/core/`, `routing/`, and `services/` to understand execution flow.
3. Check `monitoring/` and `reports/` for the latest audit findings and production constraints.
4. Verify local model paths and `.env` overrides before running `start.py` or Docker workflows.
5. Keep this playbook handy—update it whenever scope or architecture changes.

Welcome to the Hydra—keep the heads modular and the mission sharp.
