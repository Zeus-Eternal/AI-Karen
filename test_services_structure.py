#!/usr/bin/env python3
"""
Test script to validate the services architecture structure.
This script checks if all required files and directories exist without importing them.
"""

import os
import json
from pathlib import Path

def test_directory_structure():
    """Test if all required directories exist."""
    print("🔍 Testing directory structure...")
    
    base_path = Path("src/ai_karen_engine/services")
    required_dirs = [
        "ai_orchestrator",
        "cognitive", 
        "knowledge",
        "tools",
        "memory",
        "models",
        "infra",
        "monitoring",
        "audit",
        "orchestration",
        "optimization",
        "agents",
        "extensions",
        "core"
    ]
    
    missing_dirs = []
    for dir_name in required_dirs:
        dir_path = base_path / dir_name
        if not dir_path.exists():
            missing_dirs.append(dir_name)
        else:
            # Check if internal subdir exists
            internal_path = dir_path / "internal"
            if not internal_path.exists():
                missing_dirs.append(f"{dir_name}/internal")
    
    if missing_dirs:
        print(f"❌ Missing directories: {', '.join(missing_dirs)}")
        return False
    else:
        print("✅ All required directories exist")
        return True

def test_facade_files():
    """Test if all required facade files exist."""
    print("\n🔍 Testing facade files...")
    
    base_path = Path("src/ai_karen_engine/services")
    facade_files = {
        "memory": ["unified_memory_service.py", "neurovault_integration_service.py", "working_memory.py", "episodic_memory.py"],
        "models": ["model_orchestrator_service.py", "model_registry.py", "provider_registry.py", "llm_router.py", 
                  "intelligent_model_router.py", "model_library_service.py", "model_download_manager.py", 
                  "model_availability_handler.py", "provider_health_monitor.py"],
        "monitoring": ["structured_logging_service.py", "metrics_service.py", "correlation_service.py"],
        "infra": ["database_connection_manager.py", "redis_connection_manager.py", "model_connection_manager.py",
                  "integrated_cache_system.py", "smart_cache_manager.py", "database_query_cache_service.py",
                  "database_health_monitor.py", "connection_health_manager.py"],
        "audit": ["audit_logger.py", "training_audit_logger.py", "audit_cleanup.py", "audit_deduplication_service.py",
                  "privacy_compliance.py", "auth_data_cleanup_service.py"],
        "orchestration": ["intelligent_response_controller.py", "progressive_response_streamer.py", 
                          "conversation_service.py", "conversation_tracker.py", "web_ui_api.py",
                          "chat_transformation_utils.py", "ag_ui_memory_interface.py", "user_service.py",
                          "auth_service.py", "auth_utils.py", "webhook_service.py"],
        "optimization": ["optimization_configuration_manager.py", "optimization_integration_orchestrator.py",
                         "priority_processing_system.py", "resource_allocation_system.py", 
                         "graceful_degradation_coordinator.py", "fallback_provider.py", 
                         "timeout_performance_handler.py", "error_recovery_system.py", "error_response_service.py"],
        "agents": ["agent_orchestrator.py", "agent_task_router.py", "agent_reasoning.py", "agent_registry.py",
                   "agent_executor.py", "agent_memory.py", "agent_tool_broker.py", "agent_safety.py",
                   "agent_response_composer.py", "agent_monitor.py", "agent_memory_fusion.py", 
                   "agent_echo_core.py", "agent_ui_integration.py"],
        "extensions": ["extension_registry.py", "extension_loader.py", "extension_executor.py", 
                       "extension_monitor.py", "extension_config.py", "extension_auth.py", 
                       "extension_permissions.py", "extension_rbac.py", "extension_marketplace.py",
                       "extension_api.py", "extension_health_monitor.py", "extension_error_recovery.py",
                       "extension_tenant_access.py", "extension_environment_config.py", 
                       "extension_config_validator.py", "extension_config_hot_reload.py", 
                       "extension_config_integration.py", "extension_alerting_system.py"],
        "tools": ["contracts.py", "core_tools.py", "copilot_tools.py", "registry.py"],
        "ai_orchestrator": ["ai_orchestrator.py", "flow_manager.py", "decision_engine.py", 
                            "prompt_manager.py", "context_manager.py"],
        "cognitive": ["working_memory.py", "episodic_memory.py"],
        "knowledge": ["knowledge_graph_service.py", "semantic_search_service.py", "knowledge_extraction_service.py",
                     "knowledge_base_manager.py", "knowledge_integration_service.py"]
    }
    
    missing_files = []
    for domain, files in facade_files.items():
        for file_name in files:
            file_path = base_path / domain / file_name
            if not file_path.exists():
                missing_files.append(str(file_path))
    
    if missing_files:
        print(f"❌ Missing facade files: {', '.join(missing_files)}")
        return False
    else:
        print("✅ All required facade files exist")
        return True

def test_init_files():
    """Test if all __init__.py files exist."""
    print("\n🔍 Testing __init__.py files...")
    
    base_path = Path("src/ai_karen_engine/services")
    required_dirs = [
        "ai_orchestrator",
        "cognitive", 
        "knowledge",
        "tools",
        "memory",
        "models",
        "infra",
        "monitoring",
        "audit",
        "orchestration",
        "optimization",
        "agents",
        "extensions",
        "core"
    ]
    
    missing_init_files = []
    for dir_name in required_dirs:
        init_path = base_path / dir_name / "__init__.py"
        if not init_path.exists():
            missing_init_files.append(str(init_path))
        
        # Check internal __init__.py
        internal_init_path = base_path / dir_name / "internal" / "__init__.py"
        if not internal_init_path.exists():
            missing_init_files.append(str(internal_init_path))
    
    if missing_init_files:
        print(f"❌ Missing __init__.py files: {', '.join(missing_init_files)}")
        return False
    else:
        print("✅ All required __init__.py files exist")
        return True

def test_imports_in_init_files():
    """Test if __init__.py files have the correct imports."""
    print("\n🔍 Testing imports in __init__.py files...")
    
    base_path = Path("src/ai_karen_engine/services")
    required_dirs = [
        "memory",
        "models",
        "monitoring",
        "agents",
        "extensions"
    ]
    
    issues = []
    for dir_name in required_dirs:
        init_path = base_path / dir_name / "__init__.py"
        if init_path.exists():
            with open(init_path, 'r') as f:
                content = f.read()
                
            # Check if the file imports from the correct facade modules
            if dir_name == "memory" and "from .unified_memory_service import" not in content:
                issues.append(f"{init_path} doesn't import from unified_memory_service")
            elif dir_name == "models" and "from .model_orchestrator_service import" not in content:
                issues.append(f"{init_path} doesn't import from model_orchestrator_service")
            elif dir_name == "monitoring" and "from .structured_logging_service import" not in content:
                issues.append(f"{init_path} doesn't import from structured_logging_service")
            elif dir_name == "agents" and "from .agent_orchestrator import" not in content:
                issues.append(f"{init_path} doesn't import from agent_orchestrator")
            elif dir_name == "extensions" and "from .extension_registry import" not in content:
                issues.append(f"{init_path} doesn't import from extension_registry")
    
    if issues:
        print(f"❌ Import issues: {', '.join(issues)}")
        return False
    else:
        print("✅ All __init__.py files have correct imports")
        return True

def test_services_init_file():
    """Test if the main services/__init__.py file has the correct structure."""
    print("\n🔍 Testing services/__init__.py file...")
    
    init_path = Path("src/ai_karen_engine/services/__init__.py")
    if not init_path.exists():
        print("❌ services/__init__.py file doesn't exist")
        return False
    
    with open(init_path, 'r') as f:
        content = f.read()
    
    # Check if it imports from the new facade modules
    required_imports = [
        "from ai_karen_engine.services.memory.unified_memory_service import UnifiedMemoryService",
        "from ai_karen_engine.services.models.model_orchestrator_service import ModelOrchestratorService",
        "from ai_karen_engine.services.monitoring.structured_logging_service import StructuredLoggingService",
        "from ai_karen_engine.services.monitoring.metrics_service import MetricsService",
        "from ai_karen_engine.services.monitoring.correlation_service import CorrelationService",
        "from ai_karen_engine.services.agents.agent_orchestrator import AgentOrchestrator",
        "from ai_karen_engine.services.extensions.extension_registry import ExtensionRegistry",
        "from ai_karen_engine.services.extensions.extension_loader import ExtensionLoader"
    ]
    
    missing_imports = []
    for import_statement in required_imports:
        if import_statement not in content:
            missing_imports.append(import_statement)
    
    if missing_imports:
        print(f"❌ Missing imports in services/__init__.py: {', '.join(missing_imports)}")
        return False
    else:
        print("✅ services/__init__.py has all required imports")
        return True

def test_memory_service_imports():
    """Test if memory_routes.py has been updated with the new imports."""
    print("\n🔍 Testing memory_routes.py imports...")
    
    routes_path = Path("src/ai_karen_engine/api_routes/memory_routes.py")
    if not routes_path.exists():
        print("❌ memory_routes.py file doesn't exist")
        return False
    
    with open(routes_path, 'r') as f:
        content = f.read()
    
    # Check if it uses the new facade imports
    required_imports = [
        "from ai_karen_engine.services.memory.unified_memory_service import UnifiedMemoryService",
        "from ai_karen_engine.services.monitoring.structured_logging_service import StructuredLoggingService",
        "from ai_karen_engine.services.monitoring.metrics_service import MetricsService",
        "from ai_karen_engine.services.monitoring.correlation_service import CorrelationService"
    ]
    
    missing_imports = []
    for import_statement in required_imports:
        if import_statement not in content:
            missing_imports.append(import_statement)
    
    if missing_imports:
        print(f"❌ Missing imports in memory_routes.py: {', '.join(missing_imports)}")
        return False
    else:
        print("✅ memory_routes.py has all required imports")
        return True

def main():
    """Run all tests."""
    print("🧪 Testing Services Architecture Structure")
    print("=" * 50)
    
    tests = [
        test_directory_structure,
        test_facade_files,
        test_init_files,
        test_imports_in_init_files,
        test_services_init_file,
        test_memory_service_imports
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ All {total} tests passed")
        return True
    else:
        print(f"❌ {passed}/{total} tests passed")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)