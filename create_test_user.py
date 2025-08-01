#!/usr/bin/env python3

import os
import sys

# Set the environment variable before importing anything
os.environ['POSTGRES_URL'] = 'postgresql://karen_user:karen_secure_pass_change_me@localhost:5432/ai_karen'
os.environ['DATABASE_URL'] = 'postgresql://karen_user:karen_secure_pass_change_me@localhost:5432/ai_karen'

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from src.ai_karen_engine.database.models.auth_models import User
import bcrypt
import uuid
from datetime import datetime

def create_test_user():
    """Create a test user for authentication testing"""
    database_url = os.environ['POSTGRES_URL']
    print(f"Creating test user in: {database_url}")
    
    try:
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        with SessionLocal() as session:
            # Check if test user already exists
            existing_user = session.query(User).filter(User.email == 'test@example.com').first()
            
            if existing_user:
                print("✓ Test user already exists")
                return True
            
            # Create test user
            hashed_password = bcrypt.hashpw('testpassword'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            test_user = User(
                id=str(uuid.uuid4()),
                email='test@example.com',
                username='testuser',
                password_hash=hashed_password,
                is_active=True,
                is_verified=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            session.add(test_user)
            session.commit()
            
            print("✓ Test user created successfully")
            print("  Email: test@example.com")
            print("  Password: testpassword")
            
            return True
            
    except Exception as e:
        print(f"✗ Failed to create test user: {e}")
        return False

if __name__ == "__main__":
    create_test_user()