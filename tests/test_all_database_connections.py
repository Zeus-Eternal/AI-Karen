#!/usr/bin/env python3
"""
Comprehensive database connectivity test for all AI Karen databases.
Tests PostgreSQL, Redis, Elasticsearch, Milvus, and DuckDB connections.
"""

import os
import sys
import json
import time
from typing import Dict, Any

# Add src to path
sys.path.insert(0, 'src')

def test_postgresql_connection() -> Dict[str, Any]:
    """Test PostgreSQL connection using our enhanced client."""
    try:
        from ai_karen_engine.database.config import DatabaseConfig
        from ai_karen_engine.database.client import MultiTenantPostgresClient
        
        print("🔍 Testing PostgreSQL connection...")
        
        config = DatabaseConfig(
            host='localhost',
            port=5432,
            user='karen_user',
            password='karen_secure_pass_change_me',
            database='ai_karen'
        )
        
        client = MultiTenantPostgresClient(config=config)
        health = client.health_check()
        
        if health['status'] == 'healthy':
            print(f"✅ PostgreSQL: Connected successfully ({health.get('response_time_ms', 'N/A')}ms)")
            return {
                "status": "success",
                "database": "PostgreSQL",
                "version": health.get('database_version', 'Unknown'),
                "response_time_ms": health.get('response_time_ms', 0),
                "pool_status": health.get('pool_status', {}),
                "details": health
            }
        else:
            print(f"❌ PostgreSQL: Connection failed - {health.get('error', 'Unknown error')}")
            return {
                "status": "failed",
                "database": "PostgreSQL",
                "error": health.get('error', 'Unknown error'),
                "error_type": health.get('error_type', 'unknown')
            }
            
    except Exception as e:
        print(f"❌ PostgreSQL: Exception - {e}")
        return {
            "status": "error",
            "database": "PostgreSQL",
            "error": str(e)
        }

def test_redis_connection() -> Dict[str, Any]:
    """Test Redis connection."""
    try:
        import redis
        
        print("🔍 Testing Redis connection...")
        
        client = redis.Redis(
            host='localhost',
            port=6379,
            password='redis_secure_pass_change_me',
            decode_responses=True
        )
        
        start_time = time.time()
        
        # Test basic operations
        client.ping()
        client.set('test_key', 'test_value', ex=10)  # Expires in 10 seconds
        value = client.get('test_key')
        client.delete('test_key')
        
        response_time = (time.time() - start_time) * 1000
        
        # Get Redis info
        info = client.info()
        
        print(f"✅ Redis: Connected successfully ({response_time:.2f}ms)")
        return {
            "status": "success",
            "database": "Redis",
            "version": info.get('redis_version', 'Unknown'),
            "response_time_ms": round(response_time, 2),
            "memory_used": info.get('used_memory_human', 'Unknown'),
            "connected_clients": info.get('connected_clients', 0),
            "details": {
                "uptime_seconds": info.get('uptime_in_seconds', 0),
                "total_commands_processed": info.get('total_commands_processed', 0)
            }
        }
        
    except Exception as e:
        print(f"❌ Redis: Connection failed - {e}")
        return {
            "status": "error",
            "database": "Redis",
            "error": str(e)
        }

def test_elasticsearch_connection() -> Dict[str, Any]:
    """Test Elasticsearch connection."""
    try:
        import requests
        
        print("🔍 Testing Elasticsearch connection...")
        
        start_time = time.time()
        
        # Test cluster health
        health_response = requests.get('http://localhost:9200/_cluster/health', timeout=10)
        health_response.raise_for_status()
        health_data = health_response.json()
        
        # Test basic info
        info_response = requests.get('http://localhost:9200/', timeout=10)
        info_response.raise_for_status()
        info_data = info_response.json()
        
        response_time = (time.time() - start_time) * 1000
        
        print(f"✅ Elasticsearch: Connected successfully ({response_time:.2f}ms)")
        return {
            "status": "success",
            "database": "Elasticsearch",
            "version": info_data.get('version', {}).get('number', 'Unknown'),
            "response_time_ms": round(response_time, 2),
            "cluster_name": health_data.get('cluster_name', 'Unknown'),
            "cluster_status": health_data.get('status', 'Unknown'),
            "number_of_nodes": health_data.get('number_of_nodes', 0),
            "details": {
                "active_primary_shards": health_data.get('active_primary_shards', 0),
                "active_shards": health_data.get('active_shards', 0),
                "relocating_shards": health_data.get('relocating_shards', 0),
                "initializing_shards": health_data.get('initializing_shards', 0),
                "unassigned_shards": health_data.get('unassigned_shards', 0)
            }
        }
        
    except Exception as e:
        print(f"❌ Elasticsearch: Connection failed - {e}")
        return {
            "status": "error",
            "database": "Elasticsearch",
            "error": str(e)
        }

def test_milvus_connection() -> Dict[str, Any]:
    """Test Milvus connection."""
    try:
        # Try to import pymilvus
        try:
            from pymilvus import connections, utility
        except ImportError:
            print("⚠️  Milvus: pymilvus not installed, skipping test")
            return {
                "status": "skipped",
                "database": "Milvus",
                "error": "pymilvus not installed"
            }
        
        print("🔍 Testing Milvus connection...")
        
        start_time = time.time()
        
        # Connect to Milvus
        connections.connect(
            alias="default",
            host='localhost',
            port='19530'
        )
        
        # Test connection
        server_version = utility.get_server_version()
        
        response_time = (time.time() - start_time) * 1000
        
        # Disconnect
        connections.disconnect("default")
        
        print(f"✅ Milvus: Connected successfully ({response_time:.2f}ms)")
        return {
            "status": "success",
            "database": "Milvus",
            "version": server_version,
            "response_time_ms": round(response_time, 2),
            "details": {
                "server_version": server_version
            }
        }
        
    except Exception as e:
        print(f"❌ Milvus: Connection failed - {e}")
        return {
            "status": "error",
            "database": "Milvus",
            "error": str(e)
        }

def test_duckdb_connection() -> Dict[str, Any]:
    """Test DuckDB connection."""
    try:
        import duckdb
        
        print("🔍 Testing DuckDB connection...")
        
        start_time = time.time()
        
        # Connect to DuckDB (file-based)
        db_path = "kari_duckdb.db"  # Local file
        conn = duckdb.connect(db_path)
        
        # Test basic query
        result = conn.execute("SELECT version()").fetchone()
        version = result[0] if result else "Unknown"
        
        # Test table creation and query
        conn.execute("CREATE TABLE IF NOT EXISTS test_table (id INTEGER, name VARCHAR)")
        conn.execute("INSERT INTO test_table VALUES (1, 'test')")
        test_result = conn.execute("SELECT COUNT(*) FROM test_table").fetchone()
        conn.execute("DROP TABLE test_table")
        
        response_time = (time.time() - start_time) * 1000
        
        conn.close()
        
        print(f"✅ DuckDB: Connected successfully ({response_time:.2f}ms)")
        return {
            "status": "success",
            "database": "DuckDB",
            "version": version,
            "response_time_ms": round(response_time, 2),
            "database_path": db_path,
            "details": {
                "test_query_result": test_result[0] if test_result else 0
            }
        }
        
    except Exception as e:
        print(f"❌ DuckDB: Connection failed - {e}")
        return {
            "status": "error",
            "database": "DuckDB",
            "error": str(e)
        }

def main():
    """Run comprehensive database connectivity tests."""
    print("🚀 AI Karen - Comprehensive Database Connectivity Test")
    print("=" * 60)
    
    results = []
    
    # Test all databases
    databases = [
        ("PostgreSQL", test_postgresql_connection),
        ("Redis", test_redis_connection),
        ("Elasticsearch", test_elasticsearch_connection),
        ("Milvus", test_milvus_connection),
        ("DuckDB", test_duckdb_connection)
    ]
    
    for db_name, test_func in databases:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ {db_name}: Unexpected error - {e}")
            results.append({
                "status": "error",
                "database": db_name,
                "error": f"Unexpected error: {str(e)}"
            })
        
        print()  # Add spacing between tests
    
    # Summary
    print("📊 CONNECTIVITY SUMMARY")
    print("=" * 60)
    
    successful = 0
    failed = 0
    skipped = 0
    
    for result in results:
        status = result["status"]
        db_name = result["database"]
        
        if status == "success":
            successful += 1
            version = result.get("version", "Unknown")
            if isinstance(version, list):
                version = " ".join(str(v) for v in version)
            response_time = result.get("response_time_ms", "N/A")
            print(f"✅ {db_name:<15} | Version: {str(version):<20} | Response: {response_time}ms")
        elif status == "skipped":
            skipped += 1
            reason = result.get("error", "Unknown reason")
            print(f"⚠️  {db_name:<15} | Skipped: {reason}")
        else:
            failed += 1
            error = result.get("error", "Unknown error")
            print(f"❌ {db_name:<15} | Error: {error}")
    
    print("=" * 60)
    print(f"📈 Results: {successful} successful, {failed} failed, {skipped} skipped")
    
    # Save detailed results to file
    with open('reports/database_connectivity_results.json', 'w') as f:
        json.dump({
            "timestamp": time.time(),
            "summary": {
                "successful": successful,
                "failed": failed,
                "skipped": skipped,
                "total": len(results)
            },
            "results": results
        }, f, indent=2)
    
    print(f"📄 Detailed results saved to: reports/database_connectivity_results.json")
    
    if failed > 0:
        print(f"\n⚠️  {failed} database(s) failed to connect. Please check the configuration and ensure services are running.")
        sys.exit(1)
    else:
        print(f"\n🎉 All available databases connected successfully!")

if __name__ == "__main__":
    main()