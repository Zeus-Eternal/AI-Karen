# Directory Structure Migration Plan

## File Moves

### Plugin System

- `/media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/plugin_manager.py` → `/media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/plugins/manager.py`
- `/media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/plugin_router.py` → `/media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/plugins/router.py`
- `/media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/plugins/sandbox.py` → `/media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/plugins/sandbox.py`
- `/media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/plugins/sandbox_runner.py` → `/media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/plugins/sandbox_runner.py`

### Individual Plugin

- `/media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/plugins/hello_world` → `/media/zeus/Development/KIRO/AI-Karen/plugins/examples/hello-world`
  - Category: examples
- `/media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/plugins/sandbox_fail` → `/media/zeus/Development/KIRO/AI-Karen/plugins/examples/sandbox-fail`
  - Category: examples
- `/media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/plugins/time_query` → `/media/zeus/Development/KIRO/AI-Karen/plugins/core/time-query`
  - Category: core
- `/media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/plugins/tui_fallback` → `/media/zeus/Development/KIRO/AI-Karen/plugins/core/tui-fallback`
  - Category: core
- `/media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/plugins/autonomous_task_handler` → `/media/zeus/Development/KIRO/AI-Karen/plugins/automation/autonomous-task-handler`
  - Category: automation
- `/media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/plugins/git_merge_safe` → `/media/zeus/Development/KIRO/AI-Karen/plugins/automation/git-merge-safe`
  - Category: automation
- `/media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/plugins/hf_llm` → `/media/zeus/Development/KIRO/AI-Karen/plugins/ai/hf-llm`
  - Category: ai
- `/media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/plugins/fine_tune_lnm` → `/media/zeus/Development/KIRO/AI-Karen/plugins/ai/fine-tune-lnm`
  - Category: ai
- `/media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/plugins/llm_services` → `/media/zeus/Development/KIRO/AI-Karen/plugins/ai/llm-services`
  - Category: ai
- `/media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/plugins/desktop_agent` → `/media/zeus/Development/KIRO/AI-Karen/plugins/integrations/desktop-agent`
  - Category: integrations
- `/media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/plugins/k8s_scale` → `/media/zeus/Development/KIRO/AI-Karen/plugins/integrations/k8s-scale`
  - Category: integrations
- `/media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/plugins/llm_manager` → `/media/zeus/Development/KIRO/AI-Karen/plugins/integrations/llm-manager`
  - Category: integrations

### Metadata

- `/media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/plugins/__meta` → `/media/zeus/Development/KIRO/AI-Karen/plugins/__meta`

## Import Updates

### /media/zeus/Development/KIRO/AI-Karen/cli.py

- Line 7: `from ai_karen_engine.plugin_router import get_plugin_router` → `from ai_karen_engine.plugins.router import get_plugin_router`

### /media/zeus/Development/KIRO/AI-Karen/main.py

- Line 32: `from ai_karen_engine.plugin_router import get_plugin_router` → `from ai_karen_engine.plugins.router import get_plugin_router`

### /media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/fastapi.py

- Line 25: `from ai_karen_engine.plugin_router import get_plugin_router` → `from ai_karen_engine.plugins.router import get_plugin_router`

### /media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/plugin_manager.py

- Line 8: `from ai_karen_engine.plugin_router import PluginRouter` → `from ai_karen_engine.plugins.router import PluginRouter`

### /media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/__init__.py

- Line 33: `from ai_karen_engine.plugin_router import PluginRouter` → `from ai_karen_engine.plugins.router import PluginRouter`
- Line 36: `from ai_karen_engine.plugin_manager import PluginManager` → `from ai_karen_engine.plugins.manager import PluginManager`
- Line 39: `from ai_karen_engine.plugin_router import AccessDenied` → `from ai_karen_engine.plugins.router import AccessDenied`

### /media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/core/prompt_router.py

- Line 3: `from ai_karen_engine.plugin_router import PluginRouter, PluginRecord` → `from ai_karen_engine.plugins.router import PluginRouter, PluginRecord`

### /media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/core/cortex/dispatch.py

- Line 19: `from ai_karen_engine.plugin_manager import get_plugin_manager` → `from ai_karen_engine.plugins.manager import get_plugin_manager`

### /media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/extensions/manager.py

- Line 16: `from ai_karen_engine.plugin_router import PluginRouter` → `from ai_karen_engine.plugins.router import PluginRouter`

### /media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/extensions/orchestrator.py

- Line 19: `from ai_karen_engine.plugin_router import PluginRouter` → `from ai_karen_engine.plugins.router import PluginRouter`

### /media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/plugins/autonomous_task_handler/__init__.py

- Line 3: `from ai_karen_engine.plugins.autonomous_task_handler.handler import run` → `from plugins.automation.autonomous_task_handler.handler import run`

### /media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/plugins/desktop_agent/handler.py

- Line 1: `from ai_karen_engine.plugins.desktop_agent.agent import DesktopAgent` → `from plugins.integrations.desktop_agent.agent import DesktopAgent`

### /media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/plugins/desktop_agent/__init__.py

- Line 3: `from ai_karen_engine.plugins.desktop_agent.handler import run` → `from plugins.integrations.desktop_agent.handler import run`

### /media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/plugins/fine_tune_lnm/__init__.py

- Line 3: `from ai_karen_engine.plugins.fine_tune_lnm.handler import run` → `from plugins.ai.fine_tune_lnm.handler import run`

### /media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/plugins/git_merge_safe/__init__.py

- Line 3: `from ai_karen_engine.plugins.git_merge_safe.handler import run` → `from plugins.automation.git_merge_safe.handler import run`

### /media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/plugins/hello_world/__init__.py

- Line 3: `from ai_karen_engine.plugins.hello_world.handler import run` → `from plugins.examples.hello_world.handler import run`

### /media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/plugins/hf_llm/__init__.py

- Line 3: `from ai_karen_engine.plugins.hf_llm.handler import run` → `from plugins.ai.hf_llm.handler import run`

### /media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/plugins/k8s_scale/__init__.py

- Line 3: `from ai_karen_engine.plugins.k8s_scale.handler import run` → `from plugins.integrations.k8s_scale.handler import run`

### /media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/plugins/llm_manager/__init__.py

- Line 3: `from ai_karen_engine.plugins.llm_manager.handler import run` → `from plugins.integrations.llm_manager.handler import run`

### /media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/plugins/llm_services/deepseek/__init__.py

- Line 1: `from ai_karen_engine.plugins.llm_services.deepseek.handler import run` → `from plugins.ai.llm_services.deepseek.handler import run`

### /media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/plugins/llm_services/gemini/__init__.py

- Line 1: `from ai_karen_engine.plugins.llm_services.gemini.handler import run` → `from plugins.ai.llm_services.gemini.handler import run`

### /media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/plugins/llm_services/llama/llama_plugin.py

- Line 13: `from ai_karen_engine.plugins.llm_services.ollama.ollama_service import ollama_inprocess_client` → `from plugins.ai.llm_services.ollama.ollama_service import ollama_inprocess_client`

### /media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/plugins/llm_services/llama/__init__.py

- Line 1: `from ai_karen_engine.plugins.llm_services.llama.handler import run` → `from plugins.ai.llm_services.llama.handler import run`

### /media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/plugins/llm_services/openai/__init__.py

- Line 1: `from ai_karen_engine.plugins.llm_services.openai.handler import run` → `from plugins.ai.llm_services.openai.handler import run`

### /media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/plugins/time_query/__init__.py

- Line 3: `from ai_karen_engine.plugins.time_query.handler import run` → `from plugins.core.time_query.handler import run`

### /media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/plugins/tui_fallback/handler.py

- Line 1: `from ai_karen_engine.plugins.tui_fallback import tui` → `from plugins.core.tui_fallback import tui`

### /media/zeus/Development/KIRO/AI-Karen/src/ai_karen_engine/plugins/tui_fallback/__init__.py

- Line 3: `from ai_karen_engine.plugins.tui_fallback.handler import run` → `from plugins.core.tui_fallback.handler import run`

### /media/zeus/Development/KIRO/AI-Karen/tests/test_imports.py

- Line 19: `from ai_karen_engine.plugin_router import PluginRouter` → `from ai_karen_engine.plugins.router import PluginRouter`

### /media/zeus/Development/KIRO/AI-Karen/tests/test_llm_manager.py

- Line 3: `from ai_karen_engine.plugins.llm_manager.handler import run` → `from plugins.integrations.llm_manager.handler import run`

### /media/zeus/Development/KIRO/AI-Karen/tests/test_plugin_router.py

- Line 11: `from ai_karen_engine.plugin_router import AccessDenied, PluginRouter` → `from ai_karen_engine.plugins.router import AccessDenied, PluginRouter`

### /media/zeus/Development/KIRO/AI-Karen/tests/test_sandbox.py

- Line 8: `from ai_karen_engine.plugin_router import PluginRouter` → `from ai_karen_engine.plugins.router import PluginRouter`

### /media/zeus/Development/KIRO/AI-Karen/tests/test_workflow_rpa.py

- Line 15: `from ai_karen_engine.plugin_router import PluginRouter` → `from ai_karen_engine.plugins.router import PluginRouter`

## Validation Steps

1. Verify all source files exist before moving
2. Check that target directories can be created
3. Validate that no files will be overwritten
4. Test import syntax after updates
5. Run basic import tests
6. Verify plugin discovery still works
7. Test extension system integration
8. Run core functionality tests

## Rollback Steps

1. Restore original file locations
2. Revert import statement changes
3. Remove newly created directories if empty
4. Restore original plugin discovery paths
5. Verify system functionality after rollback