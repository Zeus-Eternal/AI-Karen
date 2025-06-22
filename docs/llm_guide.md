# LLM Guide

Kari supports both local and remote language models. The default flow uses the local LNM & OSIRIS stack for reasoning, but plugins can delegate to HuggingFace or OpenAI.

## Local Models

- **LNM (Local Neural Module)** – thin orchestrator for GGUF models via `llama.cpp`.
- **OSIRIS** – in-house reasoning engine used by the SelfRefactor loop.

Download models once and point the LNM server to the GGUF file:

```bash
./lnm serve --model /models/mistral.gguf
```

In `plugins/hf_llm`, the handler will automatically download a model from HuggingFace if it is missing.

## Remote Providers

- **HuggingFace Inference** – via the `hf_llm` plugin. Configure `model_name` in the plugin parameters.
- **OpenAI** – via the `openai_llm` plugin. Set `OPENAI_API_KEY` and enable the plugin manifest.

## Choosing a Model

Use the LLM Manager page in the Control Room or call the `/models` endpoints to select a backend. The `llm_manager` plugin stores the active model in a local registry so the SelfRefactor engine and other components share the same backend. Plugins can override the global model by providing their own settings.

```bash
curl -X POST -H "Content-Type: application/json" \
    -d '{"model": "hf://mistralai/Mixtral-8x7B"}' http://localhost:8000/models/select
```

See [docs/plugin_spec.md](plugin_spec.md) for manifest details and [docs/self_refactor.md](self_refactor.md) for how the SelfRefactor engine selects models dynamically.
