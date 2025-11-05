"""
Startup check module for AI Karen Engine.
Ensures system is properly initialized before starting the main application.
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class StartupChecker:
    """
    Performs startup checks and ensures system readiness.
    """
    
    def __init__(self):
        self.logger = logger
        self.models_dir = Path(os.getenv("KARI_MODEL_DIR", "models"))
        self.required_files = [
            "config.json",
            "config/llm_profiles.yml",
            "config/memory.yml",
        ]
        self.required_dirs = [
            "data",
            "logs", 
            "extensions",
            "plugins",
        ]
    
    async def perform_startup_checks(self, auto_fix: bool = True) -> Tuple[bool, List[str]]:
        """
        Perform comprehensive startup checks.
        
        Args:
            auto_fix: Automatically fix issues if possible
            
        Returns:
            Tuple of (all_checks_passed, list_of_issues)
        """
        issues = []
        
        self.logger.info("🔍 Performing startup checks...")
        
        # Check 1: Required directories
        dir_issues = await self._check_required_directories(auto_fix)
        issues.extend(dir_issues)
        
        # Check 2: Configuration files
        config_issues = await self._check_configuration_files(auto_fix)
        issues.extend(config_issues)
        
        # Check 3: Models availability
        model_issues = await self._check_models_availability(auto_fix)
        issues.extend(model_issues)
        
        # Check 4: Database files
        db_issues = await self._check_database_files(auto_fix)
        issues.extend(db_issues)
        
        # Check 5: Python dependencies
        dep_issues = await self._check_python_dependencies()
        issues.extend(dep_issues)
        
        # Check 6: Permissions
        perm_issues = await self._check_permissions()
        issues.extend(perm_issues)
        
        all_passed = len(issues) == 0
        
        if all_passed:
            self.logger.info("✅ All startup checks passed!")
        else:
            self.logger.warning(f"⚠️ Startup checks found {len(issues)} issues")
            for issue in issues:
                self.logger.warning(f"   - {issue}")
        
        return all_passed, issues
    
    async def _check_required_directories(self, auto_fix: bool) -> List[str]:
        """Check that all required directories exist."""
        issues = []
        
        for dir_name in self.required_dirs:
            dir_path = Path(dir_name)
            if not dir_path.exists():
                if auto_fix:
                    try:
                        dir_path.mkdir(parents=True, exist_ok=True)
                        self.logger.info(f"✅ Created missing directory: {dir_name}")
                    except Exception as e:
                        issues.append(f"Failed to create directory {dir_name}: {e}")
                else:
                    issues.append(f"Missing required directory: {dir_name}")
        
        # Check models directory
        if not self.models_dir.exists():
            if auto_fix:
                try:
                    self.models_dir.mkdir(parents=True, exist_ok=True)
                    self.logger.info(f"✅ Created models directory: {self.models_dir}")
                except Exception as e:
                    issues.append(f"Failed to create models directory: {e}")
            else:
                issues.append(f"Missing models directory: {self.models_dir}")
        
        return issues
    
    async def _check_configuration_files(self, auto_fix: bool) -> List[str]:
        """Check that required configuration files exist."""
        issues = []
        
        for config_file in self.required_files:
            config_path = Path(config_file)
            if not config_path.exists():
                if auto_fix:
                    # Trigger system initialization to create missing configs
                    try:
                        from ai_karen_engine.core.initialization import initialize_system
                        self.logger.info(f"🔧 Initializing system to create missing config: {config_file}")
                        await initialize_system()
                        break  # initialization will create all configs
                    except Exception as e:
                        issues.append(f"Failed to initialize system for config {config_file}: {e}")
                else:
                    issues.append(f"Missing configuration file: {config_file}")
        
        return issues
    
    async def _check_models_availability(self, auto_fix: bool) -> List[str]:
        """Check that at least some models are available."""
        issues = []
        
        # Check for any model files
        model_files = []
        if self.models_dir.exists():
            model_files.extend(list(self.models_dir.rglob("*.gguf")))
            model_files.extend(list(self.models_dir.rglob("*.bin")))
        
        # Check for transformers cache
        transformers_cache = self.models_dir / "transformers"
        has_transformers = transformers_cache.exists() and any(transformers_cache.iterdir())
        
        if not model_files and not has_transformers:
            if auto_fix:
                try:
                    from ai_karen_engine.core.initialization import initialize_system
                    self.logger.info("📥 No models found, initializing system to download default models...")
                    await initialize_system()
                except Exception as e:
                    issues.append(f"No models available and failed to initialize: {e}")
            else:
                issues.append("No models available - run system initialization to download default models")
        else:
            self.logger.info(f"✅ Found {len(model_files)} model files and transformers cache: {has_transformers}")
        
        return issues
    
    async def _check_database_files(self, auto_fix: bool) -> List[str]:
        """Check that database files exist or can be created."""
        issues = []
        
        db_files = [
            "auth.db",
            "auth_sessions.db",
            "data/kari_automation.db"
        ]
        
        for db_file in db_files:
            db_path = Path(db_file)
            if not db_path.exists():
                if auto_fix:
                    try:
                        db_path.parent.mkdir(parents=True, exist_ok=True)
                        db_path.touch()
                        self.logger.info(f"✅ Created database file: {db_file}")
                    except Exception as e:
                        issues.append(f"Failed to create database {db_file}: {e}")
                else:
                    issues.append(f"Missing database file: {db_file}")
        
        return issues
    
    async def _check_python_dependencies(self) -> List[str]:
        """Check that critical Python dependencies are available."""
        issues = []
        
        critical_deps = [
            ("pydantic", "Pydantic"),
            ("fastapi", "FastAPI"),
            ("transformers", "Transformers"),
            ("torch", "PyTorch"),
        ]
        
        for module_name, display_name in critical_deps:
            try:
                __import__(module_name)
            except ImportError:
                issues.append(f"Missing critical dependency: {display_name} ({module_name})")
        
        # Check optional dependencies
        optional_deps = [
            ("spacy", "spaCy"),
            ("sentence_transformers", "Sentence Transformers"),
        ]
        
        missing_optional = []
        for module_name, display_name in optional_deps:
            try:
                __import__(module_name)
            except ImportError:
                missing_optional.append(display_name)
        
        if missing_optional:
            self.logger.info(f"ℹ️ Optional dependencies not available: {', '.join(missing_optional)}")
        
        return issues
    
    async def _check_permissions(self) -> List[str]:
        """Check that the application has necessary permissions."""
        issues = []
        
        # Check write permissions for key directories
        write_dirs = [
            Path("data"),
            Path("logs"),
            self.models_dir,
        ]
        
        for dir_path in write_dirs:
            if dir_path.exists():
                try:
                    # Test write permission
                    test_file = dir_path / ".write_test"
                    test_file.touch()
                    test_file.unlink()
                except Exception as e:
                    issues.append(f"No write permission for {dir_path}: {e}")
        
        return issues
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status information."""
        status = {
            "startup_checks_passed": False,
            "issues": [],
            "directories": {},
            "models": {},
            "dependencies": {},
            "configuration": {}
        }
        
        # Run startup checks
        checks_passed, issues = await self.perform_startup_checks(auto_fix=False)
        status["startup_checks_passed"] = checks_passed
        status["issues"] = issues
        
        # Directory status
        for dir_name in self.required_dirs:
            dir_path = Path(dir_name)
            status["directories"][dir_name] = {
                "exists": dir_path.exists(),
                "writable": self._is_writable(dir_path) if dir_path.exists() else False
            }
        
        # Models status
        if self.models_dir.exists():
            model_files = list(self.models_dir.rglob("*.gguf")) + list(self.models_dir.rglob("*.bin"))
            status["models"] = {
                "directory_exists": True,
                "model_count": len(model_files),
                "models": [f.name for f in model_files[:5]]  # First 5 models
            }
        else:
            status["models"] = {"directory_exists": False, "model_count": 0}
        
        # Dependencies status
        deps_to_check = [
            "pydantic", "fastapi", "transformers", "torch", "spacy", "sentence_transformers"
        ]
        
        for dep in deps_to_check:
            try:
                __import__(dep)
                status["dependencies"][dep] = True
            except ImportError:
                status["dependencies"][dep] = False
        
        # Configuration status
        for config_file in self.required_files:
            config_path = Path(config_file)
            status["configuration"][config_file] = config_path.exists()
        
        return status
    
    def _is_writable(self, path: Path) -> bool:
        """Check if a path is writable."""
        try:
            test_file = path / ".write_test"
            test_file.touch()
            test_file.unlink()
            return True
        except Exception:
            return False


# Convenience function
async def perform_startup_checks(auto_fix: bool = True) -> Tuple[bool, List[str]]:
    """
    Perform startup checks for the AI Karen Engine.
    
    Args:
        auto_fix: Automatically fix issues if possible
        
    Returns:
        Tuple of (all_checks_passed, list_of_issues)
    """
    checker = StartupChecker()
    return await checker.perform_startup_checks(auto_fix)


# NOTE: Auto-check on import was removed due to race conditions.
# Applications should explicitly call perform_startup_checks() during their startup sequence.
# Example:
#
#   @app.on_event("startup")
#   async def startup():
#       from ai_karen_engine.core.startup_check import perform_startup_checks
#       passed, issues = await perform_startup_checks(auto_fix=True)
#       if not passed:
#           logger.error(f"Startup checks failed: {issues}")
#       logger.info("Startup checks complete")
#
# For migration from auto-check, set KARI_SKIP_STARTUP_CHECK=true in your environment.