"""
Production model settings API routes.

These routes back the Karen AI theme "Model" settings tab with persisted
provider selection, encrypted API key storage, and local model discovery.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from dataclasses import replace
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, urlunparse
from urllib.request import Request, urlopen

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ai_karen_engine.auth.session import get_current_user


from ai_karen_engine.config.llm_provider_config import (
    AuthenticationType,
    MODEL_SETTINGS_PROVIDER_ORDER,
    ProviderAuthentication,
    ProviderConfig,
    ProviderEndpoint,
    ProviderLimits,
    ProviderModel,
    ProviderType,
    get_provider_config_manager,
)
from ai_karen_engine.config.model_registry import list_local_gguf_models
from ai_karen_engine.integrations.llm_registry import get_registry
from ai_karen_engine.services.formatting.settings_manager import get_settings_manager
from ai_karen_engine.models.secret_manager import get_secret_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings/model", tags=["model-settings"])
DEFAULT_OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL", "http://host.docker.internal:11434"
)
LEGACY_OLLAMA_IN_STACK_URL = "http://ollama:11434"
OLLAMA_HOST_RUNTIME = "host"
OLLAMA_CONTAINER_RUNTIME = "container"
DEFAULT_OLLAMA_CONTAINER_BASE_URL = "http://ollama:11434"
OLLAMA_RUNTIME_CACHE_TTL_SECONDS = 10.0
_ollama_runtime_status_cache: Dict[str, tuple[float, "RuntimeOptionPayload"]] = {}

PROVIDER_DOC_URLS = {
    "openai": "https://platform.openai.com/docs",
    "gemini": "https://ai.google.dev/gemini-api/docs",
    "anthropic": "https://docs.anthropic.com/en/api/messages",
    "meta": "https://www.llama.com/docs/overview/",
    "deepseek": "https://api-docs.deepseek.com/",
    "azure": "https://learn.microsoft.com/en-us/azure/ai-services/openai/reference",
    "amazon-nova": "https://docs.aws.amazon.com/nova/latest/userguide/getting-started.html",
    "moonshot": "https://platform.moonshot.ai/docs/api-reference",
    "mistral": "https://docs.mistral.ai/",
    "groq": "https://console.groq.com/docs/overview",
    "xai": "https://docs.x.ai/docs/overview",
    "qwen": "https://www.alibabacloud.com/help/en/model-studio/developer-reference/compatibility-of-openai-with-dashscope",
    "zai": "https://docs.z.ai/api-reference/introduction",
    "siliconflow": "https://docs.siliconflow.cn/en/api-reference/chat-completions/chat-completions",
    "together": "https://docs.together.ai/docs/chat-overview",
    "fireworks": "https://docs.fireworks.ai/api-reference/post-chatcompletions",
    "deepinfra": "https://deepinfra.com/docs/openai_api",
    "huggingface": "https://huggingface.co/docs/api-inference/index",
    "cohere": "https://docs.cohere.com/docs/chat-api",
    "novita": "https://novita.ai/docs/api-reference/model-apis-llm-create-chat-completion",
    "gmi-cloud": "https://docs.gmicloud.ai/",
    "ollama": "https://github.com/ollama/ollama/blob/main/docs/api.md",
}

SECRET_NAMES = {
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "meta": "META_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "azure": "AZURE_OPENAI_API_KEY",
    "amazon-nova": "AWS_BEDROCK_API_KEY",
    "moonshot": "MOONSHOT_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "groq": "GROQ_API_KEY",
    "xai": "XAI_API_KEY",
    "qwen": "QWEN_API_KEY",
    "zai": "ZAI_API_KEY",
    "siliconflow": "SILICONFLOW_API_KEY",
    "together": "TOGETHER_API_KEY",
    "fireworks": "FIREWORKS_API_KEY",
    "deepinfra": "DEEPINFRA_API_KEY",
    "huggingface": "HUGGINGFACE_API_KEY",
    "cohere": "COHERE_API_KEY",
    "novita": "NOVITA_API_KEY",
    "gmi-cloud": "GMI_CLOUD_API_KEY",
    "custom": "CUSTOM_LLM_API_KEY",
}


class CustomProviderCreateRequest(BaseModel):
    name: str
    display_name: str
    base_url: str
    model: str
    description: Optional[str] = None
    api_key_header: Optional[str] = None
    api_key_prefix: Optional[str] = None
    custom_headers: Optional[Dict[str, str]] = None


class ProviderModelPayload(BaseModel):
    id: str
    name: str
    family: str = "unknown"
    context_length: Optional[int] = None
    max_tokens: Optional[int] = None
    capabilities: List[str] = Field(default_factory=list)
    supports_streaming: bool = True
    supports_functions: bool = False
    supports_vision: bool = False
    source: str = "configured"


class ProviderPayload(BaseModel):
    id: str
    display_name: str
    description: str
    provider_type: str
    docs_url: Optional[str] = None
    base_url: Optional[str] = None
    default_base_url: Optional[str] = None
    default_model: Optional[str] = None
    selected_model: Optional[str] = None
    models: List[ProviderModelPayload] = Field(default_factory=list)
    requires_api_key: bool = False
    api_key_configured: bool = False
    api_key_masked: Optional[str] = None
    selectable: bool = True
    api_key_header: str = "Authorization"
    api_key_prefix: str = "Bearer"
    custom_headers: Dict[str, str] = Field(default_factory=dict)
    supports_base_url_override: bool = True
    supports_model_discovery: bool = False
    supports_model_pull: bool = False
    supports_custom_auth: bool = False
    supports_manual_model_entry: bool = False
    runtime_source: Optional[str] = None
    runtime_options: List["RuntimeOptionPayload"] = Field(default_factory=list)


class ModelSettingsResponse(BaseModel):
    selected_provider: str
    selected_model: str
    providers: List[ProviderPayload]
    updated_at: str


class ModelSettingsUpdateRequest(BaseModel):
    provider: str
    model: Optional[str] = None
    base_url: Optional[str] = None
    runtime_source: Optional[str] = None
    api_key: Optional[str] = None
    clear_api_key: bool = False
    api_key_header: Optional[str] = None
    api_key_prefix: Optional[str] = None
    custom_headers: Optional[Dict[str, str]] = None


class ProviderModelsResponse(BaseModel):
    provider: str
    base_url: Optional[str] = None
    models: List[ProviderModelPayload]
    discovered_at: str


class ProviderSettingsValidationRequest(BaseModel):
    provider: str
    model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None


class ProviderSettingsValidationResponse(BaseModel):
    provider: str
    valid: bool
    message: str
    models_discovered: Optional[int] = None


class OllamaPullRequest(BaseModel):
    model: str
    base_url: Optional[str] = None


class RuntimeOptionPayload(BaseModel):
    source: str
    label: str
    base_url: str
    available: bool
    active: bool = False
    status: str
    message: str
    setup_required: bool = False
    setup_command: Optional[str] = None
    install_supported: bool = False


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _provider_sort_key(provider: ProviderConfig) -> tuple[int, int, str]:
    try:
        order = MODEL_SETTINGS_PROVIDER_ORDER.index(provider.name)
    except ValueError:
        order = len(MODEL_SETTINGS_PROVIDER_ORDER)
    return (order, -provider.priority, provider.display_name.lower())


def _get_provider_override(provider_id: str) -> Dict[str, Any]:
    settings = get_settings_manager()
    override = settings.get_setting(f"model_providers.{provider_id}", {}) or {}
    return override if isinstance(override, dict) else {}


def _get_secret_name(provider_id: str, provider: ProviderConfig) -> Optional[str]:
    if provider_id in SECRET_NAMES:
        return SECRET_NAMES[provider_id]
    return provider.authentication.api_key_env_var


def _get_saved_api_key(provider_id: str, provider: ProviderConfig) -> Optional[str]:
    secret_manager = get_secret_manager()
    secret_name = _get_secret_name(provider_id, provider)
    if secret_name:
        secret_value = secret_manager.get_secret(secret_name)
        if secret_value:
            return secret_value
    env_var = provider.authentication.api_key_env_var
    if env_var:
        return os.getenv(env_var)
    return None


def _has_saved_api_key(provider_id: str, provider: ProviderConfig) -> bool:
    secret_manager = get_secret_manager()
    secret_name = _get_secret_name(provider_id, provider)
    if secret_name and secret_manager.has_secret(secret_name):
        return True
    env_var = provider.authentication.api_key_env_var
    return bool(env_var and os.getenv(env_var))


def _sanitize_custom_headers(headers: Dict[str, str]) -> Dict[str, str]:
    return {
        str(key).strip(): str(value).strip()
        for key, value in headers.items()
        if str(key).strip() and str(value).strip()
    }


def _mask_api_key(secret_value: Optional[str]) -> Optional[str]:
    if not secret_value:
        return None
    trimmed = secret_value.strip()
    if not trimmed:
        return None
    if len(trimmed) <= 8:
        return "•" * len(trimmed)
    return f"{trimmed[:4]}{'•' * max(4, len(trimmed) - 8)}{trimmed[-4:]}"


def _normalize_base_url(base_url: Optional[str]) -> Optional[str]:
    if base_url is None:
        return None
    stripped = base_url.strip()
    if not stripped:
        return ""
    return stripped.rstrip("/")


def _normalize_ollama_base_url(base_url: Optional[str]) -> str:
    normalized = _normalize_base_url(base_url) or DEFAULT_OLLAMA_BASE_URL
    parsed = urlparse(normalized)
    path = parsed.path.rstrip("/")
    if path.endswith("/api"):
        return normalized
    return f"{normalized}/api"


def _normalize_ollama_runtime_source(runtime_source: Optional[str]) -> str:
    candidate = str(runtime_source or "").strip().lower()
    if candidate == OLLAMA_CONTAINER_RUNTIME:
        return OLLAMA_CONTAINER_RUNTIME
    return OLLAMA_HOST_RUNTIME


def _infer_ollama_runtime_source(base_url: Optional[str]) -> str:
    normalized = _normalize_ollama_base_url(base_url)
    hostname = (urlparse(normalized).hostname or "").strip().lower()
    if hostname == "ollama":
        return OLLAMA_CONTAINER_RUNTIME
    return OLLAMA_HOST_RUNTIME


def _resolve_ollama_runtime_source(
    override: Dict[str, Any], explicit_base_url: Optional[str] = None
) -> str:
    stored_runtime_source = str(override.get("runtime_source") or "").strip()
    if stored_runtime_source:
        return _normalize_ollama_runtime_source(stored_runtime_source)
    if explicit_base_url:
        return _infer_ollama_runtime_source(explicit_base_url)
    if override.get("base_url"):
        return _infer_ollama_runtime_source(str(override.get("base_url")))
    return OLLAMA_HOST_RUNTIME


def _base_url_for_ollama_runtime(runtime_source: str) -> str:
    if _normalize_ollama_runtime_source(runtime_source) == OLLAMA_CONTAINER_RUNTIME:
        return _normalize_ollama_base_url(DEFAULT_OLLAMA_CONTAINER_BASE_URL)
    return _normalize_ollama_base_url(DEFAULT_OLLAMA_BASE_URL)


def _iter_ollama_base_urls(base_url: Optional[str]) -> List[str]:
    normalized = _normalize_ollama_base_url(base_url)
    parsed = urlparse(normalized)
    hostname = parsed.hostname or ""

    candidates = [normalized]
    aliases: List[str] = []
    if hostname in {"localhost", "127.0.0.1", "::1", "host.docker.internal"}:
        aliases.extend(["host.docker.internal", "172.17.0.1"])
    elif hostname == "ollama":
        aliases.extend(["host.docker.internal", "172.17.0.1"])

    for alias in aliases:
        alias_netloc = alias
        if parsed.port:
            alias_netloc = f"{alias}:{parsed.port}"
        aliased = urlunparse(parsed._replace(netloc=alias_netloc))
        if aliased not in candidates:
            candidates.append(aliased)

    return candidates


def _iter_ollama_runtime_candidates(runtime_source: str) -> List[str]:
    if _normalize_ollama_runtime_source(runtime_source) == OLLAMA_CONTAINER_RUNTIME:
        return [_base_url_for_ollama_runtime(OLLAMA_CONTAINER_RUNTIME)]
    return _iter_ollama_base_urls(_base_url_for_ollama_runtime(OLLAMA_HOST_RUNTIME))


def _probe_ollama_runtime_option(runtime_source: str) -> RuntimeOptionPayload:
    runtime_source = _normalize_ollama_runtime_source(runtime_source)
    now = time.monotonic()
    cached = _ollama_runtime_status_cache.get(runtime_source)
    if cached and (now - cached[0]) < OLLAMA_RUNTIME_CACHE_TTL_SECONDS:
        return cached[1]

    base_url = _base_url_for_ollama_runtime(runtime_source)
    label = (
        "Host Machine Ollama"
        if runtime_source == OLLAMA_HOST_RUNTIME
        else "Container Ollama"
    )
    message = ""
    available = False
    last_error: Optional[Exception] = None

    for candidate in _iter_ollama_runtime_candidates(runtime_source):
        try:
            _fetch_json(f"{candidate}/tags", timeout=2.0)
            available = True
            message = (
                "Karen can reach the host machine Ollama runtime from the API container."
                if runtime_source == OLLAMA_HOST_RUNTIME
                else "Karen can reach the optional Ollama sidecar on the Docker network."
            )
            break
        except Exception as exc:
            last_error = exc

    if available:
        payload = RuntimeOptionPayload(
            source=runtime_source,
            label=label,
            base_url=base_url,
            available=True,
            status="available",
            message=message,
            install_supported=runtime_source == OLLAMA_CONTAINER_RUNTIME,
        )
    else:
        if runtime_source == OLLAMA_HOST_RUNTIME:
            payload = RuntimeOptionPayload(
                source=runtime_source,
                label=label,
                base_url=base_url,
                available=False,
                status="unavailable",
                message=(
                    "Host-machine Ollama is not reachable from the API container. "
                    "The most common cause is a loopback-only host binding: Ollama is listening on "
                    "`127.0.0.1:11434` instead of `0.0.0.0:11434`. "
                    "If Ollama is installed on the host, ensure it listens on `0.0.0.0:11434` "
                    "and the API container keeps `host.docker.internal:host-gateway`."
                ),
                setup_required=True,
            )
        else:
            payload = RuntimeOptionPayload(
                source=runtime_source,
                label=label,
                base_url=base_url,
                available=False,
                status="setup_required",
                message="Container Ollama is not currently provisioned in the Karen stack.",
                setup_required=True,
                setup_command="docker compose --profile ollama up -d ollama",
                install_supported=True,
            )
        if isinstance(last_error, HTTPError):
            payload.message = payload.message.rstrip(".") + f" HTTP {last_error.code}."
        elif isinstance(last_error, URLError):
            payload.message = payload.message.rstrip(".") + "."

    _ollama_runtime_status_cache[runtime_source] = (now, payload)
    return payload


def _resolve_provider_base_url(
    provider: ProviderConfig, override: Dict[str, Any]
) -> str:
    saved = _normalize_base_url(override.get("base_url"))
    fallback = (
        _normalize_base_url(provider.endpoint.base_url if provider.endpoint else None)
        or ""
    )
    if provider.name == "gemini":
        return fallback
    if provider.name == "ollama":
        return _base_url_for_ollama_runtime(
            _resolve_ollama_runtime_source(override, saved or fallback)
        )
    resolved = saved if saved is not None else fallback
    return resolved


def _supports_base_url_override(provider: ProviderConfig) -> bool:
    return provider.name not in {"gemini"}


def _is_custom_provider(provider: ProviderConfig) -> bool:
    return (
        provider.name == "custom"
        or provider.authentication.type == AuthenticationType.CUSTOM
    )


def _build_auth_headers(
    provider_id: str, provider: ProviderConfig, api_key: Optional[str]
) -> Dict[str, str]:
    headers = dict(provider.authentication.custom_headers or {})
    if api_key and provider.authentication.type in {
        AuthenticationType.API_KEY,
        AuthenticationType.CUSTOM,
    }:
        prefix = (provider.authentication.api_key_prefix or "").strip()
        token = f"{prefix} {api_key}".strip() if prefix else api_key
        headers[provider.authentication.api_key_header or "Authorization"] = token
    return headers


def _model_to_payload(
    model: ProviderModel, source: str = "configured"
) -> ProviderModelPayload:
    return ProviderModelPayload(
        id=model.id,
        name=model.name,
        family=model.family,
        context_length=model.context_length,
        max_tokens=model.max_tokens,
        capabilities=sorted(model.capabilities),
        supports_streaming=model.supports_streaming,
        supports_functions=model.supports_functions,
        supports_vision=model.supports_vision,
        source=source,
    )


def _infer_family(model_id: str) -> str:
    if not model_id:
        return "unknown"
    sanitized = model_id.replace("_", "-").replace("/", "-")
    return sanitized.split("-", 1)[0] or "unknown"


def _normalize_provider_id(provider_id: Optional[str]) -> str:
    value = str(provider_id or "").strip().lower()
    if value in {"localgguf", "local_gguf"}:
        return "local_gguf"
    return value


def _normalize_selected_model_for_provider(
    provider_name: str, model_id: Optional[str]
) -> str:
    value = str(model_id or "").strip()
    if not value:
        return ""
    if (
        provider_name == "local_gguf"
        and value != "auto-detect-gguf"
        and not value.endswith(".gguf")
    ):
        return f"{value}.gguf"
    return value


def _make_model_payload(
    model_id: str,
    *,
    name: Optional[str] = None,
    family: Optional[str] = None,
    context_length: Optional[int] = None,
    max_tokens: Optional[int] = None,
    capabilities: Optional[List[str]] = None,
    supports_streaming: bool = True,
    supports_functions: bool = False,
    supports_vision: bool = False,
    source: str = "discovered",
) -> ProviderModelPayload:
    return ProviderModelPayload(
        id=model_id,
        name=name or model_id,
        family=family or _infer_family(model_id),
        context_length=context_length,
        max_tokens=max_tokens,
        capabilities=capabilities or [],
        supports_streaming=supports_streaming,
        supports_functions=supports_functions,
        supports_vision=supports_vision,
        source=source,
    )


def _fetch_json(
    url: str,
    *,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    payload: Optional[Dict[str, Any]] = None,
    timeout: float = 8.0,
) -> Any:
    request_headers = {"Content-Type": "application/json"}
    if headers:
        request_headers.update(headers)

    body = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")

    request = Request(url, data=body, headers=request_headers, method=method)
    with urlopen(request, timeout=timeout) as response:
        content = response.read().decode("utf-8")
        return json.loads(content) if content else {}


def _extract_models_from_payload(payload: Any) -> List[ProviderModelPayload]:
    raw_items: Any
    if isinstance(payload, dict):
        raw_items = (
            payload.get("data") or payload.get("models") or payload.get("items") or []
        )
    else:
        raw_items = payload

    if not isinstance(raw_items, list):
        return []

    models: List[ProviderModelPayload] = []
    seen: set[str] = set()
    for item in raw_items:
        if isinstance(item, str):
            model_id = item.strip()
            if model_id and model_id not in seen:
                seen.add(model_id)
                models.append(_make_model_payload(model_id))
            continue
        if not isinstance(item, dict):
            continue

        model_id = str(
            item.get("id") or item.get("name") or item.get("model") or ""
        ).strip()
        if not model_id or model_id in seen:
            continue
        seen.add(model_id)

        modalities = item.get("modalities") or item.get("supported_modalities") or []
        supports_vision = False
        if isinstance(modalities, list):
            supports_vision = any(
                "image" in str(modality).lower() for modality in modalities
            )

        capabilities = []
        if supports_vision:
            capabilities.append("vision")
        if (
            item.get("supports_tools")
            or item.get("tool_use")
            or item.get("function_calling")
        ):
            capabilities.append("tool_use")

        context_length = (
            item.get("context_length")
            or item.get("context_window")
            or item.get("max_input_tokens")
        )
        max_tokens = item.get("max_output_tokens") or item.get("max_tokens")

        models.append(
            _make_model_payload(
                model_id,
                name=str(item.get("display_name") or item.get("name") or model_id),
                family=_infer_family(model_id),
                context_length=int(context_length)
                if isinstance(context_length, int)
                else None,
                max_tokens=int(max_tokens) if isinstance(max_tokens, int) else None,
                capabilities=capabilities,
                supports_functions="tool_use" in capabilities,
                supports_vision=supports_vision,
            )
        )

    return models


def _discover_remote_models(
    provider: ProviderConfig, override: Dict[str, Any]
) -> List[ProviderModelPayload]:
    if not provider.endpoint or not provider.endpoint.models_endpoint:
        return []

    api_key = _get_saved_api_key(provider.name, provider)
    if (
        provider.authentication.type
        in {AuthenticationType.API_KEY, AuthenticationType.CUSTOM}
        and not api_key
    ):
        return []

    base_url = _resolve_provider_base_url(provider, override)
    if not base_url:
        return []

    models_url = f"{base_url}{provider.endpoint.models_endpoint}"
    headers = _build_auth_headers(provider.name, provider, api_key)

    try:
        payload = _fetch_json(models_url, headers=headers, timeout=10.0)
        return _extract_models_from_payload(payload)
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        logger.debug("Remote model discovery failed for %s: %s", provider.name, exc)
        return []
    except Exception as exc:  # pragma: no cover - defensive fallback
        logger.warning(
            "Unexpected remote model discovery error for %s: %s", provider.name, exc
        )
        return []


def _discover_ollama_models(base_url: str) -> List[ProviderModelPayload]:
    last_error: Optional[Exception] = None
    payload: Any = {}
    for candidate in _iter_ollama_base_urls(base_url):
        try:
            payload = _fetch_json(f"{candidate}/tags", timeout=6.0)
            break
        except Exception as exc:
            last_error = exc
    else:
        if last_error:
            raise last_error

    raw_models = payload.get("models", []) if isinstance(payload, dict) else []

    models: List[ProviderModelPayload] = []
    seen: set[str] = set()
    for item in raw_models:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name or name in seen:
            continue
        seen.add(name)
        details = item.get("details") or {}
        capabilities = ["local"]
        family = str(details.get("family") or _infer_family(name))
        if "vision" in name.lower() or "llava" in name.lower():
            capabilities.append("vision")
        models.append(
            _make_model_payload(
                name,
                name=name,
                family=family,
                capabilities=capabilities,
                supports_vision="vision" in capabilities,
            )
        )
    return models


def _discover_local_gguf_models(base_url: Optional[str]) -> List[ProviderModelPayload]:
    models: List[ProviderModelPayload] = []
    seen: set[str] = set()

    for model_name in list_local_gguf_models():
        if model_name.startswith("<") and model_name.endswith(">"):
            continue
        if model_name in seen:
            continue
        seen.add(model_name)
        models.append(
            _make_model_payload(
                model_name,
                name=model_name,
                family=_infer_family(model_name),
                capabilities=["local", "gguf"],
            )
        )

    normalized_base = _normalize_base_url(base_url)
    if normalized_base:
        remote_url = (
            normalized_base
            if normalized_base.endswith("/models")
            else f"{normalized_base}/models"
        )
        try:
            payload = _fetch_json(remote_url, timeout=6.0)
            for model in _extract_models_from_payload(payload):
                if model.id in seen:
                    continue
                seen.add(model.id)
                models.append(model)
        except Exception as exc:  # pragma: no cover - local service optional
            logger.debug("Local GGUF server discovery skipped: %s", exc)

    return models


def _configured_models(provider: ProviderConfig) -> List[ProviderModelPayload]:
    models = [_model_to_payload(model) for model in provider.models]
    if models:
        return models

    default_model = str(provider.default_model or "").strip()
    if default_model:
        return [
            _make_model_payload(
                default_model,
                name=default_model,
                family=_infer_family(default_model),
                source="default",
            )
        ]
    return []


def _load_provider_models(
    provider: ProviderConfig, override: Dict[str, Any]
) -> List[ProviderModelPayload]:
    if provider.name == "ollama":
        return _discover_ollama_models(_resolve_provider_base_url(provider, override))

    if provider.name == "local_gguf":
        discovered = _discover_local_gguf_models(
            _resolve_provider_base_url(provider, override)
        )
        return discovered or _configured_models(provider)

    discovered = _discover_remote_models(provider, override)
    return discovered or _configured_models(provider)


def _build_provider_payload(
    provider: ProviderConfig, selected_provider: str, selected_model: str
) -> ProviderPayload:
    override = _get_provider_override(provider.name)
    base_url = _resolve_provider_base_url(provider, override)
    runtime_source = (
        _resolve_ollama_runtime_source(override, base_url)
        if provider.name == "ollama"
        else None
    )
    runtime_options = []
    if provider.name == "ollama":
        runtime_options = [
            _probe_ollama_runtime_option(OLLAMA_HOST_RUNTIME),
            _probe_ollama_runtime_option(OLLAMA_CONTAINER_RUNTIME),
        ]
        runtime_options = [
            option.copy(update={"active": option.source == runtime_source})
            for option in runtime_options
        ]
    last_model = _normalize_selected_model_for_provider(
        provider.name,
        override.get("last_model") or provider.default_model or "",
    )
    provider_selected_model = (
        _normalize_selected_model_for_provider(provider.name, selected_model)
        if provider.name == selected_provider
        else last_model
    )

    # Keep settings reads lightweight and deterministic.
    # Explicit model discovery happens via /providers/{provider_id}/models.
    models = _configured_models(provider)

    if provider_selected_model and all(
        model.id != provider_selected_model for model in models
    ):
        models.append(
            _make_model_payload(
                provider_selected_model,
                name=provider_selected_model,
                family=_infer_family(provider_selected_model),
                source="saved",
            )
        )

    requires_api_key = provider.authentication.type in {
        AuthenticationType.API_KEY,
        AuthenticationType.CUSTOM,
    }
    api_key_configured = _has_saved_api_key(provider.name, provider)
    api_key_masked = (
        _mask_api_key(_get_saved_api_key(provider.name, provider))
        if api_key_configured
        else None
    )
    return ProviderPayload(
        id=provider.name,
        display_name=provider.display_name,
        description=provider.description,
        provider_type=provider.provider_type.value,
        docs_url=PROVIDER_DOC_URLS.get(provider.name),
        base_url=base_url or None,
        default_base_url=provider.endpoint.base_url if provider.endpoint else None,
        default_model=provider.default_model,
        selected_model=provider_selected_model or None,
        models=models,
        requires_api_key=requires_api_key,
        api_key_configured=api_key_configured,
        api_key_masked=api_key_masked,
        # Settings reads should reflect saved configurability only. Runtime/provider
        # initialization happens during explicit validation, save, or actual use so
        # the UI does not eagerly instantiate inactive cloud providers.
        selectable=(not requires_api_key) or api_key_configured,
        api_key_header=str(
            override.get("api_key_header")
            or provider.authentication.api_key_header
            or "Authorization"
        ),
        api_key_prefix=str(
            override.get("api_key_prefix")
            if override.get("api_key_prefix") is not None
            else (provider.authentication.api_key_prefix or "")
        ),
        custom_headers=_sanitize_custom_headers(
            override.get("custom_headers")
            or provider.authentication.custom_headers
            or {}
        ),
        supports_base_url_override=_supports_base_url_override(provider),
        supports_model_discovery=provider.name in {"ollama", "local_gguf"}
        or bool(provider.endpoint and provider.endpoint.models_endpoint),
        supports_model_pull=provider.name == "ollama",
        supports_custom_auth=_is_custom_provider(provider),
        supports_manual_model_entry=_is_custom_provider(provider)
        or provider.name in {"ollama", "local_gguf"},
        runtime_source=runtime_source,
        runtime_options=runtime_options,
    )


def _build_response() -> ModelSettingsResponse:
    settings = get_settings_manager()
    provider_manager = get_provider_config_manager()
    selected_provider = _normalize_provider_id(
        settings.get_setting("provider", "ollama") or "ollama"
    )
    selected_model = str(settings.get_setting("model", "") or "")

    providers: List[ProviderPayload] = []
    for provider in sorted(provider_manager.list_providers(), key=_provider_sort_key):
        try:
            providers.append(
                _build_provider_payload(provider, selected_provider, selected_model)
            )
        except Exception as exc:  # pragma: no cover - defensive response hardening
            logger.exception(
                "Skipping invalid model-settings provider payload for %s: %s",
                provider.name,
                exc,
            )

    valid_provider_ids = {provider.id for provider in providers}
    if providers and selected_provider not in valid_provider_ids:
        selected_provider = next(
            (provider.id for provider in providers if provider.id == "ollama"),
            providers[0].id,
        )

    active = (
        next(
            (provider for provider in providers if provider.id == selected_provider),
            providers[0],
        )
        if providers
        else None
    )
    if active and not active.selectable:
        fallback = next(
            (
                provider
                for provider in providers
                if provider.provider_type == ProviderType.LOCAL.value
                and provider.selectable
            ),
            next((provider for provider in providers if provider.selectable), active),
        )
        selected_provider = fallback.id
        active = fallback

    if not selected_model and providers:
        active = active or next(
            (provider for provider in providers if provider.id == selected_provider),
            providers[0],
        )
        selected_model = active.selected_model or active.default_model or ""
    elif active:
        selected_model = _normalize_selected_model_for_provider(
            active.id, selected_model
        )

    return ModelSettingsResponse(
        selected_provider=selected_provider,
        selected_model=selected_model,
        providers=providers,
        updated_at=_utc_now(),
    )


def _persist_provider_config(
    provider: ProviderConfig,
    *,
    model: str,
    base_url: Optional[str],
    api_key_header: Optional[str],
    api_key_prefix: Optional[str],
    custom_headers: Dict[str, str],
) -> None:
    provider_manager = get_provider_config_manager()

    endpoint = provider.endpoint
    if endpoint:
        updated_base_url = endpoint.base_url
        if base_url is not None:
            updated_base_url = base_url
            if provider.name == "ollama":
                updated_base_url = _normalize_ollama_base_url(base_url)
        endpoint = replace(endpoint, base_url=updated_base_url)

    authentication = provider.authentication
    authentication = replace(
        authentication,
        api_key_header=api_key_header
        if api_key_header is not None
        else authentication.api_key_header,
        api_key_prefix=api_key_prefix
        if api_key_prefix is not None
        else authentication.api_key_prefix,
        custom_headers=custom_headers or authentication.custom_headers,
    )

    models = list(provider.models)
    if model and all(existing.id != model for existing in models):
        models.append(
            ProviderModel(
                id=model,
                name=model,
                family=_infer_family(model),
                capabilities={"text"},
            )
        )

    provider_manager.update_provider(
        provider.name,
        {
            "endpoint": endpoint,
            "authentication": authentication,
            "default_model": model or provider.default_model,
            "models": models,
        },
    )


def _refresh_runtime_provider_state(
    provider_name: str, model_name: Optional[str]
) -> None:
    """Invalidate cached runtime provider/model instances after settings changes."""
    try:
        registry = get_registry()
        registry.invalidate_provider_cache(provider_name)
    except Exception as exc:  # pragma: no cover - defensive hardening
        logger.warning(
            "Failed to invalidate provider registry cache for %s: %s",
            provider_name,
            exc,
        )

    try:
        from ai_karen_engine.llm_orchestrator import LLMOrchestrator

        orchestrator = LLMOrchestrator()
        prefixes = {f"{provider_name}:"}
        if provider_name == "local_gguf":
            prefixes.add("local_gguf:")

        with orchestrator.registry._lock:
            stale_ids = [
                mid
                for mid in orchestrator.registry._models.keys()
                if any(mid.startswith(prefix) for prefix in prefixes)
            ]
            for mid in stale_ids:
                orchestrator.registry._models.pop(mid, None)
        if stale_ids:
            logger.info(
                "Invalidated %d orchestrator model cache entrie(s) for provider %s",
                len(stale_ids),
                provider_name,
            )
    except Exception as exc:  # pragma: no cover - defensive hardening
        logger.warning(
            "Failed to invalidate orchestrator cache for %s: %s", provider_name, exc
        )


def _validate_runtime_provider(provider_name: str, model_name: str) -> None:
    """Validate that the saved provider config can instantiate and authenticate."""
    provider_config = get_provider_config_manager().get_provider(provider_name)
    if (
        provider_config
        and _is_custom_provider(provider_config)
        and provider_name != "custom"
    ):
        return

    try:
        registry = get_registry()
        provider = registry.get_provider(provider_name, model=model_name)
    except Exception as exc:  # pragma: no cover - defensive hardening
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to initialize {provider_name}: {exc}",
        ) from exc

    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to initialize {provider_name}.",
        )

    initialization_error = getattr(provider, "initialization_error", None)
    if initialization_error:
        error_text = str(initialization_error)
        lowered = error_text.lower()
        error_status = (
            status.HTTP_400_BAD_REQUEST
            if any(
                marker in lowered
                for marker in (
                    "invalid",
                    "unauthorized",
                    "forbidden",
                    "api key",
                    "credential",
                )
            )
            else status.HTTP_502_BAD_GATEWAY
        )
        raise HTTPException(status_code=error_status, detail=error_text)


def _validate_runtime_provider_with_details(
    provider_name: str,
    model_name: str,
    api_key: Optional[str],
    base_url: Optional[str],
) -> Dict[str, Any]:
    """Run provider validation and return initialization details.

    This function may perform blocking network I/O depending on provider.
    """

    registry = get_registry()
    registry.invalidate_provider_cache(provider_name)

    init_kwargs: Dict[str, Any] = {}
    if model_name:
        init_kwargs["model"] = model_name
    if api_key:
        init_kwargs["api_key"] = api_key
    # Only pass base_url when it is explicitly configured. Passing None can break
    # providers whose constructors do not accept a base_url argument (e.g. Gemini).
    if base_url:
        init_kwargs["base_url"] = base_url

    runtime_provider = registry.get_provider(provider_name, **init_kwargs)

    if runtime_provider is None:
        return {
            "valid": False,
            "message": f"Failed to initialize {provider_name}.",
            "models_discovered": None,
        }

    initialization_error = getattr(runtime_provider, "initialization_error", None)
    if initialization_error:
        return {
            "valid": False,
            "message": str(initialization_error),
            "models_discovered": None,
        }

    models_discovered: Optional[int] = None
    get_models = getattr(runtime_provider, "get_models", None)
    if callable(get_models):
        try:
            models = get_models()
            models_discovered = len(models) if isinstance(models, list) else None
        except Exception:
            models_discovered = None

    return {
        "valid": True,
        "message": "credentials validated successfully.",
        "models_discovered": models_discovered,
    }


@router.get("", response_model=ModelSettingsResponse)
async def get_model_settings(
    current_user=Depends(get_current_user),
) -> ModelSettingsResponse:
    """Return persisted provider/model settings plus provider metadata."""

    return _build_response()


@router.put("", response_model=ModelSettingsResponse)
async def update_model_settings(
    request: ModelSettingsUpdateRequest,
    current_user=Depends(get_current_user),
) -> ModelSettingsResponse:
    """Persist the selected provider/model and provider-specific auth settings."""

    provider_manager = get_provider_config_manager()
    settings = get_settings_manager()
    secret_manager = get_secret_manager()

    normalized_provider_id = _normalize_provider_id(request.provider)
    provider = provider_manager.get_provider(normalized_provider_id)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found"
        )

    requires_api_key = provider.authentication.type in {
        AuthenticationType.API_KEY,
        AuthenticationType.CUSTOM,
    }
    provided_api_key = (request.api_key or "").strip()
    has_configured_api_key = _has_saved_api_key(provider.name, provider)
    if requires_api_key and not (provided_api_key or has_configured_api_key):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{provider.display_name} is not selectable until an API key is configured.",
        )

    current_override = _get_provider_override(provider.name)
    selected_model = _normalize_selected_model_for_provider(
        provider.name,
        (request.model or "").strip()
        or str(
            current_override.get("last_model")
            or provider.default_model
            or settings.get_setting("model", "")
        ).strip(),
    )
    if not selected_model:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Model is required"
        )

    normalized_base_url = (
        _normalize_base_url(request.base_url) if request.base_url is not None else None
    )
    runtime_source = None
    if not _supports_base_url_override(provider):
        normalized_base_url = None
    elif provider.name == "ollama":
        runtime_source = _resolve_ollama_runtime_source(
            current_override, normalized_base_url
        )
        if request.runtime_source is not None:
            runtime_source = _normalize_ollama_runtime_source(request.runtime_source)
        normalized_base_url = _base_url_for_ollama_runtime(runtime_source)

    api_key_header = request.api_key_header.strip() if request.api_key_header else None
    api_key_prefix = (
        request.api_key_prefix.strip() if request.api_key_prefix is not None else None
    )
    custom_headers = _sanitize_custom_headers(request.custom_headers or {})

    settings.set_setting("provider", _normalize_provider_id(provider.name), save=False)
    settings.set_setting("model", selected_model, save=False)
    settings.set_setting("last_selected_model", selected_model, save=False)
    settings.set_setting(
        f"model_providers.{provider.name}.last_model", selected_model, save=False
    )

    if normalized_base_url is not None:
        settings.set_setting(
            f"model_providers.{provider.name}.base_url", normalized_base_url, save=False
        )
    if provider.name == "ollama" and runtime_source is not None:
        settings.set_setting(
            f"model_providers.{provider.name}.runtime_source",
            runtime_source,
            save=False,
        )
    elif not _supports_base_url_override(provider):
        provider_overrides = settings.get_setting("model_providers", {}) or {}
        if isinstance(provider_overrides, dict):
            existing_override = provider_overrides.get(provider.name)
            if isinstance(existing_override, dict):
                existing_override.pop("base_url", None)
    if api_key_header is not None:
        settings.set_setting(
            f"model_providers.{provider.name}.api_key_header",
            api_key_header,
            save=False,
        )
    if api_key_prefix is not None:
        settings.set_setting(
            f"model_providers.{provider.name}.api_key_prefix",
            api_key_prefix,
            save=False,
        )
    if request.custom_headers is not None:
        settings.set_setting(
            f"model_providers.{provider.name}.custom_headers",
            custom_headers,
            save=False,
        )

    settings.set_feature_flag(
        "copilot_cloud_enabled",
        provider.provider_type != ProviderType.LOCAL,
        save=False,
    )

    secret_name = _get_secret_name(provider.name, provider)
    api_key = provided_api_key
    if request.clear_api_key and secret_name:
        cleared = secret_manager.delete_secret(secret_name)
        if not cleared:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to clear stored credential for {provider.display_name}.",
            )
        if provider.provider_type != ProviderType.LOCAL:
            secret_manager.delete_secret("COPILOT_API_KEY")
    elif api_key and secret_name:
        stored = secret_manager.set_secret(
            secret_name, api_key, f"{provider.display_name} API key"
        )
        if not stored:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to store API key for {provider.display_name}.",
            )
        if provider.provider_type != ProviderType.LOCAL:
            secret_manager.set_secret(
                "COPILOT_API_KEY",
                api_key,
                f"Active cloud provider key for {provider.display_name}",
            )

    _persist_provider_config(
        provider,
        model=selected_model,
        base_url=normalized_base_url,
        api_key_header=api_key_header,
        api_key_prefix=api_key_prefix,
        custom_headers=custom_headers,
    )
    _refresh_runtime_provider_state(provider.name, selected_model)
    if requires_api_key and (
        provided_api_key or _has_saved_api_key(provider.name, provider)
    ):
        try:
            await asyncio.wait_for(
                asyncio.to_thread(
                    _validate_runtime_provider, provider.name, selected_model
                ),
                timeout=20.0,
            )
        except asyncio.TimeoutError as exc:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"{provider.display_name} validation timed out",
            ) from exc

    settings._save_settings()
    return _build_response()


@router.post("/providers/custom", response_model=ModelSettingsResponse)
async def create_custom_provider(
    request: CustomProviderCreateRequest,
) -> ModelSettingsResponse:
    """Create a persisted custom provider entry that appears in the model settings list."""

    provider_manager = get_provider_config_manager()
    settings = get_settings_manager()

    normalized_name = request.name.strip().lower().replace(" ", "-").replace("_", "-")
    normalized_name = "".join(
        ch for ch in normalized_name if ch.isalnum() or ch == "-"
    ).strip("-")
    if not normalized_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Custom provider name is required",
        )

    if provider_manager.get_provider(normalized_name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A provider with that name already exists",
        )

    model_id = (request.model or "").strip()
    if not model_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A default model is required",
        )

    base_url = _normalize_base_url(request.base_url)
    if not base_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Base URL is required"
        )

    custom_headers = _sanitize_custom_headers(request.custom_headers or {})
    custom_template = provider_manager.get_provider("custom")
    provider = ProviderConfig(
        name=normalized_name,
        display_name=request.display_name.strip() or normalized_name,
        description=(
            request.description
            or f"Custom provider: {request.display_name.strip() or normalized_name}"
        ).strip(),
        provider_type=ProviderType.HYBRID,
        priority=55,
        endpoint=ProviderEndpoint(
            base_url=base_url,
            chat_endpoint="/chat/completions",
            models_endpoint="/models",
        ),
        authentication=ProviderAuthentication(
            type=AuthenticationType.CUSTOM,
            api_key_env_var=f"{normalized_name.upper().replace('-', '_')}_API_KEY",
            api_key_header=(request.api_key_header or "Authorization").strip()
            or "Authorization",
            api_key_prefix=(
                request.api_key_prefix
                if request.api_key_prefix is not None
                else "Bearer"
            ).strip(),
            custom_headers=custom_headers,
        ),
        models=[
            ProviderModel(
                id=model_id,
                name=model_id,
                family=_infer_family(model_id),
                capabilities={"text"},
                supports_streaming=True,
            )
        ],
        default_model=model_id,
        capabilities={"custom_endpoint"},
        limits=custom_template.limits
        if custom_template
        else ProviderLimits(
            concurrent_requests=5,
            max_context_length=32768,
            max_output_tokens=4096,
        ),
    )

    provider_manager.add_provider(provider)
    settings.set_setting("provider", provider.name, save=False)
    settings.set_setting("model", model_id, save=False)
    settings.set_setting("last_selected_model", model_id, save=False)
    settings.set_setting(
        f"model_providers.{provider.name}.last_model", model_id, save=False
    )
    settings.set_setting(
        f"model_providers.{provider.name}.base_url", base_url, save=False
    )
    settings._save_settings()
    return _build_response()


@router.post("/validate", response_model=ProviderSettingsValidationResponse)
async def validate_model_settings_provider(
    request: ProviderSettingsValidationRequest,
) -> ProviderSettingsValidationResponse:
    """Validate a provider configuration using the same catalog/runtime path as settings save."""

    provider_manager = get_provider_config_manager()
    normalized_provider_id = _normalize_provider_id(request.provider)
    provider = provider_manager.get_provider(normalized_provider_id)
    if not provider:
        return ProviderSettingsValidationResponse(
            provider=normalized_provider_id or request.provider,
            valid=False,
            message=f"Provider '{normalized_provider_id or request.provider}' not found",
        )

    requires_api_key = provider.authentication.type in {
        AuthenticationType.API_KEY,
        AuthenticationType.CUSTOM,
    }
    provided_api_key = (request.api_key or "").strip()
    saved_api_key = _get_saved_api_key(provider.name, provider)
    effective_api_key = provided_api_key or saved_api_key

    if requires_api_key and not effective_api_key:
        return ProviderSettingsValidationResponse(
            provider=provider.name,
            valid=False,
            message=f"{provider.display_name} requires an API key.",
        )

    selected_model = _normalize_selected_model_for_provider(
        provider.name,
        (request.model or "").strip()
        or str(
            _get_provider_override(provider.name).get("last_model")
            or provider.default_model
            or ""
        ).strip(),
    )
    if not selected_model:
        return ProviderSettingsValidationResponse(
            provider=provider.name,
            valid=False,
            message="Model is required",
        )

    normalized_base_url = (
        _normalize_base_url(request.base_url) if request.base_url is not None else None
    )
    if not _supports_base_url_override(provider):
        normalized_base_url = None
    elif provider.name == "ollama" and normalized_base_url is not None:
        normalized_base_url = _normalize_ollama_base_url(normalized_base_url)

    if _is_custom_provider(provider) and provider.name != "custom":
        return ProviderSettingsValidationResponse(
            provider=provider.name,
            valid=True,
            message=f"{provider.display_name} saved. Runtime validation is deferred to the provider endpoint.",
        )

    try:
        validation_result = await asyncio.wait_for(
            asyncio.to_thread(
                _validate_runtime_provider_with_details,
                provider.name,
                selected_model,
                effective_api_key,
                normalized_base_url,
            ),
            timeout=30.0,
        )
    except asyncio.TimeoutError:
        return ProviderSettingsValidationResponse(
            provider=provider.name,
            valid=False,
            message=f"{provider.display_name} validation timed out",
        )

    if not validation_result.get("valid"):
        return ProviderSettingsValidationResponse(
            provider=provider.name,
            valid=False,
            message=str(
                validation_result.get("message")
                or f"Failed to initialize {provider.display_name}."
            ),
        )

    return ProviderSettingsValidationResponse(
        provider=provider.name,
        valid=True,
        message=f"{provider.display_name} credentials validated successfully.",
        models_discovered=validation_result.get("models_discovered"),
    )


@router.get("/providers/{provider_id}/models", response_model=ProviderModelsResponse)
async def list_provider_models(
    provider_id: str,
    base_url: Optional[str] = Query(default=None),
) -> ProviderModelsResponse:
    """List discoverable models for a provider, falling back to configured models."""

    provider_manager = get_provider_config_manager()
    normalized_provider_id = _normalize_provider_id(provider_id)
    provider = provider_manager.get_provider(normalized_provider_id)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found"
        )

    override = _get_provider_override(provider.name)
    if base_url is not None:
        override["base_url"] = base_url

    try:
        # Discovery can perform blocking network I/O (urllib). Keep it off the event loop
        # and bound response time so auth/session endpoints are not starved.
        models = await asyncio.wait_for(
            asyncio.to_thread(_load_provider_models, provider, override),
            timeout=12.0,
        )
    except HTTPError as exc:
        detail = (
            exc.read().decode("utf-8", errors="ignore")
            if hasattr(exc, "read")
            else str(exc)
        )
        raise HTTPException(
            status_code=exc.code,
            detail=detail or f"Unable to query {provider.name} models",
        ) from exc
    except URLError as exc:
        # For Ollama, network errors are critical since we expect it to be local
        if provider.name == "ollama":
            resolved_base_url = _resolve_provider_base_url(provider, override)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Unable to reach {provider.display_name} at {resolved_base_url}",
            ) from exc
        # For remote providers, network errors are expected - fall back to configured models
        logger.debug(
            "Network error for %s, falling back to configured models: %s",
            provider.name,
            exc,
        )
        models = _configured_models(provider)
    except Exception as exc:
        logger.warning("Model discovery fallback for %s: %s", provider_id, exc)
        if provider.name == "ollama":
            resolved_base_url = _resolve_provider_base_url(provider, override)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Unable to reach {provider.display_name} at {resolved_base_url}",
            ) from exc
        # For all other providers, fall back to configured models
        models = _configured_models(provider)

    selected_model = _normalize_selected_model_for_provider(
        provider.name,
        _get_provider_override(provider.name).get("last_model"),
    )
    if selected_model and all(model.id != selected_model for model in models):
        models.append(
            _make_model_payload(
                selected_model,
                name=selected_model,
                family=_infer_family(selected_model),
                source="saved",
            )
        )

    resolved_base_url = _resolve_provider_base_url(provider, override)
    return ProviderModelsResponse(
        provider=provider.name,
        base_url=resolved_base_url or None,
        models=models,
        discovered_at=_utc_now(),
    )


@router.post("/providers/ollama/pull")
async def pull_ollama_model(
    request: OllamaPullRequest,
    current_user=Depends(get_current_user),
) -> Dict[str, Any]:
    """Trigger a blocking Ollama model pull using the configured or supplied base URL."""

    model_name = request.model.strip()
    if not model_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Model name is required"
        )

    provider_manager = get_provider_config_manager()
    provider = provider_manager.get_provider("ollama")
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ollama provider is not configured",
        )

    override = _get_provider_override("ollama")
    if request.base_url is not None:
        override["base_url"] = request.base_url
    configured_base_url = _resolve_provider_base_url(provider, override)

    payload: Dict[str, Any] | List[Any] | Any = {}
    last_error: Optional[Exception] = None
    used_base_url = configured_base_url
    for candidate in _iter_ollama_base_urls(configured_base_url):
        try:
            payload = _fetch_json(
                f"{candidate}/pull",
                method="POST",
                payload={"name": model_name, "stream": False},
                timeout=600.0,
            )
            used_base_url = candidate
            break
        except Exception as exc:
            last_error = exc
    else:
        if isinstance(last_error, HTTPError):
            detail = (
                last_error.read().decode("utf-8", errors="ignore")
                if hasattr(last_error, "read")
                else str(last_error)
            )
            raise HTTPException(
                status_code=last_error.code, detail=detail or "Ollama pull failed"
            ) from last_error
        if isinstance(last_error, URLError):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Unable to reach Ollama at {configured_base_url}",
            ) from last_error
        if last_error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ollama pull failed: {last_error}",
            ) from last_error

    return {
        "provider": "ollama",
        "base_url": used_base_url,
        "model": model_name,
        "status": "completed",
        "result": payload,
        "completed_at": _utc_now(),
    }
