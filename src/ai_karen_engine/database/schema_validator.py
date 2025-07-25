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
        """
        Validate that memory-related tables exist and have required structure.
        Returns None if valid, or WebAPIErrorResponse if validation fails.
        """
        try:
            # Check if memory_entries table exists
            memory_entries_exists = await self._table_exists("memory_entries")
            
            if not memory_entries_exists:
                logger.warning("memory_entries table does not exist")
                return get_missing_tables_migration_response()
            
            # Validate memory_entries table structure
            required_columns = [
                "id", "vector_id", "user_id", "session_id", "content",
                "query", "embedding_id", "memory_metadata", "ttl",
                "timestamp", "created_at", "updated_at"
            ]
            
            missing_columns = await self._get_missing_columns("memory_entries", required_columns)
            
            if missing_columns:
                logger.warning(f"memory_entries table missing columns: {missing_columns}")
                return create_database_error_response(
                    error=Exception(f"memory_entries table missing columns: {', '.join(missing_columns)}"),
                    operation="schema_validation",
                    table_name="memory_entries",
                    user_message="Database schema is outdated. Migration required."
                )
            
            return None  # Validation passed
            
        except Exception as e:
            logger.error(f"Schema validation failed: {e}", exc_info=True)
            return create_database_error_response(
                error=e,
                operation="schema_validation",
                user_message="Database schema validation failed"
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
            
            logger.debug(f"Table {table_name} exists: {exists}")
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

            logger.debug(f"Table {table_name} missing columns: {missing_columns}")

            return missing_columns
            
        except Exception as e:
            logger.error(f"Error checking columns for table {table_name}: {e}")
            return required_columns  # Assume all are missing if we can't check
    
    async def create_memory_entries_table(self) -> bool:
        """
        Create the memory_entries table with all required fields.
        Returns True if successful, False otherwise.
        """
        try:
            create_table_sql = text("""
                CREATE TABLE IF NOT EXISTS memory_entries (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    vector_id VARCHAR(255) NOT NULL,
                    user_id UUID,
                    session_id VARCHAR(255),
                    content TEXT NOT NULL,
                    query VARCHAR(1000),
                    result TEXT,
                    embedding_id VARCHAR(255),
                    memory_metadata JSONB DEFAULT '{}',
                    ttl TIMESTAMP,
                    timestamp INTEGER,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    
                    -- Web UI integration fields (from migration 003)
                    ui_source VARCHAR(50),
                    conversation_id UUID,
                    memory_type VARCHAR(50) DEFAULT 'general',
                    tags TEXT[] DEFAULT '{}',
                    importance_score INTEGER DEFAULT 5,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TIMESTAMP,
                    ai_generated BOOLEAN DEFAULT FALSE,
                    user_confirmed BOOLEAN DEFAULT TRUE,
                    
                    -- Constraints
                    CONSTRAINT chk_importance_score CHECK (importance_score >= 1 AND importance_score <= 10)
                );
            """)
            
            await self.session.execute(create_table_sql)
            
            # Create indexes
            indexes_sql = [
                "CREATE INDEX IF NOT EXISTS idx_memory_entries_user_id ON memory_entries(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_memory_entries_vector_id ON memory_entries(vector_id);",
                "CREATE INDEX IF NOT EXISTS idx_memory_entries_session_id ON memory_entries(session_id);",
                "CREATE INDEX IF NOT EXISTS idx_memory_entries_created_at ON memory_entries(created_at);",
                "CREATE INDEX IF NOT EXISTS idx_memory_ui_source ON memory_entries(ui_source);",
                "CREATE INDEX IF NOT EXISTS idx_memory_conversation ON memory_entries(conversation_id);",
                "CREATE INDEX IF NOT EXISTS idx_memory_type ON memory_entries(memory_type);",
                "CREATE INDEX IF NOT EXISTS idx_memory_tags ON memory_entries USING GIN(tags);",
                "CREATE INDEX IF NOT EXISTS idx_memory_importance ON memory_entries(importance_score);",
                "CREATE INDEX IF NOT EXISTS idx_memory_user_conversation ON memory_entries(user_id, conversation_id);",
                "CREATE INDEX IF NOT EXISTS idx_memory_user_type ON memory_entries(user_id, memory_type);"
            ]
            
            for index_sql in indexes_sql:
                await self.session.execute(text(index_sql))
            
            await self.session.commit()
            
            logger.info("Successfully created memory_entries table with indexes")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create memory_entries table: {e}", exc_info=True)
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
            # Check and create memory_entries table
            if not await self._table_exists("memory_entries"):
                if await self.create_memory_entries_table():
                    created_tables.append("memory_entries")
                    logger.info("Auto-created memory_entries table")
                else:
                    logger.error("Failed to auto-create memory_entries table")
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
    """Get the complete SQL for creating all required tables."""
    return """
-- Create memory_entries table
CREATE TABLE IF NOT EXISTS memory_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vector_id VARCHAR(255) NOT NULL,
    user_id UUID,
    session_id VARCHAR(255),
    content TEXT NOT NULL,
    query VARCHAR(1000),
    result TEXT,
    embedding_id VARCHAR(255),
    memory_metadata JSONB DEFAULT '{}',
    ttl TIMESTAMP,
    timestamp INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Web UI integration fields
    ui_source VARCHAR(50),
    conversation_id UUID,
    memory_type VARCHAR(50) DEFAULT 'general',
    tags TEXT[] DEFAULT '{}',
    importance_score INTEGER DEFAULT 5,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,
    ai_generated BOOLEAN DEFAULT FALSE,
    user_confirmed BOOLEAN DEFAULT TRUE,
    
    -- Constraints
    CONSTRAINT chk_importance_score CHECK (importance_score >= 1 AND importance_score <= 10)
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

-- Create indexes for memory_entries
CREATE INDEX IF NOT EXISTS idx_memory_entries_user_id ON memory_entries(user_id);
CREATE INDEX IF NOT EXISTS idx_memory_entries_vector_id ON memory_entries(vector_id);
CREATE INDEX IF NOT EXISTS idx_memory_entries_session_id ON memory_entries(session_id);
CREATE INDEX IF NOT EXISTS idx_memory_entries_created_at ON memory_entries(created_at);
CREATE INDEX IF NOT EXISTS idx_memory_ui_source ON memory_entries(ui_source);
CREATE INDEX IF NOT EXISTS idx_memory_conversation ON memory_entries(conversation_id);
CREATE INDEX IF NOT EXISTS idx_memory_type ON memory_entries(memory_type);
CREATE INDEX IF NOT EXISTS idx_memory_tags ON memory_entries USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_memory_importance ON memory_entries(importance_score);
CREATE INDEX IF NOT EXISTS idx_memory_user_conversation ON memory_entries(user_id, conversation_id);
CREATE INDEX IF NOT EXISTS idx_memory_user_type ON memory_entries(user_id, memory_type);

-- Create indexes for conversations
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at);
CREATE INDEX IF NOT EXISTS idx_conversation_session ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_conversation_tags ON conversations USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_conversation_user_session ON conversations(user_id, session_id);
"""