# KARI Extension System Documentation

## Overview

The KARI Extension System is a two-tier architecture that provides a clean, modular, and scalable way to extend the functionality of the KARI AI system. It consists of two main components:

1. **Extension Host** (`src/ai_karen_engine/extension_host/`) - The runtime and loader components
2. **Extensions Catalog** (`src/extensions/`) - All actual extensions (first-party and user)

## Architecture

### Extension Host

The Extension Host contains the core machinery that handles:
- Extension discovery
- Manifest parsing
- Schema validation
- Loading Python entrypoint classes
- Registering extensions by hook point
- Executing extensions in the correct order
- Timing out slow extensions
- Error isolation
- Logging and metrics
- Enforcing permissions and RBAC rules

The Extension Host contains zero business logic and zero extension content.

### Extensions Catalog

The Extensions Catalog is the single unified home for all extensions:
- First-party Kari extensions
- Organization-specific extensions
- User-installed extensions
- Custom/private modules
- Experimental extensions

## Directory Structure

```
src/
 ├── ai_karen_engine/
 │    └── extension_host/
 │         ├── __init__.py
 │         ├── base.py
 │         ├── loader.py
 │         ├── registry.py
 │         ├── runner.py
 │         ├── config.py
 │         ├── errors.py
 │         └── utils/
 │              └── validation.py
 │
 └── extensions/
      ├── README.md
      ├── memory_short_term_booster/
      │    ├── extension_manifest.json
      │    ├── handler.py
      │    └── prompt.txt
      │
      ├── reasoning_rewriter/
      │    ├── extension_manifest.json
      │    ├── handler.py
      │    └── prompt.txt
      │
      ├── security_redactor/
      │    ├── extension_manifest.json
      │    ├── handler.py
      │    └── prompt.txt
      │
      └── <more_extensions>/
```

## Hook Points

Extensions can implement any of the following standardized hook points:

- `pre_intent_detection` - Before intent detection
- `pre_memory_retrieval` - Before memory retrieval
- `post_memory_retrieval` - After memory retrieval
- `pre_llm_prompt` - Before LLM prompt generation
- `post_llm_result` - After LLM result processing
- `post_response` - Before final response to user

## Extension Manifest

Every extension must include an `extension_manifest.json` file with the following schema:

```json
{
  "id": "kari.memory.short_term_booster",
  "name": "Short-Term Memory Booster",
  "version": "1.0.0",
  "entrypoint": "handler:ShortTermMemoryExtension",
  "description": "Enhances memory retrieval quality before LLM call.",
  "hook_points": [
    "pre_memory_retrieval",
    "post_memory_retrieval",
    "pre_llm_prompt"
  ],
  "prompt_files": {
    "system": "prompt.txt"
  },
  "config_schema": {
    "type": "object",
    "properties": {
      "similarity_threshold": { "type": "number", "default": 0.75 },
      "max_items": { "type": "integer", "default": 12 }
    }
  },
  "permissions": {
    "memory_read": true,
    "memory_write": false,
    "tools": ["search_basic"]
  },
  "rbac": {
    "allowed_roles": ["system", "admin"],
    "default_enabled": true
  }
}
```

## Extension Handler

Each extension must implement a `handler.py` file with a class that extends `ExtensionBase`:

```python
from ai_karen_engine.extension_host.base import ExtensionBase, HookPoint, HookContext

class MyExtension(ExtensionBase):
    async def execute_hook(self, hook_point: HookPoint, context: HookContext) -> Dict[str, Any]:
        # Extension logic here
        return {"result": "success"}
```

## Extension Naming Rules

Extensions in `src/extensions/` must use the format:

```
<category>_<capability>/
```

Examples:
- `memory_context_expander/`
- `security_output_redactor/`
- `reasoning_chain_optimizer/`
- `analytics_user_behavior_logger/`
- `multimedia_image_captioner/`
- `agent_router_biaser/`

## Using the Extension System

### Loading Extensions

```python
from ai_karen_engine.extension_host import ExtensionManager, ExtensionLoader, ExtensionRegistry, ExtensionRunner

# Create extension manager
manager = ExtensionManager()

# Load extensions
await manager.load_extensions()

# Get registry and runner
registry = manager.registry
runner = manager.runner
```

### Executing Hooks

```python
from ai_karen_engine.extension_host.base import HookPoint, HookContext

# Create context
context = HookContext(
    data={"message": "Hello world"},
    user_id="user123",
    session_id="session456"
)

# Execute hook
results = await runner.execute_hook(
    hook_point=HookPoint.PRE_LLM_PROMPT,
    context=context,
    user_role="user"
)
```

### Getting Metrics

```python
# Get execution statistics
stats = runner.get_execution_stats()

# Get Prometheus metrics
metrics = runner.get_prometheus_metrics()

# Get metrics for a specific extension
extension_metrics = runner.get_extension_metrics("memory_short_term_booster")

# Get metrics for a specific hook point
hook_metrics = runner.get_hook_metrics(HookPoint.PRE_LLM_PROMPT)
```

## Permissions and RBAC

Extensions can define permissions and RBAC rules in their manifest:

```json
{
  "permissions": {
    "memory_read": true,
    "memory_write": false,
    "tools": ["search_basic"]
  },
  "rbac": {
    "allowed_roles": ["system", "admin"],
    "default_enabled": true
  }
}
```

The Extension Runner will automatically check these permissions when executing extensions.

## Error Handling

The Extension System provides comprehensive error handling:

- `ExtensionNotFoundError` - Extension not found
- `ExtensionLoadError` - Error loading extension
- `ExtensionExecutionError` - Error executing extension
- `ExtensionTimeoutError` - Extension execution timed out
- `ExtensionPermissionError` - Permission denied
- `ExtensionHookError` - Error in hook execution

## Observability and Metrics

The Extension System provides comprehensive metrics and observability:

- Execution counts for hooks and extensions
- Execution duration histograms
- Error counters
- Active extensions gauge
- Timeout counters

Metrics are available both through Prometheus (if installed) and through the API methods.

## Best Practices

1. **Keep extensions focused** - Each extension should do one thing well
2. **Use appropriate hook points** - Choose the right hook point for your extension
3. **Handle errors gracefully** - Extensions should not crash the system
4. **Respect permissions** - Only access resources you have permission for
5. **Provide clear descriptions** - Document what your extension does
6. **Test thoroughly** - Ensure your extension works in all scenarios
7. **Monitor performance** - Keep an eye on execution time and resource usage

## Example Extensions

The system includes three example extensions:

1. **Memory Short Term Booster** - Enhances memory retrieval quality
2. **Reasoning Rewriter** - Improves reasoning chains and logical consistency
3. **Security Redactor** - Redacts sensitive information and enforces security policies

These examples demonstrate how to implement extensions for different hook points and use cases.

## Troubleshooting

### Extension not loading

- Check that the extension directory structure is correct
- Verify that the extension_manifest.json is valid
- Ensure that the handler.py exists and implements ExtensionBase
- Check the logs for error messages

### Extension not executing

- Check that the extension is enabled
- Verify that the user has the required permissions
- Ensure that the extension implements the required hook points
- Check the logs for error messages

### Performance issues

- Monitor execution times for extensions
- Check for timeouts in the logs
- Consider optimizing slow extensions
- Use the metrics to identify bottlenecks