import asyncio
import os
import sys

# Add src to sys.path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from ai_karen_engine.services.auth_service import AuthService, AuthConfig, UserStatus

async def list_users():
    config = AuthConfig.model_construct(name="auth_service", version="1.0.0")
    service = AuthService(config=config)
    import ai_karen_engine.services.auth_service
    print(f"DEBUG: AuthService file: {ai_karen_engine.services.auth_service.__file__}")
    await service.initialize()
    
    users = await service.get_all_users()
    print(f"Found {len(users)} users:")
    for user in users:
        print(f"- ID: {user.id}, Email: {user.email}, Full Name: {user.full_name}, Roles: {user.roles}, Status: {user.status}")

if __name__ == "__main__":
    asyncio.run(list_users())
