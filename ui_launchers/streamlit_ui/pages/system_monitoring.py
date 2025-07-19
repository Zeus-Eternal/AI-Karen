"""
System Monitoring Dashboard Page
- Real-time system health and performance monitoring
- Service status indicators and alerts
- Log aggregation and analysis
"""

import streamlit as st
from typing import Dict, Any

def system_monitoring_page(user_ctx: Dict[str, Any]):
    """Render the system monitoring dashboard."""
    
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <h1 style="display: flex; align-items: center; gap: 1rem; margin: 0;">
            📡 System Monitoring
        </h1>
        <p style="color: #64748b; margin: 0.5rem 0 0 0;">
            Real-time system health and performance monitoring
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.info("🚧 System monitoring implementation coming in task 8!")
    st.markdown("""
    **Planned Features:**
    - Live system metrics with real-time updates
    - Service health monitoring with alerting
    - Resource usage tracking and optimization suggestions
    - Log aggregation and analysis
    - Performance profiling and bottleneck identification
    """)
    
    # Placeholder system status
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("CPU Usage", "45%", "Normal")
    with col2:
        st.metric("Memory", "78%", "High")
    with col3:
        st.metric("Disk I/O", "23%", "Low")
    with col4:
        st.metric("Network", "12ms", "Good")