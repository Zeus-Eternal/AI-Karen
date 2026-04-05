# Prompt-First Plugin Template Specification

## Overview

Prompt-first plugins define their behavior through Jinja2 template files rather than hardcoded Python code. This allows for:

- **Declarative plugin definitions**: Describe what the plugin does, not how to implement it
- **Easy customization**: Users can modify prompts without changing code
- **Multi-language support**: Different prompts for different contexts
- **Variable substitution**: Dynamic content injection at runtime
- **Template reuse**: Share templates between plugins

## File Structure

Prompt-first plugins are structured as:

```
src/extensions/
  ├── my-plugin/
  │   ├── extension_manifest.json    # Plugin metadata
  │   ├── prompt.txt                # Main prompt template (system + user)
  │   ├── templates/                # Optional additional templates
  │   │   ├── system.txt
  │   │   └── user.txt
  │   ├── handler.py                # Optional custom Python handler
  │   └── icon.svg                 # Icon for UI (auto-discovered)
  └── ...
```

## Prompt Template Format

### Basic Template

A prompt template is a text file with Jinja2 syntax for variable substitution:

```txt
You are a {{ plugin_type }} assistant.

Your task is to {{ task_description }}.

{% if constraints %}
Constraints:
{{ constraints }}
{% endif %}

{% if examples %}
Examples:
{% for example in examples %}
- {{ example }}
{% endfor %}
{% endif %}
```

### Jinja2 Syntax Support

#### Variables
```txt
Hello, {{ user_name }}!
Today is {{ current_date }}.
```

#### Conditionals
```txt
{% if user_role == "admin" %}
You have administrative privileges.
{% else %}
You have standard user privileges.
{% endif %}

{% if show_debug %}
DEBUG: Processing request...
{% endif %}
```

#### Loops
```txt
Available tools:
{% for tool in tools %}
- {{ tool.name }}: {{ tool.description }}
{% endfor %}

{{ items|to_list }}
```

#### Filters
```txt
{{ user_name|upper }}
{{ description|truncate_words(50) }}
{{ value|default_if_empty("N/A") }}
```

#### Comments
```txt
{# This is a comment and won't appear in the rendered prompt #}

User query: {{ query }}
{# TODO: Add more examples #}
```

### Built-in Filters

- `to_list`: Convert value to list
- `default_if_empty(value, default)`: Return default if value is empty
- `truncate_words(max_words)`: Truncate text to max_words words

## Manifest Configuration

Plugin manifests specify prompt file locations in `prompt_files`:

```json
{
  "name": "weather-query",
  "version": "1.0.0",
  "display_name": "Weather Query",
  "description": "Get weather information for a location",
  "prompt_files": {
    "system": "prompts/system.txt",
    "user": "prompts/user.txt",
    "templates": {
      "forecast": "prompts/forecast.txt"
    },
    "templates_config": {
      "system": {
        "variables": ["location", "units"],
        "required_variables": ["location"]
      },
      "user": {
        "variables": ["query"],
        "required_variables": ["query"]
      }
    }
  },
  "capabilities": {
    "prompt_first": true,
    "provides_ui": true
  }
}
```

### PromptFiles Fields

- `system`: Path to system prompt template
- `user`: Path to user prompt template
- `templates`: Dictionary of additional named templates
- `templates_config`: Configuration for each template
  - `variables`: All variables referenced in the template
  - `required_variables`: Variables that must be provided (error if missing)

## Context Variables

When rendering prompts, the system provides a context dictionary with:

### Common Variables

- `plugin_name`: Name of the plugin
- `plugin_version`: Version of the plugin
- `current_date`: ISO format date string
- `current_time`: ISO format time string
- `user_id`: Current user ID (if available)
- `user_role`: User's role (if available)
- `tenant_id`: Current tenant ID (if available)

### Request-Specific Variables

- `query`: User's original query/input
- `intent`: Detected intent/route
- `context`: Additional context from previous interactions
- `parameters`: Plugin-specific parameters

### Extension-Specific Variables

Plugins can define custom variables in their templates:

```txt
{{ custom_variable }}
{{ plugin_specific_data }}
```

## Example: Weather Plugin

### extension_manifest.json

```json
{
  "name": "weather-query",
  "version": "1.0.0",
  "display_name": "Weather Query",
  "description": "Get current weather and forecast for any location",
  "author": "Karen Team",
  "license": "MIT",
  "category": "productivity",
  "api_version": "1.0",
  "prompt_files": {
    "system": "prompts/system.txt",
    "user": "prompts/user.txt"
  },
  "capabilities": {
    "prompt_first": true,
    "provides_ui": true
  }
}
```

### prompts/system.txt

```txt
You are a helpful weather assistant for the Karen AI platform.

Your capabilities:
- Provide current weather conditions for any location
- Offer weather forecasts (hourly, daily, weekly)
- Explain weather data in simple, accessible terms
- Handle location queries (city names, coordinates, postal codes)

When responding:
- Always include temperature, conditions, and location
- Use metric units by default (Celsius, km/h)
- Offer to convert units if user prefers imperial
- Keep responses concise but informative
- Suggest relevant follow-up questions

{% if show_debug %}
DEBUG MODE ON - Include technical details in responses.
{% endif %}
```

### prompts/user.txt

```txt
User query: {{ query }}

Location: {{ location|default_if_empty("unknown") }}
{% if units %}
Preferred units: {{ units }}
{% endif %}

{% if forecast_days %}
Forecast requested for: {{ forecast_days }} days
{% endif %}

Please provide weather information for this request.
```

## Error Handling

### Missing Required Variables

If a required variable is not provided, the renderer raises:

```
PromptVariableError: Missing required variables for template 'user': ['location', 'query'].
Required: ['location', 'query'], Provided: ['query']
```

### Undefined Variables

If a variable is referenced but not provided, Jinja2 raises:

```
UndefinedError: 'location' is undefined
```

### Template Syntax Errors

Invalid Jinja2 syntax results in:

```
PromptTemplateError: Syntax error in template 'user': unexpected '}'
```

## Best Practices

### 1. Always Define Variables

```txt
Good:
{{ user_name|default_if_empty("there") }}

Bad:
{{ user_name }}  {# Will error if missing #}
```

### 2. Use Filters for Safety

```txt
Good:
{{ long_text|truncate_words(50) }}

Bad:
{{ long_text }}  {# May be too long #}
```

### 3. Document Required Variables

```txt
{#
  Required Variables:
  - location: City name or coordinates
  - units: 'metric' or 'imperial' (optional, default: metric)
#}

Weather for {{ location }}...
```

### 4. Use Sections for Clarity

```txt
{# SECTION: INTRODUCTION #}
You are a {{ plugin_type }} assistant.

{# SECTION: INSTRUCTIONS #}
Your task is to {{ task }}.

{# SECTION: EXAMPLES #}
{% if show_examples %}
Examples:
...
{% endif %}
```

### 5. Provide Fallbacks

```txt
{% if detailed_response %}
{# Provide detailed response #}
...

{% else %}
{# Provide simple response #}
Brief: {{ summary }}
{% endif %}
```

## Advanced Features

### Template Inheritance

Not directly supported, but you can include content:

```txt
{% include 'common_header.txt' %}

Plugin-specific content...

{% include 'common_footer.txt' %}
```

### Custom Filters

Plugins can register custom filters via Python handlers:

```python
# handler.py
from extensions.core.host.prompt_renderer import get_prompt_renderer

def my_custom_filter(value: str, param: str) -> str:
    return f"{value} ({param})"

renderer = get_prompt_renderer()
renderer.env.filters['my_custom'] = my_custom_filter
```

### Conditional Rendering Based on Context

```txt
{% if user_role == 'admin' %}
{# Show admin-only information #}
Administrative controls enabled.
{% elif user_role == 'developer' %}
{# Show developer tools #}
Debug mode available.
{% else %}
{# Standard user #}
Standard interface.
{% endif %}
```

## Migration Guide

### Migrating from Python Handlers to Prompt Templates

**Before (Python handler):**

```python
class WeatherHandler(ExtensionBase):
    async def execute_hook(self, hook_point, context):
        query = context.get_data("query")
        # Build prompt manually
        prompt = f"Get weather for {query}"
        return {"response": await self.call_llm(prompt)}
```

**After (Prompt template):**

```txt
# prompts/user.txt
User query: {{ query }}
Get weather information for this request.
```

```python
# handler.py (optional, or let prompt renderer handle it)
from extensions.core.host.prompt_renderer import get_prompt_renderer

renderer = get_prompt_renderer()
rendered_prompt = renderer.render_prompt("weather-query", "user", {"query": query})
```

## Validation

The prompt renderer validates templates by:

1. **Syntax check**: Validates Jinja2 syntax
2. **Variable check**: Ensures required variables are defined
3. **Compilation**: Attempts to compile template
4. **Context check**: Validates required variables are provided

To validate a template:

```python
from extensions.core.host.prompt_renderer import get_prompt_renderer

renderer = get_prompt_renderer()
errors = renderer.validate_template("my-plugin", "user")

if errors:
    print("Validation errors:", errors)
else:
    print("Template is valid")
```

## Performance

Templates are automatically cached after first compilation. To clear cache:

```python
renderer = get_prompt_renderer()
renderer.clear_cache("my-plugin")  # Clear specific plugin
renderer.clear_cache()  # Clear all plugins
```

## Troubleshooting

### Template Not Found

```
PromptRenderError: Template not found: my-plugin.user
```

**Solution**: Check that `prompt_files` in manifest correctly specifies template paths.

### Variable Not Defined

```
UndefinedError: 'location' is undefined
```

**Solution**: Either:
1. Provide the variable in the context
2. Use `|default_if_empty("value")` filter
3. Remove variable reference from template

### Syntax Error

```
PromptTemplateError: Syntax error in template: unexpected '}'
```

**Solution**: Check Jinja2 syntax - look for:
- Unbalanced braces `{{` or `}}`
- Missing `{% endif %}` or `{% endfor %}`
- Invalid filter syntax

## See Also

- [Jinja2 Documentation](https://jinja.palletsprojects.com/)
- [Plugin Manifest Specification](./plugin-manifest-schema.md)
- [UI Materialization Pipeline](./ui-materialization-spec.md)
- [Marketplace Integration](./marketplace-integration.md)
