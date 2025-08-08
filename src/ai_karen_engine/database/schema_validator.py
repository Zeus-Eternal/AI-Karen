"""
Database Schema Validator

This module provides utilities to validate database schema and handle missing tables.
It includes automatic migration detection and table creation for the memory system.
"""

import logging
from typing import Dict, List, Optional, Tuple

import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ai_karen_engine.models.web_api_error_responses import (
    WebAPIErrorCode,
    WebAPIErrorResponse,
    create_database_error_response,
    get_missing_tables_migration_response,
)

logger = logging.getLogger(__name__)


class DatabaseSchemaValidator:
    """Validates database schema and handles missing tables."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    

    async def validate_memory_tables(self) -> Optional[WebAPIErrorResponse]:
        """Validate that memory-related tables exist and have required structure."""
        try:
            memory_items_exists = await self._table_exists("memory_items")
            if not memory_items_exists:
                logger.warning("memory_items table does not exist")
                return get_missing_tables_migration_response()

            required_columns = [
                "id",
                "scope",
                "kind",
                "content",
                "embedding",
                "metadata",
                "created_at",
            ]
            missing_columns = await self._get_missing_columns("memory_items", required_columns)
            if missing_columns:
                logger.warning(f"memory_items table missing columns: {missing_columns}")
                return create_database_error_response(
                    error=Exception(
                        f"memory_items table missing columns: {', '.join(missing_columns)}"
                    ),
                    operation="schema_validation",
                    table_name="memory_items",
                    user_message="Database schema is outdated. Migration required.",
                )
            return None
        except Exception as e:
            logger.error(f"Schema validation failed: {e}", exc_info=True)
            return create_database_error_response(
                error=e,
                operation="schema_validation",
                user_message="Database schema validation failed",
            )
    async def _table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database."""
        try:
            query = text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = :table_name
                );
            """)
            
            result = await self.session.execute(query, {"table_name": table_name})
            exists = result.scalar()
            
            return bool(exists)
            
        except Exception as e:
            logger.error(f"Error checking if table {table_name} exists: {e}")
            return False
    
    async def _get_missing_columns(self, table_name: str, required_columns: List[str]) -> List[str]:
        """Get list of missing columns in a table."""
        try:
            query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = :table_name;
            """)
            
            result = await self.session.execute(query, {"table_name": table_name})
            existing_columns = {row[0] for row in result.fetchall()}
            
            missing_columns = [col for col in required_columns if col not in existing_columns]
            
            return missing_columns
            
        except Exception as e:
            logger.error(f"Error checking columns for table {table_name}: {e}")
            return required_columns  # Assume all are missing if we can't check
    

    async def create_memory_items_table(self) -> bool:
        """Create the memory_items table with required fields."""
        try:
            create_table_sql = text(
                """
                CREATE TABLE IF NOT EXISTS memory_items (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    scope TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    content TEXT NOT NULL,
                    embedding VECTOR(768),
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT NOW()
                );
                """
            )
            await self.session.execute(create_table_sql)

            indexes_sql = [
                "CREATE INDEX IF NOT EXISTS idx_memory_items_scope_kind ON memory_items(scope, kind);",
                "CREATE INDEX IF NOT EXISTS idx_memory_items_embedding ON memory_items USING ivfflat (embedding vector_l2_ops);",
            ]
            for stmt in indexes_sql:
                await self.session.execute(text(stmt))

            await self.session.commit()
            logger.info("Successfully created memory_items table with indexes")
            return True
        except Exception as e:
            logger.error(f"Failed to create memory_items table: {e}", exc_info=True)
            await self.session.rollback()
            return False
    async def create_conversations_table(self) -> bool:
        """
        Create the conversations table if it doesn't exist.
        Returns True if successful, False otherwise.
        """
        try:
            create_table_sql = text("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL,
                    title VARCHAR(255),
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    
                    -- Web UI integration fields (from migration 003)
                    session_id VARCHAR(255),
                    ui_context JSONB DEFAULT '{}',
                    ai_insights JSONB DEFAULT '{}',
                    user_settings JSONB DEFAULT '{}',
                    summary TEXT,
                    tags TEXT[] DEFAULT '{}',
                    last_ai_response_id VARCHAR(255)
                );
            """)
            
            await self.session.execute(create_table_sql)
            
            # Create indexes
            indexes_sql = [
                "CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at);",
                "CREATE INDEX IF NOT EXISTS idx_conversation_session ON conversations(session_id);",
                "CREATE INDEX IF NOT EXISTS idx_conversation_tags ON conversations USING GIN(tags);",
                "CREATE INDEX IF NOT EXISTS idx_conversation_user_session ON conversations(user_id, session_id);"
            ]
            
            for index_sql in indexes_sql:
                await self.session.execute(text(index_sql))
            
            await self.session.commit()
            
            logger.info("Successfully created conversations table with indexes")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create conversations table: {e}", exc_info=True)
            await self.session.rollback()
            return False
    
    async def auto_migrate_missing_tables(self) -> Tuple[bool, List[str]]:
        """
        Automatically create missing tables required for the memory system.
        Returns (success, list_of_created_tables).
        """
        created_tables = []
        
        try:
            # Check and create memory_items table
            if not await self._table_exists("memory_items"):
                if await self.create_memory_items_table():
                    created_tables.append("memory_items")
                    logger.info("Auto-created memory_items table")
                else:
                    logger.error("Failed to auto-create memory_items table")
                    return False, created_tables
            
            # Check and create conversations table
            if not await self._table_exists("conversations"):
                if await self.create_conversations_table():
                    created_tables.append("conversations")
                    logger.info("Auto-created conversations table")
                else:
                    logger.error("Failed to auto-create conversations table")
                    return False, created_tables
            
            return True, created_tables
            
        except Exception as e:
            logger.error(f"Auto-migration failed: {e}", exc_info=True)
            return False, created_tables


async def validate_and_migrate_schema(session: AsyncSession) -> Optional[WebAPIErrorResponse]:
    """
    Validate database schema and auto-migrate if needed.
    Returns None if successful, or WebAPIErrorResponse if validation/migration fails.
    """
    validator = DatabaseSchemaValidator(session)
    
    # First, validate the schema
    validation_error = await validator.validate_memory_tables()
    
    if validation_error:
        # If validation failed due to missing tables, try auto-migration
        if validation_error.type == WebAPIErrorCode.MIGRATION_REQUIRED:
            logger.info("Attempting auto-migration of missing tables")
            
            success, created_tables = await validator.auto_migrate_missing_tables()
            
            if success:
                logger.info(f"Auto-migration successful. Created tables: {created_tables}")
                return None  # Migration successful
            else:
                logger.error("Auto-migration failed")
                return validation_error
        else:
            # Other validation errors can't be auto-fixed
            return validation_error
    
    return None  # Validation passed


def get_database_migration_sql() -> str:
"""
-- Create memory_items table
CREATE TABLE IF NOT EXISTS memory_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scope TEXT NOT NULL,
    kind TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(768),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    title VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Web UI integration fields
    session_id VARCHAR(255),
    ui_context JSONB DEFAULT '{}',
    ai_insights JSONB DEFAULT '{}',
    user_settings JSONB DEFAULT '{}',
    summary TEXT,
    tags TEXT[] DEFAULT '{}',
    last_ai_response_id VARCHAR(255)
);

-- Create indexes for memory_items
CREATE INDEX IF NOT EXISTS idx_memory_items_scope_kind ON memory_items(scope, kind);
CREATE INDEX IF NOT EXISTS idx_memory_items_embedding ON memory_items USING ivfflat (embedding vector_l2_ops);

-- Create indexes for conversations
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
"""