"""
Insight & Memory Components for Kari AI Streamlit Console
"""

import streamlit as st

def render_insight_zone():
    """Render insight and memory zone with tabs"""
    st.markdown("## Insight & Memory")
    
    tab1, tab2, tab3 = st.tabs(["Reasoning View", "Personal Context", "Plugin Log"])
    
    with tab1:
        render_reasoning_view()
    
    with tab2:
        render_personal_context()
    
    with tab3:
        render_plugin_log()

def render_reasoning_view():
    """Render reasoning view tab with structured traces"""
    st.markdown("### Reasoning Trace")
    
    if st.session_state.reasoning_mode == "Off":
        st.info("Reasoning is currently disabled. Enable it in the sidebar.")
        return
    
    if not st.session_state.conversation_history:
        st.info("Start a conversation to see reasoning traces.")
        return
    
    # Find the last assistant message with reasoning data
    reasoning_message = None
    for message in reversed(st.session_state.conversation_history):
        if message['role'] == 'assistant' and 'metadata' in message:
            reasoning_data = message['metadata'].get('reasoning', {})
            if reasoning_data:
                reasoning_message = message
                break
    
    if not reasoning_message:
        st.info("No reasoning data available for the last message.")
        return
    
    reasoning_data = reasoning_message['metadata'].get('reasoning', {})
    
    # Create expandable sections for different reasoning components
    with st.expander("🧠 Reasoning Overview", expanded=True):
        st.markdown(f"**Model:** {reasoning_data.get('model', 'Unknown')}")
        st.markdown(f"**Reasoning Type:** {reasoning_data.get('type', 'Standard')}")
        st.markdown(f"**Processing Time:** {reasoning_data.get('processing_time', 'N/A')} ms")
        st.markdown(f"**Confidence Score:** {reasoning_data.get('confidence', 'N/A')}")
    
    # Thought Process
    if 'thought_process' in reasoning_data:
        with st.expander("💭 Thought Process", expanded=True):
            for i, thought in enumerate(reasoning_data['thought_process']):
                st.markdown(f"**Step {i+1}:** {thought}")
    
    # Context Analysis
    if 'context_analysis' in reasoning_data:
        with st.expander("🔍 Context Analysis"):
            context_data = reasoning_data['context_analysis']
            
            if 'key_entities' in context_data:
                st.markdown("**Key Entities Identified:**")
                for entity in context_data['key_entities']:
                    st.markdown(f"- {entity}")
            
            if 'user_intent' in context_data:
                st.markdown(f"**User Intent:** {context_data['user_intent']}")
            
            if 'context_relevance' in context_data:
                relevance = context_data['context_relevance']
                st.markdown(f"**Context Relevance:** {relevance.get('score', 'N/A')}/10")
                if 'explanation' in relevance:
                    st.markdown(f"*Explanation:* {relevance['explanation']}")
    
    # Decision Making
    if 'decision_making' in reasoning_data:
        with st.expander("⚖️ Decision Making"):
            decision_data = reasoning_data['decision_making']
            
            if 'alternatives' in decision_data:
                st.markdown("**Alternatives Considered:**")
                for alt in decision_data['alternatives']:
                    st.markdown(f"- {alt}")
            
            if 'chosen_approach' in decision_data:
                st.markdown(f"**Chosen Approach:** {decision_data['chosen_approach']}")
            
            if 'rationale' in decision_data:
                st.markdown(f"**Rationale:** {decision_data['rationale']}")
    
    # Knowledge Retrieval
    if 'knowledge_retrieval' in reasoning_data:
        with st.expander("📚 Knowledge Retrieval"):
            knowledge_data = reasoning_data['knowledge_retrieval']
            
            if 'sources' in knowledge_data:
                st.markdown("**Knowledge Sources Accessed:**")
                for source in knowledge_data['sources']:
                    st.markdown(f"- {source}")
            
            if 'relevant_facts' in knowledge_data:
                st.markdown("**Relevant Facts Retrieved:**")
                for fact in knowledge_data['relevant_facts']:
                    st.markdown(f"- {fact}")
    
    # Plugin Contributions
    if 'plugin_contributions' in reasoning_data:
        with st.expander("🔌 Plugin Contributions"):
            plugin_data = reasoning_data['plugin_contributions']
            
            for plugin_name, contribution in plugin_data.items():
                st.markdown(f"**{plugin_name}:**")
                if 'insights' in contribution:
                    for insight in contribution['insights']:
                        st.markdown(f"- {insight}")
                if 'data_processed' in contribution:
                    st.markdown(f"*Data processed:* {contribution['data_processed']}")
    
    # Raw Reasoning Data (for debugging)
    with st.expander("🔧 Raw Reasoning Data"):
        st.json(reasoning_data)

def render_personal_context():
    """Render enhanced personal context tab"""
    st.markdown("### Personal Context")
    
    # User Profile Section
    with st.expander("👤 User Profile", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Basic Information**")
            st.markdown(f"**Name:** {st.session_state.user_id}")
            st.markdown("**Role:** Creator")
            st.markdown("**Account Type:** Premium")
            st.markdown("**Member Since:** Jan 2023")
        
        with col2:
            st.markdown("**Preferences**")
            st.markdown("**Language:** English")
            st.markdown("**Timezone:** UTC")
            st.markdown("**Theme:** Dark Neon")
            st.markdown("**Notification Level:** All")
    
    # Recent Activity Section
    with st.expander("📊 Recent Activity"):
        activities = [
            {"title": "Created new project", "time": "2 hours ago", "type": "project"},
            {"title": "Updated documentation", "time": "1 day ago", "type": "documentation"},
            {"title": "Completed chat session", "time": "2 days ago", "type": "chat"},
            {"title": "Modified preferences", "time": "3 days ago", "type": "settings"}
        ]
        
        for activity in activities:
            activity_icon = "📝" if activity["type"] == "documentation" else "💬" if activity["type"] == "chat" else "⚙️" if activity["type"] == "settings" else "🚀"
            st.markdown(f"{activity_icon} **{activity['title']}** - {activity['time']}")
    
    # Key Memories Section
    with st.expander("🧠 Key Memories"):
        memories = [
            {"memory": "Prefers concise responses", "context": "General preference", "strength": "High"},
            {"memory": "Working on AI project", "context": "Current project", "strength": "Medium"},
            {"memory": "Interested in machine learning", "context": "Interest area", "strength": "Medium"},
            {"memory": "Uses Python for development", "context": "Technical preference", "strength": "High"}
        ]
        
        for memory in memories:
            strength_color = "#00FF00" if memory["strength"] == "High" else "#FFFF00" if memory["strength"] == "Medium" else "#FF5555"
            st.markdown(f"**{memory['memory']}**")
            st.markdown(f"*Context:* {memory['context']}")
            st.markdown(f"<span style='color: {strength_color}'>Strength: {memory['strength']}</span>", unsafe_allow_html=True)
            st.markdown("---")
    
    # Personal Knowledge Graph
    with st.expander("🕸️ Personal Knowledge Graph"):
        st.markdown("**Key Interests & Expertise**")
        
        interests = {
            "Artificial Intelligence": {"level": "Expert", "connections": ["Machine Learning", "Neural Networks"]},
            "Machine Learning": {"level": "Advanced", "connections": ["AI", "Data Science"]},
            "Python Programming": {"level": "Expert", "connections": ["Software Development", "AI"]},
            "Data Science": {"level": "Intermediate", "connections": ["Machine Learning", "Statistics"]}
        }
        
        for interest, data in interests.items():
            level_color = "#00FF00" if data["level"] == "Expert" else "#FFFF00" if data["level"] == "Advanced" else "#FFAA00"
            st.markdown(f"**{interest}** <span style='color: {level_color}'>({data['level']})</span>", unsafe_allow_html=True)
            st.markdown(f"*Connected to:* {', '.join(data['connections'])}")
            st.markdown("---")
    
    # Personalization Settings
    with st.expander("⚙️ Personalization Settings"):
        st.markdown("**Response Style**")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Formality:** Semi-formal")
            st.markdown("**Detail Level:** Balanced")
            st.markdown("**Tone:** Helpful")
        
        with col2:
            st.markdown("**Creativity:** Medium")
            st.markdown("**Technical Depth:** Medium-High")
            st.markdown("**Example Usage:** Included")
        
        st.markdown("**Content Preferences**")
        preferences = [
            {"preference": "Code Examples", "enabled": True},
            {"preference": "Visual Aids", "enabled": True},
            {"preference": "Step-by-step Explanations", "enabled": True},
            {"preference": "Analogies", "enabled": False}
        ]
        
        for pref in preferences:
            status = "✅" if pref["enabled"] else "❌"
            st.markdown(f"{status} {pref['preference']}")

def render_plugin_log():
    """Render enhanced plugin activity log tab"""
    st.markdown("### Plugin Activity")
    
    # Plugin Overview Section
    with st.expander("📊 Plugin Overview", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Active Plugins**")
            st.markdown("### 3/3")
            st.markdown("All plugins operational")
        
        with col2:
            st.markdown("**Recent Usage**")
            st.markdown("### 12")
            st.markdown("Last 24 hours")
        
        with col3:
            st.markdown("**Success Rate**")
            st.markdown("### 98%")
            st.markdown("Excellent performance")
    
    # Plugin Activity Log
    if st.session_state.conversation_history:
        plugin_log = []
        plugin_stats = {}
        
        for message in st.session_state.conversation_history:
            if message['role'] == 'assistant' and 'metadata' in message:
                metadata = message['metadata']
                if 'plugins' in metadata and metadata['plugins']:
                    for plugin in metadata['plugins']:
                        # Generate random but realistic stats for demo
                        import random
                        execution_time = round(random.uniform(50, 500), 2)
                        status = "success" if random.random() > 0.05 else "error"
                        data_processed = f"{random.randint(1, 100)} KB"
                        
                        log_entry = {
                            "timestamp": message['timestamp'],
                            "plugin": plugin,
                            "status": status,
                            "execution_time": execution_time,
                            "data_processed": data_processed,
                            "message_id": message.get('id', 'unknown')
                        }
                        
                        plugin_log.append(log_entry)
                        
                        # Update stats
                        if plugin not in plugin_stats:
                            plugin_stats[plugin] = {
                                "count": 0,
                                "success_count": 0,
                                "total_time": 0,
                                "last_used": message['timestamp']
                            }
                        
                        plugin_stats[plugin]["count"] += 1
                        plugin_stats[plugin]["total_time"] += execution_time
                        if status == "success":
                            plugin_stats[plugin]["success_count"] += 1
        
        if plugin_log:
            # Plugin Statistics
            with st.expander("📈 Plugin Statistics"):
                for plugin, stats in plugin_stats.items():
                    success_rate = round((stats["success_count"] / stats["count"]) * 100, 1)
                    avg_time = round(stats["total_time"] / stats["count"], 2)
                    
                    st.markdown(f"**{plugin}**")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.markdown(f"Uses: {stats['count']}")
                    with col2:
                        st.markdown(f"Success: {success_rate}%")
                    with col3:
                        st.markdown(f"Avg Time: {avg_time}ms")
                    with col4:
                        st.markdown(f"Last: {stats['last_used']}")
                    st.markdown("---")
            
            # Detailed Activity Log
            with st.expander("📝 Detailed Activity Log"):
                # Show last 10 activities
                for entry in plugin_log[-10:]:
                    status_color = "#00FF00" if entry['status'] == "success" else "#FF5555"
                    status_icon = "✅" if entry['status'] == "success" else "❌"
                    
                    st.markdown(
                        f"{status_icon} **{entry['timestamp']}** - {entry['plugin']} "
                        f"(<span style='color: {status_color}'>{entry['status']}</span>) "
                        f"- {entry['execution_time']}ms - {entry['data_processed']} processed",
                        unsafe_allow_html=True
                    )
        else:
            st.info("No plugin activity yet.")
    else:
        st.info("Start a conversation to see plugin activity.")
    
    # Plugin Configuration
    with st.expander("⚙️ Plugin Configuration"):
        st.markdown("**Available Plugins**")
        
        plugins = [
            {"name": "Web Search", "status": "Active", "version": "1.2.3", "description": "Searches the web for current information"},
            {"name": "Code Execution", "status": "Active", "version": "2.1.0", "description": "Executes code in a secure environment"},
            {"name": "Document Analysis", "status": "Active", "version": "1.5.2", "description": "Analyzes documents and extracts information"}
        ]
        
        for plugin in plugins:
            status_color = "#00FF00" if plugin["status"] == "Active" else "#FF5555"
            st.markdown(f"**{plugin['name']}** <span style='color: {status_color}'>v{plugin['version']}</span>", unsafe_allow_html=True)
            st.markdown(f"*{plugin['description']}*")
            st.markdown("---")

def render_diagnostics_zone():
    """Render enhanced diagnostics zone when debug mode is enabled"""
    if st.session_state.debug_mode:
        st.markdown("## Diagnostics")
        
        # System Overview
        with st.expander("🖥️ System Overview", expanded=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                render_metric_container("0.42s", "Avg Response Time")
            
            with col2:
                render_metric_container("3/3", "Plugins Active")
            
            with col3:
                render_metric_container("100%", "Success Rate")
        
        # Performance Metrics
        with st.expander("📊 Performance Metrics"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Response Time Analysis**")
                st.markdown("- Fastest: 0.21s")
                st.markdown("- Slowest: 1.34s")
                st.markdown("- Average: 0.42s")
                st.markdown("- 95th Percentile: 0.78s")
            
            with col2:
                st.markdown("**Resource Usage**")
                st.markdown("- CPU: 23%")
                st.markdown("- Memory: 1.2GB")
                st.markdown("- GPU: 45%")
                st.markdown("- Network: 12MB/s")
        
        # Model Performance
        with st.expander("🤖 Model Performance"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Model Statistics**")
                st.markdown("- Model: GPT-4")
                st.markdown("- Tokens Processed: 24,532")
                st.markdown("- Avg Tokens/Request: 1,022")
                st.markdown("- Cache Hit Rate: 78%")
            
            with col2:
                st.markdown("**Quality Metrics**")
                st.markdown("- Coherence: 9.2/10")
                st.markdown("- Relevance: 9.5/10")
                st.markdown("- Helpfulness: 9.1/10")
                st.markdown("- Accuracy: 9.3/10")
        
        # Plugin Performance
        with st.expander("🔌 Plugin Performance"):
            plugins = [
                {"name": "Web Search", "calls": 42, "avg_time": "0.32s", "success_rate": "98%"},
                {"name": "Code Execution", "calls": 18, "avg_time": "1.24s", "success_rate": "94%"},
                {"name": "Document Analysis", "calls": 27, "avg_time": "0.87s", "success_rate": "100%"}
            ]
            
            for plugin in plugins:
                st.markdown(f"**{plugin['name']}**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"Calls: {plugin['calls']}")
                with col2:
                    st.markdown(f"Avg Time: {plugin['avg_time']}")
                with col3:
                    st.markdown(f"Success: {plugin['success_rate']}")
                st.markdown("---")
        
        # Error Analysis
        with st.expander("⚠️ Error Analysis"):
            st.markdown("**Recent Errors**")
            errors = [
                {"time": "2 hours ago", "plugin": "Web Search", "error": "Timeout", "resolved": True},
                {"time": "1 day ago", "plugin": "Code Execution", "error": "Syntax Error", "resolved": True},
                {"time": "3 days ago", "plugin": "Document Analysis", "error": "File Format", "resolved": True}
            ]
            
            for error in errors:
                status = "✅ Resolved" if error["resolved"] else "🔴 Unresolved"
                st.markdown(f"**{error['time']}** - {error['plugin']}: {error['error']} ({status})")
            
            st.markdown("**Error Rate by Category**")
            st.markdown("- Timeout: 0.5%")
            st.markdown("- Syntax Error: 0.3%")
            st.markdown("- File Format: 0.2%")
            st.markdown("- Network Issues: 0.1%")
        
        # Last Response Metadata
        with st.expander("🔍 Last Response Metadata"):
            if st.session_state.conversation_history:
                last_message = st.session_state.conversation_history[-1]
                if last_message['role'] == 'assistant' and 'metadata' in last_message:
                    st.json(last_message['metadata'])
            else:
                st.info("No response metadata available.")
        
        # System Logs
        with st.expander("📋 System Logs"):
            logs = [
                {"time": "10:23:45", "level": "INFO", "message": "System initialized successfully"},
                {"time": "10:24:12", "level": "INFO", "message": "User session started"},
                {"time": "10:24:33", "level": "DEBUG", "message": "Processing user input"},
                {"time": "10:24:45", "level": "INFO", "message": "Plugins loaded successfully"},
                {"time": "10:25:02", "level": "DEBUG", "message": "Generating response"},
                {"time": "10:25:18", "level": "INFO", "message": "Response delivered successfully"}
            ]
            
            for log in logs[-10:]:  # Show last 10 logs
                level_color = "#00FF00" if log["level"] == "INFO" else "#FFFF00" if log["level"] == "DEBUG" else "#FF5555"
                st.markdown(f"<span style='color: {level_color}'>{log['time']} [{log['level']}]</span> {log['message']}", unsafe_allow_html=True)

def render_metric_container(value, label):
    """Render a metric container with value and label"""
    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-value">{value}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-label">{label}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)