"""
Database consolidation migrator for SQLite to PostgreSQL migration.

This module provides the DatabaseConsolidationMigrator class to handle the complete
migration process from SQLite authentication databases to PostgreSQL, ensuring
consistent UUID generation and proper foreign key relationships.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import asyncpg
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from .exceptions import DatabaseConnectionError, DatabaseOperationError, MigrationError
from .models import UserData, SessionData, AuthEvent, AuthEventType

logger = logging.getLogger(__name__)


@dataclass
class MigrationResult:
    """Result of a migration operation."""
    success: bool
    migrated_users: int = 0
    migrated_sessions: int = 0
    migrated_tokens: int = 0
    validation_results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def add_error(self, error: str) -> None:
        """Add an error to the result."""
        self.errors.append(error)
        logger.error(error)
    
    def add_warning(self, warning: str) -> None:
        """Add a warning to the result."""
        self.warnings.append(warning)
        logger.warning(warning)


@dataclass
class UUIDMapping:
    """Mapping between SQLite and PostgreSQL UUIDs."""
    sqlite_id: str
    postgres_id: str
    entity_type: str  # 'user', 'session', 'token'
    created_at: datetime = field(default_factory=datetime.utcnow)


class DatabaseConsolidationMigrator:
    """
    Handles complete data migration from SQLite to PostgreSQL.
    
    This migrator ensures consistent UUID generation and mapping,
    proper foreign key relationships, and comprehensive validation
    of the migration process.
    """
    
    def __init__(self, sqlite_paths: List[str], postgres_url: str):
        """
        Initialize the migrator.
        
        Args:
            sqlite_paths: List of SQLite database file paths to migrate from
            postgres_url: PostgreSQL connection URL
        """
        self.sqlite_paths = sqlite_paths
        self.postgres_url = postgres_url
        self.logger = logging.getLogger(__name__)
        
        # UUID mapping for maintaining relationships
        self.uuid_mappings: Dict[str, UUIDMapping] = {}
        
        # Connection objects
        self.sqlite_connections: List[sqlite3.Connection] = []
        self.postgres_engine = None
        self.async_postgres_engine = None
        
        # Migration statistics
        self.migration_stats = {
            'users_processed': 0,
            'sessions_processed': 0,
            'tokens_processed': 0,
            'errors': 0,
            'warnings': 0
        }
    
    async def migrate_all_data(self) -> MigrationResult:
        """
        Execute complete migration process.
        
        Returns:
            MigrationResult with detailed information about the migration
        """
        result = MigrationResult(success=False, started_at=datetime.utcnow())
        
        try:
            self.logger.info("Starting database consolidation migration")
            
            # Initialize connections
            await self._initialize_connections()
            
            # Create PostgreSQL schema if needed
            await self._ensure_postgres_schema()
            
            # Step 1: Migrate users with UUID mapping
            self.logger.info("Step 1: Migrating users")
            user_mapping = await self._migrate_users()
            result.migrated_users = len(user_mapping)
            
            # Step 2: Migrate sessions with updated foreign keys
            self.logger.info("Step 2: Migrating sessions")
            session_count = await self._migrate_sessions(user_mapping)
            result.migrated_sessions = session_count
            
            # Step 3: Migrate tokens and other auth data
            self.logger.info("Step 3: Migrating tokens")
            token_count = await self._migrate_tokens(user_mapping)
            result.migrated_tokens = token_count
            
            # Step 4: Validate migration
            self.logger.info("Step 4: Validating migration")
            validation_result = await self._validate_migration()
            result.validation_results = validation_result
            
            result.success = validation_result.get('overall_success', False)
            result.completed_at = datetime.utcnow()
            
            self.logger.info(f"Migration completed successfully: {result}")
            return result
            
        except Exception as e:
            error_msg = f"Migration failed: {str(e)}"
            result.add_error(error_msg)
            result.completed_at = datetime.utcnow()
            
            # Attempt rollback
            try:
                await self._rollback_migration()
            except Exception as rollback_error:
                result.add_error(f"Rollback failed: {str(rollback_error)}")
            
            raise MigrationError(error_msg) from e
        
        finally:
            await self._cleanup_connections()
    
    async def _initialize_connections(self) -> None:
        """Initialize database connections."""
        try:
            # Initialize SQLite connections
            for sqlite_path in self.sqlite_paths:
                if not Path(sqlite_path).exists():
                    self.logger.warning(f"SQLite database not found: {sqlite_path}")
                    continue
                
                conn = sqlite3.connect(sqlite_path)
                conn.row_factory = sqlite3.Row
                self.sqlite_connections.append(conn)
            
            if not self.sqlite_connections:
                raise DatabaseConnectionError("No valid SQLite databases found")
            
            # Initialize PostgreSQL connections
            self.postgres_engine = create_engine(self.postgres_url)
            self.async_postgres_engine = create_async_engine(self.postgres_url)
            
            # Test PostgreSQL connection
            async with self.async_postgres_engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            
            self.logger.info(f"Initialized {len(self.sqlite_connections)} SQLite connections and PostgreSQL connection")
            
        except Exception as e:
            raise DatabaseConnectionError(f"Failed to initialize connections: {e}")
    
    async def _ensure_postgres_schema(self) -> None:
        """Ensure PostgreSQL schema exists for authentication data."""
        try:
            async with self.async_postgres_engine.begin() as conn:
                # Create users table
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS users (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        email VARCHAR(255) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        full_name VARCHAR(255),
                        tenant_id UUID NOT NULL,
                        roles JSONB DEFAULT '[]'::jsonb,
                        preferences JSONB DEFAULT '{}'::jsonb,
                        is_verified BOOLEAN DEFAULT false,
                        is_active BOOLEAN DEFAULT true,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        last_login_at TIMESTAMP WITH TIME ZONE,
                        failed_login_attempts INTEGER DEFAULT 0,
                        locked_until TIMESTAMP WITH TIME ZONE,
                        two_factor_enabled BOOLEAN DEFAULT false,
                        two_factor_secret VARCHAR(255)
                    )
                """))
                
                # Create sessions table
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        session_token VARCHAR(255) UNIQUE NOT NULL,
                        access_token TEXT,
                        refresh_token TEXT,
                        expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        ip_address INET,
                        user_agent TEXT,
                        device_fingerprint VARCHAR(255),
                        geolocation JSONB,
                        risk_score FLOAT DEFAULT 0.0,
                        security_flags JSONB DEFAULT '[]'::jsonb,
                        is_active BOOLEAN DEFAULT true,
                        invalidated_at TIMESTAMP WITH TIME ZONE,
                        invalidation_reason VARCHAR(255)
                    )
                """))
                
                # Create password reset tokens table
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS password_reset_tokens (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        token VARCHAR(255) UNIQUE NOT NULL,
                        expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                        used BOOLEAN DEFAULT false,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        ip_address INET,
                        user_agent TEXT
                    )
                """))
                
                # Create email verification tokens table
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS email_verification_tokens (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        token VARCHAR(255) UNIQUE NOT NULL,
                        expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                        used BOOLEAN DEFAULT false,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        ip_address INET,
                        user_agent TEXT
                    )
                """))
                
                # Create indexes
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_tenant_id ON users(tenant_id)"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id)"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token)"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sessions_expires ON user_sessions(expires_at)"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_reset_tokens_token ON password_reset_tokens(token)"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_reset_tokens_user_id ON password_reset_tokens(user_id)"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_verification_tokens_token ON email_verification_tokens(token)"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_verification_tokens_user_id ON email_verification_tokens(user_id)"))
            
            self.logger.info("PostgreSQL schema ensured")
            
        except Exception as e:
            raise DatabaseOperationError(f"Failed to ensure PostgreSQL schema: {e}")
    
    async def _migrate_users(self) -> Dict[str, str]:
        """
        Migrate users with consistent UUID generation and mapping.
        
        Returns:
            Dictionary mapping old user IDs to new PostgreSQL UUIDs
        """
        user_mapping = {}
        
        try:
            async with self.async_postgres_engine.begin() as conn:
                for sqlite_conn in self.sqlite_connections:
                    cursor = sqlite_conn.cursor()
                    
                    # Try different table names for users
                    user_tables = ['auth_users', 'users']
                    users_found = False
                    
                    for table_name in user_tables:
                        try:
                            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                            if cursor.fetchone():
                                cursor.execute(f"SELECT * FROM {table_name}")
                                users = cursor.fetchall()
                                users_found = True
                                
                                for user_row in users:
                                    try:
                                        # Generate consistent UUID for PostgreSQL
                                        postgres_uuid = str(uuid.uuid4())
                                        old_user_id = user_row.get('user_id') or user_row.get('id')
                                        
                                        if not old_user_id:
                                            self.logger.warning(f"User without ID found, skipping: {dict(user_row)}")
                                            continue
                                        
                                        # Check if user already exists in PostgreSQL
                                        email = user_row['email']
                                        existing_user = await conn.execute(
                                            text("SELECT id FROM users WHERE email = :email"),
                                            {"email": email}
                                        )
                                        existing_result = existing_user.fetchone()
                                        
                                        if existing_result:
                                            postgres_uuid = str(existing_result[0])
                                            self.logger.info(f"User {email} already exists, using existing UUID: {postgres_uuid}")
                                        else:
                                            # Insert new user
                                            await self._insert_user_to_postgres(conn, user_row, postgres_uuid, table_name)
                                        
                                        # Store mapping
                                        user_mapping[old_user_id] = postgres_uuid
                                        self.uuid_mappings[old_user_id] = UUIDMapping(
                                            sqlite_id=old_user_id,
                                            postgres_id=postgres_uuid,
                                            entity_type='user'
                                        )
                                        
                                        self.migration_stats['users_processed'] += 1
                                        
                                    except Exception as e:
                                        error_msg = f"Failed to migrate user {user_row.get('email', 'unknown')}: {e}"
                                        self.logger.error(error_msg)
                                        self.migration_stats['errors'] += 1
                                
                                break  # Found users in this table, no need to check others
                                
                        except sqlite3.OperationalError:
                            # Table doesn't exist, try next one
                            continue
                    
                    if not users_found:
                        self.logger.warning(f"No user tables found in {sqlite_conn}")
            
            self.logger.info(f"Migrated {len(user_mapping)} users")
            return user_mapping
            
        except Exception as e:
            raise DatabaseOperationError(f"Failed to migrate users: {e}")
    
    async def _insert_user_to_postgres(self, conn, user_row: sqlite3.Row, postgres_uuid: str, table_name: str) -> None:
        """Insert a user into PostgreSQL with proper data conversion."""
        try:
            # Helper function to safely get values
            def safe_get(row, key, default=None):
                try:
                    return row[key] if key in row.keys() else default
                except (KeyError, TypeError):
                    return default
            
            # Convert roles to JSONB
            roles = safe_get(user_row, 'roles', '["user"]')
            if isinstance(roles, str):
                try:
                    roles_list = json.loads(roles)
                except json.JSONDecodeError:
                    roles_list = [roles] if roles else ["user"]
            else:
                roles_list = roles if isinstance(roles, list) else ["user"]
            
            # Convert preferences to JSONB
            preferences = safe_get(user_row, 'preferences', '{}')
            if isinstance(preferences, str):
                try:
                    preferences_dict = json.loads(preferences)
                except json.JSONDecodeError:
                    preferences_dict = {}
            else:
                preferences_dict = preferences if isinstance(preferences, dict) else {}
            
            # Handle password hash - might be in the same table or separate table
            password_hash = safe_get(user_row, 'password_hash')
            if not password_hash:
                # Try to get from separate password table if it exists
                old_user_id = safe_get(user_row, 'user_id') or safe_get(user_row, 'id')
                if old_user_id:
                    # Check if there's a separate password hash table
                    for sqlite_conn in self.sqlite_connections:
                        cursor = sqlite_conn.cursor()
                        try:
                            cursor.execute("SELECT password_hash FROM auth_password_hashes WHERE user_id = ?", (old_user_id,))
                            hash_row = cursor.fetchone()
                            if hash_row:
                                password_hash = hash_row['password_hash']
                                break
                        except sqlite3.OperationalError:
                            continue
            
            if not password_hash:
                # Generate a placeholder hash - user will need to reset password
                password_hash = "$2b$12$placeholder.hash.user.must.reset.password"
                self.logger.warning(f"No password hash found for user {user_row['email']}, using placeholder")
            
            # Convert timestamps
            created_at = safe_get(user_row, 'created_at')
            if created_at and isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except ValueError:
                    created_at = datetime.utcnow()
            else:
                created_at = datetime.utcnow()
            
            updated_at = safe_get(user_row, 'updated_at')
            if updated_at and isinstance(updated_at, str):
                try:
                    updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                except ValueError:
                    updated_at = datetime.utcnow()
            else:
                updated_at = datetime.utcnow()
            
            last_login_at = safe_get(user_row, 'last_login_at')
            if last_login_at and isinstance(last_login_at, str):
                try:
                    last_login_at = datetime.fromisoformat(last_login_at.replace('Z', '+00:00'))
                except ValueError:
                    last_login_at = None
            
            locked_until = safe_get(user_row, 'locked_until')
            if locked_until and isinstance(locked_until, str):
                try:
                    locked_until = datetime.fromisoformat(locked_until.replace('Z', '+00:00'))
                except ValueError:
                    locked_until = None
            
            # Insert user
            await conn.execute(text("""
                INSERT INTO users (
                    id, email, password_hash, full_name, tenant_id, roles, preferences,
                    is_verified, is_active, created_at, updated_at, last_login_at,
                    failed_login_attempts, locked_until, two_factor_enabled, two_factor_secret
                ) VALUES (
                    :id, :email, :password_hash, :full_name, :tenant_id, :roles, :preferences,
                    :is_verified, :is_active, :created_at, :updated_at, :last_login_at,
                    :failed_login_attempts, :locked_until, :two_factor_enabled, :two_factor_secret
                )
            """), {
                "id": postgres_uuid,
                "email": user_row['email'],
                "password_hash": password_hash,
                "full_name": safe_get(user_row, 'full_name') or safe_get(user_row, 'name'),
                "tenant_id": safe_get(user_row, 'tenant_id', str(uuid.uuid4())),  # Generate tenant UUID if missing
                "roles": json.dumps(roles_list),
                "preferences": json.dumps(preferences_dict),
                "is_verified": bool(safe_get(user_row, 'is_verified', True)),
                "is_active": bool(safe_get(user_row, 'is_active', True)),
                "created_at": created_at,
                "updated_at": updated_at,
                "last_login_at": last_login_at,
                "failed_login_attempts": int(safe_get(user_row, 'failed_login_attempts', 0)),
                "locked_until": locked_until,
                "two_factor_enabled": bool(safe_get(user_row, 'two_factor_enabled', False)),
                "two_factor_secret": safe_get(user_row, 'two_factor_secret')
            })
            
        except Exception as e:
            raise DatabaseOperationError(f"Failed to insert user to PostgreSQL: {e}")
    
    async def _migrate_sessions(self, user_mapping: Dict[str, str]) -> int:
        """
        Migrate sessions with proper foreign key relationships.
        
        Args:
            user_mapping: Dictionary mapping old user IDs to new PostgreSQL UUIDs
            
        Returns:
            Number of sessions migrated
        """
        session_count = 0
        
        try:
            async with self.async_postgres_engine.begin() as conn:
                for sqlite_conn in self.sqlite_connections:
                    cursor = sqlite_conn.cursor()
                    
                    # Try different table names for sessions
                    session_tables = ['auth_sessions', 'user_sessions', 'sessions']
                    
                    for table_name in session_tables:
                        try:
                            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                            if cursor.fetchone():
                                cursor.execute(f"SELECT * FROM {table_name} WHERE is_active = 1")
                                sessions = cursor.fetchall()
                                
                                for session_row in sessions:
                                    try:
                                        old_user_id = session_row.get('user_id')
                                        if not old_user_id or old_user_id not in user_mapping:
                                            self.logger.warning(f"Session without valid user_id found, skipping: {dict(session_row)}")
                                            continue
                                        
                                        postgres_user_id = user_mapping[old_user_id]
                                        
                                        # Check if session already exists
                                        session_token = session_row.get('session_token')
                                        if session_token:
                                            existing_session = await conn.execute(
                                                text("SELECT id FROM user_sessions WHERE session_token = :token"),
                                                {"token": session_token}
                                            )
                                            if existing_session.fetchone():
                                                self.logger.info(f"Session {session_token} already exists, skipping")
                                                continue
                                        
                                        await self._insert_session_to_postgres(conn, session_row, postgres_user_id)
                                        session_count += 1
                                        self.migration_stats['sessions_processed'] += 1
                                        
                                    except Exception as e:
                                        error_msg = f"Failed to migrate session: {e}"
                                        self.logger.error(error_msg)
                                        self.migration_stats['errors'] += 1
                                
                                break  # Found sessions in this table
                                
                        except sqlite3.OperationalError:
                            continue
            
            self.logger.info(f"Migrated {session_count} sessions")
            return session_count
            
        except Exception as e:
            raise DatabaseOperationError(f"Failed to migrate sessions: {e}")
    
    async def _insert_session_to_postgres(self, conn, session_row: sqlite3.Row, postgres_user_id: str) -> None:
        """Insert a session into PostgreSQL with proper data conversion."""
        try:
            def safe_get(row, key, default=None):
                try:
                    return row[key] if key in row.keys() else default
                except (KeyError, TypeError):
                    return default
            
            # Generate session UUID
            session_uuid = str(uuid.uuid4())
            
            # Convert timestamps
            created_at = safe_get(session_row, 'created_at')
            if created_at and isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except ValueError:
                    created_at = datetime.utcnow()
            else:
                created_at = datetime.utcnow()
            
            last_accessed = safe_get(session_row, 'last_accessed')
            if last_accessed and isinstance(last_accessed, str):
                try:
                    last_accessed = datetime.fromisoformat(last_accessed.replace('Z', '+00:00'))
                except ValueError:
                    last_accessed = datetime.utcnow()
            else:
                last_accessed = datetime.utcnow()
            
            # Calculate expires_at from expires_in if available
            expires_at = safe_get(session_row, 'expires_at')
            if not expires_at:
                expires_in = safe_get(session_row, 'expires_in', 3600)  # Default 1 hour
                expires_at = created_at + timedelta(seconds=int(expires_in))
            elif isinstance(expires_at, str):
                try:
                    expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                except ValueError:
                    expires_at = created_at + timedelta(hours=24)  # Default 24 hours
            
            # Convert security flags and geolocation
            security_flags = safe_get(session_row, 'security_flags', '[]')
            if isinstance(security_flags, str):
                try:
                    security_flags_list = json.loads(security_flags)
                except json.JSONDecodeError:
                    security_flags_list = []
            else:
                security_flags_list = security_flags if isinstance(security_flags, list) else []
            
            geolocation = safe_get(session_row, 'geolocation')
            if isinstance(geolocation, str) and geolocation:
                try:
                    geolocation_dict = json.loads(geolocation)
                except json.JSONDecodeError:
                    geolocation_dict = None
            else:
                geolocation_dict = geolocation if isinstance(geolocation, dict) else None
            
            # Insert session
            await conn.execute(text("""
                INSERT INTO user_sessions (
                    id, user_id, session_token, access_token, refresh_token, expires_at,
                    created_at, last_accessed, ip_address, user_agent, device_fingerprint,
                    geolocation, risk_score, security_flags, is_active, invalidated_at, invalidation_reason
                ) VALUES (
                    :id, :user_id, :session_token, :access_token, :refresh_token, :expires_at,
                    :created_at, :last_accessed, :ip_address, :user_agent, :device_fingerprint,
                    :geolocation, :risk_score, :security_flags, :is_active, :invalidated_at, :invalidation_reason
                )
            """), {
                "id": session_uuid,
                "user_id": postgres_user_id,
                "session_token": safe_get(session_row, 'session_token', str(uuid.uuid4())),
                "access_token": safe_get(session_row, 'access_token'),
                "refresh_token": safe_get(session_row, 'refresh_token'),
                "expires_at": expires_at,
                "created_at": created_at,
                "last_accessed": last_accessed,
                "ip_address": safe_get(session_row, 'ip_address', '127.0.0.1'),
                "user_agent": safe_get(session_row, 'user_agent', ''),
                "device_fingerprint": safe_get(session_row, 'device_fingerprint'),
                "geolocation": json.dumps(geolocation_dict) if geolocation_dict else None,
                "risk_score": float(safe_get(session_row, 'risk_score', 0.0)),
                "security_flags": json.dumps(security_flags_list),
                "is_active": bool(safe_get(session_row, 'is_active', True)),
                "invalidated_at": None,  # Active sessions shouldn't be invalidated
                "invalidation_reason": None
            })
            
        except Exception as e:
            raise DatabaseOperationError(f"Failed to insert session to PostgreSQL: {e}")
    
    async def _migrate_tokens(self, user_mapping: Dict[str, str]) -> int:
        """
        Migrate password reset and email verification tokens.
        
        Args:
            user_mapping: Dictionary mapping old user IDs to new PostgreSQL UUIDs
            
        Returns:
            Number of tokens migrated
        """
        token_count = 0
        
        try:
            async with self.async_postgres_engine.begin() as conn:
                for sqlite_conn in self.sqlite_connections:
                    cursor = sqlite_conn.cursor()
                    
                    # Migrate password reset tokens
                    try:
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='auth_password_reset_tokens'")
                        if cursor.fetchone():
                            cursor.execute("SELECT * FROM auth_password_reset_tokens WHERE used_at IS NULL")
                            reset_tokens = cursor.fetchall()
                            
                            for token_row in reset_tokens:
                                try:
                                    old_user_id = token_row.get('user_id')
                                    if not old_user_id or old_user_id not in user_mapping:
                                        continue
                                    
                                    postgres_user_id = user_mapping[old_user_id]
                                    await self._insert_reset_token_to_postgres(conn, token_row, postgres_user_id)
                                    token_count += 1
                                    
                                except Exception as e:
                                    self.logger.error(f"Failed to migrate reset token: {e}")
                                    self.migration_stats['errors'] += 1
                    except sqlite3.OperationalError:
                        pass
                    
                    # Migrate email verification tokens
                    try:
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='auth_email_verification_tokens'")
                        if cursor.fetchone():
                            cursor.execute("SELECT * FROM auth_email_verification_tokens WHERE used_at IS NULL")
                            verification_tokens = cursor.fetchall()
                            
                            for token_row in verification_tokens:
                                try:
                                    old_user_id = token_row.get('user_id')
                                    if not old_user_id or old_user_id not in user_mapping:
                                        continue
                                    
                                    postgres_user_id = user_mapping[old_user_id]
                                    await self._insert_verification_token_to_postgres(conn, token_row, postgres_user_id)
                                    token_count += 1
                                    
                                except Exception as e:
                                    self.logger.error(f"Failed to migrate verification token: {e}")
                                    self.migration_stats['errors'] += 1
                    except sqlite3.OperationalError:
                        pass
            
            self.migration_stats['tokens_processed'] = token_count
            self.logger.info(f"Migrated {token_count} tokens")
            return token_count
            
        except Exception as e:
            raise DatabaseOperationError(f"Failed to migrate tokens: {e}")
    
    async def _insert_reset_token_to_postgres(self, conn, token_row: sqlite3.Row, postgres_user_id: str) -> None:
        """Insert a password reset token into PostgreSQL."""
        try:
            def safe_get(row, key, default=None):
                try:
                    return row[key] if key in row.keys() else default
                except (KeyError, TypeError):
                    return default
            
            # Convert timestamps
            created_at = safe_get(token_row, 'created_at')
            if created_at and isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except ValueError:
                    created_at = datetime.utcnow()
            else:
                created_at = datetime.utcnow()
            
            expires_at = safe_get(token_row, 'expires_at')
            if expires_at and isinstance(expires_at, str):
                try:
                    expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                except ValueError:
                    expires_at = created_at + timedelta(hours=1)  # Default 1 hour
            else:
                expires_at = created_at + timedelta(hours=1)
            
            await conn.execute(text("""
                INSERT INTO password_reset_tokens (
                    id, user_id, token, expires_at, used, created_at, ip_address, user_agent
                ) VALUES (
                    :id, :user_id, :token, :expires_at, :used, :created_at, :ip_address, :user_agent
                )
            """), {
                "id": str(uuid.uuid4()),
                "user_id": postgres_user_id,
                "token": safe_get(token_row, 'token_hash') or safe_get(token_row, 'token', str(uuid.uuid4())),
                "expires_at": expires_at,
                "used": bool(safe_get(token_row, 'used_at')),
                "created_at": created_at,
                "ip_address": safe_get(token_row, 'ip_address', '127.0.0.1'),
                "user_agent": safe_get(token_row, 'user_agent', '')
            })
            
        except Exception as e:
            raise DatabaseOperationError(f"Failed to insert reset token to PostgreSQL: {e}")
    
    async def _insert_verification_token_to_postgres(self, conn, token_row: sqlite3.Row, postgres_user_id: str) -> None:
        """Insert an email verification token into PostgreSQL."""
        try:
            def safe_get(row, key, default=None):
                try:
                    return row[key] if key in row.keys() else default
                except (KeyError, TypeError):
                    return default
            
            # Convert timestamps
            created_at = safe_get(token_row, 'created_at')
            if created_at and isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except ValueError:
                    created_at = datetime.utcnow()
            else:
                created_at = datetime.utcnow()
            
            expires_at = safe_get(token_row, 'expires_at')
            if expires_at and isinstance(expires_at, str):
                try:
                    expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                except ValueError:
                    expires_at = created_at + timedelta(hours=24)  # Default 24 hours
            else:
                expires_at = created_at + timedelta(hours=24)
            
            await conn.execute(text("""
                INSERT INTO email_verification_tokens (
                    id, user_id, token, expires_at, used, created_at, ip_address, user_agent
                ) VALUES (
                    :id, :user_id, :token, :expires_at, :used, :created_at, :ip_address, :user_agent
                )
            """), {
                "id": str(uuid.uuid4()),
                "user_id": postgres_user_id,
                "token": safe_get(token_row, 'token_hash') or safe_get(token_row, 'token', str(uuid.uuid4())),
                "expires_at": expires_at,
                "used": bool(safe_get(token_row, 'used_at')),
                "created_at": created_at,
                "ip_address": safe_get(token_row, 'ip_address', '127.0.0.1'),
                "user_agent": safe_get(token_row, 'user_agent', '')
            })
            
        except Exception as e:
            raise DatabaseOperationError(f"Failed to insert verification token to PostgreSQL: {e}")
    
    async def _validate_migration(self) -> Dict[str, Any]:
        """
        Comprehensive validation logic to verify migration success.
        
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            'overall_success': True,
            'user_count_match': False,
            'session_count_match': False,
            'foreign_key_integrity': False,
            'data_integrity_checks': [],
            'errors': [],
            'warnings': []
        }
        
        try:
            # Count records in SQLite
            sqlite_counts = {'users': 0, 'sessions': 0, 'tokens': 0}
            
            for sqlite_conn in self.sqlite_connections:
                cursor = sqlite_conn.cursor()
                
                # Count users
                for table in ['auth_users', 'users']:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        sqlite_counts['users'] += count
                        break
                    except sqlite3.OperationalError:
                        continue
                
                # Count sessions
                for table in ['auth_sessions', 'user_sessions', 'sessions']:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE is_active = 1")
                        count = cursor.fetchone()[0]
                        sqlite_counts['sessions'] += count
                        break
                    except sqlite3.OperationalError:
                        continue
                
                # Count tokens
                for table in ['auth_password_reset_tokens', 'auth_email_verification_tokens']:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE used_at IS NULL")
                        count = cursor.fetchone()[0]
                        sqlite_counts['tokens'] += count
                    except sqlite3.OperationalError:
                        continue
            
            # Count records in PostgreSQL
            async with self.async_postgres_engine.begin() as conn:
                # Count users
                result = await conn.execute(text("SELECT COUNT(*) FROM users"))
                postgres_user_count = result.scalar()
                
                # Count sessions
                result = await conn.execute(text("SELECT COUNT(*) FROM user_sessions WHERE is_active = true"))
                postgres_session_count = result.scalar()
                
                # Count tokens
                result = await conn.execute(text("SELECT COUNT(*) FROM password_reset_tokens WHERE used = false"))
                reset_token_count = result.scalar()
                
                result = await conn.execute(text("SELECT COUNT(*) FROM email_verification_tokens WHERE used = false"))
                verification_token_count = result.scalar()
                
                postgres_token_count = reset_token_count + verification_token_count
                
                # Validate counts
                validation_results['user_count_match'] = sqlite_counts['users'] == postgres_user_count
                validation_results['session_count_match'] = sqlite_counts['sessions'] == postgres_session_count
                
                if not validation_results['user_count_match']:
                    validation_results['errors'].append(
                        f"User count mismatch: SQLite={sqlite_counts['users']}, PostgreSQL={postgres_user_count}"
                    )
                
                if not validation_results['session_count_match']:
                    validation_results['warnings'].append(
                        f"Session count mismatch: SQLite={sqlite_counts['sessions']}, PostgreSQL={postgres_session_count}"
                    )
                
                # Check foreign key integrity
                result = await conn.execute(text("""
                    SELECT COUNT(*) FROM user_sessions s 
                    LEFT JOIN users u ON s.user_id = u.id 
                    WHERE u.id IS NULL
                """))
                orphaned_sessions = result.scalar()
                
                result = await conn.execute(text("""
                    SELECT COUNT(*) FROM password_reset_tokens t 
                    LEFT JOIN users u ON t.user_id = u.id 
                    WHERE u.id IS NULL
                """))
                orphaned_reset_tokens = result.scalar()
                
                result = await conn.execute(text("""
                    SELECT COUNT(*) FROM email_verification_tokens t 
                    LEFT JOIN users u ON t.user_id = u.id 
                    WHERE u.id IS NULL
                """))
                orphaned_verification_tokens = result.scalar()
                
                validation_results['foreign_key_integrity'] = (
                    orphaned_sessions == 0 and 
                    orphaned_reset_tokens == 0 and 
                    orphaned_verification_tokens == 0
                )
                
                if not validation_results['foreign_key_integrity']:
                    validation_results['errors'].append(
                        f"Foreign key integrity issues: {orphaned_sessions} orphaned sessions, "
                        f"{orphaned_reset_tokens} orphaned reset tokens, "
                        f"{orphaned_verification_tokens} orphaned verification tokens"
                    )
                
                # Additional data integrity checks
                validation_results['data_integrity_checks'] = await self._perform_data_integrity_checks(conn)
            
            # Overall success
            validation_results['overall_success'] = (
                validation_results['user_count_match'] and
                validation_results['foreign_key_integrity'] and
                len(validation_results['errors']) == 0
            )
            
            self.logger.info(f"Migration validation completed: {validation_results}")
            return validation_results
            
        except Exception as e:
            validation_results['overall_success'] = False
            validation_results['errors'].append(f"Validation failed: {e}")
            self.logger.error(f"Migration validation failed: {e}")
            return validation_results
    
    async def _perform_data_integrity_checks(self, conn) -> List[Dict[str, Any]]:
        """Perform additional data integrity checks."""
        checks = []
        
        try:
            # Check for duplicate emails
            result = await conn.execute(text("""
                SELECT email, COUNT(*) as count 
                FROM users 
                GROUP BY email 
                HAVING COUNT(*) > 1
            """))
            duplicate_emails = result.fetchall()
            
            checks.append({
                'check': 'duplicate_emails',
                'passed': len(duplicate_emails) == 0,
                'details': f"Found {len(duplicate_emails)} duplicate emails" if duplicate_emails else "No duplicate emails"
            })
            
            # Check for users without valid tenant_id
            result = await conn.execute(text("SELECT COUNT(*) FROM users WHERE tenant_id IS NULL"))
            null_tenant_count = result.scalar()
            
            checks.append({
                'check': 'valid_tenant_ids',
                'passed': null_tenant_count == 0,
                'details': f"Found {null_tenant_count} users without tenant_id" if null_tenant_count > 0 else "All users have tenant_id"
            })
            
            # Check for expired sessions that are still active
            result = await conn.execute(text("""
                SELECT COUNT(*) FROM user_sessions 
                WHERE is_active = true AND expires_at < NOW()
            """))
            expired_active_sessions = result.scalar()
            
            checks.append({
                'check': 'expired_active_sessions',
                'passed': expired_active_sessions == 0,
                'details': f"Found {expired_active_sessions} expired but active sessions" if expired_active_sessions > 0 else "No expired active sessions"
            })
            
        except Exception as e:
            checks.append({
                'check': 'data_integrity_error',
                'passed': False,
                'details': f"Error during integrity checks: {e}"
            })
        
        return checks
    
    async def _rollback_migration(self) -> None:
        """Rollback migration by cleaning up PostgreSQL data."""
        try:
            self.logger.warning("Attempting to rollback migration")
            
            async with self.async_postgres_engine.begin() as conn:
                # Delete migrated data in reverse order to respect foreign keys
                await conn.execute(text("DELETE FROM email_verification_tokens"))
                await conn.execute(text("DELETE FROM password_reset_tokens"))
                await conn.execute(text("DELETE FROM user_sessions"))
                await conn.execute(text("DELETE FROM users"))
            
            self.logger.info("Migration rollback completed")
            
        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
            raise
    
    async def _cleanup_connections(self) -> None:
        """Clean up database connections."""
        try:
            # Close SQLite connections
            for conn in self.sqlite_connections:
                conn.close()
            
            # Close PostgreSQL connections
            if self.async_postgres_engine:
                await self.async_postgres_engine.dispose()
            
            if self.postgres_engine:
                self.postgres_engine.dispose()
            
            self.logger.info("Database connections cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up connections: {e}")


class MigrationValidator:
    """Validates migration success and data integrity."""
    
    def __init__(self, postgres_url: str):
        self.postgres_url = postgres_url
        self.async_engine = create_async_engine(postgres_url)
    
    async def validate_complete_migration(self) -> Dict[str, Any]:
        """
        Perform comprehensive validation of the completed migration.
        
        Returns:
            Detailed validation report
        """
        validation_report = {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': 'unknown',
            'checks_performed': [],
            'issues_found': [],
            'recommendations': []
        }
        
        try:
            async with self.async_engine.begin() as conn:
                # Check table existence
                tables_check = await self._check_table_existence(conn)
                validation_report['checks_performed'].append(tables_check)
                
                # Check data consistency
                consistency_check = await self._check_data_consistency(conn)
                validation_report['checks_performed'].append(consistency_check)
                
                # Check foreign key constraints
                fk_check = await self._check_foreign_key_constraints(conn)
                validation_report['checks_performed'].append(fk_check)
                
                # Check for data anomalies
                anomaly_check = await self._check_data_anomalies(conn)
                validation_report['checks_performed'].append(anomaly_check)
                
                # Determine overall status
                all_passed = all(check.get('passed', False) for check in validation_report['checks_performed'])
                validation_report['overall_status'] = 'passed' if all_passed else 'failed'
                
                # Generate recommendations
                if not all_passed:
                    validation_report['recommendations'] = self._generate_recommendations(validation_report['checks_performed'])
            
            return validation_report
            
        except Exception as e:
            validation_report['overall_status'] = 'error'
            validation_report['issues_found'].append(f"Validation error: {e}")
            return validation_report
        
        finally:
            await self.async_engine.dispose()
    
    async def _check_table_existence(self, conn) -> Dict[str, Any]:
        """Check if all required tables exist."""
        required_tables = ['users', 'user_sessions', 'password_reset_tokens', 'email_verification_tokens']
        existing_tables = []
        
        for table in required_tables:
            result = await conn.execute(text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = '{table}'
                )
            """))
            if result.scalar():
                existing_tables.append(table)
        
        return {
            'check_name': 'table_existence',
            'passed': len(existing_tables) == len(required_tables),
            'details': {
                'required_tables': required_tables,
                'existing_tables': existing_tables,
                'missing_tables': list(set(required_tables) - set(existing_tables))
            }
        }
    
    async def _check_data_consistency(self, conn) -> Dict[str, Any]:
        """Check data consistency across tables."""
        issues = []
        
        # Check for users without sessions (might be normal)
        result = await conn.execute(text("""
            SELECT COUNT(*) FROM users u 
            LEFT JOIN user_sessions s ON u.id = s.user_id 
            WHERE s.user_id IS NULL
        """))
        users_without_sessions = result.scalar()
        
        # Check for sessions without users (should be 0)
        result = await conn.execute(text("""
            SELECT COUNT(*) FROM user_sessions s 
            LEFT JOIN users u ON s.user_id = u.id 
            WHERE u.id IS NULL
        """))
        sessions_without_users = result.scalar()
        
        if sessions_without_users > 0:
            issues.append(f"{sessions_without_users} sessions without corresponding users")
        
        return {
            'check_name': 'data_consistency',
            'passed': len(issues) == 0,
            'details': {
                'users_without_sessions': users_without_sessions,
                'sessions_without_users': sessions_without_users,
                'issues': issues
            }
        }
    
    async def _check_foreign_key_constraints(self, conn) -> Dict[str, Any]:
        """Check foreign key constraint integrity."""
        constraint_violations = []
        
        # Check user_sessions -> users
        result = await conn.execute(text("""
            SELECT COUNT(*) FROM user_sessions s 
            WHERE NOT EXISTS (SELECT 1 FROM users u WHERE u.id = s.user_id)
        """))
        session_violations = result.scalar()
        
        if session_violations > 0:
            constraint_violations.append(f"{session_violations} sessions with invalid user_id")
        
        # Check password_reset_tokens -> users
        result = await conn.execute(text("""
            SELECT COUNT(*) FROM password_reset_tokens t 
            WHERE NOT EXISTS (SELECT 1 FROM users u WHERE u.id = t.user_id)
        """))
        reset_token_violations = result.scalar()
        
        if reset_token_violations > 0:
            constraint_violations.append(f"{reset_token_violations} reset tokens with invalid user_id")
        
        # Check email_verification_tokens -> users
        result = await conn.execute(text("""
            SELECT COUNT(*) FROM email_verification_tokens t 
            WHERE NOT EXISTS (SELECT 1 FROM users u WHERE u.id = t.user_id)
        """))
        verification_token_violations = result.scalar()
        
        if verification_token_violations > 0:
            constraint_violations.append(f"{verification_token_violations} verification tokens with invalid user_id")
        
        return {
            'check_name': 'foreign_key_constraints',
            'passed': len(constraint_violations) == 0,
            'details': {
                'violations': constraint_violations,
                'session_violations': session_violations,
                'reset_token_violations': reset_token_violations,
                'verification_token_violations': verification_token_violations
            }
        }
    
    async def _check_data_anomalies(self, conn) -> Dict[str, Any]:
        """Check for data anomalies that might indicate migration issues."""
        anomalies = []
        
        # Check for duplicate emails
        result = await conn.execute(text("""
            SELECT email, COUNT(*) as count 
            FROM users 
            GROUP BY email 
            HAVING COUNT(*) > 1
        """))
        duplicate_emails = result.fetchall()
        
        if duplicate_emails:
            anomalies.append(f"{len(duplicate_emails)} duplicate email addresses found")
        
        # Check for users with null required fields
        result = await conn.execute(text("SELECT COUNT(*) FROM users WHERE email IS NULL OR password_hash IS NULL"))
        users_with_null_required = result.scalar()
        
        if users_with_null_required > 0:
            anomalies.append(f"{users_with_null_required} users with null required fields")
        
        # Check for sessions with invalid expiration dates
        result = await conn.execute(text("""
            SELECT COUNT(*) FROM user_sessions 
            WHERE expires_at < created_at
        """))
        invalid_expiration_sessions = result.scalar()
        
        if invalid_expiration_sessions > 0:
            anomalies.append(f"{invalid_expiration_sessions} sessions with invalid expiration dates")
        
        return {
            'check_name': 'data_anomalies',
            'passed': len(anomalies) == 0,
            'details': {
                'anomalies': anomalies,
                'duplicate_emails': len(duplicate_emails) if duplicate_emails else 0,
                'users_with_null_required': users_with_null_required,
                'invalid_expiration_sessions': invalid_expiration_sessions
            }
        }
    
    def _generate_recommendations(self, checks: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on failed checks."""
        recommendations = []
        
        for check in checks:
            if not check.get('passed', False):
                check_name = check.get('check_name', 'unknown')
                
                if check_name == 'table_existence':
                    missing_tables = check.get('details', {}).get('missing_tables', [])
                    if missing_tables:
                        recommendations.append(f"Create missing tables: {', '.join(missing_tables)}")
                
                elif check_name == 'data_consistency':
                    sessions_without_users = check.get('details', {}).get('sessions_without_users', 0)
                    if sessions_without_users > 0:
                        recommendations.append("Remove orphaned sessions or fix user references")
                
                elif check_name == 'foreign_key_constraints':
                    violations = check.get('details', {}).get('violations', [])
                    if violations:
                        recommendations.append("Fix foreign key constraint violations: " + "; ".join(violations))
                
                elif check_name == 'data_anomalies':
                    anomalies = check.get('details', {}).get('anomalies', [])
                    if anomalies:
                        recommendations.append("Address data anomalies: " + "; ".join(anomalies))
        
        return recommendations