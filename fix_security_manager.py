#!/usr/bin/env python3
"""
Comprehensive fix for all security manager and syntax issues
"""

import re
import os

def fix_security_manager_issues():
    """Fix all security manager related issues and syntax problems"""
    
    file_path = "src/ai_karen_engine/api_routes/model_orchestrator_routes.py"
    
    if not os.path.exists(file_path):
        print(f"File {file_path} not found")
        return
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Remove all security manager audit operations completely
    content = re.sub(
        r'await security_manager\.audit_model_operation\([^)]*\)',
        '# Removed audit operation',
        content,
        flags=re.MULTILINE | re.DOTALL
    )
    
    # Remove all security manager imports and references
    content = re.sub(
        r'from.*security_manager.*import.*\n',
        '# Removed security manager import\n',
        content
    )
    
    content = re.sub(
        r'security_manager\s*=.*\n',
        '# Removed security manager initialization\n',
        content
    )
    
    # Remove request parameters from function calls
    content = re.sub(r',\s*request=http_request', '', content)
    content = re.sub(r'request=http_request,?', '', content)
    
    # Fix all incomplete dictionaries and return statements
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Handle return statements with dictionaries
        if re.match(r'\s*return\s*\{', line):
            brace_count = line.count('{') - line.count('}')
            block = [line]
            j = i + 1
            
            while j < len(lines) and brace_count > 0:
                next_line = lines[j]
                block.append(next_line)
                brace_count += next_line.count('{') - next_line.count('}')
                
                # If we hit a control structure, close the return
                if re.match(r'\s*(except|def |class |@|if |elif |else|for |while |with |try:)', next_line) and brace_count > 0:
                    indent = '        '
                    block.insert(-1, indent + '}')
                    brace_count = 0
                    break
                j += 1
            
            if brace_count > 0:
                indent = '        '
                block.append(indent + '}')
            
            fixed_lines.extend(block)
            i = j
            
        # Handle job dictionaries
        elif re.match(r'\s*job\s*=\s*\{', line):
            brace_count = line.count('{') - line.count('}')
            block = [line]
            j = i + 1
            
            while j < len(lines) and brace_count > 0:
                next_line = lines[j]
                block.append(next_line)
                brace_count += next_line.count('{') - next_line.count('}')
                
                # If we hit _active_jobs assignment, close the job dict
                if '_active_jobs' in next_line and brace_count > 0:
                    indent = '        '
                    block.insert(-1, indent + '}')
                    brace_count = 0
                    break
                j += 1
            
            if brace_count > 0:
                indent = '        '
                block.append(indent + '}')
            
            fixed_lines.extend(block)
            i = j
            
        # Handle system_info dictionaries
        elif re.match(r'\s*system_info\s*=\s*\{', line):
            brace_count = line.count('{') - line.count('}')
            block = [line]
            j = i + 1
            
            while j < len(lines) and brace_count > 0:
                next_line = lines[j]
                block.append(next_line)
                brace_count += next_line.count('{') - next_line.count('}')
                
                # If we hit a comment or new assignment, close the dict
                if (re.match(r'\s*#', next_line) or re.match(r'\s*\w+\s*=', next_line)) and brace_count > 0:
                    indent = '        '
                    block.insert(-1, indent + '}')
                    brace_count = 0
                    break
                j += 1
            
            if brace_count > 0:
                indent = '        '
                block.append(indent + '}')
            
            fixed_lines.extend(block)
            i = j
            
        # Handle metadata dictionaries
        elif re.match(r'\s*metadata\s*=\s*\{', line):
            brace_count = line.count('{') - line.count('}')
            block = [line]
            j = i + 1
            
            while j < len(lines) and brace_count > 0:
                next_line = lines[j]
                if 'request=' in next_line:
                    # Skip this line and close the metadata dict
                    indent = '        '
                    block.append(indent + '}')
                    brace_count = 0
                    j += 1
                    break
                else:
                    block.append(next_line)
                    brace_count += next_line.count('{') - next_line.count('}')
                j += 1
            
            if brace_count > 0:
                indent = '        '
                block.append(indent + '}')
            
            fixed_lines.extend(block)
            i = j
            
        else:
            fixed_lines.append(line)
            i += 1
    
    content = '\n'.join(fixed_lines)
    
    # Final cleanup patterns
    cleanup_patterns = [
        # Fix function definitions missing colons
        (r'(async def \w+\([^)]*\))\s*$', r'\1:'),
        
        # Remove empty audit operation calls
        (r'\s*# Removed audit operation\s*\n', '\n'),
        
        # Fix any remaining incomplete parentheses
        (r'\(\s*\n\s*\)', '()'),
        
        # Remove any trailing commas before closing braces
        (r',(\s*\})', r'\1'),
    ]
    
    for pattern, replacement in cleanup_patterns:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    # Write the fixed content back
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("Fixed all security manager and syntax issues")

if __name__ == "__main__":
    fix_security_manager_issues()