"""
Dashboard page components for the Streamlit UI
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

from components.data_utils import (
    generate_sample_data, 
    generate_real_time_kpis, 
    generate_service_health_data,
    generate_analytics_data
)


def render_executive_dashboard():
    """Executive dashboard with real-time KPIs and customizable widgets"""
    st.markdown("## 📈 Executive Dashboard")
    
    # Dashboard customization controls
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        st.markdown("**Real-time System Overview**")
    with col2:
        auto_refresh = st.checkbox("🔄 Auto-refresh", value=True, key="exec_refresh")
    with col3:
        refresh_interval = st.selectbox("Interval", [5, 10, 30, 60], index=2, key="exec_interval")
    with col4:
        if st.button("⚙️ Customize", key="exec_customize"):
            st.session_state.show_dashboard_config = True
    
    # Auto-refresh logic
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()
    
    # Generate real-time data
    current_time = datetime.now()
    
    # Executive KPI Cards
    st.markdown("### 🎯 Key Performance Indicators")
    kpi_cols = st.columns(6)
    
    kpis = generate_real_time_kpis()
    
    for i, (label, value, indicator) in enumerate(kpis):
        with kpi_cols[i]:
            delta = np.random.uniform(-5, 5)
            st.metric(
                label=f"{indicator} {label}",
                value=value,
                delta=f"{delta:+.1f}%" if "%" in value else f"{delta:+.0f}"
            )
    
    # Real-time charts section
    st.markdown("### 📊 Real-time System Monitoring")
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        # System performance over time
        time_data = pd.date_range(start=current_time - pd.Timedelta(hours=24), end=current_time, freq='H')
        perf_data = pd.DataFrame({
            'time': time_data,
            'cpu': np.random.normal(45, 15, len(time_data)).clip(0, 100),
            'memory': np.random.normal(60, 20, len(time_data)).clip(0, 100),
            'network': np.random.normal(30, 10, len(time_data)).clip(0, 100)
        })
        
        fig_perf = go.Figure()
        fig_perf.add_trace(go.Scatter(x=perf_data['time'], y=perf_data['cpu'], name='CPU %', line=dict(color='#ff6b6b')))
        fig_perf.add_trace(go.Scatter(x=perf_data['time'], y=perf_data['memory'], name='Memory %', line=dict(color='#4ecdc4')))
        fig_perf.add_trace(go.Scatter(x=perf_data['time'], y=perf_data['network'], name='Network %', line=dict(color='#45b7d1')))
        
        fig_perf.update_layout(
            title="System Performance (24h)",
            xaxis_title="Time",
            yaxis_title="Usage %",
            height=350,
            showlegend=True
        )
        st.plotly_chart(fig_perf, use_container_width=True)
    
    with chart_col2:
        # Service health status
        service_df = generate_service_health_data()
        
        # Create status indicator chart
        status_colors = {'Healthy': '#10b981', 'Warning': '#f59e0b', 'Critical': '#ef4444'}
        fig_services = go.Figure(data=[
            go.Bar(
                x=service_df['Service'],
                y=service_df['Response Time (ms)'],
                marker_color=[status_colors[status] for status in service_df['Status']],
                text=[f"{status}<br>{rt:.0f}ms" for status, rt in zip(service_df['Status'], service_df['Response Time (ms)'])],
                textposition='auto'
            )
        ])
        
        fig_services.update_layout(
            title="Service Health & Response Times",
            xaxis_title="Services",
            yaxis_title="Response Time (ms)",
            height=350
        )
        st.plotly_chart(fig_services, use_container_width=True)


def render_usage_analytics():
    """Usage analytics with trend visualization and drill-down capabilities"""
    st.markdown("### 📈 Usage Analytics & Trends")
    
    # Time period selector
    period_col1, period_col2, period_col3 = st.columns([2, 1, 1])
    with period_col1:
        time_period = st.selectbox("Time Period", ["Last 7 days", "Last 30 days", "Last 90 days", "Last year"])
    with period_col2:
        metric_focus = st.selectbox("Focus Metric", ["Users", "Sessions", "Requests", "Errors"])
    with period_col3:
        view_type = st.selectbox("View", ["Trend", "Distribution", "Comparison"])
    
    # Generate analytics data based on selection
    analytics_data = generate_analytics_data(time_period)
    
    # Add trend calculation
    analytics_data['trend'] = analytics_data[metric_focus.lower()].rolling(window=3, center=True).mean()
    
    col1, col2 = st.columns(2)
    
    with col1:
        if view_type == "Trend":
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(
                x=analytics_data['date'], 
                y=analytics_data[metric_focus.lower()],
                name=f'Actual {metric_focus}',
                line=dict(color='#2563eb', width=2)
            ))
            fig_trend.add_trace(go.Scatter(
                x=analytics_data['date'], 
                y=analytics_data['trend'],
                name=f'{metric_focus} Trend',
                line=dict(color='#dc2626', width=3, dash='dash')
            ))
            
            fig_trend.update_layout(
                title=f"{metric_focus} Trend Analysis",
                xaxis_title="Date",
                yaxis_title=metric_focus,
                height=400
            )
            st.plotly_chart(fig_trend, use_container_width=True)
        
        elif view_type == "Distribution":
            fig_dist = px.histogram(
                analytics_data, 
                x=metric_focus.lower(),
                title=f"{metric_focus} Distribution",
                nbins=20,
                color_discrete_sequence=['#2563eb']
            )
            fig_dist.update_layout(height=400)
            st.plotly_chart(fig_dist, use_container_width=True)
        
        else:  # Comparison
            comparison_data = analytics_data.melt(
                id_vars=['date'], 
                value_vars=['users', 'sessions', 'requests'],
                var_name='metric', 
                value_name='value'
            )
            fig_comp = px.line(
                comparison_data, 
                x='date', 
                y='value', 
                color='metric',
                title="Metrics Comparison"
            )
            fig_comp.update_layout(height=400)
            st.plotly_chart(fig_comp, use_container_width=True)
    
    with col2:
        # Drill-down capabilities
        st.markdown("**📊 Detailed Breakdown**")
        
        # Top performing periods
        top_periods = analytics_data.nlargest(5, metric_focus.lower())
        st.markdown(f"**Top 5 {metric_focus} Periods:**")
        for idx, row in top_periods.iterrows():
            st.write(f"• {row['date'].strftime('%Y-%m-%d')}: {row[metric_focus.lower()]:,}")
        
        # Growth metrics
        if len(analytics_data) > 1:
            current_value = analytics_data[metric_focus.lower()].iloc[-1]
            previous_value = analytics_data[metric_focus.lower()].iloc[-2]
            growth_rate = ((current_value - previous_value) / previous_value) * 100
            
            st.markdown("**📈 Growth Metrics:**")
            st.metric(
                label=f"Latest {metric_focus}",
                value=f"{current_value:,}",
                delta=f"{growth_rate:+.1f}%"
            )
        
        # Statistical summary
        st.markdown("**📋 Statistical Summary:**")
        stats = analytics_data[metric_focus.lower()].describe()
        st.write(f"• Average: {stats['mean']:,.0f}")
        st.write(f"• Median: {stats['50%']:,.0f}")
        st.write(f"• Max: {stats['max']:,.0f}")
        st.write(f"• Min: {stats['min']:,.0f}")
        st.write(f"• Std Dev: {stats['std']:,.0f}")


def render_interactive_dashboard():
    """Interactive dashboard with real-time data and filters"""
    render_executive_dashboard()
    
    st.markdown("---")
    
    render_usage_analytics()
    
    # Auto-refresh toggle
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        auto_refresh = st.checkbox("🔄 Auto-refresh (30s)", value=False)
    with col2:
        if st.button("🔄 Refresh Now"):
            st.rerun()
    with col3:
        st.write(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
    
    if auto_refresh:
        time.sleep(30)
        st.rerun()
    
    # Generate sample data
    metrics_data, chat_data = generate_sample_data()
    
    # Interactive filters
    st.markdown("### 🎛️ Filters")
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    
    with filter_col1:
        date_range = st.date_input(
            "Date Range",
            value=(datetime(2024, 7, 1).date(), datetime(2024, 7, 19).date()),
            min_value=datetime(2024, 1, 1).date(),
            max_value=datetime(2024, 7, 19).date()
        )
    
    with filter_col2:
        metric_type = st.selectbox(
            "Metric Type",
            ["All", "CPU Usage", "Memory Usage", "Requests", "Response Time", "Errors"]
        )
    
    with filter_col3:
        search_term = st.text_input("🔍 Search", placeholder="Search data...")
    
    # Filter data based on selections
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_data = metrics_data[
            (metrics_data['date'].dt.date >= start_date) & 
            (metrics_data['date'].dt.date <= end_date)
        ]
    else:
        filtered_data = metrics_data
    
    # Real-time metrics cards
    st.markdown("### 📈 Live Metrics")
    metric_cols = st.columns(5)
    
    current_metrics = {
        'CPU': f"{filtered_data['cpu_usage'].iloc[-1]:.1f}%",
        'Memory': f"{filtered_data['memory_usage'].iloc[-1]:.1f}%",
        'Requests': f"{filtered_data['requests'].iloc[-1]:,}",
        'Response': f"{filtered_data['response_time'].iloc[-1]:.2f}s",
        'Errors': f"{filtered_data['errors'].iloc[-1]}"
    }
    
    for i, (label, value) in enumerate(current_metrics.items()):
        with metric_cols[i]:
            delta = np.random.choice([-1, 1]) * np.random.uniform(0.1, 5.0)
            st.metric(label, value, f"{delta:+.1f}")
    
    # Interactive charts
    st.markdown("### 📊 Interactive Visualizations")
    
    chart_tabs = st.tabs(["Time Series", "Distribution", "Correlation", "Real-time"])
    
    with chart_tabs[0]:
        # Time series chart with selection
        fig_ts = go.Figure()
        
        if metric_type == "All" or metric_type == "CPU Usage":
            fig_ts.add_trace(go.Scatter(
                x=filtered_data['date'], 
                y=filtered_data['cpu_usage'],
                name='CPU Usage (%)',
                line=dict(color='#2563eb')
            ))
        
        if metric_type == "All" or metric_type == "Memory Usage":
            fig_ts.add_trace(go.Scatter(
                x=filtered_data['date'], 
                y=filtered_data['memory_usage'],
                name='Memory Usage (%)',
                line=dict(color='#10b981')
            ))
        
        if metric_type == "All" or metric_type == "Requests":
            fig_ts.add_trace(go.Scatter(
                x=filtered_data['date'], 
                y=filtered_data['requests'],
                name='Requests',
                yaxis='y2',
                line=dict(color='#f59e0b')
            ))
        
        fig_ts.update_layout(
            title="System Metrics Over Time",
            xaxis_title="Date",
            yaxis_title="Percentage (%)",
            yaxis2=dict(title="Requests", overlaying='y', side='right'),
            hovermode='x unified',
            height=400
        )
        
        st.plotly_chart(fig_ts, use_container_width=True)
    
    with chart_tabs[1]:
        # Distribution charts
        col1, col2 = st.columns(2)
        
        with col1:
            fig_hist = px.histogram(
                filtered_data, 
                x='cpu_usage', 
                title='CPU Usage Distribution',
                nbins=20,
                color_discrete_sequence=['#2563eb']
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        
        with col2:
            fig_box = px.box(
                filtered_data.melt(
                    id_vars=['date'], 
                    value_vars=['cpu_usage', 'memory_usage'],
                    var_name='metric', 
                    value_name='value'
                ),
                x='metric', 
                y='value',
                title='Resource Usage Box Plot',
                color='metric'
            )
            st.plotly_chart(fig_box, use_container_width=True)
    
    with chart_tabs[2]:
        # Correlation heatmap
        corr_data = filtered_data[['cpu_usage', 'memory_usage', 'requests', 'response_time', 'errors']].corr()
        
        fig_heatmap = px.imshow(
            corr_data,
            title='Metrics Correlation Heatmap',
            color_continuous_scale='RdBu',
            aspect='auto'
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)
    
    with chart_tabs[3]:
        # Real-time updating chart
        st.markdown("**Live Data Stream** (Updates every 5 seconds)")
        
        # Placeholder for real-time data
        chart_placeholder = st.empty()
        
        # Simulate real-time data
        if st.button("Start Live Stream"):
            for i in range(10):
                # Generate new data point
                new_data = {
                    'time': datetime.now() - timedelta(seconds=i*5),
                    'value': np.random.normal(50, 10)
                }
                
                # Create simple line chart
                fig_live = go.Figure()
                fig_live.add_trace(go.Scatter(
                    x=[new_data['time']],
                    y=[new_data['value']],
                    mode='lines+markers',
                    name='Live Data'
                ))
                
                fig_live.update_layout(
                    title=f"Live Data - {new_data['time'].strftime('%H:%M:%S')}",
                    height=300
                )
                
                chart_placeholder.plotly_chart(fig_live, use_container_width=True)
                time.sleep(1)