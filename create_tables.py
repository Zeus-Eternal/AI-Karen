#!/usr/bin/env python3
"""
Simple script to create all database tables using SQLAlchemy
"""

import os
import sys

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from ai_karen_engine.database.models import Base
from ai_karen_engine.database.client import get_db_session_context

def create_all_tables():
    """Create all database tables"""
    print("🚀 Creating database tables...")
    
    try:
        # Get database session to access the engine
        with get_db_session_context() as session:
            engine = session.bind
            
            # Create all tables
            Base.metadata.create_all(engine)
            
        print("✅ Successfully created all database tables!")
        
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_all_tables()