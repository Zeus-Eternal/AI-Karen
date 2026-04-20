import asyncio
import sys
import os
from passlib.context import CryptContext

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.curdir))

# Mock settings or import them
from ai_karen_engine.database.integration_manager import get_database_manager

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_admin():
    settings = Settings()
    db_manager = get_database_manager()

    email = "admin@karen.ai"
    password = "Admin@123!"
    full_name = "Admin User"

    hashed_password = pwd_context.hash(password)

    print(f"Creating user {email}...")

    query = """
    INSERT INTO users (email, hashed_password, full_name, is_active, is_superuser, created_at, updated_at)
    VALUES (:email, :hashed_password, :full_name, true, true, now(), now())
    ON CONFLICT (email) DO UPDATE 
    SET hashed_password = EXCLUDED.hashed_password,
        full_name = EXCLUDED.full_name,
        is_active = true,
        updated_at = now();
    """

    try:
        # We need an async session
        from sqlalchemy import text

        # This is a bit simplified, but let's try to use the db_manager's engine
        async with db_manager.get_session() as session:
            await session.execute(
                text(query),
                {
                    "email": email,
                    "hashed_password": hashed_password,
                    "full_name": full_name,
                },
            )
            await session.commit()
            print("Successfully created/updated admin user.")
    except Exception as e:
        print(f"Error creating user: {e}")


if __name__ == "__main__":
    asyncio.run(create_admin())
