#!/usr/bin/env python3
"""
Aggressive cleanup of all audit operations
"""

import re

def aggressive_cleanup():
    file_path = "src/ai_karen_engine/api_routes/model_orchestrator_routes.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Remove entire audit operation blocks
    # Pattern to match: await security_manager.audit_model_operation( ... )
    pattern = r'await security_manager\.audit_model_operation\(\s*\n(?:[^)]*\n)*\s*\)'
    content = re.sub(pattern, '# Removed audit operation', content, flags=re.MULTILINE | re.DOTALL)
    
    # Remove any remaining standalone audit parameters
    lines = content.split('\n')
    cleaned_lines = []
    skip_until_close = False
    
    for line in lines:
        if 'await security_manager.audit_model_operation(' in line:
            skip_until_close = True
            cleaned_lines.append('        # Removed audit operation')
            continue
        
        if skip_until_close:
            if line.strip() == ')':
                skip_until_close = False
            continue
        
        # Skip standalone audit parameters
        if any(param in line for param in ['operation=', 'metadata=', 'model_id=', 'request=request']):
            if not any(keyword in line for keyword in ['def ', 'class ', 'return ', 'if ', 'for ', 'while ']):
                continue
        
        cleaned_lines.append(line)
    
    content = '\n'.join(cleaned_lines)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("Aggressive cleanup completed")

if __name__ == "__main__":
    aggressive_cleanup()