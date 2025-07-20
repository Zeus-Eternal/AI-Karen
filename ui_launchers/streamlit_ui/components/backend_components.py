"""
Backend-Integrated UI Components
Components that seamlessly integrate with AI Karen backend services.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import asyncio
import json

from services.backend_integration import get_backend_service, run_async


def render_memory_explorer():
    """Render memory exploration interface with backend integration."""
    st.subheader("🧠 Memory Explorer")
    
    backend = get_backend_service()
    
    # Memory search interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query_text = st.text_input(
            "Search memories",
            placeholder="Enter your search query...",
            help="Search through your stored memories using semantic search"
        )
    
    with col2:
        search_button = st.button("🔍 Search", type="primary")
    
    # Advanced search options
    with st.expander("🔧 Advanced Search Options"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            top_k = st.slider("Max results", 1, 50, 10)
            similarity_threshold = st.slider("Similarity threshold", 0.0, 1.0, 0.7, 0.1)
        
        with col2:
            tags_input = st.text_input("Tags (comma-separated)", "")
            tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()]
        
        with col3:
            time_range_option = st.selectbox(
                "Time range",
                ["All time", "Last 24 hours", "Last week", "Last month"]
            )
    
    # Perform search
    if search_button and query_text:
        with st.spinner("Searching memories..."):
            # Convert time range
            time_range = None
            if time_range_option != "All time":
                end_time = datetime.now()
                if time_range_option == "Last 24 hours":
                    start_time = end_time - timedelta(hours=24)
                elif time_range_option == "Last week":
                    start_time = end_time - timedelta(weeks=1)
                elif time_range_option == "Last month":
                    start_time = end_time - timedelta(days=30)
                time_range = (start_time, end_time)
            
            # Search memories
            memories = run_async(backend.memory.query_memories(
                query_text=query_text,
                top_k=top_k,
                similarity_threshold=similarity_threshold,
                tags=tags if tags else None,
                time_range=time_range
            ))
            
            if memories:
                st.success(f"Found {len(memories)} matching memories")
                
                # Display results
                for i, memory in enumerate(memories):
                    with st.expander(f"Memory {i+1} (Score: {memory.get('similarity_score', 0):.3f})"):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.write(memory['content'])
                            
                            if memory.get('tags'):
                                st.write("**Tags:**", ", ".join(memory['tags']))
                            
                            if memory.get('metadata'):
                                st.write("**Metadata:**")
                                st.json(memory['metadata'])
                        
                        with col2:
                            st.write(f"**Created:** {datetime.fromtimestamp(memory['timestamp']).strftime('%Y-%m-%d %H:%M')}")
                            st.write(f"**User:** {memory.get('user_id', 'Unknown')}")
                            
                            if st.button(f"🗑️ Delete", key=f"delete_{memory['id']}"):
                                if run_async(backend.memory.delete_memory(memory['id'])):
                                    st.success("Memory deleted!")
                                    st.rerun()
                                else:
                                    st.error("Failed to delete memory")
            else:
                st.info("No memories found matching your search criteria")
    
    # Memory statistics
    st.markdown("---")
    st.subheader("📊 Memory Statistics")
    
    with st.spinner("Loading memory statistics..."):
        stats = run_async(backend.memory.get_memory_stats())
        
        if stats and "error" not in stats:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Memories", stats.get("total_memories", 0))
            
            with col2:
                st.metric("Recent (24h)", stats.get("recent_memories_24h", 0))
            
            with col3:
                st.metric("Expired", stats.get("expired_memories", 0))
            
            with col4:
                st.metric("Users", len(stats.get("memories_by_user", {})))
            
            # Memory by user chart
            if stats.get("memories_by_user"):
                user_data = stats["memories_by_user"]
                df = pd.DataFrame(list(user_data.items()), columns=["User", "Count"])
                
                fig = px.bar(df, x="User", y="Count", title="Memories by User")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("Failed to load memory statistics")


def render_plugin_manager():
    """Render plugin management interface with backend integration."""
    st.subheader("🧩 Plugin Manager")
    
    backend = get_backend_service()
    
    # Plugin execution interface
    st.markdown("### Execute Plugin")
    
    # Get available plugins
    plugins = backend.plugins.get_available_plugins()
    
    if plugins:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            selected_plugin = st.selectbox(
                "Select Plugin",
                options=[p["name"] for p in plugins],
                format_func=lambda x: next(p["description"] for p in plugins if p["name"] == x)
            )
        
        with col2:
            execute_button = st.button("▶️ Execute", type="primary")
        
        # Plugin parameters
        st.markdown("### Parameters")
        
        # Dynamic parameter input based on plugin
        parameters = {}
        
        # Common parameters for all plugins
        with st.expander("🔧 Plugin Parameters"):
            param_input = st.text_area(
                "Parameters (JSON format)",
                value="{}",
                help="Enter plugin parameters in JSON format"
            )
            
            try:
                parameters = json.loads(param_input) if param_input.strip() else {}
            except json.JSONDecodeError:
                st.error("Invalid JSON format in parameters")
                parameters = {}
        
        # Execute plugin
        if execute_button and selected_plugin:
            with st.spinner(f"Executing {selected_plugin}..."):
                result = run_async(backend.plugins.run_plugin(
                    plugin_name=selected_plugin,
                    parameters=parameters
                ))
                
                if result["success"]:
                    st.success(f"Plugin {selected_plugin} executed successfully!")
                    
                    # Display results
                    with st.expander("📋 Execution Results"):
                        st.write("**Result:**")
                        st.code(str(result["result"]))
                        
                        if result.get("stdout"):
                            st.write("**Standard Output:**")
                            st.code(result["stdout"])
                        
                        if result.get("stderr"):
                            st.write("**Standard Error:**")
                            st.code(result["stderr"])
                        
                        st.write(f"**Executed at:** {result['timestamp']}")
                else:
                    st.error(f"Plugin execution failed: {result.get('error', 'Unknown error')}")
        
        # Plugin list
        st.markdown("---")
        st.markdown("### Available Plugins")
        
        for plugin in plugins:
            with st.expander(f"{plugin['name']} - {plugin['description']}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Category:** {plugin.get('category', 'Unknown')}")
                    st.write(f"**Version:** {plugin.get('version', 'Unknown')}")
                    st.write(f"**Status:** {'✅ Enabled' if plugin.get('enabled') else '❌ Disabled'}")
                
                with col2:
                    if st.button(f"ℹ️ Details", key=f"details_{plugin['name']}"):
                        st.info(f"Plugin: {plugin['name']}\nMore details would be shown here.")
    else:
        st.warning("No plugins available")


def render_system_health():
    """Render system health monitoring with backend integration."""
    st.subheader("🏥 System Health")
    
    backend = get_backend_service()
    
    # Health check
    with st.spinner("Checking system health..."):
        health = run_async(backend.health_check())
    
    # Overall status
    overall_status = health.get("overall", "unknown")
    status_colors = {
        "healthy": "🟢",
        "degraded": "🟡", 
        "error": "🔴",
        "unknown": "⚪"
    }
    
    st.markdown(f"### Overall Status: {status_colors.get(overall_status, '⚪')} {overall_status.title()}")
    
    # Service status
    services = health.get("services", {})
    
    if services:
        col1, col2, col3 = st.columns(3)
        
        service_items = list(services.items())
        for i, (service_name, service_info) in enumerate(service_items):
            col = [col1, col2, col3][i % 3]
            
            with col:
                status = service_info.get("status", "unknown")
                status_icon = status_colors.get(status, "⚪")
                
                st.markdown(f"**{status_icon} {service_name.title()}**")
                st.write(f"Status: {status}")
                
                if "error" in service_info:
                    st.error(f"Error: {service_info['error']}")
                elif "details" in service_info:
                    details = service_info["details"]
                    if isinstance(details, dict):
                        for key, value in details.items():
                            if key != "error":
                                st.write(f"{key}: {value}")
    
    # System metrics
    st.markdown("---")
    st.markdown("### System Metrics")
    
    with st.spinner("Loading system metrics..."):
        metrics = run_async(backend.analytics.get_system_metrics())
    
    if metrics:
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            cpu_usage = metrics.get("cpu_usage", 0)
            st.metric("CPU Usage", f"{cpu_usage:.1f}%", delta=None)
        
        with col2:
            memory_usage = metrics.get("memory_usage", 0)
            st.metric("Memory Usage", f"{memory_usage:.1f}%", delta=None)
        
        with col3:
            active_sessions = metrics.get("active_sessions", 0)
            st.metric("Active Sessions", active_sessions)
        
        with col4:
            response_time = metrics.get("response_time_avg", 0)
            st.metric("Avg Response Time", f"{response_time:.2f}s")
        
        # Performance chart
        st.markdown("### Performance Trends")
        
        # Mock time series data for demonstration
        import numpy as np
        
        times = pd.date_range(start=datetime.now() - timedelta(hours=24), end=datetime.now(), freq='H')
        cpu_data = np.random.normal(cpu_usage, 10, len(times))
        memory_data = np.random.normal(memory_usage, 15, len(times))
        
        df = pd.DataFrame({
            'Time': times,
            'CPU Usage': np.clip(cpu_data, 0, 100),
            'Memory Usage': np.clip(memory_data, 0, 100)
        })
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['Time'],
            y=df['CPU Usage'],
            mode='lines',
            name='CPU Usage (%)',
            line=dict(color='#ff6b6b')
        ))
        
        fig.add_trace(go.Scatter(
            x=df['Time'],
            y=df['Memory Usage'],
            mode='lines',
            name='Memory Usage (%)',
            line=dict(color='#4ecdc4')
        ))
        
        fig.update_layout(
            title="System Performance (24h)",
            xaxis_title="Time",
            yaxis_title="Usage (%)",
            hovermode='x unified',
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)


def render_page_navigator():
    """Render dynamic page navigation based on backend page manifest."""
    st.subheader("🧭 Page Navigator")
    
    backend = get_backend_service()
    
    # Get available pages
    pages = backend.pages.get_available_pages()
    
    if pages:
        # Group pages by category
        categories = {}
        for page in pages:
            category = page.get("category", "general")
            if category not in categories:
                categories[category] = []
            categories[category].append(page)
        
        # Display pages by category
        for category, category_pages in categories.items():
            st.markdown(f"### {category.title()}")
            
            cols = st.columns(min(3, len(category_pages)))
            
            for i, page in enumerate(category_pages):
                col = cols[i % len(cols)]
                
                with col:
                    # Check access
                    has_access = backend.pages.check_page_access(page["route"])
                    
                    if has_access:
                        if st.button(
                            f"{page['icon']} {page['label']}",
                            key=f"nav_{page['route']}",
                            help=page.get("description", ""),
                            use_container_width=True
                        ):
                            st.session_state.current_page = page["route"]
                            st.rerun()
                    else:
                        st.button(
                            f"🔒 {page['label']}",
                            key=f"nav_locked_{page['route']}",
                            help="Access denied",
                            disabled=True,
                            use_container_width=True
                        )
    else:
        st.warning("No pages available")


def render_analytics_dashboard():
    """Render analytics dashboard with backend data."""
    st.subheader("📊 Analytics Dashboard")
    
    backend = get_backend_service()
    
    # Time range selector
    time_range = st.selectbox(
        "Time Range",
        ["24h", "7d", "30d"],
        format_func=lambda x: {"24h": "Last 24 hours", "7d": "Last 7 days", "30d": "Last 30 days"}[x]
    )
    
    # Load analytics data
    with st.spinner("Loading analytics data..."):
        analytics = run_async(backend.analytics.get_usage_analytics(time_range))
    
    if analytics:
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Interactions", analytics.get("total_interactions", 0))
        
        with col2:
            st.metric("Unique Users", analytics.get("unique_users", 0))
        
        with col3:
            satisfaction = analytics.get("user_satisfaction", 0)
            st.metric("User Satisfaction", f"{satisfaction:.1f}/5.0")
        
        with col4:
            peak_hour = max(analytics.get("peak_hours", [0]))
            st.metric("Peak Hour", f"{peak_hour}:00")
        
        # Feature usage chart
        popular_features = analytics.get("popular_features", [])
        if popular_features:
            st.markdown("### Feature Usage")
            
            df = pd.DataFrame(popular_features)
            fig = px.bar(
                df,
                x="name",
                y="usage_count",
                title="Most Popular Features",
                color="usage_count",
                color_continuous_scale="viridis"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Peak hours heatmap
        peak_hours = analytics.get("peak_hours", [])
        if peak_hours:
            st.markdown("### Usage Patterns")
            
            # Create hourly usage data
            hourly_data = [0] * 24
            for hour in peak_hours:
                if 0 <= hour < 24:
                    hourly_data[hour] = 1
            
            df_hours = pd.DataFrame({
                'Hour': list(range(24)),
                'Usage': hourly_data
            })
            
            fig = px.bar(
                df_hours,
                x="Hour",
                y="Usage",
                title="Peak Usage Hours",
                color="Usage",
                color_continuous_scale="blues"
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Failed to load analytics data")


def render_integrated_chat():
    """Render chat interface with memory integration."""
    st.subheader("💬 AI Chat with Memory")
    
    backend = get_backend_service()
    
    # Chat interface
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    
    # Display chat messages
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me anything..."):
        # Add user message
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.write(prompt)
        
        # Search relevant memories
        with st.spinner("Searching memories..."):
            relevant_memories = run_async(backend.memory.query_memories(
                query_text=prompt,
                top_k=3,
                similarity_threshold=0.6
            ))
        
        # Generate response (mock for now)
        response = f"I found {len(relevant_memories)} relevant memories. "
        if relevant_memories:
            response += "Based on your previous interactions: "
            for memory in relevant_memories[:2]:
                response += f"\n- {memory['content'][:100]}..."
        else:
            response += "This seems like a new topic for us to explore together."
        
        # Add assistant message
        st.session_state.chat_messages.append({"role": "assistant", "content": response})
        
        with st.chat_message("assistant"):
            st.write(response)
        
        # Store conversation in memory
        conversation_text = f"User: {prompt}\nAssistant: {response}"
        run_async(backend.memory.store_memory(
            content=conversation_text,
            tags=["conversation", "chat"],
            metadata={"type": "chat_interaction", "timestamp": datetime.now().isoformat()}
        ))
        
        st.rerun()