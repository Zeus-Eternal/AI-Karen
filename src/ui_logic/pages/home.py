"""
AI Karen Dashboard - Modern Overview
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import random

def home_page(user_ctx=None):
    """Modern AI Karen dashboard with live metrics and insights"""
    
    # Welcome section with user personalization
    username = user_ctx.get('username', 'User') if user_ctx else 'User'
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"""
        # Welcome back, {username}! 👋
        
        Your AI assistant is ready to help. Here's what's happening today.
        """)
    
    with col2:
        current_time = datetime.now()
        st.markdown(f"""
        ### {current_time.strftime('%A')}
        **{current_time.strftime('%B %d, %Y')}**  
        {current_time.strftime('%I:%M %p')}
        """)
    
    st.divider()
    
    # Quick stats row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🤖 AI Interactions Today",
            value="47",
            delta="12 vs yesterday"
        )
    
    with col2:
        st.metric(
            label="⚡ System Health",
            value="98.5%",
            delta="0.3%"
        )
    
    with col3:
        st.metric(
            label="🧠 Memory Usage",
            value="2.1 GB",
            delta="-0.2 GB"
        )
    
    with col4:
        st.metric(
            label="🔧 Active Plugins",
            value="8",
            delta="2 new"
        )
    
    st.divider()
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📈 Activity Overview")
        
        # Generate sample activity data
        dates = pd.date_range(start=datetime.now() - timedelta(days=7), end=datetime.now(), freq='D')
        activity_data = pd.DataFrame({
            'Date': dates,
            'Conversations': [random.randint(20, 60) for _ in range(len(dates))],
            'Tasks Completed': [random.randint(5, 25) for _ in range(len(dates))]
        })
        
        # Create activity chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=activity_data['Date'],
            y=activity_data['Conversations'],
            mode='lines+markers',
            name='Conversations',
            line=dict(color='#3b82f6', width=3),
            marker=dict(size=8)
        ))
        
        fig.add_trace(go.Scatter(
            x=activity_data['Date'],
            y=activity_data['Tasks Completed'],
            mode='lines+markers',
            name='Tasks Completed',
            line=dict(color='#10b981', width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title="7-Day Activity Trend",
            xaxis_title="Date",
            yaxis_title="Count",
            hovermode='x unified',
            template='plotly_white',
            height=300,
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🎯 Quick Actions")
        
        if st.button("💬 Start New Chat", use_container_width=True):
            st.session_state.current_page = 'Chat'
            st.rerun()
        
        if st.button("🧠 Browse Memory", use_container_width=True):
            st.session_state.current_page = 'Memory'
            st.rerun()
        
        if st.button("📊 View Analytics", use_container_width=True):
            st.session_state.current_page = 'Analytics'
            st.rerun()
        
        if st.button("🧩 Manage Plugins", use_container_width=True):
            st.session_state.current_page = 'Plugins'
            st.rerun()
        
        st.markdown("---")
        
        st.subheader("🔔 Recent Activity")
        
        activities = [
            {"time": "2 min ago", "action": "Chat session completed", "icon": "💬"},
            {"time": "15 min ago", "action": "Memory updated", "icon": "🧠"},
            {"time": "1 hour ago", "action": "Plugin installed", "icon": "🧩"},
            {"time": "3 hours ago", "action": "Analytics generated", "icon": "📊"}
        ]
        
        for activity in activities:
            st.markdown(f"""
            <div style="display: flex; align-items: center; padding: 0.5rem; margin: 0.25rem 0; 
                        background: #f8fafc; border-radius: 0.5rem; border-left: 3px solid #3b82f6;">
                <span style="margin-right: 0.5rem; font-size: 1.2rem;">{activity['icon']}</span>
                <div>
                    <div style="font-weight: 500; font-size: 0.9rem;">{activity['action']}</div>
                    <div style="color: #64748b; font-size: 0.8rem;">{activity['time']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.divider()
    
    # System status section
    st.subheader("🖥️ System Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **🤖 AI Engine**  
        Status: ✅ Operational  
        Response Time: 0.3s  
        Uptime: 99.9%
        """)
    
    with col2:
        st.markdown("""
        **💾 Database**  
        Status: ✅ Connected  
        Queries/sec: 45  
        Storage: 2.1GB used
        """)
    
    with col3:
        st.markdown("""
        **🔌 Plugins**  
        Status: ✅ All Active  
        Loaded: 8/8  
        Last Update: 2h ago
        """)
    
    # Tips section
    with st.expander("💡 Tips & Shortcuts"):
        st.markdown("""
        - **Quick Chat**: Press `Ctrl+/` to start a new conversation
        - **Memory Search**: Use `@remember` in chat to search your knowledge base
        - **Plugin Commands**: Type `/plugins` to see available commands
        - **Analytics**: View your usage patterns in the Analytics tab
        - **Settings**: Customize your AI assistant in Settings
        """)
    
    # Footer with version info
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #64748b; font-size: 0.8rem;">
        AI Karen v2.0 • Last updated: {time} • System healthy ✅
    </div>
    """.format(time=datetime.now().strftime("%H:%M")), unsafe_allow_html=True)
