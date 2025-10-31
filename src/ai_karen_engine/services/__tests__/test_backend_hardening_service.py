"""
Unit tests for Backend Hardening Service
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from ..backend_hardening_service import BackendHardeningService, HardeningFix
from ...core.services.base import ServiceConfig


class TestBackendHardeningService:
    """Test cases for BackendHardeningService."""
    
    @pytest.fixture
    def service(self):
        """Create a test service instance."""
        config = ServiceConfig(
            name="test_hardening",
            enabled=True,
            config={
                "target_directories": ["test_src"],
                "backup_directory": "test_backups",
                "dry_run": True  # Don't modify files during tests
            }
        )
        return BackendHardeningService(config)
    
    @pytest.fixture
    def temp_file(self):
        """Create a temporary file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
def test_function():
    # TODO: Implement this function
    raise NotImplementedError("Feature not implemented")
    
def authenticate_user(username, password):
    if username == "admin" and password == "password":
        return True
    return False

def debug_function():
    print("Debug: processing data")
    import pdb; pdb.set_trace()
    
API_BASE = "http://localhost:8000/api"
ADMIN_EMAIL = "admin@example.com"
""")
            temp_path = Path(f.name)
        
        yield temp_path
        
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, service):
        """Test service initialization."""
        await service.initialize()
        assert service.backup_directory.exists()
    
    @pytest.mark.asyncio
    async def test_health_check(self, service):
        """Test health check functionality."""
        await service.initialize()
        health_status = await service.health_check()
        assert health_status is True
    
    def test_fix_notimplementederror_stubs(self, service, temp_file):
        """Test fixing NotImplementedError stubs."""
        fixes = service._fix_notimplementederror_stubs(temp_file)
        
        assert len(fixes) > 0
        assert any(fix.fix_type == "notimplementederror_fix" for fix in fixes)
        assert any("NotImplementedError" in fix.original_code for fix in fixes)
    
    def test_fix_placeholder_credentials(self, service, temp_file):
        """Test fixing placeholder credentials."""
        fixes = service._fix_placeholder_credentials(temp_file)
        
        assert len(fixes) > 0
        assert any(fix.fix_type == "placeholder_credentials" for fix in fixes)
        assert any("admin@example.com" in fix.original_code for fix in fixes)
    
    def test_fix_hardcoded_urls(self, service, temp_file):
        """Test fixing hardcoded URLs."""
        fixes = service._fix_hardcoded_urls(temp_file)
        
        assert len(fixes) > 0
        assert any(fix.fix_type == "hardcoded_urls" for fix in fixes)
        assert any("localhost:8000" in fix.original_code for fix in fixes)
    
    def test_fix_debug_code(self, service, temp_file):
        """Test removing debug code."""
        fixes = service._fix_debug_code(temp_file)
        
        assert len(fixes) > 0
        assert any(fix.fix_type == "debug_code_removal" for fix in fixes)
        assert any("pdb.set_trace" in fix.original_code for fix in fixes)
    
    def test_fix_error_handling(self, service, temp_file):
        """Test improving error handling."""
        # Create a file with bare except clause
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
try:
    risky_operation()
except:
    pass
""")
            temp_path = Path(f.name)
        
        try:
            fixes = service._fix_error_handling(temp_path)
            
            assert len(fixes) > 0
            assert any(fix.fix_type == "error_handling_improvement" for fix in fixes)
            assert any("except:" in fix.original_code for fix in fixes)
        finally:
            if temp_path.exists():
                temp_path.unlink()
    
    @pytest.mark.asyncio
    async def test_harden_backend_services(self, service):
        """Test the main hardening process."""
        # Create a temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_src = temp_path / "test_src"
            test_src.mkdir()
            
            # Create test files
            test_file = test_src / "test_module.py"
            test_file.write_text("""
def test_function():
    raise NotImplementedError("Not implemented")
    
ADMIN_EMAIL = "admin@example.com"
API_URL = "http://localhost:8000"
""")
            
            # Update service config
            service.target_directories = [str(test_src)]
            service.backup_directory = temp_path / "backups"
            
            await service.initialize()
            fixes = await service.harden_backend_services()
            
            assert len(fixes) > 0
            assert len(service.fixes_applied) > 0
    
    def test_generate_hardening_report(self, service):
        """Test hardening report generation."""
        # Add some mock fixes
        service.fixes_applied = [
            HardeningFix(
                file_path="test.py",
                line_number=1,
                original_code="raise NotImplementedError",
                fixed_code="return None",
                fix_type="notimplementederror_fix",
                description="Fixed NotImplementedError"
            ),
            HardeningFix(
                file_path="test.py",
                line_number=2,
                original_code="admin@example.com",
                fixed_code="os.getenv('ADMIN_EMAIL')",
                fix_type="placeholder_credentials",
                description="Fixed placeholder email"
            )
        ]
        
        report = service.generate_hardening_report()
        
        assert report["total_fixes"] == 2
        assert "notimplementederror_fix" in report["fixes_by_type"]
        assert "placeholder_credentials" in report["fixes_by_type"]
        assert report["files_modified"] == 1
        assert len(report["fixes"]) == 2
    
    def test_ui_page_implementation_generation(self, service):
        """Test UI page implementation generation."""
        workflows_impl = service._generate_workflows_implementation()
        white_label_impl = service._generate_white_label_implementation()
        
        assert "render_page" in workflows_impl
        assert "Workflow Automation" in workflows_impl
        assert "require_role" in workflows_impl
        
        assert "render_page" in white_label_impl
        assert "White Label Branding" in white_label_impl
        assert "require_role" in white_label_impl
    
    def test_placeholder_fix_methods(self, service):
        """Test specific placeholder fix methods."""
        # Test semantic search fix
        line = 'raise NotImplementedError("semantic_search_df is not implemented yet.")'
        fixed = service._fix_semantic_search_placeholder(line)
        assert "semantic_search_df is not implemented yet" not in fixed
        assert "logger.warning" in fixed
        
        # Test notification fix
        line = 'raise NotImplementedError'
        fixed = service._fix_notification_placeholder(line)
        assert "NotImplementedError" not in fixed
        assert "return True" in fixed
        
        # Test provider method fix
        line = 'raise NotImplementedError'
        fixed = service._fix_provider_method_placeholder(line)
        assert "NotImplementedError" not in fixed
        assert "RuntimeError" in fixed
    
    def test_backup_functionality(self, service, temp_file):
        """Test file backup functionality."""
        service.dry_run = False
        await service.initialize()
        
        backup_path = service._backup_file(temp_file)
        
        assert backup_path.exists()
        assert backup_path.read_text() == temp_file.read_text()
        
        # Cleanup
        if backup_path.exists():
            backup_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__])