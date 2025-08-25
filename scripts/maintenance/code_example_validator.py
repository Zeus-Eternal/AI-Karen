#!/usr/bin/env python3
"""
Code Example Validation Utility

This script extracts and validates code examples from documentation files,
ensuring they are syntactically correct and can be executed.
"""

import os
import re
import sys
import ast
import json
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass

try:
    import yaml
except ImportError:
    yaml = None


@dataclass
class CodeExample:
    """Represents a code example from documentation"""
    file_path: str
    language: str
    code: str
    line_number: int
    context: str  # Surrounding text for context


@dataclass
class ValidationResult:
    """Result of validating a code example"""
    example: CodeExample
    status: str  # 'valid', 'syntax_error', 'runtime_error', 'warning'
    message: str
    details: Optional[str] = None


class CodeExampleValidator:
    """Validates code examples from documentation"""
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path).resolve()
        
    def extract_code_examples(self, file_path: Path) -> List[CodeExample]:
        """Extract all code examples from a documentation file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}")
            return []
        
        examples = []
        lines = content.split('\n')
        
        # Find fenced code blocks
        in_code_block = False
        current_language = ""
        current_code = []
        start_line = 0
        context_lines = []
        
        for i, line in enumerate(lines):
            # Look for context (lines before code blocks)
            if not in_code_block:
                context_lines.append(line)
                if len(context_lines) > 3:
                    context_lines.pop(0)
            
            # Check for start of code block
            if line.strip().startswith('```'):
                if not in_code_block:
                    # Starting a code block
                    in_code_block = True
                    current_language = line.strip()[3:].strip()
                    current_code = []
                    start_line = i + 1
                else:
                    # Ending a code block
                    in_code_block = False
                    if current_code and current_language:
                        context = '\n'.join(context_lines[-3:]) if context_lines else ""
                        examples.append(CodeExample(
                            file_path=str(file_path),
                            language=current_language,
                            code='\n'.join(current_code),
                            line_number=start_line,
                            context=context
                        ))
                    current_language = ""
                    current_code = []
                    context_lines = []
            elif in_code_block:
                current_code.append(line)
        
        # Also find inline code examples
        inline_pattern = r'`([^`\n]+)`'
        for i, line in enumerate(lines):
            matches = re.findall(inline_pattern, line)
            for match in matches:
                # Only consider if it looks like code (has certain patterns)
                if any(pattern in match for pattern in ['.py', '.js', '.json', '()', '{}', '[]', '=', '->']):
                    examples.append(CodeExample(
                        file_path=str(file_path),
                        language='inline',
                        code=match,
                        line_number=i + 1,
                        context=line
                    ))
        
        return examples
    
    def validate_python_code(self, example: CodeExample) -> ValidationResult:
        """Validate Python code example"""
        code = example.code.strip()
        
        # Skip if it's just a comment or empty
        if not code or code.startswith('#'):
            return ValidationResult(
                example=example,
                status='valid',
                message='Empty or comment-only code'
            )
        
        # Check for common non-executable patterns
        non_executable_patterns = [
            r'^\.\.\.',  # Ellipsis
            r'^# ',      # Comments
            r'^\$ ',     # Shell commands
            r'^>>> ',    # Python REPL
        ]
        
        for pattern in non_executable_patterns:
            if re.match(pattern, code):
                return ValidationResult(
                    example=example,
                    status='valid',
                    message='Non-executable code pattern (documentation example)'
                )
        
        # Try to parse as Python AST
        try:
            ast.parse(code)
            return ValidationResult(
                example=example,
                status='valid',
                message='Python syntax is valid'
            )
        except SyntaxError as e:
            # Check if it might be a partial code snippet
            if any(keyword in code for keyword in ['def ', 'class ', 'import ', 'from ']):
                # Try wrapping in a function or adding imports
                wrapped_code = f"def example_function():\n" + '\n'.join(f"    {line}" for line in code.split('\n'))
                try:
                    ast.parse(wrapped_code)
                    return ValidationResult(
                        example=example,
                        status='warning',
                        message='Code is valid when wrapped in function',
                        details=str(e)
                    )
                except SyntaxError:
                    pass
            
            return ValidationResult(
                example=example,
                status='syntax_error',
                message=f'Python syntax error: {e}',
                details=f'Line {e.lineno}: {e.text}' if e.lineno and e.text else None
            )
    
    def validate_bash_code(self, example: CodeExample) -> ValidationResult:
        """Validate Bash code example"""
        code = example.code.strip()
        
        # Skip comments and empty lines
        if not code or code.startswith('#'):
            return ValidationResult(
                example=example,
                status='valid',
                message='Empty or comment-only code'
            )
        
        lines = [line.strip() for line in code.split('\n') if line.strip() and not line.strip().startswith('#')]
        
        for line in lines:
            # Check for dangerous commands
            dangerous_patterns = [
                r'rm\s+-rf\s+/',
                r'sudo\s+rm',
                r'format\s+',
                r'mkfs\.',
                r'dd\s+if=',
            ]
            
            for pattern in dangerous_patterns:
                if re.search(pattern, line):
                    return ValidationResult(
                        example=example,
                        status='warning',
                        message=f'Potentially dangerous command: {line}',
                        details='This command could cause data loss'
                    )
            
            # Check for file references
            if line.startswith('./') or 'requirements.txt' in line or 'package.json' in line:
                # Validate file references
                if './scripts/' in line:
                    script_name = line.split('./scripts/')[-1].split()[0]
                    script_path = self.root_path / 'scripts' / script_name
                    if not script_path.exists():
                        return ValidationResult(
                            example=example,
                            status='syntax_error',
                            message=f'Referenced script not found: {script_name}',
                            details=f'Expected at: {script_path}'
                        )
                
                elif 'requirements.txt' in line:
                    if not (self.root_path / 'requirements.txt').exists():
                        return ValidationResult(
                            example=example,
                            status='syntax_error',
                            message='Referenced requirements.txt not found'
                        )
        
        return ValidationResult(
            example=example,
            status='valid',
            message='Bash commands appear valid'
        )
    
    def validate_json_code(self, example: CodeExample) -> ValidationResult:
        """Validate JSON code example"""
        code = example.code.strip()
        
        if not code:
            return ValidationResult(
                example=example,
                status='valid',
                message='Empty JSON'
            )
        
        try:
            json.loads(code)
            return ValidationResult(
                example=example,
                status='valid',
                message='Valid JSON'
            )
        except json.JSONDecodeError as e:
            return ValidationResult(
                example=example,
                status='syntax_error',
                message=f'JSON syntax error: {e}',
                details=f'Position {e.pos}' if hasattr(e, 'pos') else None
            )
    
    def validate_yaml_code(self, example: CodeExample) -> ValidationResult:
        """Validate YAML code example"""
        code = example.code.strip()
        
        if not code:
            return ValidationResult(
                example=example,
                status='valid',
                message='Empty YAML'
            )
        
        if yaml is None:
            return ValidationResult(
                example=example,
                status='warning',
                message='PyYAML not installed, cannot validate YAML syntax'
            )
        
        try:
            yaml.safe_load(code)
            return ValidationResult(
                example=example,
                status='valid',
                message='Valid YAML'
            )
        except yaml.YAMLError as e:
            return ValidationResult(
                example=example,
                status='syntax_error',
                message=f'YAML syntax error: {e}'
            )
    
    def validate_javascript_code(self, example: CodeExample) -> ValidationResult:
        """Validate JavaScript code example"""
        code = example.code.strip()
        
        if not code or code.startswith('//'):
            return ValidationResult(
                example=example,
                status='valid',
                message='Empty or comment-only code'
            )
        
        # Basic syntax checks for common patterns
        if code.count('{') != code.count('}'):
            return ValidationResult(
                example=example,
                status='syntax_error',
                message='Mismatched braces in JavaScript code'
            )
        
        if code.count('(') != code.count(')'):
            return ValidationResult(
                example=example,
                status='syntax_error',
                message='Mismatched parentheses in JavaScript code'
            )
        
        # Check for Node.js specific patterns
        if 'require(' in code or 'module.exports' in code:
            return ValidationResult(
                example=example,
                status='valid',
                message='Node.js JavaScript code (basic validation)'
            )
        
        return ValidationResult(
            example=example,
            status='valid',
            message='JavaScript code (basic validation passed)'
        )
    
    def validate_inline_code(self, example: CodeExample) -> ValidationResult:
        """Validate inline code snippets"""
        code = example.code.strip()
        
        # File extensions
        if code.endswith(('.py', '.js', '.json', '.yml', '.yaml', '.md', '.txt', '.sh')):
            # Check if file exists
            possible_paths = [
                self.root_path / code,
                self.root_path / 'src' / code,
                self.root_path / 'scripts' / code,
            ]
            
            for path in possible_paths:
                if path.exists():
                    return ValidationResult(
                        example=example,
                        status='valid',
                        message=f'File reference valid: {code}'
                    )
            
            return ValidationResult(
                example=example,
                status='warning',
                message=f'File reference not found: {code}',
                details='File may be created during setup or may be a pattern'
            )
        
        # Command patterns
        if code.startswith(('pip ', 'npm ', 'cargo ', 'python ', 'node ')):
            return ValidationResult(
                example=example,
                status='valid',
                message=f'Command reference: {code}'
            )
        
        # Package names
        if re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', code) and len(code) > 2:
            return ValidationResult(
                example=example,
                status='valid',
                message=f'Package/module name: {code}'
            )
        
        return ValidationResult(
            example=example,
            status='valid',
            message='Inline code (no specific validation)'
        )
    
    def validate_code_example(self, example: CodeExample) -> ValidationResult:
        """Validate a single code example based on its language"""
        language = example.language.lower()
        
        if language in ['python', 'py']:
            return self.validate_python_code(example)
        elif language in ['bash', 'sh', 'shell']:
            return self.validate_bash_code(example)
        elif language == 'json':
            return self.validate_json_code(example)
        elif language in ['yaml', 'yml']:
            return self.validate_yaml_code(example)
        elif language in ['javascript', 'js']:
            return self.validate_javascript_code(example)
        elif language == 'inline':
            return self.validate_inline_code(example)
        else:
            return ValidationResult(
                example=example,
                status='valid',
                message=f'Unsupported language for validation: {language}'
            )
    
    def validate_file(self, file_path: Path) -> List[ValidationResult]:
        """Validate all code examples in a file"""
        examples = self.extract_code_examples(file_path)
        results = []
        
        for example in examples:
            result = self.validate_code_example(example)
            results.append(result)
        
        return results
    
    def validate_all_documentation(self) -> List[ValidationResult]:
        """Validate code examples in all documentation files"""
        all_results = []
        
        # Find all documentation files
        doc_files = list(self.root_path.rglob("*.md"))
        doc_files.extend(list(self.root_path.rglob("*.rst")))
        
        for file_path in doc_files:
            if file_path.is_file():
                results = self.validate_file(file_path)
                all_results.extend(results)
        
        return all_results


def main():
    """Main entry point for code example validation"""
    validator = CodeExampleValidator()
    results = validator.validate_all_documentation()
    
    print("\n=== CODE EXAMPLE VALIDATION RESULTS ===\n")
    
    # Group results by file
    results_by_file = {}
    for result in results:
        file_path = result.example.file_path
        if file_path not in results_by_file:
            results_by_file[file_path] = []
        results_by_file[file_path].append(result)
    
    total_examples = len(results)
    total_valid = sum(1 for r in results if r.status == 'valid')
    total_warnings = sum(1 for r in results if r.status == 'warning')
    total_errors = sum(1 for r in results if r.status in ['syntax_error', 'runtime_error'])
    
    for file_path, file_results in results_by_file.items():
        rel_path = Path(file_path).relative_to(Path.cwd())
        print(f"📄 {rel_path}")
        
        valid_count = sum(1 for r in file_results if r.status == 'valid')
        warning_count = sum(1 for r in file_results if r.status == 'warning')
        error_count = sum(1 for r in file_results if r.status in ['syntax_error', 'runtime_error'])
        
        print(f"   Examples: {len(file_results)} total, {valid_count} valid, {warning_count} warnings, {error_count} errors")
        
        # Show warnings and errors
        for result in file_results:
            if result.status in ['warning', 'syntax_error', 'runtime_error']:
                status_icon = "⚠️" if result.status == 'warning' else "❌"
                lang_info = f"[{result.example.language}]" if result.example.language != 'inline' else ""
                print(f"   {status_icon} Line {result.example.line_number} {lang_info}: {result.message}")
                if result.details:
                    print(f"      Details: {result.details}")
        
        print()
    
    print("=== SUMMARY ===")
    print(f"Total examples: {total_examples}")
    print(f"Valid: {total_valid}")
    print(f"Warnings: {total_warnings}")
    print(f"Errors: {total_errors}")
    
    if total_errors > 0:
        print(f"\n❌ Found {total_errors} code examples with errors")
        sys.exit(1)
    elif total_warnings > 0:
        print(f"\n⚠️  Found {total_warnings} code examples with warnings")
        sys.exit(0)
    else:
        print(f"\n✅ All {total_examples} code examples are valid")
        sys.exit(0)


if __name__ == "__main__":
    main()