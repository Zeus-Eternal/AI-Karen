"""
Prompt Template System - Jinja2 rendering engine for prompt-first plugins.

This module provides:
- Prompt template specification and validation
- Jinja2 rendering with variable substitution
- Support for system and user prompts
- Template caching and management
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from jinja2 import (
    Environment,
    Template,
    TemplateSyntaxError,
    TemplateError,
    StrictUndefined,
    pass_context,
    meta,
)

from ai_karen_engine.extensions.platform.core.manifest import PromptTemplateConfig, ExtensionManifest


logger = logging.getLogger(__name__)


class PromptTemplateError(Exception):
    """Error in prompt template."""

    pass


class PromptVariableError(PromptTemplateError):
    """Error with prompt variable."""

    pass


class PromptRenderError(PromptTemplateError):
    """Error rendering prompt."""

    pass


class PromptTemplate:
    """
    Represents a prompt template with Jinja2 support.

    Supports:
    - Variable substitution: {{ variable_name }}
    - Conditionals: {% if variable_name %}...{% endif %}
    - Loops: {% for item in items %}...{% endfor %}
    - Filters: {{ variable|upper }}
    - Comments: {# comment #}
    """

    def __init__(
        self,
        template_name: str,
        template_content: str,
        config: Optional[PromptTemplateConfig] = None,
    ):
        """
        Initialize a prompt template.

        Args:
            template_name: Name of the template
            template_content: Jinja2 template content
            config: Optional template configuration with variable definitions
        """
        self.template_name = template_name
        self.raw_content = template_content
        self.config = config or PromptTemplateConfig()
        self._template: Optional[Template] = None
        self._compiled = False

    def compile(self) -> None:
        """
        Compile the Jinja2 template.

        Raises:
            PromptTemplateError: If template syntax is invalid
        """
        try:
            env = self._create_jinja2_environment()
            self._template = env.from_string(self.raw_content)
            self._compiled = True
            logger.debug(f"Compiled prompt template: {self.template_name}")
        except TemplateSyntaxError as e:
            raise PromptTemplateError(
                f"Syntax error in template '{self.template_name}': {e}"
            ) from e
        except Exception as e:
            raise PromptTemplateError(
                f"Failed to compile template '{self.template_name}': {e}"
            ) from e

    def _create_jinja2_environment(self) -> Environment:
        """
        Create a Jinja2 environment with custom configuration.

        Returns:
            Configured Jinja2 Environment
        """
        env = Environment(
            undefined=StrictUndefined,  # Raise error for undefined variables
            trim_blocks=True,  # Remove newline after control blocks
            lstrip_blocks=True,  # Strip whitespace before control blocks
            autoescape=False,  # Don't auto-escape (prompts are plain text)
        )

        # Add custom filters
        env.filters["to_list"] = self._to_list_filter
        env.filters["default_if_empty"] = self._default_if_empty_filter
        env.filters["truncate_words"] = self._truncate_words_filter

        return env

    @staticmethod
    def _to_list_filter(value: Any) -> List[Any]:
        """Convert value to list."""
        if isinstance(value, list):
            return value
        elif isinstance(value, (str, int, float)):
            return [value]
        else:
            try:
                return list(value)
            except Exception:
                return []

    @staticmethod
    def _default_if_empty_filter(value: Any, default: Any = "") -> Any:
        """Return default if value is empty or None."""
        if value is None or (isinstance(value, str) and not value.strip()):
            return default
        return value

    @staticmethod
    def _truncate_words_filter(value: str, max_words: int = 50) -> str:
        """Truncate text to max_words words."""
        words = str(value).split()
        if len(words) <= max_words:
            return " ".join(words)
        return " ".join(words[:max_words]) + "..."

    def render(self, context: Dict[str, Any]) -> str:
        """
        Render the template with given context.

        Args:
            context: Dictionary of variables to substitute into template

        Returns:
            Rendered prompt string

        Raises:
            PromptRenderError: If rendering fails
        """
        if not self._compiled:
            self.compile()

        if not self._template:
            raise PromptRenderError("Template not compiled")

        try:
            # Validate that all required variables are provided
            self._validate_required_variables(context)

            # Render the template
            rendered = self._template.render(**context)
            logger.debug(f"Rendered template '{self.template_name}' successfully")
            return rendered

        except TemplateError as e:
            raise PromptRenderError(
                f"Error rendering template '{self.template_name}': {e}"
            ) from e
        except Exception as e:
            raise PromptRenderError(
                f"Unexpected error rendering template '{self.template_name}': {e}"
            ) from e

    def _validate_required_variables(self, context: Dict[str, Any]) -> None:
        """
        Validate that all required variables are in context.

        Args:
            context: Variables provided for rendering

        Raises:
            PromptVariableError: If required variables are missing
        """
        # Extract variable names from template
        if not self._template:
            return

        try:
            variables = meta.find_undeclared_variables(self._template)
        except Exception:
            # If we can't extract variables, skip validation
            return

        # Check for missing required variables
        missing_vars = set(self.config.required_variables) - set(context.keys())

        if missing_vars:
            raise PromptVariableError(
                f"Missing required variables for template '{self.template_name}': {missing_vars}. "
                f"Required: {self.config.required_variables}, Provided: {list(context.keys())}"
            )

    def get_variables(self) -> List[str]:
        """
        Get all variables referenced in the template.

        Returns:
            List of variable names
        """
        if not self._template:
            self.compile()

        try:
            return list(meta.find_undeclared_variables(self._template))
        except Exception:
            # Fallback to config if extraction fails
            return self.config.variables.copy()

    def validate(self) -> List[str]:
        """
        Validate the template and return any issues.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        try:
            # Try to compile
            self.compile()
        except PromptTemplateError as e:
            errors.append(str(e))
            return errors

        # Check for required variables
        variables = self.get_variables()
        for var in self.config.required_variables:
            if var not in variables:
                errors.append(f"Required variable '{var}' not referenced in template")

        return errors


class PromptRenderer:
    """
    Manages and renders prompt templates for extensions.

    Provides:
    - Template discovery and loading
    - Template caching
    - Variable validation
    - Context management
    """

    def __init__(self, extensions_dir: str = "src/ai_karen_engine/extensions/plugins"):
        """
        Initialize the prompt renderer.

        Args:
            extensions_dir: Path to extensions directory
        """
        self.extensions_dir = Path(extensions_dir)
        self._templates: Dict[str, PromptTemplate] = {}
        self._manifests: Dict[str, ExtensionManifest] = {}
        logger.info(
            f"PromptRenderer initialized with extensions_dir={self.extensions_dir}"
        )

    def load_prompt_from_manifest(
        self, manifest: ExtensionManifest
    ) -> Dict[str, PromptTemplate]:
        """
        Load all prompt templates from an extension manifest.

        Args:
            manifest: Extension manifest with prompt file configuration

        Returns:
            Dictionary of template_name -> PromptTemplate
        """
        templates = {}

        if not manifest.prompt_files:
            logger.debug(f"Extension {manifest.name} has no prompt_files")
            return templates

        # Load system prompt
        if manifest.prompt_files.system:
            try:
                system_template = self._load_prompt_file(
                    self.extensions_dir / manifest.name / manifest.prompt_files.system,
                    "system",
                    manifest.prompt_files.templates_config.get("system"),
                )
                if system_template:
                    templates["system"] = system_template
            except Exception as e:
                logger.warning(f"Failed to load system prompt for {manifest.name}: {e}")

        # Load user prompt
        if manifest.prompt_files.user:
            try:
                user_template = self._load_prompt_file(
                    self.extensions_dir / manifest.name / manifest.prompt_files.user,
                    "user",
                    manifest.prompt_files.templates_config.get("user"),
                )
                if user_template:
                    templates["user"] = user_template
            except Exception as e:
                logger.warning(f"Failed to load user prompt for {manifest.name}: {e}")

        # Load additional templates
        for template_name, template_path in manifest.prompt_files.templates.items():
            try:
                template = self._load_prompt_file(
                    self.extensions_dir / manifest.name / template_path,
                    template_name,
                    manifest.prompt_files.templates_config.get(template_name),
                )
                if template:
                    templates[template_name] = template
            except Exception as e:
                logger.warning(
                    f"Failed to load template '{template_name}' for {manifest.name}: {e}"
                )

        # Cache templates
        for name, template in templates.items():
            cache_key = f"{manifest.name}.{name}"
            self._templates[cache_key] = template

        logger.info(f"Loaded {len(templates)} prompt templates for {manifest.name}")
        return templates

    def _load_prompt_file(
        self,
        template_path: Path,
        template_name: str,
        config: Optional[PromptTemplateConfig] = None,
    ) -> Optional[PromptTemplate]:
        """
        Load a single prompt template file.

        Args:
            template_path: Path to the template file
            template_name: Name for the template
            config: Optional template configuration

        Returns:
            PromptTemplate or None if file doesn't exist
        """
        if not template_path.exists():
            logger.debug(f"Template file not found: {template_path}")
            return None

        try:
            content = template_path.read_text(encoding="utf-8")
            template = PromptTemplate(template_name, content, config)
            template.compile()
            return template
        except Exception as e:
            raise PromptTemplateError(
                f"Failed to load template file {template_path}: {e}"
            ) from e

    def render_prompt(
        self,
        extension_name: str,
        template_name: str,
        context: Dict[str, Any],
    ) -> str:
        """
        Render a specific prompt template for an extension.

        Args:
            extension_name: Name of the extension
            template_name: Name of the template (e.g., "system", "user")
            context: Variables to substitute

        Returns:
            Rendered prompt string

        Raises:
            PromptRenderError: If rendering fails or template not found
        """
        cache_key = f"{extension_name}.{template_name}"
        template = self._templates.get(cache_key)

        if not template:
            raise PromptRenderError(
                f"Template not found: {cache_key}. "
                f"Available templates: {list(self._templates.keys())}"
            )

        return template.render(context)

    def get_extension_prompts(self, extension_name: str) -> Dict[str, str]:
        """
        Get all available prompt templates for an extension.

        Args:
            extension_name: Name of the extension

        Returns:
            Dictionary of template_name -> template_content
        """
        prompts = {}
        for cache_key, template in self._templates.items():
            if cache_key.startswith(f"{extension_name}."):
                template_name = cache_key.split(".", 1)[1]
                prompts[template_name] = template.raw_content
        return prompts

    def get_template_variables(
        self, extension_name: str, template_name: str
    ) -> List[str]:
        """
        Get variables referenced in a template.

        Args:
            extension_name: Name of the extension
            template_name: Name of the template

        Returns:
            List of variable names
        """
        cache_key = f"{extension_name}.{template_name}"
        template = self._templates.get(cache_key)

        if not template:
            return []

        return template.get_variables()

    def validate_template(self, extension_name: str, template_name: str) -> List[str]:
        """
        Validate a template and return any errors.

        Args:
            extension_name: Name of the extension
            template_name: Name of the template

        Returns:
            List of validation errors (empty if valid)
        """
        cache_key = f"{extension_name}.{template_name}"
        template = self._templates.get(cache_key)

        if not template:
            return [f"Template not found: {cache_key}"]

        return template.validate()

    def clear_cache(self, extension_name: Optional[str] = None) -> None:
        """
        Clear cached templates.

        Args:
            extension_name: If specified, only clear templates for this extension
        """
        if extension_name:
            keys_to_remove = [
                k for k in self._templates.keys() if k.startswith(f"{extension_name}.")
            ]
            for key in keys_to_remove:
                del self._templates[key]
        else:
            self._templates.clear()

        logger.debug(
            f"Cleared prompt template cache for {extension_name or 'all extensions'}"
        )


# Singleton instance
_renderer_instance: Optional[PromptRenderer] = None


def get_prompt_renderer(extensions_dir: str = "src/ai_karen_engine/extensions/plugins") -> PromptRenderer:
    """Get the singleton prompt renderer instance."""
    global _renderer_instance
    if _renderer_instance is None:
        _renderer_instance = PromptRenderer(extensions_dir)
    return _renderer_instance


__all__ = [
    "PromptTemplate",
    "PromptRenderer",
    "PromptTemplateError",
    "PromptVariableError",
    "PromptRenderError",
    "get_prompt_renderer",
]
