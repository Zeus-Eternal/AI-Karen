"""
Extension Marketplace Database Utilities

This module provides database initialization and management utilities
for the extension marketplace.
"""

import logging
from pathlib import Path
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from .models import Base

logger = logging.getLogger(__name__)


class MarketplaceDatabaseManager:
    """Manages marketplace database operations."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_tables(self) -> bool:
        """Create all marketplace tables."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Marketplace tables created successfully")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Failed to create marketplace tables: {e}")
            return False
    
    def drop_tables(self) -> bool:
        """Drop all marketplace tables."""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("Marketplace tables dropped successfully")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Failed to drop marketplace tables: {e}")
            return False
    
    def run_migration(self, migration_file: Path) -> bool:
        """Run a SQL migration file."""
        try:
            with open(migration_file, 'r') as f:
                migration_sql = f.read()
            
            with self.engine.connect() as conn:
                # Split by semicolon and execute each statement
                statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
                
                for statement in statements:
                    if statement.upper().startswith(('CREATE', 'ALTER', 'INSERT', 'UPDATE', 'DELETE', 'DROP')):
                        conn.execute(text(statement))
                
                conn.commit()
            
            logger.info(f"Migration {migration_file.name} executed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to run migration {migration_file.name}: {e}")
            return False
    
    def initialize_marketplace(self) -> bool:
        """Initialize the marketplace database with schema and sample data."""
        try:
            # Run the initial migration
            migration_file = Path(__file__).parent / "migrations" / "001_create_marketplace_tables.sql"
            
            if migration_file.exists():
                return self.run_migration(migration_file)
            else:
                # Fallback to creating tables directly
                return self.create_tables()
                
        except Exception as e:
            logger.error(f"Failed to initialize marketplace database: {e}")
            return False
    
    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()
    
    def health_check(self) -> bool:
        """Check if the database is accessible."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def get_table_counts(self) -> dict:
        """Get row counts for all marketplace tables."""
        counts = {}
        
        try:
            with self.get_session() as session:
                from .models import ExtensionListing, ExtensionVersion, ExtensionInstallation
                
                counts['extension_listings'] = session.query(ExtensionListing).count()
                counts['extension_versions'] = session.query(ExtensionVersion).count()
                counts['extension_installations'] = session.query(ExtensionInstallation).count()
                
        except Exception as e:
            logger.error(f"Failed to get table counts: {e}")
            
        return counts


def init_marketplace_database(database_url: str) -> Optional[MarketplaceDatabaseManager]:
    """Initialize the marketplace database."""
    try:
        db_manager = MarketplaceDatabaseManager(database_url)
        
        if db_manager.health_check():
            if db_manager.initialize_marketplace():
                logger.info("Marketplace database initialized successfully")
                return db_manager
            else:
                logger.error("Failed to initialize marketplace database")
        else:
            logger.error("Database health check failed")
            
    except Exception as e:
        logger.error(f"Failed to initialize marketplace database: {e}")
    
    return None


def get_marketplace_session(database_url: str) -> Optional[Session]:
    """Get a marketplace database session."""
    try:
        db_manager = MarketplaceDatabaseManager(database_url)
        return db_manager.get_session()
    except Exception as e:
        logger.error(f"Failed to get marketplace session: {e}")
        return None