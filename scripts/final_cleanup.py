#!/usr/bin/env python3
"""
Final cleanup - remove all orphaned parameters
"""

def final_cleanup():
    file_path = "src/ai_karen_engine/api_routes/model_orchestrator_routes.py"
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    cleaned_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Skip lines that are clearly orphaned parameters
        stripped = line.strip()
        if (stripped.startswith('"') and stripped.endswith('",') or
            stripped.startswith('"') and stripped.endswith('"') or
            stripped in ['},', '}', ')', '),'] or
            'request=http_request' in stripped or
            'request=request' in stripped):
            # Check if this looks like an orphaned parameter
            if i > 0:
                prev_line = lines[i-1].strip()
                if (prev_line.endswith(')') or 
                    'logger.info(' in prev_line or
                    prev_line.startswith('#')):
                    i += 1
                    continue
        
        cleaned_lines.append(line)
        i += 1
    
    with open(file_path, 'w') as f:
        f.writelines(cleaned_lines)
    
    print("Final cleanup completed")

if __name__ == "__main__":
    final_cleanup()