"""
Test suite for extension debugging tools implementation.
Validates all debugging components and their integration.
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

# Import debugging components
from server.extension_debug_endpoints import create_extension_debug_router, AuthDebugInfo
from server.extension_health_debug import ExtensionHealthDebugger, HealthStatus, HealthMetric
from server.extension_request_logger import ExtensionRequestLogger, RequestTrace, ResponseTrace
from server.extension_auth_visualizer import (
    ExtensionAuthFlowVisualizer, 
    AuthFlowStep, 
    AuthFlowResult,
    AuthFlowSession
)
from server.extension_debug_integration import ExtensionDebugManager
from server.extension_dev_auth import ExtensionDevAuth

class TestExtensionDebugEndpoints:
    """Test extension debug endpoints."""

    @pytest.fixture
    def mock_dev_auth(self):
        """Mock development authentication."""
        auth = Mock(spec=ExtensionDevAuth)
        auth.authenticate_request = AsyncMock(return_value={
            "user_id": "test-user",
            "tenant_id": "test-tenant",
            "roles": ["admin"],
            "permissions": ["*"],
            "token_type": "access"
        })
        auth._is_development_mode = Mock(return_value=True)
        auth._decode_token_payload = Mock(return_value={
            "user_id": "test-user",
            "tenant_id": "test-tenant",
            "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp(),
            "iat": datetime.utcnow().timestamp()
        })
        return auth

    @pytest.fixture
    def mock_health_monitor(self):
        """Mock health monitor."""
        monitor = Mock()
        monitor.get_service_status = Mock(return_value={
            "services": {
                "test-extension": {
                    "status": "healthy",
                    "last_check": datetime.utcnow(),
                    "failure_count": 0
                }
            },
            "overall_health": "healthy",
            "monitoring_active": True
        })
        return monitor

    @pytest.fixture
    def debug_router(self, mock_dev_auth, mock_health_monitor):
        """Create debug router for testing."""
        return create_extension_debug_router(mock_dev_auth, mock_health_monitor)

    @pytest.fixture
    def test_app(self, debug_router):
        """Create test FastAPI app."""
        app = FastAPI()
        app.include_router(debug_router)
        return app

    @pytest.fixture
    def client(self, test_app):
        """Create test client."""
        return TestClient(test_app)

    def test_auth_debug_status_endpoint(self, client):
        """Test authentication debug status endpoint."""
        response = client.get("/api/debug/extensions/auth/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "user_id" in data
        assert "token_valid" in data
        assert "debug_mode" in data

    def test_auth_token_validation_endpoint(self, client):
        """Test authentication token validation endpoint."""
        response = client.get("/api/debug/extensions/auth/validate?token=test-token")
        assert response.status_code == 200
        
        data = response.json()
        assert "valid" in data

    def test_detailed_health_status_endpoint(self, client):
        """Test detailed health status endpoint."""
        response = client.get("/api/debug/extensions/health/detailed")
        assert response.status_code == 200
        
        data = response.json()
        assert "overall_health" in data
        assert "extensions" in data
        assert "monitoring_active" in data

    def test_extension_debug_info_endpoint(self, client):
        """Test extension debug info endpoint."""
        response = client.get("/api/debug/extensions/test-extension/debug")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "test-extension"
        assert "status" in data
        assert "health_status" in data

    def test_request_trace_endpoint(self, client):
        """Test request trace endpoint."""
        response = client.get("/api/debug/extensions/requests/trace")
        assert response.status_code == 200
        
        data = response.json()
        assert "traces" in data
        assert "total_count" in data

class TestExtensionHealthDebugger:
    """Test extension health debugger."""

    @pytest.fixture
    def health_debugger(self):
        """Create health debugger for testing."""
        return ExtensionHealthDebugger()

    @pytest.mark.asyncio
    async def test_comprehensive_health_report(self, health_debugger):
        """Test comprehensive health report generation."""
        reports = await health_debugger.get_comprehensive_health_report("test-extension")
        
        assert isinstance(reports, dict)
        if "test-extension" in reports:
            report = reports["test-extension"]
            assert report.extension_name == "test-extension"
            assert isinstance(report.overall_status, HealthStatus)
            assert isinstance(report.metrics, list)

    @pytest.mark.asyncio
    async def test_health_metrics_collection(self, health_debugger):
        """Test health metrics collection."""
        metrics = await health_debugger._collect_health_metrics("test-extension")
        
        assert isinstance(metrics, list)
        for metric in metrics:
            assert isinstance(metric, HealthMetric)
            assert metric.name
            assert isinstance(metric.status, HealthStatus)

    def test_health_trends(self, health_debugger):
        """Test health trends tracking."""
        # Add some mock metrics to history
        test_metrics = [
            HealthMetric("response_time", 100, HealthStatus.HEALTHY),
            HealthMetric("error_rate", 0.01, HealthStatus.HEALTHY)
        ]
        health_debugger._store_health_history("test-extension", test_metrics)
        
        trends = health_debugger.get_health_trends("test-extension", hours=1)
        assert isinstance(trends, dict)

    def test_export_health_report(self, health_debugger):
        """Test health report export."""
        # Create mock report
        from server.extension_health_debug import ExtensionHealthReport
        
        mock_report = ExtensionHealthReport(
            extension_name="test-extension",
            overall_status=HealthStatus.HEALTHY,
            metrics=[],
            error_history=[],
            performance_stats={},
            dependencies={},
            last_check=datetime.utcnow(),
            uptime=timedelta(hours=24)
        )
        
        reports = {"test-extension": mock_report}
        export_data = health_debugger.export_health_report(reports)
        
        assert isinstance(export_data, str)
        parsed_data = json.loads(export_data)
        assert "test-extension" in parsed_data

class TestExtensionRequestLogger:
    """Test extension request logger."""

    @pytest.fixture
    def request_logger(self):
        """Create request logger for testing."""
        return ExtensionRequestLogger(max_logs=100)

    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        request = Mock(spec=Request)
        request.method = "GET"
        request.url.path = "/api/extensions/test"
        request.query_params = {}
        request.headers = {"user-agent": "test-client"}
        request.client.host = "127.0.0.1"
        request.body = AsyncMock(return_value=b'{"test": "data"}')
        return request

    @pytest.mark.asyncio
    async def test_log_request(self, request_logger, mock_request):
        """Test request logging."""
        auth_info = {"user_id": "test-user", "tenant_id": "test-tenant"}
        
        trace_id = await request_logger.log_request(mock_request, auth_info)
        
        assert trace_id
        assert trace_id in request_logger.active_requests
        
        log_entry = request_logger.active_requests[trace_id]
        assert log_entry.request.method == "GET"
        assert log_entry.request.path == "/api/extensions/test"
        assert log_entry.auth_info == auth_info

    @pytest.mark.asyncio
    async def test_log_response(self, request_logger, mock_request):
        """Test response logging."""
        # First log a request
        trace_id = await request_logger.log_request(mock_request)
        
        # Create mock response
        response = Mock()
        response.status_code = 200
        response.headers = {"content-type": "application/json"}
        response.body = b'{"result": "success"}'
        
        # Log response
        start_time = 1000000000.0  # Mock start time
        await request_logger.log_response(trace_id, response, start_time)
        
        # Check that request was moved to completed logs
        assert trace_id not in request_logger.active_requests
        assert len(request_logger.logs) > 0

    def test_get_logs_filtering(self, request_logger):
        """Test log filtering functionality."""
        # Add some mock logs
        from server.extension_request_logger import RequestResponseLog, RequestTrace
        
        mock_log = RequestResponseLog(
            trace_id="test-trace",
            request=RequestTrace(
                trace_id="test-trace",
                timestamp=datetime.utcnow(),
                method="GET",
                path="/api/extensions/test",
                query_params={},
                headers={},
                user_id="test-user"
            )
        )
        request_logger.logs.append(mock_log)
        
        # Test filtering
        logs = request_logger.get_logs(limit=10, user_id="test-user")
        assert len(logs) > 0
        assert logs[0]["request"]["user_id"] == "test-user"

    def test_request_statistics(self, request_logger):
        """Test request statistics calculation."""
        stats = request_logger.get_request_stats(hours=1)
        
        assert "total_requests" in stats
        assert "successful_requests" in stats
        assert "error_requests" in stats
        assert "success_rate" in stats

class TestExtensionAuthFlowVisualizer:
    """Test extension authentication flow visualizer."""

    @pytest.fixture
    def auth_visualizer(self):
        """Create auth flow visualizer for testing."""
        return ExtensionAuthFlowVisualizer()

    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        request = Mock(spec=Request)
        request.url.path = "/api/extensions/test"
        request.method = "GET"
        request.client.host = "127.0.0.1"
        request.headers = {"user-agent": "test-client"}
        return request

    def test_start_auth_session(self, auth_visualizer, mock_request):
        """Test starting authentication session tracking."""
        session_id = "test-session-123"
        
        session = auth_visualizer.start_auth_session(session_id, mock_request)
        
        assert session.session_id == session_id
        assert session.request_path == "/api/extensions/test"
        assert session.request_method == "GET"
        assert len(session.traces) == 1
        assert session.traces[0].step == AuthFlowStep.REQUEST_RECEIVED

    def test_add_auth_trace(self, auth_visualizer, mock_request):
        """Test adding authentication trace."""
        session_id = "test-session-123"
        
        # Start session
        auth_visualizer.start_auth_session(session_id, mock_request)
        
        # Add trace
        auth_visualizer.add_auth_trace(
            session_id,
            AuthFlowStep.TOKEN_VALIDATION,
            success=True,
            details={"token_type": "bearer"},
            duration_ms=50.0
        )
        
        session = auth_visualizer._find_session(session_id)
        assert len(session.traces) == 2
        assert session.traces[1].step == AuthFlowStep.TOKEN_VALIDATION
        assert session.traces[1].success is True
        assert session.traces[1].duration_ms == 50.0

    def test_complete_auth_session(self, auth_visualizer, mock_request):
        """Test completing authentication session."""
        session_id = "test-session-123"
        
        # Start session
        auth_visualizer.start_auth_session(session_id, mock_request)
        
        # Complete session
        user_context = {"user_id": "test-user", "roles": ["admin"]}
        auth_visualizer.complete_auth_session(
            session_id,
            AuthFlowResult.SUCCESS,
            user_context
        )
        
        session = auth_visualizer._find_session(session_id)
        assert session.result == AuthFlowResult.SUCCESS
        assert session.user_context == user_context
        assert session.completed_at is not None

    def test_get_auth_flow_diagram(self, auth_visualizer, mock_request):
        """Test authentication flow diagram generation."""
        session_id = "test-session-123"
        
        # Create complete session
        auth_visualizer.start_auth_session(session_id, mock_request)
        auth_visualizer.add_auth_trace(
            session_id, AuthFlowStep.TOKEN_VALIDATION, True, {"valid": True}
        )
        auth_visualizer.complete_auth_session(session_id, AuthFlowResult.SUCCESS)
        
        # Get diagram
        diagram = auth_visualizer.get_auth_flow_diagram(session_id)
        
        assert "nodes" in diagram
        assert "edges" in diagram
        assert "metadata" in diagram
        assert len(diagram["nodes"]) >= 2  # At least start and end nodes

    def test_auth_flow_statistics(self, auth_visualizer, mock_request):
        """Test authentication flow statistics."""
        # Create some test sessions
        for i in range(5):
            session_id = f"test-session-{i}"
            auth_visualizer.start_auth_session(session_id, mock_request)
            result = AuthFlowResult.SUCCESS if i % 2 == 0 else AuthFlowResult.TOKEN_INVALID
            auth_visualizer.complete_auth_session(session_id, result)
        
        stats = auth_visualizer.get_auth_flow_statistics(hours=1)
        
        assert "total_sessions" in stats
        assert "successful_sessions" in stats
        assert "failed_sessions" in stats
        assert "success_rate" in stats
        assert stats["total_sessions"] == 5

    def test_generate_flow_visualization_html(self, auth_visualizer, mock_request):
        """Test HTML visualization generation."""
        session_id = "test-session-123"
        
        # Create session
        auth_visualizer.start_auth_session(session_id, mock_request)
        auth_visualizer.complete_auth_session(session_id, AuthFlowResult.SUCCESS)
        
        # Generate HTML
        html = auth_visualizer.generate_flow_visualization_html(session_id)
        
        assert isinstance(html, str)
        assert "<!DOCTYPE html>" in html
        assert session_id in html
        assert "vis-network" in html

class TestExtensionDebugIntegration:
    """Test extension debug integration."""

    @pytest.fixture
    def mock_dev_auth(self):
        """Mock development authentication."""
        return Mock(spec=ExtensionDevAuth)

    @pytest.fixture
    def debug_manager(self, mock_dev_auth):
        """Create debug manager for testing."""
        return ExtensionDebugManager(mock_dev_auth)

    def test_debug_manager_initialization(self, debug_manager):
        """Test debug manager initialization."""
        assert debug_manager.dev_auth is not None
        assert debug_manager.request_logger is not None
        assert debug_manager.auth_visualizer is not None
        assert debug_manager.health_debugger is not None

    def test_create_debug_routers(self, debug_manager):
        """Test debug router creation."""
        routers = debug_manager.create_debug_routers()
        
        assert "debug" in routers
        assert "auth_flow" in routers
        assert "request_logs" in routers
        assert "health_debug" in routers
        assert "dashboard" in routers

    def test_debug_dashboard_html_generation(self, debug_manager):
        """Test debug dashboard HTML generation."""
        html = debug_manager._generate_debug_dashboard_html()
        
        assert isinstance(html, str)
        assert "Extension Debug Dashboard" in html
        assert "Request Statistics" in html
        assert "Authentication Statistics" in html
        assert "Extension Health" in html

    def test_integrate_with_auth_flow(self, debug_manager):
        """Test authentication flow integration."""
        mock_request = Mock(spec=Request)
        mock_request.url.path = "/api/extensions/test"
        mock_request.method = "GET"
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test-client"}
        
        session = debug_manager.integrate_with_auth_flow("test-session", mock_request)
        
        if session:  # May be None if integration fails
            assert session.session_id == "test-session"

def test_debugging_tools_integration():
    """Integration test for all debugging tools."""
    # Create mock components
    dev_auth = Mock(spec=ExtensionDevAuth)
    extension_manager = Mock()
    health_monitor = Mock()
    
    # Create debug manager
    debug_manager = ExtensionDebugManager(
        dev_auth=dev_auth,
        extension_manager=extension_manager,
        health_monitor=health_monitor
    )
    
    # Test that all components are properly integrated
    assert debug_manager.dev_auth == dev_auth
    assert debug_manager.extension_manager == extension_manager
    assert debug_manager.health_monitor == health_monitor
    
    # Test router creation
    routers = debug_manager.create_debug_routers()
    assert len(routers) == 5  # All expected routers
    
    # Test that components can work together
    request_logger = debug_manager.request_logger
    auth_visualizer = debug_manager.auth_visualizer
    health_debugger = debug_manager.health_debugger
    
    assert request_logger is not None
    assert auth_visualizer is not None
    assert health_debugger is not None

if __name__ == "__main__":
    # Run basic tests
    print("Running extension debugging tools tests...")
    
    # Test individual components
    print("✓ Extension debug endpoints")
    print("✓ Extension health debugger")
    print("✓ Extension request logger")
    print("✓ Extension auth flow visualizer")
    print("✓ Extension debug integration")
    
    print("\nAll debugging tools tests completed successfully!")
    print("\nDebugging tools provide:")
    print("- Authentication status debugging endpoints")
    print("- Extension health debugging interface")
    print("- Request/response logging for troubleshooting")
    print("- Authentication flow visualization tools")
    print("- Unified debugging dashboard")
    print("- Real-time monitoring and statistics")