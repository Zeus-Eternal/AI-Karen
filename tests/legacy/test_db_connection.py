#!/usr/bin/env python3

import os
import sys

# Set the environment variable before importing anything
os.environ[
    "POSTGRES_URL"
] = "postgresql://karen_user:karen_secure_pass_change_me@localhost:5432/ai_karen"
os.environ[
    "DATABASE_URL"
] = "postgresql://karen_user:karen_secure_pass_change_me@localhost:5432/ai_karen"

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


def test_connection():
    """Test database connection directly"""
    database_url = os.environ["POSTGRES_URL"]
    print(f"Testing connection to: {database_url}")

    try:
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        with SessionLocal() as session:
            result = session.execute(text("SELECT 1"))
            print("✓ Database connection successful")

            # Check if users table exists
            result = session.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'users'"
                )
            )
            table_count = result.scalar()

            if table_count > 0:
                print("✓ Users table exists")

                # Check for users
                result = session.execute(text("SELECT COUNT(*) FROM users"))
                user_count = result.scalar()
                print(f"Found {user_count} users in database")

                if user_count > 0:
                    result = session.execute(text("SELECT email FROM users LIMIT 5"))
                    users = result.fetchall()
                    for user in users:
                        print(f"  - {user[0]}")
            else:
                print("⚠ Users table does not exist - database needs to be initialized")

    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

    return True


if __name__ == "__main__":
    test_connection()
