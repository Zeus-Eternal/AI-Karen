#!/usr/bin/env python3

import os
import sys
import json

# Set the environment variable before importing anything
os.environ['POSTGRES_URL'] = 'postgresql://karen_user:karen_secure_pass_change_me@localhost:5432/ai_karen'
os.environ['DATABASE_URL'] = 'postgresql://karen_user:karen_secure_pass_change_me@localhost:5432/ai_karen'

from sqlalchemy import create_engine, text
import bcrypt
import uuid
from datetime import datetime

def create_anonymous_user():
    """Create or update anonymous user for web UI memory operations"""
    database_url = os.environ['POSTGRES_URL']
    print(f"Setting up anonymous user in: {database_url}")
    
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as connection:
            # Check if the existing anonymous user from schema exists
            result = connection.execute(
                text("SELECT id, password_hash FROM users WHERE email = :email"),
                {"email": "anonymous@ai-karen.local"}
            )
            existing_user = result.fetchone()
            
            if existing_user and existing_user[1]:  # Has password
                print("✓ Anonymous user already exists with password")
                print("  Email: anonymous@ai-karen.local")
                print("  Password: anonymous")
                return True
            elif existing_user:  # Exists but no password
                print("✓ Found existing anonymous user, adding password...")
                hashed_password = bcrypt.hashpw('anonymous'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                
                connection.execute(
                    text("UPDATE users SET password_hash = :password_hash WHERE id = :id"),
                    {"password_hash": hashed_password, "id": existing_user[0]}
                )
                connection.commit()
                
                print("✓ Anonymous user password set successfully")
                print("  Email: anonymous@ai-karen.local")
                print("  Password: anonymous")
                return True
            
            # If no existing user, create a new one
            print("Creating new anonymous user...")
            
            # Get the default tenant ID
            tenant_result = connection.execute(
                text("SELECT id FROM tenants WHERE slug = 'default' LIMIT 1")
            )
            tenant_row = tenant_result.fetchone()
            
            if not tenant_row:
                print("✗ Default tenant not found. Please run the database schema first.")
                return False
            
            tenant_id = tenant_row[0]
            
            # Create anonymous user with hashed password
            hashed_password = bcrypt.hashpw('anonymous'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            user_id = str(uuid.uuid4())
            
            connection.execute(
                text("""
                    INSERT INTO users (id, tenant_id, email, password_hash, roles, preferences, is_active, is_verified, created_at, updated_at)
                    VALUES (:id, :tenant_id, :email, :password_hash, ARRAY['user'], :preferences::jsonb, :is_active, :is_verified, :created_at, :updated_at)
                """),
                {
                    "id": user_id,
                    "tenant_id": tenant_id,
                    "email": "anonymous@ai-karen.local",
                    "password_hash": hashed_password,
                    "preferences": json.dumps({"ui_theme": "auto", "language": "en", "timezone": "UTC"}),
                    "is_active": True,
                    "is_verified": True,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            )
            
            connection.commit()
            
            print("✓ Anonymous user created successfully")
            print("  Email: anonymous@ai-karen.local")
            print("  Password: anonymous")
            print("  This user is for web UI memory operations when no user is logged in")
            
            return True
            
    except Exception as e:
        print(f"✗ Failed to setup anonymous user: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    create_anonymous_user()