"""Validation tests for the production model registry."""

from __future__ import annotations

import json
from pathlib import Path


REGISTRY_PATH = Path(__file__).resolve().parents[3] / "model_registry.json"
ALLOWED_SOURCES = {"local", "remote", "huggingface"}


def _load_registry() -> list[dict[str, object]]:
    """Load the shared registry file for assertions."""
    try:
        data = json.loads(REGISTRY_PATH.read_text())
    except FileNotFoundError as exc:
        raise AssertionError("model_registry.json is missing") from exc
    except json.JSONDecodeError as exc:  # pragma: no cover - invalid JSON would fail earlier
        raise AssertionError(f"model_registry.json is not valid JSON: {exc}") from exc

    if not isinstance(data, list):
        raise AssertionError("model_registry.json must contain a JSON array of model entries")

    return data


def test_registry_contains_production_entries():
    """Ensure that the registry only contains production ready models."""
    entries = _load_registry()
    assert entries, "Registry must contain at least one model entry"

    seen_names: set[str] = set()

    for entry in entries:
        assert isinstance(entry, dict), "Registry entries must be objects"

        name = entry.get("name")
        assert isinstance(name, str) and name.strip(), "Every model requires a non-empty name"
        assert name not in seen_names, f"Duplicate registry entry detected for {name}"
        seen_names.add(name)

        source = entry.get("source")
        assert source in ALLOWED_SOURCES, f"Unsupported source '{source}' for {name}"

        managed = entry.get("managed")
        assert isinstance(managed, bool), f"Managed flag must be boolean for {name}"

        if source == "remote":
            assert managed is False, f"Remote model {name} should not be marked as managed"
        else:
            assert managed is True, f"Local/Hugging Face model {name} must be marked as managed"
            path = entry.get("path")
            assert isinstance(path, str) and path.strip(), f"Managed model {name} needs a local path"

        capabilities = entry.get("capabilities")
        assert isinstance(capabilities, list) and capabilities, f"Model {name} must declare capabilities"
        for capability in capabilities:
            assert isinstance(capability, str) and capability.strip(), (
                f"Capability entries must be non-empty strings for {name}"
            )

        if "pricing" in entry:
            pricing = entry["pricing"]
            assert isinstance(pricing, dict), f"Pricing must be an object for {name}"
            for key in ("input_usd", "output_usd"):
                if key in pricing:
                    value = pricing[key]
                    assert isinstance(value, (int, float)) and value >= 0, (
                        f"Pricing value {key} must be a non-negative number for {name}"
                    )

        if "context_window" in entry:
            context_window = entry["context_window"]
            assert isinstance(context_window, int) and context_window > 0, (
                f"Context window must be a positive integer for {name}"
            )

        if "embedding_dimension" in entry:
            dimension = entry["embedding_dimension"]
            assert isinstance(dimension, int) and dimension > 0, (
                f"Embedding dimension must be positive for {name}"
            )


def test_registry_has_balanced_provider_coverage():
    """Verify that key providers referenced in the production UI are represented."""
    entries = _load_registry()
    providers = {entry.get("provider") for entry in entries}

    expected_providers = {"openai", "anthropic", "google", "groq", "mistral", "transformers", "llama-gguf", "voyage"}
    missing = expected_providers - providers

    assert not missing, f"Registry is missing provider coverage for: {', '.join(sorted(missing))}"

    # Ensure we also expose at least one embedding model and one chat model
    assert any("embeddings" in entry.get("capabilities", []) for entry in entries), (
        "Registry must include at least one embedding-capable model"
    )
    assert any("chat" in entry.get("capabilities", []) for entry in entries), (
        "Registry must include at least one chat-capable model"
    )
