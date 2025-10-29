"""
Extension Data Management System.

This module provides data storage and management capabilities for extensions
with proper tenant isolation, user access controls, and configuration management.
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

try:
    from sqlalchemy import (
        create_engine, MetaData, Table, Column, String, Integer,
        DateTime, Text, Boolean, JSON, select, insert, update, delete,
        and_, func
    )
    from sqlalchemy.engine import Engine
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    Engine = None


class DataAccessLevel(Enum):
    """Data access levels for extensions."""
    READ_ONLY = "read_only"
    READ_WRITE = "read_write"
    ADMIN = "admin"


class StorageType(Enum):
    """Types of storage backends."""
    POSTGRES = "postgres"
    SQLITE = "sqlite"
    MEMORY = "memory"


@dataclass
class DataSchema:
    """Defines the schema for extension data tables."""
    table_name: str
    columns: Dict[str, str]  # column_name -> column_type
    indexes: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)


@dataclass
class QueryFilter:
    """Represents a query filter."""
    column: str
    operator: str  # '=', '!=', '>', '<', 'LIKE', 'IN', etc.
    value: Any
    
    def to_sql_condition(self, table):
        """Convert filter to SQLAlchemy condition."""
        col = getattr(table.c, self.column)
        
        if self.operator == '=':
            return col == self.value
        elif self.operator == '!=':
            return col != self.value
        elif self.operator == '>':
            return col > self.value
        elif self.operator == '<':
            return col < self.value
        elif self.operator == '>=':
            return col >= self.value
        elif self.operator == '<=':
            return col <= self.value
        elif self.operator == 'LIKE':
            return col.like(self.value)
        elif self.operator == 'IN':
            return col.in_(self.value)
        elif self.operator == 'NOT IN':
            return col.notin_(self.value)
        else:
            raise ValueError(f"Unsupported operator: {self.operator}")


@dataclass
class DataRecord:
    """Represents a data record with metadata."""
    data: Dict[str, Any]
    tenant_id: str
    user_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    record_id: Optional[str] = None


class ExtensionDataManager:
    """
    Manages data storage for extensions with tenant isolation.
    
    This class provides a high-level interface for extensions to store and
    retrieve data while ensuring proper tenant isolation and access controls.
    """
    
    def __init__(
        self, 
        db_session_or_extension_name,
        extension_name: Optional[str] = None,
        database_url: Optional[str] = None,
        storage_type: StorageType = StorageType.SQLITE
    ):
        """
        Initialize the data manager.
        
        Args:
            db_session_or_extension_name: Database session (new style) or extension name (legacy)
            extension_name: Extension name (when using db_session)
            database_url: Database connection URL
            storage_type: Type of storage backend to use
        """
        # Handle both old and new constructor signatures for backward compatibility
        if extension_name is None and isinstance(db_session_or_extension_name, str):
            # Legacy constructor: ExtensionDataManager(extension_name, ...)
            self.extension_name = db_session_or_extension_name
            self.db_session = None
        else:
            # New constructor: ExtensionDataManager(db_session, extension_name, ...)
            self.db_session = db_session_or_extension_name
            self.extension_name = extension_name or "unknown"
        
        self.storage_type = storage_type
        self.logger = logging.getLogger(f"extension.data.{self.extension_name}")
        
        # Table prefix for this extension
        self.table_prefix = f"ext_{self._sanitize_name(self.extension_name)}_"
        
        # Database connection
        self.engine: Optional[Engine] = None
        self.metadata = MetaData() if SQLALCHEMY_AVAILABLE else None
        self.tables: Dict[str, Table] = {}
        
        # NoSQL-style document storage (JSON-based)
        self._document_collections: Dict[str, str] = {}  # collection_name -> table_name mapping
        
        # Privacy and compliance tracking
        self._data_retention_policies: Dict[str, Dict[str, Any]] = {}
        self._encryption_keys: Dict[str, str] = {}
        
        # Initialize database connection
        if SQLALCHEMY_AVAILABLE and not self.db_session:
            self._initialize_database(database_url)
        elif not SQLALCHEMY_AVAILABLE:
            self.logger.warning("SQLAlchemy not available, using in-memory storage")
            self._memory_storage: Dict[str, List[Dict[str, Any]]] = {}
        else:
            # Using provided db_session
            self._memory_storage: Dict[str, List[Dict[str, Any]]] = {}
    
    def _sanitize_name(self, name: str) -> str:
        """Sanitize name for use in database table names."""
        # Replace non-alphanumeric characters with underscores
        sanitized = ''.join(c if c.isalnum() else '_' for c in name.lower())
        # Remove consecutive underscores
        while '__' in sanitized:
            sanitized = sanitized.replace('__', '_')
        return sanitized.strip('_')
    
    def _initialize_database(self, database_url: Optional[str] = None) -> None:
        """Initialize database connection."""
        if not database_url:
            if self.storage_type == StorageType.SQLITE:
                database_url = f"sqlite:///extensions_{self.extension_name}.db"
            elif self.storage_type == StorageType.MEMORY:
                database_url = "sqlite:///:memory:"
            else:
                raise ValueError("Database URL required for non-SQLite storage")
        
        try:
            self.engine = create_engine(database_url, echo=False)
            self.logger.info(f"Connected to database: {database_url}")
        except Exception as e:
            self.logger.error(f"Failed to connect to database: {e}")
            raise
    
    def get_tenant_table_name(self, base_table_name: str, tenant_id: str) -> str:
        """
        Get tenant-specific table name.
        
        Args:
            base_table_name: Base table name
            tenant_id: Tenant ID
            
        Returns:
            Tenant-specific table name
        """
        tenant_suffix = self._sanitize_name(tenant_id)
        return f"{self.table_prefix}{base_table_name}_{tenant_suffix}"
    
    async def create_table(
        self,
        table_name: str,
        schema: DataSchema,
        tenant_id: str
    ) -> bool:
        """
        Create a tenant-isolated table.
        
        Args:
            table_name: Base table name
            schema: Table schema definition
            tenant_id: Tenant ID
            
        Returns:
            True if table was created successfully
        """
        if not SQLALCHEMY_AVAILABLE:
            # For in-memory storage, just initialize the structure
            full_table_name = self.get_tenant_table_name(table_name, tenant_id)
            if full_table_name not in self._memory_storage:
                self._memory_storage[full_table_name] = []
            return True
        
        try:
            full_table_name = self.get_tenant_table_name(table_name, tenant_id)
            
            # Define table columns
            columns = [
                Column('id', Integer, primary_key=True, autoincrement=True),
                Column('tenant_id', String(255), nullable=False, index=True),
                Column('user_id', String(255), nullable=True, index=True),
                Column('created_at', DateTime, nullable=False, default=func.now()),
                Column('updated_at', DateTime, nullable=False, default=func.now(), onupdate=func.now()),
            ]
            
            # Add custom columns from schema
            for col_name, col_type in schema.columns.items():
                if col_type.upper() == 'STRING':
                    columns.append(Column(col_name, String(255)))
                elif col_type.upper() == 'TEXT':
                    columns.append(Column(col_name, Text))
                elif col_type.upper() == 'INTEGER':
                    columns.append(Column(col_name, Integer))
                elif col_type.upper() == 'BOOLEAN':
                    columns.append(Column(col_name, Boolean))
                elif col_type.upper() == 'JSON':
                    columns.append(Column(col_name, JSON))
                else:
                    # Default to String for unknown types
                    columns.append(Column(col_name, String(255)))
            
            # Create table
            table = Table(full_table_name, self.metadata, *columns)
            self.tables[full_table_name] = table
            
            # Create table in database
            table.create(self.engine, checkfirst=True)
            
            self.logger.info(f"Created table: {full_table_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create table {table_name}: {e}")
            return False
    
    async def insert(
        self,
        table_name: str,
        data: Dict[str, Any],
        tenant_id: str,
        user_id: Optional[str] = None
    ) -> Optional[int]:
        """
        Insert data into a tenant-isolated table.
        
        Args:
            table_name: Base table name
            data: Data to insert
            tenant_id: Tenant ID
            user_id: User ID (optional)
            
        Returns:
            Record ID if successful, None otherwise
        """
        if not SQLALCHEMY_AVAILABLE:
            # In-memory storage
            full_table_name = self.get_tenant_table_name(table_name, tenant_id)
            if full_table_name not in self._memory_storage:
                self._memory_storage[full_table_name] = []
            
            record = {
                'id': len(self._memory_storage[full_table_name]) + 1,
                'tenant_id': tenant_id,
                'user_id': user_id,
                'created_at': time.time(),
                'updated_at': time.time(),
                **data
            }
            self._memory_storage[full_table_name].append(record)
            return record['id']
        
        try:
            full_table_name = self.get_tenant_table_name(table_name, tenant_id)
            
            if full_table_name not in self.tables:
                self.logger.error(f"Table {full_table_name} does not exist")
                return None
            
            table = self.tables[full_table_name]
            
            # Prepare insert data
            insert_data = {
                'tenant_id': tenant_id,
                'user_id': user_id,
                **data
            }
            
            # Execute insert
            with self.engine.connect() as conn:
                result = conn.execute(insert(table).values(**insert_data))
                conn.commit()
                
                record_id = result.inserted_primary_key[0]
                self.logger.debug(f"Inserted record {record_id} into {full_table_name}")
                return record_id
                
        except Exception as e:
            self.logger.error(f"Failed to insert data into {table_name}: {e}")
            return None
    
    async def query(
        self,
        table_name: str,
        filters: Optional[List[QueryFilter]] = None,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query data with automatic tenant/user filtering.
        
        Args:
            table_name: Base table name
            filters: Query filters
            tenant_id: Tenant ID for filtering
            user_id: User ID for filtering
            limit: Maximum number of records to return
            offset: Number of records to skip
            order_by: Column to order by
            
        Returns:
            List of matching records
        """
        if not SQLALCHEMY_AVAILABLE:
            # In-memory storage
            if tenant_id:
                full_table_name = self.get_tenant_table_name(table_name, tenant_id)
                records = self._memory_storage.get(full_table_name, [])
            else:
                # Search across all tenant tables for this base table
                records = []
                for table_key, table_records in self._memory_storage.items():
                    if table_key.startswith(f"{self.table_prefix}{table_name}_"):
                        records.extend(table_records)
            
            # Apply filters
            if filters:
                for filter_obj in filters:
                    records = [r for r in records if self._apply_memory_filter(r, filter_obj)]
            
            # Apply user filtering
            if user_id:
                records = [r for r in records if r.get('user_id') == user_id]
            
            # Apply ordering
            if order_by:
                reverse = order_by.startswith('-')
                col = order_by.lstrip('-')
                records.sort(key=lambda x: x.get(col, ''), reverse=reverse)
            
            # Apply pagination
            if offset:
                records = records[offset:]
            if limit:
                records = records[:limit]
            
            return records
        
        try:
            if tenant_id:
                full_table_name = self.get_tenant_table_name(table_name, tenant_id)
                if full_table_name not in self.tables:
                    return []
                
                table = self.tables[full_table_name]
                query = select(table)
                
                # Add tenant filtering
                conditions = [table.c.tenant_id == tenant_id]
                
                # Add user filtering
                if user_id:
                    conditions.append(table.c.user_id == user_id)
                
                # Add custom filters
                if filters:
                    for filter_obj in filters:
                        conditions.append(filter_obj.to_sql_condition(table))
                
                # Apply conditions
                if conditions:
                    query = query.where(and_(*conditions))
                
                # Apply ordering
                if order_by:
                    if order_by.startswith('-'):
                        query = query.order_by(getattr(table.c, order_by[1:]).desc())
                    else:
                        query = query.order_by(getattr(table.c, order_by))
                
                # Apply pagination
                if limit:
                    query = query.limit(limit)
                if offset:
                    query = query.offset(offset)
                
                # Execute query
                with self.engine.connect() as conn:
                    result = conn.execute(query)
                    return [dict(row._mapping) for row in result]
            else:
                # Query across all tenant tables (admin operation)
                all_records = []
                for table_key, table in self.tables.items():
                    if table_key.startswith(f"{self.table_prefix}{table_name}_"):
                        query = select(table)
                        
                        # Add user filtering if specified
                        if user_id:
                            query = query.where(table.c.user_id == user_id)
                        
                        # Add custom filters
                        if filters:
                            conditions = []
                            for filter_obj in filters:
                                conditions.append(filter_obj.to_sql_condition(table))
                            if conditions:
                                query = query.where(and_(*conditions))
                        
                        with self.engine.connect() as conn:
                            result = conn.execute(query)
                            all_records.extend([dict(row._mapping) for row in result])
                
                # Apply ordering and pagination to combined results
                if order_by:
                    reverse = order_by.startswith('-')
                    col = order_by.lstrip('-')
                    all_records.sort(key=lambda x: x.get(col, ''), reverse=reverse)
                
                if offset:
                    all_records = all_records[offset:]
                if limit:
                    all_records = all_records[:limit]
                
                return all_records
                
        except Exception as e:
            self.logger.error(f"Failed to query {table_name}: {e}")
            return []
    
    def _apply_memory_filter(self, record: Dict[str, Any], filter_obj: QueryFilter) -> bool:
        """Apply filter to in-memory record."""
        value = record.get(filter_obj.column)
        
        if filter_obj.operator == '=':
            return value == filter_obj.value
        elif filter_obj.operator == '!=':
            return value != filter_obj.value
        elif filter_obj.operator == '>':
            return value > filter_obj.value
        elif filter_obj.operator == '<':
            return value < filter_obj.value
        elif filter_obj.operator == '>=':
            return value >= filter_obj.value
        elif filter_obj.operator == '<=':
            return value <= filter_obj.value
        elif filter_obj.operator == 'LIKE':
            return str(filter_obj.value).replace('%', '') in str(value)
        elif filter_obj.operator == 'IN':
            return value in filter_obj.value
        elif filter_obj.operator == 'NOT IN':
            return value not in filter_obj.value
        else:
            return False
    
    async def update(
        self,
        table_name: str,
        record_id: int,
        data: Dict[str, Any],
        tenant_id: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Update a record in a tenant-isolated table.
        
        Args:
            table_name: Base table name
            record_id: ID of record to update
            data: Data to update
            tenant_id: Tenant ID
            user_id: User ID for access control
            
        Returns:
            True if update was successful
        """
        if not SQLALCHEMY_AVAILABLE:
            # In-memory storage
            full_table_name = self.get_tenant_table_name(table_name, tenant_id)
            records = self._memory_storage.get(full_table_name, [])
            
            for record in records:
                if record['id'] == record_id and record['tenant_id'] == tenant_id:
                    if user_id and record.get('user_id') != user_id:
                        return False  # Access denied
                    
                    record.update(data)
                    record['updated_at'] = time.time()
                    return True
            return False
        
        try:
            full_table_name = self.get_tenant_table_name(table_name, tenant_id)
            
            if full_table_name not in self.tables:
                return False
            
            table = self.tables[full_table_name]
            
            # Build update conditions
            conditions = [
                table.c.id == record_id,
                table.c.tenant_id == tenant_id
            ]
            
            if user_id:
                conditions.append(table.c.user_id == user_id)
            
            # Execute update
            with self.engine.connect() as conn:
                result = conn.execute(
                    update(table)
                    .where(and_(*conditions))
                    .values(**data)
                )
                conn.commit()
                
                return result.rowcount > 0
                
        except Exception as e:
            self.logger.error(f"Failed to update record {record_id} in {table_name}: {e}")
            return False
    
    async def delete(
        self,
        table_name: str,
        record_id: int,
        tenant_id: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Delete a record from a tenant-isolated table.
        
        Args:
            table_name: Base table name
            record_id: ID of record to delete
            tenant_id: Tenant ID
            user_id: User ID for access control
            
        Returns:
            True if deletion was successful
        """
        if not SQLALCHEMY_AVAILABLE:
            # In-memory storage
            full_table_name = self.get_tenant_table_name(table_name, tenant_id)
            records = self._memory_storage.get(full_table_name, [])
            
            for i, record in enumerate(records):
                if record['id'] == record_id and record['tenant_id'] == tenant_id:
                    if user_id and record.get('user_id') != user_id:
                        return False  # Access denied
                    
                    del records[i]
                    return True
            return False
        
        try:
            full_table_name = self.get_tenant_table_name(table_name, tenant_id)
            
            if full_table_name not in self.tables:
                return False
            
            table = self.tables[full_table_name]
            
            # Build delete conditions
            conditions = [
                table.c.id == record_id,
                table.c.tenant_id == tenant_id
            ]
            
            if user_id:
                conditions.append(table.c.user_id == user_id)
            
            # Execute delete
            with self.engine.connect() as conn:
                result = conn.execute(
                    delete(table).where(and_(*conditions))
                )
                conn.commit()
                
                return result.rowcount > 0
                
        except Exception as e:
            self.logger.error(f"Failed to delete record {record_id} from {table_name}: {e}")
            return False
    
    async def get_config(
        self,
        config_key: str,
        tenant_id: str,
        default: Any = None
    ) -> Any:
        """
        Get extension configuration value.
        
        Args:
            config_key: Configuration key
            tenant_id: Tenant ID
            default: Default value if not found
            
        Returns:
            Configuration value or default
        """
        try:
            # Query configuration table
            filters = [QueryFilter('config_key', '=', config_key)]
            results = await self.query('config', filters, tenant_id)
            
            if results:
                config_value = results[0].get('config_value')
                if isinstance(config_value, str):
                    try:
                        return json.loads(config_value)
                    except json.JSONDecodeError:
                        return config_value
                return config_value
            
            return default
            
        except Exception as e:
            self.logger.error(f"Failed to get config {config_key}: {e}")
            return default
    
    async def set_config(
        self,
        config_key: str,
        config_value: Any,
        tenant_id: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Set extension configuration value.
        
        Args:
            config_key: Configuration key
            config_value: Configuration value
            tenant_id: Tenant ID
            user_id: User ID
            
        Returns:
            True if successful
        """
        try:
            # Ensure config table exists
            config_schema = DataSchema(
                table_name='config',
                columns={
                    'config_key': 'STRING',
                    'config_value': 'TEXT'
                }
            )
            await self.create_table('config', config_schema, tenant_id)
            
            # Serialize value if needed
            if not isinstance(config_value, str):
                config_value = json.dumps(config_value)
            
            # Check if config already exists
            filters = [QueryFilter('config_key', '=', config_key)]
            existing = await self.query('config', filters, tenant_id)
            
            if existing:
                # Update existing config
                return await self.update(
                    'config',
                    existing[0]['id'],
                    {'config_value': config_value},
                    tenant_id,
                    user_id
                )
            else:
                # Insert new config
                record_id = await self.insert(
                    'config',
                    {
                        'config_key': config_key,
                        'config_value': config_value
                    },
                    tenant_id,
                    user_id
                )
                return record_id is not None
                
        except Exception as e:
            self.logger.error(f"Failed to set config {config_key}: {e}")
            return False
    
    async def create_document_collection(
        self,
        collection_name: str,
        tenant_id: str,
        schema_validation: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Create a NoSQL-style document collection.
        
        Args:
            collection_name: Name of the collection
            tenant_id: Tenant ID
            schema_validation: Optional JSON schema for document validation
            
        Returns:
            True if collection was created successfully
        """
        try:
            # Create underlying table for document storage
            table_name = f"docs_{collection_name}"
            schema = DataSchema(
                table_name=table_name,
                columns={
                    'document_id': 'STRING',
                    'document_data': 'JSON',
                    'document_version': 'INTEGER',
                    'document_tags': 'JSON',
                    'schema_version': 'STRING'
                }
            )
            
            success = await self.create_table(table_name, schema, tenant_id)
            if success:
                self._document_collections[collection_name] = self.get_tenant_table_name(table_name, tenant_id)
                
                # Store schema validation if provided
                if schema_validation:
                    await self.set_config(
                        f"collection_schema_{collection_name}",
                        schema_validation,
                        tenant_id
                    )
                
                self.logger.info(f"Created document collection: {collection_name}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to create document collection {collection_name}: {e}")
            return False
    
    async def insert_document(
        self,
        collection_name: str,
        document_id: str,
        document_data: Dict[str, Any],
        tenant_id: str,
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """
        Insert a document into a collection.
        
        Args:
            collection_name: Collection name
            document_id: Unique document identifier
            document_data: Document data
            tenant_id: Tenant ID
            user_id: User ID
            tags: Optional tags for the document
            
        Returns:
            True if document was inserted successfully
        """
        try:
            # Validate document against schema if available
            schema = await self.get_config(f"collection_schema_{collection_name}", tenant_id)
            if schema:
                # Basic schema validation (can be enhanced with jsonschema library)
                if not self._validate_document_schema(document_data, schema):
                    self.logger.warning(f"Document {document_id} failed schema validation")
                    return False
            
            # Insert document
            table_name = f"docs_{collection_name}"
            record_id = await self.insert(
                table_name,
                {
                    'document_id': document_id,
                    'document_data': document_data,
                    'document_version': 1,
                    'document_tags': tags or [],
                    'schema_version': '1.0'
                },
                tenant_id,
                user_id
            )
            
            return record_id is not None
            
        except Exception as e:
            self.logger.error(f"Failed to insert document {document_id}: {e}")
            return False
    
    async def find_documents(
        self,
        collection_name: str,
        tenant_id: str,
        query: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Find documents in a collection.
        
        Args:
            collection_name: Collection name
            tenant_id: Tenant ID
            query: Query filters (applied to document_data)
            user_id: User ID for filtering
            tags: Tags to filter by
            limit: Maximum number of documents to return
            
        Returns:
            List of matching documents
        """
        try:
            table_name = f"docs_{collection_name}"
            filters = []
            
            # Add tag filtering
            if tags:
                # This is a simplified implementation - in production, use proper JSON querying
                for tag in tags:
                    filters.append(QueryFilter('document_tags', 'LIKE', f'%"{tag}"%'))
            
            # Query documents
            results = await self.query(
                table_name,
                filters,
                tenant_id,
                user_id,
                limit=limit
            )
            
            # Apply document-level query filtering
            if query:
                filtered_results = []
                for result in results:
                    document_data = result.get('document_data', {})
                    if self._matches_document_query(document_data, query):
                        filtered_results.append({
                            'document_id': result.get('document_id'),
                            'document_data': document_data,
                            'document_version': result.get('document_version'),
                            'document_tags': result.get('document_tags', []),
                            'created_at': result.get('created_at'),
                            'updated_at': result.get('updated_at')
                        })
                return filtered_results
            else:
                return [{
                    'document_id': result.get('document_id'),
                    'document_data': result.get('document_data', {}),
                    'document_version': result.get('document_version'),
                    'document_tags': result.get('document_tags', []),
                    'created_at': result.get('created_at'),
                    'updated_at': result.get('updated_at')
                } for result in results]
            
        except Exception as e:
            self.logger.error(f"Failed to find documents in {collection_name}: {e}")
            return []
    
    def _validate_document_schema(self, document: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """Basic document schema validation."""
        # This is a simplified implementation
        # In production, use jsonschema library for proper validation
        required_fields = schema.get('required', [])
        for field in required_fields:
            if field not in document:
                return False
        return True
    
    def _matches_document_query(self, document: Dict[str, Any], query: Dict[str, Any]) -> bool:
        """Check if document matches query criteria."""
        for key, value in query.items():
            if key not in document:
                return False
            if isinstance(value, dict) and '$eq' in value:
                if document[key] != value['$eq']:
                    return False
            elif isinstance(value, dict) and '$in' in value:
                if document[key] not in value['$in']:
                    return False
            elif document[key] != value:
                return False
        return True
    
    async def set_data_retention_policy(
        self,
        table_name: str,
        tenant_id: str,
        retention_days: int,
        auto_delete: bool = True
    ) -> bool:
        """
        Set data retention policy for privacy compliance.
        
        Args:
            table_name: Table name
            tenant_id: Tenant ID
            retention_days: Number of days to retain data
            auto_delete: Whether to automatically delete expired data
            
        Returns:
            True if policy was set successfully
        """
        try:
            policy_key = f"{table_name}_{tenant_id}"
            self._data_retention_policies[policy_key] = {
                'retention_days': retention_days,
                'auto_delete': auto_delete,
                'created_at': time.time()
            }
            
            # Store policy in configuration
            await self.set_config(
                f"retention_policy_{table_name}",
                self._data_retention_policies[policy_key],
                tenant_id
            )
            
            self.logger.info(f"Set retention policy for {table_name}: {retention_days} days")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set retention policy: {e}")
            return False
    
    async def cleanup_expired_data(self, tenant_id: str) -> Dict[str, int]:
        """
        Clean up expired data based on retention policies.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Dictionary with cleanup statistics
        """
        cleanup_stats = {}
        
        try:
            # Get all retention policies for this tenant
            for policy_key, policy in self._data_retention_policies.items():
                if not policy_key.endswith(f"_{tenant_id}"):
                    continue
                
                table_name = policy_key.replace(f"_{tenant_id}", "")
                retention_days = policy['retention_days']
                auto_delete = policy.get('auto_delete', True)
                
                if not auto_delete:
                    continue
                
                # Calculate cutoff date
                cutoff_timestamp = time.time() - (retention_days * 24 * 60 * 60)
                
                # Find expired records
                if not SQLALCHEMY_AVAILABLE:
                    # In-memory cleanup
                    full_table_name = self.get_tenant_table_name(table_name, tenant_id)
                    records = self._memory_storage.get(full_table_name, [])
                    original_count = len(records)
                    
                    # Filter out expired records
                    self._memory_storage[full_table_name] = [
                        r for r in records 
                        if r.get('created_at', time.time()) > cutoff_timestamp
                    ]
                    
                    deleted_count = original_count - len(self._memory_storage[full_table_name])
                    cleanup_stats[table_name] = deleted_count
                else:
                    # Database cleanup
                    full_table_name = self.get_tenant_table_name(table_name, tenant_id)
                    if full_table_name in self.tables:
                        table = self.tables[full_table_name]
                        
                        with self.engine.connect() as conn:
                            # Count records to be deleted
                            count_query = select(func.count()).select_from(table).where(
                                and_(
                                    table.c.tenant_id == tenant_id,
                                    table.c.created_at < func.datetime('now', f'-{retention_days} days')
                                )
                            )
                            result = conn.execute(count_query)
                            delete_count = result.scalar()
                            
                            # Delete expired records
                            if delete_count > 0:
                                delete_query = delete(table).where(
                                    and_(
                                        table.c.tenant_id == tenant_id,
                                        table.c.created_at < func.datetime('now', f'-{retention_days} days')
                                    )
                                )
                                conn.execute(delete_query)
                                conn.commit()
                            
                            cleanup_stats[table_name] = delete_count
            
            if cleanup_stats:
                self.logger.info(f"Cleaned up expired data: {cleanup_stats}")
            
            return cleanup_stats
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup expired data: {e}")
            return {}
    
    async def encrypt_sensitive_field(
        self,
        table_name: str,
        field_name: str,
        tenant_id: str,
        encryption_key: Optional[str] = None
    ) -> bool:
        """
        Mark a field for encryption (placeholder for encryption implementation).
        
        Args:
            table_name: Table name
            field_name: Field to encrypt
            tenant_id: Tenant ID
            encryption_key: Optional encryption key
            
        Returns:
            True if field was marked for encryption
        """
        try:
            # Store encryption metadata
            encryption_config = {
                'field_name': field_name,
                'encryption_enabled': True,
                'key_id': encryption_key or f"key_{tenant_id}_{field_name}",
                'algorithm': 'AES-256-GCM'
            }
            
            await self.set_config(
                f"encryption_{table_name}_{field_name}",
                encryption_config,
                tenant_id
            )
            
            self.logger.info(f"Enabled encryption for {table_name}.{field_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to enable encryption: {e}")
            return False
    
    def get_table_info(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about tables for this extension.
        
        Args:
            tenant_id: Tenant ID (optional, for admin queries)
            
        Returns:
            Dictionary with table information
        """
        info = {
            'extension_name': self.extension_name,
            'table_prefix': self.table_prefix,
            'storage_type': self.storage_type.value,
            'tables': [],
            'document_collections': list(self._document_collections.keys()),
            'retention_policies': len(self._data_retention_policies)
        }
        
        if not SQLALCHEMY_AVAILABLE:
            # In-memory storage info
            for table_name in self._memory_storage.keys():
                if table_name.startswith(self.table_prefix):
                    record_count = len(self._memory_storage[table_name])
                    info['tables'].append({
                        'name': table_name,
                        'record_count': record_count,
                        'type': 'document' if any(table_name.endswith(f"docs_{col}_{tenant_id or 'unknown'}") for col in self._document_collections.keys()) else 'relational'
                    })
        else:
            # Database table info
            for table_name, table in self.tables.items():
                if tenant_id:
                    # Get count for specific tenant
                    try:
                        with self.engine.connect() as conn:
                            count_query = select(func.count()).select_from(table).where(
                                table.c.tenant_id == tenant_id
                            )
                            result = conn.execute(count_query)
                            record_count = result.scalar()
                    except Exception:
                        record_count = 0
                else:
                    # Get total count
                    try:
                        with self.engine.connect() as conn:
                            count_query = select(func.count()).select_from(table)
                            result = conn.execute(count_query)
                            record_count = result.scalar()
                    except Exception:
                        record_count = 0
                
                info['tables'].append({
                    'name': table_name,
                    'record_count': record_count,
                    'type': 'document' if 'docs_' in table_name else 'relational'
                })
        
        return info


# Export the main classes
__all__ = [
    "ExtensionDataManager",
    "DataSchema",
    "QueryFilter",
    "DataRecord",
    "DataAccessLevel",
    "StorageType"
]