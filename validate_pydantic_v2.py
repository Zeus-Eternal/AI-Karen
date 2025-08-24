#!/usr/bin/env python3
"""
Final validation script for Pydantic V2 compatibility
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ai_karen_engine.utils.pydantic_validator import PydanticV1Validator


def main():
    """Run final validation"""
    print("Running Pydantic V2 compatibility validation...")
    
    validator = PydanticV1Validator()
    result = validator.validate_directory("src", recursive=True)
    
    # Filter out acceptable patterns
    real_issues = []
    
    for file_result in result.get('files', []):
        violations = file_result.get('violations', [])
        for violation in violations:
            file_path = violation['file']
            line_content = violation.get('line_content', '')
            
            # Skip false positives
            if 'json_schema_extra' in line_content:
                continue
            if 'chat_memory_config.py' in file_path and 'class Config:' in line_content:
                continue  # This file has conditional V1/V2 support
            if 'pydantic_migration' in file_path or 'pydantic_validator' in file_path:
                continue  # These files contain patterns as strings
            
            if violation['severity'] == 'error':
                real_issues.append(violation)
    
    if real_issues:
        print(f"\n❌ Found {len(real_issues)} real Pydantic V1 compatibility issues:")
        for issue in real_issues:
            print(f"  - {issue['file']}:{issue['line']} - {issue['message']}")
            print(f"    Code: {issue['line_content']}")
        return False
    else:
        print("\n✅ All files are Pydantic V2 compatible!")
        return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)