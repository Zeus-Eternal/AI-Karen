"""
Pydantic V2 Migration Utility

This module provides utilities to automatically detect and migrate deprecated
Pydantic V1 patterns to V2 equivalents, addressing requirement 4.1-4.5.
"""

import ast
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class PydanticV1Pattern:
    """Represents a deprecated Pydantic V1 pattern"""
    
    def __init__(self, pattern: str, replacement: str, description: str):
        self.pattern = pattern
        self.replacement = replacement
        self.description = description


class PydanticMigrationUtility:
    """Utility for migrating Pydantic V1 patterns to V2"""
    
    # Define deprecated patterns and their V2 replacements
    DEPRECATED_PATTERNS = [
        PydanticV1Pattern(
            pattern=r'class Config:\s*\n\s*schema_extra\s*=\s*({[^}]*})',
            replacement=r'model_config = ConfigDict(\n        json_schema_extra=\1\n    )',
            description="Replace Config.schema_extra with model_config.json_schema_extra"
        ),
        PydanticV1Pattern(
            pattern=r'class Config:\s*\n\s*json_encoders\s*=\s*({[^}]*})',
            replacement=r'model_config = ConfigDict(\n        json_encoders=\1\n    )',
            description="Replace Config.json_encoders with model_config.json_encoders"
        ),
        PydanticV1Pattern(
            pattern=r'class Config:\s*\n\s*extra\s*=\s*["\'](\w+)["\']',
            replacement=r'model_config = ConfigDict(extra="\1")',
            description="Replace Config.extra with model_config.extra"
        ),
        PydanticV1Pattern(
            pattern=r'class Config:\s*\n\s*allow_population_by_field_name\s*=\s*(True|False)',
            replacement=r'model_config = ConfigDict(populate_by_name=\1)',
            description="Replace Config.allow_population_by_field_name with model_config.populate_by_name"
        ),
        PydanticV1Pattern(
            pattern=r'class Config:\s*\n\s*use_enum_values\s*=\s*(True|False)',
            replacement=r'model_config = ConfigDict(use_enum_values=\1)',
            description="Replace Config.use_enum_values with model_config.use_enum_values"
        ),
        PydanticV1Pattern(
            pattern=r'from pydantic import ([^\n]+BaseModel[^\n]*)',
            replacement=r'from pydantic import \1, ConfigDict',
            description="Add ConfigDict import when BaseModel is imported"
        ),
    ]
    
    def __init__(self, root_path: str = "src"):
        self.root_path = Path(root_path)
        self.issues_found: List[Dict] = []
        self.files_processed: Set[str] = set()
        
    def scan_for_deprecated_patterns(self) -> List[Dict]:
        """Scan all Python files for deprecated Pydantic V1 patterns"""
        logger.info(f"Scanning for deprecated Pydantic patterns in {self.root_path}")
        
        self.issues_found.clear()
        self.files_processed.clear()
        
        # Find all Python files
        python_files = list(self.root_path.rglob("*.py"))
        
        for file_path in python_files:
            try:
                self._scan_file(file_path)
            except Exception as e:
                logger.error(f"Error scanning {file_path}: {e}")
                
        logger.info(f"Scanned {len(self.files_processed)} files, found {len(self.issues_found)} issues")
        return self.issues_found
    
    def _scan_file(self, file_path: Path) -> None:
        """Scan a single file for deprecated patterns"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            self.files_processed.add(str(file_path))
            
            # Check if file contains Pydantic imports
            if not self._contains_pydantic_imports(content):
                return
                
            # Check for deprecated patterns
            for pattern in self.DEPRECATED_PATTERNS:
                matches = re.finditer(pattern.pattern, content, re.MULTILINE | re.DOTALL)
                for match in matches:
                    line_number = content[:match.start()].count('\n') + 1
                    
                    self.issues_found.append({
                        'file': str(file_path),
                        'line': line_number,
                        'pattern': pattern.description,
                        'matched_text': match.group(0),
                        'suggested_fix': pattern.replacement,
                        'severity': 'warning'
                    })
                    
            # Check for specific deprecated Field usage
            self._check_deprecated_field_usage(file_path, content)
            
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
    
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
    
    def _check_deprecated_field_usage(self, file_path: Path, content: str) -> None:
        """Check for deprecated Field parameter usage"""
        # Check for deprecated 'env' parameter in Field
        env_pattern = r'Field\([^)]*env\s*=\s*["\'][^"\']*["\'][^)]*\)'
        matches = re.finditer(env_pattern, content)
        
        for match in matches:
            line_number = content[:match.start()].count('\n') + 1
            self.issues_found.append({
                'file': str(file_path),
                'line': line_number,
                'pattern': 'Deprecated Field env parameter',
                'matched_text': match.group(0),
                'suggested_fix': 'Use json_schema_extra={"env": "ENV_VAR"} instead',
                'severity': 'warning'
            })
    
    def migrate_file(self, file_path: str, dry_run: bool = True) -> Dict:
        """Migrate a single file to Pydantic V2 patterns"""
        file_path = Path(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
                
            modified_content = original_content
            changes_made = []
            
            # Apply each migration pattern
            for pattern in self.DEPRECATED_PATTERNS:
                matches = list(re.finditer(pattern.pattern, modified_content, re.MULTILINE | re.DOTALL))
                
                if matches:
                    # Apply replacements in reverse order to maintain positions
                    for match in reversed(matches):
                        old_text = match.group(0)
                        new_text = re.sub(pattern.pattern, pattern.replacement, old_text, flags=re.MULTILINE | re.DOTALL)
                        
                        modified_content = (
                            modified_content[:match.start()] + 
                            new_text + 
                            modified_content[match.end():]
                        )
                        
                        changes_made.append({
                            'pattern': pattern.description,
                            'line': original_content[:match.start()].count('\n') + 1,
                            'old': old_text.strip(),
                            'new': new_text.strip()
                        })
            
            # Ensure ConfigDict import is added if needed
            if changes_made and 'ConfigDict' not in original_content:
                modified_content = self._add_configdict_import(modified_content)
                changes_made.append({
                    'pattern': 'Add ConfigDict import',
                    'line': 1,
                    'old': '',
                    'new': 'Added ConfigDict to pydantic imports'
                })
            
            # Write changes if not dry run
            if not dry_run and changes_made:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
                    
                logger.info(f"Migrated {file_path} with {len(changes_made)} changes")
            
            return {
                'file': str(file_path),
                'changes_made': len(changes_made),
                'changes': changes_made,
                'success': True,
                'dry_run': dry_run
            }
            
        except Exception as e:
            logger.error(f"Error migrating {file_path}: {e}")
            return {
                'file': str(file_path),
                'changes_made': 0,
                'changes': [],
                'success': False,
                'error': str(e),
                'dry_run': dry_run
            }
    
    def _add_configdict_import(self, content: str) -> str:
        """Add ConfigDict import to existing pydantic imports"""
        # Look for existing pydantic imports
        pydantic_import_pattern = r'from pydantic import ([^\n]+)'
        match = re.search(pydantic_import_pattern, content)
        
        if match:
            imports = match.group(1)
            if 'ConfigDict' not in imports:
                # Clean up any duplicate imports and add ConfigDict
                import_list = [imp.strip() for imp in imports.split(',')]
                if 'ConfigDict' not in import_list:
                    import_list.append('ConfigDict')
                # Remove duplicates while preserving order
                seen = set()
                clean_imports = []
                for imp in import_list:
                    if imp not in seen:
                        clean_imports.append(imp)
                        seen.add(imp)
                new_imports = ', '.join(clean_imports)
                content = content.replace(match.group(0), f'from pydantic import {new_imports}')
        
        return content
    
    def migrate_all_files(self, dry_run: bool = True) -> Dict:
        """Migrate all files in the project"""
        logger.info(f"Starting migration of all files (dry_run={dry_run})")
        
        # First scan for issues
        issues = self.scan_for_deprecated_patterns()
        
        if not issues:
            logger.info("No deprecated patterns found")
            return {
                'files_processed': 0,
                'total_changes': 0,
                'results': [],
                'success': True
            }
        
        # Get unique files that need migration
        files_to_migrate = set(issue['file'] for issue in issues)
        
        results = []
        total_changes = 0
        
        for file_path in files_to_migrate:
            result = self.migrate_file(file_path, dry_run=dry_run)
            results.append(result)
            total_changes += result['changes_made']
        
        logger.info(f"Migration complete: {len(files_to_migrate)} files, {total_changes} changes")
        
        return {
            'files_processed': len(files_to_migrate),
            'total_changes': total_changes,
            'results': results,
            'success': True
        }
    
    def generate_report(self) -> str:
        """Generate a detailed migration report"""
        if not self.issues_found:
            return "No deprecated Pydantic patterns found."
        
        report = ["Pydantic V2 Migration Report", "=" * 30, ""]
        
        # Group issues by file
        files_with_issues = {}
        for issue in self.issues_found:
            file_path = issue['file']
            if file_path not in files_with_issues:
                files_with_issues[file_path] = []
            files_with_issues[file_path].append(issue)
        
        report.append(f"Found {len(self.issues_found)} deprecated patterns in {len(files_with_issues)} files:")
        report.append("")
        
        for file_path, file_issues in files_with_issues.items():
            report.append(f"File: {file_path}")
            report.append("-" * (len(file_path) + 6))
            
            for issue in file_issues:
                report.append(f"  Line {issue['line']}: {issue['pattern']}")
                report.append(f"    Current: {issue['matched_text'][:100]}...")
                report.append(f"    Fix: {issue['suggested_fix']}")
                report.append("")
        
        return "\n".join(report)


def validate_pydantic_v2_compliance(file_path: str) -> Dict:
    """Validate that a file complies with Pydantic V2 patterns"""
    utility = PydanticMigrationUtility()
    utility._scan_file(Path(file_path))
    
    return {
        'file': file_path,
        'compliant': len(utility.issues_found) == 0,
        'issues': utility.issues_found
    }


def main():
    """CLI entry point for the migration utility"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Pydantic V2 Migration Utility')
    parser.add_argument('--scan', action='store_true', help='Scan for deprecated patterns')
    parser.add_argument('--migrate', action='store_true', help='Migrate files to V2')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without applying them')
    parser.add_argument('--file', help='Process specific file')
    parser.add_argument('--root', default='src', help='Root directory to scan')
    
    args = parser.parse_args()
    
    utility = PydanticMigrationUtility(args.root)
    
    if args.scan:
        issues = utility.scan_for_deprecated_patterns()
        print(utility.generate_report())
        
    elif args.migrate:
        if args.file:
            result = utility.migrate_file(args.file, dry_run=args.dry_run)
            print(f"Migration result for {args.file}:")
            print(f"  Changes made: {result['changes_made']}")
            if result['changes']:
                for change in result['changes']:
                    print(f"    {change['pattern']} at line {change['line']}")
        else:
            result = utility.migrate_all_files(dry_run=args.dry_run)
            print(f"Migration complete:")
            print(f"  Files processed: {result['files_processed']}")
            print(f"  Total changes: {result['total_changes']}")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()