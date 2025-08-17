"""
PostgreSQL authentication schema definition and creation utilities.

This module defines the PostgreSQL schema for authentication data and provides
utilities for creating tables with proper indexes and foreign key relationships.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    """PostgreSQL user table with consistent UUID generation."""
    
    __tablename__ = 'auth_users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    roles = Column(JSONB, default=list)
    preferences = Column(JSONB, default=dict)
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True, index=True)
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(255))
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True))
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True))
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_auth_users_tenant_email', 'tenant_id', 'email'),
        Index('idx_auth_users_active', 'is_active'),
        Index('idx_auth_users_locked', 'locked_until'),
    )


class UserSession(Base):
    """PostgreSQL session table with proper foreign key relationships."""
    
    __tablename__ = 'auth_sessions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('auth_users.id', ondelete='CASCADE'), nullable=False, index=True)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    access_token = Column(Text)
    refresh_token = Column(Text)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    last_accessed = Column(DateTime(timezone=True), default=func.now())
    ip_address = Column(INET)
    user_agent = Column(Text)
    device_fingerprint = Column(String(255))
    geolocation = Column(JSONB)
    risk_score = Column(Float, default=0.0)
    security_flags = Column(JSONB, default=list)
    is_active = Column(Boolean, default=True, index=True)
    invalidated_at = Column(DateTime(timezone=True))
    invalidation_reason = Column(String(255))
    
    # Relationship
    user = relationship("User", back_populates="sessions")
    
    __table_args__ = (
        Index('idx_auth_sessions_user_active', 'user_id', 'is_active'),
        Index('idx_auth_sessions_last_accessed', 'last_accessed'),
        Index('idx_auth_sessions_expires', 'expires_at'),
        Index('idx_auth_sessions_token', 'session_token'),
    )


class PasswordResetToken(Base):
    """PostgreSQL password reset token table."""
    
    __tablename__ = 'password_reset_tokens'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('auth_users.id', ondelete='CASCADE'), nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=func.now())
    ip_address = Column(INET)
    user_agent = Column(Text)
    
    # Relationship
    user = relationship("User", back_populates="password_reset_tokens")
    
    __table_args__ = (
        Index('idx_reset_tokens_token', 'token'),
        Index('idx_reset_tokens_user_id', 'user_id'),
        Index('idx_reset_tokens_expires', 'expires_at'),
        Index('idx_reset_tokens_used', 'used'),
    )


class AuthProvider(Base):
    """PostgreSQL auth provider table for external authentication."""
    
    __tablename__ = 'auth_providers'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_id = Column(String(255), unique=True, nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), index=True)
    provider_type = Column(String(50), nullable=False)  # oauth, saml, oidc
    config = Column(JSONB, nullable=False)
    provider_metadata = Column(JSONB, default=dict)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # Relationships
    user_identities = relationship("UserIdentity", back_populates="provider", cascade="all, delete-orphan")


class UserIdentity(Base):
    """PostgreSQL user identity table for external provider mappings."""
    
    __tablename__ = 'user_identities'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('auth_users.id', ondelete='CASCADE'), nullable=False, index=True)
    provider_id = Column(UUID(as_uuid=True), ForeignKey('auth_providers.id', ondelete='CASCADE'), nullable=False, index=True)
    provider_user_id = Column(String(255), nullable=False)
    identity_metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=func.now())
    
    # Relationships
    user = relationship("User")
    provider = relationship("AuthProvider", back_populates="user_identities")
    
    __table_args__ = (
        Index('idx_user_identities_user', 'user_id'),
        Index('idx_user_identities_provider', 'provider_id'),
        Index('idx_user_identities_provider_user', 'provider_id', 'provider_user_id'),
    )


class PostgreSQLAuthSchema:
    """
    PostgreSQL authentication schema manager.
    
    Handles creation, validation, and management of PostgreSQL authentication
    tables with proper indexes and foreign key relationships.
    """
    
    def __init__(self, database_url: str):
        """
        Initialize schema manager.
        
        Args:
            database_url: PostgreSQL connection URL
        """
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.logger = logging.getLogger(__name__)
    
    def create_schema(self, drop_existing: bool = False) -> bool:
        """
        Create PostgreSQL authentication schema.
        
        Args:
            drop_existing: Whether to drop existing tables first
            
        Returns:
            True if schema created successfully
            
        Raises:
            Exception: If schema creation fails
        """
        try:
            if drop_existing:
                self.logger.warning("Dropping existing authentication tables")
                Base.metadata.drop_all(bind=self.engine)
            
            self.logger.info("Creating PostgreSQL authentication schema")
            Base.metadata.create_all(bind=self.engine)
            
            # Verify schema creation
            if self.validate_schema():
                self.logger.info("PostgreSQL authentication schema created successfully")
                return True
            else:
                raise Exception("Schema validation failed after creation")
                
        except Exception as e:
            self.logger.error(f"Failed to create PostgreSQL schema: {e}")
            raise
    
    def validate_schema(self) -> bool:
        """
        Validate that all required tables and indexes exist.
        
        Returns:
            True if schema is valid
        """
        try:
            required_tables = [
                'auth_users',
                'auth_sessions', 
                'password_reset_tokens',
                'auth_providers',
                'user_identities'
            ]
            
            # Check if all tables exist
            from sqlalchemy import inspect
            inspector = inspect(self.engine)
            existing_tables = inspector.get_table_names()
            
            for table in required_tables:
                if table not in existing_tables:
                    self.logger.error(f"Required table {table} not found")
                    return False
            
            # Check foreign key constraints
            sessions_fks = inspector.get_foreign_keys('auth_sessions')
            if not any(fk['referred_table'] == 'auth_users' for fk in sessions_fks):
                self.logger.error("Missing foreign key constraint from auth_sessions to auth_users")
                return False
            
            reset_tokens_fks = inspector.get_foreign_keys('password_reset_tokens')
            if not any(fk['referred_table'] == 'auth_users' for fk in reset_tokens_fks):
                self.logger.error("Missing foreign key constraint from password_reset_tokens to auth_users")
                return False
            
            self.logger.info("PostgreSQL authentication schema validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Schema validation failed: {e}")
            return False
    
    def get_table_info(self) -> Dict[str, Dict]:
        """
        Get information about all authentication tables.
        
        Returns:
            Dictionary with table information
        """
        try:
            from sqlalchemy import inspect
            inspector = inspect(self.engine)
            
            table_info = {}
            for table_name in ['auth_users', 'auth_sessions', 'password_reset_tokens', 'auth_providers', 'user_identities']:
                if table_name in inspector.get_table_names():
                    columns = inspector.get_columns(table_name)
                    indexes = inspector.get_indexes(table_name)
                    foreign_keys = inspector.get_foreign_keys(table_name)
                    
                    table_info[table_name] = {
                        'columns': [col['name'] for col in columns],
                        'indexes': [idx['name'] for idx in indexes],
                        'foreign_keys': [(fk['constrained_columns'], fk['referred_table'], fk['referred_columns']) for fk in foreign_keys]
                    }
            
            return table_info
            
        except Exception as e:
            self.logger.error(f"Failed to get table info: {e}")
            return {}
    
    def create_indexes(self) -> bool:
        """
        Create additional performance indexes for authentication operations.
        
        Returns:
            True if indexes created successfully
        """
        try:
            with self.engine.connect() as conn:
                # Additional performance indexes
                performance_indexes = [
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_auth_users_email_active ON auth_users(email) WHERE is_active = true",
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_auth_sessions_user_expires ON auth_sessions(user_id, expires_at) WHERE is_active = true",
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_auth_sessions_token_active ON auth_sessions(session_token) WHERE is_active = true",
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reset_tokens_active ON password_reset_tokens(token, expires_at) WHERE used = false",
                ]
                
                for index_sql in performance_indexes:
                    try:
                        conn.execute(index_sql)
                        self.logger.info(f"Created index: {index_sql.split('idx_')[1].split(' ')[0]}")
                    except Exception as e:
                        # Index might already exist, log but continue
                        self.logger.warning(f"Index creation warning: {e}")
                
                conn.commit()
            
            self.logger.info("Performance indexes created successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create performance indexes: {e}")
            return False
    
    def get_schema_ddl(self) -> str:
        """
        Generate DDL statements for the authentication schema.
        
        Returns:
            DDL statements as string
        """
        try:
            from sqlalchemy.schema import CreateTable
            
            ddl_statements = []
            
            # Generate CREATE TABLE statements
            for table in Base.metadata.tables.values():
                create_table = CreateTable(table)
                ddl_statements.append(str(create_table.compile(self.engine)))
            
            return "\n\n".join(ddl_statements)
            
        except Exception as e:
            self.logger.error(f"Failed to generate schema DDL: {e}")
            return ""
    
    def cleanup_expired_tokens(self) -> int:
        """
        Clean up expired password reset tokens.
        
        Returns:
            Number of tokens cleaned up
        """
        try:
            with self.SessionLocal() as session:
                expired_count = session.query(PasswordResetToken).filter(
                    PasswordResetToken.expires_at < datetime.utcnow()
                ).delete()
                
                session.commit()
                
                if expired_count > 0:
                    self.logger.info(f"Cleaned up {expired_count} expired password reset tokens")
                
                return expired_count
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup expired tokens: {e}")
            return 0
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        try:
            with self.SessionLocal() as session:
                expired_count = session.query(UserSession).filter(
                    UserSession.expires_at < datetime.utcnow(),
                    UserSession.is_active == True
                ).update({
                    'is_active': False,
                    'invalidated_at': datetime.utcnow(),
                    'invalidation_reason': 'expired'
                })
                
                session.commit()
                
                if expired_count > 0:
                    self.logger.info(f"Cleaned up {expired_count} expired sessions")
                
                return expired_count
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0