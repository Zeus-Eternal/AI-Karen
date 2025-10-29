"""
Extension debugging tools integration.
Combines all debugging components into a unified debugging interface.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse

from server.extension_debug_endpoints import create_extension_debug_router
from server.extension_health_debug import ExtensionHealthDebugger
from server.extension_request_logger import (
    ExtensionRequestLogger, 
    ExtensionRequestLoggingMiddleware,
    extension_request_logger
)
from server.extension_auth_visualizer import (
    ExtensionAuthFlowVisualizer,
    create_auth_visualization_router,
    extension_auth_visualizer
)
from server.extension_dev_auth import ExtensionDevAuth

logger = logging.getLogger(__name__)

class ExtensionDebugManager:
    """Unified extension debugging manager."""

    def __init__(
        self,
        dev_auth: ExtensionDevAuth,
        extension_manager=None,
        health_monitor=None
    ):
        self.dev_auth = dev_auth
        self.extension_manager = extension_manager
        self.health_monitor = health_monitor
        
        # Initialize debugging components
        self.request_logger = extension_request_logger
        self.auth_visualizer = extension_auth_visualizer
        self.health_debugger = ExtensionHealthDebugger(
            extension_manager=extension_manager,
            health_monitor=health_monitor
        )
        
        # Setup request logging filters
        self._setup_logging_filters()

    def _setup_logging_filters(self):
        """Setup default logging filters."""
        # Log all debug requests
        def debug_requests_filter(log_entry):
            return (
                log_entry.request.path.startswith('/api/debug/') or
                log_entry.request.path.startswith('/api/extensions/')
            )
        
        # Log authentication failures
        def auth_failure_filter(log_entry):
            return (
                log_entry.response and 
                log_entry.response.status_code == 403
            )
        
        self.request_logger.add_filter(debug_requests_filter)
        self.request_logger.add_filter(auth_failure_filter)

    def create_debug_routers(self) -> Dict[str, APIRouter]:
        """Create all debug routers."""
        routers = {}
        
        # Main debug endpoints
        routers['debug'] = create_extension_debug_router(
            dev_auth=self.dev_auth,
            health_monitor=self.health_monitor
        )
        
        # Authentication flow visualization
        routers['auth_flow'] = create_auth_visualization_router(
            visualizer=self.auth_visualizer
        )
        
        # Request logging endpoints
        routers['request_logs'] = self._create_request_logging_router()
        
        # Health debugging endpoints
        routers['health_debug'] = self._create_health_debug_router()
        
        # Debug dashboard
        routers['dashboard'] = self._create_debug_dashboard_router()
        
        return routers

    def _create_request_logging_router(self) -> APIRouter:
        """Create request logging debug router."""
        router = APIRouter(prefix="/api/debug/requests", tags=["request-logging"])
        
        @router.get("/logs")
        async def get_request_logs(
            limit: int = 100,
            extension_name: Optional[str] = None,
            status_code: Optional[int] = None,
            user_id: Optional[str] = None
        ):
            """Get filtered request logs."""
            return self.request_logger.get_logs(
                limit=limit,
                extension_name=extension_name,
                status_code=status_code,
                user_id=user_id
            )
        
        @router.get("/stats")
        async def get_request_stats(hours: int = 24):
            """Get request statistics."""
            return self.request_logger.get_request_stats(hours)
        
        @router.get("/trace/{trace_id}")
        async def get_trace_details(trace_id: str):
            """Get detailed trace information."""
            trace_details = self.request_logger.get_trace_details(trace_id)
            if not trace_details:
                return {"error": f"Trace {trace_id} not found"}
            return trace_details
        
        @router.delete("/logs")
        async def clear_request_logs(older_than_hours: Optional[int] = None):
            """Clear request logs."""
            self.request_logger.clear_logs(older_than_hours)
            return {"message": "Request logs cleared"}
        
        return router

    def _create_health_debug_router(self) -> APIRouter:
        """Create health debugging router."""
        router = APIRouter(prefix="/api/debug/health", tags=["health-debug"])
        
        @router.get("/comprehensive")
        async def get_comprehensive_health(extension_name: Optional[str] = None):
            """Get comprehensive health report."""
            reports = await self.health_debugger.get_comprehensive_health_report(extension_name)
            
            # Convert reports to JSON-serializable format
            json_reports = {}
            for name, report in reports.items():
                json_reports[name] = {
                    "extension_name": report.extension_name,
                    "overall_status": report.overall_status.value,
                    "metrics": [
                        {
                            "name": m.name,
                            "value": m.value,
                            "status": m.status.value,
                            "threshold": m.threshold,
                            "unit": m.unit,
                            "description": m.description,
                            "last_updated": m.last_updated.isoformat()
                        }
                        for m in report.metrics
                    ],
                    "error_history": report.error_history,
                    "performance_stats": report.performance_stats,
                    "dependencies": {k: v.value for k, v in report.dependencies.items()},
                    "last_check": report.last_check.isoformat(),
                    "uptime_hours": report.uptime.total_seconds() / 3600,
                    "recovery_info": report.recovery_info
                }
            
            return json_reports
        
        @router.get("/trends/{extension_name}")
        async def get_health_trends(extension_name: str, hours: int = 24):
            """Get health trends for extension."""
            return self.health_debugger.get_health_trends(extension_name, hours)
        
        @router.get("/export")
        async def export_health_reports(extension_name: Optional[str] = None):
            """Export health reports."""
            reports = await self.health_debugger.get_comprehensive_health_report(extension_name)
            return {"export": self.health_debugger.export_health_report(reports)}
        
        return router

    def _create_debug_dashboard_router(self) -> APIRouter:
        """Create debug dashboard router."""
        router = APIRouter(prefix="/api/debug/dashboard", tags=["debug-dashboard"])
        
        @router.get("/", response_class=HTMLResponse)
        async def debug_dashboard():
            """Main debug dashboard."""
            return self._generate_debug_dashboard_html()
        
        @router.get("/summary")
        async def get_debug_summary():
            """Get debug summary information."""
            try:
                # Get recent request stats
                request_stats = self.request_logger.get_request_stats(hours=1)
                
                # Get auth flow stats
                auth_stats = self.auth_visualizer.get_auth_flow_statistics(hours=1)
                
                # Get health status
                health_reports = await self.health_debugger.get_comprehensive_health_report()
                
                # Calculate overall health
                healthy_extensions = sum(
                    1 for report in health_reports.values()
                    if report.overall_status.value == "healthy"
                )
                total_extensions = len(health_reports)
                
                summary = {
                    "timestamp": request_stats.get("timestamp"),
                    "request_stats": {
                        "total_requests": request_stats.get("total_requests", 0),
                        "error_requests": request_stats.get("error_requests", 0),
                        "success_rate": request_stats.get("success_rate", 0),
                        "avg_response_time": request_stats.get("average_response_time_ms", 0)
                    },
                    "auth_stats": {
                        "total_sessions": auth_stats.get("total_sessions", 0),
                        "failed_sessions": auth_stats.get("failed_sessions", 0),
                        "success_rate": auth_stats.get("success_rate", 0),
                        "avg_duration": auth_stats.get("average_duration_ms", 0)
                    },
                    "health_stats": {
                        "healthy_extensions": healthy_extensions,
                        "total_extensions": total_extensions,
                        "health_rate": healthy_extensions / total_extensions if total_extensions > 0 else 0
                    }
                }
                
                return summary
                
            except Exception as e:
                logger.error(f"Error getting debug summary: {e}")
                return {"error": str(e)}
        
        return router

    def _generate_debug_dashboard_html(self) -> str:
        """Generate HTML debug dashboard."""
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Extension Debug Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: #2196F3; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .section { background: white; padding: 20px; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .metric { text-align: center; padding: 15px; background: #f9f9f9; border-radius: 3px; }
        .metric h3 { margin: 0 0 10px 0; color: #333; }
        .metric .value { font-size: 2em; font-weight: bold; color: #2196F3; }
        .success { color: #4CAF50; }
        .error { color: #f44336; }
        .warning { color: #FF9800; }
        .nav { margin: 20px 0; }
        .nav a { display: inline-block; padding: 10px 20px; margin: 0 10px; background: #2196F3; color: white; text-decoration: none; border-radius: 3px; }
        .nav a:hover { background: #1976D2; }
        .refresh-btn { float: right; padding: 10px 20px; background: #4CAF50; color: white; border: none; border-radius: 3px; cursor: pointer; }
        .refresh-btn:hover { background: #45a049; }
    </style>
    <script>
        async function refreshDashboard() {
            try {
                const response = await fetch('/api/debug/dashboard/summary');
                const data = await response.json();
                updateDashboard(data);
            } catch (error) {
                console.error('Error refreshing dashboard:', error);
            }
        }
        
        function updateDashboard(data) {
            if (data.error) {
                document.getElementById('error-message').textContent = data.error;
                return;
            }
            
            // Update request metrics
            document.getElementById('total-requests').textContent = data.request_stats.total_requests;
            document.getElementById('error-requests').textContent = data.request_stats.error_requests;
            document.getElementById('request-success-rate').textContent = (data.request_stats.success_rate * 100).toFixed(1) + '%';
            document.getElementById('avg-response-time').textContent = data.request_stats.avg_response_time.toFixed(1) + 'ms';
            
            // Update auth metrics
            document.getElementById('total-auth-sessions').textContent = data.auth_stats.total_sessions;
            document.getElementById('failed-auth-sessions').textContent = data.auth_stats.failed_sessions;
            document.getElementById('auth-success-rate').textContent = (data.auth_stats.success_rate * 100).toFixed(1) + '%';
            document.getElementById('avg-auth-duration').textContent = data.auth_stats.avg_duration.toFixed(1) + 'ms';
            
            // Update health metrics
            document.getElementById('healthy-extensions').textContent = data.health_stats.healthy_extensions;
            document.getElementById('total-extensions').textContent = data.health_stats.total_extensions;
            document.getElementById('health-rate').textContent = (data.health_stats.health_rate * 100).toFixed(1) + '%';
            
            // Update timestamp
            document.getElementById('last-updated').textContent = new Date(data.timestamp).toLocaleString();
        }
        
        // Auto-refresh every 30 seconds
        setInterval(refreshDashboard, 30000);
        
        // Initial load
        window.onload = refreshDashboard;
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Extension Debug Dashboard</h1>
            <button class="refresh-btn" onclick="refreshDashboard()">Refresh</button>
            <p>Real-time monitoring and debugging for extension system</p>
        </div>
        
        <div id="error-message" class="error" style="display: none;"></div>
        
        <div class="nav">
            <a href="/api/debug/extensions/auth/status">Auth Status</a>
            <a href="/api/debug/extensions/health/detailed">Health Details</a>
            <a href="/api/debug/requests/logs">Request Logs</a>
            <a href="/api/debug/auth-flow/sessions">Auth Sessions</a>
            <a href="/api/debug/health/comprehensive">Health Reports</a>
        </div>
        
        <div class="section">
            <h2>Request Statistics (Last Hour)</h2>
            <div class="grid">
                <div class="metric">
                    <h3>Total Requests</h3>
                    <div class="value" id="total-requests">-</div>
                </div>
                <div class="metric">
                    <h3>Error Requests</h3>
                    <div class="value error" id="error-requests">-</div>
                </div>
                <div class="metric">
                    <h3>Success Rate</h3>
                    <div class="value success" id="request-success-rate">-</div>
                </div>
                <div class="metric">
                    <h3>Avg Response Time</h3>
                    <div class="value" id="avg-response-time">-</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>Authentication Statistics (Last Hour)</h2>
            <div class="grid">
                <div class="metric">
                    <h3>Auth Sessions</h3>
                    <div class="value" id="total-auth-sessions">-</div>
                </div>
                <div class="metric">
                    <h3>Failed Sessions</h3>
                    <div class="value error" id="failed-auth-sessions">-</div>
                </div>
                <div class="metric">
                    <h3>Success Rate</h3>
                    <div class="value success" id="auth-success-rate">-</div>
                </div>
                <div class="metric">
                    <h3>Avg Duration</h3>
                    <div class="value" id="avg-auth-duration">-</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>Extension Health</h2>
            <div class="grid">
                <div class="metric">
                    <h3>Healthy Extensions</h3>
                    <div class="value success" id="healthy-extensions">-</div>
                </div>
                <div class="metric">
                    <h3>Total Extensions</h3>
                    <div class="value" id="total-extensions">-</div>
                </div>
                <div class="metric">
                    <h3>Health Rate</h3>
                    <div class="value success" id="health-rate">-</div>
                </div>
                <div class="metric">
                    <h3>Last Updated</h3>
                    <div class="value" id="last-updated" style="font-size: 1em;">-</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>Quick Actions</h2>
            <div class="nav">
                <a href="/api/debug/extensions/auth/validate">Validate Token</a>
                <a href="/api/debug/requests/stats">Request Stats</a>
                <a href="/api/debug/health/comprehensive">Health Report</a>
                <a href="/api/debug/auth-flow/statistics">Auth Flow Stats</a>
            </div>
        </div>
    </div>
</body>
</html>
        """
        return html_template

    def setup_middleware(self, app: FastAPI):
        """Setup debugging middleware."""
        # Add request logging middleware
        app.add_middleware(
            ExtensionRequestLoggingMiddleware,
            request_logger=self.request_logger
        )

    def integrate_with_auth_flow(self, session_id: str, request: Request):
        """Integrate with authentication flow for visualization."""
        try:
            # Start auth session tracking
            session = self.auth_visualizer.start_auth_session(session_id, request)
            return session
        except Exception as e:
            logger.error(f"Error integrating with auth flow: {e}")
            return None

# Factory function to create debug manager
def create_extension_debug_manager(
    dev_auth: ExtensionDevAuth,
    extension_manager=None,
    health_monitor=None
) -> ExtensionDebugManager:
    """Create extension debug manager with all components."""
    return ExtensionDebugManager(
        dev_auth=dev_auth,
        extension_manager=extension_manager,
        health_monitor=health_monitor
    )