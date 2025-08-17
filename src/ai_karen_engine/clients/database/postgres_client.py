"""Enhanced Postgres client with multi-tenant support and optional SQLite fallback."""
from __future__ import annotations

import json
import os
import sqlite3
import logging
from typing import Any, Dict, List, Optional, Union
import uuid

try:
    import psycopg
    _PSYCOPG_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    psycopg = None
    _PSYCOPG_AVAILABLE = False

# Import the new multi-tenant client
try:
    from ai_karen_engine.database.client import MultiTenantPostgresClient
    _MULTITENANT_AVAILABLE = True
except ImportError:
    MultiTenantPostgresClient = None
    _MULTITENANT_AVAILABLE = False

logger = logging.getLogger(__name__)


class PostgresClient:
    """Enhanced Postgres client with multi-tenant support and memory persistence."""

    def __init__(self, dsn: str = "", use_sqlite: bool = False, enable_multitenant: bool = True) -> None:
        self.dsn = dsn
        self.use_sqlite = use_sqlite or not _PSYCOPG_AVAILABLE
        self.enable_multitenant = enable_multitenant and _MULTITENANT_AVAILABLE and not use_sqlite
        
        # Initialize multi-tenant client if available
        self.multitenant_client = None
        if self.enable_multitenant:
            try:
                database_url = self._build_database_url(dsn)
                self.multitenant_client = MultiTenantPostgresClient(database_url)
                logger.info("Multi-tenant PostgreSQL client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize multi-tenant client: {e}")
                self.enable_multitenant = False
        
        # Initialize legacy connection for backward compatibility
        if self.use_sqlite:
            path = dsn.replace("sqlite://", "") or ":memory:"
            self.conn = sqlite3.connect(path, check_same_thread=False)
        else:
            pg_dsn = dsn or (
                "dbname=%s user=%s password=%s host=%s port=%s"
                % (
                    os.getenv("POSTGRES_DB", "postgres"),
                    os.getenv("POSTGRES_USER", "postgres"),
                    os.getenv("POSTGRES_PASSWORD", "postgres"),
                    os.getenv("POSTGRES_HOST", "localhost"),
                    os.getenv("POSTGRES_PORT", "5432"),
                )
            )
            self.conn = psycopg.connect(pg_dsn, autocommit=True)
        self._ensure_table()
    
    def _build_database_url(self, dsn: str = "") -> str:
        """Build database URL for multi-tenant client."""
        if dsn and dsn.startswith("postgresql://"):
            return dsn
        
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "postgres")
        database = os.getenv("POSTGRES_DB", "ai_karen")
        
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"

    @property
    def placeholder(self) -> str:
        """Return SQL placeholder appropriate for the backend."""
        return "?" if self.use_sqlite else "%s"

    # ------------------------------------------------------------------
    def _ensure_table(self) -> None:
        create_sql = (
            "CREATE TABLE IF NOT EXISTS memory ("
            "vector_id BIGINT PRIMARY KEY,"
            "tenant_id VARCHAR,"
            "user_id VARCHAR,"
            "session_id VARCHAR,"
            "query TEXT,"
            "result TEXT,"
            "timestamp BIGINT"
            ")"
        )
        cur = self.conn.cursor()
        cur.execute(create_sql)
        self.conn.commit()
        cur.close()

    # ------------------------------------------------------------------
    def _execute(self, sql: str, params: Optional[List[Any]] = None, fetch: bool = False) -> List[tuple]:
        cur = self.conn.cursor()
        cur.execute(sql, params or [])
        rows = cur.fetchall() if fetch else []
        self.conn.commit()
        cur.close()
        return rows

    # ------------------------------------------------------------------
    def upsert_memory(
        self,
        vector_id: int,
        tenant_id: str,
        user_id: str,
        session_id: str,
        query: str,
        result: Any,
        timestamp: int = 0,
    ) -> None:
        data_json = json.dumps(result)
        if self.use_sqlite:
            sql = (
                "INSERT INTO memory (vector_id, tenant_id, user_id, session_id, query, result, timestamp) "
                "VALUES (?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(vector_id) DO UPDATE SET "
                "tenant_id=excluded.tenant_id, user_id=excluded.user_id, session_id=excluded.session_id, "
                "query=excluded.query, result=excluded.result, timestamp=excluded.timestamp"
            )
            self._execute(
                sql, [vector_id, tenant_id, user_id, session_id, query, data_json, timestamp]
            )
        else:
            sql = (
                "INSERT INTO memory (vector_id, tenant_id, user_id, session_id, query, result, timestamp) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s) "
                "ON CONFLICT (vector_id) DO UPDATE SET "
                "tenant_id=EXCLUDED.tenant_id, user_id=EXCLUDED.user_id, session_id=EXCLUDED.session_id, "
                "query=EXCLUDED.query, result=EXCLUDED.result, timestamp=EXCLUDED.timestamp"
            )
            self._execute(
                sql, [vector_id, tenant_id, user_id, session_id, query, data_json, timestamp]
            )

    def get_by_vector(self, vector_id: int) -> Optional[Dict[str, Any]]:
        sql = "SELECT tenant_id, user_id, session_id, query, result, timestamp FROM memory WHERE vector_id = "
        sql += "?" if self.use_sqlite else "%s"
        rows = self._execute(sql, [vector_id], fetch=True)
        if not rows:
            return None
        row = rows[0]
        return {
            "tenant_id": row[0],
            "user_id": row[1],
            "session_id": row[2],
            "query": row[3],
            "result": json.loads(row[4]),
            "timestamp": row[5],
        }

    def get_session_records(self, session_id: str, tenant_id: str) -> List[Dict[str, Any]]:
        sql = "SELECT vector_id, tenant_id, user_id, session_id, query, result, timestamp FROM memory WHERE session_id = "
        sql += "?" if self.use_sqlite else "%s"
        sql += " AND tenant_id = " + ("?" if self.use_sqlite else "%s")
        params = [session_id, tenant_id]
        rows = self._execute(sql, params, fetch=True)
        return [
            {
                "vector_id": r[0],
                "tenant_id": r[1],
                "user_id": r[2],
                "session_id": r[3],
                "query": r[4],
                "result": json.loads(r[5]),
                "timestamp": r[6],
            }
            for r in rows
        ]

    def recall_memory(
        self, user_id: str, query: Optional[str] = None, limit: int = 5, tenant_id: str = ""
    ) -> List[Dict[str, Any]]:
        sql = (
            "SELECT vector_id, tenant_id, user_id, session_id, query, result, timestamp FROM memory "
            "WHERE user_id = "
        )
        sql += "?" if self.use_sqlite else "%s"
        sql += " AND tenant_id = " + ("?" if self.use_sqlite else "%s")
        params = [user_id, tenant_id]
        sql += " ORDER BY timestamp DESC LIMIT "
        sql += "?" if self.use_sqlite else "%s"
        params.append(limit)
        rows = self._execute(sql, params, fetch=True)
        return [
            {
                "vector_id": r[0],
                "tenant_id": r[1],
                "user_id": r[2],
                "session_id": r[3],
                "query": r[4],
                "result": json.loads(r[5]),
                "timestamp": r[6],
            }
            for r in rows
        ]

    def delete(self, vector_id: int) -> None:
        sql = "DELETE FROM memory WHERE vector_id = "
        sql += "?" if self.use_sqlite else "%s"
        self._execute(sql, [vector_id])

    def health(self) -> bool:
        try:
            self._execute("SELECT 1", fetch=True)
            return True
        except Exception:
            return False
    
    # Multi-tenant methods (new functionality)
    def setup_tenant(self, tenant_id: str, tenant_name: str, tenant_slug: str) -> bool:
        """Set up a new tenant with isolated schema.
        
        Args:
            tenant_id: Tenant UUID
            tenant_name: Tenant name
            tenant_slug: Tenant slug
            
        Returns:
            True if setup was successful
        """
        if not self.enable_multitenant:
            logger.warning("Multi-tenant support not available")
            return False
        
        try:
            return self.multitenant_client.create_tenant_schema(tenant_id)
        except Exception as e:
            logger.error(f"Failed to setup tenant {tenant_id}: {e}")
            return False
    
    def teardown_tenant(self, tenant_id: str) -> bool:
        """Teardown a tenant and remove all data.
        
        Args:
            tenant_id: Tenant UUID
            
        Returns:
            True if teardown was successful
        """
        if not self.enable_multitenant:
            logger.warning("Multi-tenant support not available")
            return False
        
        try:
            return self.multitenant_client.drop_tenant_schema(tenant_id)
        except Exception as e:
            logger.error(f"Failed to teardown tenant {tenant_id}: {e}")
            return False
    
    def tenant_exists(self, tenant_id: str) -> bool:
        """Check if tenant schema exists.
        
        Args:
            tenant_id: Tenant UUID
            
        Returns:
            True if tenant exists
        """
        if not self.enable_multitenant:
            return False
        
        try:
            return self.multitenant_client.tenant_schema_exists(tenant_id)
        except Exception as e:
            logger.error(f"Failed to check tenant {tenant_id}: {e}")
            return False
    
    def get_tenant_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Get statistics for a tenant.
        
        Args:
            tenant_id: Tenant UUID
            
        Returns:
            Tenant statistics
        """
        if not self.enable_multitenant:
            return {"error": "Multi-tenant support not available"}
        
        try:
            return self.multitenant_client.get_tenant_stats(tenant_id)
        except Exception as e:
            logger.error(f"Failed to get tenant stats for {tenant_id}: {e}")
            return {"error": str(e)}
    
    def execute_tenant_query(
        self,
        query: str,
        tenant_id: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute a query in tenant context.
        
        Args:
            query: SQL query
            tenant_id: Tenant UUID
            params: Query parameters
            
        Returns:
            Query result
        """
        if not self.enable_multitenant:
            raise RuntimeError("Multi-tenant support not available")
        
        return self.multitenant_client.execute_tenant_query(query, tenant_id, params)
    
    def upsert_tenant_memory(
        self,
        vector_id: int,
        tenant_id: str,
        user_id: str,
        session_id: str,
        query: str,
        result: Any,
        timestamp: int = 0,
    ) -> None:
        """Upsert memory entry in tenant-specific schema.
        
        This method uses the new multi-tenant architecture when available,
        otherwise falls back to the legacy method.
        """
        if self.enable_multitenant:
            try:
                # Use tenant-specific schema
                data_json = json.dumps(result)
                sql = """
                    INSERT INTO memory_items (id, scope, kind, content, metadata, created_at)
                    VALUES (%s, %s, %s, %s, %s, to_timestamp(%s))
                    ON CONFLICT (id) DO UPDATE SET
                    scope=EXCLUDED.scope, kind=EXCLUDED.kind,
                    content=EXCLUDED.content, metadata=EXCLUDED.metadata,
                    created_at=EXCLUDED.created_at
                """
                self.multitenant_client.execute_tenant_query(
                    sql, tenant_id,
                    [str(vector_id), user_id, session_id, query, data_json, timestamp]
                )
                return
            except Exception as e:
                logger.warning(f"Failed to use tenant-specific memory storage: {e}, falling back to legacy")
        
        # Fall back to legacy method
        self.upsert_memory(vector_id, tenant_id, user_id, session_id, query, result, timestamp)
    
    def get_multitenant_client(self) -> Optional[MultiTenantPostgresClient]:
        """Get the underlying multi-tenant client.
        
        Returns:
            MultiTenantPostgresClient instance or None if not available
        """
        return self.multitenant_client
    
    def is_multitenant_enabled(self) -> bool:
        """Check if multi-tenant support is enabled.
        
        Returns:
            True if multi-tenant support is available and enabled
        """
        return self.enable_multitenant and self.multitenant_client is not None


__all__ = ["PostgresClient"]
