#!/usr/bin/env python3
"""Production Database Setup Script.

Creates all necessary tables and initial data for production deployment.
"""

# mypy: ignore-errors

import asyncio
import os
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from ai_karen_engine.auth.service import AuthService, get_auth_service  # noqa: E402
from ai_karen_engine.core.logging import get_logger  # noqa: E402
from ai_karen_engine.database.client import (  # noqa: E402
    create_database_tables,
    db_client,
)

auth_service: AuthService | None = None

logger = get_logger(__name__)


async def create_admin_user():
    """Create initial admin user"""

    try:
        admin_email = "admin@karen.ai"
        admin_password = "admin123"  # Change this in production!

        # Check if admin user already exists
        with db_client.session_scope() as session:
            from ai_karen_engine.database.models import AuthUser

            existing_admin = (
                session.query(AuthUser).filter(AuthUser.email == admin_email).first()
            )

            if existing_admin:
                logger.info("Admin user already exists")
                return

        # Create admin user
        admin_user = await auth_service.create_user(
            email=admin_email,
            password=admin_password,
            full_name="System Administrator",
            roles=["admin", "user"],
            tenant_id="default",
            preferences={
                "personalityTone": "professional",
                "personalityVerbosity": "detailed",
                "memoryDepth": "deep",
                "customPersonaInstructions": "You are an AI assistant for system administration.",
                "preferredLLMProvider": "llama-cpp",
                "preferredModel": "llama3.2:latest",
                "temperature": 0.7,
                "maxTokens": 2000,
                "notifications": {"email": True, "push": True},
                "ui": {"theme": "dark", "language": "en", "avatarUrl": ""},
                "chatMemory": {
                    "shortTermDays": 7,
                    "longTermDays": 90,
                    "tailTurns": 5,
                    "summarizeThresholdTokens": 4000,
                },
            },
        )

        # Mark admin as verified
        with db_client.session_scope() as session:
            from ai_karen_engine.database.models import AuthUser

            admin_db_user = (
                session.query(AuthUser)
                .filter(AuthUser.user_id == admin_user.id)
                .first()
            )
            if admin_db_user:
                admin_db_user.is_verified = True
                session.commit()

        logger.info(f"Created admin user: {admin_email}")
        print(f"✅ Admin user created: {admin_email}")
        print(f"⚠️  Default password: {admin_password}")
        print("🔒 Please change the admin password immediately after first login!")

    except Exception as e:
        logger.error(f"Failed to create admin user: {e}")
        print(f"❌ Failed to create admin user: {e}")


async def create_demo_user():
    """Create demo user for testing"""

    try:
        demo_email = "demo@karen.ai"
        demo_password = "demo123"

        # Check if demo user already exists
        with db_client.session_scope() as session:
            from ai_karen_engine.database.models import AuthUser

            existing_demo = (
                session.query(AuthUser).filter(AuthUser.email == demo_email).first()
            )

            if existing_demo:
                logger.info("Demo user already exists")
                return

        # Create demo user
        demo_user = await auth_service.create_user(
            email=demo_email,
            password=demo_password,
            full_name="Demo User",
            roles=["user"],
            tenant_id="default",
            preferences={
                "personalityTone": "friendly",
                "personalityVerbosity": "balanced",
                "memoryDepth": "medium",
                "customPersonaInstructions": "",
                "preferredLLMProvider": "llama-cpp",
                "preferredModel": "llama3.2:latest",
                "temperature": 0.7,
                "maxTokens": 1000,
                "notifications": {"email": False, "push": False},
                "ui": {"theme": "light", "language": "en", "avatarUrl": ""},
                "chatMemory": {
                    "shortTermDays": 1,
                    "longTermDays": 30,
                    "tailTurns": 3,
                    "summarizeThresholdTokens": 3000,
                },
            },
        )

        # Mark demo user as verified
        with db_client.session_scope() as session:
            from ai_karen_engine.database.models import AuthUser

            demo_db_user = (
                session.query(AuthUser).filter(AuthUser.user_id == demo_user.id).first()
            )
            if demo_db_user:
                demo_db_user.is_verified = True
                session.commit()

        logger.info(f"Created demo user: {demo_email}")
        print(f"✅ Demo user created: {demo_email}")
        print(f"🔑 Password: {demo_password}")

    except Exception as e:
        logger.error(f"Failed to create demo user: {e}")
        print(f"❌ Failed to create demo user: {e}")


def check_database_connection():
    """Check if database is accessible"""

    try:
        if db_client.health_check():
            print("✅ Database connection successful")
            return True
        else:
            print("❌ Database connection failed")
            return False

    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False


async def main():
    """Main setup function"""

    print("🚀 Setting up AI Karen Production Database")
    print("=" * 50)

    # Check database connection
    print("1. Checking database connection...")
    if not check_database_connection():
        print(
            "❌ Cannot connect to database. Please check your POSTGRES_URL (or legacy DATABASE_URL) configuration."
        )
        sys.exit(1)

    # Create tables
    print("2. Creating database tables...")
    try:
        create_database_tables()
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        sys.exit(1)

    # Create admin user
    print("3. Creating admin user...")
    global auth_service
    if auth_service is None:
        auth_service = await get_auth_service()
    await create_admin_user()

    # Create demo user
    print("4. Creating demo user...")
    await create_demo_user()

    print("\n🎉 Production database setup complete!")
    print("\n📋 Next steps:")
    print("1. Update your environment variables with proper database credentials")
    print("2. Configure Redis URL for session management")
    print("3. Set up vector database (Milvus) for chat memory")
    print("4. Change default admin password")
    print("5. Configure email service for password resets")
    print("\n🔐 Security reminders:")
    print("- Change default passwords immediately")
    print("- Use strong, unique passwords in production")
    print("- Enable 2FA for admin accounts")
    print("- Regularly backup your database")


if __name__ == "__main__":
    asyncio.run(main())
