"""
Status Bar Component for AI Karen Premium UI
- Real-time system status indicators
- User session information
- Quick system metrics
- Connection status monitoring
"""

import streamlit as st
import time
from typing import Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass

@dataclass
class SystemStatus:
    """System status information."""
    service: str
    status: str  # healthy, warning, error, unknown
    message: str
    last_check: datetime
    response_time: float = 0.0

class StatusBar:
    """Real-time status bar component."""
    
    def __init__(self):
        self.status_cache = {}
        self.cache_duration = 30  # seconds
    
    def _get_system_status(self) -> List[SystemStatus]:
        """Get current system status for all services."""
        current_time = datetime.now()
        
        # Check if we have cached status that's still valid
        if (hasattr(self, '_last_status_check') and 
            (current_time - self._last_status_check).seconds < self.cache_duration):
            return getattr(self, '_cached_status', [])
        
        # Simulate system status checks (in real implementation, these would be actual health checks)
        statuses = [
            SystemStatus(
                service="AI Engine",
                status="healthy",
                message="All AI services operational",
                last_check=current_time,
                response_time=0.045
            ),
            SystemStatus(
                service="Database",
                status="healthy",
                message="All databases connected",
                last_check=current_time,
                response_time=0.012
            ),
            SystemStatus(
                service="Memory",
                status="warning",
                message="Memory usage at 78%",
                last_check=current_time,
                response_time=0.003
            ),
            SystemStatus(
                service="Plugins",
                status="healthy",
                message="15 plugins active",
                last_check=current_time,
                response_time=0.008
            ),
            SystemStatus(
                service="API",
                status="healthy",
                message="API responding normally",
                last_check=current_time,
                response_time=0.023
            )
        ]
        
        # Cache the results
        self._cached_status = statuses
        self._last_status_check = current_time
        
        return statuses
    
    def _get_session_info(self, user_ctx: Dict[str, Any]) -> Dict[str, Any]:
        """Get current session information."""
        session_start = st.session_state.get('session_start', datetime.now())
        current_time = datetime.now()
        session_duration = current_time - session_start
        
        return {
            'username': user_ctx.get('username', 'Guest'),
            'user_id': user_ctx.get('user_id', 'unknown'),
            'roles': user_ctx.get('roles', ['user']),
            'session_duration': session_duration,
            'last_activity': st.session_state.get('last_activity', current_time),
            'current_page': st.session_state.get('current_page', 'dashboard'),
            'theme': st.session_state.get('current_theme', 'executive')
        }
    
    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        # In a real implementation, these would come from actual monitoring
        return {
            'cpu_usage': 45.2,
            'memory_usage': 78.5,
            'disk_usage': 34.1,
            'network_latency': 23,
            'active_connections': 12,
            'requests_per_minute': 156
        }
    
    def render_status_bar(self, user_ctx: Dict[str, Any]):
        """Render the main status bar."""
        # Create status bar container
        status_container = st.container()
        
        with status_container:
            # Status bar styling
            st.markdown("""
            <style>
            .status-bar {
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
                background: linear-gradient(90deg, var(--theme-primary), var(--theme-secondary));
                color: white;
                padding: 8px 16px;
                font-size: 12px;
                z-index: 1000;
                border-top: 1px solid rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
            }
            
            .status-item {
                display: inline-flex;
                align-items: center;
                gap: 4px;
                margin-right: 16px;
                padding: 2px 6px;
                border-radius: 4px;
                background: rgba(255, 255, 255, 0.1);
            }
            
            .status-healthy { color: #10b981; }
            .status-warning { color: #f59e0b; }
            .status-error { color: #ef4444; }
            .status-unknown { color: #6b7280; }
            
            .status-separator {
                display: inline-block;
                width: 1px;
                height: 16px;
                background: rgba(255, 255, 255, 0.2);
                margin: 0 12px;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Get status information
            system_statuses = self._get_system_status()
            session_info = self._get_session_info(user_ctx)
            performance_metrics = self._get_performance_metrics()
            
            # Build status bar HTML
            status_html = self._build_status_html(system_statuses, session_info, performance_metrics)
            
            # Render status bar
            st.markdown(status_html, unsafe_allow_html=True)
    
    def _build_status_html(self, statuses: List[SystemStatus], session_info: Dict[str, Any], 
                          metrics: Dict[str, Any]) -> str:
        """Build the status bar HTML."""
        # System status indicators
        system_status_html = ""
        overall_status = "healthy"
        
        for status in statuses:
            status_class = f"status-{status.status}"
            status_icon = self._get_status_icon(status.status)
            
            system_status_html += f"""
            <span class="status-item {status_class}" title="{status.message}">
                {status_icon} {status.service}
            </span>
            """
            
            # Determine overall status
            if status.status == "error":
                overall_status = "error"
            elif status.status == "warning" and overall_status != "error":
                overall_status = "warning"
        
        # Session information
        session_duration = session_info['session_duration']
        duration_str = f"{int(session_duration.total_seconds() // 3600)}h {int((session_duration.total_seconds() % 3600) // 60)}m"
        
        session_html = f"""
        <span class="status-item" title="Current user session">
            👤 {session_info['username']} ({', '.join(session_info['roles'])})
        </span>
        <span class="status-item" title="Session duration">
            ⏱️ {duration_str}
        </span>
        <span class="status-item" title="Current page">
            📄 {session_info['current_page'].title()}
        </span>
        """
        
        # Performance metrics
        performance_html = f"""
        <span class="status-item" title="CPU Usage">
            🖥️ CPU: {metrics['cpu_usage']:.1f}%
        </span>
        <span class="status-item" title="Memory Usage">
            🧠 RAM: {metrics['memory_usage']:.1f}%
        </span>
        <span class="status-item" title="Network Latency">
            🌐 {metrics['network_latency']}ms
        </span>
        """
        
        # Current time
        current_time = datetime.now().strftime("%H:%M:%S")
        time_html = f"""
        <span class="status-item" title="Current time">
            🕐 {current_time}
        </span>
        """
        
        # Overall status indicator
        overall_icon = self._get_status_icon(overall_status)
        overall_html = f"""
        <span class="status-item status-{overall_status}" title="Overall system status">
            {overall_icon} System {overall_status.title()}
        </span>
        """
        
        # Combine all elements
        return f"""
        <div class="status-bar">
            {overall_html}
            <span class="status-separator"></span>
            {system_status_html}
            <span class="status-separator"></span>
            {session_html}
            <span class="status-separator"></span>
            {performance_html}
            <span class="status-separator"></span>
            {time_html}
        </div>
        """
    
    def _get_status_icon(self, status: str) -> str:
        """Get icon for status type."""
        icons = {
            "healthy": "🟢",
            "warning": "🟡", 
            "error": "🔴",
            "unknown": "⚫"
        }
        return icons.get(status, "⚫")
    
    def render_detailed_status(self, user_ctx: Dict[str, Any]):
        """Render detailed system status page."""
        st.title("🔍 System Status Details")
        
        # Refresh button
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("🔄 Refresh Status"):
                # Clear cache to force refresh
                if hasattr(self, '_last_status_check'):
                    delattr(self, '_last_status_check')
                st.rerun()
        
        with col2:
            auto_refresh = st.checkbox("Auto Refresh (30s)", value=False)
        
        if auto_refresh:
            time.sleep(30)
            st.rerun()
        
        # System status overview
        st.subheader("🖥️ System Services")
        
        statuses = self._get_system_status()
        
        # Create status cards
        cols = st.columns(len(statuses))
        
        for i, status in enumerate(statuses):
            with cols[i]:
                status_color = {
                    "healthy": "green",
                    "warning": "orange", 
                    "error": "red",
                    "unknown": "gray"
                }.get(status.status, "gray")
                
                st.metric(
                    label=f"{self._get_status_icon(status.status)} {status.service}",
                    value=status.status.title(),
                    delta=f"{status.response_time*1000:.1f}ms"
                )
                
                with st.expander(f"Details - {status.service}"):
                    st.write(f"**Status:** {status.status.title()}")
                    st.write(f"**Message:** {status.message}")
                    st.write(f"**Last Check:** {status.last_check.strftime('%H:%M:%S')}")
                    st.write(f"**Response Time:** {status.response_time*1000:.1f}ms")
        
        # Performance metrics
        st.subheader("📊 Performance Metrics")
        
        metrics = self._get_performance_metrics()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("CPU Usage", f"{metrics['cpu_usage']:.1f}%")
            st.metric("Memory Usage", f"{metrics['memory_usage']:.1f}%")
        
        with col2:
            st.metric("Disk Usage", f"{metrics['disk_usage']:.1f}%")
            st.metric("Network Latency", f"{metrics['network_latency']}ms")
        
        with col3:
            st.metric("Active Connections", metrics['active_connections'])
            st.metric("Requests/Min", metrics['requests_per_minute'])
        
        # Session information
        st.subheader("👤 Session Information")
        
        session_info = self._get_session_info(user_ctx)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**User:** {session_info['username']}")
            st.write(f"**User ID:** {session_info['user_id']}")
            st.write(f"**Roles:** {', '.join(session_info['roles'])}")
        
        with col2:
            st.write(f"**Session Duration:** {session_info['session_duration']}")
            st.write(f"**Current Page:** {session_info['current_page']}")
            st.write(f"**Theme:** {session_info['theme']}")
        
        # System logs (simulated)
        st.subheader("📋 Recent System Events")
        
        with st.expander("View System Logs"):
            # Simulate recent log entries
            log_entries = [
                {"time": "14:32:15", "level": "INFO", "message": "User login successful", "service": "Auth"},
                {"time": "14:31:45", "level": "INFO", "message": "Database connection established", "service": "DB"},
                {"time": "14:31:20", "level": "WARN", "message": "Memory usage above 75%", "service": "System"},
                {"time": "14:30:55", "level": "INFO", "message": "Plugin loaded: analytics-pro", "service": "Plugins"},
                {"time": "14:30:30", "level": "INFO", "message": "Theme changed to executive", "service": "UI"}
            ]
            
            for entry in log_entries:
                level_color = {
                    "INFO": "🟢",
                    "WARN": "🟡",
                    "ERROR": "🔴"
                }.get(entry["level"], "⚫")
                
                st.write(f"{level_color} `{entry['time']}` **{entry['service']}** - {entry['message']}")
    
    def get_system_health_summary(self) -> Dict[str, Any]:
        """Get a summary of system health for other components."""
        statuses = self._get_system_status()
        metrics = self._get_performance_metrics()
        
        # Calculate overall health score
        healthy_count = len([s for s in statuses if s.status == "healthy"])
        warning_count = len([s for s in statuses if s.status == "warning"])
        error_count = len([s for s in statuses if s.status == "error"])
        
        total_services = len(statuses)
        health_score = (healthy_count * 100 + warning_count * 50) / (total_services * 100) if total_services > 0 else 0
        
        overall_status = "healthy"
        if error_count > 0:
            overall_status = "error"
        elif warning_count > 0:
            overall_status = "warning"
        
        return {
            "overall_status": overall_status,
            "health_score": health_score,
            "services": {
                "total": total_services,
                "healthy": healthy_count,
                "warning": warning_count,
                "error": error_count
            },
            "performance": {
                "cpu_usage": metrics["cpu_usage"],
                "memory_usage": metrics["memory_usage"],
                "network_latency": metrics["network_latency"]
            },
            "last_updated": datetime.now()
        }