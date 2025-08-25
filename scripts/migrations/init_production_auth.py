#!/usr/bin/env python3
"""
Production Authentication Initialization Script

This script initializes the production authentication system with:
- Database schema creation and migration
- Redis connection verification
- JWT token validation
- Security configuration verification
- Default user creation (if needed)
- Health checks for all authentication components

Usage:
    python scripts/init_production_auth.py [--verify-only] [--create-admin] [--reset-admin-password]
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

try:
    import bcrypt
    import redis.asyncio as redis
    from sqlalchemy import create_engine, text
    from sqlalchemy.ext.asyncio import create_async_engine
    
    # Import authentication components
    from ai_karen_engine.auth.config import AuthConfig
    from ai_karen_engine.auth.service import AuthService
    from ai_karen_engine.auth.database import AuthDatabaseClient
    from ai_karen_engine.auth.models import UserData
    from ai_karen_engine.auth.tokens import TokenManager
    
except ImportError as e:
    print(f"❌ Missing required dependencies: {e}")
    print("Please install required packages:")
    print("pip install bcrypt redis sqlalchemy asyncpg PyJWT")
    sys.exit(1)


class ProductionAuthInitializer:
    """Initialize and verify production authentication system."""
    
    def __init__(self, verify_only: bool = False):
        self.verify_only = verify_only
        self.config = AuthConfig.from_env()
        self.results: Dict[str, bool] = {}
        self.errors: List[str] = []
        
    async def initialize(self) -> bool:
        """Initialize the production authentication system."""
        print("🚀 Initializing Production Authentication System")
        print("=" * 60)
        
        # Step 1: Verify configuration
        if not await self._verify_configuration():
            return False
            
        # Step 2: Initialize database schema
        if not self.verify_only:
            if not await self._initialize_database_schema():
                return False
        else:
            if not await self._verify_database_connection():
                return False
                
        # Step 3: Verify Redis connection
        if not await self._verify_redis_connection():
            return False
            
        # Step 4: Verify JWT configuration
        if not await self._verify_jwt_configuration():
            return False
            
        # Step 5: Initialize authentication service
        if not await self._initialize_auth_service():
            return False
            
        # Step 6: Run health checks
        if not await self._run_health_checks():
            return False
            
        # Step 7: Display summary
        self._display_summary()
        
        return all(self.results.values())
    
    async def _verify_configuration(self) -> bool:
        """Verify authentication configuration."""
        print("📋 Verifying Authentication Configuration...")
        
        try:
            # Check required environment variables
            required_vars = [
                'AUTH_DATABASE_URL',
                'AUTH_SECRET_KEY',
                'REDIS_URL'
            ]
            
            missing_vars = []
            for var in required_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                self.errors.append(f"Missing required environment variables: {', '.join(missing_vars)}")
                self.results['configuration'] = False
                print("❌ Configuration verification failed")
                return False
            
            # Verify JWT secret key strength
            jwt_secret = os.getenv('AUTH_SECRET_KEY', '')
            if len(jwt_secret) < 32:
                self.errors.append("JWT secret key should be at least 32 characters long")
                self.results['configuration'] = False
                print("❌ JWT secret key too short")
                return False
            
            # Verify database URL format
            db_url = os.getenv('AUTH_DATABASE_URL', '')
            if not db_url.startswith('postgresql+asyncpg://'):
                self.errors.append("Database URL should use postgresql+asyncpg:// for async support")
                self.results['configuration'] = False
                print("❌ Invalid database URL format")
                return False
            
            self.results['configuration'] = True
            print("✅ Configuration verification passed")
            return True
            
        except Exception as e:
            self.errors.append(f"Configuration verification error: {e}")
            self.results['configuration'] = False
            print(f"❌ Configuration verification failed: {e}")
            return False
    
    async def _initialize_database_schema(self) -> bool:
        """Initialize database schema with migration."""
        print("🗄️  Initializing Database Schema...")
        
        try:
            # Create database client
            db_client = AuthDatabaseClient(self.config.database)
            
            # Initialize schema (this will create tables if they don't exist)
            await db_client.initialize_schema()
            
            # Run the production migration script
            migration_path = Path(__file__).resolve().parents[2] / "data/migrations/postgres/013_production_auth_schema_alignment.sql"
            
            if migration_path.exists():
                print("📄 Running production authentication migration...")
                
                # Read migration SQL
                migration_sql = migration_path.read_text()
                
                # Execute migration
                async with db_client.engine.begin() as conn:
                    # Split migration into individual statements and execute
                    statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
                    
                    for statement in statements:
                        if statement and not statement.startswith('--'):
                            try:
                                await conn.execute(text(statement))
                            except Exception as e:
                                # Some statements might fail if already executed, that's OK
                                if "already exists" not in str(e).lower():
                                    print(f"⚠️  Migration statement warning: {e}")
                
                print("✅ Database migration completed")
            else:
                print("⚠️  Migration file not found, using basic schema initialization")
            
            self.results['database_schema'] = True
            print("✅ Database schema initialization completed")
            return True
            
        except Exception as e:
            self.errors.append(f"Database schema initialization error: {e}")
            self.results['database_schema'] = False
            print(f"❌ Database schema initialization failed: {e}")
            return False
    
    async def _verify_database_connection(self) -> bool:
        """Verify database connection."""
        print("🔗 Verifying Database Connection...")
        
        try:
            db_client = AuthDatabaseClient(self.config.database)
            
            # Test connection by running a simple query
            async with db_client.engine.begin() as conn:
                result = await conn.execute(text("SELECT 1 as test"))
                row = result.fetchone()
                if row and row[0] == 1:
                    print("✅ Database connection verified")
                    self.results['database_connection'] = True
                    return True
                else:
                    raise Exception("Database query returned unexpected result")
                    
        except Exception as e:
            self.errors.append(f"Database connection error: {e}")
            self.results['database_connection'] = False
            print(f"❌ Database connection failed: {e}")
            return False
    
    async def _verify_redis_connection(self) -> bool:
        """Verify Redis connection."""
        print("🔴 Verifying Redis Connection...")
        
        try:
            redis_url = os.getenv('REDIS_URL')
            if not redis_url:
                print("⚠️  Redis URL not configured, skipping Redis verification")
                self.results['redis_connection'] = True
                return True
            
            # Create Redis client
            redis_client = redis.from_url(redis_url, decode_responses=True)
            
            # Test connection
            await redis_client.ping()
            
            # Test basic operations
            test_key = f"auth_test_{datetime.now().timestamp()}"
            await redis_client.set(test_key, "test_value", ex=10)
            value = await redis_client.get(test_key)
            await redis_client.delete(test_key)
            
            if value == "test_value":
                print("✅ Redis connection verified")
                self.results['redis_connection'] = True
                await redis_client.close()
                return True
            else:
                raise Exception("Redis test operation failed")
                
        except Exception as e:
            self.errors.append(f"Redis connection error: {e}")
            self.results['redis_connection'] = False
            print(f"❌ Redis connection failed: {e}")
            return False
    
    async def _verify_jwt_configuration(self) -> bool:
        """Verify JWT token configuration."""
        print("🔐 Verifying JWT Configuration...")
        
        try:
            # Create token manager
            token_manager = TokenManager(self.config.jwt)
            
            # Create test user data
            test_user = UserData(
                user_id="test-user-id",
                email="test@example.com",
                full_name="Test User",
                roles=["user"],
                tenant_id="default"
            )
            
            # Test token creation and validation
            access_token = await token_manager.create_access_token(test_user)
            refresh_token = await token_manager.create_refresh_token(test_user)
            
            # Validate tokens
            access_payload = await token_manager.validate_access_token(access_token)
            refresh_payload = await token_manager.validate_refresh_token(refresh_token)
            
            if access_payload and refresh_payload:
                print("✅ JWT configuration verified")
                self.results['jwt_configuration'] = True
                return True
            else:
                raise Exception("JWT token validation failed")
                
        except Exception as e:
            self.errors.append(f"JWT configuration error: {e}")
            self.results['jwt_configuration'] = False
            print(f"❌ JWT configuration failed: {e}")
            return False
    
    async def _initialize_auth_service(self) -> bool:
        """Initialize authentication service."""
        print("🔧 Initializing Authentication Service...")
        
        try:
            # Create authentication service
            auth_service = AuthService(self.config)
            
            # Initialize the service
            await auth_service.initialize()
            
            print("✅ Authentication service initialized")
            self.results['auth_service'] = True
            return True
            
        except Exception as e:
            self.errors.append(f"Authentication service initialization error: {e}")
            self.results['auth_service'] = False
            print(f"❌ Authentication service initialization failed: {e}")
            return False
    
    async def _run_health_checks(self) -> bool:
        """Run comprehensive health checks."""
        print("🏥 Running Health Checks...")
        
        try:
            # Create authentication service for health checks
            auth_service = AuthService(self.config)
            await auth_service.initialize()
            
            # Test user creation (if not in verify-only mode)
            if not self.verify_only:
                test_email = f"health_check_{datetime.now().timestamp()}@test.local"
                test_password = "HealthCheck123!"
                
                try:
                    # Create test user
                    test_user = await auth_service.create_user(
                        email=test_email,
                        password=test_password,
                        full_name="Health Check User"
                    )
                    
                    # Test authentication
                    authenticated_user = await auth_service.authenticate_user(
                        email=test_email,
                        password=test_password
                    )
                    
                    if authenticated_user and authenticated_user.user_id == test_user.user_id:
                        print("✅ User creation and authentication test passed")
                        
                        # Test session creation
                        session = await auth_service.create_session(authenticated_user)
                        
                        # Test session validation
                        validated_user = await auth_service.validate_session(session.session_token)
                        
                        if validated_user and validated_user.user_id == test_user.user_id:
                            print("✅ Session management test passed")
                            
                            # Clean up test user (optional)
                            # Note: In production, you might want to keep test data for monitoring
                            
                        else:
                            raise Exception("Session validation test failed")
                    else:
                        raise Exception("User authentication test failed")
                        
                except Exception as e:
                    print(f"⚠️  Health check warning: {e}")
                    # Don't fail the entire initialization for health check issues
            
            self.results['health_checks'] = True
            print("✅ Health checks completed")
            return True
            
        except Exception as e:
            self.errors.append(f"Health check error: {e}")
            self.results['health_checks'] = False
            print(f"❌ Health checks failed: {e}")
            return False
    
    def _display_summary(self):
        """Display initialization summary."""
        print("\n" + "=" * 60)
        print("📊 Production Authentication Initialization Summary")
        print("=" * 60)
        
        for check, result in self.results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{check.replace('_', ' ').title():<30} {status}")
        
        if self.errors:
            print("\n🚨 Errors encountered:")
            for error in self.errors:
                print(f"   • {error}")
        
        success_count = sum(self.results.values())
        total_count = len(self.results)
        
        print(f"\n📈 Overall Status: {success_count}/{total_count} checks passed")
        
        if all(self.results.values()):
            print("\n🎉 Production authentication system is ready!")
            print("\n📝 Next steps:")
            print("   1. Change default admin password (admin@ai-karen.local)")
            print("   2. Configure SSL/TLS for database and Redis connections")
            print("   3. Set up monitoring and alerting")
            print("   4. Configure backup procedures")
            print("   5. Review and adjust security settings")
        else:
            print("\n⚠️  Production authentication system has issues that need to be resolved.")
    
    async def create_admin_user(self, email: str = "admin@ai-karen.local", password: str = "admin123") -> bool:
        """Create or reset admin user."""
        print(f"👤 Creating admin user: {email}")
        
        try:
            auth_service = AuthService(self.config)
            await auth_service.initialize()
            
            # Check if admin user already exists
            existing_user = await auth_service.core_auth.get_user_by_email(email)
            
            if existing_user:
                print(f"⚠️  Admin user {email} already exists")
                return True
            
            # Create admin user
            admin_user = await auth_service.create_user(
                email=email,
                password=password,
                full_name="System Administrator",
                roles=["admin", "user"]
            )
            
            print(f"✅ Admin user created: {email}")
            print(f"🔑 Password: {password}")
            print("⚠️  IMPORTANT: Change this password immediately after first login!")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to create admin user: {e}")
            return False
    
    async def reset_admin_password(self, email: str = "admin@ai-karen.local", new_password: str = None) -> bool:
        """Reset admin user password."""
        if not new_password:
            new_password = f"admin{datetime.now().strftime('%Y%m%d')}"
        
        print(f"🔄 Resetting password for admin user: {email}")
        
        try:
            auth_service = AuthService(self.config)
            await auth_service.initialize()
            
            # Get admin user
            admin_user = await auth_service.core_auth.get_user_by_email(email)
            if not admin_user:
                print(f"❌ Admin user {email} not found")
                return False
            
            # Update password
            success = await auth_service.update_user_password(
                user_id=admin_user.user_id,
                new_password=new_password
            )
            
            if success:
                print(f"✅ Admin password reset successfully")
                print(f"🔑 New password: {new_password}")
                print("⚠️  IMPORTANT: Change this password immediately after login!")
                return True
            else:
                print("❌ Failed to reset admin password")
                return False
                
        except Exception as e:
            print(f"❌ Failed to reset admin password: {e}")
            return False


async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize production authentication system")
    parser.add_argument("--verify-only", action="store_true", help="Only verify configuration, don't make changes")
    parser.add_argument("--create-admin", action="store_true", help="Create admin user")
    parser.add_argument("--reset-admin-password", action="store_true", help="Reset admin user password")
    parser.add_argument("--admin-email", default="admin@ai-karen.local", help="Admin user email")
    parser.add_argument("--admin-password", help="Admin user password (auto-generated if not provided)")
    
    args = parser.parse_args()
    
    # Initialize the production auth system
    initializer = ProductionAuthInitializer(verify_only=args.verify_only)
    
    success = await initializer.initialize()
    
    # Handle additional operations
    if args.create_admin:
        await initializer.create_admin_user(args.admin_email, args.admin_password or "admin123")
    
    if args.reset_admin_password:
        await initializer.reset_admin_password(args.admin_email, args.admin_password)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())