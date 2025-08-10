#!/usr/bin/env python3
"""
Database Connection Validator

This script validates database connectivity and provides guidance for setting up
the database if it's not available.
"""

import asyncio
import os
import sys
import subprocess
from pathlib import Path

try:
    import psycopg2
    from sqlalchemy import create_engine, text
    from sqlalchemy.ext.asyncio import create_async_engine
except ImportError as e:
    print(f"❌ Missing required dependencies: {e}")
    print("Please install: pip install psycopg2-binary sqlalchemy asyncpg")
    sys.exit(1)


class DatabaseValidator:
    """Validate and setup database connectivity."""
    
    def __init__(self):
        self.database_url = self._get_database_url()
        self.connection_params = self._parse_database_url()
    
    def _get_database_url(self) -> str:
        """Get database URL from environment variables."""
        return (
            os.getenv("AUTH_DATABASE_URL") or 
            os.getenv("POSTGRES_URL") or 
            os.getenv("DATABASE_URL") or
            "postgresql://karen_user:karen_secure_pass_change_me@localhost:5432/ai_karen"
        )
    
    def _parse_database_url(self) -> dict:
        """Parse database URL into components."""
        # Simple URL parsing for PostgreSQL
        url = self.database_url
        if url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgresql+asyncpg://", "postgresql://")
        elif url.startswith("postgresql://"):
            pass
        else:
            raise ValueError(f"Unsupported database URL format: {url}")
        
        # Extract components
        # Format: postgresql://user:password@host:port/database
        try:
            parts = url.replace("postgresql://", "").split("/")
            db_name = parts[1] if len(parts) > 1 else "ai_karen"
            
            auth_host = parts[0].split("@")
            host_port = auth_host[1] if len(auth_host) > 1 else "localhost:5432"
            user_pass = auth_host[0] if len(auth_host) > 1 else "karen_user:karen_secure_pass_change_me"
            
            host = host_port.split(":")[0]
            port = int(host_port.split(":")[1]) if ":" in host_port else 5432
            
            user = user_pass.split(":")[0]
            password = user_pass.split(":")[1] if ":" in user_pass else ""
            
            return {
                "host": host,
                "port": port,
                "user": user,
                "password": password,
                "database": db_name
            }
        except Exception as e:
            raise ValueError(f"Failed to parse database URL: {e}")
    
    def check_postgresql_service(self) -> bool:
        """Check if PostgreSQL service is running."""
        print("🔍 Checking PostgreSQL service status...")
        
        try:
            # Try to connect to PostgreSQL
            conn = psycopg2.connect(
                host=self.connection_params["host"],
                port=self.connection_params["port"],
                user=self.connection_params["user"],
                password=self.connection_params["password"],
                database="postgres",  # Connect to default database first
                connect_timeout=5
            )
            conn.close()
            print("✅ PostgreSQL service is running")
            return True
            
        except psycopg2.OperationalError as e:
            error_msg = str(e).lower()
            if "connection refused" in error_msg:
                print("❌ PostgreSQL service is not running")
                return False
            elif "authentication failed" in error_msg:
                print("❌ PostgreSQL authentication failed")
                print(f"   Trying to connect with user: {self.connection_params['user']}")
                return False
            elif "database" in error_msg and "does not exist" in error_msg:
                print("⚠️  PostgreSQL is running but database doesn't exist")
                return True  # Service is running, just need to create database
            else:
                print(f"❌ PostgreSQL connection error: {e}")
                return False
    
    def check_database_exists(self) -> bool:
        """Check if the target database exists."""
        print(f"🔍 Checking if database '{self.connection_params['database']}' exists...")
        
        try:
            # Connect to default postgres database
            conn = psycopg2.connect(
                host=self.connection_params["host"],
                port=self.connection_params["port"],
                user=self.connection_params["user"],
                password=self.connection_params["password"],
                database="postgres",
                connect_timeout=5
            )
            
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (self.connection_params["database"],)
            )
            exists = cursor.fetchone() is not None
            
            cursor.close()
            conn.close()
            
            if exists:
                print(f"✅ Database '{self.connection_params['database']}' exists")
            else:
                print(f"❌ Database '{self.connection_params['database']}' does not exist")
            
            return exists
            
        except Exception as e:
            print(f"❌ Failed to check database existence: {e}")
            return False
    
    def check_database_connectivity(self) -> bool:
        """Check if we can connect to the target database."""
        print(f"🔍 Testing connection to database '{self.connection_params['database']}'...")
        
        try:
            conn = psycopg2.connect(
                host=self.connection_params["host"],
                port=self.connection_params["port"],
                user=self.connection_params["user"],
                password=self.connection_params["password"],
                database=self.connection_params["database"],
                connect_timeout=5
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if result and result[0] == 1:
                print("✅ Database connection successful")
                return True
            else:
                print("❌ Database connection test failed")
                return False
                
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def check_auth_tables(self) -> bool:
        """Check if authentication tables exist."""
        print("🔍 Checking for authentication tables...")
        
        try:
            conn = psycopg2.connect(
                host=self.connection_params["host"],
                port=self.connection_params["port"],
                user=self.connection_params["user"],
                password=self.connection_params["password"],
                database=self.connection_params["database"],
                connect_timeout=5
            )
            
            cursor = conn.cursor()
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name LIKE 'auth_%'
                ORDER BY table_name
            """)
            
            tables = [row[0] for row in cursor.fetchall()]
            cursor.close()
            conn.close()
            
            expected_tables = [
                'auth_users',
                'auth_password_hashes',
                'auth_sessions',
                'auth_events'
            ]
            
            missing_tables = [t for t in expected_tables if t not in tables]
            
            if tables:
                print(f"✅ Found {len(tables)} auth tables: {', '.join(tables)}")
            
            if missing_tables:
                print(f"⚠️  Missing auth tables: {', '.join(missing_tables)}")
                return False
            else:
                print("✅ All required auth tables exist")
                return True
                
        except Exception as e:
            print(f"❌ Failed to check auth tables: {e}")
            return False
    
    def provide_setup_instructions(self):
        """Provide setup instructions based on the current state."""
        print("\n" + "=" * 60)
        print("🛠️  Database Setup Instructions")
        print("=" * 60)
        
        if not self.check_postgresql_service():
            print("\n📋 PostgreSQL Service Setup:")
            print("1. Install PostgreSQL:")
            print("   Ubuntu/Debian: sudo apt-get install postgresql postgresql-contrib")
            print("   CentOS/RHEL:   sudo yum install postgresql-server postgresql-contrib")
            print("   macOS:         brew install postgresql")
            print()
            print("2. Start PostgreSQL service:")
            print("   Ubuntu/Debian: sudo systemctl start postgresql")
            print("   CentOS/RHEL:   sudo systemctl start postgresql")
            print("   macOS:         brew services start postgresql")
            print()
            print("3. Enable PostgreSQL to start on boot:")
            print("   sudo systemctl enable postgresql")
            return
        
        if not self.check_database_exists():
            print("\n📋 Database Creation:")
            print("1. Connect to PostgreSQL as superuser:")
            print("   sudo -u postgres psql")
            print()
            print("2. Create database and user:")
            print(f"   CREATE DATABASE {self.connection_params['database']};")
            print(f"   CREATE USER {self.connection_params['user']} WITH PASSWORD '{self.connection_params['password']}';")
            print(f"   GRANT ALL PRIVILEGES ON DATABASE {self.connection_params['database']} TO {self.connection_params['user']};")
            print("   CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")
            print("   CREATE EXTENSION IF NOT EXISTS \"pgcrypto\";")
            print("   \\q")
            return
        
        if not self.check_database_connectivity():
            print("\n📋 Connection Issues:")
            print("1. Check PostgreSQL configuration:")
            print("   - Verify pg_hba.conf allows connections")
            print("   - Verify postgresql.conf has correct listen_addresses")
            print()
            print("2. Check firewall settings:")
            print("   - Ensure port 5432 is open")
            print("   - Check iptables/ufw rules")
            return
        
        if not self.check_auth_tables():
            print("\n📋 Authentication Tables Setup:")
            print("1. Run the database migration:")
            print("   python3 scripts/simple_migration_runner.py")
            print()
            print("2. Or manually run the migration SQL:")
            print("   psql -h localhost -U karen_user -d ai_karen -f data/migrations/postgres/013_production_auth_schema_alignment.sql")
            return
        
        print("\n✅ Database is properly configured!")
        print("\n📋 Next Steps:")
        print("1. Test the authentication system:")
        print("   python3 tests/test_production_auth_integration.py")
        print()
        print("2. Initialize production authentication:")
        print("   python3 scripts/init_production_auth.py")
    
    async def validate_async_connection(self) -> bool:
        """Test async database connection."""
        print("🔍 Testing async database connection...")
        
        try:
            # Ensure async driver
            async_url = self.database_url
            if async_url.startswith("postgresql://"):
                async_url = async_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            
            engine = create_async_engine(async_url, pool_timeout=5)
            
            async with engine.begin() as conn:
                result = await conn.execute(text("SELECT 1 as test"))
                row = result.fetchone()
                
                if row and row[0] == 1:
                    print("✅ Async database connection successful")
                    await engine.dispose()
                    return True
                else:
                    print("❌ Async database connection test failed")
                    await engine.dispose()
                    return False
                    
        except Exception as e:
            print(f"❌ Async database connection failed: {e}")
            return False
    
    async def run_validation(self) -> bool:
        """Run complete database validation."""
        print("🗄️  Database Connection Validation")
        print("=" * 50)
        print(f"Database URL: {self.database_url}")
        print(f"Host: {self.connection_params['host']}:{self.connection_params['port']}")
        print(f"Database: {self.connection_params['database']}")
        print(f"User: {self.connection_params['user']}")
        print()
        
        # Check PostgreSQL service
        if not self.check_postgresql_service():
            self.provide_setup_instructions()
            return False
        
        # Check database exists
        if not self.check_database_exists():
            self.provide_setup_instructions()
            return False
        
        # Check connectivity
        if not self.check_database_connectivity():
            self.provide_setup_instructions()
            return False
        
        # Check async connectivity
        if not await self.validate_async_connection():
            self.provide_setup_instructions()
            return False
        
        # Check auth tables
        if not self.check_auth_tables():
            self.provide_setup_instructions()
            return False
        
        print("\n🎉 Database validation completed successfully!")
        print("✅ PostgreSQL service is running")
        print("✅ Database exists and is accessible")
        print("✅ Authentication tables are present")
        print("✅ Async connections work properly")
        
        return True


async def main():
    """Main function."""
    validator = DatabaseValidator()
    success = await validator.run_validation()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())