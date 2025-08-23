"""
Database Connector - Database schema knowledge ingestion

This connector handles database schema introspection for read-only
metadata extraction, creating knowledge documents from table schemas,
relationships, and database structure.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, AsyncGenerator, Set
import json

from .base_connector import BaseConnector, ConnectorType, ChangeDetection, ChangeType

try:
    from llama_index.core import Document
except ImportError:
    Document = None

try:
    import sqlalchemy
    from sqlalchemy import create_engine, MetaData, inspect
    from sqlalchemy.engine import Engine
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    sqlalchemy = None
    MetaData = None
    Engine = None


class DatabaseConnector(BaseConnector):
    """
    Connector for ingesting knowledge from database schemas.
    Performs read-only introspection to extract table structures,
    relationships, and metadata for knowledge indexing.
    """
    
    def __init__(self, connector_id: str, config: Dict[str, Any]):
        super().__init__(connector_id, ConnectorType.DATABASE, config)
        
        # Database configuration
        self.connection_string = config.get("connection_string")
        self.database_type = config.get("database_type", "postgresql")
        self.schema_names = config.get("schema_names", ["public"])
        self.include_tables = config.get("include_tables", [])
        self.exclude_tables = config.get("exclude_tables", [])
        
        # Introspection configuration
        self.include_views = config.get("include_views", True)
        self.include_indexes = config.get("include_indexes", True)
        self.include_constraints = config.get("include_constraints", True)
        self.include_relationships = config.get("include_relationships", True)
        self.include_sample_data = config.get("include_sample_data", False)
        self.sample_data_limit = config.get("sample_data_limit", 5)
        
        # Connection management
        self.engine: Optional[Engine] = None
        self.metadata: Optional[MetaData] = None
        self.inspector = None
        
        # Schema tracking
        self.schema_checksums: Dict[str, str] = {}
        self.last_schema_scan: Optional[datetime] = None
    
    async def scan_sources(self) -> AsyncGenerator[Document, None]:
        """Scan database schemas and yield documents."""
        if not SQLALCHEMY_AVAILABLE:
            self.logger.error("SQLAlchemy not available - database connector disabled")
            return
        
        try:
            # Initialize database connection
            await self._initialize_connection()
            
            if not self.engine or not self.inspector:
                self.logger.error("Failed to initialize database connection")
                return
            
            # Process each schema
            for schema_name in self.schema_names:
                async for document in self._scan_schema(schema_name):
                    yield document
                    await asyncio.sleep(0.001)  # Yield control
        
        except Exception as e:
            self.logger.error(f"Error scanning database sources: {e}")
        finally:
            await self._cleanup_connection()
    
    async def _initialize_connection(self):
        """Initialize database connection and inspector."""
        try:
            if not self.connection_string:
                raise ValueError("Connection string is required")
            
            # Create engine with read-only configuration
            self.engine = create_engine(
                self.connection_string,
                echo=False,
                pool_pre_ping=True,
                connect_args={"options": "-c default_transaction_isolation=serializable"}
            )
            
            # Create inspector for schema introspection
            self.inspector = inspect(self.engine)
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(sqlalchemy.text("SELECT 1"))
            
            self.logger.info("Database connection initialized successfully")
        
        except Exception as e:
            self.logger.error(f"Failed to initialize database connection: {e}")
            raise
    
    async def _cleanup_connection(self):
        """Clean up database connection."""
        try:
            if self.engine:
                self.engine.dispose()
                self.engine = None
                self.inspector = None
                self.logger.info("Database connection cleaned up")
        except Exception as e:
            self.logger.error(f"Error cleaning up database connection: {e}")
    
    async def _scan_schema(self, schema_name: str) -> AsyncGenerator[Document, None]:
        """Scan a specific database schema."""
        try:
            # Get tables in schema
            table_names = self.inspector.get_table_names(schema=schema_name)
            
            # Filter tables
            filtered_tables = self._filter_tables(table_names)
            
            # Process each table
            for table_name in filtered_tables:
                document = await self._process_table(schema_name, table_name)
                if document:
                    yield document
            
            # Process views if enabled
            if self.include_views:
                view_names = self.inspector.get_view_names(schema=schema_name)
                filtered_views = self._filter_tables(view_names)  # Use same filter logic
                
                for view_name in filtered_views:
                    document = await self._process_view(schema_name, view_name)
                    if document:
                        yield document
            
            # Create schema overview document
            schema_doc = await self._create_schema_overview(schema_name, filtered_tables)
            if schema_doc:
                yield schema_doc
        
        except Exception as e:
            self.logger.error(f"Error scanning schema {schema_name}: {e}")
    
    def _filter_tables(self, table_names: List[str]) -> List[str]:
        """Filter table names based on include/exclude patterns."""
        filtered = []
        
        for table_name in table_names:
            # Check exclude list
            if self.exclude_tables and table_name in self.exclude_tables:
                continue
            
            # Check include list (if specified)
            if self.include_tables and table_name not in self.include_tables:
                continue
            
            filtered.append(table_name)
        
        return filtered
    
    async def _process_table(self, schema_name: str, table_name: str) -> Optional[Document]:
        """Process a database table and create a document."""
        try:
            # Get table metadata
            table_info = await self._get_table_info(schema_name, table_name)
            
            # Create document content
            content = self._create_table_content(table_info)
            
            # Create metadata
            metadata = {
                "source_type": "database_table",
                "schema_name": schema_name,
                "table_name": table_name,
                "database_type": self.database_type,
                "connector_id": self.connector_id,
                "table_info": table_info
            }
            
            # Create document
            source_path = f"{schema_name}.{table_name}"
            document = self._create_document(content, source_path, metadata)
            
            return document
        
        except Exception as e:
            self.logger.error(f"Error processing table {schema_name}.{table_name}: {e}")
            return None
    
    async def _process_view(self, schema_name: str, view_name: str) -> Optional[Document]:
        """Process a database view and create a document."""
        try:
            # Get view metadata
            view_info = await self._get_view_info(schema_name, view_name)
            
            # Create document content
            content = self._create_view_content(view_info)
            
            # Create metadata
            metadata = {
                "source_type": "database_view",
                "schema_name": schema_name,
                "view_name": view_name,
                "database_type": self.database_type,
                "connector_id": self.connector_id,
                "view_info": view_info
            }
            
            # Create document
            source_path = f"{schema_name}.{view_name}_view"
            document = self._create_document(content, source_path, metadata)
            
            return document
        
        except Exception as e:
            self.logger.error(f"Error processing view {schema_name}.{view_name}: {e}")
            return None
    
    async def _get_table_info(self, schema_name: str, table_name: str) -> Dict[str, Any]:
        """Get comprehensive information about a table."""
        table_info = {
            "schema_name": schema_name,
            "table_name": table_name,
            "columns": [],
            "primary_keys": [],
            "foreign_keys": [],
            "indexes": [],
            "constraints": [],
            "sample_data": []
        }
        
        try:
            # Get columns
            columns = self.inspector.get_columns(table_name, schema=schema_name)
            table_info["columns"] = [
                {
                    "name": col["name"],
                    "type": str(col["type"]),
                    "nullable": col.get("nullable", True),
                    "default": str(col.get("default")) if col.get("default") is not None else None,
                    "comment": col.get("comment")
                }
                for col in columns
            ]
            
            # Get primary keys
            pk_constraint = self.inspector.get_pk_constraint(table_name, schema=schema_name)
            if pk_constraint:
                table_info["primary_keys"] = pk_constraint.get("constrained_columns", [])
            
            # Get foreign keys
            if self.include_relationships:
                foreign_keys = self.inspector.get_foreign_keys(table_name, schema=schema_name)
                table_info["foreign_keys"] = [
                    {
                        "name": fk.get("name"),
                        "constrained_columns": fk.get("constrained_columns", []),
                        "referred_table": fk.get("referred_table"),
                        "referred_columns": fk.get("referred_columns", []),
                        "referred_schema": fk.get("referred_schema")
                    }
                    for fk in foreign_keys
                ]
            
            # Get indexes
            if self.include_indexes:
                indexes = self.inspector.get_indexes(table_name, schema=schema_name)
                table_info["indexes"] = [
                    {
                        "name": idx.get("name"),
                        "column_names": idx.get("column_names", []),
                        "unique": idx.get("unique", False)
                    }
                    for idx in indexes
                ]
            
            # Get check constraints
            if self.include_constraints:
                try:
                    check_constraints = self.inspector.get_check_constraints(table_name, schema=schema_name)
                    table_info["constraints"] = [
                        {
                            "name": cc.get("name"),
                            "sqltext": cc.get("sqltext")
                        }
                        for cc in check_constraints
                    ]
                except Exception:
                    # Some databases don't support check constraints introspection
                    pass
            
            # Get sample data if enabled
            if self.include_sample_data:
                sample_data = await self._get_sample_data(schema_name, table_name)
                table_info["sample_data"] = sample_data
        
        except Exception as e:
            self.logger.error(f"Error getting table info for {schema_name}.{table_name}: {e}")
        
        return table_info
    
    async def _get_view_info(self, schema_name: str, view_name: str) -> Dict[str, Any]:
        """Get information about a database view."""
        view_info = {
            "schema_name": schema_name,
            "view_name": view_name,
            "columns": [],
            "definition": None
        }
        
        try:
            # Get view columns
            columns = self.inspector.get_columns(view_name, schema=schema_name)
            view_info["columns"] = [
                {
                    "name": col["name"],
                    "type": str(col["type"]),
                    "nullable": col.get("nullable", True)
                }
                for col in columns
            ]
            
            # Try to get view definition
            try:
                view_definition = self.inspector.get_view_definition(view_name, schema=schema_name)
                if view_definition:
                    view_info["definition"] = str(view_definition)
            except Exception:
                # Some databases don't support view definition introspection
                pass
        
        except Exception as e:
            self.logger.error(f"Error getting view info for {schema_name}.{view_name}: {e}")
        
        return view_info
    
    async def _get_sample_data(self, schema_name: str, table_name: str) -> List[Dict[str, Any]]:
        """Get sample data from a table."""
        sample_data = []
        
        try:
            # Build qualified table name
            if schema_name and schema_name != "public":
                qualified_name = f'"{schema_name}"."{table_name}"'
            else:
                qualified_name = f'"{table_name}"'
            
            # Execute sample query
            query = sqlalchemy.text(f"SELECT * FROM {qualified_name} LIMIT {self.sample_data_limit}")
            
            with self.engine.connect() as conn:
                result = conn.execute(query)
                columns = result.keys()
                
                for row in result:
                    row_data = {}
                    for i, value in enumerate(row):
                        # Convert non-serializable types to strings
                        if isinstance(value, (datetime, bytes)):
                            row_data[columns[i]] = str(value)
                        else:
                            row_data[columns[i]] = value
                    sample_data.append(row_data)
        
        except Exception as e:
            self.logger.error(f"Error getting sample data for {schema_name}.{table_name}: {e}")
        
        return sample_data
    
    def _create_table_content(self, table_info: Dict[str, Any]) -> str:
        """Create document content for a table."""
        content_parts = []
        
        # Table header
        content_parts.append(f"# Table: {table_info['schema_name']}.{table_info['table_name']}")
        content_parts.append("")
        
        # Columns section
        content_parts.append("## Columns")
        for col in table_info["columns"]:
            nullable = "NULL" if col["nullable"] else "NOT NULL"
            default = f" DEFAULT {col['default']}" if col["default"] else ""
            comment = f" -- {col['comment']}" if col.get("comment") else ""
            
            content_parts.append(f"- **{col['name']}**: {col['type']} {nullable}{default}{comment}")
        content_parts.append("")
        
        # Primary keys
        if table_info["primary_keys"]:
            content_parts.append("## Primary Keys")
            content_parts.append(f"- {', '.join(table_info['primary_keys'])}")
            content_parts.append("")
        
        # Foreign keys
        if table_info["foreign_keys"]:
            content_parts.append("## Foreign Keys")
            for fk in table_info["foreign_keys"]:
                ref_table = fk["referred_table"]
                if fk.get("referred_schema"):
                    ref_table = f"{fk['referred_schema']}.{ref_table}"
                
                content_parts.append(
                    f"- **{fk['name']}**: {', '.join(fk['constrained_columns'])} → "
                    f"{ref_table}({', '.join(fk['referred_columns'])})"
                )
            content_parts.append("")
        
        # Indexes
        if table_info["indexes"]:
            content_parts.append("## Indexes")
            for idx in table_info["indexes"]:
                unique = " (UNIQUE)" if idx["unique"] else ""
                content_parts.append(f"- **{idx['name']}**: {', '.join(idx['column_names'])}{unique}")
            content_parts.append("")
        
        # Constraints
        if table_info["constraints"]:
            content_parts.append("## Constraints")
            for constraint in table_info["constraints"]:
                content_parts.append(f"- **{constraint['name']}**: {constraint['sqltext']}")
            content_parts.append("")
        
        # Sample data
        if table_info["sample_data"]:
            content_parts.append("## Sample Data")
            content_parts.append("```json")
            content_parts.append(json.dumps(table_info["sample_data"], indent=2))
            content_parts.append("```")
            content_parts.append("")
        
        return "\n".join(content_parts)
    
    def _create_view_content(self, view_info: Dict[str, Any]) -> str:
        """Create document content for a view."""
        content_parts = []
        
        # View header
        content_parts.append(f"# View: {view_info['schema_name']}.{view_info['view_name']}")
        content_parts.append("")
        
        # Columns section
        content_parts.append("## Columns")
        for col in view_info["columns"]:
            nullable = "NULL" if col["nullable"] else "NOT NULL"
            content_parts.append(f"- **{col['name']}**: {col['type']} {nullable}")
        content_parts.append("")
        
        # View definition
        if view_info.get("definition"):
            content_parts.append("## Definition")
            content_parts.append("```sql")
            content_parts.append(view_info["definition"])
            content_parts.append("```")
            content_parts.append("")
        
        return "\n".join(content_parts)
    
    async def _create_schema_overview(self, schema_name: str, table_names: List[str]) -> Optional[Document]:
        """Create an overview document for the schema."""
        try:
            content_parts = []
            
            # Schema header
            content_parts.append(f"# Database Schema: {schema_name}")
            content_parts.append("")
            content_parts.append(f"Database Type: {self.database_type}")
            content_parts.append(f"Total Tables: {len(table_names)}")
            content_parts.append("")
            
            # Tables list
            content_parts.append("## Tables")
            for table_name in sorted(table_names):
                content_parts.append(f"- {table_name}")
            content_parts.append("")
            
            # Schema relationships (if available)
            relationships = await self._get_schema_relationships(schema_name, table_names)
            if relationships:
                content_parts.append("## Table Relationships")
                for rel in relationships:
                    content_parts.append(f"- {rel}")
                content_parts.append("")
            
            content = "\n".join(content_parts)
            
            # Create metadata
            metadata = {
                "source_type": "database_schema",
                "schema_name": schema_name,
                "database_type": self.database_type,
                "table_count": len(table_names),
                "connector_id": self.connector_id
            }
            
            # Create document
            source_path = f"{schema_name}_schema_overview"
            document = self._create_document(content, source_path, metadata)
            
            return document
        
        except Exception as e:
            self.logger.error(f"Error creating schema overview for {schema_name}: {e}")
            return None
    
    async def _get_schema_relationships(self, schema_name: str, table_names: List[str]) -> List[str]:
        """Get relationships between tables in the schema."""
        relationships = []
        
        try:
            for table_name in table_names:
                foreign_keys = self.inspector.get_foreign_keys(table_name, schema=schema_name)
                
                for fk in foreign_keys:
                    ref_table = fk.get("referred_table")
                    if ref_table in table_names:  # Only include relationships within this schema
                        relationship = (
                            f"{table_name}({', '.join(fk.get('constrained_columns', []))}) → "
                            f"{ref_table}({', '.join(fk.get('referred_columns', []))})"
                        )
                        relationships.append(relationship)
        
        except Exception as e:
            self.logger.error(f"Error getting schema relationships: {e}")
        
        return relationships
    
    async def detect_changes(self) -> List[ChangeDetection]:
        """Detect changes in database schema."""
        changes = []
        
        try:
            # Initialize connection if needed
            if not self.engine:
                await self._initialize_connection()
            
            if not self.engine:
                return changes
            
            # Get current schema checksums
            current_checksums = {}
            
            for schema_name in self.schema_names:
                schema_checksum = await self._calculate_schema_checksum(schema_name)
                current_checksums[schema_name] = schema_checksum
                
                # Compare with previous checksum
                old_checksum = self.schema_checksums.get(schema_name)
                
                if old_checksum is None:
                    # New schema
                    changes.append(ChangeDetection(
                        source_path=f"{schema_name}_schema",
                        change_type=ChangeType.CREATED,
                        timestamp=datetime.utcnow(),
                        new_checksum=schema_checksum
                    ))
                elif old_checksum != schema_checksum:
                    # Modified schema
                    changes.append(ChangeDetection(
                        source_path=f"{schema_name}_schema",
                        change_type=ChangeType.MODIFIED,
                        timestamp=datetime.utcnow(),
                        old_checksum=old_checksum,
                        new_checksum=schema_checksum
                    ))
            
            # Update stored checksums
            self.schema_checksums = current_checksums
        
        except Exception as e:
            self.logger.error(f"Error detecting database changes: {e}")
        finally:
            await self._cleanup_connection()
        
        return changes
    
    async def _calculate_schema_checksum(self, schema_name: str) -> str:
        """Calculate checksum for schema structure."""
        try:
            # Get all table names and their column info
            table_names = self.inspector.get_table_names(schema=schema_name)
            schema_data = {"tables": {}}
            
            for table_name in sorted(table_names):
                if self._filter_tables([table_name]):  # Apply filters
                    columns = self.inspector.get_columns(table_name, schema=schema_name)
                    schema_data["tables"][table_name] = {
                        "columns": [
                            {
                                "name": col["name"],
                                "type": str(col["type"]),
                                "nullable": col.get("nullable")
                            }
                            for col in columns
                        ]
                    }
            
            # Calculate checksum of schema structure
            schema_json = json.dumps(schema_data, sort_keys=True)
            return self._calculate_checksum(schema_json)
        
        except Exception as e:
            self.logger.error(f"Error calculating schema checksum: {e}")
            return ""
    
    async def get_source_metadata(self, source_path: str) -> Dict[str, Any]:
        """Get metadata for a database source."""
        return {
            "source_type": "database",
            "source_path": source_path,
            "database_type": self.database_type,
            "connector_id": self.connector_id,
            "connection_string": self.connection_string.split('@')[-1] if self.connection_string else None  # Hide credentials
        }
    
    async def validate_configuration(self) -> List[str]:
        """Validate database connector configuration."""
        errors = await super().validate_configuration()
        
        # Check SQLAlchemy availability
        if not SQLALCHEMY_AVAILABLE:
            errors.append("SQLAlchemy is required for database connector")
        
        # Check connection string
        if not self.connection_string:
            errors.append("Database connection string is required")
        
        # Check schema names
        if not self.schema_names:
            errors.append("At least one schema name must be specified")
        
        # Test database connection
        try:
            await self._initialize_connection()
            await self._cleanup_connection()
        except Exception as e:
            errors.append(f"Database connection test failed: {str(e)}")
        
        return errors