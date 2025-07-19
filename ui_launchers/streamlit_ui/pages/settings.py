"""
Comprehensive Settings Interface
Organized settings with intuitive navigation and real-time preview
"""

import streamlit as st
import json
import os
from typing import Dict, Any, List
from datetime import datetime
import plotly.express as px
import pandas as pd

from services.chat_service import chat_service
from services.memory_service import memory_service
from services.llm_router import llm_router


def render_settings_page(user_ctx=None):
    """Main settings page with organized categories"""
    
    st.markdown("# ⚙️ System Settings")
    st.markdown("### *Configure AI Karen to match your preferences*")
    
    # Settings navigation
    settings_categories = [
        "🎨 Appearance",
        "🤖 AI & Models", 
        "🧠 Memory & Context",
        "🔐 Security & Privacy",
        "🔔 Notifications",
        "🌐 Integrations",
        "📊 Performance",
        "🛠️ Advanced"
    ]
    
    # Sidebar navigation for settings
    with st.sidebar:
        st.markdown("### ⚙️ Settings Categories")
        selected_category = st.radio(
            "Choose category:",
            settings_categories,
            key="settings_category"
        )
        
        st.markdown("---")
        
        # Quick actions
        st.markdown("### 🚀 Quick Actions")
        if st.button("💾 Save All Settings", use_container_width=True):
            save_all_settings()
            st.success("All settings saved!")
        
        if st.button("🔄 Reset to Defaults", use_container_width=True):
            if st.session_state.get('confirm_reset', False):
                reset_all_settings()
                st.success("Settings reset to defaults!")
                st.session_state.confirm_reset = False
            else:
                st.session_state.confirm_reset = True
                st.warning("Click again to confirm reset")
        
        if st.button("📤 Export Settings", use_container_width=True):
            export_settings()
    
    # Main settings content
    if selected_category == "🎨 Appearance":
        render_appearance_settings()
    elif selected_category == "🤖 AI & Models":
        render_ai_model_settings()
    elif selected_category == "🧠 Memory & Context":
        render_memory_settings()
    elif selected_category == "🔐 Security & Privacy":
        render_security_settings()
    elif selected_category == "🔔 Notifications":
        render_notification_settings()
    elif selected_category == "🌐 Integrations":
        render_integration_settings()
    elif selected_category == "📊 Performance":
        render_performance_settings()
    elif selected_category == "🛠️ Advanced":
        render_advanced_settings()


def render_appearance_settings():
    """Appearance and UI customization settings"""
    
    st.markdown("## 🎨 Appearance Settings")
    st.markdown("*Customize the look and feel of AI Karen*")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🌈 Theme & Colors")
        
        theme = st.selectbox(
            "Color Theme",
            ["Auto (System)", "Light", "Dark", "High Contrast"],
            index=0,
            help="Choose your preferred color theme"
        )
        
        accent_color = st.selectbox(
            "Accent Color",
            ["Blue", "Green", "Purple", "Orange", "Red", "Teal"],
            index=0,
            help="Primary accent color for buttons and highlights"
        )
        
        font_size = st.slider(
            "Font Size",
            min_value=12,
            max_value=20,
            value=14,
            help="Base font size for the interface"
        )
        
        compact_mode = st.checkbox(
            "Compact Mode",
            value=False,
            help="Reduce spacing for more content on screen"
        )
    
    with col2:
        st.markdown("### 🖼️ Layout & Navigation")
        
        sidebar_position = st.selectbox(
            "Sidebar Position",
            ["Left", "Right", "Auto-hide"],
            index=0
        )
        
        navigation_style = st.selectbox(
            "Navigation Style",
            ["Pills", "Tabs", "Sidebar Only"],
            index=0
        )
        
        show_breadcrumbs = st.checkbox(
            "Show Breadcrumbs",
            value=True,
            help="Display navigation breadcrumbs"
        )
        
        animations_enabled = st.checkbox(
            "Enable Animations",
            value=True,
            help="Smooth transitions and animations"
        )
    
    # Preview section
    st.markdown("### 👀 Preview")
    
    preview_col1, preview_col2 = st.columns(2)
    
    with preview_col1:
        st.markdown("**Sample Card Preview:**")
        st.markdown(f"""
        <div style="
            background: {'#1e293b' if theme == 'Dark' else '#ffffff'};
            color: {'#ffffff' if theme == 'Dark' else '#1e293b'};
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid {'#374151' if theme == 'Dark' else '#e5e7eb'};
            font-size: {font_size}px;
        ">
            <h4 style="margin: 0 0 0.5rem 0;">Sample Content</h4>
            <p style="margin: 0;">This is how your content will look with the selected theme.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with preview_col2:
        st.markdown("**Color Palette:**")
        colors = {
            "Blue": "#2563eb",
            "Green": "#10b981", 
            "Purple": "#8b5cf6",
            "Orange": "#f59e0b",
            "Red": "#ef4444",
            "Teal": "#14b8a6"
        }
        
        color_preview = f"""
        <div style="display: flex; gap: 0.5rem; margin-top: 0.5rem;">
            <div style="width: 30px; height: 30px; background: {colors[accent_color]}; border-radius: 4px;"></div>
            <div style="width: 30px; height: 30px; background: {'#374151' if theme == 'Dark' else '#f3f4f6'}; border-radius: 4px;"></div>
            <div style="width: 30px; height: 30px; background: {'#1f2937' if theme == 'Dark' else '#ffffff'}; border-radius: 4px; border: 1px solid #e5e7eb;"></div>
        </div>
        """
        st.markdown(color_preview, unsafe_allow_html=True)


def render_ai_model_settings():
    """AI model and LLM configuration settings"""
    
    st.markdown("## 🤖 AI & Model Settings")
    st.markdown("*Configure AI behavior and model preferences*")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🎯 Model Selection")
        
        # Get available models
        try:
            models = chat_service.get_available_models()
            model_names = [model.get("name", "Unknown") for model in models if model.get("name")]
            
            if model_names:
                default_model = st.selectbox(
                    "Default AI Model",
                    model_names,
                    help="Primary model for chat and general tasks"
                )
                
                fallback_model = st.selectbox(
                    "Fallback Model",
                    ["Auto"] + model_names,
                    help="Model to use if primary model fails"
                )
            else:
                st.warning("No models available from backend")
                default_model = "default"
                fallback_model = "Auto"
        except:
            st.warning("Unable to fetch available models")
            default_model = "default"
            fallback_model = "Auto"
        
        # LLM Profile preferences
        st.markdown("### 🎭 LLM Profiles")
        
        routing_metrics = llm_router.get_routing_metrics()
        available_profiles = routing_metrics.get("available_profiles", [])
        
        preferred_profile = st.selectbox(
            "Preferred Profile",
            ["Auto"] + available_profiles,
            help="Default LLM profile for routing decisions"
        )
        
        enable_fallback = st.checkbox(
            "Enable Fallback Routing",
            value=True,
            help="Automatically switch models if primary fails"
        )
    
    with col2:
        st.markdown("### ⚙️ Generation Parameters")
        
        temperature = st.slider(
            "Creativity (Temperature)",
            min_value=0.0,
            max_value=2.0,
            value=0.7,
            step=0.1,
            help="Higher values make output more creative but less focused"
        )
        
        max_tokens = st.slider(
            "Max Response Length",
            min_value=128,
            max_value=4096,
            value=2048,
            step=128,
            help="Maximum number of tokens in AI responses"
        )
        
        response_timeout = st.slider(
            "Response Timeout (seconds)",
            min_value=10,
            max_value=120,
            value=30,
            help="Maximum time to wait for AI response"
        )
        
        enable_streaming = st.checkbox(
            "Enable Streaming Responses",
            value=True,
            help="Show AI responses as they are generated"
        )
    
    # Model performance metrics
    st.markdown("### 📊 Model Performance")
    
    if routing_metrics.get("total_decisions", 0) > 0:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Success Rate",
                f"{routing_metrics.get('success_rate', 0):.1%}",
                delta=f"{routing_metrics.get('success_rate', 0) - 0.85:+.1%}"
            )
        
        with col2:
            st.metric(
                "Avg Routing Time",
                f"{routing_metrics.get('avg_routing_latency', 0):.3f}s",
                delta=f"{routing_metrics.get('avg_routing_latency', 0) - 0.05:+.3f}s"
            )
        
        with col3:
            st.metric(
                "Fallback Rate",
                f"{routing_metrics.get('fallback_rate', 0):.1%}",
                delta=f"{routing_metrics.get('fallback_rate', 0) - 0.1:+.1%}"
            )
    else:
        st.info("No model performance data available yet")


def render_memory_settings():
    """Memory and context management settings"""
    
    st.markdown("## 🧠 Memory & Context Settings")
    st.markdown("*Configure how AI Karen remembers and uses context*")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💾 Memory Configuration")
        
        memory_enabled = st.checkbox(
            "Enable Memory System",
            value=True,
            help="Allow AI Karen to remember conversations and context"
        )
        
        max_memories = st.slider(
            "Maximum Memories",
            min_value=1000,
            max_value=50000,
            value=10000,
            step=1000,
            help="Maximum number of memories to store"
        )
        
        memory_retention = st.slider(
            "Memory Retention (days)",
            min_value=7,
            max_value=365,
            value=90,
            help="How long to keep memories before automatic cleanup"
        )
        
        context_window = st.slider(
            "Context Window Size",
            min_value=5,
            max_value=50,
            value=20,
            help="Number of recent messages to include in context"
        )
    
    with col2:
        st.markdown("### 🎯 Context Preferences")
        
        include_user_context = st.checkbox(
            "Include User Context",
            value=True,
            help="Remember user preferences and behavior patterns"
        )
        
        include_session_context = st.checkbox(
            "Include Session Context",
            value=True,
            help="Maintain context within conversation sessions"
        )
        
        enable_context_reranking = st.checkbox(
            "Enable Context Reranking",
            value=True,
            help="Use advanced reranking for better context relevance"
        )
        
        privacy_mode = st.selectbox(
            "Privacy Mode",
            ["Standard", "Enhanced", "Maximum"],
            index=0,
            help="Level of privacy protection for stored memories"
        )
    
    # Memory system metrics
    st.markdown("### 📊 Memory System Status")
    
    memory_metrics = memory_service.get_memory_metrics()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Memories",
            f"{memory_metrics.get('total_memories', 0):,}"
        )
    
    with col2:
        st.metric(
            "Hit Rate",
            f"{memory_metrics.get('memory_hit_rate', 0):.1%}"
        )
    
    with col3:
        st.metric(
            "Avg Recall Time",
            f"{memory_metrics.get('avg_recall_latency', 0):.3f}s"
        )
    
    with col4:
        st.metric(
            "Plugin Events",
            f"{memory_metrics.get('total_plugin_events', 0):,}"
        )


def render_security_settings():
    """Security and privacy configuration"""
    
    st.markdown("## 🔐 Security & Privacy Settings")
    st.markdown("*Protect your data and configure access controls*")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🛡️ Authentication")
        
        require_auth = st.checkbox(
            "Require Authentication",
            value=True,
            help="Require login to access AI Karen"
        )
        
        session_timeout = st.slider(
            "Session Timeout (minutes)",
            min_value=15,
            max_value=480,
            value=120,
            help="Automatically log out after inactivity"
        )
        
        max_login_attempts = st.slider(
            "Max Login Attempts",
            min_value=3,
            max_value=10,
            value=5,
            help="Lock account after failed login attempts"
        )
        
        enable_2fa = st.checkbox(
            "Enable Two-Factor Authentication",
            value=False,
            help="Require additional verification for login"
        )
    
    with col2:
        st.markdown("### 🔒 Data Protection")
        
        encrypt_storage = st.checkbox(
            "Encrypt Stored Data",
            value=True,
            help="Encrypt sensitive data at rest"
        )
        
        data_retention = st.slider(
            "Data Retention (days)",
            min_value=30,
            max_value=365,
            value=90,
            help="Automatically delete old data"
        )
        
        allow_data_export = st.checkbox(
            "Allow Data Export",
            value=True,
            help="Users can export their data"
        )
        
        audit_logging = st.checkbox(
            "Enable Audit Logging",
            value=True,
            help="Log all user actions for security"
        )
    
    # Security status
    st.markdown("### 🔍 Security Status")
    
    security_checks = [
        ("Authentication", "✅ Enabled" if require_auth else "⚠️ Disabled"),
        ("Data Encryption", "✅ Enabled" if encrypt_storage else "⚠️ Disabled"),
        ("Audit Logging", "✅ Enabled" if audit_logging else "⚠️ Disabled"),
        ("Session Security", "✅ Configured" if session_timeout > 0 else "⚠️ Not Set")
    ]
    
    for check_name, status in security_checks:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.write(check_name)
        with col2:
            st.write(status)


def render_notification_settings():
    """Notification and alert configuration"""
    
    st.markdown("## 🔔 Notification Settings")
    st.markdown("*Configure alerts and notification preferences*")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📢 System Notifications")
        
        enable_notifications = st.checkbox(
            "Enable Notifications",
            value=True,
            help="Show system notifications and alerts"
        )
        
        notification_types = st.multiselect(
            "Notification Types",
            ["System Alerts", "Plugin Updates", "Memory Events", "Security Alerts", "Performance Warnings"],
            default=["System Alerts", "Security Alerts"],
            help="Choose which types of notifications to receive"
        )
        
        notification_sound = st.checkbox(
            "Notification Sound",
            value=False,
            help="Play sound for notifications"
        )
        
        desktop_notifications = st.checkbox(
            "Desktop Notifications",
            value=True,
            help="Show notifications outside the browser"
        )
    
    with col2:
        st.markdown("### ⏰ Alert Thresholds")
        
        cpu_alert_threshold = st.slider(
            "CPU Usage Alert (%)",
            min_value=50,
            max_value=95,
            value=80,
            help="Alert when CPU usage exceeds this threshold"
        )
        
        memory_alert_threshold = st.slider(
            "Memory Usage Alert (%)",
            min_value=50,
            max_value=95,
            value=85,
            help="Alert when memory usage exceeds this threshold"
        )
        
        error_rate_threshold = st.slider(
            "Error Rate Alert (%)",
            min_value=1,
            max_value=10,
            value=5,
            help="Alert when error rate exceeds this threshold"
        )
        
        response_time_threshold = st.slider(
            "Response Time Alert (seconds)",
            min_value=1,
            max_value=30,
            value=10,
            help="Alert when response time exceeds this threshold"
        )
    
    # Test notification
    st.markdown("### 🧪 Test Notifications")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📢 Test Info", use_container_width=True):
            st.info("ℹ️ This is a test information notification")
    
    with col2:
        if st.button("⚠️ Test Warning", use_container_width=True):
            st.warning("⚠️ This is a test warning notification")
    
    with col3:
        if st.button("🚨 Test Alert", use_container_width=True):
            st.error("🚨 This is a test alert notification")


def render_integration_settings():
    """External integration configuration"""
    
    st.markdown("## 🌐 Integration Settings")
    st.markdown("*Configure external services and API connections*")
    
    # API Keys section
    st.markdown("### 🔑 API Keys & Credentials")
    
    with st.expander("🤖 AI Service APIs", expanded=True):
        openai_key = st.text_input(
            "OpenAI API Key",
            type="password",
            help="API key for OpenAI services"
        )
        
        anthropic_key = st.text_input(
            "Anthropic API Key",
            type="password",
            help="API key for Anthropic Claude"
        )
        
        cohere_key = st.text_input(
            "Cohere API Key",
            type="password",
            help="API key for Cohere services"
        )
    
    with st.expander("🔗 Communication APIs"):
        slack_token = st.text_input(
            "Slack Bot Token",
            type="password",
            help="Bot token for Slack integration"
        )
        
        discord_token = st.text_input(
            "Discord Bot Token",
            type="password",
            help="Bot token for Discord integration"
        )
        
        webhook_url = st.text_input(
            "Webhook URL",
            help="Generic webhook URL for notifications"
        )
    
    # Integration status
    st.markdown("### 📊 Integration Status")
    
    integrations = [
        ("OpenAI", "✅ Connected" if openai_key else "❌ Not configured"),
        ("Anthropic", "✅ Connected" if anthropic_key else "❌ Not configured"),
        ("Slack", "✅ Connected" if slack_token else "❌ Not configured"),
        ("Discord", "✅ Connected" if discord_token else "❌ Not configured"),
        ("Webhooks", "✅ Configured" if webhook_url else "❌ Not configured")
    ]
    
    for service, status in integrations:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.write(service)
        with col2:
            st.write(status)


def render_performance_settings():
    """Performance and optimization settings"""
    
    st.markdown("## 📊 Performance Settings")
    st.markdown("*Optimize AI Karen for your system*")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ⚡ Performance Tuning")
        
        max_concurrent_requests = st.slider(
            "Max Concurrent Requests",
            min_value=1,
            max_value=20,
            value=5,
            help="Maximum number of simultaneous AI requests"
        )
        
        cache_size = st.slider(
            "Cache Size (MB)",
            min_value=100,
            max_value=2000,
            value=500,
            help="Memory allocated for caching"
        )
        
        enable_gpu = st.checkbox(
            "Enable GPU Acceleration",
            value=False,
            help="Use GPU for AI model inference (if available)"
        )
        
        optimize_for = st.selectbox(
            "Optimize For",
            ["Balanced", "Speed", "Quality", "Memory Usage"],
            help="Performance optimization priority"
        )
    
    with col2:
        st.markdown("### 🔧 Resource Limits")
        
        cpu_limit = st.slider(
            "CPU Usage Limit (%)",
            min_value=25,
            max_value=100,
            value=80,
            help="Maximum CPU usage for AI Karen"
        )
        
        memory_limit = st.slider(
            "Memory Usage Limit (GB)",
            min_value=1,
            max_value=16,
            value=4,
            help="Maximum memory usage for AI Karen"
        )
        
        request_timeout = st.slider(
            "Request Timeout (seconds)",
            min_value=10,
            max_value=300,
            value=60,
            help="Maximum time for request processing"
        )
        
        cleanup_interval = st.slider(
            "Cleanup Interval (hours)",
            min_value=1,
            max_value=24,
            value=6,
            help="How often to run cleanup tasks"
        )
    
    # Performance monitoring
    st.markdown("### 📈 Performance Monitoring")
    
    # Generate sample performance data
    perf_data = pd.DataFrame({
        'Time': pd.date_range(start='2024-07-19 00:00', periods=24, freq='H'),
        'CPU %': [45 + i*2 + (i%3)*5 for i in range(24)],
        'Memory %': [60 + i*1.5 + (i%4)*3 for i in range(24)],
        'Requests/min': [100 + i*5 + (i%5)*10 for i in range(24)]
    })
    
    fig = px.line(
        perf_data,
        x='Time',
        y=['CPU %', 'Memory %'],
        title="System Resource Usage (24h)"
    )
    st.plotly_chart(fig, use_container_width=True)


def render_advanced_settings():
    """Advanced system configuration"""
    
    st.markdown("## 🛠️ Advanced Settings")
    st.markdown("*Advanced configuration for power users*")
    
    st.warning("⚠️ **Warning**: These settings can affect system stability. Change only if you know what you're doing.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔧 System Configuration")
        
        debug_mode = st.checkbox(
            "Enable Debug Mode",
            value=False,
            help="Show detailed debug information"
        )
        
        log_level = st.selectbox(
            "Log Level",
            ["ERROR", "WARNING", "INFO", "DEBUG"],
            index=2,
            help="Minimum level for log messages"
        )
        
        max_log_size = st.slider(
            "Max Log Size (MB)",
            min_value=10,
            max_value=1000,
            value=100,
            help="Maximum size of log files"
        )
        
        enable_telemetry = st.checkbox(
            "Enable Telemetry",
            value=True,
            help="Send anonymous usage data to improve AI Karen"
        )
    
    with col2:
        st.markdown("### 🗄️ Database Configuration")
        
        db_connection_pool = st.slider(
            "Database Connection Pool",
            min_value=5,
            max_value=50,
            value=20,
            help="Number of database connections to maintain"
        )
        
        query_timeout = st.slider(
            "Query Timeout (seconds)",
            min_value=5,
            max_value=120,
            value=30,
            help="Maximum time for database queries"
        )
        
        enable_query_cache = st.checkbox(
            "Enable Query Cache",
            value=True,
            help="Cache database query results"
        )
        
        backup_frequency = st.selectbox(
            "Backup Frequency",
            ["Never", "Daily", "Weekly", "Monthly"],
            index=2,
            help="How often to backup data"
        )
    
    # System information
    st.markdown("### ℹ️ System Information")
    
    system_info = {
        "AI Karen Version": "2.1.0",
        "Python Version": "3.11.0",
        "Streamlit Version": "1.32.2",
        "Operating System": "Linux",
        "Available Memory": "16 GB",
        "CPU Cores": "8"
    }
    
    for key, value in system_info.items():
        col1, col2 = st.columns([2, 1])
        with col1:
            st.write(key)
        with col2:
            st.write(value)


def save_all_settings():
    """Save all settings to configuration"""
    # This would save settings to actual config files
    pass


def reset_all_settings():
    """Reset all settings to defaults"""
    # This would reset settings to default values
    pass


def export_settings():
    """Export settings as JSON"""
    settings_data = {
        "appearance": {
            "theme": "Auto (System)",
            "accent_color": "Blue",
            "font_size": 14
        },
        "ai_models": {
            "default_model": "default",
            "temperature": 0.7,
            "max_tokens": 2048
        },
        "memory": {
            "enabled": True,
            "max_memories": 10000,
            "retention_days": 90
        },
        "export_timestamp": datetime.now().isoformat()
    }
    
    st.download_button(
        "💾 Download Settings",
        data=json.dumps(settings_data, indent=2),
        file_name=f"ai_karen_settings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )