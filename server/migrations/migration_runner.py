"""
Migration runner for database schema changes.
Handles running migrations in order and tracking applied migrations.
"""

import logging
import asyncio
import asyncpg
from typing import Dict, Any, List, Optional
from pathlib import Path
import importlib.util
import sys
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)

class MigrationRunner:
    """Handles running database migrations for the extension authentication system."""
    
    def __init__(self, db_config: Dict[str, Any], migrations_dir: Optional[Path] = None):
        self.db_config = db_config
        self.migrations_dir = migrations_dir or Path(__file__).parent
        self.connection: Optional[asyncpg.Connection] = None
    
    async def connect(self):
        """Connect to the database."""
        if not self.connection:
            self.connection = await asyncpg.connect(
                host=self.db_config.get('host', 'localhost'),
                port=self.db_config.get('port', 5432),
                user=self.db_config.get('user', 'postgres'),
                password=self.db_config.get('password', ''),
                database=self.db_config.get('database', 'kari')
            )
    
    async def disconnect(self):
        """Disconnect from the database."""
        if self.connection:
            await self.connection.close()
            self.connection = None
    
    async def ensure_migrations_table(self):
        """Ensure the schema_migrations table exists."""
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id SERIAL PRIMARY KEY,
                migration_id VARCHAR(255) NOT NULL UNIQUE,
                description TEXT,
                applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                checksum VARCHAR(64),
                execution_time_ms INTEGER
            );
        """)
    
    async def get_applied_migrations(self) -> List[str]:
        """Get list of applied migration IDs."""
        rows = await self.connection.fetch("""
            SELECT migration_id FROM schema_migrations 
            ORDER BY applied_at
        """)
        return [row['migration_id'] for row in rows]
    
    def discover_migrations(self) -> List[Path]:
        """Discover migration files in the migrations directory."""
        migration_files = []
        
        for file_path in self.migrations_dir.glob("*.py"):
            if file_path.name.startswith("__"):
                continue
            if file_path.name == "migration_runner.py":
                continue
            migration_files.append(file_path)
        
        # Sort by filename to ensure order
        migration_files.sort(key=lambda x: x.name)
        return migration_files
    
    def load_migration_module(self, file_path: Path):
        """Load a migration module from file."""
        spec = importlib.util.spec_from_file_location(
            f"migration_{file_path.stem}", 
            file_path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    
    def calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate checksum of migration file."""
        with open(file_path, 'rb') as f:
            content = f.read()
        return hashlib.sha256(content).hexdigest()[:16]
    
    async def run_migrations(self, target_migration: Optional[str] = None) -> Dict[str, Any]:
        """Run pending migrations up to target migration."""
        try:
            await self.connect()
            await self.ensure_migrations_table()
            
            applied_migrations = await self.get_applied_migrations()
            migration_files = self.discover_migrations()
            
            results = {
                'applied': [],
                'skipped': [],
                'errors': [],
                'total_time_ms': 0
            }
            
            for file_path in migration_files:
                migration_id = file_path.stem
                
                # Skip if already applied
                if migration_id in applied_migrations:
                    results['skipped'].append(migration_id)
                    continue
                
                # Stop if we've reached target migration
                if target_migration and migration_id == target_migration:
                    break
                
                try:
                    # Load and run migration
                    start_time = datetime.utcnow()
                    
                    module = self.load_migration_module(file_path)
                    
                    # Look for migration class or run_migration function
                    if hasattr(module, 'run_migration'):
                        success = await module.run_migration(self.db_config, "up")
                    else:
                        # Look for migration class
                        migration_class = None
                        for attr_name in dir(module):
                            attr = getattr(module, attr_name)
                            if (isinstance(attr, type) and 
                                hasattr(attr, 'up') and 
                                attr_name.endswith('Migration')):
                                migration_class = attr
                                break
                        
                        if migration_class:
                            migration = migration_class(self.db_config)
                            success = await migration.up(self.connection)
                        else:
                            raise ValueError(f"No migration class or run_migration function found in {file_path}")
                    
                    end_time = datetime.utcnow()
                    execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
                    
                    if success:
                        # Record migration
                        checksum = self.calculate_file_checksum(file_path)
                        await self.connection.execute("""
                            INSERT INTO schema_migrations 
                            (migration_id, description, checksum, execution_time_ms)
                            VALUES ($1, $2, $3, $4)
                            ON CONFLICT (migration_id) DO UPDATE SET
                                checksum = EXCLUDED.checksum,
                                execution_time_ms = EXCLUDED.execution_time_ms
                        """, migration_id, f"Migration from {file_path.name}", 
                             checksum, execution_time_ms)
                        
                        results['applied'].append({
                            'migration_id': migration_id,
                            'execution_time_ms': execution_time_ms
                        })
                        results['total_time_ms'] += execution_time_ms
                        
                        logger.info(f"Applied migration {migration_id} in {execution_time_ms}ms")
                    else:
                        results['errors'].append({
                            'migration_id': migration_id,
                            'error': 'Migration returned False'
                        })
                
                except Exception as e:
                    error_msg = f"Failed to apply migration {migration_id}: {e}"
                    logger.error(error_msg)
                    results['errors'].append({
                        'migration_id': migration_id,
                        'error': str(e)
                    })
                    # Stop on error
                    break
            
            return results
            
        finally:
            await self.disconnect()
    
    async def rollback_migration(self, migration_id: str) -> bool:
        """Rollback a specific migration."""
        try:
            await self.connect()
            
            # Find migration file
            migration_files = self.discover_migrations()
            target_file = None
            
            for file_path in migration_files:
                if file_path.stem == migration_id:
                    target_file = file_path
                    break
            
            if not target_file:
                raise ValueError(f"Migration {migration_id} not found")
            
            # Load and run rollback
            module = self.load_migration_module(target_file)
            
            if hasattr(module, 'run_migration'):
                success = await module.run_migration(self.db_config, "down")
            else:
                # Look for migration class
                migration_class = None
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        hasattr(attr, 'down') and 
                        attr_name.endswith('Migration')):
                        migration_class = attr
                        break
                
                if migration_class:
                    migration = migration_class(self.db_config)
                    success = await migration.down(self.connection)
                else:
                    raise ValueError(f"No migration class found in {target_file}")
            
            if success:
                # Remove migration record
                await self.connection.execute("""
                    DELETE FROM schema_migrations 
                    WHERE migration_id = $1
                """, migration_id)
                
                logger.info(f"Rolled back migration {migration_id}")
                return True
            else:
                logger.error(f"Failed to rollback migration {migration_id}")
                return False
                
        finally:
            await self.disconnect()
    
    async def get_migration_status(self) -> Dict[str, Any]:
        """Get status of all migrations."""
        try:
            await self.connect()
            await self.ensure_migrations_table()
            
            applied_migrations = await self.get_applied_migrations()
            migration_files = self.discover_migrations()
            
            status = {
                'total_migrations': len(migration_files),
                'applied_count': len(applied_migrations),
                'pending_count': 0,
                'migrations': []
            }
            
            for file_path in migration_files:
                migration_id = file_path.stem
                is_applied = migration_id in applied_migrations
                
                if not is_applied:
                    status['pending_count'] += 1
                
                # Get migration details if applied
                details = None
                if is_applied:
                    row = await self.connection.fetchrow("""
                        SELECT applied_at, execution_time_ms, checksum
                        FROM schema_migrations 
                        WHERE migration_id = $1
                    """, migration_id)
                    if row:
                        details = {
                            'applied_at': row['applied_at'].isoformat(),
                            'execution_time_ms': row['execution_time_ms'],
                            'checksum': row['checksum']
                        }
                
                status['migrations'].append({
                    'migration_id': migration_id,
                    'file_path': str(file_path),
                    'is_applied': is_applied,
                    'details': details
                })
            
            return status
            
        finally:
            await self.disconnect()


async def main():
    """CLI interface for migration runner."""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description='Database Migration Runner')
    parser.add_argument('command', choices=['migrate', 'rollback', 'status'], 
                       help='Migration command')
    parser.add_argument('--target', help='Target migration ID')
    parser.add_argument('--config', help='Database config file path')
    
    args = parser.parse_args()
    
    # Load database configuration
    if args.config:
        config_path = Path(args.config)
    else:
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
    
    runner = MigrationRunner(db_config)
    
    try:
        if args.command == 'migrate':
            results = await runner.run_migrations(args.target)
            print(f"Applied {len(results['applied'])} migrations")
            if results['errors']:
                print(f"Errors: {len(results['errors'])}")
                for error in results['errors']:
                    print(f"  - {error['migration_id']}: {error['error']}")
        
        elif args.command == 'rollback':
            if not args.target:
                print("Target migration ID required for rollback")
                sys.exit(1)
            
            success = await runner.rollback_migration(args.target)
            if success:
                print(f"Rolled back migration {args.target}")
            else:
                print(f"Failed to rollback migration {args.target}")
                sys.exit(1)
        
        elif args.command == 'status':
            status = await runner.get_migration_status()
            print(f"Total migrations: {status['total_migrations']}")
            print(f"Applied: {status['applied_count']}")
            print(f"Pending: {status['pending_count']}")
            print("\nMigrations:")
            for migration in status['migrations']:
                status_str = "✓" if migration['is_applied'] else "○"
                print(f"  {status_str} {migration['migration_id']}")
                if migration['details']:
                    print(f"    Applied: {migration['details']['applied_at']}")
                    print(f"    Time: {migration['details']['execution_time_ms']}ms")
    
    except Exception as e:
        logger.error(f"Migration command failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())