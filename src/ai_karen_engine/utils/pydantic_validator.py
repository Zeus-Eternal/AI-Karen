"""
Pydantic V2 Validation Utility

This module provides validation to prevent future usage of deprecated
Pydantic V1 patterns, addressing requirements 4.4 and 4.5.
"""

import ast
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class PydanticV1Validator:
    """Validator to prevent usage of deprecated Pydantic V1 patterns"""
    
    # Patterns that should trigger validation errors
    FORBIDDEN_PATTERNS = [
        {
            'pattern': r'class Config:',
            'message': 'Use model_config = ConfigDict(...) instead of class Config:',
            'severity': 'error'
        },
        {
            'pattern': r'schema_extra\s*=',
            'message': 'Use json_schema_extra in ConfigDict instead of schema_extra',
            'severity': 'error'
        },
        {
            'pattern': r'Field\([^)]*env\s*=',
            'message': 'Use json_schema_extra={"env": "VAR"} instead of env parameter in Field',
            'severity': 'error'
        },
        {
            'pattern': r'allow_population_by_field_name\s*=',
            'message': 'Use populate_by_name in ConfigDict instead of allow_population_by_field_name',
            'severity': 'error'
        },
        {
            'pattern': r'allow_reuse\s*=',
            'message': 'allow_reuse is deprecated in Pydantic V2',
            'severity': 'warning'
        },
        {
            'pattern': r'validate_all\s*=',
            'message': 'validate_all is deprecated in Pydantic V2',
            'severity': 'warning'
        },
        {
            'pattern': r'@validator\(',
            'message': 'Use @field_validator instead of @validator',
            'severity': 'error'
        },
        {
            'pattern': r'@root_validator\(',
            'message': 'Use @model_validator instead of @root_validator',
            'severity': 'error'
        }
    ]
    
    def __init__(self):
        self.violations: List[Dict] = []
        
    def validate_file(self, file_path: str) -> Dict:
        """Validate a single file for Pydantic V2 compliance"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            return {
                'file': str(file_path),
                'valid': False,
                'error': 'File does not exist',
                'violations': []
            }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Skip files that don't use Pydantic
            if not self._contains_pydantic_imports(content):
                return {
                    'file': str(file_path),
                    'valid': True,
                    'violations': [],
                    'message': 'No Pydantic usage detected'
                }
            
            violations = self._check_violations(file_path, content)
            
            return {
                'file': str(file_path),
                'valid': len([v for v in violations if v['severity'] == 'error']) == 0,
                'violations': violations,
                'error_count': len([v for v in violations if v['severity'] == 'error']),
                'warning_count': len([v for v in violations if v['severity'] == 'warning'])
            }
            
        except Exception as e:
            logger.error(f"Error validating {file_path}: {e}")
            return {
                'file': str(file_path),
                'valid': False,
                'error': str(e),
                'violations': []
            }
    
    def _contains_pydantic_imports(self, content: str) -> bool:
        """Check if file contains Pydantic imports"""
        pydantic_imports = [
            'from pydantic import',
            'import pydantic',
            'from pydantic.',
            'BaseModel',
            'BaseSettings'
        ]
        
        return any(imp in content for imp in pydantic_imports)
    
    def _check_violations(self, file_path: Path, content: str) -> List[Dict]:
        """Check for Pydantic V1 pattern violations"""
        violations = []
        
        for pattern_info in self.FORBIDDEN_PATTERNS:
            pattern = pattern_info['pattern']
            message = pattern_info['message']
            severity = pattern_info['severity']
            
            matches = re.finditer(pattern, content, re.MULTILINE)
            
            for match in matches:
                line_number = content[:match.start()].count('\n') + 1
                line_content = content.split('\n')[line_number - 1].strip()
                
                violations.append({
                    'file': str(file_path),
                    'line': line_number,
                    'column': match.start() - content.rfind('\n', 0, match.start()) - 1,
                    'pattern': pattern,
                    'message': message,
                    'severity': severity,
                    'line_content': line_content,
                    'matched_text': match.group(0)
                })
        
        return violations
    
    def validate_directory(self, directory: str, recursive: bool = True) -> Dict:
        """Validate all Python files in a directory"""
        directory = Path(directory)
        
        if not directory.exists():
            return {
                'directory': str(directory),
                'valid': False,
                'error': 'Directory does not exist',
                'files': []
            }
        
        pattern = "**/*.py" if recursive else "*.py"
        python_files = list(directory.glob(pattern))
        
        results = []
        total_errors = 0
        total_warnings = 0
        
        for file_path in python_files:
            result = self.validate_file(file_path)
            results.append(result)
            
            if 'error_count' in result:
                total_errors += result['error_count']
            if 'warning_count' in result:
                total_warnings += result['warning_count']
        
        return {
            'directory': str(directory),
            'valid': total_errors == 0,
            'files_checked': len(python_files),
            'total_errors': total_errors,
            'total_warnings': total_warnings,
            'files': results
        }
    
    def generate_report(self, validation_result: Dict) -> str:
        """Generate a human-readable validation report"""
        if 'files' in validation_result:
            # Directory validation result
            return self._generate_directory_report(validation_result)
        else:
            # Single file validation result
            return self._generate_file_report(validation_result)
    
    def _generate_file_report(self, result: Dict) -> str:
        """Generate report for single file validation"""
        lines = [f"Pydantic V2 Validation Report for {result['file']}", "=" * 50]
        
        if result.get('error'):
            lines.append(f"ERROR: {result['error']}")
            return "\n".join(lines)
        
        if result.get('message'):
            lines.append(result['message'])
            return "\n".join(lines)
        
        violations = result.get('violations', [])
        
        if not violations:
            lines.append("✅ No Pydantic V1 patterns detected")
            return "\n".join(lines)
        
        error_count = result.get('error_count', 0)
        warning_count = result.get('warning_count', 0)
        
        lines.append(f"Found {len(violations)} issues ({error_count} errors, {warning_count} warnings):")
        lines.append("")
        
        for violation in violations:
            severity_icon = "❌" if violation['severity'] == 'error' else "⚠️"
            lines.append(f"{severity_icon} Line {violation['line']}: {violation['message']}")
            lines.append(f"   Pattern: {violation['pattern']}")
            lines.append(f"   Code: {violation['line_content']}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_directory_report(self, result: Dict) -> str:
        """Generate report for directory validation"""
        lines = [f"Pydantic V2 Validation Report for {result['directory']}", "=" * 50]
        
        if result.get('error'):
            lines.append(f"ERROR: {result['error']}")
            return "\n".join(lines)
        
        files_checked = result.get('files_checked', 0)
        total_errors = result.get('total_errors', 0)
        total_warnings = result.get('total_warnings', 0)
        
        lines.append(f"Checked {files_checked} Python files")
        lines.append(f"Found {total_errors} errors and {total_warnings} warnings")
        lines.append("")
        
        if total_errors == 0 and total_warnings == 0:
            lines.append("✅ All files are Pydantic V2 compliant!")
            return "\n".join(lines)
        
        # Group violations by file
        files_with_issues = [f for f in result['files'] if f.get('violations')]
        
        for file_result in files_with_issues:
            violations = file_result.get('violations', [])
            if not violations:
                continue
                
            lines.append(f"📁 {file_result['file']}")
            
            for violation in violations:
                severity_icon = "❌" if violation['severity'] == 'error' else "⚠️"
                lines.append(f"  {severity_icon} Line {violation['line']}: {violation['message']}")
            
            lines.append("")
        
        return "\n".join(lines)


class PydanticV2PreCommitHook:
    """Pre-commit hook to validate Pydantic V2 compliance"""
    
    def __init__(self):
        self.validator = PydanticV1Validator()
    
    def check_files(self, file_paths: List[str]) -> bool:
        """Check multiple files and return True if all are valid"""
        all_valid = True
        
        for file_path in file_paths:
            if not file_path.endswith('.py'):
                continue
                
            result = self.validator.validate_file(file_path)
            
            if not result.get('valid', False):
                all_valid = False
                print(f"❌ {file_path}: Pydantic V1 patterns detected")
                
                violations = result.get('violations', [])
                for violation in violations:
                    if violation['severity'] == 'error':
                        print(f"   Line {violation['line']}: {violation['message']}")
            else:
                print(f"✅ {file_path}: Pydantic V2 compliant")
        
        return all_valid


def create_pre_commit_hook() -> str:
    """Create a pre-commit hook script"""
    hook_script = '''#!/usr/bin/env python3
"""
Pre-commit hook to validate Pydantic V2 compliance
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from ai_karen_engine.utils.pydantic_validator import PydanticV2PreCommitHook

def main():
    """Main entry point for pre-commit hook"""
    if len(sys.argv) < 2:
        print("Usage: pydantic_v2_hook.py <file1> <file2> ...")
        sys.exit(1)
    
    hook = PydanticV2PreCommitHook()
    files_to_check = sys.argv[1:]
    
    if hook.check_files(files_to_check):
        print("✅ All files are Pydantic V2 compliant")
        sys.exit(0)
    else:
        print("❌ Some files contain deprecated Pydantic V1 patterns")
        print("Run 'python -m ai_karen_engine.utils.pydantic_migration --migrate' to fix them")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    return hook_script


def main():
    """CLI entry point for the validator"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Pydantic V2 Validation Utility')
    parser.add_argument('path', help='File or directory to validate')
    parser.add_argument('--recursive', action='store_true', help='Recursively validate directory')
    parser.add_argument('--create-hook', action='store_true', help='Create pre-commit hook')
    
    args = parser.parse_args()
    
    if args.create_hook:
        hook_content = create_pre_commit_hook()
        hook_path = Path('.git/hooks/pre-commit')
        
        if hook_path.parent.exists():
            with open(hook_path, 'w') as f:
                f.write(hook_content)
            hook_path.chmod(0o755)
            print(f"Created pre-commit hook at {hook_path}")
        else:
            print("Error: .git/hooks directory not found")
        return
    
    validator = PydanticV1Validator()
    path = Path(args.path)
    
    if path.is_file():
        result = validator.validate_file(args.path)
        print(validator.generate_report(result))
        
        if not result.get('valid', False):
            sys.exit(1)
            
    elif path.is_dir():
        result = validator.validate_directory(args.path, recursive=args.recursive)
        print(validator.generate_report(result))
        
        if not result.get('valid', False):
            sys.exit(1)
    else:
        print(f"Error: {args.path} is not a valid file or directory")
        sys.exit(1)


if __name__ == '__main__':
    import sys
    main()