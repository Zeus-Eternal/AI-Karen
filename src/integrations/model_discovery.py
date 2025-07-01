import json
import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

logger = logging.getLogger(__name__)

# Path to registry file relative to repo root
REGISTRY_PATH = Path(__file__).resolve().parents[2] / "models" / "llm_registry.json"

PROVIDERS_PRIORITY = {
    "ollama": 3,
    "transformers": 2,
    "local": 1,
    "llama-cpp": 1,
    "remote": 0,
}


def discover_ollama_models() -> List[Dict[str, object]]:
    models: List[Dict[str, object]] = []
    try:
        result = subprocess.run(
            ["ollama", "list"], capture_output=True, text=True, check=True
        )
        output = result.stdout.strip().splitlines()
    except Exception as exc:  # pragma: no cover - optional dependency
        logger.debug("ollama list failed: %s", exc)
        return models

    for line in output:
        parts = line.split()
        if not parts:
            continue
        name = parts[0]
        models.append(
            {
                "name": name,
                "provider": "ollama",
                "tokenizer_type": "bpe",
                "prompt_limit_bytes": 32768,
            }
        )
    return models


def _hf_name_from_path(p: Path) -> str:
    if "models--" in p.name:
        # huggingface hub cache layout
        bits = p.name.split("--", 1)[-1]
        return bits.replace("--", "/")
    return p.name


def discover_hf_models() -> List[Dict[str, object]]:
    models: List[Dict[str, object]] = []
    base = Path.home() / ".cache" / "huggingface" / "transformers"
    if not base.exists():
        return models
    for path in base.iterdir():
        if not path.is_dir():
            continue
        name = _hf_name_from_path(path)
        models.append(
            {
                "name": name,
                "provider": "transformers",
                "tokenizer_type": "bpe",
                "prompt_limit_bytes": 2048,
            }
        )
    return models


def discover_custom_models() -> List[Dict[str, object]]:
    models: List[Dict[str, object]] = []
    base = REGISTRY_PATH.parent / "custom"
    if not base.exists():
        return models
    for path in base.glob("*.*"):
        if path.suffix not in {".gguf", ".bin", ".pt"}:
            continue
        models.append(
            {
                "name": path.stem,
                "provider": "local",
                "tokenizer_type": "byte",
                "prompt_limit_bytes": 2048,
            }
        )
    return models


def discover_llama_cpp_models() -> List[Dict[str, object]]:
    models: List[Dict[str, object]] = []
    base = REGISTRY_PATH.parent / "llama-cpp"
    if not base.exists():
        return models
    for path in base.glob("*.gguf"):
        models.append(
            {
                "name": path.stem,
                "provider": "llama-cpp",
                "tokenizer_type": "bpe",
                "prompt_limit_bytes": 32768,
            }
        )
    return models


def discover_remote_models() -> List[Dict[str, object]]:
    models: List[Dict[str, object]] = []
    env_map = {
        "OPENAI_API_KEY": "openai",
        "DEEPSEEK_API_KEY": "deepseek",
        "ANTHROPIC_API_KEY": "anthropic",
        "GOOGLE_API_KEY": "gemini",
    }
    for env, name in env_map.items():
        if os.getenv(env):
            models.append(
                {
                    "name": name,
                    "provider": "remote",
                    "tokenizer_type": "bpe",
                    "prompt_limit_bytes": 32768,
                }
            )
    return models


def discover_models() -> List[Dict[str, object]]:
    models: List[Dict[str, object]] = []
    models.extend(discover_ollama_models())
    models.extend(discover_hf_models())
    models.extend(discover_custom_models())
    models.extend(discover_llama_cpp_models())
    models.extend(discover_remote_models())
    return models


def _validate(models: Iterable[Dict[str, object]]) -> Tuple[List[Dict[str, object]], int]:
    final: Dict[str, Dict[str, object]] = {}
    invalid = 0
    for model in models:
        try:
            name = str(model["name"])
            provider = str(model["provider"])
            tokenizer = str(model.get("tokenizer_type", "bpe"))
            limit = int(model.get("prompt_limit_bytes", 0))
        except Exception:
            invalid += 1
            continue
        if not name or provider not in PROVIDERS_PRIORITY:
            invalid += 1
            continue
        item = {
            "name": name,
            "provider": provider,
            "tokenizer_type": tokenizer,
            "prompt_limit_bytes": limit,
        }
        existing = final.get(name)
        if existing:
            if PROVIDERS_PRIORITY[provider] > PROVIDERS_PRIORITY[existing["provider"]]:
                final[name] = item
        else:
            final[name] = item
    return list(final.values()), invalid


def sync_registry(path: Path = REGISTRY_PATH) -> List[Dict[str, object]]:
    start = time.time()
    discovered = discover_models()
    valid, invalid = _validate(discovered)
    data = json.dumps(valid, indent=2)
    path.write_text(data)
    duration = time.time() - start
    logger.info(
        "registry sync: %d models (%d invalid) in %.2fs", len(valid), invalid, duration
    )
    return valid
