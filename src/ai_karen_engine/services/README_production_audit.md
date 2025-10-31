# Production Hardening Audit Service

The Production Hardening Audit Service provides comprehensive scanning capabilities to identify development artifacts, TODO comments, dummy logic, and placeholder implementations that need to be addressed before production deployment.

## Features

### Issue Detection
- **TODO Comments**: Identifies TODO, FIXME, HACK, XXX, and BUG comments
- **Dummy Logic**: Detects placeholder implementations, NotImplementedError, and stub code
- **Debug Code**: Finds console.log, print statements, debugger calls, and pdb imports
- **Placeholder Data**: Identifies example.com domains, test credentials, and dummy API keys
- **Development Config**: Detects localhost URLs and development-specific settings
- **Missing Error Handling**: Finds bare except clauses and inadequate error handling

### Severity Classification
- **Critical**: Security-related placeholders, hardcoded credentials
- **High**: NotImplementedError, development configurations, security issues
- **Medium**: Regular TODO comments, general dummy logic
- **Low**: Debug statements, console logs
- **Info**: Minor issues and suggestions

### Report Generation
- **JSON**: Machine-readable format for CI/CD integration
- **HTML**: Rich visual reports with styling and navigation
- **Markdown**: Documentation-friendly format

## Usage

### Basic Usage

```python
from ai_karen_engine.services.production_hardening_audit import create_production_audit_service

# Create service
service = create_production_audit_service(
    scan_directories=["src", "ui_launchers", "extensions"],
    output_directory="reports/production_audit"
)

# Run audit
await service.startup()
report = await service.audit_codebase()

# Generate reports
json_report = await service.generate_report(report, "json")
html_report = await service.generate_report(report, "html")

await service.shutdown()
```

### Command Line Usage

```bash
# Basic audit
python scripts/production_audit.py

# Custom directories and formats
python scripts/production_audit.py --dirs src ui_launchers --format html markdown

# Verbose output
python scripts/production_audit.py --verbose

# Custom output directory
python scripts/production_audit.py --output /tmp/audit_reports
```

### Production Readiness Validation

```python
# Check if codebase is production ready
is_ready, blocking_issues = await service.validate_production_readiness()

if not is_ready:
    print(f"Blocking issues: {blocking_issues}")
    # Handle deployment blocking
else:
    print("Codebase is production ready!")
    # Proceed with deployment
```

## Configuration

### Service Configuration

```python
config = ServiceConfig(
    name="production_hardening_audit",
    enabled=True,
    config={
        "scan_directories": ["src", "ui_launchers", "extensions"],
        "exclude_patterns": [
            "*.pyc", "__pycache__", ".git", "node_modules",
            "*.log", "*.tmp", ".pytest_cache", "htmlcov"
        ],
        "file_extensions": [".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".yaml", ".yml"],
        "max_file_size_mb": 10,
        "output_directory": "reports/production_audit"
    }
)
```

### Pattern Customization

The service uses regex patterns to identify issues. You can extend the patterns by subclassing:

```python
class CustomAuditService(ProductionHardeningAuditService):
    CUSTOM_PATTERNS = [
        r'CUSTOM_TODO_PATTERN',
        r'CUSTOM_DUMMY_PATTERN'
    ]
    
    def __init__(self, config):
        super().__init__(config)
        # Add custom patterns
        self._compiled_patterns[IssueType.TODO_COMMENT].extend([
            re.compile(p, re.IGNORECASE) for p in self.CUSTOM_PATTERNS
        ])
```

## Integration

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Run Production Audit
  run: |
    python scripts/production_audit.py --format json
    # Check exit code: 0=ready, 1=issues, 2=critical issues
    if [ $? -eq 2 ]; then
      echo "Critical issues found - blocking deployment"
      exit 1
    fi
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: production-audit
        name: Production Readiness Audit
        entry: python scripts/production_audit.py --dirs src
        language: system
        pass_filenames: false
```

## Report Structure

### Audit Report Fields

- `timestamp`: When the audit was performed
- `total_files_scanned`: Number of files examined
- `total_issues_found`: Total issues discovered
- `issues_by_type`: Count of each issue type
- `issues_by_severity`: Count by severity level
- `issues`: Detailed list of all issues
- `scan_duration_seconds`: Time taken for the scan
- `recommendations`: High-level recommendations
- `overall_status`: Production readiness status

### Issue Fields

- `file_path`: Path to the file containing the issue
- `line_number`: Line number where issue was found
- `issue_type`: Type of issue (TODO_COMMENT, DUMMY_LOGIC, etc.)
- `severity`: Severity level (CRITICAL, HIGH, MEDIUM, LOW, INFO)
- `description`: Human-readable description
- `code_snippet`: The problematic code
- `recommendation`: Suggested fix
- `context`: Additional context information

## Best Practices

### Regular Auditing
- Run audits during development to catch issues early
- Include in CI/CD pipeline to prevent production deployment of problematic code
- Use as part of code review process

### Issue Prioritization
1. **Critical**: Must be fixed before any production deployment
2. **High**: Should be fixed before production deployment
3. **Medium**: Should be addressed but may not block deployment
4. **Low**: Nice to fix but not blocking

### Maintenance
- Review and update patterns regularly
- Customize severity levels based on your organization's standards
- Add project-specific patterns for domain-specific issues

## Testing

The service includes comprehensive tests:

```bash
# Run unit tests
python -m pytest src/ai_karen_engine/services/__tests__/test_production_hardening_audit.py

# Run integration test
python test_audit_service.py

# Validate on real files
python validate_audit_service.py
```

## Performance

- Scans ~144 files in ~0.13 seconds
- Memory efficient with streaming file processing
- Configurable file size limits to avoid large files
- Regex pattern compilation for optimal performance

## Extensibility

The service is designed to be extensible:

1. **Custom Issue Types**: Add new issue types by extending the IssueType enum
2. **Custom Patterns**: Add regex patterns for specific issues
3. **Custom Severity Logic**: Override severity determination logic
4. **Custom Report Formats**: Add new report generation formats
5. **Language Support**: Add support for additional programming languages

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
2. **Permission Errors**: Check file system permissions for output directory
3. **Large Files**: Adjust `max_file_size_mb` setting if needed
4. **Pattern Matching**: Test regex patterns with sample code

### Debug Mode

Enable verbose logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

To contribute to the audit service:

1. Add new patterns to the appropriate pattern lists
2. Include tests for new functionality
3. Update documentation
4. Ensure backward compatibility
5. Follow the existing code style and patterns