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
        extension_name: str,
        database_url: Optional[str] = None,
        storage_type: StorageType = StorageType.SQLITE
    ):
        """
        Initialize the data manager.
        
        Args:
            extension_name: Name of the extension
            database_url: Database connection URL
            storage_type: Type of storage backend to use
        """
        self.extension_name = extension_name
        self.storage_type = storage_type
        self.logger = logging.getLogger(f"extension.data.{extension_name}")
        
        # Table prefix for this extension
        self.table_prefix = f"ext_{self._sanitize_name(extension_name)}_"
        
        # Database connection
        self.engine: Optional[Engine] = None
        self.metadata = MetaData()
        self.tables: Dict[str, Table] = {}
        
        # Initialize database connection
        if SQLALCHEMY_AVAILABLE:
            self._initialize_database(database_url)
        else:
            self.logger.warning("SQLAlchemy not available, using in-memory storage")
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
            'tables': []
        }
        
        if not SQLALCHEMY_AVAILABLE:
            # In-memory storage info
            for table_name in self._memory_storage.keys():
                if table_name.startswith(self.table_prefix):
                    record_count = len(self._memory_storage[table_name])
                    info['tables'].append({
                        'name': table_name,
                        'record_count': record_count
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
                    'record_count': record_count
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