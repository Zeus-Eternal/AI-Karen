"""
Plugin Marketplace and Management Interface
Visual plugin discovery, installation, and configuration
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, Any
import json

from services.plugin_service import plugin_service, PluginInfo


def render_plugin_marketplace():
    """Main plugin marketplace interface"""
    
    st.markdown("# 🧩 Plugin Marketplace")
    st.markdown("### *Discover, install, and manage AI Karen plugins*")
    
    # Plugin metrics overview
    metrics = plugin_service.get_plugin_metrics()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📦 Available Plugins", metrics["total_available"])
    with col2:
        st.metric("✅ Installed", metrics["total_installed"], 
                 delta=f"+{metrics['total_installed'] - metrics['total_enabled']} disabled")
    with col3:
        st.metric("🟢 Active", metrics["total_enabled"])
    with col4:
        st.metric("📂 Categories", metrics["categories"])
    
    st.markdown("---")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["🛒 Marketplace", "📦 Installed", "⚙️ Configuration", "📊 Analytics"])
    
    with tab1:
        render_marketplace_browser()
    
    with tab2:
        render_installed_plugins()
    
    with tab3:
        render_plugin_configuration()
    
    with tab4:
        render_plugin_analytics()


def render_marketplace_browser():
    """Plugin marketplace browser"""
    
    st.markdown("## 🛒 Browse Plugins")
    
    # Search and filter controls
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_query = st.text_input("🔍 Search plugins", placeholder="Search by name, description, or tags...")
    
    with col2:
        categories = plugin_service.get_plugin_categories()
        selected_category = st.selectbox("📂 Category", categories)
    
    with col3:
        sort_by = st.selectbox("🔄 Sort by", ["Rating", "Downloads", "Name", "Updated"])
    
    # Get filtered plugins
    plugins = plugin_service.get_available_plugins(
        category=selected_category if selected_category != "All" else None,
        search_query=search_query if search_query else None
    )
    
    # Sort plugins
    if sort_by == "Rating":
        plugins.sort(key=lambda x: x.rating, reverse=True)
    elif sort_by == "Downloads":
        plugins.sort(key=lambda x: x.downloads, reverse=True)
    elif sort_by == "Name":
        plugins.sort(key=lambda x: x.name)
    elif sort_by == "Updated":
        plugins.sort(key=lambda x: x.last_updated, reverse=True)
    
    if not plugins:
        st.info("No plugins found matching your criteria.")
        return
    
    # Display plugins in a grid
    cols_per_row = 2
    for i in range(0, len(plugins), cols_per_row):
        cols = st.columns(cols_per_row)
        
        for j, col in enumerate(cols):
            if i + j < len(plugins):
                plugin = plugins[i + j]
                with col:
                    render_plugin_card(plugin)


def render_plugin_card(plugin: PluginInfo):
    """Render individual plugin card"""
    
    # Plugin card container
    with st.container():
        st.markdown(f"""
        <div style="
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            background: white;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        ">
        </div>
        """, unsafe_allow_html=True)
        
        # Plugin header
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.markdown(f"<div style='font-size: 3rem; text-align: center;'>{plugin.icon}</div>", 
                       unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"**{plugin.name}** `v{plugin.version}`")
            st.markdown(f"*by {plugin.author}*")
            
            # Rating and downloads
            stars = "⭐" * int(plugin.rating) + "☆" * (5 - int(plugin.rating))
            st.markdown(f"{stars} {plugin.rating:.1f} • {plugin.downloads:,} downloads")
        
        # Description
        st.markdown(plugin.description)
        
        # Tags
        if plugin.tags:
            tag_html = " ".join([f"<span style='background: #e2e8f0; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.8rem; margin-right: 0.3rem;'>{tag}</span>" for tag in plugin.tags[:4]])
            st.markdown(tag_html, unsafe_allow_html=True)
        
        # Plugin details
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**Category:** {plugin.category}")
        with col2:
            st.markdown(f"**Size:** {plugin.install_size}")
        with col3:
            st.markdown(f"**License:** {plugin.license}")
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if plugin.installed:
                if plugin.enabled:
                    if st.button("🔴 Disable", key=f"disable_{plugin.id}", use_container_width=True):
                        if plugin_service.disable_plugin(plugin.id):
                            st.success(f"Disabled {plugin.name}")
                            st.rerun()
                else:
                    if st.button("🟢 Enable", key=f"enable_{plugin.id}", use_container_width=True):
                        if plugin_service.enable_plugin(plugin.id):
                            st.success(f"Enabled {plugin.name}")
                            st.rerun()
            else:
                if st.button("📥 Install", key=f"install_{plugin.id}", use_container_width=True, type="primary"):
                    with st.spinner(f"Installing {plugin.name}..."):
                        installation = plugin_service.install_plugin(plugin.id)
                        if installation.status == "installed":
                            st.success(f"Successfully installed {plugin.name}!")
                            st.rerun()
                        else:
                            st.error(f"Installation failed: {installation.message}")
        
        with col2:
            if st.button("ℹ️ Details", key=f"details_{plugin.id}", use_container_width=True):
                st.session_state[f"show_details_{plugin.id}"] = True
        
        with col3:
            if plugin.installed:
                if st.button("🗑️ Uninstall", key=f"uninstall_{plugin.id}", use_container_width=True):
                    if plugin_service.uninstall_plugin(plugin.id):
                        st.success(f"Uninstalled {plugin.name}")
                        st.rerun()
        
        # Show details modal
        if st.session_state.get(f"show_details_{plugin.id}", False):
            render_plugin_details_modal(plugin)


def render_plugin_details_modal(plugin: PluginInfo):
    """Render plugin details modal"""
    
    with st.expander(f"📋 {plugin.name} Details", expanded=True):
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 Plugin Information")
            st.markdown(f"**Name:** {plugin.name}")
            st.markdown(f"**Version:** {plugin.version}")
            st.markdown(f"**Author:** {plugin.author}")
            st.markdown(f"**Category:** {plugin.category}")
            st.markdown(f"**License:** {plugin.license}")
            st.markdown(f"**Install Size:** {plugin.install_size}")
            st.markdown(f"**Last Updated:** {plugin.last_updated.strftime('%Y-%m-%d')}")
            
            if plugin.dependencies:
                st.markdown("**Dependencies:**")
                for dep in plugin.dependencies:
                    st.markdown(f"- `{dep}`")
        
        with col2:
            st.markdown("### 🏷️ Tags & Links")
            
            if plugin.tags:
                st.markdown("**Tags:**")
                tag_html = " ".join([f"<span style='background: #2563eb; color: white; padding: 0.3rem 0.6rem; border-radius: 6px; font-size: 0.8rem; margin-right: 0.5rem; margin-bottom: 0.3rem; display: inline-block;'>{tag}</span>" for tag in plugin.tags])
                st.markdown(tag_html, unsafe_allow_html=True)
            
            st.markdown("**Links:**")
            if plugin.documentation_url:
                st.markdown(f"📖 [Documentation]({plugin.documentation_url})")
            if plugin.source_url:
                st.markdown(f"💻 [Source Code]({plugin.source_url})")
        
        st.markdown("### 📝 Description")
        st.markdown(plugin.description)
        
        # Installation status
        if plugin.installed:
            status_color = "🟢" if plugin.enabled else "🟡"
            status_text = "Enabled" if plugin.enabled else "Disabled"
            st.markdown(f"**Status:** {status_color} {status_text}")
        
        if st.button("❌ Close Details", key=f"close_details_{plugin.id}"):
            st.session_state[f"show_details_{plugin.id}"] = False
            st.rerun()


def render_installed_plugins():
    """Installed plugins management"""
    
    st.markdown("## 📦 Installed Plugins")
    
    installed_plugins = list(plugin_service.installed_plugins.values())
    
    if not installed_plugins:
        st.info("No plugins installed yet. Visit the Marketplace to install plugins.")
        return
    
    # Plugin status overview
    enabled_count = sum(1 for p in installed_plugins if p.enabled)
    disabled_count = len(installed_plugins) - enabled_count
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Installed", len(installed_plugins))
    with col2:
        st.metric("🟢 Enabled", enabled_count)
    with col3:
        st.metric("🔴 Disabled", disabled_count)
    
    st.markdown("---")
    
    # Installed plugins table
    plugin_data = []
    for plugin in installed_plugins:
        plugin_data.append({
            "Plugin": f"{plugin.icon} {plugin.name}",
            "Version": plugin.version,
            "Category": plugin.category,
            "Status": "🟢 Enabled" if plugin.enabled else "🔴 Disabled",
            "Config Required": "⚙️ Yes" if plugin.config_required else "✅ No"
        })
    
    if plugin_data:
        df = pd.DataFrame(plugin_data)
        st.dataframe(df, use_container_width=True)
        
        # Bulk actions
        st.markdown("### 🔧 Bulk Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🟢 Enable All", use_container_width=True):
                for plugin in installed_plugins:
                    plugin_service.enable_plugin(plugin.id)
                st.success("All plugins enabled!")
                st.rerun()
        
        with col2:
            if st.button("🔴 Disable All", use_container_width=True):
                for plugin in installed_plugins:
                    plugin_service.disable_plugin(plugin.id)
                st.success("All plugins disabled!")
                st.rerun()
        
        with col3:
            if st.button("🔄 Refresh Status", use_container_width=True):
                st.rerun()


def render_plugin_configuration():
    """Plugin configuration interface"""
    
    st.markdown("## ⚙️ Plugin Configuration")
    
    # Get plugins that require configuration
    config_plugins = [p for p in plugin_service.installed_plugins.values() if p.config_required]
    
    if not config_plugins:
        st.info("No installed plugins require configuration.")
        return
    
    # Plugin selector
    plugin_names = [f"{p.icon} {p.name}" for p in config_plugins]
    selected_plugin_name = st.selectbox("Select plugin to configure:", plugin_names)
    
    if not selected_plugin_name:
        return
    
    # Find selected plugin
    selected_plugin = next(p for p in config_plugins if f"{p.icon} {p.name}" == selected_plugin_name)
    
    st.markdown(f"### ⚙️ Configuring {selected_plugin.name}")
    
    # Get configuration schema
    config_schema = plugin_service.get_plugin_config_schema(selected_plugin.id)
    
    if not config_schema:
        st.warning("No configuration schema available for this plugin.")
        return
    
    # Render configuration form
    config_values = {}
    
    with st.form(f"config_form_{selected_plugin.id}"):
        st.markdown("**Configuration Settings:**")
        
        for field_name, field_config in config_schema.items():
            field_type = field_config.get("type", "string")
            field_label = field_name.replace("_", " ").title()
            field_help = field_config.get("description", "")
            field_required = field_config.get("required", False)
            
            if field_required:
                field_label += " *"
            
            if field_type == "string":
                config_values[field_name] = st.text_input(
                    field_label,
                    value=field_config.get("default", ""),
                    help=field_help,
                    type="password" if "key" in field_name.lower() or "password" in field_name.lower() else "default"
                )
            elif field_type == "number":
                config_values[field_name] = st.number_input(
                    field_label,
                    value=field_config.get("default", 0),
                    min_value=field_config.get("min", None),
                    max_value=field_config.get("max", None),
                    help=field_help
                )
            elif field_type == "boolean":
                config_values[field_name] = st.checkbox(
                    field_label,
                    value=field_config.get("default", False),
                    help=field_help
                )
            elif field_type == "select":
                options = field_config.get("options", [])
                default_index = 0
                if "default" in field_config and field_config["default"] in options:
                    default_index = options.index(field_config["default"])
                
                config_values[field_name] = st.selectbox(
                    field_label,
                    options,
                    index=default_index,
                    help=field_help
                )
        
        # Form submission
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("💾 Save Configuration", type="primary", use_container_width=True):
                # Validate required fields
                missing_fields = []
                for field_name, field_config in config_schema.items():
                    if field_config.get("required", False) and not config_values.get(field_name):
                        missing_fields.append(field_name.replace("_", " ").title())
                
                if missing_fields:
                    st.error(f"Please fill in required fields: {', '.join(missing_fields)}")
                else:
                    if plugin_service.save_plugin_config(selected_plugin.id, config_values):
                        st.success(f"Configuration saved for {selected_plugin.name}!")
                    else:
                        st.error("Failed to save configuration.")
        
        with col2:
            if st.form_submit_button("🔄 Reset to Defaults", use_container_width=True):
                st.rerun()


def render_plugin_analytics():
    """Plugin usage analytics"""
    
    st.markdown("## 📊 Plugin Analytics")
    
    metrics = plugin_service.get_plugin_metrics()
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Available", metrics["total_available"])
    with col2:
        st.metric("Installation Rate", f"{(metrics['total_installed'] / metrics['total_available'] * 100):.1f}%")
    with col3:
        st.metric("Activation Rate", f"{(metrics['total_enabled'] / max(metrics['total_installed'], 1) * 100):.1f}%")
    with col4:
        st.metric("Failed Installs", metrics["failed_installations"])
    
    # Plugin category distribution
    plugins = plugin_service.get_available_plugins()
    category_data = {}
    for plugin in plugins:
        category_data[plugin.category] = category_data.get(plugin.category, 0) + 1
    
    if category_data:
        import plotly.express as px
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.pie(
                values=list(category_data.values()),
                names=list(category_data.keys()),
                title="Plugin Categories Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Installation status
            status_data = {
                "Installed": metrics["total_installed"],
                "Not Installed": metrics["total_available"] - metrics["total_installed"]
            }
            
            fig = px.pie(
                values=list(status_data.values()),
                names=list(status_data.keys()),
                title="Installation Status",
                color_discrete_sequence=['#10b981', '#e5e7eb']
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Popular plugins
    st.markdown("### 🏆 Most Popular Plugins")
    
    popular_plugins = sorted(plugins, key=lambda x: x.downloads, reverse=True)[:5]
    
    for i, plugin in enumerate(popular_plugins, 1):
        col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
        
        with col1:
            st.markdown(f"**#{i}**")
        with col2:
            st.markdown(f"{plugin.icon} **{plugin.name}**")
        with col3:
            st.markdown(f"{plugin.downloads:,} downloads")
        with col4:
            stars = "⭐" * int(plugin.rating)
            st.markdown(f"{stars} {plugin.rating:.1f}")


# Main render function
def render_plugins_page(user_ctx=None):
    """Main plugins page render function"""
    render_plugin_marketplace()