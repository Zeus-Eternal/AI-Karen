#!/usr/bin/env python3
"""
Advanced Migration Manager for AI Karen
Provides version control, rollback, and advanced migration features
"""

import os
import sys
import json
import hashlib
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class MigrationManager:
    """Advanced migration management with version control and rollback support"""
    
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.migrations_path = self.base_path / "migrations"
        self.state_file = self.base_path / "migration_state.json"
        self.load_state()
    
    def load_state(self):
        """Load migration state from file"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                self.state = json.load(f)
        else:
            self.state = {
                "version": "1.0.0",
                "last_migration": None,
                "services": {
                    "postgres": {"version": "0", "migrations": []},
                    "duckdb": {"version": "0", "migrations": []},
                    "elasticsearch": {"version": "0", "migrations": []},
                    "milvus": {"version": "0", "migrations": []}
                }
            }
    
    def save_state(self):
        """Save migration state to file"""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2, default=str)
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file"""
        if not file_path.exists():
            return ""
        
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    
    def get_migration_files(self, service: str) -> List[Tuple[str, Path]]:
        """Get sorted list of migration files for a service"""
        service_path = self.migrations_path / service
        if not service_path.exists():
            return []
        
        files = []
        for file_path in service_path.glob("*"):
            if file_path.is_file() and not file_path.name.startswith('.'):
                files.append((file_path.name, file_path))
        
        return sorted(files, key=lambda x: x[0])
    
    def get_pending_migrations(self, service: str) -> List[Tuple[str, Path]]:
        """Get migrations that haven't been applied yet"""
        all_migrations = self.get_migration_files(service)
        applied_migrations = set(m["name"] for m in self.state["services"][service]["migrations"])
        
        return [(name, path) for name, path in all_migrations if name not in applied_migrations]
    
    def apply_migration(self, service: str, migration_name: str, migration_path: Path) -> bool:
        """Apply a single migration"""
        print(f"Applying {service} migration: {migration_name}")
        
        try:
            if service == "postgres":
                return self._apply_postgres_migration(migration_path)
            elif service == "duckdb":
                return self._apply_duckdb_migration(migration_path)
            elif service == "elasticsearch":
                return self._apply_elasticsearch_migration(migration_path)
            elif service == "milvus":
                return self._apply_milvus_migration(migration_path)
            else:
                print(f"Unknown service: {service}")
                return False
        except Exception as e:
            print(f"Error applying migration {migration_name}: {e}")
            return False
    
    def _apply_postgres_migration(self, migration_path: Path) -> bool:
        """Apply PostgreSQL migration"""
        cmd = [
            "psql",
            "-h", os.getenv("POSTGRES_HOST", "localhost"),
            "-U", os.getenv("POSTGRES_USER", "karen_user"),
            "-d", os.getenv("POSTGRES_DB", "ai_karen"),
            "-f", str(migration_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ PostgreSQL migration applied successfully")
            return True
        else:
            print(f"❌ PostgreSQL migration failed: {result.stderr}")
            return False
    
    def _apply_duckdb_migration(self, migration_path: Path) -> bool:
        """Apply DuckDB migration"""
        duckdb_path = os.getenv("DUCKDB_PATH", "./data/duckdb/kari_duckdb.db")
        
        cmd = ["duckdb", duckdb_path, f".read {migration_path}"]
        
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print(f"✅ DuckDB migration applied successfully")
            return True
        else:
            print(f"❌ DuckDB migration failed: {result.stderr}")
            return False
    
    def _apply_elasticsearch_migration(self, migration_path: Path) -> bool:
        """Apply Elasticsearch migration"""
        es_host = os.getenv("ELASTICSEARCH_HOST", "localhost")
        es_port = os.getenv("ELASTICSEARCH_PORT", "9200")
        
        index_name = migration_path.stem
        
        cmd = [
            "curl", "-s", "-X", "PUT",
            f"http://{es_host}:{es_port}/{index_name}",
            "-H", "Content-Type: application/json",
            "-d", f"@{migration_path}"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and '"acknowledged":true' in result.stdout:
            print(f"✅ Elasticsearch migration applied successfully")
            return True
        else:
            print(f"❌ Elasticsearch migration failed: {result.stdout}")
            return False
    
    def _apply_milvus_migration(self, migration_path: Path) -> bool:
        """Apply Milvus migration"""
        if not migration_path.suffix == '.py':
            print(f"❌ Milvus migration must be a Python file: {migration_path}")
            return False
        
        cmd = ["python3", str(migration_path)]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Milvus migration applied successfully")
            return True
        else:
            print(f"❌ Milvus migration failed: {result.stderr}")
            return False
    
    def record_migration(self, service: str, migration_name: str, migration_path: Path):
        """Record a successful migration in state"""
        migration_record = {
            "name": migration_name,
            "applied_at": datetime.now().isoformat(),
            "checksum": self.calculate_file_hash(migration_path),
            "status": "applied"
        }
        
        self.state["services"][service]["migrations"].append(migration_record)
        self.state["services"][service]["version"] = str(len(self.state["services"][service]["migrations"]))
        self.state["last_migration"] = {
            "service": service,
            "migration": migration_name,
            "applied_at": migration_record["applied_at"]
        }
        
        self.save_state()
    
    def migrate_service(self, service: str) -> bool:
        """Apply all pending migrations for a service"""
        if service not in self.state["services"]:
            print(f"Unknown service: {service}")
            return False
        
        pending = self.get_pending_migrations(service)
        if not pending:
            print(f"No pending migrations for {service}")
            return True
        
        print(f"Found {len(pending)} pending migrations for {service}")
        
        for migration_name, migration_path in pending:
            if self.apply_migration(service, migration_name, migration_path):
                self.record_migration(service, migration_name, migration_path)
                print(f"✅ Recorded migration: {migration_name}")
            else:
                print(f"❌ Failed to apply migration: {migration_name}")
                return False
        
        return True
    
    def migrate_all(self) -> bool:
        """Apply all pending migrations for all services"""
        services = ["postgres", "duckdb", "elasticsearch", "milvus"]
        success = True
        
        for service in services:
            print(f"\n--- Migrating {service.upper()} ---")
            if not self.migrate_service(service):
                success = False
                print(f"❌ Failed to migrate {service}")
            else:
                print(f"✅ {service} migrations completed")
        
        return success
    
    def show_status(self, service: Optional[str] = None):
        """Show migration status"""
        if service:
            services = [service] if service in self.state["services"] else []
        else:
            services = list(self.state["services"].keys())
        
        print("Migration Status")
        print("=" * 50)
        
        for svc in services:
            svc_state = self.state["services"][svc]
            applied_count = len(svc_state["migrations"])
            pending = self.get_pending_migrations(svc)
            pending_count = len(pending)
            
            print(f"\n{svc.upper()}:")
            print(f"  Version: {svc_state['version']}")
            print(f"  Applied: {applied_count}")
            print(f"  Pending: {pending_count}")
            
            if applied_count > 0:
                print("  Last applied:")
                last_migration = svc_state["migrations"][-1]
                print(f"    {last_migration['name']} ({last_migration['applied_at']})")
            
            if pending_count > 0:
                print("  Pending migrations:")
                for name, _ in pending[:3]:  # Show first 3
                    print(f"    - {name}")
                if pending_count > 3:
                    print(f"    ... and {pending_count - 3} more")
    
    def create_migration(self, service: str, name: str) -> bool:
        """Create a new migration file"""
        if service not in self.state["services"]:
            print(f"Unknown service: {service}")
            return False
        
        service_path = self.migrations_path / service
        service_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if service in ["postgres", "duckdb"]:
            filename = f"{timestamp}_{name}.sql"
            template = f"-- {service.upper()} Migration: {name}\n-- Created: {datetime.now()}\n\n-- Add your migration SQL here\n"
        elif service == "elasticsearch":
            filename = f"{timestamp}_{name}.json"
            template = '{\n  "settings": {\n    "number_of_shards": 1,\n    "number_of_replicas": 0\n  },\n  "mappings": {\n    "properties": {\n      "example_field": {\n        "type": "text"\n      }\n    }\n  }\n}'
        elif service == "milvus":
            filename = f"{timestamp}_{name}.py"
            template = f'''#!/usr/bin/env python3
"""
Milvus Migration: {name}
Created: {datetime.now()}
"""

import os
from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility

def main():
    # Connect to Milvus
    host = os.getenv('MILVUS_HOST', 'localhost')
    port = os.getenv('MILVUS_PORT', '19530')
    
    connections.connect(alias="default", host=host, port=port)
    
    # Add your migration code here
    print("Migration {name} executed successfully")

if __name__ == "__main__":
    main()
'''
        
        file_path = service_path / filename
        
        with open(file_path, 'w') as f:
            f.write(template)
        
        if service == "milvus":
            os.chmod(file_path, 0o755)
        
        print(f"✅ Migration created: {file_path}")
        return True
    
    def rollback_service(self, service: str, steps: int = 1) -> bool:
        """Rollback migrations for a service"""
        print(f"⚠️  Rollback functionality is limited and may require manual intervention")
        print(f"Service: {service}, Steps: {steps}")
        
        svc_state = self.state["services"][service]
        if len(svc_state["migrations"]) < steps:
            print(f"❌ Cannot rollback {steps} steps, only {len(svc_state['migrations'])} migrations applied")
            return False
        
        # For now, just remove from state (actual rollback would need service-specific logic)
        for _ in range(steps):
            if svc_state["migrations"]:
                removed = svc_state["migrations"].pop()
                print(f"⚠️  Removed from state: {removed['name']}")
        
        svc_state["version"] = str(len(svc_state["migrations"]))
        self.save_state()
        
        print(f"⚠️  State updated. Manual database cleanup may be required.")
        return True

def main():
    """Main CLI interface"""
    if len(sys.argv) < 2:
        print("Usage: migration-manager.py <command> [args...]")
        print("Commands: migrate, status, create, rollback")
        return
    
    manager = MigrationManager()
    command = sys.argv[1]
    
    if command == "migrate":
        service = sys.argv[2] if len(sys.argv) > 2 else None
        if service:
            success = manager.migrate_service(service)
        else:
            success = manager.migrate_all()
        
        if success:
            print("\n🎉 Migrations completed successfully!")
        else:
            print("\n❌ Migration failed!")
            sys.exit(1)
    
    elif command == "status":
        service = sys.argv[2] if len(sys.argv) > 2 else None
        manager.show_status(service)
    
    elif command == "create":
        if len(sys.argv) < 4:
            print("Usage: migration-manager.py create <service> <name>")
            return
        
        service = sys.argv[2]
        name = sys.argv[3]
        manager.create_migration(service, name)
    
    elif command == "rollback":
        if len(sys.argv) < 3:
            print("Usage: migration-manager.py rollback <service> [steps]")
            return
        
        service = sys.argv[2]
        steps = int(sys.argv[3]) if len(sys.argv) > 3 else 1
        manager.rollback_service(service, steps)
    
    else:
        print(f"Unknown command: {command}")
        print("Available commands: migrate, status, create, rollback")

if __name__ == "__main__":
    main()