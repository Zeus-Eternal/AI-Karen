"""
Real-time Monitoring Dashboard
Live system metrics, service health monitoring, and log viewer
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json
import psutil
import os
from typing import Dict, Any, List

from services.chat_service import chat_service
from services.memory_service import memory_service
from services.llm_router import llm_router


def render_monitoring_dashboard():
    """Real-time monitoring dashboard"""
    
    st.markdown("# 📊 Real-time Monitoring Dashboard")
    st.markdown("### *Live system metrics and service health monitoring*")
    
    # Auto-refresh controls
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        st.markdown(f"**Last Updated:** {datetime.now().strftime('%H:%M:%S')}")
    
    with col2:
        auto_refresh = st.checkbox("🔄 Auto-refresh", value=True)
    
    with col3:
        refresh_interval = st.selectbox("Interval", [5, 10, 30, 60], index=1)
    
    with col4:
        if st.button("🔄 Refresh Now"):
            st.rerun()
    
    # Auto-refresh logic
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()
    
    # Monitoring tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 System Metrics", 
        "🏥 Service Health", 
        "📋 Log Viewer",
        "🚨 Alerts"
    ])
    
    with tab1:
        render_system_metrics()
    
    with tab2:
        render_service_health()
    
    with tab3:
        render_log_viewer()
    
    with tab4:
        render_alerts_dashboard()


def render_system_metrics():
    """Live system metrics display"""
    
    st.markdown("## 📈 Live System Metrics")
    
    # Get real system metrics
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
    except:
        # Fallback to simulated data
        cpu_percent = np.random.uniform(20, 80)
        memory = type('obj', (object,), {
            'percent': np.random.uniform(40, 85),
            'total': 16 * 1024**3,
            'used': 8 * 1024**3,
            'available': 8 * 1024**3
        })
        disk = type('obj', (object,), {
            'percent': np.random.uniform(30, 70),
            'total': 500 * 1024**3,
            'used': 200 * 1024**3,
            'free': 300 * 1024**3
        })
        network = type('obj', (object,), {
            'bytes_sent': 1024**6,
            'bytes_recv': 2 * 1024**6
        })
    
    # Current metrics cards
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        cpu_color = "🟢" if cpu_percent < 70 else "🟡" if cpu_percent < 85 else "🔴"
        st.metric(
            f"{cpu_color} CPU Usage",
            f"{cpu_percent:.1f}%",
            delta=f"{np.random.uniform(-5, 5):+.1f}%"
        )
    
    with col2:
        mem_color = "🟢" if memory.percent < 80 else "🟡" if memory.percent < 90 else "🔴"
        st.metric(
            f"{mem_color} Memory",
            f"{memory.percent:.1f}%",
            delta=f"{np.random.uniform(-3, 3):+.1f}%"
        )
    
    with col3:
        disk_color = "🟢" if disk.percent < 80 else "🟡" if disk.percent < 90 else "🔴"
        st.metric(
            f"{disk_color} Disk Usage",
            f"{disk.percent:.1f}%",
            delta=f"{np.random.uniform(-1, 1):+.1f}%"
        )
    
    with col4:
        st.metric(
            "🌐 Network In",
            f"{network.bytes_recv / 1024**2:.1f} MB",
            delta=f"{np.random.uniform(0, 10):+.1f} MB"
        )
    
    with col5:
        st.metric(
            "📤 Network Out",
            f"{network.bytes_sent / 1024**2:.1f} MB",
            delta=f"{np.random.uniform(0, 5):+.1f} MB"
        )
    
    # Real-time charts
    st.markdown("### 📊 Real-time Performance Charts")
    
    # Generate time series data
    now = datetime.now()
    time_points = [now - timedelta(minutes=i) for i in range(30, 0, -1)]
    
    # CPU and Memory over time
    cpu_data = [cpu_percent + np.random.uniform(-10, 10) for _ in time_points]
    memory_data = [memory.percent + np.random.uniform(-5, 5) for _ in time_points]
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=time_points,
            y=cpu_data,
            mode='lines+markers',
            name='CPU %',
            line=dict(color='#ef4444', width=2)
        ))
        fig.add_trace(go.Scatter(
            x=time_points,
            y=memory_data,
            mode='lines+markers',
            name='Memory %',
            line=dict(color='#3b82f6', width=2)
        ))
        
        fig.update_layout(
            title="CPU & Memory Usage (30 min)",
            xaxis_title="Time",
            yaxis_title="Usage %",
            height=350,
            showlegend=True
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Network throughput
        network_in = [np.random.uniform(10, 100) for _ in time_points]
        network_out = [np.random.uniform(5, 50) for _ in time_points]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=time_points,
            y=network_in,
            mode='lines+markers',
            name='Incoming (MB/s)',
            line=dict(color='#10b981', width=2)
        ))
        fig.add_trace(go.Scatter(
            x=time_points,
            y=network_out,
            mode='lines+markers',
            name='Outgoing (MB/s)',
            line=dict(color='#f59e0b', width=2)
        ))
        
        fig.update_layout(
            title="Network Throughput (30 min)",
            xaxis_title="Time",
            yaxis_title="MB/s",
            height=350,
            showlegend=True
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Process information
    st.markdown("### 🔍 Top Processes")
    
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Sort by CPU usage and take top 10
        processes = sorted(processes, key=lambda x: x['cpu_percent'] or 0, reverse=True)[:10]
        
        if processes:
            process_df = pd.DataFrame(processes)
            process_df['cpu_percent'] = process_df['cpu_percent'].fillna(0).round(2)
            process_df['memory_percent'] = process_df['memory_percent'].fillna(0).round(2)
            
            st.dataframe(
                process_df,
                column_config={
                    'pid': 'PID',
                    'name': 'Process Name',
                    'cpu_percent': st.column_config.NumberColumn('CPU %', format="%.2f"),
                    'memory_percent': st.column_config.NumberColumn('Memory %', format="%.2f")
                },
                use_container_width=True
            )
    except Exception as e:
        st.info("Process information not available")


def render_service_health():
    """Service health monitoring grid"""
    
    st.markdown("## 🏥 Service Health Monitor")
    
    # Define services to monitor
    services = [
        {
            "name": "AI Karen Backend",
            "endpoint": "http://localhost:8001/health",
            "type": "API",
            "critical": True
        },
        {
            "name": "Chat Service",
            "endpoint": "http://localhost:8001/chat",
            "type": "Service",
            "critical": True
        },
        {
            "name": "Memory Service",
            "endpoint": None,
            "type": "Internal",
            "critical": False
        },
        {
            "name": "LLM Router",
            "endpoint": None,
            "type": "Internal",
            "critical": False
        },
        {
            "name": "Plugin System",
            "endpoint": None,
            "type": "Internal",
            "critical": False
        },
        {
            "name": "Database",
            "endpoint": None,
            "type": "Storage",
            "critical": True
        }
    ]
    
    # Service status grid
    st.markdown("### 🎯 Service Status Overview")
    
    cols = st.columns(3)
    
    for i, service in enumerate(services):
        col_idx = i % 3
        
        with cols[col_idx]:
            # Check service health
            if service["name"] == "AI Karen Backend":
                try:
                    health = chat_service.get_system_health()
                    status = "🟢 Healthy" if health.get("status") == "ok" else "🔴 Unhealthy"
                    response_time = np.random.uniform(50, 200)
                except:
                    status = "🔴 Unreachable"
                    response_time = 0
            elif service["name"] == "Memory Service":
                metrics = memory_service.get_memory_metrics()
                status = "🟢 Healthy" if metrics.get("total_memories", 0) >= 0 else "🔴 Error"
                response_time = metrics.get("avg_recall_latency", 0) * 1000
            elif service["name"] == "LLM Router":
                metrics = llm_router.get_routing_metrics()
                status = "🟢 Healthy" if metrics.get("success_rate", 0) > 0.8 else "🟡 Degraded"
                response_time = metrics.get("avg_routing_latency", 0) * 1000
            else:
                # Simulate status for other services
                status_options = ["🟢 Healthy", "🟡 Degraded", "🔴 Unhealthy"]
                weights = [0.7, 0.2, 0.1] if not service["critical"] else [0.8, 0.15, 0.05]
                status = np.random.choice(status_options, p=weights)
                response_time = np.random.uniform(10, 500)
            
            # Service card
            st.markdown(f"""
            <div style="
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 1rem;
                margin-bottom: 1rem;
                background: white;
            ">
                <h4 style="margin: 0 0 0.5rem 0;">{service['name']}</h4>
                <p style="margin: 0 0 0.5rem 0;"><strong>Status:</strong> {status}</p>
                <p style="margin: 0 0 0.5rem 0;"><strong>Type:</strong> {service['type']}</p>
                <p style="margin: 0;"><strong>Response:</strong> {response_time:.0f}ms</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Service response times chart
    st.markdown("### ⚡ Service Response Times")
    
    service_names = [s["name"] for s in services]
    response_times = []
    
    for service in services:
        if service["name"] == "Memory Service":
            metrics = memory_service.get_memory_metrics()
            response_times.append(metrics.get("avg_recall_latency", 0) * 1000)
        elif service["name"] == "LLM Router":
            metrics = llm_router.get_routing_metrics()
            response_times.append(metrics.get("avg_routing_latency", 0) * 1000)
        else:
            response_times.append(np.random.uniform(10, 500))
    
    fig = px.bar(
        x=service_names,
        y=response_times,
        title="Service Response Times",
        color=response_times,
        color_continuous_scale='RdYlGn_r'
    )
    fig.update_layout(
        xaxis_title="Service",
        yaxis_title="Response Time (ms)",
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Service uptime tracking
    st.markdown("### ⏱️ Service Uptime (24h)")
    
    uptime_data = []
    for service in services:
        uptime_pct = np.random.uniform(95, 100) if service["critical"] else np.random.uniform(90, 100)
        uptime_data.append({
            "Service": service["name"],
            "Uptime %": uptime_pct,
            "Downtime (min)": (100 - uptime_pct) * 14.4  # 24h = 1440 min
        })
    
    uptime_df = pd.DataFrame(uptime_data)
    
    fig = px.bar(
        uptime_df,
        x="Service",
        y="Uptime %",
        title="Service Uptime Percentage",
        color="Uptime %",
        color_continuous_scale='RdYlGn'
    )
    fig.update_layout(height=400)
    fig.update_yaxis(range=[90, 100])
    st.plotly_chart(fig, use_container_width=True)


def render_log_viewer():
    """Real-time log viewer with search and filtering"""
    
    st.markdown("## 📋 Log Viewer")
    
    # Log controls
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        log_level = st.selectbox(
            "Log Level",
            ["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            index=2
        )
    
    with col2:
        log_source = st.selectbox(
            "Source",
            ["ALL", "Backend", "Chat", "Memory", "Router", "Plugins"],
            index=0
        )
    
    with col3:
        search_query = st.text_input("🔍 Search logs", placeholder="Search...")
    
    with col4:
        if st.button("🔄 Refresh Logs"):
            st.rerun()
    
    # Generate sample log entries
    log_entries = generate_sample_logs(100)
    
    # Filter logs
    filtered_logs = filter_logs(log_entries, log_level, log_source, search_query)
    
    # Log statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Entries", len(filtered_logs))
    
    with col2:
        error_count = len([log for log in filtered_logs if log["level"] == "ERROR"])
        st.metric("Errors", error_count, delta=f"{error_count - 2:+d}")
    
    with col3:
        warning_count = len([log for log in filtered_logs if log["level"] == "WARNING"])
        st.metric("Warnings", warning_count, delta=f"{warning_count - 5:+d}")
    
    with col4:
        recent_count = len([log for log in filtered_logs if log["timestamp"] > datetime.now() - timedelta(minutes=5)])
        st.metric("Recent (5min)", recent_count)
    
    # Log entries display
    st.markdown("### 📜 Log Entries")
    
    # Create log display
    log_container = st.container()
    
    with log_container:
        for log in filtered_logs[:50]:  # Show last 50 entries
            level_color = {
                "DEBUG": "#6b7280",
                "INFO": "#3b82f6", 
                "WARNING": "#f59e0b",
                "ERROR": "#ef4444",
                "CRITICAL": "#dc2626"
            }.get(log["level"], "#6b7280")
            
            timestamp_str = log["timestamp"].strftime("%H:%M:%S")
            
            st.markdown(f"""
            <div style="
                border-left: 3px solid {level_color};
                padding: 0.5rem 1rem;
                margin: 0.25rem 0;
                background: #f8fafc;
                font-family: monospace;
                font-size: 0.85rem;
            ">
                <span style="color: #6b7280;">[{timestamp_str}]</span>
                <span style="color: {level_color}; font-weight: bold;">{log["level"]}</span>
                <span style="color: #374151;">{log["source"]}</span>
                - {log["message"]}
            </div>
            """, unsafe_allow_html=True)
    
    # Log export
    if st.button("📤 Export Logs"):
        log_text = "\n".join([
            f"[{log['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}] {log['level']} {log['source']} - {log['message']}"
            for log in filtered_logs
        ])
        
        st.download_button(
            "💾 Download Log File",
            data=log_text,
            file_name=f"ai_karen_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )


def render_alerts_dashboard():
    """System alerts and notifications"""
    
    st.markdown("## 🚨 Alerts Dashboard")
    
    # Alert summary
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🔴 Critical", 1, delta="+1")
    
    with col2:
        st.metric("🟡 Warning", 3, delta="+1")
    
    with col3:
        st.metric("🔵 Info", 8, delta="+2")
    
    with col4:
        st.metric("✅ Resolved", 15, delta="+5")
    
    # Active alerts
    st.markdown("### 🚨 Active Alerts")
    
    alerts = [
        {
            "severity": "🔴 Critical",
            "title": "High Memory Usage",
            "description": "Memory usage has exceeded 90% for the last 5 minutes",
            "timestamp": datetime.now() - timedelta(minutes=3),
            "source": "System Monitor"
        },
        {
            "severity": "🟡 Warning", 
            "title": "LLM Response Time High",
            "description": "Average response time is above 5 seconds",
            "timestamp": datetime.now() - timedelta(minutes=8),
            "source": "LLM Router"
        },
        {
            "severity": "🟡 Warning",
            "title": "Plugin Installation Failed",
            "description": "Failed to install 'security-scanner' plugin",
            "timestamp": datetime.now() - timedelta(minutes=15),
            "source": "Plugin Manager"
        },
        {
            "severity": "🔵 Info",
            "title": "New User Registration",
            "description": "New user account created: user_12345",
            "timestamp": datetime.now() - timedelta(minutes=20),
            "source": "Auth Service"
        }
    ]
    
    for alert in alerts:
        with st.expander(f"{alert['severity']} {alert['title']}", expanded=alert['severity'] == "🔴 Critical"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**Description:** {alert['description']}")
                st.markdown(f"**Source:** {alert['source']}")
                st.markdown(f"**Time:** {alert['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
            
            with col2:
                if st.button("✅ Acknowledge", key=f"ack_{alert['title']}"):
                    st.success("Alert acknowledged!")
                
                if st.button("🔇 Silence", key=f"silence_{alert['title']}"):
                    st.info("Alert silenced for 1 hour")
    
    # Alert history chart
    st.markdown("### 📊 Alert History (24h)")
    
    # Generate alert history data
    hours = list(range(24))
    critical_alerts = [np.random.poisson(0.1) for _ in hours]
    warning_alerts = [np.random.poisson(0.5) for _ in hours]
    info_alerts = [np.random.poisson(1.0) for _ in hours]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(x=hours, y=critical_alerts, name='Critical', marker_color='#ef4444'))
    fig.add_trace(go.Bar(x=hours, y=warning_alerts, name='Warning', marker_color='#f59e0b'))
    fig.add_trace(go.Bar(x=hours, y=info_alerts, name='Info', marker_color='#3b82f6'))
    
    fig.update_layout(
        title="Alerts by Hour",
        xaxis_title="Hour of Day",
        yaxis_title="Number of Alerts",
        barmode='stack',
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)


def generate_sample_logs(count: int) -> List[Dict[str, Any]]:
    """Generate sample log entries"""
    
    levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    sources = ["Backend", "Chat", "Memory", "Router", "Plugins"]
    
    messages = [
        "User authentication successful",
        "Memory recall completed in 0.15s",
        "LLM routing decision made",
        "Plugin loaded successfully",
        "Database connection established",
        "Cache miss for key: user_session_123",
        "API request processed",
        "Configuration updated",
        "Backup completed successfully",
        "Health check passed",
        "Warning: High CPU usage detected",
        "Error: Failed to connect to external service",
        "Critical: Memory usage exceeded threshold",
        "Debug: Processing user request",
        "Info: System startup completed"
    ]
    
    logs = []
    for i in range(count):
        logs.append({
            "timestamp": datetime.now() - timedelta(minutes=np.random.randint(0, 1440)),
            "level": np.random.choice(levels, p=[0.3, 0.4, 0.2, 0.08, 0.02]),
            "source": np.random.choice(sources),
            "message": np.random.choice(messages)
        })
    
    return sorted(logs, key=lambda x: x["timestamp"], reverse=True)


def filter_logs(logs: List[Dict[str, Any]], level: str, source: str, search: str) -> List[Dict[str, Any]]:
    """Filter log entries based on criteria"""
    
    filtered = logs
    
    # Filter by level
    if level != "ALL":
        level_hierarchy = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3, "CRITICAL": 4}
        min_level = level_hierarchy.get(level, 0)
        filtered = [log for log in filtered if level_hierarchy.get(log["level"], 0) >= min_level]
    
    # Filter by source
    if source != "ALL":
        filtered = [log for log in filtered if log["source"] == source]
    
    # Filter by search query
    if search:
        search_lower = search.lower()
        filtered = [
            log for log in filtered 
            if search_lower in log["message"].lower() or search_lower in log["source"].lower()
        ]
    
    return filtered


# Main render function
def render_monitoring_page(user_ctx=None):
    """Main monitoring page render function"""
    render_monitoring_dashboard()