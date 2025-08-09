#!/usr/bin/env python3

import os
import sys
import uuid
from datetime import datetime

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import bcrypt
from ai_karen_engine.database.client import get_db_session_context
from ai_karen_engine.database.models import AuthUser, Tenant

def setup_test_user():
    """Create a default tenant and test user for authentication testing"""
    print("🚀 Setting up test user...")
    
    try:
        with get_db_session_context() as session:
            # First, check if default tenant exists
            default_tenant = session.query(Tenant).filter(Tenant.slug == "default").first()
            
            if not default_tenant:
                print("📝 Creating default tenant...")
                default_tenant = Tenant(
                    id=uuid.uuid4(),
                    name="Default Tenant",
                    slug="default",
                    subscription_tier="basic",
                    settings={},
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                session.add(default_tenant)
                session.flush()  # Get the ID
                print(f"✅ Created default tenant with ID: {default_tenant.id}")
            else:
                print(f"✅ Found existing default tenant with ID: {default_tenant.id}")
            
            # Check if test user already exists
            existing_user = session.query(AuthUser).filter(AuthUser.email == "test@example.com").first()
            
            if existing_user:
                print("✅ Test user already exists")
                print("  Email: test@example.com")
                print("  Password: testpassword")
                return True
            
            # Create test user
            print("👤 Creating test user...")
            hashed_password = bcrypt.hashpw("testpassword".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            
            test_user = AuthUser(
                user_id=str(uuid.uuid4()),
                email="test@example.com",
                full_name="Test User",
                password_hash=hashed_password,
                tenant_id=default_tenant.id,  # Use the UUID
                is_active=True,
                is_verified=True,
                roles=["user"],
                preferences={},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            session.add(test_user)
            session.commit()
            
            print("✅ Test user created successfully!")
            print("  Email: test@example.com")
            print("  Password: testpassword")
            print(f"  Tenant: {default_tenant.name} ({default_tenant.id})")
            
            return True
            
    except Exception as e:
        print(f"❌ Failed to setup test user: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    setup_test_user()