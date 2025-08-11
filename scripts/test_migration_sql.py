#!/usr/bin/env python3
"""
Simple test to validate the NeuroVault migration SQL syntax.
This script parses the SQL file to check for syntax errors without requiring a database connection.
"""

import re
import sys
from pathlib import Path

def validate_sql_syntax(sql_content: str) -> tuple[bool, list[str]]:
    """
    Basic SQL syntax validation.
    Returns (is_valid, list_of_issues)
    """
    issues = []
    
    # Check for basic SQL syntax issues
    lines = sql_content.split('\n')
    
    # Track parentheses balance
    paren_balance = 0
    in_comment = False
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
            
        # Handle comments
        if line.startswith('--'):
            continue
        if '/*' in line and '*/' in line:
            continue
        if '/*' in line:
            in_comment = True
            continue
        if '*/' in line:
            in_comment = False
            continue
        if in_comment:
            continue
            
        # Check parentheses balance
        paren_balance += line.count('(') - line.count(')')
        
        # Check for common SQL syntax issues
        if line.upper().startswith(('CREATE', 'ALTER', 'INSERT', 'UPDATE', 'DELETE', 'SELECT')):
            if not line.endswith((';', ',')):
                # Check if this is a multi-line statement
                next_lines = lines[line_num:line_num+5] if line_num < len(lines) else []
                has_continuation = any(l.strip().endswith(';') for l in next_lines)
                if not has_continuation and 'RETURNS' not in line.upper():
                    issues.append(f"Line {line_num}: SQL statement may be missing semicolon: {line[:50]}...")
    
    # Check final parentheses balance
    if paren_balance != 0:
        issues.append(f"Unbalanced parentheses: {paren_balance} unclosed")
    
    return len(issues) == 0, issues

def validate_neuro_vault_migration():
    """Validate the NeuroVault migration SQL file."""
    migration_file = Path(__file__).parent.parent / "data/migrations/postgres/015_neuro_vault_schema_extensions.sql"
    
    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return False
    
    print(f"📄 Validating migration file: {migration_file}")
    
    try:
        sql_content = migration_file.read_text()
        print(f"📊 File size: {len(sql_content)} characters, {len(sql_content.splitlines())} lines")
        
        # Basic syntax validation
        is_valid, issues = validate_sql_syntax(sql_content)
        
        if issues:
            print("⚠️  Potential issues found:")
            for issue in issues:
                print(f"   - {issue}")
        
        # Check for required components
        required_components = [
            "ALTER TABLE memory_items",
            "CREATE TABLE IF NOT EXISTS memory_relationships",
            "CREATE INDEX",
            "CREATE OR REPLACE FUNCTION calculate_decay_score",
            "CREATE OR REPLACE FUNCTION update_memory_access",
            "CREATE OR REPLACE FUNCTION create_memory_relationship",
            "CREATE OR REPLACE VIEW active_memories_with_decay",
            "CREATE OR REPLACE VIEW memory_relationship_details",
            "CREATE OR REPLACE VIEW memory_analytics"
        ]
        
        missing_components = []
        for component in required_components:
            if component not in sql_content:
                missing_components.append(component)
        
        if missing_components:
            print("❌ Missing required components:")
            for component in missing_components:
                print(f"   - {component}")
            return False
        
        # Check for NeuroVault-specific columns
        neuro_columns = [
            "neuro_type",
            "decay_lambda", 
            "reflection_count",
            "source_memories",
            "derived_memories",
            "importance_decay",
            "last_reflection",
            "importance_score",
            "access_count"
        ]
        
        missing_columns = []
        for column in neuro_columns:
            if f"ADD COLUMN IF NOT EXISTS {column}" not in sql_content:
                missing_columns.append(column)
        
        if missing_columns:
            print("❌ Missing NeuroVault columns:")
            for column in missing_columns:
                print(f"   - {column}")
            return False
        
        # Check for constraints
        constraint_checks = [
            "chk_neuro_type",
            "chk_decay_lambda",
            "chk_importance_score",
            "chk_confidence_score"
        ]
        
        missing_constraints = []
        for constraint in constraint_checks:
            if constraint not in sql_content:
                missing_constraints.append(constraint)
        
        if missing_constraints:
            print("⚠️  Missing constraints (may affect data validation):")
            for constraint in missing_constraints:
                print(f"   - {constraint}")
        
        # Summary
        print("\n" + "="*50)
        print("MIGRATION SQL VALIDATION SUMMARY")
        print("="*50)
        
        print(f"✓ File exists and readable")
        print(f"✓ All required components present")
        print(f"✓ All NeuroVault columns defined")
        
        if issues:
            print(f"⚠️  {len(issues)} potential syntax issues")
        else:
            print(f"✓ No obvious syntax issues")
            
        if missing_constraints:
            print(f"⚠️  {len(missing_constraints)} missing constraints")
        else:
            print(f"✓ All expected constraints present")
        
        print(f"\n📈 Migration Statistics:")
        print(f"   - ALTER TABLE statements: {sql_content.count('ALTER TABLE')}")
        print(f"   - CREATE TABLE statements: {sql_content.count('CREATE TABLE')}")
        print(f"   - CREATE INDEX statements: {sql_content.count('CREATE INDEX')}")
        print(f"   - CREATE FUNCTION statements: {sql_content.count('CREATE OR REPLACE FUNCTION')}")
        print(f"   - CREATE VIEW statements: {sql_content.count('CREATE OR REPLACE VIEW')}")
        print(f"   - ADD COLUMN statements: {sql_content.count('ADD COLUMN IF NOT EXISTS')}")
        
        if not issues and not missing_components and not missing_columns:
            print(f"\n🎉 Migration SQL validation passed!")
            return True
        else:
            print(f"\n❌ Migration SQL validation failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error reading migration file: {e}")
        return False

def main():
    """Main entry point."""
    print("NeuroVault Migration SQL Validator")
    print("=" * 40)
    
    success = validate_neuro_vault_migration()
    
    if success:
        print("\n✅ Validation completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Validation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()