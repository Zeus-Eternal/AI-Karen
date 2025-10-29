#!/usr/bin/env python3
"""
Remove all remaining audit operations completely
"""

def remove_all_audits():
    file_path = "src/ai_karen_engine/api_routes/model_orchestrator_routes.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    lines = content.split('\n')
    cleaned_lines = []
    skip_block = False
    brace_count = 0
    paren_count = 0
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Start skipping when we see an audit operation
        if 'await security_manager.audit_model_operation(' in line:
            skip_block = True
            brace_count = 0
            paren_count = 1  # Start with 1 for the opening paren
            cleaned_lines.append('        # Removed audit operation')
            i += 1
            continue
        
        if skip_block:
            # Count braces and parentheses to know when the block ends
            brace_count += line.count('{') - line.count('}')
            paren_count += line.count('(') - line.count(')')
            
            # If we've closed all braces and parentheses, stop skipping
            if brace_count <= 0 and paren_count <= 0:
                skip_block = False
            i += 1
            continue
        
        cleaned_lines.append(line)
        i += 1
    
    content = '\n'.join(cleaned_lines)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("Removed all audit operations")

if __name__ == "__main__":
    remove_all_audits()