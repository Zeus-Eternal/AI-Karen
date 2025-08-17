"""
Backup and rollback manager for database migration operations.

This module provides utilities for creating backups of SQLite databases
and PostgreSQL data before migration, and rolling back if needed.
"""

import json
import logging
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


class BackupManager:
    """
    Manages backup and rollback operations for database migration.
    
    Provides functionality to backup SQLite databases, create PostgreSQL
    snapshots, and restore data if migration fails.
    """
    
    def __init__(self, backup_dir: str = "migration_backups"):
        """
        Initialize backup manager.
        
        Args:
            backup_dir: Directory to store backup files
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self.backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def backup_sqlite_databases(self, sqlite_paths: List[str]) -> Dict[str, str]:
        """
        Create backups of SQLite database files.
        
        Args:
            sqlite_paths: List of SQLite database file paths
            
        Returns:
            Dictionary mapping original paths to backup paths
            
        Raises:
            Exception: If backup creation fails
        """
        backup_mapping = {}
        
        try:
            for sqlite_path in sqlite_paths:
                source_path = Path(sqlite_path)
                if not source_path.exists():
                    self.logger.warning(f"SQLite database not found: {sqlite_path}")
                    continue
                
                # Create backup filename with timestamp
                backup_filename = f"{source_path.stem}_{self.backup_timestamp}{source_path.suffix}"
                backup_path = self.backup_dir / backup_filename
                
                # Copy SQLite file
                shutil.copy2(source_path, backup_path)
                backup_mapping[sqlite_path] = str(backup_path)
                
                self.logger.info(f"Backed up SQLite database: {sqlite_path} -> {backup_path}")
                
                # Also create a SQL dump for additional safety
                self._create_sqlite_dump(sqlite_path, backup_path.with_suffix('.sql'))
            
            # Create backup manifest
            manifest_path = self.backup_dir / f"backup_manifest_{self.backup_timestamp}.json"
            manifest = {
                'timestamp': self.backup_timestamp,
                'sqlite_backups': backup_mapping,
                'created_at': datetime.now().isoformat()
            }
            
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            self.logger.info(f"Created backup manifest: {manifest_path}")
            return backup_mapping
            
        except Exception as e:
            self.logger.error(f"Failed to backup SQLite databases: {e}")
            raise
    
    def _create_sqlite_dump(self, sqlite_path: str, dump_path: Path) -> None:
        """
        Create SQL dump of SQLite database.
        
        Args:
            sqlite_path: Path to SQLite database
            dump_path: Path for SQL dump file
        """
        try:
            conn = sqlite3.connect(sqlite_path)
            
            with open(dump_path, 'w') as f:
                for line in conn.iterdump():
                    f.write(f"{line}\n")
            
            conn.close()
            self.logger.info(f"Created SQLite dump: {dump_path}")
            
        except Exception as e:
            self.logger.warning(f"Failed to create SQLite dump for {sqlite_path}: {e}")
    
    def create_postgres_snapshot(self, database_url: str, snapshot_name: Optional[str] = None) -> str:
        """
        Create PostgreSQL database snapshot before migration.
        
        Args:
            database_url: PostgreSQL connection URL
            snapshot_name: Optional custom snapshot name
            
        Returns:
            Snapshot identifier
            
        Raises:
            Exception: If snapshot creation fails
        """
        if not snapshot_name:
            snapshot_name = f"auth_migration_snapshot_{self.backup_timestamp}"
        
        try:
            engine = create_engine(database_url)
            
            # Export authentication data to JSON files
            auth_data = self._export_postgres_auth_data(engine)
            
            # Save to backup directory
            snapshot_dir = self.backup_dir / snapshot_name
            snapshot_dir.mkdir(exist_ok=True)
            
            for table_name, data in auth_data.items():
                json_path = snapshot_dir / f"{table_name}.json"
                with open(json_path, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            
            # Create snapshot manifest
            manifest = {
                'snapshot_name': snapshot_name,
                'timestamp': self.backup_timestamp,
                'database_url': database_url.split('@')[1] if '@' in database_url else 'redacted',
                'tables': list(auth_data.keys()),
                'created_at': datetime.now().isoformat()
            }
            
            manifest_path = snapshot_dir / 'snapshot_manifest.json'
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            self.logger.info(f"Created PostgreSQL snapshot: {snapshot_name}")
            return snapshot_name
            
        except Exception as e:
            self.logger.error(f"Failed to create PostgreSQL snapshot: {e}")
            raise
    
    def _export_postgres_auth_data(self, engine) -> Dict[str, List[Dict]]:
        """
        Export existing PostgreSQL authentication data.
        
        Args:
            engine: SQLAlchemy engine
            
        Returns:
            Dictionary with table data
        """
        auth_tables = [
            'auth_users',
            'auth_sessions', 
            'password_reset_tokens',
            'auth_providers',
            'user_identities'
        ]
        
        exported_data = {}
        
        with engine.connect() as conn:
            for table_name in auth_tables:
                try:
                    result = conn.execute(text(f"SELECT * FROM {table_name}"))
                    rows = result.fetchall()
                    columns = result.keys()
                    
                    table_data = []
                    for row in rows:
                        row_dict = dict(zip(columns, row))
                        table_data.append(row_dict)
                    
                    exported_data[table_name] = table_data
                    self.logger.info(f"Exported {len(table_data)} rows from {table_name}")
                    
                except Exception as e:
                    # Table might not exist yet
                    self.logger.info(f"Table {table_name} not found or empty: {e}")
                    exported_data[table_name] = []
        
        return exported_data
    
    def restore_sqlite_databases(self, backup_mapping: Dict[str, str]) -> bool:
        """
        Restore SQLite databases from backups.
        
        Args:
            backup_mapping: Dictionary mapping original paths to backup paths
            
        Returns:
            True if restoration successful
        """
        try:
            for original_path, backup_path in backup_mapping.items():
                backup_file = Path(backup_path)
                if not backup_file.exists():
                    self.logger.error(f"Backup file not found: {backup_path}")
                    return False
                
                # Restore backup
                shutil.copy2(backup_file, original_path)
                self.logger.info(f"Restored SQLite database: {backup_path} -> {original_path}")
            
            self.logger.info("SQLite database restoration completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to restore SQLite databases: {e}")
            return False
    
    def restore_postgres_snapshot(self, database_url: str, snapshot_name: str) -> bool:
        """
        Restore PostgreSQL data from snapshot.
        
        Args:
            database_url: PostgreSQL connection URL
            snapshot_name: Snapshot identifier
            
        Returns:
            True if restoration successful
        """
        try:
            snapshot_dir = self.backup_dir / snapshot_name
            if not snapshot_dir.exists():
                self.logger.error(f"Snapshot directory not found: {snapshot_dir}")
                return False
            
            # Load snapshot manifest
            manifest_path = snapshot_dir / 'snapshot_manifest.json'
            if not manifest_path.exists():
                self.logger.error(f"Snapshot manifest not found: {manifest_path}")
                return False
            
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            engine = create_engine(database_url)
            
            # Restore data for each table
            for table_name in manifest['tables']:
                json_path = snapshot_dir / f"{table_name}.json"
                if json_path.exists():
                    with open(json_path, 'r') as f:
                        table_data = json.load(f)
                    
                    if table_data:
                        self._restore_table_data(engine, table_name, table_data)
            
            self.logger.info(f"PostgreSQL snapshot restoration completed: {snapshot_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to restore PostgreSQL snapshot: {e}")
            return False
    
    def _restore_table_data(self, engine, table_name: str, table_data: List[Dict]) -> None:
        """
        Restore data to a specific table.
        
        Args:
            engine: SQLAlchemy engine
            table_name: Name of table to restore
            table_data: List of row dictionaries
        """
        try:
            with engine.connect() as conn:
                # Clear existing data
                conn.execute(text(f"DELETE FROM {table_name}"))
                
                # Insert restored data
                if table_data:
                    columns = list(table_data[0].keys())
                    placeholders = ', '.join([f":{col}" for col in columns])
                    insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                    
                    conn.execute(text(insert_sql), table_data)
                
                conn.commit()
                self.logger.info(f"Restored {len(table_data)} rows to {table_name}")
                
        except Exception as e:
            self.logger.error(f"Failed to restore table {table_name}: {e}")
            raise
    
    def list_backups(self) -> List[Dict]:
        """
        List available backups.
        
        Returns:
            List of backup information dictionaries
        """
        backups = []
        
        try:
            for manifest_file in self.backup_dir.glob("backup_manifest_*.json"):
                with open(manifest_file, 'r') as f:
                    manifest = json.load(f)
                    backups.append(manifest)
            
            # Sort by timestamp
            backups.sort(key=lambda x: x['timestamp'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Failed to list backups: {e}")
        
        return backups
    
    def list_snapshots(self) -> List[Dict]:
        """
        List available PostgreSQL snapshots.
        
        Returns:
            List of snapshot information dictionaries
        """
        snapshots = []
        
        try:
            for snapshot_dir in self.backup_dir.iterdir():
                if snapshot_dir.is_dir():
                    manifest_path = snapshot_dir / 'snapshot_manifest.json'
                    if manifest_path.exists():
                        with open(manifest_path, 'r') as f:
                            manifest = json.load(f)
                            snapshots.append(manifest)
            
            # Sort by timestamp
            snapshots.sort(key=lambda x: x['timestamp'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Failed to list snapshots: {e}")
        
        return snapshots
    
    def cleanup_old_backups(self, keep_count: int = 5) -> int:
        """
        Clean up old backup files, keeping only the most recent ones.
        
        Args:
            keep_count: Number of recent backups to keep
            
        Returns:
            Number of backups cleaned up
        """
        try:
            backups = self.list_backups()
            snapshots = self.list_snapshots()
            
            cleaned_count = 0
            
            # Clean up old backup manifests and files
            if len(backups) > keep_count:
                old_backups = backups[keep_count:]
                for backup in old_backups:
                    timestamp = backup['timestamp']
                    
                    # Remove manifest file
                    manifest_file = self.backup_dir / f"backup_manifest_{timestamp}.json"
                    if manifest_file.exists():
                        manifest_file.unlink()
                        cleaned_count += 1
                    
                    # Remove backup files
                    for backup_path in backup.get('sqlite_backups', {}).values():
                        backup_file = Path(backup_path)
                        if backup_file.exists():
                            backup_file.unlink()
                            cleaned_count += 1
                        
                        # Remove SQL dump
                        dump_file = backup_file.with_suffix('.sql')
                        if dump_file.exists():
                            dump_file.unlink()
                            cleaned_count += 1
            
            # Clean up old snapshots
            if len(snapshots) > keep_count:
                old_snapshots = snapshots[keep_count:]
                for snapshot in old_snapshots:
                    snapshot_name = snapshot['snapshot_name']
                    snapshot_dir = self.backup_dir / snapshot_name
                    
                    if snapshot_dir.exists():
                        shutil.rmtree(snapshot_dir)
                        cleaned_count += 1
            
            if cleaned_count > 0:
                self.logger.info(f"Cleaned up {cleaned_count} old backup files")
            
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old backups: {e}")
            return 0
    
    def verify_backup_integrity(self, backup_mapping: Dict[str, str]) -> bool:
        """
        Verify integrity of backup files.
        
        Args:
            backup_mapping: Dictionary mapping original paths to backup paths
            
        Returns:
            True if all backups are valid
        """
        try:
            for original_path, backup_path in backup_mapping.items():
                backup_file = Path(backup_path)
                
                if not backup_file.exists():
                    self.logger.error(f"Backup file missing: {backup_path}")
                    return False
                
                # Verify SQLite backup can be opened
                try:
                    conn = sqlite3.connect(str(backup_file))
                    conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    conn.close()
                except Exception as e:
                    self.logger.error(f"Backup file corrupted: {backup_path} - {e}")
                    return False
            
            self.logger.info("Backup integrity verification passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Backup integrity verification failed: {e}")
            return False