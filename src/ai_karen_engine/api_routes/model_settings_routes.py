"""
Production model settings API routes.

These routes back the Karen AI theme "Model" settings tab with persisted
provider selection, encrypted API key storage, and local model discovery.
"""

from __future__ import annotations

import json
import logging
import os
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
    ProviderAuthentication,
    ProviderConfig,
    ProviderEndpoint,
    ProviderModel,
    ProviderType,
    get_provider_config_manager,
)
from ai_karen_engine.config.model_registry import list_llama_cpp_models
from services.memory.settings_manager import get_settings_manager
from services.models.secret_manager import get_secret_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings/model", tags=["model-settings"])
DEFAULT_OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/api")

LEADING_PROVIDER_ORDER = [
    "openai",
    "gemini",
    "anthropic",
    "deepseek",
    "mistral",
    "groq",
    "xai",
    "qwen",
    "zai",
    "huggingface",
    "ollama",
    "llama-cpp",
    "custom",
]

PROVIDER_DOC_URLS = {
    "openai": "https://platform.openai.com/docs",
    "gemini": "https://ai.google.dev/gemini-api/docs",
    "anthropic": "https://docs.anthropic.com/en/api/messages",
    "deepseek": "https://api-docs.deepseek.com/",
    "mistral": "https://docs.mistral.ai/",
    "groq": "https://console.groq.com/docs/overview",
    "xai": "https://docs.x.ai/docs/overview",
    "qwen": "https://www.alibabacloud.com/help/en/model-studio/developer-reference/compatibility-of-openai-with-dashscope",
    "zai": "https://docs.z.ai/api-reference/introduction",
    "huggingface": "https://huggingface.co/docs/api-inference/index",
    "ollama": "https://github.com/ollama/ollama/blob/main/docs/api.md",
    "llama-cpp": "https://github.com/ggml-org/llama.cpp/tree/master/examples/server",
}

SECRET_NAMES = {
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "groq": "GROQ_API_KEY",
    "xai": "XAI_API_KEY",
    "qwen": "QWEN_API_KEY",
    "zai": "ZAI_API_KEY",
    "huggingface": "HUGGINGFACE_API_KEY",
    "custom": "CUSTOM_LLM_API_KEY",
}


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
    api_key_header: str = "Authorization"
    api_key_prefix: str = "Bearer"
    custom_headers: Dict[str, str] = Field(default_factory=dict)
    supports_base_url_override: bool = True
    supports_model_discovery: bool = False
    supports_model_pull: bool = False
    supports_custom_auth: bool = False
    supports_manual_model_entry: bool = False


class ModelSettingsResponse(BaseModel):
    selected_provider: str
    selected_model: str
    providers: List[ProviderPayload]
    updated_at: str


class ModelSettingsUpdateRequest(BaseModel):
    provider: str
    model: Optional[str] = None
    base_url: Optional[str] = None
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


class OllamaPullRequest(BaseModel):
    model: str
    base_url: Optional[str] = None


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _provider_sort_key(provider: ProviderConfig) -> tuple[int, int, str]:
    try:
        order = LEADING_PROVIDER_ORDER.index(provider.name)
    except ValueError:
        order = len(LEADING_PROVIDER_ORDER)
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


def _iter_ollama_base_urls(base_url: Optional[str]) -> List[str]:
    normalized = _normalize_ollama_base_url(base_url)
    parsed = urlparse(normalized)
    hostname = parsed.hostname or ""

    candidates = [normalized]
    if hostname in {"localhost", "127.0.0.1", "::1"}:
        for alias in ("host.docker.internal", "172.17.0.1"):
            alias_netloc = alias
            if parsed.port:
                alias_netloc = f"{alias}:{parsed.port}"
            aliased = urlunparse(parsed._replace(netloc=alias_netloc))
            if aliased not in candidates:
                candidates.append(aliased)

    return candidates


def _resolve_provider_base_url(provider: ProviderConfig, override: Dict[str, Any]) -> str:
    saved = _normalize_base_url(override.get("base_url"))
    fallback = _normalize_base_url(provider.endpoint.base_url if provider.endpoint else None) or ""
    resolved = saved if saved is not None else fallback
    if provider.name == "ollama":
        return _normalize_ollama_base_url(resolved)
    return resolved


def _build_auth_headers(provider_id: str, provider: ProviderConfig, api_key: Optional[str]) -> Dict[str, str]:
    headers = dict(provider.authentication.custom_headers or {})
    if api_key and provider.authentication.type in {AuthenticationType.API_KEY, AuthenticationType.CUSTOM}:
        prefix = (provider.authentication.api_key_prefix or "").strip()
        token = f"{prefix} {api_key}".strip() if prefix else api_key
        headers[provider.authentication.api_key_header or "Authorization"] = token
    return headers


def _model_to_payload(model: ProviderModel, source: str = "configured") -> ProviderModelPayload:
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
        raw_items = payload.get("data") or payload.get("models") or payload.get("items") or []
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

        model_id = str(item.get("id") or item.get("name") or item.get("model") or "").strip()
        if not model_id or model_id in seen:
            continue
        seen.add(model_id)

        modalities = item.get("modalities") or item.get("supported_modalities") or []
        supports_vision = False
        if isinstance(modalities, list):
            supports_vision = any("image" in str(modality).lower() for modality in modalities)

        capabilities = []
        if supports_vision:
            capabilities.append("vision")
        if item.get("supports_tools") or item.get("tool_use") or item.get("function_calling"):
            capabilities.append("tool_use")

        context_length = item.get("context_length") or item.get("context_window") or item.get("max_input_tokens")
        max_tokens = item.get("max_output_tokens") or item.get("max_tokens")

        models.append(
            _make_model_payload(
                model_id,
                name=str(item.get("display_name") or item.get("name") or model_id),
                family=_infer_family(model_id),
                context_length=int(context_length) if isinstance(context_length, int) else None,
                max_tokens=int(max_tokens) if isinstance(max_tokens, int) else None,
                capabilities=capabilities,
                supports_functions="tool_use" in capabilities,
                supports_vision=supports_vision,
            )
        )

    return models


def _discover_remote_models(provider: ProviderConfig, override: Dict[str, Any]) -> List[ProviderModelPayload]:
    if not provider.endpoint or not provider.endpoint.models_endpoint:
        return []

    api_key = _get_saved_api_key(provider.name, provider)
    if provider.authentication.type in {AuthenticationType.API_KEY, AuthenticationType.CUSTOM} and not api_key:
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
        logger.warning("Unexpected remote model discovery error for %s: %s", provider.name, exc)
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


def _discover_llama_cpp_models(base_url: Optional[str]) -> List[ProviderModelPayload]:
    models: List[ProviderModelPayload] = []
    seen: set[str] = set()

    for model_name in list_llama_cpp_models():
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
        remote_url = normalized_base if normalized_base.endswith("/models") else f"{normalized_base}/models"
        try:
            payload = _fetch_json(remote_url, timeout=6.0)
            for model in _extract_models_from_payload(payload):
                if model.id in seen:
                    continue
                seen.add(model.id)
                models.append(model)
        except Exception as exc:  # pragma: no cover - local service optional
            logger.debug("llama.cpp server discovery skipped: %s", exc)

    return models


def _configured_models(provider: ProviderConfig) -> List[ProviderModelPayload]:
    return [_model_to_payload(model) for model in provider.models]


def _load_provider_models(provider: ProviderConfig, override: Dict[str, Any]) -> List[ProviderModelPayload]:
    if provider.name == "ollama":
        return _discover_ollama_models(_resolve_provider_base_url(provider, override))

    if provider.name == "llama-cpp":
        discovered = _discover_llama_cpp_models(_resolve_provider_base_url(provider, override))
        return discovered or _configured_models(provider)

    discovered = _discover_remote_models(provider, override)
    return discovered or _configured_models(provider)


def _build_provider_payload(provider: ProviderConfig, selected_provider: str, selected_model: str) -> ProviderPayload:
    override = _get_provider_override(provider.name)
    base_url = _resolve_provider_base_url(provider, override)
    configured_models = _configured_models(provider)
    last_model = override.get("last_model") or provider.default_model or ""
    provider_selected_model = selected_model if provider.name == selected_provider else last_model

    if provider_selected_model and all(model.id != provider_selected_model for model in configured_models):
        configured_models.append(
            _make_model_payload(
                provider_selected_model,
                name=provider_selected_model,
                family=_infer_family(provider_selected_model),
                source="saved",
            )
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
        models=configured_models,
        requires_api_key=provider.authentication.type in {AuthenticationType.API_KEY, AuthenticationType.CUSTOM},
        api_key_configured=_has_saved_api_key(provider.name, provider),
        api_key_header=str(override.get("api_key_header") or provider.authentication.api_key_header or "Authorization"),
        api_key_prefix=str(
            override.get("api_key_prefix")
            if override.get("api_key_prefix") is not None
            else (provider.authentication.api_key_prefix or "")
        ),
        custom_headers=_sanitize_custom_headers(override.get("custom_headers") or provider.authentication.custom_headers or {}),
        supports_base_url_override=True,
        supports_model_discovery=provider.name in {"ollama", "llama-cpp"} or bool(provider.endpoint and provider.endpoint.models_endpoint),
        supports_model_pull=provider.name == "ollama",
        supports_custom_auth=provider.name == "custom",
        supports_manual_model_entry=provider.name in {"custom", "ollama", "llama-cpp"},
    )


def _build_response() -> ModelSettingsResponse:
    settings = get_settings_manager()
    provider_manager = get_provider_config_manager()
    selected_provider = str(settings.get_setting("provider", "ollama") or "ollama")
    selected_model = str(settings.get_setting("model", "") or "")

    providers: List[ProviderPayload] = []
    for provider in sorted(provider_manager.list_providers(), key=_provider_sort_key):
        if provider.name not in LEADING_PROVIDER_ORDER:
            continue
        try:
            providers.append(_build_provider_payload(provider, selected_provider, selected_model))
        except Exception as exc:  # pragma: no cover - defensive response hardening
            logger.exception("Skipping invalid model-settings provider payload for %s: %s", provider.name, exc)

    valid_provider_ids = {provider.id for provider in providers}
    if providers and selected_provider not in valid_provider_ids:
        selected_provider = next((provider.id for provider in providers if provider.id == "ollama"), providers[0].id)
    if not selected_model and providers:
        active = next((provider for provider in providers if provider.id == selected_provider), providers[0])
        selected_model = active.selected_model or active.default_model or ""

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
        api_key_header=api_key_header if api_key_header is not None else authentication.api_key_header,
        api_key_prefix=api_key_prefix if api_key_prefix is not None else authentication.api_key_prefix,
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


@router.get("", response_model=ModelSettingsResponse)
async def get_model_settings() -> ModelSettingsResponse:
    """Return persisted provider/model settings plus provider metadata."""

    return _build_response()


@router.put("", response_model=ModelSettingsResponse)
async def update_model_settings(
    request: ModelSettingsUpdateRequest,
) -> ModelSettingsResponse:
    """Persist the selected provider/model and provider-specific auth settings."""

    provider_manager = get_provider_config_manager()
    settings = get_settings_manager()
    secret_manager = get_secret_manager()

    provider = provider_manager.get_provider(request.provider)
    if not provider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")

    current_override = _get_provider_override(provider.name)
    selected_model = (
        (request.model or "").strip()
        or str(current_override.get("last_model") or provider.default_model or settings.get_setting("model", "")).strip()
    )
    if not selected_model:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Model is required")

    normalized_base_url = _normalize_base_url(request.base_url) if request.base_url is not None else None
    if provider.name == "ollama" and normalized_base_url is not None:
        normalized_base_url = _normalize_ollama_base_url(normalized_base_url)

    api_key_header = request.api_key_header.strip() if request.api_key_header else None
    api_key_prefix = request.api_key_prefix.strip() if request.api_key_prefix is not None else None
    custom_headers = _sanitize_custom_headers(request.custom_headers or {})

    settings.set_setting("provider", provider.name, save=False)
    settings.set_setting("model", selected_model, save=False)
    settings.set_setting(f"model_providers.{provider.name}.last_model", selected_model, save=False)

    if normalized_base_url is not None:
        settings.set_setting(f"model_providers.{provider.name}.base_url", normalized_base_url, save=False)
    if api_key_header is not None:
        settings.set_setting(f"model_providers.{provider.name}.api_key_header", api_key_header, save=False)
    if api_key_prefix is not None:
        settings.set_setting(f"model_providers.{provider.name}.api_key_prefix", api_key_prefix, save=False)
    if request.custom_headers is not None:
        settings.set_setting(f"model_providers.{provider.name}.custom_headers", custom_headers, save=False)

    settings.set_feature_flag(
        "copilot_cloud_enabled",
        provider.provider_type != ProviderType.LOCAL,
        save=False,
    )

    secret_name = _get_secret_name(provider.name, provider)
    api_key = (request.api_key or "").strip()
    if request.clear_api_key and secret_name:
        secret_manager.delete_secret(secret_name)
        if provider.provider_type != ProviderType.LOCAL:
            secret_manager.delete_secret("COPILOT_API_KEY")
    elif api_key and secret_name:
        secret_manager.set_secret(secret_name, api_key, f"{provider.display_name} API key")
        if provider.provider_type != ProviderType.LOCAL:
            secret_manager.set_secret("COPILOT_API_KEY", api_key, f"Active cloud provider key for {provider.display_name}")

    _persist_provider_config(
        provider,
        model=selected_model,
        base_url=normalized_base_url,
        api_key_header=api_key_header,
        api_key_prefix=api_key_prefix,
        custom_headers=custom_headers,
    )

    settings._save_settings()
    return _build_response()


@router.get("/providers/{provider_id}/models", response_model=ProviderModelsResponse)
async def list_provider_models(
    provider_id: str,
    base_url: Optional[str] = Query(default=None),
) -> ProviderModelsResponse:
    """List discoverable models for a provider, falling back to configured models."""

    provider_manager = get_provider_config_manager()
    provider = provider_manager.get_provider(provider_id)
    if not provider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")

    override = _get_provider_override(provider_id)
    if base_url is not None:
        override["base_url"] = base_url

    try:
        models = _load_provider_models(provider, override)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore") if hasattr(exc, "read") else str(exc)
        raise HTTPException(status_code=exc.code, detail=detail or f"Unable to query {provider_id} models") from exc
    except URLError as exc:
        resolved_base_url = _resolve_provider_base_url(provider, override)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Unable to reach {provider.display_name} at {resolved_base_url}",
        ) from exc
    except Exception as exc:
        if provider.name == "ollama":
            resolved_base_url = _resolve_provider_base_url(provider, override)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Unable to reach {provider.display_name} at {resolved_base_url}",
            ) from exc
        models = _configured_models(provider)

    selected_model = _get_provider_override(provider_id).get("last_model")
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
        provider=provider_id,
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Model name is required")

    provider_manager = get_provider_config_manager()
    provider = provider_manager.get_provider("ollama")
    if not provider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ollama provider is not configured")

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
            detail = last_error.read().decode("utf-8", errors="ignore") if hasattr(last_error, "read") else str(last_error)
            raise HTTPException(status_code=last_error.code, detail=detail or "Ollama pull failed") from last_error
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
