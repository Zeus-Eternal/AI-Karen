"""Enhanced Analytics Dashboard Extension with AG-UI Integration."""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ai_karen_engine.extensions.base import BaseExtension
from ai_karen_engine.hooks.hook_mixin import HookMixin
from ai_karen_engine.utils.metrics import init_metrics
from ai_karen_engine.core.plugin_metrics import PLUGIN_CALLS, MEMORY_WRITES

logger = logging.getLogger(__name__)

try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("Prometheus client not available, using dummy metrics")


class AnalyticsDashboardExtension(BaseExtension, HookMixin):
    """Enhanced analytics dashboard with AG-UI data visualization."""
    
    def __init__(self):
        super().__init__()
        self.name = "analytics-dashboard"
        self.version = "2.0.0"
        self.description = "Enhanced analytics dashboard with AG-UI charts and real-time metrics"
        
        # Initialize metrics
        self._init_prometheus_metrics()
        
        # Data storage for analytics
        self.conversation_metrics: List[Dict[str, Any]] = []
        self.memory_analytics: List[Dict[str, Any]] = []
        self.user_engagement_data: List[Dict[str, Any]] = []
        self.llm_performance_data: List[Dict[str, Any]] = []
        
        # Register hooks
        asyncio.create_task(self._register_analytics_hooks())
    
    def _init_prometheus_metrics(self):
        """Initialize Prometheus metrics for analytics."""
        if not PROMETHEUS_AVAILABLE:
            return
            
        try:
            # Chat-specific metrics
            self.chat_hub_latency_seconds = Histogram(
                'chat_hub_latency_seconds',
                'Chat hub response latency in seconds',
                ['provider', 'model']
            )
            
            self.conversation_count = Counter(
                'conversations_total',
                'Total number of conversations',
                ['user_type', 'status']
            )
            
            self.message_count = Counter(
                'messages_total',
                'Total number of messages',
                ['type', 'source']
            )
            
            self.user_satisfaction_gauge = Gauge(
                'user_satisfaction_score',
                'Current user satisfaction score',
                ['user_id', 'timeframe']
            )
            
            self.ai_insights_count = Counter(
                'ai_insights_total',
                'Total AI insights generated',
                ['type', 'confidence_level']
            )
            
            self.token_usage_counter = Counter(
                'token_usage_total',
                'Total token usage',
                ['provider', 'model', 'operation']
            )
            
            # Memory system metrics
            self.memory_operations = Counter(
                'memory_operations_total',
                'Total memory operations',
                ['operation', 'success']
            )
            
            self.memory_retrieval_latency = Histogram(
                'memory_retrieval_latency_seconds',
                'Memory retrieval latency in seconds',
                ['query_type']
            )
            
            # Extension and plugin metrics
            self.extension_operations = Counter(
                'extension_operations_total',
                'Total extension operations',
                ['extension', 'operation', 'success']
            )
            
            # Collaboration-specific metrics
            self.collaboration_sessions = Gauge(
                'collaboration_sessions_active',
                'Number of active collaboration sessions',
                ['session_type', 'conversation_id']
            )
            
            self.collaboration_participants = Gauge(
                'collaboration_participants_total',
                'Total number of collaboration participants',
                ['session_type']
            )
            
            self.presence_updates = Counter(
                'presence_updates_total',
                'Total presence updates',
                ['status', 'user_type']
            )
            
            self.typing_indicators = Counter(
                'typing_indicators_total',
                'Total typing indicator events',
                ['conversation_id', 'action']
            )
            
            self.collaborative_edits = Counter(
                'collaborative_edits_total',
                'Total collaborative editing events',
                ['session_type', 'edit_type']
            )
            
            self.websocket_connections = Gauge(
                'websocket_connections_active',
                'Number of active WebSocket connections',
                ['authenticated', 'conversation_id']
            )
            
            logger.info("Prometheus metrics initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Prometheus metrics: {e}")
    
    async def _register_analytics_hooks(self):
        """Register hooks for analytics data collection."""
        try:
            # Chat analytics hooks
            await self.register_hook(
                'post_message',
                self._collect_message_analytics,
                priority=90
            )
            
            await self.register_hook(
                'llm_response',
                self._collect_llm_performance,
                priority=95
            )
            
            # Memory analytics hooks
            await self.register_hook(
                'memory_store',
                self._collect_memory_analytics,
                priority=85
            )
            
            await self.register_hook(
                'memory_retrieve',
                self._track_memory_retrieval,
                priority=85
            )
            
            # User engagement hooks
            await self.register_hook(
                'ui_component_render',
                self._track_ui_engagement,
                priority=80
            )
            
            # Collaboration analytics hooks
            await self.register_hook(
                'collaboration_session_start',
                self._track_collaboration_session,
                priority=85
            )
            
            await self.register_hook(
                'user_presence_update',
                self._track_presence_update,
                priority=85
            )
            
            await self.register_hook(
                'typing_indicator',
                self._track_typing_indicator,
                priority=85
            )
            
            await self.register_hook(
                'collaborative_edit',
                self._track_collaborative_edit,
                priority=85
            )
            
            await self.register_hook(
                'websocket_connection',
                self._track_websocket_connection,
                priority=85
            )
            
            logger.info("Analytics hooks registered successfully")
            
        except Exception as e:
            logger.error(f"Failed to register analytics hooks: {e}")
    
    async def _collect_message_analytics(self, context: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Collect analytics data from message processing."""
        try:
            message = context.get('message', {})
            response = context.get('response', {})
            timestamp = datetime.utcnow()
            
            # Extract analytics data
            analytics_data = {
                'timestamp': timestamp,
                'message_id': message.get('id'),
                'user_id': user_context.get('userId'),
                'message_length': len(message.get('content', '')),
                'response_time': response.get('processing_time', 0),
                'llm_provider': response.get('provider', 'unknown'),
                'model': response.get('model', 'unknown'),
                'token_usage': response.get('token_usage', 0),
                'confidence_score': response.get('confidence', 0.0),
                'has_code_blocks': bool(response.get('code_blocks')),
                'ai_insights_count': len(response.get('ai_insights', [])),
                'user_satisfaction': context.get('user_satisfaction', 0.0)
            }
            
            # Store for AG-UI visualization
            self.conversation_metrics.append(analytics_data)
            
            # Update Prometheus metrics
            if PROMETHEUS_AVAILABLE:
                self.message_count.labels(
                    type=message.get('type', 'user'),
                    source=message.get('source', 'chat')
                ).inc()
                
                if analytics_data['response_time'] > 0:
                    self.chat_hub_latency_seconds.labels(
                        provider=analytics_data['llm_provider'],
                        model=analytics_data['model']
                    ).observe(analytics_data['response_time'] / 1000)  # Convert to seconds
                
                if analytics_data['ai_insights_count'] > 0:
                    confidence_level = 'high' if analytics_data['confidence_score'] > 0.8 else 'medium' if analytics_data['confidence_score'] > 0.5 else 'low'
                    self.ai_insights_count.labels(
                        type='contextual',
                        confidence_level=confidence_level
                    ).inc(analytics_data['ai_insights_count'])
                
                if analytics_data['token_usage'] > 0:
                    self.token_usage_counter.labels(
                        provider=analytics_data['llm_provider'],
                        model=analytics_data['model'],
                        operation='chat'
                    ).inc(analytics_data['token_usage'])
            
            # Keep only recent data (last 24 hours)
            cutoff_time = timestamp - timedelta(hours=24)
            self.conversation_metrics = [
                m for m in self.conversation_metrics 
                if m['timestamp'] > cutoff_time
            ]
            
            return {'success': True, 'analytics_collected': True}
            
        except Exception as e:
            logger.error(f"Failed to collect message analytics: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _collect_llm_performance(self, context: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Collect LLM performance metrics."""
        try:
            response = context.get('response', {})
            timestamp = datetime.utcnow()
            
            performance_data = {
                'timestamp': timestamp,
                'provider': response.get('provider', 'unknown'),
                'model': response.get('model', 'unknown'),
                'response_time': response.get('processing_time', 0),
                'token_usage': response.get('token_usage', 0),
                'tokens_per_second': response.get('tokens_per_second', 0),
                'error_rate': 1.0 if response.get('error') else 0.0,
                'confidence_score': response.get('confidence', 0.0),
                'context_length': response.get('context_length', 0),
                'completion_reason': response.get('completion_reason', 'unknown')
            }
            
            self.llm_performance_data.append(performance_data)
            
            # Keep only recent data
            cutoff_time = timestamp - timedelta(hours=24)
            self.llm_performance_data = [
                p for p in self.llm_performance_data 
                if p['timestamp'] > cutoff_time
            ]
            
            return {'success': True, 'llm_performance_collected': True}
            
        except Exception as e:
            logger.error(f"Failed to collect LLM performance: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _collect_memory_analytics(self, context: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Collect memory system analytics."""
        try:
            memory_data = context.get('memory', {})
            timestamp = datetime.utcnow()
            
            analytics_data = {
                'timestamp': timestamp,
                'user_id': user_context.get('userId'),
                'memory_type': memory_data.get('type', 'unknown'),
                'confidence': memory_data.get('confidence', 0.0),
                'semantic_cluster': memory_data.get('semantic_cluster', 'unknown'),
                'relationship_count': len(memory_data.get('relationships', [])),
                'tag_count': len(memory_data.get('tags', [])),
                'content_length': len(memory_data.get('content', '')),
                'source': memory_data.get('source', 'unknown')
            }
            
            self.memory_analytics.append(analytics_data)
            
            # Update Prometheus metrics
            if PROMETHEUS_AVAILABLE:
                self.memory_operations.labels(
                    operation='store',
                    success='true'
                ).inc()
            
            # Keep only recent data
            cutoff_time = timestamp - timedelta(hours=24)
            self.memory_analytics = [
                m for m in self.memory_analytics 
                if m['timestamp'] > cutoff_time
            ]
            
            return {'success': True, 'memory_analytics_collected': True}
            
        except Exception as e:
            logger.error(f"Failed to collect memory analytics: {e}")
            if PROMETHEUS_AVAILABLE:
                self.memory_operations.labels(
                    operation='store',
                    success='false'
                ).inc()
            return {'success': False, 'error': str(e)}
    
    async def _track_memory_retrieval(self, context: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Track memory retrieval performance."""
        try:
            query = context.get('query', {})
            results = context.get('results', [])
            retrieval_time = context.get('retrieval_time', 0)
            
            if PROMETHEUS_AVAILABLE and retrieval_time > 0:
                self.memory_retrieval_latency.labels(
                    query_type=query.get('type', 'semantic')
                ).observe(retrieval_time / 1000)  # Convert to seconds
                
                self.memory_operations.labels(
                    operation='retrieve',
                    success='true' if results else 'false'
                ).inc()
            
            return {'success': True, 'retrieval_tracked': True}
            
        except Exception as e:
            logger.error(f"Failed to track memory retrieval: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _track_ui_engagement(self, context: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Track user engagement with UI components."""
        try:
            component = context.get('component', {})
            timestamp = datetime.utcnow()
            
            engagement_data = {
                'timestamp': timestamp,
                'user_id': user_context.get('userId'),
                'component_type': component.get('type', 'unknown'),
                'component_id': component.get('id', 'unknown'),
                'interaction_type': context.get('interaction_type', 'view'),
                'duration': context.get('duration', 0),
                'success': context.get('success', True),
                'error_message': context.get('error_message')
            }
            
            self.user_engagement_data.append(engagement_data)
            
            # Keep only recent data
            cutoff_time = timestamp - timedelta(hours=24)
            self.user_engagement_data = [
                e for e in self.user_engagement_data 
                if e['timestamp'] > cutoff_time
            ]
            
            return {'success': True, 'engagement_tracked': True}
            
        except Exception as e:
            logger.error(f"Failed to track UI engagement: {e}")
            return {'success': False, 'error': str(e)}
    
    # API endpoints for AG-UI data
    async def get_conversation_analytics(self, timeframe: str = '24h', user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get conversation analytics data for AG-UI charts."""
        try:
            # Filter by timeframe
            now = datetime.utcnow()
            if timeframe == '1h':
                cutoff = now - timedelta(hours=1)
            elif timeframe == '24h':
                cutoff = now - timedelta(hours=24)
            elif timeframe == '7d':
                cutoff = now - timedelta(days=7)
            elif timeframe == '30d':
                cutoff = now - timedelta(days=30)
            else:
                cutoff = now - timedelta(hours=24)
            
            filtered_data = [
                m for m in self.conversation_metrics 
                if m['timestamp'] > cutoff and (not user_id or m.get('user_id') == user_id)
            ]
            
            # Convert datetime objects to ISO strings for JSON serialization
            for item in filtered_data:
                if isinstance(item['timestamp'], datetime):
                    item['timestamp'] = item['timestamp'].isoformat()
            
            return filtered_data
            
        except Exception as e:
            logger.error(f"Failed to get conversation analytics: {e}")
            return []
    
    async def get_memory_network_data(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get memory network data for AG-UI network visualization."""
        try:
            # Filter memory data
            filtered_memories = [
                m for m in self.memory_analytics 
                if not user_id or m.get('user_id') == user_id
            ]
            
            # Group by semantic cluster
            clusters = {}
            for memory in filtered_memories:
                cluster = memory.get('semantic_cluster', 'unknown')
                if cluster not in clusters:
                    clusters[cluster] = []
                clusters[cluster].append(memory)
            
            # Create network nodes and edges
            nodes = []
            edges = []
            
            for cluster_name, memories in clusters.items():
                # Create cluster node
                cluster_node = {
                    'id': f'cluster_{cluster_name}',
                    'label': cluster_name.replace('_', ' ').title(),
                    'type': 'cluster',
                    'size': len(memories),
                    'color': self._get_cluster_color(cluster_name)
                }
                nodes.append(cluster_node)
                
                # Create memory nodes
                for memory in memories:
                    memory_node = {
                        'id': f"memory_{memory.get('timestamp', '').replace(':', '_')}",
                        'label': memory.get('memory_type', 'unknown'),
                        'type': 'memory',
                        'confidence': memory.get('confidence', 0.0),
                        'cluster': cluster_name
                    }
                    nodes.append(memory_node)
                    
                    # Create edge to cluster
                    edges.append({
                        'from': memory_node['id'],
                        'to': cluster_node['id'],
                        'weight': memory.get('confidence', 0.0)
                    })
            
            return {
                'nodes': nodes,
                'edges': edges,
                'clusters': list(clusters.keys()),
                'total_memories': len(filtered_memories)
            }
            
        except Exception as e:
            logger.error(f"Failed to get memory network data: {e}")
            return {'nodes': [], 'edges': [], 'clusters': [], 'total_memories': 0}
    
    async def get_user_engagement_grid_data(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get user engagement data for AG-UI data grids."""
        try:
            filtered_data = [
                e for e in self.user_engagement_data 
                if not user_id or e.get('user_id') == user_id
            ]
            
            # Convert datetime objects to ISO strings
            for item in filtered_data:
                if isinstance(item['timestamp'], datetime):
                    item['timestamp'] = item['timestamp'].isoformat()
            
            return filtered_data
            
        except Exception as e:
            logger.error(f"Failed to get user engagement data: {e}")
            return []
    
    async def get_prometheus_metrics(self) -> str:
        """Get Prometheus metrics in text format."""
        if not PROMETHEUS_AVAILABLE:
            return "# Prometheus client not available\n"
        
        try:
            return generate_latest().decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to generate Prometheus metrics: {e}")
            return f"# Error generating metrics: {e}\n"
    
    async def _track_collaboration_session(self, context: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Track collaboration session analytics."""
        try:
            session_data = context.get('session', {})
            timestamp = datetime.utcnow()
            
            collaboration_data = {
                'timestamp': timestamp,
                'session_id': session_data.get('session_id'),
                'conversation_id': session_data.get('conversation_id'),
                'session_type': session_data.get('session_type', 'chat'),
                'participant_count': len(session_data.get('participants', [])),
                'initiator_id': user_context.get('userId'),
                'action': context.get('action', 'start')  # start, join, leave, end
            }
            
            # Update Prometheus metrics
            if PROMETHEUS_AVAILABLE:
                if collaboration_data['action'] == 'start':
                    self.collaboration_sessions.labels(
                        session_type=collaboration_data['session_type'],
                        conversation_id=collaboration_data['conversation_id']
                    ).inc()
                    
                    self.collaboration_participants.labels(
                        session_type=collaboration_data['session_type']
                    ).set(collaboration_data['participant_count'])
            
            return {'success': True, 'collaboration_tracked': True}
            
        except Exception as e:
            logger.error(f"Failed to track collaboration session: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _track_presence_update(self, context: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Track user presence updates."""
        try:
            presence_data = context.get('presence', {})
            
            # Update Prometheus metrics
            if PROMETHEUS_AVAILABLE:
                self.presence_updates.labels(
                    status=presence_data.get('status', 'unknown'),
                    user_type=user_context.get('user_type', 'regular')
                ).inc()
            
            return {'success': True, 'presence_tracked': True}
            
        except Exception as e:
            logger.error(f"Failed to track presence update: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _track_typing_indicator(self, context: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Track typing indicator events."""
        try:
            typing_data = context.get('typing', {})
            
            # Update Prometheus metrics
            if PROMETHEUS_AVAILABLE:
                action = 'start' if typing_data.get('is_typing', False) else 'stop'
                self.typing_indicators.labels(
                    conversation_id=typing_data.get('conversation_id', 'unknown'),
                    action=action
                ).inc()
            
            return {'success': True, 'typing_tracked': True}
            
        except Exception as e:
            logger.error(f"Failed to track typing indicator: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _track_collaborative_edit(self, context: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Track collaborative editing events."""
        try:
            edit_data = context.get('edit', {})
            
            # Update Prometheus metrics
            if PROMETHEUS_AVAILABLE:
                self.collaborative_edits.labels(
                    session_type=edit_data.get('session_type', 'chat'),
                    edit_type=edit_data.get('edit_type', 'text')
                ).inc()
            
            return {'success': True, 'collaborative_edit_tracked': True}
            
        except Exception as e:
            logger.error(f"Failed to track collaborative edit: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _track_websocket_connection(self, context: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Track WebSocket connection events."""
        try:
            connection_data = context.get('connection', {})
            
            # Update Prometheus metrics
            if PROMETHEUS_AVAILABLE:
                action = context.get('action', 'connect')  # connect, disconnect
                if action == 'connect':
                    self.websocket_connections.labels(
                        authenticated=str(connection_data.get('authenticated', False)),
                        conversation_id=connection_data.get('conversation_id', 'none')
                    ).inc()
                elif action == 'disconnect':
                    self.websocket_connections.labels(
                        authenticated=str(connection_data.get('authenticated', False)),
                        conversation_id=connection_data.get('conversation_id', 'none')
                    ).dec()
            
            return {'success': True, 'websocket_tracked': True}
            
        except Exception as e:
            logger.error(f"Failed to track WebSocket connection: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_collaboration_analytics(self, timeframe: str = '24h', conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """Get collaboration analytics data for AG-UI visualization."""
        try:
            # This would typically query a database, but for now we'll return sample data
            # based on the metrics we're tracking
            
            now = datetime.utcnow()
            if timeframe == '1h':
                cutoff = now - timedelta(hours=1)
            elif timeframe == '24h':
                cutoff = now - timedelta(hours=24)
            elif timeframe == '7d':
                cutoff = now - timedelta(days=7)
            else:
                cutoff = now - timedelta(hours=24)
            
            # Generate sample collaboration data
            collaboration_data = {
                'active_sessions': 3,
                'total_participants': 8,
                'session_types': {
                    'chat': 2,
                    'screen_share': 1,
                    'collaborative_edit': 0
                },
                'presence_status': {
                    'online': 5,
                    'away': 2,
                    'offline': 1
                },
                'typing_activity': {
                    'active_typers': 2,
                    'total_typing_events': 45
                },
                'collaborative_edits': {
                    'total_edits': 12,
                    'edit_types': {
                        'text': 8,
                        'code': 3,
                        'markdown': 1
                    }
                },
                'websocket_connections': {
                    'total_connections': 6,
                    'authenticated_connections': 5
                }
            }
            
            return collaboration_data
            
        except Exception as e:
            logger.error(f"Failed to get collaboration analytics: {e}")
            return {}
    
    def _get_cluster_color(self, cluster_name: str) -> str:
        """Get color for semantic cluster visualization."""
        colors = {
            'programming_preferences': '#3b82f6',
            'current_projects': '#10b981',
            'technical_skills': '#f59e0b',
            'communication_style': '#8b5cf6',
            'user_created': '#ef4444',
            'unknown': '#6b7280'
        }
        return colors.get(cluster_name, '#6b7280')
    
    async def start(self):
        """Start the analytics extension."""
        logger.info("Analytics Dashboard Extension started")
        return True
    
    async def stop(self):
        """Stop the analytics extension."""
        logger.info("Analytics Dashboard Extension stopped")
        return True
    
    async def get_status(self) -> Dict[str, Any]:
        """Get extension status."""
        return {
            'name': self.name,
            'version': self.version,
            'status': 'running',
            'metrics_collected': {
                'conversations': len(self.conversation_metrics),
                'memories': len(self.memory_analytics),
                'engagement_events': len(self.user_engagement_data),
                'llm_performance': len(self.llm_performance_data)
            },
            'prometheus_available': PROMETHEUS_AVAILABLE
        }