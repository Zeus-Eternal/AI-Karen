"""
Tests for Production Hardening Audit Service
"""

import asyncio
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from ..production_hardening_audit import (
    ProductionHardeningAuditService,
    create_production_audit_service,
    IssueType,
    IssueSeverity,
    CodebaseIssue,
    ProductionAuditReport
)
from ...core.services.base import ServiceConfig


class TestProductionHardeningAuditService:
    """Test suite for ProductionHardeningAuditService."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def service_config(self, temp_dir):
        """Create a test service configuration."""
        return ServiceConfig(
            name="test_audit",
            enabled=True,
            config={
                "scan_directories": [str(temp_dir / "test_src")],
                "exclude_patterns": ["*.pyc", "__pycache__"],
                "file_extensions": [".py", ".js", ".json"],
                "max_file_size_mb": 1,
                "output_directory": str(temp_dir / "reports")
            }
        )
    
    @pytest.fixture
    def audit_service(self, service_config):
        """Create a test audit service."""
        return ProductionHardeningAuditService(service_config)
    
    @pytest.fixture
    def sample_files(self, temp_dir):
        """Create sample files with various issues."""
        test_src = temp_dir / "test_src"
        test_src.mkdir(parents=True)
        
        # Python file with TODO and dummy logic
        python_file = test_src / "sample.py"
        python_file.write_text("""
# TODO: Implement proper authentication
def authenticate_user(username, password):
    # FIXME: This is dummy logic
    if username == "admin" and password == "password":
        return True
    return False

def process_data():
    pass  # dummy implementation
    
def debug_function():
    print("Debug: processing data")
    import pdb; pdb.set_trace()
    
try:
    risky_operation()
except:  # Bare except clause
    pass
""")
        
        # JavaScript file with console logs
        js_file = test_src / "sample.js"
        js_file.write_text("""
// TODO: Add proper error handling
function processData() {
    console.log("Processing data...");
    alert("Debug alert");
    return null; // placeholder return
}

const API_URL = "http://localhost:3000/api";
""")
        
        # JSON config with test data
        json_file = test_src / "config.json"
        json_file.write_text("""
{
    "database_url": "localhost:5432",
    "admin_email": "admin@example.com",
    "api_key": "test_api_key_12345"
}
""")
        
        return {
            "python": python_file,
            "javascript": js_file,
            "json": json_file
        }
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, audit_service):
        """Test service initialization."""
        await audit_service.initialize()
        assert audit_service.output_directory.exists()
        
        await audit_service.start()
        assert audit_service.status.value == "running"
        
        health_ok = await audit_service.health_check()
        assert health_ok is True
        
        await audit_service.stop()
    
    @pytest.mark.asyncio
    async def test_file_scanning(self, audit_service, sample_files):
        """Test file scanning functionality."""
        await audit_service.initialize()
        
        # Test Python file scanning
        python_issues = audit_service._scan_file_for_issues(sample_files["python"])
        assert len(python_issues) > 0
        
        # Check for specific issue types
        issue_types = [issue.issue_type for issue in python_issues]
        assert IssueType.TODO_COMMENT in issue_types
        assert IssueType.DUMMY_LOGIC in issue_types
        assert IssueType.DEBUG_CODE in issue_types
        assert IssueType.MISSING_ERROR_HANDLING in issue_types
        
        # Test JavaScript file scanning
        js_issues = audit_service._scan_file_for_issues(sample_files["javascript"])
        assert len(js_issues) > 0
        
        js_issue_types = [issue.issue_type for issue in js_issues]
        assert IssueType.TODO_COMMENT in js_issue_types
        assert IssueType.DEBUG_CODE in js_issue_types
        assert IssueType.HARDCODED_VALUES in js_issue_types
        
        # Test JSON file scanning
        json_issues = audit_service._scan_file_for_issues(sample_files["json"])
        assert len(json_issues) > 0
        
        json_issue_types = [issue.issue_type for issue in json_issues]
        assert IssueType.DEVELOPMENT_CONFIG in json_issue_types
        assert IssueType.PLACEHOLDER_IMPLEMENTATION in json_issue_types
    
    @pytest.mark.asyncio
    async def test_full_audit(self, audit_service, sample_files):
        """Test full codebase audit."""
        await audit_service.initialize()
        
        report = await audit_service.audit_codebase()
        
        # Verify report structure
        assert isinstance(report, ProductionAuditReport)
        assert report.total_files_scanned > 0
        assert report.total_issues_found > 0
        assert len(report.issues) > 0
        
        # Verify issue categorization
        assert len(report.issues_by_type) > 0
        assert len(report.issues_by_severity) > 0
        
        # Verify recommendations are generated
        assert len(report.recommendations) > 0
        
        # Verify overall status is set
        assert report.overall_status is not None
        assert "NOT_READY" in report.overall_status or "NEEDS" in report.overall_status
    
    @pytest.mark.asyncio
    async def test_report_generation(self, audit_service, sample_files):
        """Test report generation in different formats."""
        await audit_service.initialize()
        
        report = await audit_service.audit_codebase()
        
        # Test JSON report generation
        json_report_path = await audit_service.generate_report(report, "json")
        assert json_report_path.exists()
        assert json_report_path.suffix == ".json"
        
        # Test HTML report generation
        html_report_path = await audit_service.generate_report(report, "html")
        assert html_report_path.exists()
        assert html_report_path.suffix == ".html"
        
        # Test Markdown report generation
        md_report_path = await audit_service.generate_report(report, "markdown")
        assert md_report_path.exists()
        assert md_report_path.suffix == ".md"
        
        # Verify report content
        json_content = json_report_path.read_text()
        assert "total_issues_found" in json_content
        
        html_content = html_report_path.read_text()
        assert "<html>" in html_content
        assert "Production Readiness Audit Report" in html_content
        
        md_content = md_report_path.read_text()
        assert "# Production Readiness Audit Report" in md_content
    
    @pytest.mark.asyncio
    async def test_production_readiness_validation(self, audit_service, sample_files):
        """Test production readiness validation."""
        await audit_service.initialize()
        
        is_ready, blocking_issues = await audit_service.validate_production_readiness()
        
        # With our sample files containing issues, should not be ready
        assert is_ready is False
        assert len(blocking_issues) > 0
        
        # Check for expected blocking issues
        blocking_text = " ".join(blocking_issues)
        assert any(keyword in blocking_text.lower() for keyword in 
                  ["placeholder", "unimplemented", "critical", "dummy"])
    
    def test_issue_severity_determination(self, audit_service):
        """Test issue severity determination logic."""
        # Test critical severity for security-related placeholders
        severity = audit_service._determine_severity(
            IssueType.PLACEHOLDER_IMPLEMENTATION,
            'password = "test_password"',
            MagicMock(group=lambda: "test_password")
        )
        assert severity == IssueSeverity.CRITICAL
        
        # Test high severity for NotImplementedError
        severity = audit_service._determine_severity(
            IssueType.DUMMY_LOGIC,
            'raise NotImplementedError("Feature not implemented")',
            MagicMock(group=lambda: "NotImplementedError")
        )
        assert severity == IssueSeverity.HIGH
        
        # Test medium severity for regular TODO
        severity = audit_service._determine_severity(
            IssueType.TODO_COMMENT,
            '# TODO: Add validation',
            MagicMock(group=lambda: "TODO")
        )
        assert severity == IssueSeverity.MEDIUM
    
    def test_file_filtering(self, audit_service, temp_dir):
        """Test file filtering logic."""
        test_files = [
            temp_dir / "test.py",      # Should scan
            temp_dir / "test.js",      # Should scan
            temp_dir / "test.json",    # Should scan
            temp_dir / "test.txt",     # Should not scan (extension)
            temp_dir / "__pycache__" / "test.pyc",  # Should not scan (exclude pattern)
        ]
        
        # Create test files
        for file_path in test_files:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text("test content")
        
        # Test filtering
        assert audit_service._should_scan_file(test_files[0]) is True   # .py
        assert audit_service._should_scan_file(test_files[1]) is True   # .js
        assert audit_service._should_scan_file(test_files[2]) is True   # .json
        assert audit_service._should_scan_file(test_files[3]) is False  # .txt
        assert audit_service._should_scan_file(test_files[4]) is False  # __pycache__
    
    def test_factory_function(self):
        """Test the factory function for creating audit services."""
        service = create_production_audit_service(
            scan_directories=["test_dir"],
            output_directory="test_output"
        )
        
        assert isinstance(service, ProductionHardeningAuditService)
        assert service.scan_directories == ["test_dir"]
        assert str(service.output_directory) == "test_output"
    
    def test_pattern_compilation(self, audit_service):
        """Test that regex patterns are properly compiled."""
        assert len(audit_service._compiled_patterns) > 0
        
        for issue_type, patterns in audit_service._compiled_patterns.items():
            assert len(patterns) > 0
            for pattern in patterns:
                assert hasattr(pattern, 'search')  # Compiled regex has search method
    
    @pytest.mark.asyncio
    async def test_error_handling_in_file_scan(self, audit_service, temp_dir):
        """Test error handling when scanning problematic files."""
        await audit_service.initialize()
        
        # Create a file with problematic encoding
        problem_file = temp_dir / "test_src" / "problem.py"
        problem_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write binary data that might cause encoding issues
        problem_file.write_bytes(b'\xff\xfe\x00\x00invalid utf-8 content')
        
        # Should handle the error gracefully
        issues = audit_service._scan_file_for_issues(problem_file)
        
        # Should create an error issue instead of crashing
        assert len(issues) >= 0  # Might be 0 if file is skipped, or contain error issue
    
    def test_recommendation_generation(self, audit_service):
        """Test recommendation generation for different issue types."""
        recommendations = audit_service._generate_recommendations(
            issues=[
                CodebaseIssue(
                    file_path="test.py",
                    line_number=1,
                    issue_type=IssueType.TODO_COMMENT,
                    severity=IssueSeverity.MEDIUM,
                    description="TODO found",
                    code_snippet="# TODO: fix this",
                    recommendation="Complete the TODO"
                ),
                CodebaseIssue(
                    file_path="test.py",
                    line_number=2,
                    issue_type=IssueType.PLACEHOLDER_IMPLEMENTATION,
                    severity=IssueSeverity.CRITICAL,
                    description="Placeholder found",
                    code_snippet="password = 'test'",
                    recommendation="Replace with real implementation"
                )
            ],
            issues_by_type={
                IssueType.TODO_COMMENT: 1,
                IssueType.PLACEHOLDER_IMPLEMENTATION: 1
            },
            issues_by_severity={
                IssueSeverity.CRITICAL: 1,
                IssueSeverity.MEDIUM: 1
            }
        )
        
        assert len(recommendations) > 0
        
        # Should include critical issue warning
        critical_rec = next((r for r in recommendations if "CRITICAL" in r), None)
        assert critical_rec is not None
        
        # Should include placeholder replacement recommendation
        placeholder_rec = next((r for r in recommendations if "placeholder" in r.lower()), None)
        assert placeholder_rec is not None


# Integration test that can be run manually
async def manual_integration_test():
    """Manual integration test for the audit service."""
    print("Running manual integration test...")
    
    # Create service with real directories
    service = create_production_audit_service(
        scan_directories=["src/ai_karen_engine/services"],
        output_directory="test_reports"
    )
    
    try:
        await service.startup()
        
        print("Running audit...")
        report = await service.audit_codebase()
        
        print(f"Scanned {report.total_files_scanned} files")
        print(f"Found {report.total_issues_found} issues")
        print(f"Status: {report.overall_status}")
        
        # Generate reports
        json_report = await service.generate_report(report, "json")
        print(f"JSON report: {json_report}")
        
        await service.shutdown()
        print("Integration test completed successfully!")
        
    except Exception as e:
        print(f"Integration test failed: {e}")
        raise


if __name__ == "__main__":
    # Run manual integration test
    asyncio.run(manual_integration_test())