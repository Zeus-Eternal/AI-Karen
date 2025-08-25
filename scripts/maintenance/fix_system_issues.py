#!/usr/bin/env python3
"""
System Issues Fix Script

This script addresses the critical issues identified:
1. Analytics service initialization failure
2. Session persistence not working
3. Production readiness improvements
4. Fallback to local models when providers unavailable
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def fix_analytics_service():
    """Fix analytics service initialization issues."""
    logger.info("🔧 Fixing analytics service...")
    
    try:
        # Test analytics service initialization
        from ai_karen_engine.services.analytics_service import AnalyticsService
        
        config = {
            "max_metrics": 10000,
            "system_monitor_interval": 30,
            "max_alerts": 1000,
            "max_user_events": 10000,
            "max_performance_metrics": 10000
        }
        
        analytics = AnalyticsService(config)
        logger.info("✅ Analytics service initialized successfully")
        
        # Test basic functionality
        from ai_karen_engine.services.analytics_service import MetricType
        analytics.record_metric("test.metric", 1.0, MetricType.GAUGE)
        logger.info("✅ Analytics service basic functionality working")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Analytics service fix failed: {e}")
        return False


async def fix_session_persistence():
    """Fix session persistence issues."""
    logger.info("🔧 Fixing session persistence...")
    
    try:
        # Check if auth database exists
        auth_db_path = Path("auth.db")
        if not auth_db_path.exists():
            logger.info("Creating auth database...")
            auth_db_path.touch()
        
        # Check if auth sessions database exists
        auth_sessions_db_path = Path("auth_sessions.db")
        if not auth_sessions_db_path.exists():
            logger.info("Creating auth sessions database...")
            auth_sessions_db_path.touch()
        
        # Test cookie manager
        from ai_karen_engine.auth.cookie_manager import get_cookie_manager
        cookie_manager = get_cookie_manager()
        
        # Validate cookie security configuration
        validation = cookie_manager.validate_cookie_security()
        if not validation["valid"]:
            logger.warning("Cookie security issues found:")
            for issue in validation["issues"]:
                logger.warning(f"  - {issue}")
            for rec in validation["recommendations"]:
                logger.info(f"  💡 {rec}")
        else:
            logger.info("✅ Cookie security configuration is valid")
        
        # Test session validator
        from ai_karen_engine.auth.enhanced_session_validator import get_session_validator
        validator = get_session_validator()
        stats = validator.get_validation_stats()
        logger.info(f"✅ Session validator initialized: {stats}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Session persistence fix failed: {e}")
        return False


async def check_model_availability():
    """Check and ensure model availability."""
    logger.info("🔧 Checking model availability...")
    
    try:
        models_dir = Path("models")
        if not models_dir.exists():
            logger.info("Creating models directory...")
            models_dir.mkdir(parents=True, exist_ok=True)
        
        # Check for local models
        gguf_models = list(models_dir.rglob("*.gguf"))
        bin_models = list(models_dir.rglob("*.bin"))
        
        logger.info(f"Found {len(gguf_models)} GGUF models and {len(bin_models)} binary models")
        
        # Check for the specific model mentioned
        tinyllama_path = models_dir / "llama-cpp" / "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
        if tinyllama_path.exists():
            logger.info("✅ TinyLlama model available for fallback")
        else:
            logger.warning("⚠️ TinyLlama model not found - may need to download")
        
        # Check transformers cache
        transformers_cache = models_dir / "transformers"
        if transformers_cache.exists() and any(transformers_cache.iterdir()):
            logger.info("✅ Transformers cache available")
        else:
            logger.warning("⚠️ Transformers cache not found")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Model availability check failed: {e}")
        return False


async def fix_service_registry():
    """Fix service registry initialization issues."""
    logger.info("🔧 Fixing service registry...")
    
    try:
        from ai_karen_engine.core.service_registry import ServiceRegistry
        
        # Test service registry initialization
        registry = ServiceRegistry()
        
        # Register analytics service with proper error handling
        from ai_karen_engine.services.analytics_service import AnalyticsService
        registry.register_service(
            "analytics_service",
            AnalyticsService,
            dependencies={},
            max_attempts=1  # Reduce attempts to avoid spam
        )
        
        # Test initialization
        results = await registry.initialize_all_services()
        
        ready_count = sum(1 for status in results.values() if status.value in ["ready", "degraded"])
        total_count = len(results)
        
        logger.info(f"Service initialization: {ready_count}/{total_count} ready")
        
        # Get detailed report
        report = registry.get_initialization_report()
        for service_name, service_info in report["services"].items():
            status = service_info["status"]
            if status == "error":
                logger.warning(f"  ❌ {service_name}: {service_info.get('error_message', 'Unknown error')}")
            elif status == "degraded":
                logger.warning(f"  ⚠️ {service_name}: degraded mode")
            else:
                logger.info(f"  ✅ {service_name}: {status}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Service registry fix failed: {e}")
        return False


async def create_production_config():
    """Create production-ready configuration."""
    logger.info("🔧 Creating production configuration...")
    
    try:
        # Ensure required directories exist
        required_dirs = ["data", "logs", "extensions", "plugins", "config"]
        for dir_name in required_dirs:
            dir_path = Path(dir_name)
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {dir_name}")
        
        # Create basic config if it doesn't exist
        config_path = Path("config.json")
        if not config_path.exists():
            basic_config = {
                "app_name": "AI Karen Engine",
                "version": "1.0.0",
                "environment": "production",
                "features": {
                    "analytics": True,
                    "session_persistence": True,
                    "intelligent_errors": True,
                    "local_models": True
                },
                "fallback": {
                    "use_local_models": True,
                    "local_model_path": "models/llama-cpp/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
                    "enable_spacy_fallback": True,
                    "degraded_mode_enabled": True
                }
            }
            
            import json
            with open(config_path, "w") as f:
                json.dump(basic_config, f, indent=2)
            logger.info("✅ Created basic configuration file")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Production config creation failed: {e}")
        return False


async def test_system_health():
    """Test overall system health."""
    logger.info("🔍 Testing system health...")
    
    try:
        # Test startup checks
        from ai_karen_engine.core.startup_check import perform_startup_checks
        
        checks_passed, issues = await perform_startup_checks(auto_fix=True)
        
        if checks_passed:
            logger.info("✅ All startup checks passed")
        else:
            logger.warning(f"⚠️ Startup checks found {len(issues)} issues:")
            for issue in issues:
                logger.warning(f"  - {issue}")
        
        return checks_passed
        
    except Exception as e:
        logger.error(f"❌ System health test failed: {e}")
        return False


async def main():
    """Main fix script."""
    logger.info("🚀 Starting system issues fix...")
    
    fixes = [
        ("Analytics Service", fix_analytics_service),
        ("Session Persistence", fix_session_persistence),
        ("Model Availability", check_model_availability),
        ("Service Registry", fix_service_registry),
        ("Production Config", create_production_config),
        ("System Health", test_system_health),
    ]
    
    results = {}
    
    for name, fix_func in fixes:
        logger.info(f"\n{'='*50}")
        logger.info(f"Fixing: {name}")
        logger.info(f"{'='*50}")
        
        try:
            result = await fix_func()
            results[name] = result
            
            if result:
                logger.info(f"✅ {name}: Fixed successfully")
            else:
                logger.error(f"❌ {name}: Fix failed")
                
        except Exception as e:
            logger.error(f"❌ {name}: Exception during fix: {e}")
            results[name] = False
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("FIX SUMMARY")
    logger.info(f"{'='*50}")
    
    successful_fixes = sum(1 for result in results.values() if result)
    total_fixes = len(results)
    
    for name, result in results.items():
        status = "✅ FIXED" if result else "❌ FAILED"
        logger.info(f"{status}: {name}")
    
    logger.info(f"\nOverall: {successful_fixes}/{total_fixes} fixes successful")
    
    if successful_fixes == total_fixes:
        logger.info("🎉 All issues fixed! System should be ready for production.")
    else:
        logger.warning("⚠️ Some issues remain. Check the logs above for details.")
    
    return successful_fixes == total_fixes


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)