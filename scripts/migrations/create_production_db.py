#!/usr/bin/env python3
"""Production Database Setup Script.

Creates all necessary tables and initial data for production deployment.
"""

# mypy: ignore-errors

import asyncio
import os
import sys

# Add src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

# Import AuthService and UserRole from correct module (same way as existing system)
from ai_karen_engine.services import AuthService, UserRole  # noqa: E402
from ai_karen_engine.core.logging import get_logger  # noqa: E402
from ai_karen_engine.database.client import (  # noqa: E402
    create_database_tables,
    db_client,
)

# Don't instantiate at module level - will be done in main() when DB is ready
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

        # Create admin user using actual create_user signature
        admin_user, error = await auth_service.create_user(
            email=admin_email,
            password=admin_password,
            full_name="System Administrator",
            roles=[UserRole.ADMIN, UserRole.USER],
            is_verified=True
        )

        if error:
            logger.error(f"Failed to create admin user: {error}")
            print(f"❌ Failed to create admin user: {error}")
            return

        logger.info(f"Created admin user: {admin_email}")
        print(f"✅ Admin user created: {admin_email}")
        print(f"⚠️  Default password: {admin_password}")
        print("🔒 Please change admin password immediately after first login!")

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

        # Create demo user using actual create_user signature
        demo_user, error = await auth_service.create_user(
            email=demo_email,
            password=demo_password,
            full_name="Demo User",
            roles=[UserRole.USER],
            is_verified=True
        )

        if error:
            logger.error(f"Failed to create demo user: {error}")
            print(f"❌ Failed to create demo user: {error}")
            return

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

    # Initialize AuthService (after DB is ready)
    global auth_service
    # Use model_construct to bypass Pydantic validation for required fields
    from ai_karen_engine.services.auth_service import AuthConfig
    auth_config = AuthConfig.model_construct(
        name="auth_service",
        version="1.0.0"
    )
    auth_service = AuthService(config=auth_config)
    
    # Set database session for AuthService
    # Note: We need to create a new session for each create_user() call
    # because the session scope context manager closes the session
    # So we'll set it inside each create_user function instead
    
    # Manually initialize service to prevent circular dependency
    # The service's initialize() method tries to create a default admin user,
    # which calls create_user(), which tries to initialize() again, causing a hang
    # So we'll mark it as initialized without calling the full initialize() method
    auth_service._initialized = True
    auth_service._lock = asyncio.Lock()
    
    # Create admin user
    print("3. Creating admin user...")
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
