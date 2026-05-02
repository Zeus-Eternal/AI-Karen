from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Iterable

from .runtime_compatibility import (
    estimate_vram_gb,
    infer_quantization,
    infer_model_artifact_kind,
    infer_model_format,
    is_vllm_available,
    probe_runtime_compatibility,
)

from ai_karen_engine.core.logging import get_logger
logger = get_logger(__name__)


def _normalize_policy_id(value: str) -> str:
    normalized = str(value or "").strip().replace("\\", "/")
    for prefix in ("models/transformers/", "transformers/", "/models/transformers/", "/app/models/transformers/"):
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):]
    return normalized.strip("/")


def _policy_model_names(discovery_config: dict[str, Any] | None, key: str) -> set[str]:
    policy = (discovery_config or {}).get("discovery_policy") or {}
    raw_values = policy.get(key) or []
    return {_normalize_policy_id(str(item)) for item in raw_values if str(item).strip()}


def _metadata_files(path: Path) -> set[str]:
    files: set[str] = set()
    if path.is_file():
        files.add(path.name)
        return files

    for candidate in path.rglob("*"):
        if candidate.is_file():
            files.add(candidate.relative_to(path).as_posix())
    return files


def _load_transformers_config(path: Path) -> dict[str, Any]:
    config_path = path / "config.json"
    if not path.is_dir() or not config_path.exists():
        return {}

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return {}

    if not isinstance(data, dict):
        return {}

    return data


def _display_name(path: Path) -> str:
    return path.stem if path.is_file() else path.name


def _has_model_marker(path: Path) -> bool:
    if not path.exists():
        return False
    if path.is_file():
        return path.suffix.lower() in {".gguf", ".onnx"}

    marker_files = {
        "config.json",
        "tokenizer.json",
        "tokenizer_config.json",
        "generation_config.json",
        "adapter_config.json",
        "modules.json",
        "1_Pooling/config.json",
        "preprocessor_config.json",
        "processor_config.json",
    }
    for marker in marker_files:
        if (path / marker).exists():
            return True
    if any(candidate.is_file() and candidate.suffix.lower() in {".gguf", ".onnx"} for candidate in path.iterdir()):
        return True
    return False


def _has_ancestor_model_marker(path: Path, base: Path) -> bool:
    current = path.parent
    while current != base and base in current.parents:
        if _has_model_marker(current):
            return True
        current = current.parent
    return False


def _infer_capabilities(model_format: str, artifact_kind: str, metadata_files: set[str]) -> list[str]:
    capabilities: list[str] = []
    if model_format == "gguf":
        capabilities.extend(["chat_completion", "text_generation"])
    elif model_format == "transformers":
        capabilities.extend(["chat_completion", "text_generation"])
        if artifact_kind in {"embedding_pipeline", "sentence_transformer"}:
            capabilities.extend(["embedding", "reranking"])
    elif model_format == "onnx":
        capabilities.extend(["embedding", "classification"])
    else:
        capabilities.append("external_endpoint")

    lowered = {item.lower() for item in metadata_files}
    if any("reranker" in item for item in lowered):
        capabilities.append("reranking")
    if any("embedding" in item for item in lowered):
        capabilities.append("embedding")
    if any("vision" in item or "processor_config.json" in item for item in lowered):
        capabilities.append("vlm_helper")
    return sorted(set(capabilities))


def _infer_model_type(model_format: str, capabilities: Iterable[str]) -> str:
    caps = set(capabilities)
    if "embedding" in caps:
        return "embedding"
    if "reranking" in caps:
        return "reranker"
    if "classification" in caps:
        return "classifier"
    if model_format == "gguf":
        return "text_generation"
    if model_format == "transformers":
        return "text_generation"
    return "unknown"


def discover_local_model_candidates(models_root: str | Path, discovery_config: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    root = Path(models_root).resolve()
    runtime_visible_transformers = _policy_model_names(discovery_config, "runtime_visible_transformers")
    runtime_excluded_transformers = _policy_model_names(discovery_config, "exclude_from_runtime_discovery")
    system_transformers = _policy_model_names(discovery_config, "system_transformers")
    
    # Deduplicate roots using resolved paths
    roots_set: set[Path] = {root} if root.exists() else set()
    if discovery_config:
        for item in discovery_config.get("model_roots", []) or []:
            candidate = Path(str(item)).resolve()
            if candidate.exists():
                roots_set.add(candidate)

    if not roots_set:
        return []

    # Sort roots by depth (shortest first) to ensure we find models at the highest level possible first
    roots = sorted(list(roots_set), key=lambda p: len(p.parts))

    records: list[dict[str, Any]] = []
    seen_paths: set[Path] = set()

    for base in roots:
        try:
            for path in base.iterdir():
                resolved_path = path.resolve()
                if resolved_path in seen_paths:
                    continue
                
                if path.name.startswith("."):
                    continue
                if not path.is_file() and not path.is_dir():
                    continue

                if path.is_file():
                    if path.suffix.lower() not in {".gguf", ".onnx"}:
                        continue
                else:
                    if not _has_model_marker(path):
                        continue

                seen_paths.add(resolved_path)
                metadata_files = _metadata_files(path if path.is_dir() else path.parent)
                config_data = _load_transformers_config(path if path.is_dir() else path.parent)
                architectures = config_data.get("architectures") or []

                # Generate a user-friendly model_id
                try:
                    # Use the primary models_root for relative IDs whenever possible
                    if resolved_path.is_relative_to(root):
                        rel_id = str(resolved_path.relative_to(root)).replace("\\", "/")
                    else:
                        rel_id = str(path.relative_to(base)).replace("\\", "/")
                except Exception:
                    rel_id = str(path.relative_to(base)).replace("\\", "/")

                # Unescape standard Transformers folder naming (e.g. Qwen--Qwen3.5 -> Qwen/Qwen3.5)
                # and strip common prefixes for a cleaner ID
                clean_id = rel_id
                for prefix in ["transformers/", "local-gguf/", "onnx/", "models/"]:
                    if clean_id.startswith(prefix):
                        clean_id = clean_id[len(prefix):]
                
                clean_id = clean_id.replace("--", "/")
                policy_id = _normalize_policy_id(rel_id)

                model_format = infer_model_format(path, metadata_files)
                artifact_kind = infer_model_artifact_kind(model_format, metadata_files)
                quantization = infer_quantization(metadata_files, path)
                size_bytes = path.stat().st_size if path.is_file() else sum(
                    candidate.stat().st_size for candidate in path.rglob("*") if candidate.is_file()
                )
                capabilities = _infer_capabilities(model_format, artifact_kind, metadata_files)
                compatibility = probe_runtime_compatibility(
                    model_format,
                    artifact_kind,
                    {
                        "adapter_only": artifact_kind == "adapter",
                        "capabilities": capabilities,
                        "model_type": _infer_model_type(model_format, capabilities),
                        "hf_model_type": str(config_data.get("model_type") or "").lower(),
                        "architectures": architectures,
                        "tokenizer_present": "tokenizer.json" in metadata_files or "tokenizer_config.json" in metadata_files,
                        "weights_present": any(file.endswith((".gguf", ".bin", ".safetensors")) for file in metadata_files) or path.is_file(),
                        "config_present": "config.json" in metadata_files or path.is_dir(),
                        "vllm_available": is_vllm_available(),
                    },
                )
                if (
                    model_format == "transformers"
                    and policy_id in runtime_excluded_transformers
                    and compatibility.get("compatibility_confidence") != "unsupported"
                ):
                    compatibility = {
                        **compatibility,
                        "compatible_runtimes": ["transformers_direct"],
                        "preferred_runtime": "transformers_direct",
                        "compatibility_confidence": "system_reserved",
                        "runtime_notes": [
                            *compatibility.get("runtime_notes", []),
                            "Reserved for Karen system helpers; hidden from chat/runtime discovery.",
                        ],
                    }

                is_runtime_visible = True
                if model_format == "transformers" and runtime_visible_transformers:
                    is_runtime_visible = policy_id in runtime_visible_transformers
                if policy_id in runtime_excluded_transformers:
                    is_runtime_visible = False

                weights_present = bool(any(file.endswith((".gguf", ".bin", ".safetensors")) for file in metadata_files) or path.is_file())
                if not weights_present:
                    is_runtime_visible = False

                records.append({
                    "model_id": clean_id,
                    "display_name": _display_name(path),
                    "path": str(resolved_path),
                    "relative_path": str(path.relative_to(base)),
                    "model_format": model_format,
                    "artifact_kind": artifact_kind,
                    "capabilities": capabilities,
                    "compatible_runtimes": compatibility["compatible_runtimes"],
                    "preferred_runtime": compatibility["preferred_runtime"],
                    "compatibility_confidence": compatibility["compatibility_confidence"],
                    "model_type": _infer_model_type(model_format, capabilities),
                    "hf_model_type": str(config_data.get("model_type") or "").lower(),
                    "runtime_visible": is_runtime_visible,
                    "system_reserved": policy_id in system_transformers,
                    "architectures": architectures,
                    "tokenizer_present": bool("tokenizer.json" in metadata_files or "tokenizer_config.json" in metadata_files),
                    "weights_present": weights_present,
                    "metadata_files": sorted(metadata_files),
                    "quantization": quantization,
                    "dtype": None,
                    "max_context": None,
                    "size_bytes": int(size_bytes),
                    "estimated_vram_gb": estimate_vram_gb(int(size_bytes), model_format, quantization),
                    "adapter_only": artifact_kind == "adapter",
                    "base_model_ref": None,
                    "security_flags": compatibility["security_flags"],
                    "runtime_notes": compatibility["runtime_notes"],
                })
        except Exception as exc:
            logger.error(f"Error scanning discovery root {base}: {exc}")
            continue

    return records
