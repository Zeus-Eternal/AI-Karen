"""Tests for Enhanced Analytics Dashboard Extension."""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

from extensions.analytics.dashboard.analytics_extension import AnalyticsDashboardExtension
from extensions.analytics.dashboard.api_routes import router
from fastapi.testclient import TestClient
from fastapi import FastAPI


class TestAnalyticsDashboardExtension:
    """Test suite for AnalyticsDashboardExtension."""
    
    @pytest.fixture
    def extension(self):
        """Create analytics extension instance."""
        return AnalyticsDashboardExtension()
    
    @pytest.fixture
    def mock_hook_context(self):
        """Mock hook context data."""
        return {
            'message': {
                'id': 'msg_123',
                'content': 'Test message',
                'type': 'user',
                'source': 'chat'
            },
            'response': {
                'provider': 'openai',
                'model': 'gpt-4',
                'processing_time': 1500,
                'token_usage': 150,
                'confidence': 0.85,
                'ai_insights': [{'type': 'suggestion', 'content': 'Test insight'}]
            },
            'user_satisfaction': 4.2
        }
    
    @pytest.fixture
    def mock_user_context(self):
        """Mock user context data."""
        return {
            'userId': 'user_123',
            'sessionId': 'session_456'
        }
    
    @pytest.mark.asyncio
    async def test_extension_initialization(self, extension):
        """Test extension initializes correctly."""
        assert extension.name == "analytics-dashboard"
        assert extension.version == "2.0.0"
        assert hasattr(extension, 'conversation_metrics')
        assert hasattr(extension, 'memory_analytics')
        assert hasattr(extension, 'user_engagement_data')
        assert hasattr(extension, 'llm_performance_data')
    
    @pytest.mark.asyncio
    async def test_collect_message_analytics(self, extension, mock_hook_context, mock_user_context):
        """Test message analytics collection."""
        result = await extension._collect_message_analytics(mock_hook_context, mock_user_context)
        
        assert result['success'] is True
        assert result['analytics_collected'] is True
        assert len(extension.conversation_metrics) == 1
        
        analytics_data = extension.conversation_metrics[0]
        assert analytics_data['message_id'] == 'msg_123'
        assert analytics_data['user_id'] == 'user_123'
        assert analytics_data['response_time'] == 1500
        assert analytics_data['llm_provider'] == 'openai'
        assert analytics_data['ai_insights_count'] == 1
    
    @pytest.mark.asyncio
    async def test_collect_llm_performance(self, extension, mock_user_context):
        """Test LLM performance metrics collection."""
        context = {
            'response': {
                'provider': 'ollama',
                'model': 'llama2',
                'processing_time': 2000,
                'token_usage': 200,
                'tokens_per_second': 50,
                'confidence': 0.9,
                'context_length': 1000,
                'completion_reason': 'stop'
            }
        }
        
        result = await extension._collect_llm_performance(context, mock_user_context)
        
        assert result['success'] is True
        assert result['llm_performance_collected'] is True
        assert len(extension.llm_performance_data) == 1
        
        performance_data = extension.llm_performance_data[0]
        assert performance_data['provider'] == 'ollama'
        assert performance_data['model'] == 'llama2'
        assert performance_data['response_time'] == 2000
        assert performance_data['tokens_per_second'] == 50
    
    @pytest.mark.asyncio
    async def test_collect_memory_analytics(self, extension, mock_user_context):
        """Test memory analytics collection."""
        context = {
            'memory': {
                'type': 'fact',
                'confidence': 0.95,
                'semantic_cluster': 'programming_preferences',
                'relationships': ['mem_1', 'mem_2'],
                'tags': ['typescript', 'programming'],
                'content': 'User prefers TypeScript over JavaScript',
                'source': 'conversation'
            }
        }
        
        result = await extension._collect_memory_analytics(context, mock_user_context)
        
        assert result['success'] is True
        assert result['memory_analytics_collected'] is True
        assert len(extension.memory_analytics) == 1
        
        memory_data = extension.memory_analytics[0]
        assert memory_data['user_id'] == 'user_123'
        assert memory_data['memory_type'] == 'fact'
        assert memory_data['confidence'] == 0.95
        assert memory_data['semantic_cluster'] == 'programming_preferences'
        assert memory_data['relationship_count'] == 2
        assert memory_data['tag_count'] == 2
    
    @pytest.mark.asyncio
    async def test_track_memory_retrieval(self, extension, mock_user_context):
        """Test memory retrieval tracking."""
        context = {
            'query': {'type': 'semantic', 'text': 'programming preferences'},
            'results': [{'id': 'mem_1'}, {'id': 'mem_2'}],
            'retrieval_time': 500
        }
        
        result = await extension._track_memory_retrieval(context, mock_user_context)
        
        assert result['success'] is True
        assert result['retrieval_tracked'] is True
    
    @pytest.mark.asyncio
    async def test_track_ui_engagement(self, extension, mock_user_context):
        """Test UI engagement tracking."""
        context = {
            'component': {
                'type': 'chat',
                'id': 'chat_interface_123'
            },
            'interaction_type': 'click',
            'duration': 2500,
            'success': True
        }
        
        result = await extension._track_ui_engagement(context, mock_user_context)
        
        assert result['success'] is True
        assert result['engagement_tracked'] is True
        assert len(extension.user_engagement_data) == 1
        
        engagement_data = extension.user_engagement_data[0]
        assert engagement_data['user_id'] == 'user_123'
        assert engagement_data['component_type'] == 'chat'
        assert engagement_data['interaction_type'] == 'click'
        assert engagement_data['duration'] == 2500
    
    @pytest.mark.asyncio
    async def test_get_conversation_analytics(self, extension):
        """Test conversation analytics retrieval."""
        # Add test data
        test_data = {
            'timestamp': datetime.utcnow(),
            'message_id': 'msg_123',
            'user_id': 'user_123',
            'response_time': 1500,
            'llm_provider': 'openai',
            'ai_insights_count': 2
        }
        extension.conversation_metrics.append(test_data)
        
        # Test retrieval
        result = await extension.get_conversation_analytics('24h', 'user_123')
        
        assert len(result) == 1
        assert result[0]['message_id'] == 'msg_123'
        assert result[0]['user_id'] == 'user_123'
        assert isinstance(result[0]['timestamp'], str)  # Should be ISO string
    
    @pytest.mark.asyncio
    async def test_get_memory_network_data(self, extension):
        """Test memory network data generation."""
        # Add test memory data
        test_memories = [
            {
                'timestamp': datetime.utcnow().isoformat(),
                'user_id': 'user_123',
                'memory_type': 'fact',
                'confidence': 0.9,
                'semantic_cluster': 'programming_preferences'
            },
            {
                'timestamp': datetime.utcnow().isoformat(),
                'user_id': 'user_123',
                'memory_type': 'preference',
                'confidence': 0.85,
                'semantic_cluster': 'programming_preferences'
            },
            {
                'timestamp': datetime.utcnow().isoformat(),
                'user_id': 'user_123',
                'memory_type': 'context',
                'confidence': 0.8,
                'semantic_cluster': 'current_projects'
            }
        ]
        extension.memory_analytics.extend(test_memories)
        
        result = await extension.get_memory_network_data('user_123')
        
        assert 'nodes' in result
        assert 'edges' in result
        assert 'clusters' in result
        assert result['total_memories'] == 3
        
        # Check clusters are created
        cluster_nodes = [node for node in result['nodes'] if node['type'] == 'cluster']
        assert len(cluster_nodes) == 2  # programming_preferences and current_projects
        
        # Check memory nodes are created
        memory_nodes = [node for node in result['nodes'] if node['type'] == 'memory']
        assert len(memory_nodes) == 3
        
        # Check edges connect memories to clusters
        assert len(result['edges']) == 3
    
    @pytest.mark.asyncio
    async def test_get_user_engagement_grid_data(self, extension):
        """Test user engagement grid data retrieval."""
        # Add test engagement data
        test_engagement = {
            'timestamp': datetime.utcnow(),
            'user_id': 'user_123',
            'component_type': 'analytics',
            'interaction_type': 'view',
            'duration': 3000,
            'success': True
        }
        extension.user_engagement_data.append(test_engagement)
        
        result = await extension.get_user_engagement_grid_data('user_123')
        
        assert len(result) == 1
        assert result[0]['user_id'] == 'user_123'
        assert result[0]['component_type'] == 'analytics'
        assert isinstance(result[0]['timestamp'], str)  # Should be ISO string
    
    @pytest.mark.asyncio
    async def test_data_cleanup(self, extension):
        """Test that old data is cleaned up properly."""
        # Add old data (more than 24 hours ago)
        old_timestamp = datetime.utcnow() - timedelta(hours=25)
        old_data = {
            'timestamp': old_timestamp,
            'message_id': 'old_msg',
            'user_id': 'user_123'
        }
        extension.conversation_metrics.append(old_data)
        
        # Add recent data
        recent_data = {
            'timestamp': datetime.utcnow(),
            'message_id': 'recent_msg',
            'user_id': 'user_123'
        }
        extension.conversation_metrics.append(recent_data)
        
        # Trigger cleanup by collecting new analytics
        mock_context = {
            'message': {'id': 'new_msg'},
            'response': {'processing_time': 1000, 'provider': 'test'}
        }
        mock_user_context = {'userId': 'user_123'}
        
        await extension._collect_message_analytics(mock_context, mock_user_context)
        
        # Check that old data is removed
        timestamps = [item['timestamp'] for item in extension.conversation_metrics]
        old_count = sum(1 for ts in timestamps if ts == old_timestamp)
        assert old_count == 0  # Old data should be cleaned up
    
    @pytest.mark.asyncio
    async def test_error_handling(self, extension):
        """Test error handling in analytics collection."""
        # Test with invalid context
        invalid_context = {'invalid': 'data'}
        mock_user_context = {'userId': 'user_123'}
        
        result = await extension._collect_message_analytics(invalid_context, mock_user_context)
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_get_status(self, extension):
        """Test extension status reporting."""
        # Add some test data
        extension.conversation_metrics.append({'test': 'data'})
        extension.memory_analytics.append({'test': 'data'})
        
        status = await extension.get_status()
        
        assert status['name'] == 'analytics-dashboard'
        assert status['version'] == '2.0.0'
        assert status['status'] == 'running'
        assert status['metrics_collected']['conversations'] == 1
        assert status['metrics_collected']['memories'] == 1
        assert 'prometheus_available' in status


class TestAnalyticsAPIRoutes:
    """Test suite for Analytics API routes."""
    
    @pytest.fixture
    def app(self):
        """Create FastAPI test app."""
        app = FastAPI()
        app.include_router(router)
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_extension(self):
        """Mock analytics extension."""
        extension = Mock(spec=AnalyticsDashboardExtension)
        extension.get_conversation_analytics = AsyncMock(return_value=[
            {
                'timestamp': '2024-01-01T10:00:00Z',
                'messageCount': 25,
                'responseTime': 1500,
                'userSatisfaction': 4.2,
                'aiInsights': 5,
                'tokenUsage': 150,
                'llmProvider': 'openai'
            }
        ])
        extension.get_memory_network_data = AsyncMock(return_value={
            'nodes': [{'id': 'node1', 'label': 'Test', 'type': 'memory'}],
            'edges': [],
            'clusters': ['test'],
            'totalMemories': 1
        })
        extension.get_user_engagement_grid_data = AsyncMock(return_value=[
            {
                'timestamp': '2024-01-01T10:00:00Z',
                'userId': 'user123',
                'componentType': 'chat',
                'componentId': 'chat_1',
                'interactionType': 'click',
                'duration': 1000,
                'success': True
            }
        ])
        extension.get_status = AsyncMock(return_value={
            'name': 'analytics-dashboard',
            'status': 'running'
        })
        extension.get_prometheus_metrics = AsyncMock(return_value="# Test metrics")
        return extension
    
    @patch('extensions.analytics.dashboard.api_routes.get_analytics_extension')
    def test_get_conversation_analytics(self, mock_get_extension, client, mock_extension):
        """Test conversation analytics API endpoint."""
        mock_get_extension.return_value = mock_extension
        
        response = client.get("/api/analytics/conversation-data?timeframe=24h")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['llmProvider'] == 'openai'
        mock_extension.get_conversation_analytics.assert_called_once_with('24h', None)
    
    @patch('extensions.analytics.dashboard.api_routes.get_analytics_extension')
    def test_get_memory_network(self, mock_get_extension, client, mock_extension):
        """Test memory network API endpoint."""
        mock_get_extension.return_value = mock_extension
        
        response = client.get("/api/analytics/memory-network")
        
        assert response.status_code == 200
        data = response.json()
        assert 'nodes' in data
        assert 'edges' in data
        assert data['totalMemories'] == 1
        mock_extension.get_memory_network_data.assert_called_once_with(None)
    
    @patch('extensions.analytics.dashboard.api_routes.get_analytics_extension')
    def test_get_user_engagement(self, mock_get_extension, client, mock_extension):
        """Test user engagement API endpoint."""
        mock_get_extension.return_value = mock_extension
        
        response = client.get("/api/analytics/user-engagement?user_id=user123")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['userId'] == 'user123'
        mock_extension.get_user_engagement_grid_data.assert_called_once_with('user123')
    
    @patch('extensions.analytics.dashboard.api_routes.get_analytics_extension')
    def test_get_analytics_stats(self, mock_get_extension, client, mock_extension):
        """Test analytics stats API endpoint."""
        mock_get_extension.return_value = mock_extension
        
        response = client.get("/api/analytics/stats?timeframe=7d")
        
        assert response.status_code == 200
        data = response.json()
        assert 'totalConversations' in data
        assert 'totalMessages' in data
        assert 'avgResponseTime' in data
        mock_extension.get_conversation_analytics.assert_called_once_with('7d')
    
    @patch('extensions.analytics.dashboard.api_routes.get_analytics_extension')
    def test_get_prometheus_metrics(self, mock_get_extension, client, mock_extension):
        """Test Prometheus metrics API endpoint."""
        mock_get_extension.return_value = mock_extension
        
        response = client.get("/api/analytics/prometheus-metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert data['metrics'] == "# Test metrics"
        assert data['content_type'] == "text/plain"
    
    @patch('extensions.analytics.dashboard.api_routes.get_analytics_extension')
    def test_get_analytics_health(self, mock_get_extension, client, mock_extension):
        """Test analytics health API endpoint."""
        mock_get_extension.return_value = mock_extension
        
        response = client.get("/api/analytics/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data['name'] == 'analytics-dashboard'
        assert data['status'] == 'running'
    
    @patch('extensions.analytics.dashboard.api_routes.get_analytics_extension')
    def test_api_error_handling(self, mock_get_extension, client):
        """Test API error handling when extension is unavailable."""
        mock_get_extension.side_effect = Exception("Extension not available")
        
        response = client.get("/api/analytics/conversation-data")
        
        assert response.status_code == 503
        assert "Analytics service unavailable" in response.json()['detail']
    
    def test_invalid_timeframe_parameter(self, client):
        """Test API validation for invalid timeframe parameter."""
        with patch('extensions.analytics.dashboard.api_routes.get_analytics_extension') as mock_get:
            mock_get.return_value = Mock()
            
            response = client.get("/api/analytics/conversation-data?timeframe=invalid")
            
            assert response.status_code == 422  # Validation error


@pytest.mark.integration
class TestAnalyticsIntegration:
    """Integration tests for analytics system."""
    
    @pytest.mark.asyncio
    async def test_full_analytics_pipeline(self):
        """Test complete analytics data flow."""
        extension = AnalyticsDashboardExtension()
        
        # Simulate message processing
        message_context = {
            'message': {
                'id': 'msg_123',
                'content': 'Test message',
                'type': 'user'
            },
            'response': {
                'provider': 'openai',
                'model': 'gpt-4',
                'processing_time': 1500,
                'token_usage': 150,
                'confidence': 0.85,
                'ai_insights': [{'type': 'suggestion'}]
            }
        }
        user_context = {'userId': 'user_123'}
        
        # Collect analytics
        await extension._collect_message_analytics(message_context, user_context)
        
        # Simulate memory operation
        memory_context = {
            'memory': {
                'type': 'fact',
                'confidence': 0.9,
                'semantic_cluster': 'test_cluster',
                'relationships': [],
                'tags': ['test'],
                'content': 'Test memory',
                'source': 'conversation'
            }
        }
        
        await extension._collect_memory_analytics(memory_context, user_context)
        
        # Simulate UI interaction
        ui_context = {
            'component': {'type': 'chat', 'id': 'chat_1'},
            'interaction_type': 'click',
            'duration': 1000,
            'success': True
        }
        
        await extension._track_ui_engagement(ui_context, user_context)
        
        # Verify data collection
        assert len(extension.conversation_metrics) == 1
        assert len(extension.memory_analytics) == 1
        assert len(extension.user_engagement_data) == 1
        
        # Test data retrieval
        conversation_data = await extension.get_conversation_analytics('24h', 'user_123')
        memory_network = await extension.get_memory_network_data('user_123')
        engagement_data = await extension.get_user_engagement_grid_data('user_123')
        
        assert len(conversation_data) == 1
        assert memory_network['total_memories'] == 1
        assert len(engagement_data) == 1
        
        # Test status reporting
        status = await extension.get_status()
        assert status['metrics_collected']['conversations'] == 1
        assert status['metrics_collected']['memories'] == 1
        assert status['metrics_collected']['engagement_events'] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])