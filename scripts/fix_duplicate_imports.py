#!/usr/bin/env python3
"""
Quick script to fix duplicate ConfigDict imports
"""

import re
from pathlib import Path

def fix_duplicate_imports(file_path):
    """Fix duplicate ConfigDict imports in a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern to match pydantic imports with potential duplicates
        pattern = r'from pydantic import ([^\n]+)'
        match = re.search(pattern, content)
        
        if match:
            imports_str = match.group(1)
            # Split imports and clean up
            imports = [imp.strip() for imp in imports_str.split(',')]
            
            # Remove duplicates while preserving order
            seen = set()
            clean_imports = []
            for imp in imports:
                if imp and imp not in seen:
                    clean_imports.append(imp)
                    seen.add(imp)
            
            # Only update if there were duplicates
            if len(clean_imports) != len(imports):
                new_imports_str = ', '.join(clean_imports)
                new_line = f'from pydantic import {new_imports_str}'
                content = content.replace(match.group(0), new_line)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"Fixed {file_path}")
                return True
        
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Fix all Python files in src directory"""
    src_dir = Path('src')
    fixed_count = 0
    
    for py_file in src_dir.rglob('*.py'):
        if fix_duplicate_imports(py_file):
            fixed_count += 1
    
    print(f"Fixed {fixed_count} files")

if __name__ == '__main__':
    main()