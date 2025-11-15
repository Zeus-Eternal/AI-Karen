#!/usr/bin/env python3
"""
Fix pydantic imports across the codebase by adding try/except ImportError fallback.
"""

import re
from pathlib import Path
from typing import List, Tuple

# Files to fix (from the analysis)
FILES_TO_FIX = [
    # API Routes (39 files)
    "src/ai_karen_engine/api_routes/training_interface_routes.py",
    "src/ai_karen_engine/api_routes/scheduler_routes.py",
    "src/ai_karen_engine/api_routes/copilotkit_settings_routes.py",
    "src/ai_karen_engine/api_routes/public_routes.py",
    "src/ai_karen_engine/api_routes/response_core_routes.py",
    "src/ai_karen_engine/api_routes/error_dashboard_routes.py",
    "src/ai_karen_engine/api_routes/copilot_settings_routes.py",
    "src/ai_karen_engine/api_routes/plugin_routes.py",
    "src/ai_karen_engine/api_routes/slo_routes.py",
    "src/ai_karen_engine/api_routes/error_recovery_routes.py",
    "src/ai_karen_engine/api_routes/optimization_integration_routes.py",
    "src/ai_karen_engine/api_routes/plan_routes.py",
    "src/ai_karen_engine/api_routes/basic_training_routes.py",
    "src/ai_karen_engine/api_routes/copilot_routes.py",
    "src/ai_karen_engine/api_routes/unified_schemas.py",
    "src/ai_karen_engine/api_routes/knowledge_routes.py",
    "src/ai_karen_engine/api_routes/advanced_training_routes.py",
    "src/ai_karen_engine/api_routes/orchestration_routes.py",
    "src/ai_karen_engine/api_routes/performance_monitoring_routes.py",
    "src/ai_karen_engine/api_routes/persona_routes.py",
    "src/ai_karen_engine/api_routes/cognitive_routes.py",
    "src/ai_karen_engine/api_routes/ai_orchestrator_routes.py",
    "src/ai_karen_engine/api_routes/memory_routes.py",
    "src/ai_karen_engine/api_routes/error_response_routes.py",
    "src/ai_karen_engine/api_routes/reasoning_routes.py",
    "src/ai_karen_engine/api_routes/advanced_formatting_routes.py",
    "src/ai_karen_engine/api_routes/web_api_compatibility.py",
    "src/ai_karen_engine/api_routes/analytics_routes.py",
    "src/ai_karen_engine/api_routes/cache_management_routes.py",
    "src/ai_karen_engine/api_routes/privacy_routes.py",
    "src/ai_karen_engine/api_routes/dynamic_provider_routes.py",
    "src/ai_karen_engine/api_routes/performance_routes.py",
    "src/ai_karen_engine/api_routes/chat_runtime.py",
    "src/ai_karen_engine/api_routes/orchestration_agent_routes.py",
    "src/ai_karen_engine/api_routes/production_monitoring_routes.py",
    "src/ai_karen_engine/api_routes/production_auth_routes.py",
    "src/ai_karen_engine/api_routes/provider_compatibility_routes.py",
    "src/ai_karen_engine/api_routes/events.py",
    "src/ai_karen_engine/api_routes/training_data_routes.py",
    # Models (6 files)
    "src/ai_karen_engine/models/web_ui_types.py",
    "src/ai_karen_engine/models/shared_types.py",
    "src/ai_karen_engine/models/web_api_error_responses.py",
    "src/ai_karen_engine/models/persona_models.py",
    "src/ai_karen_engine/models/ag_ui_types.py",
    "src/ai_karen_engine/models/error_responses.py",
    # Services (10 files)
    "src/ai_karen_engine/services/analytics_dashboard.py",
    "src/ai_karen_engine/services/plugin_execution.py",
    "src/ai_karen_engine/services/tool_service.py",
    "src/ai_karen_engine/services/conversation_service.py",
    "src/ai_karen_engine/services/error_response_service.py",
    "src/ai_karen_engine/services/plugin_registry.py",
    "src/ai_karen_engine/services/unified_memory_service.py",
    "src/ai_karen_engine/services/analytics_service.py",
    "src/ai_karen_engine/services/enhanced_memory_service.py",
    "src/ai_karen_engine/services/memory_service.py",
    "src/ai_karen_engine/services/conversation_tracker.py",
    "src/ai_karen_engine/services/memory_writeback.py",
    # Chat (1 file)
    "src/ai_karen_engine/chat/conversation_models.py",
    # Config (2 files)
    "src/ai_karen_engine/config/enhanced_config_manager.py",
    "src/ai_karen_engine/config/deployment_config_manager.py",
    # Core (2 files)
    "src/ai_karen_engine/core/chat_memory_config.py",
    "src/ai_karen_engine/core/services/base.py",
    # Utils (1 file)
    "src/ai_karen_engine/utils/pydantic_base.py",
]


def fix_pydantic_import(file_path: str) -> Tuple[bool, str]:
    """
    Fix pydantic imports in a single file.
    Returns (success, message)
    """
    path = Path(file_path)
    if not path.exists():
        return False, f"File not found: {file_path}"

    try:
        content = path.read_text()
        original_content = content

        # Pattern to match pydantic import lines
        # Matches: from pydantic import ...
        pydantic_import_pattern = r'^([ \t]*)(from pydantic import [^\n]+)$'

        lines = content.split('\n')
        new_lines = []
        i = 0
        modified = False

        while i < len(lines):
            line = lines[i]
            match = re.match(pydantic_import_pattern, line)

            if match:
                indent = match.group(1)
                import_statement = match.group(2)

                # Check if this is already in a try/except block
                # Look back to see if there's a try: statement
                has_try_before = False
                for j in range(max(0, i-5), i):
                    if 'try:' in lines[j] and 'pydantic' in lines[j:i+1].__str__():
                        has_try_before = True
                        break

                if not has_try_before:
                    # Extract what's being imported
                    imports_part = import_statement.replace('from pydantic import ', '')

                    # Create the try/except block
                    new_lines.append(f"{indent}try:")
                    new_lines.append(f"{indent}    {import_statement}")
                    new_lines.append(f"{indent}except ImportError:")
                    new_lines.append(f"{indent}    from ai_karen_engine.pydantic_stub import {imports_part}")

                    modified = True
                else:
                    # Already has try block, keep as is
                    new_lines.append(line)
            else:
                new_lines.append(line)

            i += 1

        if modified:
            new_content = '\n'.join(new_lines)
            path.write_text(new_content)
            return True, f"✓ Fixed: {file_path}"
        else:
            return True, f"○ No changes needed: {file_path}"

    except Exception as e:
        return False, f"✗ Error processing {file_path}: {e}"


def main():
    """Fix all files."""
    print("=" * 70)
    print("Fixing pydantic imports across AI-Karen codebase")
    print("=" * 70)
    print()

    success_count = 0
    error_count = 0
    modified_count = 0

    for file_path in FILES_TO_FIX:
        success, message = fix_pydantic_import(file_path)
        print(message)

        if success:
            success_count += 1
            if "✓ Fixed:" in message:
                modified_count += 1
        else:
            error_count += 1

    print()
    print("=" * 70)
    print(f"Summary:")
    print(f"  Total files processed: {len(FILES_TO_FIX)}")
    print(f"  Successfully modified: {modified_count}")
    print(f"  No changes needed: {success_count - modified_count}")
    print(f"  Errors: {error_count}")
    print("=" * 70)

    return error_count == 0


if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)
