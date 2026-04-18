"""
Prompt API Routes - Backend endpoints for prompt-first plugin system.

Provides API endpoints for:
- Getting prompt templates from plugins
- Rendering prompts with context variables
- Validating prompt templates
- Getting variable information
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ai_karen_engine.extensions.platform.core.host.prompt_renderer import (
    get_prompt_renderer,
    PromptTemplateError,
    PromptRenderError,
    PromptVariableError,
)
from ai_karen_engine.extensions.platform.core.host.loader import ExtensionLoader
from ai_karen_engine.extensions.platform.core.manifest import ExtensionManifest


router = APIRouter(prefix="/api/plugins", tags=["prompts"])


# Request/Response Models
class PromptContext(BaseModel):
    """Context variables for prompt rendering."""

    variables: Dict[str, Any] = Field(default_factory=dict)
    query: Optional[str] = None
    user_id: Optional[str] = None
    user_role: Optional[str] = None
    tenant_id: Optional[str] = None


class PromptRenderRequest(BaseModel):
    """Request to render a prompt template."""

    context: PromptContext


class PromptValidationRequest(BaseModel):
    """Request to validate a prompt template."""

    template_name: str


class PromptTemplateResponse(BaseModel):
    """Response containing prompt template information."""

    template_name: str
    content: str
    variables: List[str]
    required_variables: List[str]


class PromptRenderResponse(BaseModel):
    """Response containing rendered prompt."""

    template_name: str
    rendered_prompt: str
    variables_used: List[str]


class PromptValidationResponse(BaseModel):
    """Response containing validation results."""

    template_name: str
    is_valid: bool
    errors: List[str]


class PluginPromptsResponse(BaseModel):
    """Response containing all prompts for a plugin."""

    plugin_name: str
    plugin_version: str
    templates: Dict[str, PromptTemplateResponse]


# Helper Functions
def _get_plugin_manifest(plugin_id: str) -> Optional[ExtensionManifest]:
    """
    Get plugin manifest by ID.

    Args:
        plugin_id: Plugin identifier

    Returns:
        ExtensionManifest or None if not found
    """
    try:
        loader = ExtensionLoader()
        return loader.load_manifest(plugin_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin '{plugin_id}' not found: {e}",
        )


def _ensure_prompt_files_loaded(plugin_id: str, manifest: ExtensionManifest) -> None:
    """
    Ensure prompt templates are loaded for a plugin.

    Args:
        plugin_id: Plugin identifier
        manifest: Plugin manifest
    """
    renderer = get_prompt_renderer()
    if not manifest.prompt_files:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin '{plugin_id}' does not define prompt_files in manifest",
        )

    # Try to load prompts (renderer will cache them)
    try:
        renderer.load_prompt_from_manifest(manifest)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load prompts for plugin '{plugin_id}': {e}",
        )


# API Endpoints
@router.get("/{plugin_id}/prompt", response_model=PluginPromptsResponse)
async def get_plugin_prompts(plugin_id: str) -> PluginPromptsResponse:
    """
    Get all prompt templates for a plugin.

    Args:
        plugin_id: Plugin identifier

    Returns:
        Dictionary of all prompt templates for the plugin
    """
    # Get plugin manifest
    manifest = _get_plugin_manifest(plugin_id)

    # Ensure prompts are loaded
    _ensure_prompt_files_loaded(plugin_id, manifest)

    # Get all prompts
    renderer = get_prompt_renderer()
    templates_data = renderer.get_extension_prompts(plugin_id)

    # Build response with metadata
    templates_response = {}
    for template_name, content in templates_data.items():
        variables = renderer.get_template_variables(plugin_id, template_name)
        # Get required variables from config if available
        required_vars = []
        if manifest.prompt_files and manifest.prompt_files.templates_config:
            config = manifest.prompt_files.templates_config.get(template_name)
            if config:
                required_vars = config.required_variables

        templates_response[template_name] = PromptTemplateResponse(
            template_name=template_name,
            content=content,
            variables=variables,
            required_variables=required_vars,
        )

    return PluginPromptsResponse(
        plugin_name=manifest.name,
        plugin_version=manifest.version,
        templates=templates_response,
    )


@router.get(
    "/{plugin_id}/prompt/{template_name}", response_model=PromptTemplateResponse
)
async def get_plugin_prompt(
    plugin_id: str, template_name: str
) -> PromptTemplateResponse:
    """
    Get a specific prompt template for a plugin.

    Args:
        plugin_id: Plugin identifier
        template_name: Name of the template (e.g., "system", "user")

    Returns:
        Prompt template information

    Raises:
        404: Plugin or template not found
    """
    # Get plugin manifest
    manifest = _get_plugin_manifest(plugin_id)

    # Ensure prompts are loaded
    _ensure_prompt_files_loaded(plugin_id, manifest)

    # Get specific prompt
    renderer = get_prompt_renderer()
    prompts = renderer.get_extension_prompts(plugin_id)

    if template_name not in prompts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{template_name}' not found for plugin '{plugin_id}'. "
            f"Available templates: {list(prompts.keys())}",
        )

    content = prompts[template_name]
    variables = renderer.get_template_variables(plugin_id, template_name)

    # Get required variables from config if available
    required_vars = []
    if manifest.prompt_files and manifest.prompt_files.templates_config:
        config = manifest.prompt_files.templates_config.get(template_name)
        if config:
            required_vars = config.required_variables

    return PromptTemplateResponse(
        template_name=template_name,
        content=content,
        variables=variables,
        required_variables=required_vars,
    )


@router.post(
    "/{plugin_id}/prompt/{template_name}/render", response_model=PromptRenderResponse
)
async def render_prompt(
    plugin_id: str,
    template_name: str,
    request: PromptRenderRequest,
) -> PromptRenderResponse:
    """
    Render a prompt template with context variables.

    Args:
        plugin_id: Plugin identifier
        template_name: Name of the template
        request: Rendering context and variables

    Returns:
        Rendered prompt string

    Raises:
        404: Plugin or template not found
        400: Invalid context (missing required variables)
    """
    # Get plugin manifest
    manifest = _get_plugin_manifest(plugin_id)

    # Ensure prompts are loaded
    _ensure_prompt_files_loaded(plugin_id, manifest)

    # Build full context from request
    full_context = request.context.dict()
    # Add plugin metadata to context
    full_context.update(
        {
            "plugin_name": manifest.name,
            "plugin_version": manifest.version,
        }
    )

    # Render the prompt
    renderer = get_prompt_renderer()
    try:
        rendered = renderer.render_prompt(plugin_id, template_name, full_context)
    except PromptVariableError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PromptRenderError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to render prompt: {e}",
        )

    # Get variables used
    variables = renderer.get_template_variables(plugin_id, template_name)

    return PromptRenderResponse(
        template_name=template_name,
        rendered_prompt=rendered,
        variables_used=variables,
    )


@router.get("/{plugin_id}/prompt/{template_name}/variables")
async def get_prompt_variables(plugin_id: str, template_name: str) -> Dict[str, Any]:
    """
    Get variables referenced in a prompt template.

    Args:
        plugin_id: Plugin identifier
        template_name: Name of the template

    Returns:
        Dictionary with variable information
    """
    # Get plugin manifest
    manifest = _get_plugin_manifest(plugin_id)

    # Ensure prompts are loaded
    _ensure_prompt_files_loaded(plugin_id, manifest)

    # Get variables
    renderer = get_prompt_renderer()
    variables = renderer.get_template_variables(plugin_id, template_name)

    # Get required variables from config if available
    required_vars = []
    if manifest.prompt_files and manifest.prompt_files.templates_config:
        config = manifest.prompt_files.templates_config.get(template_name)
        if config:
            required_vars = config.required_variables

    return {
        "plugin_id": plugin_id,
        "template_name": template_name,
        "variables": variables,
        "required_variables": required_vars,
        "total_variables": len(variables),
        "required_count": len(required_vars),
    }


@router.post(
    "/{plugin_id}/prompt/validate", response_model=List[PromptValidationResponse]
)
async def validate_prompts(
    plugin_id: str,
    request: Optional[PromptValidationRequest] = None,
) -> List[PromptValidationResponse]:
    """
    Validate prompt templates for a plugin.

    Args:
        plugin_id: Plugin identifier
        request: Optional template name to validate. If not provided, validates all templates.

    Returns:
        List of validation results for each template
    """
    # Get plugin manifest
    manifest = _get_plugin_manifest(plugin_id)

    # Ensure prompts are loaded
    _ensure_prompt_files_loaded(plugin_id, manifest)

    # Get prompts to validate
    renderer = get_prompt_renderer()
    prompts = renderer.get_extension_prompts(plugin_id)

    templates_to_validate = []
    if request and request.template_name:
        if request.template_name not in prompts:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template '{request.template_name}' not found for plugin '{plugin_id}'",
            )
        templates_to_validate = [request.template_name]
    else:
        templates_to_validate = list(prompts.keys())

    # Validate each template
    results = []
    for template_name in templates_to_validate:
        errors = renderer.validate_template(plugin_id, template_name)
        is_valid = len(errors) == 0
        results.append(
            PromptValidationResponse(
                template_name=template_name,
                is_valid=is_valid,
                errors=errors,
            )
        )

    return results


@router.post("/{plugin_id}/prompt/reload")
async def reload_prompts(plugin_id: str) -> Dict[str, Any]:
    """
    Reload prompt templates for a plugin from disk.

    Clears cache and reloads all prompt templates.

    Args:
        plugin_id: Plugin identifier

    Returns:
        Reload status
    """
    # Get plugin manifest
    manifest = _get_plugin_manifest(plugin_id)

    if not manifest.prompt_files:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin '{plugin_id}' does not define prompt_files in manifest",
        )

    # Clear cache for this plugin
    renderer = get_prompt_renderer()
    renderer.clear_cache(plugin_id)

    # Reload prompts
    try:
        loaded = renderer.load_prompt_from_manifest(manifest)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reload prompts: {e}",
        )

    return {
        "plugin_id": plugin_id,
        "reloaded": True,
        "templates_count": len(loaded),
        "message": f"Successfully reloaded {len(loaded)} prompt templates",
    }


__all__ = ["router"]
