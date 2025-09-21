#!/usr/bin/env bash
set -euo pipefail

# Reorganize documentation into a clearer structure.
# Run from repo root: bash scripts/reorg_docs.sh

mk() { mkdir -p "$1"; }
mv_if() { [ -e "$1" ] && git mv "$1" "$2" || echo "skip: $1"; }

mk docs/overview docs/getting-started docs/security docs/models docs/internals docs/releases docs/archive

# Overview
mv_if docs/architecture.md docs/overview/architecture.md
mv_if docs/memory_arch.md docs/overview/memory_arch.md
mv_if docs/mesh_arch.md docs/overview/mesh_arch.md
mv_if docs/agent_flow.md docs/overview/agent_flow.md
mv_if docs/agent_roadmap.md docs/overview/agent_roadmap.md

# Getting started (from guides)
mv_if docs/guides/development_guide.md docs/getting-started/development_guide.md
mv_if docs/guides/developer-configuration-guide.md docs/getting-started/developer-configuration-guide.md
mv_if docs/guides/environment-variables.md docs/getting-started/environment-variables.md
mv_if docs/guides/deployment.md docs/getting-started/deployment.md
mv_if docs/guides/deployment-configuration-guide.md docs/getting-started/deployment-configuration-guide.md
mv_if docs/guides/one-liner-launch.md docs/getting-started/one-liner-launch.md
mv_if docs/guides/troubleshooting-guide.md docs/getting-started/troubleshooting-guide.md
mv_if docs/guides/troubleshooting.md docs/getting-started/troubleshooting.md

# API (already in place)
# Auth
mv_if docs/PRODUCTION_AUTH_IMPLEMENTATION.md docs/auth/PRODUCTION_AUTH_IMPLEMENTATION.md
mv_if docs/user/authentication_troubleshooting.md docs/auth/authentication_troubleshooting.md
mv_if docs/LONG_LIVED_TOKEN_IMPLEMENTATION.md docs/auth/LONG_LIVED_TOKEN_IMPLEMENTATION.md

# Security
mv_if docs/security.md docs/security/security.md
mv_if docs/security_framework.md docs/security/security_framework.md
mv_if docs/validation_monitoring_guide.md docs/security/validation_monitoring_guide.md

# Models
mv_if docs/llm_guide.md docs/models/llm_guide.md
mv_if docs/llamacpp_manager.md docs/models/llamacpp_manager.md
mv_if docs/LLAMACPP_MIGRATION_VALIDATION_REPORT.md docs/models/LLAMACPP_MIGRATION_VALIDATION_REPORT.md
mv_if docs/model_library_documentation_index.md docs/models/model_library_documentation_index.md
mv_if docs/model_library_help_guide.md docs/models/model_library_help_guide.md
mv_if docs/model_library_integration_summary.md docs/models/model_library_integration_summary.md
mv_if docs/model_library_technical_guide.md docs/models/model_library_technical_guide.md
mv_if docs/model_library_user_guide.md docs/models/model_library_user_guide.md

# Guides (move root-level guides into the guides folder)
mv_if docs/chat_interface.md docs/guides/chat_interface.md
mv_if docs/web_ui_compatibility_layer.md docs/guides/web_ui_compatibility_layer.md
mv_if docs/performance_audit_guide.md docs/guides/performance_audit_guide.md
mv_if docs/copilotkit_provider.md docs/guides/copilotkit_provider.md
mv_if docs/n8n_integration.md docs/guides/n8n_integration.md
mv_if docs/tests.md docs/guides/tests.md
mv_if docs/ui_blueprint.md docs/guides/ui_blueprint.md
mv_if docs/side_by_side_openai_kari.md docs/guides/side_by_side_openai_kari.md
mv_if docs/CONSOLE_ERROR_DEBUGGING_GUIDE.md docs/guides/CONSOLE_ERROR_DEBUGGING_GUIDE.md

# Internals
mv_if docs/enhanced_config_manager.md docs/internals/enhanced_config_manager.md
mv_if docs/event_bus.md docs/internals/event_bus.md
mv_if docs/response_core_api_integration.md docs/internals/response_core_api_integration.md
mv_if docs/ice_wrapper.md docs/internals/ice_wrapper.md
mv_if docs/service_classification_system.md docs/internals/service_classification_system.md
mv_if docs/automation_features.md docs/internals/automation_features.md
mv_if docs/LANGGRAPH_ORCHESTRATION.md docs/internals/LANGGRAPH_ORCHESTRATION.md
mv_if docs/milvus_client_benchmark.md docs/internals/milvus_client_benchmark.md

# Releases
mv_if docs/CHANGELOG.md docs/releases/CHANGELOG.md

# Archive (historical fix/summary docs)
for f in \
  ASYNC_TASK_ORCHESTRATOR_IMPLEMENTATION_SUMMARY.md \
  AUTHENTICATION_CONCURRENCY_FIX_SUMMARY.md \
  AUTHENTICATION_FIX_SUMMARY.md \
  AUTHENTICATION_TIMEOUT_FIX.md \
  CUSTOM_SERVER_IMPLEMENTATION_SUMMARY.md \
  ERROR_HANDLING_GRACEFUL_DEGRADATION_IMPLEMENTATION_SUMMARY.md \
  FINAL_AUTHENTICATION_FIX_SUMMARY.md \
  FRONTEND_BACKEND_CONNECTION_FIX.md \
  GPU_COMPUTE_OFFLOADER_IMPLEMENTATION_SUMMARY.md \
  LOGIN_HANGING_FIX_SUMMARY.md \
  LONG_LIVED_TOKEN_FIX_SUMMARY.md \
  MODEL_CACHE_IMPLEMENTATION_SUMMARY.md \
  MODEL_LIBRARY_TIMEOUT_FIX_SUMMARY.md \
  MODEL_ORCHESTRATOR_TEST_IMPLEMENTATION_SUMMARY.md \
  PERFORMANCE_METRICS_IMPLEMENTATION_SUMMARY.md \
  RATE_LIMITING_ENHANCEMENT_SUMMARY.md \
  RATE_LIMITING_FIX_SUMMARY.md \
  RESOURCE_MONITOR_IMPLEMENTATION_SUMMARY.md \
  SECURITY_RBAC_FIXES_SUMMARY.md \
  SERVER_ISSUES_FIX_SUMMARY.md \
  SESSION_PERSISTENCE_FIX_SUMMARY.md \
  TASK_11_TESTING_IMPLEMENTATION_SUMMARY.md \
  task_12_2_implementation_summary.md \
  TASK_13_INTEGRATION_SUMMARY.md \
  TASK_4_IMPLEMENTATION_SUMMARY.md \
  TASK_5_IMPLEMENTATION_SUMMARY.md \
  TINYLLAMA_IMPLEMENTATION_SUMMARY.md \
  CONSOLE_ERROR_FIXES_COMPLETE.md \
  CONSOLE_ERROR_FIX_SUMMARY.md \
  ; do
  mv_if "docs/$f" "docs/archive/$f"
done

# Root-level docs to archive
mv_if AUTHENTICATION_AUDIT_REPORT.md docs/archive/AUTHENTICATION_AUDIT_REPORT.md
mv_if AUTH_SYSTEM_AUDIT_COMPLETE.md docs/archive/AUTH_SYSTEM_AUDIT_COMPLETE.md
mv_if STARTUP_GUIDE_UPDATE.md docs/archive/STARTUP_GUIDE_UPDATE.md

echo "Docs reorganization completed. Review changes and update links if needed."

