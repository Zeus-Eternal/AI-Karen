# ICE Reasoning Wrapper

The Integrated Cognitive Engine (ICE) is Kari's lightweight deep reasoning layer. It builds on top of the SoftReasoningEngine and a local LLM to analyse user requests and surface relevant context.

## Overview

1. **Memory Recall** – recent text snippets are stored in the SoftReasoningEngine with surprise weighting. Queries return the top matches along with a recency-adjusted score.
2. **Entropy Check** – the wrapper computes an entropy score (1 - similarity). When entropy exceeds the configured threshold, the text is ingested as new knowledge.
3. **LLM Analysis** – matching snippets are fed to a local model (via `LLMUtils`) to generate a short summary highlighting novel information.
4. **Async Interface** – both synchronous and async `process` methods are available for integration with FastAPI endpoints.
5. **EchoCore Hook** – extracts user metadata via the EchoVault and feeds the personal LNM when training is enabled.

## Example

```python
from ai_karen_engine.core.reasoning.ice_integration import KariICEWrapper

ice = KariICEWrapper()
result = ice.process("How does Milvus handle vector deletes?")
print(result["analysis"])
```

The returned dictionary includes `entropy`, `memory_matches` and `analysis`. For asynchronous use call `await ice.aprocess(text)`.

## Use Cases

- **Deep Reasoning Capsules** – invoke the ICE wrapper when intents require additional context or summarisation.
- **SelfRefactor Hints** – feed commit messages or patch descriptions to capture surprising information for future runs.

```text
{ "entropy": 0.4, "memory_matches": [...], "analysis": "Milvus uses ..." }
```
