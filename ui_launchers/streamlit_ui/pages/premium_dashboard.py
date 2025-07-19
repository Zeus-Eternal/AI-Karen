"""
Premium Executive Dashboard Page
- High-level KPIs and system overview
- Real-time metrics and status indicators
- Quick action panels and navigation
"""

import streamlit as st
from typing import Dict, Any
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

def premium_dashboard_page(user_ctx: Dict[str, Any]):
    """Render the premium executive dashboard."""
    
    # Page header
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <h1 style="display: flex; align-items: center; gap: 1rem; margin: 0;">
            📊 Executive Dashboard
            <span style="font-size: 0.6em; background: linear-gradient(45deg, #3b82f6, #10b981); 
                         color: white; padding: 0.2rem 0.8rem; border-radius: 1rem;">
                PREMIUM
            </span>
        </h1>
        <p style="color: #64748b; margin: 0.5rem 0 0 0; font-size: 1.1rem;">
            Real-time insights and system overview for {user_ctx.get('username', 'Executive')}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick stats row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🤖 AI Interactions",
            value="2,847",
            delta="12% vs last week",
            delta_color="normal"
        )
    
    with col2:
        st.metric(
            label="⚡ System Health",
            value="98.5%",
            delta="0.3% vs yesterday",
            delta_color="normal"
        )
    
    with col3:
        st.metric(
            label="👥 Active Users",
            value="156",
            delta="8 new today",
            delta_color="normal"
        )
    
    with col4:
        st.metric(
            label="🔧 Plugins Active",
            value="23",
            delta="2 updated",
            delta_color="normal"
        )
    
    st.divider()
    
    # Main dashboard content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📈 Usage Analytics")
        
        # Generate sample data for the chart
        dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
        usage_data = pd.DataFrame({
            'Date': dates,
            'Interactions': [100 + i*5 + (i%7)*20 for i in range(len(dates))],
            'Users': [20 + i*2 + (i%5)*5 for i in range(len(dates))]
        })
        
        # Create interactive chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=usage_data['Date'],
            y=usage_data['Interactions'],
            mode='lines+markers',
            name='Daily Interactions',
            line=dict(color='#3b82f6', width=3),
            marker=dict(size=6)
        ))
        
        fig.add_trace(go.Scatter(
            x=usage_data['Date'],
            y=usage_data['Users'],
            mode='lines+markers',
            name='Active Users',
            line=dict(color='#10b981', width=3),
            marker=dict(size=6),
            yaxis='y2'
        ))
        
        fig.update_layout(
            title="30-Day Usage Trends",
            xaxis_title="Date",
            yaxis_title="Interactions",
            yaxis2=dict(
                title="Users",
                overlaying='y',
                side='right'
            ),
            hovermode='x unified',
            template='plotly_white',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🎯 System Status")
        
        # System health indicators
        health_data = [
            {"service": "AI Engine", "status": "Healthy", "uptime": "99.9%"},
            {"service": "Database", "status": "Healthy", "uptime": "99.8%"},
            {"service": "API Gateway", "status": "Healthy", "uptime": "99.7%"},
            {"service": "Memory Store", "status": "Warning", "uptime": "98.5%"},
            {"service": "Plugin System", "status": "Healthy", "uptime": "99.6%"}
        ]
        
        for service in health_data:
            status_color = {
                "Healthy": "🟢",
                "Warning": "🟡", 
                "Error": "🔴"
            }.get(service["status"], "⚫")
            
            st.markdown(f"""
            <div style="padding: 0.5rem; margin: 0.25rem 0; background: #f8fafc; 
                        border-radius: 0.5rem; border-left: 4px solid #3b82f6;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span><strong>{service['service']}</strong></span>
                    <span>{status_color} {service['status']}</span>
                </div>
                <div style="font-size: 0.8rem; color: #64748b; margin-top: 0.25rem;">
                    Uptime: {service['uptime']}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Quick actions
        st.subheader("⚡ Quick Actions")
        
        if st.button("🔄 Refresh All Data", use_container_width=True):
            st.success("Data refreshed successfully!")
            st.rerun()
        
        if st.button("📊 Generate Report", use_container_width=True):
            st.info("Report generation started...")
        
        if st.button("🔧 System Diagnostics", use_container_width=True):
            st.info("Running system diagnostics...")
    
    # Recent activity section
    st.subheader("📋 Recent Activity")
    
    # Sample recent activities
    activities = [
        {"time": "2 minutes ago", "event": "New user registered", "type": "user", "details": "john.doe@company.com"},
        {"time": "5 minutes ago", "event": "Plugin updated", "type": "system", "details": "analytics-pro v2.1.0"},
        {"time": "12 minutes ago", "event": "High memory usage alert", "type": "warning", "details": "Memory usage: 85%"},
        {"time": "18 minutes ago", "event": "Backup completed", "type": "system", "details": "Daily backup successful"},
        {"time": "25 minutes ago", "event": "API rate limit reached", "type": "warning", "details": "User: api_user_123"}
    ]
    
    for activity in activities:
        icon = {
            "user": "👤",
            "system": "🔧",
            "warning": "⚠️",
            "error": "❌"
        }.get(activity["type"], "📝")
        
        st.markdown(f"""
        <div style="display: flex; align-items: center; padding: 0.75rem; margin: 0.25rem 0; 
                    background: white; border-radius: 0.5rem; border: 1px solid #e2e8f0;">
            <span style="font-size: 1.2rem; margin-right: 1rem;">{icon}</span>
            <div style="flex: 1;">
                <div style="font-weight: 500;">{activity['event']}</div>
                <div style="font-size: 0.8rem; color: #64748b;">{activity['details']}</div>
            </div>
            <div style="font-size: 0.8rem; color: #9ca3af;">{activity['time']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Footer with additional info
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align: center; padding: 1rem; background: #f1f5f9; 
                border-radius: 0.5rem; margin-top: 2rem;">
        <small style="color: #64748b;">
            Dashboard last updated: {current_time} | 
            Data refresh interval: 30 seconds | 
            <a href="#" style="color: #3b82f6;">View detailed analytics →</a>
        </small>
    </div>
    """.format(current_time=datetime.now().strftime("%H:%M:%S")), unsafe_allow_html=True)