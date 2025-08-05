"""
Tests for CopilotKit Code Reviewer Plugin

Tests the CopilotKit code reviewer plugin functionality including
comprehensive code review, security analysis, and performance assessment.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List

# Import the plugin handler
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "plugin_marketplace" / "ai" / "copilotkit-code-reviewer"))

from handler import run, CopilotKitCodeReviewer, ReviewFinding, ReviewReport


class TestReviewFinding:
    """Test ReviewFinding dataclass."""
    
    def test_review_finding_creation(self):
        """Test creating a ReviewFinding instance."""
        finding = ReviewFinding(
            category="security",
            severity="high",
            title="SQL Injection vulnerability",
            description="Potential SQL injection in user input handling",
            line_number=42,
            suggestion="Use parameterized queries",
            code_snippet="query = f'SELECT * FROM users WHERE id = {user_id}'",
            confidence=0.9
        )
        
        assert finding.category == "security"
        assert finding.severity == "high"
        assert finding.title == "SQL Injection vulnerability"
        assert finding.line_number == 42
        assert finding.confidence == 0.9
    
    def test_review_finding_defaults(self):
        """Test ReviewFinding with default values."""
        finding = ReviewFinding(
            category="performance",
            severity="medium",
            title="Inefficient loop",
            description="Loop can be optimized"
        )
        
        assert finding.line_number is None
        assert finding.suggestion is None
        assert finding.code_snippet is None
        assert finding.confidence == 0.8


class TestReviewReport:
    """Test ReviewReport dataclass."""
    
    def test_review_report_creation(self):
        """Test creating a ReviewReport instance."""
        findings = [
            ReviewFinding("security", "high", "Test finding", "Test description")
        ]
        
        report = ReviewReport(
            overall_score=8.5,
            findings=findings,
            summary="Code review completed",
            recommendations=["Fix security issues"],
            metrics={"total_lines": 100},
            review_categories={"security": 7.0}
        )
        
        assert report.overall_score == 8.5
        assert len(report.findings) == 1
        assert report.summary == "Code review completed"
        assert "Fix security issues" in report.recommendations
    
    def test_review_report_defaults(self):
        """Test ReviewReport with default values."""
        report = ReviewReport(overall_score=5.0)
        
        assert len(report.findings) == 0
        assert report.summary == ""
        assert len(report.recommendations) == 0
        assert len(report.metrics) == 0
        assert len(report.review_categories) == 0


class TestCopilotKitCodeReviewer:
    """Test CopilotKit code reviewer functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.code_reviewer = CopilotKitCodeReviewer()
    
    @pytest.mark.asyncio
    async def test_validate_review_request_valid(self):
        """Test review request validation with valid input."""
        context = {
            "code": "def hello():\n    print('Hello, World!')",
            "language": "python",
            "review_scope": ["security", "performance"]
        }
        user_context = {}
        
        result = await self.code_reviewer._validate_review_request(context, user_context)
        
        assert result["valid"] is True
        assert len(result["warnings"]) == 0
    
    @pytest.mark.asyncio
    async def test_validate_review_request_empty_code(self):
        """Test review request validation with empty code."""
        context = {
            "code": "",
            "language": "python",
            "review_scope": []
        }
        user_context = {}
        
        result = await self.code_reviewer._validate_review_request(context, user_context)
        
        assert result["valid"] is False
        assert "No code provided for review" in result["warnings"]
    
    @pytest.mark.asyncio
    async def test_validate_review_request_large_code(self):
        """Test review request validation with very large code."""
        context = {
            "code": "x = 1\n" * 30000,  # Large code
            "language": "python",
            "review_scope": []
        }
        user_context = {}
        
        result = await self.code_reviewer._validate_review_request(context, user_context)
        
        assert result["valid"] is True
        assert any("very large" in warning for warning in result["warnings"])
        assert any("breaking large files" in suggestion for suggestion in result["suggestions"])
    
    @pytest.mark.asyncio
    async def test_validate_review_request_invalid_scope(self):
        """Test review request validation with invalid review scope."""
        context = {
            "code": "def hello(): pass",
            "language": "python",
            "review_scope": ["security", "invalid_category", "performance"]
        }
        user_context = {}
        
        result = await self.code_reviewer._validate_review_request(context, user_context)
        
        assert result["valid"] is True  # Still valid, just warning
        assert any("Unknown review categories" in warning for warning in result["warnings"])
        assert any("Available categories" in suggestion for suggestion in result["suggestions"])
    
    @pytest.mark.asyncio
    async def test_generate_review_report(self):
        """Test review report generation."""
        findings = [
            ReviewFinding("security", "high", "Security issue", "High severity security finding"),
            ReviewFinding("performance", "medium", "Performance issue", "Medium severity performance finding"),
            ReviewFinding("readability", "low", "Readability issue", "Low severity readability finding")
        ]
        
        review_report = ReviewReport(
            overall_score=7.5,
            findings=findings,
            summary="Review completed",
            recommendations=["Fix security issues first"],
            review_categories={"security": 6.0, "performance": 8.0}
        )
        
        context = {
            "review_report": review_report,
            "language": "python"
        }
        user_context = {}
        
        result = await self.code_reviewer._generate_review_report(context, user_context)
        
        assert result["generated"] is True
        assert "formatted_report" in result
        assert "findings_summary" in result
        
        # Check findings summary
        findings_summary = result["findings_summary"]
        assert findings_summary["high"] == 1
        assert findings_summary["medium"] == 1
        assert findings_summary["low"] == 1
        
        # Check formatted report content
        formatted_report = result["formatted_report"]
        assert "Code Review Summary" in formatted_report
        assert "Overall Score: 7.5/10" in formatted_report
        assert "Total Findings: 3" in formatted_report
    
    @pytest.mark.asyncio
    async def test_python_static_analysis(self):
        """Test Python static analysis."""
        code = """
import os
eval("print('hello')")
try:
    risky_operation()
except:
    pass
print("Debug message")
"""
        
        findings = await self.code_reviewer._python_static_analysis(code)
        
        # Should find eval() usage and bare except
        assert len(findings) >= 2
        
        # Check for eval finding
        eval_findings = [f for f in findings if "eval()" in f.title]
        assert len(eval_findings) == 1
        assert eval_findings[0].severity == "high"
        assert eval_findings[0].category == "security"
        
        # Check for bare except finding
        except_findings = [f for f in findings if "except clause" in f.title]
        assert len(except_findings) == 1
        assert except_findings[0].severity == "medium"
        assert except_findings[0].category == "best_practices"
    
    @pytest.mark.asyncio
    async def test_javascript_static_analysis(self):
        """Test JavaScript static analysis."""
        code = """
var oldVar = "should use let/const";
if (x == null) {
    console.log("Debug message");
}
"""
        
        findings = await self.code_reviewer._javascript_static_analysis(code)
        
        # Should find == usage and var declaration
        assert len(findings) >= 2
        
        # Check for == finding
        equality_findings = [f for f in findings if "== instead of ===" in f.title]
        assert len(equality_findings) == 1
        assert equality_findings[0].severity == "medium"
        assert equality_findings[0].category == "best_practices"
        
        # Check for var finding
        var_findings = [f for f in findings if "var declaration" in f.title]
        assert len(var_findings) == 1
        assert var_findings[0].severity == "low"
        assert var_findings[0].category == "best_practices"
    
    @pytest.mark.asyncio
    async def test_fallback_code_analysis(self):
        """Test fallback code analysis."""
        context = {
            "code": "def hello():\n    print('Hello')",
            "language": "python"
        }
        user_context = {}
        
        result = await self.code_reviewer._fallback_code_analysis(context, user_context)
        
        assert "review_report" in result
        assert result["analysis_type"] == "fallback"
        
        review_report = result["review_report"]
        assert isinstance(review_report, ReviewReport)
        assert review_report.overall_score > 0
        assert "Basic static analysis" in review_report.summary
    
    @pytest.mark.asyncio
    async def test_parse_analysis_response(self):
        """Test parsing analysis response into findings."""
        response = """
1. Critical security vulnerability in line 10
   This is a serious SQL injection risk that needs immediate attention.

2. High priority performance issue
   The loop can be optimized for better performance.

- Medium severity code smell detected
  Consider refactoring this method for better readability.

* Low priority suggestion
  Add more comments to improve documentation.
"""
        
        findings = await self.code_reviewer._parse_analysis_response(response, "security")
        
        assert len(findings) == 4
        
        # Check first finding
        assert findings[0].category == "security"
        assert findings[0].severity == "critical"
        assert "security vulnerability" in findings[0].title
        
        # Check second finding
        assert findings[1].severity == "high"
        assert "performance issue" in findings[1].title
        
        # Check third finding
        assert findings[2].severity == "medium"
        assert "code smell" in findings[2].title
        
        # Check fourth finding
        assert findings[3].severity == "low"
        assert "suggestion" in findings[3].title


class TestCopilotKitCodeReviewerPlugin:
    """Test the main plugin entry point."""
    
    @pytest.mark.asyncio
    @patch('handler.get_orchestrator')
    async def test_plugin_run_comprehensive_review(self, mock_get_orchestrator):
        """Test plugin run with comprehensive code review."""
        # Mock orchestrator
        mock_orchestrator = Mock()
        mock_orchestrator.enhanced_route = AsyncMock(return_value="""
1. High security issue: Potential SQL injection
2. Medium performance issue: Inefficient loop
3. Low readability issue: Poor variable naming
""")
        mock_get_orchestrator.return_value = mock_orchestrator
        
        params = {
            "code": "def process_data(user_input):\n    query = f'SELECT * FROM users WHERE name = {user_input}'\n    return execute_query(query)",
            "language": "python",
            "review_scope": ["security", "performance", "readability"],
            "include_suggestions": True,
            "user_context": {}
        }
        
        result = await run(params)
        
        assert result["success"] is True
        assert result["language"] == "python"
        assert result["overall_score"] > 0
        assert result["findings_count"] > 0
        assert len(result["findings"]) > 0
        assert result["provider"] == "copilotkit_code_reviewer"
        
        # Check that findings have required fields
        for finding in result["findings"]:
            assert "category" in finding
            assert "severity" in finding
            assert "title" in finding
            assert "description" in finding
    
    @pytest.mark.asyncio
    @patch('handler.get_orchestrator')
    async def test_plugin_run_specific_categories(self, mock_get_orchestrator):
        """Test plugin run with specific review categories."""
        # Mock orchestrator
        mock_orchestrator = Mock()
        mock_orchestrator.enhanced_route = AsyncMock(return_value="Security analysis: No issues found")
        mock_get_orchestrator.return_value = mock_orchestrator
        
        params = {
            "code": "def secure_function():\n    return 'safe'",
            "language": "python",
            "review_scope": ["security"],
            "user_context": {}
        }
        
        result = await run(params)
        
        assert result["success"] is True
        assert result["language"] == "python"
        
        # Verify orchestrator was called for security analysis
        mock_orchestrator.enhanced_route.assert_called()
        call_args = mock_orchestrator.enhanced_route.call_args[0][0]
        assert "security" in call_args.lower()
    
    @pytest.mark.asyncio
    async def test_plugin_run_validation_failure(self):
        """Test plugin run with validation failure."""
        params = {
            "code": "",  # Empty code should fail validation
            "language": "python",
            "review_scope": [],
            "user_context": {}
        }
        
        result = await run(params)
        
        assert result["success"] is False
        assert result["error"] == "Input validation failed"
        assert "validation_warnings" in result
        assert any("No code provided" in warning for warning in result["validation_warnings"])
    
    @pytest.mark.asyncio
    @patch('handler.get_orchestrator')
    async def test_plugin_run_with_orchestrator_failure(self, mock_get_orchestrator):
        """Test plugin run when orchestrator fails."""
        # Mock orchestrator to raise exception
        mock_orchestrator = Mock()
        mock_orchestrator.enhanced_route = AsyncMock(side_effect=Exception("Orchestrator failed"))
        mock_get_orchestrator.return_value = mock_orchestrator
        
        params = {
            "code": "def test(): pass",
            "language": "python",
            "review_scope": ["security"],
            "user_context": {}
        }
        
        result = await run(params)
        
        # Should fall back to fallback analysis
        assert result["success"] is True
        assert result["provider"] == "fallback_analyzer"
        assert "warning" in result
        assert "CopilotKit unavailable" in result["warning"]
    
    @pytest.mark.asyncio
    async def test_plugin_run_complete_failure(self):
        """Test plugin run when everything fails."""
        # Mock to cause complete failure
        with patch('handler.CopilotKitCodeReviewer') as mock_class:
            mock_class.side_effect = Exception("Complete failure")
            
            params = {
                "code": "def test(): pass",
                "language": "python",
                "review_scope": [],
                "user_context": {}
            }
            
            result = await run(params)
            
            assert result["success"] is False
            assert "error" in result
            assert "fallback_error" in result
            assert result["provider"] == "copilotkit_code_reviewer"
    
    @pytest.mark.asyncio
    @patch('handler.get_orchestrator')
    async def test_plugin_run_default_scope(self, mock_get_orchestrator):
        """Test plugin run with default review scope."""
        # Mock orchestrator
        mock_orchestrator = Mock()
        mock_orchestrator.enhanced_route = AsyncMock(return_value="Analysis complete")
        mock_get_orchestrator.return_value = mock_orchestrator
        
        params = {
            "code": "def test(): pass",
            "language": "python",
            # No review_scope specified - should use default
            "user_context": {}
        }
        
        result = await run(params)
        
        assert result["success"] is True
        
        # Should have called orchestrator for default categories
        assert mock_orchestrator.enhanced_route.call_count >= 4  # security, performance, maintainability, readability
    
    @pytest.mark.asyncio
    @patch('handler.get_orchestrator')
    async def test_plugin_run_multiple_languages(self, mock_get_orchestrator):
        """Test plugin run with different programming languages."""
        # Mock orchestrator
        mock_orchestrator = Mock()
        mock_orchestrator.enhanced_route = AsyncMock(return_value="Language-specific analysis")
        mock_get_orchestrator.return_value = mock_orchestrator
        
        languages = ["python", "javascript", "typescript", "java", "c++"]
        
        for language in languages:
            params = {
                "code": "function test() { return true; }" if language in ["javascript", "typescript"] else "def test(): return True",
                "language": language,
                "review_scope": ["security"],
                "user_context": {}
            }
            
            result = await run(params)
            
            assert result["success"] is True
            assert result["language"] == language
            assert result["provider"] == "copilotkit_code_reviewer"
    
    @pytest.mark.asyncio
    @patch('handler.get_orchestrator')
    async def test_plugin_run_with_formatted_report(self, mock_get_orchestrator):
        """Test plugin run generates formatted report."""
        # Mock orchestrator
        mock_orchestrator = Mock()
        mock_orchestrator.enhanced_route = AsyncMock(return_value="""
1. Critical issue: Buffer overflow vulnerability
2. High issue: Memory leak detected
""")
        mock_get_orchestrator.return_value = mock_orchestrator
        
        params = {
            "code": "char buffer[10]; strcpy(buffer, user_input);",
            "language": "c++",
            "review_scope": ["security"],
            "user_context": {}
        }
        
        result = await run(params)
        
        assert result["success"] is True
        assert "formatted_report" in result
        
        formatted_report = result["formatted_report"]
        assert "Code Review Summary" in formatted_report
        assert "Overall Score:" in formatted_report
        assert "Total Findings:" in formatted_report


class TestCodeReviewerHooks:
    """Test code reviewer hook integration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.code_reviewer = CopilotKitCodeReviewer()
    
    @pytest.mark.asyncio
    async def test_hook_registration(self):
        """Test that hooks are properly registered."""
        # This is a basic test to ensure hooks can be registered
        assert hasattr(self.code_reviewer, 'register_hook')
        assert hasattr(self.code_reviewer, 'trigger_hook_safe')
    
    @pytest.mark.asyncio
    async def test_validation_hook_integration(self):
        """Test validation hook integration."""
        context = {
            "code": "def test(): pass",
            "language": "python",
            "review_scope": ["security"]
        }
        user_context = {}
        
        # Test direct hook call
        result = await self.code_reviewer._validate_review_request(context, user_context)
        
        assert isinstance(result, dict)
        assert "valid" in result
        assert "warnings" in result
        assert "suggestions" in result
    
    @pytest.mark.asyncio
    async def test_report_generation_hook_integration(self):
        """Test report generation hook integration."""
        review_report = ReviewReport(
            overall_score=8.0,
            findings=[
                ReviewFinding("security", "high", "Test finding", "Test description")
            ],
            summary="Test review"
        )
        
        context = {
            "review_report": review_report,
            "language": "python"
        }
        user_context = {}
        
        # Test direct hook call
        result = await self.code_reviewer._generate_review_report(context, user_context)
        
        assert isinstance(result, dict)
        assert "generated" in result
        assert result["generated"] is True
    
    @pytest.mark.asyncio
    async def test_fallback_hook_integration(self):
        """Test fallback hook integration."""
        context = {
            "code": "def test(): pass",
            "language": "python"
        }
        user_context = {}
        
        # Test direct hook call
        result = await self.code_reviewer._fallback_code_analysis(context, user_context)
        
        assert isinstance(result, dict)
        assert "review_report" in result
        assert "analysis_type" in result
        assert result["analysis_type"] == "fallback"


if __name__ == "__main__":
    pytest.main([__file__])