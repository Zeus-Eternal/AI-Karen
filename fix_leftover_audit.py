#!/usr/bin/env python3
"""
Fix all leftover audit operations and syntax issues
"""

import re
import os

def fix_all_issues():
    """Fix all remaining issues in model_orchestrator_routes.py"""
    
    file_path = "src/ai_karen_engine/api_routes/model_orchestrator_routes.py"
    
    if not os.path.exists(file_path):
        print(f"File {file_path} not found")
        return
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Remove all audit operations completely
    content = re.sub(
        r'await security_manager\.audit_model_operation\([^)]*\)',
        '# Removed audit operation',
        content,
        flags=re.MULTILINE | re.DOTALL
    )
    
    # Fix all return statements that are missing closing braces
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Look for return statements with opening braces
        if re.match(r'\s*return\s*\{', line):
            # Count braces to find where the return statement should end
            brace_count = line.count('{') - line.count('}')
            return_block = [line]
            j = i + 1
            
            while j < len(lines) and brace_count > 0:
                next_line = lines[j]
                return_block.append(next_line)
                brace_count += next_line.count('{') - next_line.count('}')
                
                # If we encounter except, def, class, or @, we need to close the return
                if re.match(r'\s*(except|def |class |@)', next_line) and brace_count > 0:
                    # Insert closing brace before this line
                    indent = '        '  # Standard indentation
                    return_block.insert(-1, indent + '}')
                    brace_count = 0
                    break
                j += 1
            
            # If we reached end of file and still have open braces, close them
            if brace_count > 0:
                indent = '        '
                return_block.append(indent + '}')
            
            fixed_lines.extend(return_block)
            i = j
        else:
            fixed_lines.append(line)
            i += 1
    
    content = '\n'.join(fixed_lines)
    
    # Fix specific patterns
    fixes = [
        # Fix function definitions that are missing colons
        (r'(async def \w+\([^)]*\))\s*$', r'\1:'),
        
        # Fix incomplete metadata dictionaries
        (r'metadata=\{([^}]*)\n\s+request=', r'metadata={\1}\n        # request parameter removed'),
        
        # Remove any remaining audit parameters
        (r',\s*request=http_request', ''),
        (r'request=http_request,?', ''),
        
        # Fix any remaining incomplete dictionaries
        (r'(\{[^}]*"timestamp":[^}]*)\n(\s+)(except|def|class|@)', r'\1\n\2}\n\2\3'),
    ]
    
    for pattern, replacement in fixes:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    # Write the fixed content back
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("Fixed all leftover audit operations and syntax issues")

if __name__ == "__main__":
    fix_all_issues()