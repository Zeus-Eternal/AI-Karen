"""
Production Hardening Audit Service

This service provides comprehensive auditing capabilities to identify and catalog
development artifacts, TODO comments, dummy logic, and placeholder implementations
throughout the codebase to ensure production readiness.
"""

import ast
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
import json

from ...internal..core.services.base import BaseService, ServiceConfig


class IssueType(str, Enum):
    """Types of production readiness issues."""
    TODO_COMMENT = "todo_comment"
    DUMMY_LOGIC = "dummy_logic"
    PLACEHOLDER_IMPLEMENTATION = "placeholder_implementation"
    DEBUG_CODE = "debug_code"
    TEST_DATA = "test_data"
    DEVELOPMENT_CONFIG = "development_config"
    HARDCODED_VALUES = "hardcoded_values"
    MISSING_ERROR_HANDLING = "missing_error_handling"


class IssueSeverity(str, Enum):
    """Severity levels for production readiness issues."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class CodebaseIssue:
    """Represents a production readiness issue found in the codebase."""
    file_path: str
    line_number: int
    issue_type: IssueType
    severity: IssueSeverity
    description: str
    code_snippet: str
    recommendation: str
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditReport:
    """Comprehensive production readiness audit report."""
    timestamp: datetime
    total_files_scanned: int
    total_issues_found: int
    issues_by_type: Dict[IssueType, int]
    issues_by_severity: Dict[IssueSeverity, int]
    issues: List[CodebaseIssue]
    scan_duration_seconds: float
    recommendations: List[str]
    overall_status: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "total_files_scanned": self.total_files_scanned,
            "total_issues_found": self.total_issues_found,
            "issues_by_type": {k.value: v for k, v in self.issues_by_type.items()},
            "issues_by_severity": {k.value: v for k, v in self.issues_by_severity.items()},
            "issues": [
                {
                    "file_path": issue.file_path,
                    "line_number": issue.line_number,
                    "issue_type": issue.issue_type.value,
                    "severity": issue.severity.value,
                    "description": issue.description,
                    "code_snippet": issue.code_snippet,
                    "recommendation": issue.recommendation,
                    "context": issue.context
                }
                for issue in self.issues
            ],
            "scan_duration_seconds": self.scan_duration_seconds,
            "recommendations": self.recommendations,
            "overall_status": self.overall_status
        }


class ProductionHardeningAuditService(BaseService):
    """
    Service for auditing codebase production readiness.
    
    Scans the codebase to identify TODO comments, dummy logic, placeholder
    implementations, and other development artifacts that need to be addressed
    before production deployment.
    """
    
    # Patterns for identifying different types of issues
    TODO_PATTERNS = [
        r'#\s*TODO[:\s]',
        r'#\s*FIXME[:\s]',
        r'#\s*HACK[:\s]',
        r'#\s*XXX[:\s]',
        r'#\s*BUG[:\s]',
        r'#\s*NOTE[:\s].*(?:fix|todo|implement)',
        r'\/\/\s*TODO[:\s]',
        r'\/\/\s*FIXME[:\s]',
        r'\/\*\s*TODO[:\s]',
    ]
    
    DUMMY_LOGIC_PATTERNS = [
        r'pass\s*#.*(?:dummy|placeholder|stub)',
        r'return\s+None\s*#.*(?:dummy|placeholder|stub)',
        r'return\s+\{\}\s*#.*(?:dummy|placeholder|stub)',
        r'return\s+\[\]\s*#.*(?:dummy|placeholder|stub)',
        r'raise\s+NotImplementedError',
        r'print\s*\(\s*["\'].*(?:dummy|test|debug|placeholder)',
        r'console\.log\s*\(\s*["\'].*(?:dummy|test|debug|placeholder)',
    ]
    
    PLACEHOLDER_PATTERNS = [
        r'(?:example|demo|test|placeholder|dummy)\.(?:com|org|net)',
        r'admin@example\.com',
        r'user@example\.com',
        r'test@test\.com',
        r'password.*=.*["\'](?:password|123456|admin|test)',
        r'api_key.*=.*["\'](?:your_api_key|test_key|dummy_key)',
        r'secret.*=.*["\'](?:your_secret|test_secret|dummy_secret)',
    ]
    
    DEBUG_CODE_PATTERNS = [
        r'console\.log\s*\(',
        r'print\s*\(\s*["\'].*(?:debug|DEBUG)',
        r'debugger;',
        r'pdb\.set_trace\(\)',
        r'breakpoint\(\)',
        r'import\s+pdb',
        r'from\s+pdb\s+import',
    ]
    
    HARDCODED_PATTERNS = [
        r'localhost:(?:3000|8000|5000|9000)',
        r'127\.0\.0\.1:(?:3000|8000|5000|9000)',
        r'http://localhost',
        r'http://127\.0\.0\.1',
    ]
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        if config is None:
            config = ServiceConfig(
                name="production_hardening_audit",
                enabled=True,
                config={
                    "scan_directories": ["src", "ui_launchers", "extensions", "config"],
                    "exclude_patterns": [
                        "*.pyc", "__pycache__", ".git", "node_modules", 
                        "*.log", "*.tmp", ".pytest_cache", "htmlcov",
                        "*.egg-info", ".venv", "venv"
                    ],
                    "file_extensions": [".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".yaml", ".yml"],
                    "max_file_size_mb": 10,
                    "output_directory": "reports/production_audit"
                }
            )
        
        super().__init__(config)
        self.scan_directories = config.config.get("scan_directories", ["src"])
        self.exclude_patterns = config.config.get("exclude_patterns", [])
        self.file_extensions = config.config.get("file_extensions", [".py"])
        self.max_file_size_mb = config.config.get("max_file_size_mb", 10)
        self.output_directory = Path(config.config.get("output_directory", "reports/production_audit"))
        
        # Compile regex patterns for performance
        self._compiled_patterns = {
            IssueType.TODO_COMMENT: [re.compile(pattern, re.IGNORECASE) for pattern in self.TODO_PATTERNS],
            IssueType.DUMMY_LOGIC: [re.compile(pattern, re.IGNORECASE) for pattern in self.DUMMY_LOGIC_PATTERNS],
            IssueType.PLACEHOLDER_IMPLEMENTATION: [re.compile(pattern, re.IGNORECASE) for pattern in self.PLACEHOLDER_PATTERNS],
            IssueType.DEBUG_CODE: [re.compile(pattern, re.IGNORECASE) for pattern in self.DEBUG_CODE_PATTERNS],
            IssueType.HARDCODED_VALUES: [re.compile(pattern, re.IGNORECASE) for pattern in self.HARDCODED_PATTERNS],
        }
    
    async def initialize(self) -> None:
        """Initialize the audit service."""
        self.logger.info("Initializing Production Hardening Audit Service")
        
        # Create output directory if it doesn't exist
        self.output_directory.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Audit service initialized. Output directory: {self.output_directory}")
    
    async def start(self) -> None:
        """Start the audit service."""
        self.logger.info("Production Hardening Audit Service started")
    
    async def stop(self) -> None:
        """Stop the audit service."""
        self.logger.info("Production Hardening Audit Service stopped")
    
    async def health_check(self) -> bool:
        """Perform health check."""
        try:
            # Check if output directory is writable
            test_file = self.output_directory / "health_check.tmp"
            test_file.write_text("health check")
            test_file.unlink()
            return True
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    def _should_scan_file(self, file_path: Path) -> bool:
        """Determine if a file should be scanned."""
        # Check file extension
        if file_path.suffix not in self.file_extensions:
            return False
        
        # Check file size
        try:
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            if file_size_mb > self.max_file_size_mb:
                self.logger.warning(f"Skipping large file: {file_path} ({file_size_mb:.2f}MB)")
                return False
        except OSError:
            return False
        
        # Check exclude patterns
        file_str = str(file_path)
        for pattern in self.exclude_patterns:
            if pattern in file_str:
                return False
        
        return True
    
    def _get_files_to_scan(self) -> List[Path]:
        """Get list of files to scan."""
        files_to_scan = []
        
        for directory in self.scan_directories:
            dir_path = Path(directory)
            if not dir_path.exists():
                self.logger.warning(f"Scan directory does not exist: {directory}")
                continue
            
            for file_path in dir_path.rglob("*"):
                if file_path.is_file() and self._should_scan_file(file_path):
                    files_to_scan.append(file_path)
        
        return files_to_scan
    
    def _scan_file_for_issues(self, file_path: Path) -> List[CodebaseIssue]:
        """Scan a single file for production readiness issues."""
        issues = []
        
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.splitlines()
            
            for line_num, line in enumerate(lines, 1):
                # Check each pattern type
                for issue_type, patterns in self._compiled_patterns.items():
                    for pattern in patterns:
                        matches = pattern.finditer(line)
                        for match in matches:
                            issue = self._create_issue(
                                file_path, line_num, line, issue_type, match
                            )
                            if issue:
                                issues.append(issue)
                
                # Additional checks for specific file types
                if file_path.suffix == '.py':
                    issues.extend(self._scan_python_specific_issues(file_path, line_num, line))
                elif file_path.suffix in ['.js', '.ts', '.tsx', '.jsx']:
                    issues.extend(self._scan_javascript_specific_issues(file_path, line_num, line))
                elif file_path.suffix in ['.json', '.yaml', '.yml']:
                    issues.extend(self._scan_config_specific_issues(file_path, line_num, line))
        
        except Exception as e:
            self.logger.error(f"Error scanning file {file_path}: {e}")
            # Create an issue for the scan error itself
            issues.append(CodebaseIssue(
                file_path=str(file_path),
                line_number=0,
                issue_type=IssueType.MISSING_ERROR_HANDLING,
                severity=IssueSeverity.MEDIUM,
                description=f"File scan error: {str(e)}",
                code_snippet="",
                recommendation="Investigate file encoding or permissions issues",
                context={"error": str(e)}
            ))
        
        return issues
    
    def _create_issue(self, file_path: Path, line_num: int, line: str, 
                     issue_type: IssueType, match: re.Match) -> Optional[CodebaseIssue]:
        """Create a CodebaseIssue from a pattern match."""
        severity = self._determine_severity(issue_type, line, match)
        description = self._generate_description(issue_type, line, match)
        recommendation = self._generate_recommendation(issue_type, line, match)
        
        return CodebaseIssue(
            file_path=str(file_path),
            line_number=line_num,
            issue_type=issue_type,
            severity=severity,
            description=description,
            code_snippet=line.strip(),
            recommendation=recommendation,
            context={
                "match_text": match.group(),
                "match_start": match.start(),
                "match_end": match.end()
            }
        )
    
    def _scan_python_specific_issues(self, file_path: Path, line_num: int, line: str) -> List[CodebaseIssue]:
        """Scan for Python-specific production readiness issues."""
        issues = []
        
        # Check for missing error handling in try blocks
        if re.search(r'except\s*:', line):
            issues.append(CodebaseIssue(
                file_path=str(file_path),
                line_number=line_num,
                issue_type=IssueType.MISSING_ERROR_HANDLING,
                severity=IssueSeverity.HIGH,
                description="Bare except clause catches all exceptions",
                code_snippet=line.strip(),
                recommendation="Use specific exception types or 'except Exception as e:'"
            ))
        
        # Check for development imports
        dev_imports = ['pdb', 'ipdb', 'pudb', 'pytest', 'unittest.mock']
        for dev_import in dev_imports:
            if re.search(rf'import\s+{dev_import}|from\s+{dev_import}', line):
                issues.append(CodebaseIssue(
                    file_path=str(file_path),
                    line_number=line_num,
                    issue_type=IssueType.DEBUG_CODE,
                    severity=IssueSeverity.MEDIUM,
                    description=f"Development import: {dev_import}",
                    code_snippet=line.strip(),
                    recommendation=f"Remove {dev_import} import from production code"
                ))
        
        return issues
    
    def _scan_javascript_specific_issues(self, file_path: Path, line_num: int, line: str) -> List[CodebaseIssue]:
        """Scan for JavaScript/TypeScript-specific production readiness issues."""
        issues = []
        
        # Check for console statements
        if re.search(r'console\.(log|debug|info|warn|error)', line):
            issues.append(CodebaseIssue(
                file_path=str(file_path),
                line_number=line_num,
                issue_type=IssueType.DEBUG_CODE,
                severity=IssueSeverity.LOW,
                description="Console statement found",
                code_snippet=line.strip(),
                recommendation="Remove console statements or replace with proper logging"
            ))
        
        # Check for alert/confirm statements
        if re.search(r'alert\s*\(|confirm\s*\(', line):
            issues.append(CodebaseIssue(
                file_path=str(file_path),
                line_number=line_num,
                issue_type=IssueType.DEBUG_CODE,
                severity=IssueSeverity.MEDIUM,
                description="Browser alert/confirm found",
                code_snippet=line.strip(),
                recommendation="Replace with proper UI components"
            ))
        
        return issues
    
    def _scan_config_specific_issues(self, file_path: Path, line_num: int, line: str) -> List[CodebaseIssue]:
        """Scan for configuration-specific production readiness issues."""
        issues = []
        
        # Check for development URLs
        if re.search(r'localhost|127\.0\.0\.1', line):
            issues.append(CodebaseIssue(
                file_path=str(file_path),
                line_number=line_num,
                issue_type=IssueType.DEVELOPMENT_CONFIG,
                severity=IssueSeverity.HIGH,
                description="Development URL found in configuration",
                code_snippet=line.strip(),
                recommendation="Replace with production URLs or environment variables"
            ))
        
        # Check for test/demo data
        if re.search(r'test|demo|example|dummy', line, re.IGNORECASE):
            issues.append(CodebaseIssue(
                file_path=str(file_path),
                line_number=line_num,
                issue_type=IssueType.TEST_DATA,
                severity=IssueSeverity.MEDIUM,
                description="Potential test/demo data in configuration",
                code_snippet=line.strip(),
                recommendation="Replace with production data or remove if not needed"
            ))
        
        return issues
    
    def _determine_severity(self, issue_type: IssueType, line: str, match: re.Match) -> IssueSeverity:
        """Determine the severity of an issue based on context."""
        # Critical issues that must be fixed
        if issue_type == IssueType.PLACEHOLDER_IMPLEMENTATION:
            if any(keyword in line.lower() for keyword in ['password', 'secret', 'key', 'token']):
                return IssueSeverity.CRITICAL
            return IssueSeverity.HIGH
        
        if issue_type == IssueType.DEVELOPMENT_CONFIG:
            return IssueSeverity.HIGH
        
        if issue_type == IssueType.DUMMY_LOGIC:
            if 'NotImplementedError' in line:
                return IssueSeverity.HIGH
            return IssueSeverity.MEDIUM
        
        if issue_type == IssueType.TODO_COMMENT:
            if any(keyword in line.lower() for keyword in ['critical', 'urgent', 'security', 'bug']):
                return IssueSeverity.HIGH
            return IssueSeverity.MEDIUM
        
        if issue_type == IssueType.DEBUG_CODE:
            return IssueSeverity.LOW
        
        return IssueSeverity.MEDIUM
    
    def _generate_description(self, issue_type: IssueType, line: str, match: re.Match) -> str:
        """Generate a description for the issue."""
        descriptions = {
            IssueType.TODO_COMMENT: "TODO comment found that needs to be addressed",
            IssueType.DUMMY_LOGIC: "Dummy or placeholder logic that needs implementation",
            IssueType.PLACEHOLDER_IMPLEMENTATION: "Placeholder implementation with example/test data",
            IssueType.DEBUG_CODE: "Debug code that should be removed from production",
            IssueType.TEST_DATA: "Test or demo data that should be replaced with production data",
            IssueType.DEVELOPMENT_CONFIG: "Development configuration that needs production values",
            IssueType.HARDCODED_VALUES: "Hardcoded values that should be configurable",
            IssueType.MISSING_ERROR_HANDLING: "Missing or inadequate error handling"
        }
        
        base_description = descriptions.get(issue_type, "Production readiness issue found")
        matched_text = match.group().strip()
        
        return f"{base_description}: '{matched_text}'"
    
    def _generate_recommendation(self, issue_type: IssueType, line: str, match: re.Match) -> str:
        """Generate a recommendation for fixing the issue."""
        recommendations = {
            IssueType.TODO_COMMENT: "Complete the TODO item or remove the comment if no longer relevant",
            IssueType.DUMMY_LOGIC: "Implement proper logic to replace the placeholder",
            IssueType.PLACEHOLDER_IMPLEMENTATION: "Replace with production-ready implementation and real data",
            IssueType.DEBUG_CODE: "Remove debug code or replace with proper logging",
            IssueType.TEST_DATA: "Replace with production data or remove if not needed",
            IssueType.DEVELOPMENT_CONFIG: "Use environment variables or production configuration",
            IssueType.HARDCODED_VALUES: "Move to configuration file or environment variables",
            IssueType.MISSING_ERROR_HANDLING: "Add proper error handling with specific exception types"
        }
        
        return recommendations.get(issue_type, "Review and fix this issue before production deployment")
    
    async def audit_codebase(self) -> AuditReport:
        """
        Perform comprehensive codebase audit for production readiness.
        
        Returns:
            AuditReport: Detailed audit report with all findings
        """
        start_time = datetime.now()
        self.logger.info("Starting production readiness audit")
        
        # Get files to scan
        files_to_scan = self._get_files_to_scan()
        self.logger.info(f"Scanning {len(files_to_scan)} files")
        
        # Scan all files
        all_issues = []
        for file_path in files_to_scan:
            self.logger.debug(f"Scanning file: {file_path}")
            file_issues = self._scan_file_for_issues(file_path)
            all_issues.extend(file_issues)
        
        # Generate statistics
        issues_by_type = {}
        issues_by_severity = {}
        
        for issue in all_issues:
            issues_by_type[issue.issue_type] = issues_by_type.get(issue.issue_type, 0) + 1
            issues_by_severity[issue.severity] = issues_by_severity.get(issue.severity, 0) + 1
        
        # Determine overall status
        critical_count = issues_by_severity.get(IssueSeverity.CRITICAL, 0)
        high_count = issues_by_severity.get(IssueSeverity.HIGH, 0)
        
        if critical_count > 0:
            overall_status = "NOT_READY - Critical issues must be resolved"
        elif high_count > 10:
            overall_status = "NOT_READY - Too many high-severity issues"
        elif high_count > 0:
            overall_status = "NEEDS_ATTENTION - High-severity issues found"
        elif len(all_issues) > 50:
            overall_status = "NEEDS_IMPROVEMENT - Many issues found"
        elif len(all_issues) > 0:
            overall_status = "MOSTLY_READY - Minor issues found"
        else:
            overall_status = "PRODUCTION_READY - No issues found"
        
        # Generate recommendations
        recommendations = self._generate_recommendations(all_issues, issues_by_type, issues_by_severity)
        
        end_time = datetime.now()
        scan_duration = (end_time - start_time).total_seconds()
        
        report = AuditReport(
            timestamp=start_time,
            total_files_scanned=len(files_to_scan),
            total_issues_found=len(all_issues),
            issues_by_type=issues_by_type,
            issues_by_severity=issues_by_severity,
            issues=all_issues,
            scan_duration_seconds=scan_duration,
            recommendations=recommendations,
            overall_status=overall_status
        )
        
        self.logger.info(f"Audit completed in {scan_duration:.2f}s. Found {len(all_issues)} issues.")
        return report
    
    def _generate_recommendations(self, issues: List[CodebaseIssue], 
                                issues_by_type: Dict[IssueType, int],
                                issues_by_severity: Dict[IssueSeverity, int]) -> List[str]:
        """Generate high-level recommendations based on audit results."""
        recommendations = []
        
        # Critical issues
        if issues_by_severity.get(IssueSeverity.CRITICAL, 0) > 0:
            recommendations.append("🚨 CRITICAL: Address all critical security and configuration issues immediately")
        
        # High severity issues
        high_count = issues_by_severity.get(IssueSeverity.HIGH, 0)
        if high_count > 0:
            recommendations.append(f"⚠️  HIGH PRIORITY: Resolve {high_count} high-severity issues before deployment")
        
        # Specific issue type recommendations
        if issues_by_type.get(IssueType.TODO_COMMENT, 0) > 10:
            recommendations.append("📝 Complete or remove excessive TODO comments")
        
        if issues_by_type.get(IssueType.DUMMY_LOGIC, 0) > 0:
            recommendations.append("🔧 Implement all placeholder and dummy logic")
        
        if issues_by_type.get(IssueType.DEBUG_CODE, 0) > 0:
            recommendations.append("🐛 Remove all debug code and console statements")
        
        if issues_by_type.get(IssueType.PLACEHOLDER_IMPLEMENTATION, 0) > 0:
            recommendations.append("🔐 Replace all placeholder credentials and test data")
        
        if issues_by_type.get(IssueType.DEVELOPMENT_CONFIG, 0) > 0:
            recommendations.append("⚙️  Update development configurations for production")
        
        # General recommendations
        if len(issues) > 0:
            recommendations.append("📊 Run this audit regularly during development")
            recommendations.append("🔍 Consider adding pre-commit hooks to catch issues early")
        
        if len(recommendations) == 0:
            recommendations.append("✅ Codebase appears production-ready!")
        
        return recommendations
    
    async def generate_report(self, report: AuditReport, 
                            format: str = "json") -> Path:
        """
        Generate and save audit report to file.
        
        Args:
            report: The audit report to save
            format: Output format ("json", "html", "markdown")
            
        Returns:
            Path to the generated report file
        """
        timestamp_str = report.timestamp.strftime("%Y%m%d_%H%M%S")
        
        if format == "json":
            report_file = self.output_directory / f"audit_report_{timestamp_str}.json"
            report_file.write_text(json.dumps(report.to_dict(), indent=2))
        
        elif format == "html":
            report_file = self.output_directory / f"audit_report_{timestamp_str}.html"
            html_content = self._generate_html_report(report)
            report_file.write_text(html_content)
        
        elif format == "markdown":
            report_file = self.output_directory / f"audit_report_{timestamp_str}.md"
            markdown_content = self._generate_markdown_report(report)
            report_file.write_text(markdown_content)
        
        else:
            raise ValueError(f"Unsupported report format: {format}")
        
        self.logger.info(f"Report generated: {report_file}")
        return report_file
    
    def _generate_html_report(self, report: AuditReport) -> str:
        """Generate HTML report."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Production Readiness Audit Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
        .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
        .stat-box {{ background: #e9ecef; padding: 15px; border-radius: 5px; flex: 1; }}
        .issue {{ margin: 10px 0; padding: 10px; border-left: 4px solid #ccc; }}
        .critical {{ border-left-color: #dc3545; }}
        .high {{ border-left-color: #fd7e14; }}
        .medium {{ border-left-color: #ffc107; }}
        .low {{ border-left-color: #28a745; }}
        .code {{ background: #f8f9fa; padding: 5px; font-family: monospace; }}
        .recommendations {{ background: #d4edda; padding: 15px; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Production Readiness Audit Report</h1>
        <p><strong>Generated:</strong> {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Status:</strong> {report.overall_status}</p>
    </div>
    
    <div class="summary">
        <div class="stat-box">
            <h3>Files Scanned</h3>
            <p>{report.total_files_scanned}</p>
        </div>
        <div class="stat-box">
            <h3>Issues Found</h3>
            <p>{report.total_issues_found}</p>
        </div>
        <div class="stat-box">
            <h3>Scan Duration</h3>
            <p>{report.scan_duration_seconds:.2f}s</p>
        </div>
    </div>
    
    <h2>Issues by Severity</h2>
    <ul>
        {chr(10).join(f'<li>{severity.value.title()}: {count}</li>' for severity, count in report.issues_by_severity.items())}
    </ul>
    
    <h2>Recommendations</h2>
    <div class="recommendations">
        <ul>
            {chr(10).join(f'<li>{rec}</li>' for rec in report.recommendations)}
        </ul>
    </div>
    
    <h2>Detailed Issues</h2>
    {chr(10).join(f'''
    <div class="issue {issue.severity.value}">
        <h4>{issue.issue_type.value.replace('_', ' ').title()}</h4>
        <p><strong>File:</strong> {issue.file_path}:{issue.line_number}</p>
        <p><strong>Description:</strong> {issue.description}</p>
        <div class="code">{issue.code_snippet}</div>
        <p><strong>Recommendation:</strong> {issue.recommendation}</p>
    </div>
    ''' for issue in report.issues)}
</body>
</html>
        """
        return html
    
    def _generate_markdown_report(self, report: AuditReport) -> str:
        """Generate Markdown report."""
        markdown = f"""# Production Readiness Audit Report

**Generated:** {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}  
**Status:** {report.overall_status}  
**Files Scanned:** {report.total_files_scanned}  
**Issues Found:** {report.total_issues_found}  
**Scan Duration:** {report.scan_duration_seconds:.2f}s  

## Summary

### Issues by Severity
{chr(10).join(f'- **{severity.value.title()}:** {count}' for severity, count in report.issues_by_severity.items())}

### Issues by Type
{chr(10).join(f'- **{issue_type.value.replace("_", " ").title()}:** {count}' for issue_type, count in report.issues_by_type.items())}

## Recommendations

{chr(10).join(f'- {rec}' for rec in report.recommendations)}

## Detailed Issues

{chr(10).join(f'''### {issue.issue_type.value.replace('_', ' ').title()} - {issue.severity.value.upper()}

**File:** `{issue.file_path}:{issue.line_number}`  
**Description:** {issue.description}  

```
{issue.code_snippet}
```

**Recommendation:** {issue.recommendation}

---
''' for issue in report.issues)}
        """
        return markdown
    
    async def validate_production_readiness(self) -> Tuple[bool, List[str]]:
        """
        Validate if the codebase is ready for production deployment.
        
        Returns:
            Tuple of (is_ready, blocking_issues)
        """
        report = await self.audit_codebase()
        
        # Check for blocking issues
        blocking_issues = []
        
        critical_count = report.issues_by_severity.get(IssueSeverity.CRITICAL, 0)
        if critical_count > 0:
            blocking_issues.append(f"{critical_count} critical security/configuration issues")
        
        high_count = report.issues_by_severity.get(IssueSeverity.HIGH, 0)
        if high_count > 10:
            blocking_issues.append(f"Too many high-severity issues ({high_count})")
        
        # Check for specific blocking issue types
        dummy_logic_count = report.issues_by_type.get(IssueType.DUMMY_LOGIC, 0)
        if dummy_logic_count > 0:
            blocking_issues.append(f"{dummy_logic_count} unimplemented features")
        
        placeholder_count = report.issues_by_type.get(IssueType.PLACEHOLDER_IMPLEMENTATION, 0)
        if placeholder_count > 0:
            blocking_issues.append(f"{placeholder_count} placeholder implementations")
        
        is_ready = len(blocking_issues) == 0
        
        self.logger.info(f"Production readiness validation: {'READY' if is_ready else 'NOT READY'}")
        if blocking_issues:
            self.logger.warning(f"Blocking issues: {', '.join(blocking_issues)}")
        
        return is_ready, blocking_issues


# Factory function for easy service creation
def create_production_audit_service(scan_directories: Optional[List[str]] = None,
                                   output_directory: Optional[str] = None) -> ProductionHardeningAuditService:
    """
    Create a production hardening audit service with custom configuration.
    
    Args:
        scan_directories: Directories to scan (defaults to ["src", "ui_launchers", "extensions"])
        output_directory: Output directory for reports (defaults to "reports/production_audit")
    
    Returns:
        Configured ProductionHardeningAuditService instance
    """
    config = ServiceConfig(
        name="production_hardening_audit",
        enabled=True,
        config={
            "scan_directories": scan_directories or ["src", "ui_launchers", "extensions", "config"],
            "exclude_patterns": [
                "*.pyc", "__pycache__", ".git", "node_modules", 
                "*.log", "*.tmp", ".pytest_cache", "htmlcov",
                "*.egg-info", ".venv", "venv", "*.min.js", "*.min.css"
            ],
            "file_extensions": [".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".yaml", ".yml"],
            "max_file_size_mb": 10,
            "output_directory": output_directory or "reports/production_audit"
        }
    )
    
    return ProductionHardeningAuditService(config)