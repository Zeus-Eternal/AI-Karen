# PromptBuilder Implementation

The PromptBuilder is a Jinja2-based prompt construction system that implements the PromptBuilder protocol for the Response Core orchestrator. It creates structured prompts with persona and context data injection.

## Features

- **Protocol Compliance**: Implements the `PromptBuilder` protocol interface
- **Template-Based**: Uses Jinja2 templates for flexible prompt construction
- **Persona-Aware**: Adapts prompts based on selected persona and user mood
- **Context Integration**: Incorporates memory context and conversation history
- **Onboarding Support**: Handles profile gaps with structured onboarding flows
- **CopilotKit Integration**: Optional enhanced features when CopilotKit is available
- **Graceful Fallbacks**: Continues working even when templates fail to load

## Core Templates

### system_base.j2
The system message template that sets up the AI persona and behavior:
- Persona-specific instructions
- Mood-based adaptations (especially for frustrated users)
- Intent-specific guidance (optimize_code, debug_error, documentation)
- CopilotKit feature enablement
- Response structure guidelines

### user_frame.j2
The user message template that formats user input with context:
- Context section with relevant conversation history
- Current request formatting
- Intent-specific guidance for the AI
- Context truncation (shows first 3 items, indicates more available)

### onboarding.j2
The onboarding template for handling profile gaps:
- Structured "Quick Setup Needed" section
- Primary gap focus (asks one question at a time)
- Context-aware question formatting
- Persona-specific encouragement
- Secondary gaps indication

## Usage

### Basic Usage

```python
from ai_karen_engine.core.response.prompt_builder import PromptBuilder

builder = PromptBuilder()

messages = builder.build_prompt(
    user_text="Help me optimize this code",
    persona="ruthless_optimizer",
    context=[{"text": "Previous discussion about performance"}],
    intent="optimize_code",
    mood="neutral"
)

# Returns list of message dicts for LLM:
# [
#   {"role": "system", "content": "You are ruthless_optimizer..."},
#   {"role": "user", "content": "## Context\n..."}
# ]
```

### With Onboarding

```python
messages = builder.build_prompt(
    user_text="I need help with my project",
    persona="calm_fixit",
    context=[],
    gaps=["project_context", "tech_stack"],
    intent="general_assist",
    mood="frustrated"
)
```

### With CopilotKit

```python
messages = builder.build_prompt(
    user_text="Show me the component structure",
    persona="technical_writer",
    context=[],
    ui_caps={"copilotkit": True},
    intent="documentation"
)
```

### Direct Template Rendering

```python
# Render specific templates directly
system_prompt = builder.render_template(
    "system_base",
    persona="ruthless_optimizer",
    intent="debug_error",
    mood="neutral",
    ui_caps={},
    copilotkit_enabled=False
)
```

## Template Variables

### system_base.j2 Variables
- `persona`: Selected persona (ruthless_optimizer, calm_fixit, technical_writer)
- `intent`: User intent (optimize_code, debug_error, documentation, general_assist)
- `mood`: User mood (neutral, frustrated, positive, negative)
- `ui_caps`: UI capabilities dictionary
- `copilotkit_enabled`: Boolean for CopilotKit features

### user_frame.j2 Variables
- `user_text`: Original user input
- `context`: List of context dictionaries from memory
- `context_count`: Number of context items
- `intent`: User intent for specific guidance
- `persona`: Selected persona

### onboarding.j2 Variables
- `gaps`: List of profile gaps to address
- `primary_gap`: First/most important gap
- `persona`: Selected persona for appropriate tone
- `intent`: User intent for context

## Error Handling

The PromptBuilder includes comprehensive error handling:

1. **Template Not Found**: Falls back to simple string formatting
2. **Rendering Errors**: Logs errors and uses fallback prompts
3. **Missing Variables**: Jinja2 handles missing variables gracefully
4. **Template Cache**: Caches loaded templates for performance

## Integration with Response Core

The PromptBuilder integrates seamlessly with the Response Core orchestrator:

```python
from ai_karen_engine.core.response import create_response_orchestrator

# The orchestrator uses PromptBuilder internally
orchestrator = create_response_orchestrator()

response = orchestrator.respond(
    user_text="Help me debug this error",
    ui_caps={"copilotkit": True}
)
```

## Requirements Satisfied

This implementation satisfies the following requirements:

- **Requirement 2.3**: Build structured prompts using Jinja2 templates
- **Requirement 3.4**: Support persona detection and suggestion
- **Requirement 3.6**: Handle onboarding gaps with concise questions
- **Requirement 8.2**: Include structured sections (Quick Plan, Next Action, Optional Boost)

## Testing

Comprehensive tests are available in `tests/test_prompt_builder.py`:

```bash
python -m pytest tests/test_prompt_builder.py -v
```

## Demo

Run the demo to see the PromptBuilder in action:

```bash
python examples/prompt_builder_demo.py
```

## Template Customization

Templates can be customized by:

1. Modifying existing templates in `src/ai_karen_engine/core/response/templates/`
2. Adding new templates and using `render_template()` method
3. Creating custom template directories and passing to constructor

The templates use standard Jinja2 syntax with conditional logic, loops, and variable substitution.