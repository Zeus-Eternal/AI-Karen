"""
Authentication flow visualization tools for extension debugging.
Provides visual representation of authentication flows and decision trees.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse

logger = logging.getLogger(__name__)

class AuthFlowStep(Enum):
    """Authentication flow step types."""
    REQUEST_RECEIVED = "request_received"
    TOKEN_EXTRACTION = "token_extraction"
    TOKEN_VALIDATION = "token_validation"
    PERMISSION_CHECK = "permission_check"
    USER_CONTEXT_CREATION = "user_context_creation"
    DEVELOPMENT_BYPASS = "development_bypass"
    SUCCESS = "success"
    FAILURE = "failure"

class AuthFlowResult(Enum):
    """Authentication flow results."""
    SUCCESS = "success"
    TOKEN_MISSING = "token_missing"
    TOKEN_INVALID = "token_invalid"
    TOKEN_EXPIRED = "token_expired"
    INSUFFICIENT_PERMISSIONS = "insufficient_permissions"
    DEVELOPMENT_BYPASS = "development_bypass"
    SYSTEM_ERROR = "system_error"

@dataclass
class AuthFlowTrace:
    """Authentication flow trace entry."""
    step: AuthFlowStep
    timestamp: datetime
    success: bool
    details: Dict[str, Any]
    error: Optional[str] = None
    duration_ms: float = 0

@dataclass
class AuthFlowSession:
    """Complete authentication flow session."""
    session_id: str
    request_path: str
    request_method: str
    client_ip: str
    user_agent: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[AuthFlowResult] = None
    traces: List[AuthFlowTrace] = None
    user_context: Optional[Dict[str, Any]] = None
    total_duration_ms: float = 0

    def __post_init__(self):
        if self.traces is None:
            self.traces = []

class ExtensionAuthFlowVisualizer:
    """Authentication flow visualization and analysis tool."""

    def __init__(self, max_sessions: int = 500):
        self.max_sessions = max_sessions
        self.sessions: List[AuthFlowSession] = []
        self.flow_patterns: Dict[str, int] = {}
        self.common_failures: Dict[AuthFlowResult, int] = {}

    def start_auth_session(
        self, 
        session_id: str, 
        request: Request
    ) -> AuthFlowSession:
        """Start tracking an authentication session."""
        try:
            session = AuthFlowSession(
                session_id=session_id,
                request_path=str(request.url.path),
                request_method=request.method,
                client_ip=request.client.host if request.client else "unknown",
                user_agent=request.headers.get("user-agent", "unknown"),
                started_at=datetime.utcnow()
            )
            
            # Add initial trace
            session.traces.append(AuthFlowTrace(
                step=AuthFlowStep.REQUEST_RECEIVED,
                timestamp=datetime.utcnow(),
                success=True,
                details={
                    "path": session.request_path,
                    "method": session.request_method,
                    "client_ip": session.client_ip
                }
            ))
            
            # Store session (keep only recent sessions)
            self.sessions.append(session)
            if len(self.sessions) > self.max_sessions:
                self.sessions = self.sessions[-self.max_sessions:]
            
            return session
            
        except Exception as e:
            logger.error(f"Error starting auth session {session_id}: {e}")
            raise

    def add_auth_trace(
        self, 
        session_id: str, 
        step: AuthFlowStep, 
        success: bool,
        details: Dict[str, Any],
        error: Optional[str] = None,
        duration_ms: float = 0
    ):
        """Add a trace entry to an authentication session."""
        try:
            session = self._find_session(session_id)
            if not session:
                logger.warning(f"Auth session {session_id} not found")
                return
            
            trace = AuthFlowTrace(
                step=step,
                timestamp=datetime.utcnow(),
                success=success,
                details=details,
                error=error,
                duration_ms=duration_ms
            )
            
            session.traces.append(trace)
            
        except Exception as e:
            logger.error(f"Error adding auth trace to session {session_id}: {e}")

    def complete_auth_session(
        self, 
        session_id: str, 
        result: AuthFlowResult,
        user_context: Optional[Dict[str, Any]] = None
    ):
        """Complete an authentication session."""
        try:
            session = self._find_session(session_id)
            if not session:
                logger.warning(f"Auth session {session_id} not found")
                return
            
            session.completed_at = datetime.utcnow()
            session.result = result
            session.user_context = user_context
            session.total_duration_ms = (
                session.completed_at - session.started_at
            ).total_seconds() * 1000
            
            # Add final trace
            session.traces.append(AuthFlowTrace(
                step=AuthFlowStep.SUCCESS if result == AuthFlowResult.SUCCESS else AuthFlowStep.FAILURE,
                timestamp=session.completed_at,
                success=result == AuthFlowResult.SUCCESS,
                details={
                    "result": result.value,
                    "total_duration_ms": session.total_duration_ms
                }
            ))
            
            # Update statistics
            self._update_flow_statistics(session)
            
        except Exception as e:
            logger.error(f"Error completing auth session {session_id}: {e}")

    def _find_session(self, session_id: str) -> Optional[AuthFlowSession]:
        """Find session by ID."""
        for session in reversed(self.sessions):
            if session.session_id == session_id:
                return session
        return None

    def _update_flow_statistics(self, session: AuthFlowSession):
        """Update flow pattern statistics."""
        try:
            # Create flow pattern signature
            pattern = " -> ".join([trace.step.value for trace in session.traces])
            self.flow_patterns[pattern] = self.flow_patterns.get(pattern, 0) + 1
            
            # Update failure statistics
            if session.result and session.result != AuthFlowResult.SUCCESS:
                self.common_failures[session.result] = self.common_failures.get(session.result, 0) + 1
                
        except Exception as e:
            logger.error(f"Error updating flow statistics: {e}")

    def get_auth_flow_diagram(self, session_id: str) -> Dict[str, Any]:
        """Generate flow diagram data for a specific session."""
        try:
            session = self._find_session(session_id)
            if not session:
                return {"error": f"Session {session_id} not found"}
            
            # Create nodes and edges for flow diagram
            nodes = []
            edges = []
            
            for i, trace in enumerate(session.traces):
                # Create node
                node = {
                    "id": f"step_{i}",
                    "label": trace.step.value.replace("_", " ").title(),
                    "type": "success" if trace.success else "error",
                    "details": trace.details,
                    "timestamp": trace.timestamp.isoformat(),
                    "duration_ms": trace.duration_ms,
                    "error": trace.error
                }
                nodes.append(node)
                
                # Create edge to next step
                if i > 0:
                    edge = {
                        "from": f"step_{i-1}",
                        "to": f"step_{i}",
                        "label": f"{trace.duration_ms:.1f}ms" if trace.duration_ms > 0 else "",
                        "type": "success" if trace.success else "error"
                    }
                    edges.append(edge)
            
            return {
                "session_id": session_id,
                "nodes": nodes,
                "edges": edges,
                "metadata": {
                    "request_path": session.request_path,
                    "request_method": session.request_method,
                    "client_ip": session.client_ip,
                    "started_at": session.started_at.isoformat(),
                    "completed_at": session.completed_at.isoformat() if session.completed_at else None,
                    "result": session.result.value if session.result else None,
                    "total_duration_ms": session.total_duration_ms
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating flow diagram for session {session_id}: {e}")
            return {"error": str(e)}

    def get_auth_flow_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get authentication flow statistics."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            recent_sessions = [
                s for s in self.sessions 
                if s.started_at > cutoff_time
            ]
            
            if not recent_sessions:
                return {
                    "total_sessions": 0,
                    "time_period_hours": hours,
                    "statistics": {}
                }
            
            # Calculate statistics
            total_sessions = len(recent_sessions)
            successful_sessions = sum(1 for s in recent_sessions 
                                    if s.result == AuthFlowResult.SUCCESS)
            failed_sessions = total_sessions - successful_sessions
            
            # Average duration
            completed_sessions = [s for s in recent_sessions if s.completed_at]
            avg_duration = (
                sum(s.total_duration_ms for s in completed_sessions) / len(completed_sessions)
                if completed_sessions else 0
            )
            
            # Failure breakdown
            failure_breakdown = {}
            for session in recent_sessions:
                if session.result and session.result != AuthFlowResult.SUCCESS:
                    result = session.result.value
                    failure_breakdown[result] = failure_breakdown.get(result, 0) + 1
            
            # Most common flow patterns
            pattern_counts = {}
            for session in recent_sessions:
                if session.traces:
                    pattern = " -> ".join([trace.step.value for trace in session.traces])
                    pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
            
            top_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Performance by step
            step_performance = {}
            for session in recent_sessions:
                for trace in session.traces:
                    step = trace.step.value
                    if step not in step_performance:
                        step_performance[step] = {
                            "count": 0,
                            "total_duration_ms": 0,
                            "success_count": 0
                        }
                    
                    step_performance[step]["count"] += 1
                    step_performance[step]["total_duration_ms"] += trace.duration_ms
                    if trace.success:
                        step_performance[step]["success_count"] += 1
            
            # Calculate averages
            for step_data in step_performance.values():
                step_data["avg_duration_ms"] = (
                    step_data["total_duration_ms"] / step_data["count"]
                    if step_data["count"] > 0 else 0
                )
                step_data["success_rate"] = (
                    step_data["success_count"] / step_data["count"]
                    if step_data["count"] > 0 else 0
                )
            
            return {
                "total_sessions": total_sessions,
                "successful_sessions": successful_sessions,
                "failed_sessions": failed_sessions,
                "success_rate": successful_sessions / total_sessions if total_sessions > 0 else 0,
                "average_duration_ms": avg_duration,
                "time_period_hours": hours,
                "failure_breakdown": failure_breakdown,
                "top_flow_patterns": top_patterns,
                "step_performance": step_performance,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting auth flow statistics: {e}")
            return {"error": str(e)}

    def get_recent_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent authentication sessions."""
        try:
            recent_sessions = list(reversed(self.sessions))[:limit]
            
            session_summaries = []
            for session in recent_sessions:
                summary = {
                    "session_id": session.session_id,
                    "request_path": session.request_path,
                    "request_method": session.request_method,
                    "client_ip": session.client_ip,
                    "started_at": session.started_at.isoformat(),
                    "completed_at": session.completed_at.isoformat() if session.completed_at else None,
                    "result": session.result.value if session.result else "in_progress",
                    "total_duration_ms": session.total_duration_ms,
                    "step_count": len(session.traces),
                    "user_id": session.user_context.get("user_id") if session.user_context else None
                }
                session_summaries.append(summary)
            
            return session_summaries
            
        except Exception as e:
            logger.error(f"Error getting recent sessions: {e}")
            return []

    def generate_flow_visualization_html(self, session_id: str) -> str:
        """Generate HTML visualization for authentication flow."""
        try:
            flow_data = self.get_auth_flow_diagram(session_id)
            
            if "error" in flow_data:
                return f"<html><body><h1>Error</h1><p>{flow_data['error']}</p></body></html>"
            
            # Generate HTML with embedded JavaScript for visualization
            html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Authentication Flow - {session_id}</title>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        #flow-diagram {{ width: 100%; height: 600px; border: 1px solid #ccc; }}
        .metadata {{ background: #f5f5f5; padding: 15px; margin: 20px 0; border-radius: 5px; }}
        .success {{ color: green; }}
        .error {{ color: red; }}
        .step-details {{ margin: 10px 0; padding: 10px; background: #f9f9f9; border-radius: 3px; }}
    </style>
</head>
<body>
    <h1>Authentication Flow Visualization</h1>
    
    <div class="metadata">
        <h3>Session Information</h3>
        <p><strong>Session ID:</strong> {session_id}</p>
        <p><strong>Request:</strong> {request_method} {request_path}</p>
        <p><strong>Client IP:</strong> {client_ip}</p>
        <p><strong>Started:</strong> {started_at}</p>
        <p><strong>Completed:</strong> {completed_at}</p>
        <p><strong>Result:</strong> <span class="{result_class}">{result}</span></p>
        <p><strong>Total Duration:</strong> {total_duration_ms:.2f}ms</p>
    </div>
    
    <div id="flow-diagram"></div>
    
    <div class="step-details">
        <h3>Step Details</h3>
        {step_details_html}
    </div>
    
    <script>
        const nodes = new vis.DataSet({nodes_data});
        const edges = new vis.DataSet({edges_data});
        
        const container = document.getElementById('flow-diagram');
        const data = {{ nodes: nodes, edges: edges }};
        const options = {{
            layout: {{
                direction: 'UD',
                sortMethod: 'directed'
            }},
            physics: false,
            nodes: {{
                shape: 'box',
                margin: 10,
                font: {{ size: 14 }},
                color: {{
                    background: '#e1f5fe',
                    border: '#01579b'
                }}
            }},
            edges: {{
                arrows: 'to',
                color: '#666',
                font: {{ size: 12 }}
            }}
        }};
        
        const network = new vis.Network(container, data, options);
        
        network.on('selectNode', function(params) {{
            const nodeId = params.nodes[0];
            const node = nodes.get(nodeId);
            alert('Step: ' + node.label + '\\nDetails: ' + JSON.stringify(node.details, null, 2));
        }});
    </script>
</body>
</html>
            """
            
            # Prepare data for template
            metadata = flow_data["metadata"]
            nodes_data = json.dumps(flow_data["nodes"])
            edges_data = json.dumps(flow_data["edges"])
            
            # Generate step details HTML
            step_details_html = ""
            for i, node in enumerate(flow_data["nodes"]):
                step_class = "success" if node["type"] == "success" else "error"
                step_details_html += f"""
                <div class="step-details">
                    <h4 class="{step_class}">Step {i+1}: {node['label']}</h4>
                    <p><strong>Timestamp:</strong> {node['timestamp']}</p>
                    <p><strong>Duration:</strong> {node['duration_ms']:.2f}ms</p>
                    {f"<p><strong>Error:</strong> {node['error']}</p>" if node.get('error') else ""}
                    <p><strong>Details:</strong> <code>{json.dumps(node['details'], indent=2)}</code></p>
                </div>
                """
            
            # Fill template
            html = html_template.format(
                session_id=session_id,
                request_method=metadata["request_method"],
                request_path=metadata["request_path"],
                client_ip=metadata["client_ip"],
                started_at=metadata["started_at"],
                completed_at=metadata["completed_at"] or "In Progress",
                result=metadata["result"] or "In Progress",
                result_class="success" if metadata["result"] == "success" else "error",
                total_duration_ms=metadata["total_duration_ms"],
                nodes_data=nodes_data,
                edges_data=edges_data,
                step_details_html=step_details_html
            )
            
            return html
            
        except Exception as e:
            logger.error(f"Error generating flow visualization HTML: {e}")
            return f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>"

def create_auth_visualization_router(visualizer: ExtensionAuthFlowVisualizer) -> APIRouter:
    """Create authentication visualization router."""
    
    router = APIRouter(prefix="/api/debug/auth-flow", tags=["auth-visualization"])
    
    @router.get("/sessions")
    async def get_recent_auth_sessions(
        limit: int = Query(50, description="Number of recent sessions to return")
    ) -> List[Dict[str, Any]]:
        """Get recent authentication sessions."""
        return visualizer.get_recent_sessions(limit)
    
    @router.get("/sessions/{session_id}")
    async def get_auth_session_details(session_id: str) -> Dict[str, Any]:
        """Get detailed information for specific authentication session."""
        return visualizer.get_auth_flow_diagram(session_id)
    
    @router.get("/sessions/{session_id}/visualize", response_class=HTMLResponse)
    async def visualize_auth_flow(session_id: str) -> str:
        """Get HTML visualization for authentication flow."""
        return visualizer.generate_flow_visualization_html(session_id)
    
    @router.get("/statistics")
    async def get_auth_flow_statistics(
        hours: int = Query(24, description="Time period in hours")
    ) -> Dict[str, Any]:
        """Get authentication flow statistics."""
        return visualizer.get_auth_flow_statistics(hours)
    
    return router

# Global visualizer instance
extension_auth_visualizer = ExtensionAuthFlowVisualizer()