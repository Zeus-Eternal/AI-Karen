#!/usr/bin/env python3
"""
Initialize Authentication Database
Creates all necessary tables and test users for AI Karen authentication system
"""

import os
import subprocess
import sys
from pathlib import Path


def run_sql_migration():
    """Run the SQL migration script"""

    # Get database URL from environment
    database_url = os.getenv("POSTGRES_URL") or os.getenv("DATABASE_URL")

    if not database_url:
        print("❌ Error: POSTGRES_URL or DATABASE_URL environment variable not set")
        print(
            "   Please set one of these variables to your PostgreSQL connection string"
        )
        print("   Example: postgresql://karen_user:password@localhost:5432/ai_karen")
        return False

    print(
        f"🔗 Connecting to database: {database_url.split('@')[1] if '@' in database_url else database_url}"
    )

    # Find the SQL migration file
    script_dir = Path(__file__).parent
    sql_file = (
        script_dir.parent
        / "data"
        / "migrations"
        / "postgres"
        / "001_create_auth_tables.sql"
    )

    if not sql_file.exists():
        print(f"❌ Error: SQL migration file not found at {sql_file}")
        return False

    print(f"📄 Running SQL migration: {sql_file}")

    try:
        # Run the SQL script using psql
        result = subprocess.run(
            ["psql", database_url, "-f", str(sql_file), "-v", "ON_ERROR_STOP=1"],
            capture_output=True,
            text=True,
            check=True,
        )

        print("✅ Database migration completed successfully!")

        # Print any output from the migration
        if result.stdout:
            print("\n📋 Migration output:")
            print(result.stdout)

        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Error running migration: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False

    except FileNotFoundError:
        print("❌ Error: 'psql' command not found")
        print("   Please install PostgreSQL client tools")
        print("   Ubuntu/Debian: sudo apt-get install postgresql-client")
        print("   macOS: brew install postgresql")
        return False


def run_python_migration():
    """Alternative: Run migration using Python/SQLAlchemy"""

    print("🐍 Running Python-based migration...")

    # Set environment variables
    database_url = os.getenv("POSTGRES_URL") or os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ Error: POSTGRES_URL or DATABASE_URL environment variable not set")
        return False

    os.environ["POSTGRES_URL"] = database_url
    os.environ["DATABASE_URL"] = database_url

    try:
        # Add the project root to Python path
        project_root = Path(__file__).resolve().parents[2]
        sys.path.insert(0, str(project_root))

        import uuid
        from datetime import datetime

        import bcrypt
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker

        # Import models to ensure they're registered
        from ai_karen_engine.database.models import AuthUser, Base

        print(f"🔗 Connecting to database...")
        engine = create_engine(database_url)

        # Create all tables
        print("📋 Creating database tables...")
        Base.metadata.create_all(bind=engine)

        # Create session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        with SessionLocal() as session:
            # Check if test user exists
            existing_user = (
                session.query(AuthUser)
                .filter(AuthUser.email == "test@example.com")
                .first()
            )

            if not existing_user:
                print("👤 Creating test user...")

                # Create test user
                hashed_password = bcrypt.hashpw(
                    "testpassword".encode("utf-8"), bcrypt.gensalt()
                ).decode("utf-8")

                test_user = AuthUser(
                    user_id=str(uuid.uuid4()),
                    email="test@example.com",
                    full_name="Test User",
                    password_hash=hashed_password,
                    is_active=True,
                    is_verified=True,
                    roles=["user"],
                    tenant_id="default",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )

                session.add(test_user)
                session.commit()

                print("✅ Test user created:")
                print("   📧 Email: test@example.com")
                print("   🔑 Password: testpassword")
            else:
                print("ℹ️  Test user already exists: test@example.com")

            # Check if admin user exists
            existing_admin = (
                session.query(AuthUser)
                .filter(AuthUser.email == "admin@example.com")
                .first()
            )

            if not existing_admin:
                print("👑 Creating admin user...")

                # Create admin user
                hashed_password = bcrypt.hashpw(
                    "adminpassword".encode("utf-8"), bcrypt.gensalt()
                ).decode("utf-8")

                admin_user = AuthUser(
                    user_id=str(uuid.uuid4()),
                    email="admin@example.com",
                    full_name="Admin User",
                    password_hash=hashed_password,
                    is_active=True,
                    is_verified=True,
                    roles=["admin", "user"],
                    tenant_id="default",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )

                session.add(admin_user)
                session.commit()

                print("✅ Admin user created:")
                print("   📧 Email: admin@example.com")
                print("   🔑 Password: adminpassword")
            else:
                print("ℹ️  Admin user already exists: admin@example.com")

            # Show user statistics
            user_count = session.query(AuthUser).count()
            active_users = (
                session.query(AuthUser).filter(AuthUser.is_active == True).count()
            )
            verified_users = (
                session.query(AuthUser).filter(AuthUser.is_verified == True).count()
            )

            print(f"\n📊 Database Statistics:")
            print(f"   👥 Total users: {user_count}")
            print(f"   ✅ Active users: {active_users}")
            print(f"   ✉️  Verified users: {verified_users}")

        print("\n✅ Python migration completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Error running Python migration: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Main function"""
    print("🚀 AI Karen - Authentication Database Initialization")
    print("=" * 60)

    # Check if we should use SQL or Python migration
    use_python = "--python" in sys.argv or "--py" in sys.argv

    if use_python:
        success = run_python_migration()
    else:
        print("🔧 Attempting SQL migration (use --python for Python-based migration)")
        success = run_sql_migration()

        if not success:
            print("\n🔄 SQL migration failed, trying Python migration...")
            success = run_python_migration()

    if success:
        print("\n🎉 Database initialization completed successfully!")
        print("\n📝 You can now test authentication with:")
        print("   • Test User: test@example.com / testpassword")
        print("   • Admin User: admin@example.com / adminpassword")
        print("\n🌐 Test the login endpoint:")
        print("   curl -X POST -H 'Content-Type: application/json' \\")
        print(
            '        -d \'{"email":"test@example.com","password":"testpassword"}\' \\'
        )
        print("        http://localhost:8000/api/auth/login")
    else:
        print("\n❌ Database initialization failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
