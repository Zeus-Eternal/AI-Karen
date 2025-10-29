"""
Database migration script for extension authentication tables.
Migration 001: Create authentication tables for extension system.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio
import asyncpg
from pathlib import Path

logger = logging.getLogger(__name__)

class AuthTablesMigration:
    """Migration to create authentication tables for extension system."""
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.migration_id = "001_create_auth_tables"
        self.description = "Create authentication tables for extension system"
        
    async def up(self, connection: asyncpg.Connection) -> bool:
        """Apply the migration - create authentication tables."""
        try:
            logger.info(f"Applying migration {self.migration_id}")
            
            # Create extension_auth_tokens table
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS extension_auth_tokens (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    tenant_id VARCHAR(255) NOT NULL,
                    token_type VARCHAR(50) NOT NULL DEFAULT 'access',
                    token_hash VARCHAR(512) NOT NULL,
                    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    is_revoked BOOLEAN DEFAULT FALSE,
                    revoked_at TIMESTAMP WITH TIME ZONE NULL,
                    metadata JSONB DEFAULT '{}',
                    UNIQUE(token_hash)
                );
            """)
            
            # Create extension_permissions table
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS extension_permissions (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    tenant_id VARCHAR(255) NOT NULL,
                    extension_name VARCHAR(255) NOT NULL,
                    permission_type VARCHAR(100) NOT NULL,
                    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    granted_by VARCHAR(255) NOT NULL,
                    expires_at TIMESTAMP WITH TIME ZONE NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    metadata JSONB DEFAULT '{}',
                    UNIQUE(user_id, tenant_id, extension_name, permission_type)
                );
            """)
            
            # Create extension_auth_sessions table
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS extension_auth_sessions (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255) NOT NULL UNIQUE,
                    user_id VARCHAR(255) NOT NULL,
                    tenant_id VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    last_accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    user_agent TEXT,
                    ip_address INET,
                    metadata JSONB DEFAULT '{}'
                );
            """)
            
            # Create extension_auth_audit table
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS extension_auth_audit (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    tenant_id VARCHAR(255) NOT NULL,
                    action VARCHAR(100) NOT NULL,
                    resource VARCHAR(255) NOT NULL,
                    result VARCHAR(50) NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    ip_address INET,
                    user_agent TEXT,
                    details JSONB DEFAULT '{}'
                );
            """)
            
            # Create indexes for performance
            await self._create_indexes(connection)
            
            # Record migration
            await self._record_migration(connection)
            
            logger.info(f"Migration {self.migration_id} applied successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply migration {self.migration_id}: {e}")
            raise
    
    async def down(self, connection: asyncpg.Connection) -> bool:
        """Rollback the migration - drop authentication tables."""
        try:
            logger.info(f"Rolling back migration {self.migration_id}")
            
            # Drop tables in reverse order
            tables = [
                'extension_auth_audit',
                'extension_auth_sessions', 
                'extension_permissions',
                'extension_auth_tokens'
            ]
            
            for table in tables:
                await connection.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
            
            # Remove migration record
            await connection.execute("""
                DELETE FROM schema_migrations 
                WHERE migration_id = $1
            """, self.migration_id)
            
            logger.info(f"Migration {self.migration_id} rolled back successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rollback migration {self.migration_id}: {e}")
            raise
    
    async def _create_indexes(self, connection: asyncpg.Connection):
        """Create indexes for authentication tables."""
        indexes = [
            # extension_auth_tokens indexes
            "CREATE INDEX IF NOT EXISTS idx_auth_tokens_user_tenant ON extension_auth_tokens(user_id, tenant_id);",
            "CREATE INDEX IF NOT EXISTS idx_auth_tokens_expires ON extension_auth_tokens(expires_at);",
            "CREATE INDEX IF NOT EXISTS idx_auth_tokens_type ON extension_auth_tokens(token_type);",
            "CREATE INDEX IF NOT EXISTS idx_auth_tokens_revoked ON extension_auth_tokens(is_revoked);",
            
            # extension_permissions indexes
            "CREATE INDEX IF NOT EXISTS idx_permissions_user_tenant ON extension_permissions(user_id, tenant_id);",
            "CREATE INDEX IF NOT EXISTS idx_permissions_extension ON extension_permissions(extension_name);",
            "CREATE INDEX IF NOT EXISTS idx_permissions_active ON extension_permissions(is_active);",
            "CREATE INDEX IF NOT EXISTS idx_permissions_expires ON extension_permissions(expires_at);",
            
            # extension_auth_sessions indexes
            "CREATE INDEX IF NOT EXISTS idx_sessions_user_tenant ON extension_auth_sessions(user_id, tenant_id);",
            "CREATE INDEX IF NOT EXISTS idx_sessions_expires ON extension_auth_sessions(expires_at);",
            "CREATE INDEX IF NOT EXISTS idx_sessions_active ON extension_auth_sessions(is_active);",
            "CREATE INDEX IF NOT EXISTS idx_sessions_last_accessed ON extension_auth_sessions(last_accessed_at);",
            
            # extension_auth_audit indexes
            "CREATE INDEX IF NOT EXISTS idx_audit_user_tenant ON extension_auth_audit(user_id, tenant_id);",
            "CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON extension_auth_audit(timestamp);",
            "CREATE INDEX IF NOT EXISTS idx_audit_action ON extension_auth_audit(action);",
            "CREATE INDEX IF NOT EXISTS idx_audit_resource ON extension_auth_audit(resource);"
        ]
        
        for index_sql in indexes:
            await connection.execute(index_sql)
    
    async def _record_migration(self, connection: asyncpg.Connection):
        """Record migration in schema_migrations table."""
        # Create schema_migrations table if it doesn't exist
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id SERIAL PRIMARY KEY,
                migration_id VARCHAR(255) NOT NULL UNIQUE,
                description TEXT,
                applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                checksum VARCHAR(64)
            );
        """)
        
        # Record this migration
        await connection.execute("""
            INSERT INTO schema_migrations (migration_id, description)
            VALUES ($1, $2)
            ON CONFLICT (migration_id) DO NOTHING
        """, self.migration_id, self.description)


async def run_migration(db_config: Dict[str, Any], direction: str = "up") -> bool:
    """Run the authentication tables migration."""
    migration = AuthTablesMigration(db_config)
    
    try:
        # Connect to database
        connection = await asyncpg.connect(
            host=db_config.get('host', 'localhost'),
            port=db_config.get('port', 5432),
            user=db_config.get('user', 'postgres'),
            password=db_config.get('password', ''),
            database=db_config.get('database', 'kari')
        )
        
        try:
            if direction == "up":
                result = await migration.up(connection)
            elif direction == "down":
                result = await migration.down(connection)
            else:
                raise ValueError(f"Invalid migration direction: {direction}")
            
            return result
            
        finally:
            await connection.close()
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


if __name__ == "__main__":
    import sys
    import json
    
    # Load database configuration
    config_path = Path(__file__).parent.parent / "config" / "database.json"
    
    if config_path.exists():
        with open(config_path) as f:
            db_config = json.load(f)
    else:
        # Default configuration
        db_config = {
            'host': 'localhost',
            'port': 5432,
            'user': 'postgres',
            'password': '',
            'database': 'kari'
        }
    
    # Get direction from command line
    direction = sys.argv[1] if len(sys.argv) > 1 else "up"
    
    # Run migration
    asyncio.run(run_migration(db_config, direction))