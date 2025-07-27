#!/usr/bin/env python3
"""
Fix database schema by dropping and recreating tenant schemas
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def fix_database_schema():
    """Drop and recreate tenant schemas with correct structure"""
    
    print("🔧 Fixing Database Schema...")
    
    try:
        from ai_karen_engine.database.client import MultiTenantPostgresClient
        from ai_karen_engine.database.models import Tenant
        from sqlalchemy import text
        
        # Initialize database client
        db_client = MultiTenantPostgresClient()
        print("✅ Database client initialized")
        
        # Get all tenants
        with db_client._get_session() as session:
            tenants = session.query(Tenant).all()
            print(f"📋 Found {len(tenants)} tenants")
            
            for tenant in tenants:
                schema_name = db_client.get_tenant_schema_name(tenant.id)
                print(f"\n🗑️ Dropping schema: {schema_name}")
                
                # Drop the schema
                try:
                    session.execute(text(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE"))
                    session.commit()
                    print(f"✅ Dropped schema: {schema_name}")
                except Exception as e:
                    print(f"⚠️ Warning dropping schema {schema_name}: {e}")
                
                # Recreate the schema with correct structure
                print(f"🔨 Recreating schema: {schema_name}")
                success = db_client.create_tenant_schema(tenant.id)
                if success:
                    print(f"✅ Recreated schema: {schema_name}")
                else:
                    print(f"❌ Failed to recreate schema: {schema_name}")
        
        print("\n🎉 Database schema fix completed!")
        return True
        
    except Exception as e:
        print(f"❌ Database schema fix failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    fix_database_schema()