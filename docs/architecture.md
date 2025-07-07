# Kari Architecture

Kari is a local-first conversational platform composed of modular layers. FastAPI exposes chat and plugin endpoints while the Control Room (Tauri) surfaces dashboards and plugin UIs. Plugins declare intents and optional UI panels in a manifest. The PromptRouter injects requests into templates and dispatches to plugins. Context is stored in Milvus and Redis with Postgres for structured logs. The SelfRefactor engine periodically tests and merges patches.

Key components:

- **FastAPI Gateway** – REST and WebSocket interface with RBAC.
- **PromptRouter** – parses user text and hands off to plugins.
- **Memory Layer** – Milvus, Redis and Postgres with exponential decay.
- **Hydra-Ops Mesh** – capsules executed via the event bus with guardrails.
- **SelfRefactor Engine** – runs tests in a sandbox and records sanitized logs.
- **Control Room** – Tauri desktop app streaming metrics and plugin UIs.
- **OSIRIS Knowledge Engine** – hybrid soft/hard reasoning with multi-hop queries.
- **EchoCore** – per-user training utilities and immutable vault backups.

For a comparison with OpenAI's CS-Agent stack see [side_by_side_openai_kari.md](side_by_side_openai_kari.md). More detail on capsules and risk management is in [mesh_arch.md](mesh_arch.md).
