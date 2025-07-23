#!/usr/bin/env python3
"""
Documentation Validation Utilities

This script validates README files for consistency with the actual implementation,
checks links, and validates code examples.
"""

import os
import re
import json
import subprocess
import sys
import ast
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass
from urllib.parse import urlparse
import requests
import tempfile


@dataclass
class ValidationResult:
    """Container for validation results"""
    file_path: str
    issues: List[str]
    warnings: List[str]
    passed_checks: List[str]


class DocumentationValidator:
    """Validates README files against actual implementation"""
    
    def __init__(self, root_path: str = ".", system_info_file: str = "system_analysis.json"):
        self.root_path = Path(root_path).resolve()
        self.system_info = self._load_system_info(system_info_file)
        
    def _load_system_info(self, system_info_file: str) -> Dict[str, Any]:
        """Load system information from analysis"""
        try:
            with open(system_info_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: {system_info_file} not found. Run doc_analysis.py first.")
            return {}
    
    def validate_readme_file(self, readme_path: Path) -> ValidationResult:
        """Validate a single README file"""
        issues = []
        warnings = []
        passed_checks = []
        
        if not readme_path.exists():
            return ValidationResult(
                file_path=str(readme_path),
                issues=[f"README file does not exist: {readme_path}"],
                warnings=[],
                passed_checks=[]
            )
        
        try:
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return ValidationResult(
                file_path=str(readme_path),
                issues=[f"Could not read file: {e}"],
                warnings=[],
                passed_checks=[]
            )
        
        # Validate dependencies
        dep_issues, dep_warnings, dep_passed = self._validate_dependencies(content, readme_path)
        issues.extend(dep_issues)
        warnings.extend(dep_warnings)
        passed_checks.extend(dep_passed)
        
        # Validate links
        link_issues, link_warnings, link_passed = self._validate_links(content, readme_path)
        issues.extend(link_issues)
        warnings.extend(link_warnings)
        passed_checks.extend(link_passed)
        
        # Validate code examples
        code_issues, code_warnings, code_passed = self._validate_code_examples(content, readme_path)
        issues.extend(code_issues)
        warnings.extend(code_warnings)
        passed_checks.extend(code_passed)
        
        # Validate file references
        file_issues, file_warnings, file_passed = self._validate_file_references(content, readme_path)
        issues.extend(file_issues)
        warnings.extend(file_warnings)
        passed_checks.extend(file_passed)
        
        return ValidationResult(
            file_path=str(readme_path),
            issues=issues,
            warnings=warnings,
            passed_checks=passed_checks
        )
    
    def _validate_dependencies(self, content: str, readme_path: Path) -> Tuple[List[str], List[str], List[str]]:
        """Validate dependency information in README"""
        issues = []
        warnings = []
        passed_checks = []
        
        if not self.system_info:
            warnings.append("No system info available for dependency validation")
            return issues, warnings, passed_checks
        
        # Check Python dependencies
        python_deps = self.system_info.get('python_dependencies', {})
        
        # Look for version specifications in README
        version_patterns = [
            r'(\w+)==([\d\.]+)',  # package==1.0.0
            r'(\w+)\s+([\d\.]+)',  # package 1.0.0
            r'`(\w+)==([\d\.]+)`',  # `package==1.0.0`
        ]
        
        for pattern in version_patterns:
            matches = re.findall(pattern, content)
            for package, version in matches:
                if package in python_deps:
                    actual_version = python_deps[package]
                    if actual_version != version and actual_version != "latest":
                        if actual_version.startswith('>='):
                            # Handle >= constraints
                            continue
                        issues.append(f"Version mismatch for {package}: README shows {version}, actual is {actual_version}")
                    else:
                        passed_checks.append(f"Version correct for {package}: {version}")
                else:
                    warnings.append(f"Package {package} mentioned in README but not found in requirements")
        
        # Check for outdated technology mentions
        outdated_tech = {
            'python 2': 'Python 2 is deprecated',
            'node.js 12': 'Node.js 12 is deprecated',
            'node.js 14': 'Node.js 14 is deprecated',
        }
        
        content_lower = content.lower()
        for tech, message in outdated_tech.items():
            if tech in content_lower:
                warnings.append(f"Outdated technology reference: {message}")
        
        return issues, warnings, passed_checks
    
    def _validate_links(self, content: str, readme_path: Path) -> Tuple[List[str], List[str], List[str]]:
        """Validate links in README"""
        issues = []
        warnings = []
        passed_checks = []
        
        # Find all markdown links
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        links = re.findall(link_pattern, content)
        
        for link_text, link_url in links:
            # Skip anchor links
            if link_url.startswith('#'):
                continue
                
            # Handle relative file links
            if not link_url.startswith(('http://', 'https://', 'mailto:')):
                # Resolve relative to README location
                if readme_path.name == 'README.md':
                    base_path = readme_path.parent
                else:
                    base_path = self.root_path
                
                target_path = base_path / link_url
                
                if target_path.exists():
                    passed_checks.append(f"Internal link valid: {link_url}")
                else:
                    issues.append(f"Broken internal link: {link_url} (from {readme_path.name})")
            
            # Handle external links (basic check)
            elif link_url.startswith(('http://', 'https://')):
                try:
                    # Basic URL validation
                    parsed = urlparse(link_url)
                    if parsed.scheme and parsed.netloc:
                        passed_checks.append(f"External link format valid: {link_url}")
                    else:
                        issues.append(f"Invalid URL format: {link_url}")
                except Exception:
                    issues.append(f"Invalid URL format: {link_url}")
        
        return issues, warnings, passed_checks
    
    def _validate_code_examples(self, content: str, readme_path: Path) -> Tuple[List[str], List[str], List[str]]:
        """Validate code examples in README"""
        issues = []
        warnings = []
        passed_checks = []
        
        # Find code blocks
        code_block_pattern = r'```(\w+)?\n(.*?)\n```'
        code_blocks = re.findall(code_block_pattern, content, re.DOTALL)
        
        for language, code in code_blocks:
            if language == 'bash' or language == '':
                # Validate bash commands
                bash_issues, bash_warnings, bash_passed = self._validate_bash_commands(code)
                issues.extend(bash_issues)
                warnings.extend(bash_warnings)
                passed_checks.extend(bash_passed)
            
            elif language == 'python':
                # Validate Python code
                python_issues, python_warnings, python_passed = self._validate_python_code(code)
                issues.extend(python_issues)
                warnings.extend(python_warnings)
                passed_checks.extend(python_passed)
            
            elif language == 'json':
                # Validate JSON
                try:
                    json.loads(code)
                    passed_checks.append("JSON code block is valid")
                except json.JSONDecodeError as e:
                    issues.append(f"Invalid JSON in code block: {e}")
        
        return issues, warnings, passed_checks
    
    def _validate_bash_commands(self, code: str) -> Tuple[List[str], List[str], List[str]]:
        """Validate bash commands"""
        issues = []
        warnings = []
        passed_checks = []
        
        lines = code.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Check for common command patterns
            if line.startswith('./scripts/'):
                script_path = self.root_path / line[2:]  # Remove './'
                if script_path.exists():
                    passed_checks.append(f"Script exists: {line}")
                else:
                    issues.append(f"Script not found: {line}")
            
            elif 'requirements.txt' in line:
                if (self.root_path / 'requirements.txt').exists():
                    passed_checks.append("requirements.txt referenced and exists")
                else:
                    issues.append("requirements.txt referenced but not found")
            
            elif 'package.json' in line:
                # Check if any package.json exists
                if list(self.root_path.rglob('package.json')):
                    passed_checks.append("package.json referenced and exists")
                else:
                    warnings.append("package.json referenced but not found")
            
            # Check for potentially dangerous commands
            dangerous_commands = ['rm -rf /', 'sudo rm', 'format', 'mkfs']
            for dangerous in dangerous_commands:
                if dangerous in line:
                    warnings.append(f"Potentially dangerous command: {line}")
        
        return issues, warnings, passed_checks
    
    def _validate_python_code(self, code: str) -> Tuple[List[str], List[str], List[str]]:
        """Validate Python code examples"""
        issues = []
        warnings = []
        passed_checks = []
        
        try:
            # Try to parse the Python code
            ast.parse(code)
            passed_checks.append("Python code syntax is valid")
        except SyntaxError as e:
            issues.append(f"Python syntax error: {e}")
        
        # Check for imports that should exist
        import_pattern = r'from\s+(\S+)\s+import|import\s+(\S+)'
        imports = re.findall(import_pattern, code)
        
        for from_module, import_module in imports:
            module = from_module or import_module
            module = module.split('.')[0]  # Get base module
            
            # Check if it's a standard library or known dependency
            if module in self.system_info.get('python_dependencies', {}):
                passed_checks.append(f"Import {module} is in dependencies")
            elif module in ['os', 'sys', 'json', 're', 'pathlib', 'typing']:
                passed_checks.append(f"Import {module} is standard library")
            else:
                warnings.append(f"Import {module} not found in dependencies")
        
        return issues, warnings, passed_checks
    
    def _validate_file_references(self, content: str, readme_path: Path) -> Tuple[List[str], List[str], List[str]]:
        """Validate file and directory references"""
        issues = []
        warnings = []
        passed_checks = []
        
        # Find file/directory references in backticks
        file_pattern = r'`([^`]+\.(py|js|json|yml|yaml|md|txt|sh|toml))`'
        file_refs = re.findall(file_pattern, content)
        
        for file_ref, ext in file_refs:
            # Try to find the file
            possible_paths = [
                self.root_path / file_ref,
                readme_path.parent / file_ref,
            ]
            
            found = False
            for path in possible_paths:
                if path.exists():
                    passed_checks.append(f"File reference valid: {file_ref}")
                    found = True
                    break
            
            if not found:
                # Check if it's a pattern that might exist
                if '*' in file_ref or file_ref.endswith('/'):
                    warnings.append(f"File pattern reference (not validated): {file_ref}")
                else:
                    issues.append(f"File reference not found: {file_ref}")
        
        # Find directory references
        dir_pattern = r'`([^`]+/)`'
        dir_refs = re.findall(dir_pattern, content)
        
        for dir_ref in dir_refs:
            dir_path = self.root_path / dir_ref.rstrip('/')
            if dir_path.exists() and dir_path.is_dir():
                passed_checks.append(f"Directory reference valid: {dir_ref}")
            else:
                issues.append(f"Directory reference not found: {dir_ref}")
        
        return issues, warnings, passed_checks
    
    def validate_all_readmes(self) -> List[ValidationResult]:
        """Validate all README files in the project"""
        results = []
        
        # Find all README files
        readme_files = list(self.root_path.rglob("README.md"))
        readme_files.extend(list(self.root_path.rglob("readme.md")))
        
        for readme_file in readme_files:
            result = self.validate_readme_file(readme_file)
            results.append(result)
        
        return results


def main():
    """Main entry point for documentation validation"""
    validator = DocumentationValidator()
    results = validator.validate_all_readmes()
    
    print("\n=== DOCUMENTATION VALIDATION RESULTS ===\n")
    
    total_issues = 0
    total_warnings = 0
    total_passed = 0
    
    for result in results:
        rel_path = Path(result.file_path).relative_to(Path.cwd())
        print(f"📄 {rel_path}")
        
        if result.issues:
            print("  ❌ Issues:")
            for issue in result.issues:
                print(f"    • {issue}")
            total_issues += len(result.issues)
        
        if result.warnings:
            print("  ⚠️  Warnings:")
            for warning in result.warnings:
                print(f"    • {warning}")
            total_warnings += len(result.warnings)
        
        if result.passed_checks:
            print(f"  ✅ Passed: {len(result.passed_checks)} checks")
            total_passed += len(result.passed_checks)
        
        print()
    
    print("=== SUMMARY ===")
    print(f"Files validated: {len(results)}")
    print(f"Total issues: {total_issues}")
    print(f"Total warnings: {total_warnings}")
    print(f"Total passed checks: {total_passed}")
    
    if total_issues > 0:
        print("\n❌ Validation failed with issues")
        sys.exit(1)
    elif total_warnings > 0:
        print("\n⚠️  Validation passed with warnings")
        sys.exit(0)
    else:
        print("\n✅ All validations passed")
        sys.exit(0)


if __name__ == "__main__":
    main()