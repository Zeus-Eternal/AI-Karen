"""
Test suite for NeuroVault database schema migration.
"""

import pytest
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any

from ai_karen_engine.database.client import MultiTenantPostgresClient
from ai_karen_engine.database.config import DatabaseConfig


class TestNeuroVaultSchemaMigration:
    """Test the NeuroVault database schema migration."""
    
    @pytest.fixture
    async def db_client(self):
        """Create a database client for testing."""
        config = DatabaseConfig()
        client = MultiTenantPostgresClient(config)
        yield client
        await client.close()
    
    @pytest.mark.asyncio
    async def test_memory_items_neuro_columns_exist(self, db_client):
        """Test that all NeuroVault columns exist in memory_items table."""
        async with db_client.get_async_session() as session:
            result = await session.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'memory_items' 
                AND column_name IN (
                    'neuro_type', 'decay_lambda', 'reflection_count',
                    'source_memories', 'derived_memories', 'importance_decay',
                    'last_reflection', 'importance_score', 'access_count'
                );
            """)
            columns = [row[0] for row in result.fetchall()]
            
            expected_columns = [
                'neuro_type', 'decay_lambda', 'reflection_count',
                'source_memories', 'derived_memories', 'importance_decay',
                'last_reflection', 'importance_score', 'access_count'
            ]
            
            for col in expected_columns:
                assert col in columns, f"Missing NeuroVault column: {col}"
    
    @pytest.mark.asyncio
    async def test_memory_relationships_table_exists(self, db_client):
        """Test that memory_relationships table exists with correct structure."""
        async with db_client.get_async_session() as session:
            # Check table exists
            result = await session.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'memory_relationships'
                );
            """)
            assert result.scalar(), "memory_relationships table does not exist"
            
            # Check required columns exist
            result = await session.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'memory_relationships';
            """)
            columns = [row[0] for row in result.fetchall()]
            
            required_columns = [
                'id', 'source_memory_id', 'derived_memory_id',
                'relationship_type', 'confidence_score', 'metadata',
                'created_at', 'updated_at'
            ]
            
            for col in required_columns:
                assert col in columns, f"Missing column in memory_relationships: {col}"
    
    @pytest.mark.asyncio
    async def test_neuro_vault_functions_exist(self, db_client):
        """Test that all NeuroVault functions exist."""
        async with db_client.get_async_session() as session:
            result = await session.execute("""
                SELECT routine_name 
                FROM information_schema.routines 
                WHERE routine_schema = 'public' 
                AND routine_name IN (
                    'calculate_decay_score', 'update_memory_access', 'create_memory_relationship'
                );
            """)
            functions = [row[0] for row in result.fetchall()]
            
            expected_functions = ['calculate_decay_score', 'update_memory_access', 'create_memory_relationship']
            
            for func in expected_functions:
                assert func in functions, f"Missing NeuroVault function: {func}"
    
    @pytest.mark.asyncio
    async def test_neuro_vault_views_exist(self, db_client):
        """Test that all NeuroVault views exist."""
        async with db_client.get_async_session() as session:
            result = await session.execute("""
                SELECT table_name 
                FROM information_schema.views 
                WHERE table_schema = 'public' 
                AND table_name IN (
                    'active_memories_with_decay', 'memory_relationship_details', 'memory_analytics'
                );
            """)
            views = [row[0] for row in result.fetchall()]
            
            expected_views = ['active_memories_with_decay', 'memory_relationship_details', 'memory_analytics']
            
            for view in expected_views:
                assert view in views, f"Missing NeuroVault view: {view}"
    
    @pytest.mark.asyncio
    async def test_decay_score_calculation(self, db_client):
        """Test the decay score calculation function."""
        async with db_client.get_async_session() as session:
            # Test episodic memory decay (should decay faster)
            result = await session.execute("""
                SELECT calculate_decay_score(NOW() - INTERVAL '1 day', 'episodic', 5, 0);
            """)
            episodic_score = result.scalar()
            
            # Test semantic memory decay (should decay slower)
            result = await session.execute("""
                SELECT calculate_decay_score(NOW() - INTERVAL '1 day', 'semantic', 5, 0);
            """)
            semantic_score = result.scalar()
            
            # Test procedural memory decay (should decay slowest)
            result = await session.execute("""
                SELECT calculate_decay_score(NOW() - INTERVAL '1 day', 'procedural', 5, 0);
            """)
            procedural_score = result.scalar()
            
            # Verify scores are valid (between 0 and 1)
            assert 0.0 <= episodic_score <= 1.0, f"Invalid episodic decay score: {episodic_score}"
            assert 0.0 <= semantic_score <= 1.0, f"Invalid semantic decay score: {semantic_score}"
            assert 0.0 <= procedural_score <= 1.0, f"Invalid procedural decay score: {procedural_score}"
            
            # Verify decay rates (episodic should decay fastest)
            assert episodic_score < semantic_score, "Episodic memory should decay faster than semantic"
            assert semantic_score < procedural_score, "Semantic memory should decay faster than procedural"
    
    @pytest.mark.asyncio
    async def test_memory_access_update(self, db_client):
        """Test the memory access update function."""
        async with db_client.get_async_session() as session:
            # Create a test memory
            result = await session.execute("""
                INSERT INTO memory_items (
                    scope, kind, content, neuro_type, importance_score, access_count
                ) VALUES (
                    'test', 'validation', 'Test memory for access update', 'episodic', 5, 0
                ) RETURNING id;
            """)
            memory_id = result.scalar()
            
            try:
                # Update memory access
                await session.execute(f"SELECT update_memory_access('{memory_id}');")
                
                # Verify access count was incremented
                result = await session.execute(f"""
                    SELECT access_count, last_accessed 
                    FROM memory_items 
                    WHERE id = '{memory_id}';
                """)
                row = result.fetchone()
                access_count, last_accessed = row
                
                assert access_count == 1, f"Expected access_count=1, got {access_count}"
                assert last_accessed is not None, "last_accessed should be set"
                assert isinstance(last_accessed, datetime), "last_accessed should be a datetime"
                
                # Update again
                await session.execute(f"SELECT update_memory_access('{memory_id}');")
                
                result = await session.execute(f"""
                    SELECT access_count FROM memory_items WHERE id = '{memory_id}';
                """)
                access_count = result.scalar()
                
                assert access_count == 2, f"Expected access_count=2, got {access_count}"
                
            finally:
                # Clean up test memory
                await session.execute(f"DELETE FROM memory_items WHERE id = '{memory_id}';")
                await session.commit()
    
    @pytest.mark.asyncio
    async def test_memory_relationship_creation(self, db_client):
        """Test the memory relationship creation function."""
        async with db_client.get_async_session() as session:
            # Create two test memories
            result1 = await session.execute("""
                INSERT INTO memory_items (
                    scope, kind, content, neuro_type, importance_score
                ) VALUES (
                    'test', 'validation', 'Source memory for relationship test', 'episodic', 5
                ) RETURNING id;
            """)
            source_id = result1.scalar()
            
            result2 = await session.execute("""
                INSERT INTO memory_items (
                    scope, kind, content, neuro_type, importance_score
                ) VALUES (
                    'test', 'validation', 'Derived memory for relationship test', 'semantic', 7
                ) RETURNING id;
            """)
            derived_id = result2.scalar()
            
            try:
                # Create relationship
                result = await session.execute(f"""
                    SELECT create_memory_relationship(
                        '{source_id}', '{derived_id}', 'reflection', 0.8, '{{"test": true}}'::jsonb
                    );
                """)
                relationship_id = result.scalar()
                
                assert relationship_id is not None, "Relationship creation should return an ID"
                
                # Verify relationship was created
                result = await session.execute(f"""
                    SELECT source_memory_id, derived_memory_id, relationship_type, confidence_score
                    FROM memory_relationships 
                    WHERE id = '{relationship_id}';
                """)
                row = result.fetchone()
                
                assert row is not None, "Relationship should exist in database"
                assert str(row[0]) == str(source_id), "Source memory ID should match"
                assert str(row[1]) == str(derived_id), "Derived memory ID should match"
                assert row[2] == 'reflection', "Relationship type should match"
                assert row[3] == 0.8, "Confidence score should match"
                
                # Verify memory arrays were updated
                result = await session.execute(f"""
                    SELECT derived_memories FROM memory_items WHERE id = '{source_id}';
                """)
                derived_memories = result.scalar()
                assert str(derived_id) in str(derived_memories), "Source memory should reference derived memory"
                
                result = await session.execute(f"""
                    SELECT source_memories FROM memory_items WHERE id = '{derived_id}';
                """)
                source_memories = result.scalar()
                assert str(source_id) in str(source_memories), "Derived memory should reference source memory"
                
            finally:
                # Clean up test data
                await session.execute(f"DELETE FROM memory_relationships WHERE source_memory_id = '{source_id}' OR derived_memory_id = '{derived_id}';")
                await session.execute(f"DELETE FROM memory_items WHERE id IN ('{source_id}', '{derived_id}');")
                await session.commit()
    
    @pytest.mark.asyncio
    async def test_neuro_type_constraints(self, db_client):
        """Test that neuro_type constraints work correctly."""
        async with db_client.get_async_session() as session:
            # Test valid neuro_type
            result = await session.execute("""
                INSERT INTO memory_items (
                    scope, kind, content, neuro_type, importance_score
                ) VALUES (
                    'test', 'validation', 'Test memory with valid neuro_type', 'episodic', 5
                ) RETURNING id;
            """)
            memory_id = result.scalar()
            assert memory_id is not None, "Should be able to insert memory with valid neuro_type"
            
            # Clean up
            await session.execute(f"DELETE FROM memory_items WHERE id = '{memory_id}';")
            
            # Test invalid neuro_type (should fail)
            with pytest.raises(Exception):
                await session.execute("""
                    INSERT INTO memory_items (
                        scope, kind, content, neuro_type, importance_score
                    ) VALUES (
                        'test', 'validation', 'Test memory with invalid neuro_type', 'invalid_type', 5
                    );
                """)
                await session.commit()
    
    @pytest.mark.asyncio
    async def test_importance_score_constraints(self, db_client):
        """Test that importance_score constraints work correctly."""
        async with db_client.get_async_session() as session:
            # Test valid importance_score
            result = await session.execute("""
                INSERT INTO memory_items (
                    scope, kind, content, neuro_type, importance_score
                ) VALUES (
                    'test', 'validation', 'Test memory with valid importance', 'episodic', 7
                ) RETURNING id;
            """)
            memory_id = result.scalar()
            assert memory_id is not None, "Should be able to insert memory with valid importance_score"
            
            # Clean up
            await session.execute(f"DELETE FROM memory_items WHERE id = '{memory_id}';")
            
            # Test invalid importance_score (should fail)
            with pytest.raises(Exception):
                await session.execute("""
                    INSERT INTO memory_items (
                        scope, kind, content, neuro_type, importance_score
                    ) VALUES (
                        'test', 'validation', 'Test memory with invalid importance', 'episodic', 15
                    );
                """)
                await session.commit()
    
    @pytest.mark.asyncio
    async def test_active_memories_view(self, db_client):
        """Test the active_memories_with_decay view."""
        async with db_client.get_async_session() as session:
            # Create a test memory
            result = await session.execute("""
                INSERT INTO memory_items (
                    scope, kind, content, neuro_type, importance_score, importance_decay
                ) VALUES (
                    'test', 'validation', 'Test memory for view test', 'episodic', 5, 0.8
                ) RETURNING id;
            """)
            memory_id = result.scalar()
            
            try:
                # Query the view
                result = await session.execute(f"""
                    SELECT id, current_decay_score, should_cleanup
                    FROM active_memories_with_decay 
                    WHERE id = '{memory_id}';
                """)
                row = result.fetchone()
                
                assert row is not None, "Memory should appear in active_memories_with_decay view"
                assert row[1] is not None, "current_decay_score should be calculated"
                assert isinstance(row[1], float), "current_decay_score should be a float"
                assert 0.0 <= row[1] <= 1.0, "current_decay_score should be between 0 and 1"
                assert isinstance(row[2], bool), "should_cleanup should be a boolean"
                
            finally:
                # Clean up test memory
                await session.execute(f"DELETE FROM memory_items WHERE id = '{memory_id}';")
                await session.commit()
    
    @pytest.mark.asyncio
    async def test_memory_analytics_view(self, db_client):
        """Test the memory_analytics view."""
        async with db_client.get_async_session() as session:
            # Query the analytics view
            result = await session.execute("""
                SELECT neuro_type, total_count, avg_importance, avg_decay_score
                FROM memory_analytics
                LIMIT 5;
            """)
            rows = result.fetchall()
            
            # Should return some data (even if empty, the view should work)
            assert isinstance(rows, list), "memory_analytics view should return a list"
            
            # If there are rows, validate the structure
            for row in rows:
                assert len(row) >= 4, "Each row should have at least 4 columns"
                if row[1] > 0:  # If there are memories of this type
                    assert row[2] is not None, "avg_importance should not be None if memories exist"
                    assert row[3] is not None, "avg_decay_score should not be None if memories exist"