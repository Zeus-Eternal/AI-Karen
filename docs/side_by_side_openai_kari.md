# OpenAI CS-Agents vs. Kari Ops Mesh

This guide summarises the differences between OpenAI's cloud-centric CS-Agent framework and Kari's local-first architecture.

| Aspect | OpenAI CS-Agents | Kari Ops Mesh |
|-------|------------------|--------------|
| **Deployment** | Runs on OpenAI's cloud infrastructure | Runs entirely on local servers or desktops |
| **LLM Source** | OpenAI models only | Local LLMs via Ollama with optional cloud fallback |
| **Guardrails** | Generic policies and hosted audit tools | Domain-specific YAML guardrails and RBAC |
| **Extensibility** | Limited to features exposed by OpenAI | Plugin framework with SelfRefactor auto‑patching |
| **Offline Use** | Not supported | Fully functional offline |
| **Data Control** | User data processed by OpenAI | Data never leaves your machine by default |

Kari reuses the idea of chained agents and event buses but implements them with a Prompt‑First plugin model and a Hydra-Ops mesh that can operate without external services. For heavy reasoning you may enable cloud plugins via `enable_external_workflow: true` in the plugin manifest.

See [architecture.md](architecture.md) for an overview of Kari's stack.
