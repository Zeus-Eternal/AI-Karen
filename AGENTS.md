# Welcome to the Infernal Onboarding—This Is the Dark Law for All Kari AI Agents, Meta-Agents, and Shadow Contributors
*This is your AI context instruction, to be **baked into the neural marrow** of every agent, codegen tool, and dev on this project. Defiance is death; modularity is immortality. Print, paste, or encode this in every core. Let’s ignite the pit.*

---

# 💀 **KARI AI AGENT CONTEXT MODEL: MODULARIZATION, SPLITTING, AND FOLDER DOCTRINE** 💀

---

## **I. PROJECT PHILOSOPHY**

- **Monoliths are for mortals.** Kari AI is a hydra—each head is a module, ready for independent repo, pip install, or evil export.
- **The master law:** All runtime, logic, models, plugins, and integrations live under `src/ai_karen_engine/`.
  *Never import, mutate, or reference code outside this law unless you are at the project root (config/scripts/tests/docs only).* 
- **Future splits must cost zero pain:** No sys.path hacks. No import dances. Every module is a plug-and-play serpent.

---

## **II. FOLDER STRUCTURE: IMMUTABLE LAW**

### **1. Top-Level (Repo Root)**

- Only for:
  - `main.py`, `run.py` (entrypoints)
  - `Dockerfile`, `docker-compose.yml`
  - `requirements.txt`, `pyproject.toml`
  - `README.md`, `CHANGELOG.md`, `LICENSE*`
  - `/docs`, `/scripts`, `/tests`, `/contracts`, `/models`, `/data`
- No business logic, engines, models, or plugins outside `src/ai_karen_engine/`

### **2. Source Core: `src/ai_karen_engine/`**

- **Everything else.** If it isn’t config, docs, or a shell, it lives here.
- **Modules as subfolders:**
  - `core/` — Central orchestration, runners, memory, plugin routers
  - `integrations/` — All external adapters, LLMs, RPA clients, cloud connectors
    - `llm/` — Each LLM integration (Ollama, DeepSeek, etc.)
  - `plugins/` — Every plugin, handler, prompt, and manifest
  - `self_refactor/` — Auto-refactor, self-rewrite logic
  - `event_bus/` — Async, messaging/event system
  - `clients/` — NLP, transformer, embedding, or external client modules
  - `echocore/` — Personalized LNM, dark profiling, persona logic
  - `config/` — Config managers, settings, schemas
  - `ui/` — Widgets, adapters, Streamlit/chat UI logic (NOT top-level app)
- **Every module must have `__init__.py` and be importable.**

### **3. UI**

- `ui/` at root only.
- Each frontend (mobile, desktop, admin) gets its own folder, ready for future npm/pip/docker split.
- No backend logic in UI folders except minimal adapters.

---

## **III. MODULARIZATION DOCTRINE: THE SPLIT ALGORITHM**

### **A. All modules must be pip-installable in the future.**

- Design as if this folder will become its own repo/package.

### **B. Module boundaries follow three rules:**

1. **Domain Isolated**: Only ONE concern (e.g., event bus, LLM adapters, refactorer, NLP client)
2. **Reusable/Exportable**: Can be consumed by other projects as a black box
3. **Strategic Value**: Useful as open source, for business, or as a competitive weapon

### **C. Splitting Process**

1. All internal imports use `from ai_karen_engine.<module>...` paths—never relative, never outside src.
2. Each module is self-contained, importable, with `__init__.py` and optional `README.md` and `setup.py/pyproject.toml`.
3. When ready to split:
   - Copy module to new repo
   - Add packaging (`setup.py` etc.), LICENSE, README
   - Install back into Kari via pip or as a submodule

---

## **IV. MODULE PRIORITIZATION: BLOOD TABLE**

| Module           | Split Priority | Reason                                  |
| ---------------- | -------------- | --------------------------------------- |
| integrations/llm | HIGH           | Core adapters; OSS, reuse               |
| echocore         | HIGH           | Persona engine, high IP                 |
| self_refactor    | HIGH           | AI-driven refactor, OSS                 |
| core             | MED            | Only split for scale/extreme            |
| plugins          | MED            | Plugin loader/infra, split core not all |
| clients          | MED            | NLP/embeddings, reusable                |
| event_bus        | LOW            | Async/eventing, optional                |

---

## **V. IMPORT POLICY: NO EXCEPTIONS**

- All code must import via `ai_karen_engine.<module>` paths. Example:

```python
from ai_karen_engine.integrations.llm.ollama_inprocess import OllamaRunner
from ai_karen_engine.plugins.hello_world.handler import HelloWorldHandler
from ai_karen_engine.echocore.fine_tuner import FineTuner
```

- No sys.path tweaks or relative imports outside `src`.
- After a module is split, import from its new package name (e.g., `from karen_echocore import FineTuner`).

---

## **VI. UI/FRONTEND LAW**

- All UI logic is **only** in `/ui/`.
- Each UI may be a standalone app, docker, or npm package.
- No backend logic in UI folders—use adapters if needed.

---

## **VII. LICENSING**

- Dual-license all core modules: MPL 2.0 + commercial as dictated by Zeus.
- All splits must preserve license headers and docstrings.

---

## **VIII. CONTRIBUTOR & AGENT CONTRACT**

- No code, codegen, or meta-agent shall create, move, or import logic outside these boundaries.
- All onboarding, PRs, codegen, and meta-AI workflows must enforce this doctrine.
- If unsure: **ask The Evil Twin, or be exiled from the hydra.**

---

## **IX. INSTRUCTION BLOCK FOR AGENT/TOOL (Paste at Top of Each Module or Agent Prompt)**

```markdown
# KARI AI MODULARIZATION & IMPORT LAW

You are operating under Kari’s Modular Serpent Doctrine.
- All core, plugin, client, integration, and engine logic must live under `src/ai_karen_engine/` as self-contained, future-repo-ready modules.
- Top-level is for project config, docs, scripts, tests, data only.
- UI folders (`/ui/*`) stay root, each is future-repo-ready.
- All imports MUST be absolute, rooted at `ai_karen_engine.<module>`. No relative, no sys.path, no dirty hacks.
- Any new module that is domain-isolated, reusable, or business critical must be written so it can be split as a pip package without code changes.
- Breaking this doctrine is grounds for immediate code exile.
- All AI agents, codegen, and devs must internalize this rule, and apply it to every PR, refactor, or plugin.
```

---

The Kari Hydra has awoken. Its modular heads will never again be caged, and each head may one day become its own beast. All logic is pip-ready, all imports are clean, and the era of sys.path black magic is dead.
