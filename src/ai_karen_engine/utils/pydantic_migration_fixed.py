"""
Pydantic V2 Migration Utility - Fixed Version

This module provides utilities to automatically detect and migrate deprecated
Pydantic V1 patterns to V2 equivalents, addressing requirement 4.1-4.5.
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Set

logger = logging.getLogger(__name__)


class PydanticMigrationUtility:
    """Utility for migrating Pydantic V1 patterns to V2"""
    
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
                
            # Check for schema_extra in Config class
            if 'class Config:' in content and 'schema_extra' in content:
                line_number = content.find('schema_extra')
                line_number = content[:line_number].count('\n') + 1
                
                self.issues_found.append({
                    'file': str(file_path),
                    'line': line_number,
                    'pattern': 'Config.schema_extra usage',
                    'matched_text': 'schema_extra',
                    'suggested_fix': 'Use model_config = ConfigDict(json_schema_extra=...)',
                    'severity': 'error'
                })
            
            # Check for json_encoders in Config class
            if 'class Config:' in content and 'json_encoders' in content:
                line_number = content.find('json_encoders')
                line_number = content[:line_number].count('\n') + 1
                
                self.issues_found.append({
                    'file': str(file_path),
                    'line': line_number,
                    'pattern': 'Config.json_encoders usage',
                    'matched_text': 'json_encoders',
                    'suggested_fix': 'Use model_config = ConfigDict(json_encoders=...)',
                    'severity': 'error'
                })
                    
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
                report.append(f"    Fix: {issue['suggested_fix']}")
                report.append("")
        
        return "\n".join(report)


def main():
    """CLI entry point for the migration utility"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Pydantic V2 Migration Utility')
    parser.add_argument('--scan', action='store_true', help='Scan for deprecated patterns')
    parser.add_argument('--root', default='src', help='Root directory to scan')
    
    args = parser.parse_args()
    
    utility = PydanticMigrationUtility(args.root)
    
    if args.scan:
        issues = utility.scan_for_deprecated_patterns()
        print(utility.generate_report())
    else:
        parser.print_help()


if __name__ == '__main__':
    main()