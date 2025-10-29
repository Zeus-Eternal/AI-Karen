"""
Automation Studio - Main UI for creating and managing prompt-driven workflows.
"""

import streamlit as st
import json
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional


class AutomationStudio:
    """Main UI component for the Automation Studio."""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.extension_api = f"{api_base_url}/api/extensions/prompt-driven-automation"
    
    def render(self):
        """Render the main Automation Studio interface."""
        st.title("⚡ Automation Studio")
        st.markdown("Create AI-powered workflows with natural language")
        
        # Sidebar navigation
        with st.sidebar:
            page = st.selectbox(
                "Navigate",
                ["Create Workflow", "My Workflows", "Templates", "Plugin Discovery", "Analytics"]
            )
        
        # Main content area
        if page == "Create Workflow":
            self._render_create_workflow()
        elif page == "My Workflows":
            self._render_workflow_list()
        elif page == "Templates":
            self._render_templates()
        elif page == "Plugin Discovery":
            self._render_plugin_discovery()
        elif page == "Analytics":
            self._render_analytics()
    
    def _render_create_workflow(self):
        """Render the workflow creation interface."""
        st.header("Create New Workflow")
        
        # Natural language input
        st.subheader("Describe Your Workflow")
        prompt = st.text_area(
            "What would you like to automate?",
            placeholder="Example: Monitor our GitHub repo and notify Slack when tests fail",
            height=100
        )
        
        # Optional settings
        with st.expander("Advanced Settings"):
            workflow_name = st.text_input("Workflow Name (optional)")
            
            # Trigger configuration
            st.subheader("Triggers")
            trigger_type = st.selectbox("Trigger Type", ["Manual", "Schedule", "Webhook", "Event"])
            
            triggers = []
            if trigger_type == "Schedule":
                schedule = st.text_input("Cron Schedule", placeholder="0 9 * * *")
                if schedule:
                    triggers.append({"type": "schedule", "schedule": schedule})
            elif trigger_type == "Webhook":
                triggers.append({"type": "webhook"})
            elif trigger_type == "Event":
                event_type = st.text_input("Event Type", placeholder="github.push")
                if event_type:
                    triggers.append({"type": "event", "event_type": event_type})
            else:
                triggers.append({"type": "manual"})
        
        # Create workflow button
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("🔍 Analyze Workflow", type="secondary"):
                if prompt:
                    with st.spinner("Analyzing your workflow..."):
                        self._analyze_workflow_prompt(prompt)
        
        with col2:
            if st.button("✨ Create Workflow", type="primary"):
                if prompt:
                    with st.spinner("Creating your workflow..."):
                        self._create_workflow(prompt, workflow_name, triggers)
    
    def _render_workflow_list(self):
        """Render the list of existing workflows."""
        st.header("My Workflows")
        
        try:
            response = requests.get(f"{self.extension_api}/workflows")
            if response.status_code == 200:
                data = response.json()
                workflows = data.get("workflows", [])
                
                if not workflows:
                    st.info("No workflows created yet. Create your first workflow!")
                    return
                
                # Workflow filters
                col1, col2, col3 = st.columns([1, 1, 1])
                with col1:
                    status_filter = st.selectbox("Filter by Status", ["All", "Active", "Draft", "Paused", "Failed"])
                with col2:
                    sort_by = st.selectbox("Sort by", ["Created Date", "Name", "Success Rate", "Execution Count"])
                with col3:
                    sort_order = st.selectbox("Order", ["Descending", "Ascending"])
                
                # Filter workflows
                filtered_workflows = workflows
                if status_filter != "All":
                    filtered_workflows = [w for w in workflows if w["status"].lower() == status_filter.lower()]
                
                # Sort workflows
                reverse = sort_order == "Descending"
                if sort_by == "Name":
                    filtered_workflows.sort(key=lambda x: x["name"], reverse=reverse)
                elif sort_by == "Success Rate":
                    filtered_workflows.sort(key=lambda x: x["success_rate"], reverse=reverse)
                elif sort_by == "Execution Count":
                    filtered_workflows.sort(key=lambda x: x["execution_count"], reverse=reverse)
                else:  # Created Date
                    filtered_workflows.sort(key=lambda x: x["created_at"], reverse=reverse)
                
                # Display workflows
                for workflow in filtered_workflows:
                    self._render_workflow_card(workflow)
            
            else:
                st.error(f"Failed to load workflows: {response.status_code}")
        
        except Exception as e:
            st.error(f"Error loading workflows: {str(e)}")
    
    def _render_workflow_card(self, workflow: Dict[str, Any]):
        """Render a single workflow card."""
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                st.subheader(workflow["name"])
                st.write(workflow["description"][:100] + "..." if len(workflow["description"]) > 100 else workflow["description"])
                
                # Status badge
                status = workflow["status"]
                status_color = {
                    "active": "🟢",
                    "draft": "🟡",
                    "paused": "🟠",
                    "failed": "🔴",
                    "completed": "✅"
                }.get(status.lower(), "⚪")
                st.write(f"Status: {status_color} {status.title()}")
            
            with col2:
                st.metric("Executions", workflow["execution_count"])
            
            with col3:
                success_rate = workflow["success_rate"] * 100
                st.metric("Success Rate", f"{success_rate:.1f}%")
            
            with col4:
                if st.button("▶️ Execute", key=f"exec_{workflow['id']}"):
                    self._execute_workflow(workflow["id"])
                
                if st.button("⚙️ Manage", key=f"manage_{workflow['id']}"):
                    self._show_workflow_details(workflow)
            
            st.divider()
    
    def _render_templates(self):
        """Render workflow templates."""
        st.header("Workflow Templates")
        st.markdown("Quick-start templates for common automation scenarios")
        
        try:
            response = requests.get(f"{self.extension_api}/templates")
            if response.status_code == 200:
                data = response.json()
                templates = data.get("templates", {})
                
                if not templates:
                    st.info("No templates available.")
                    return
                
                # Display templates in a grid
                cols = st.columns(2)
                for i, (template_id, template) in enumerate(templates.items()):
                    with cols[i % 2]:
                        with st.container():
                            st.subheader(template["name"])
                            st.write(template["description"])
                            
                            # Show required plugins
                            plugins = template.get("plugins", [])
                            if plugins:
                                st.write("**Required Plugins:**")
                                for plugin in plugins:
                                    st.write(f"• {plugin}")
                            
                            if st.button(f"Use Template", key=f"template_{template_id}"):
                                self._use_template(template_id, template)
                            
                            st.divider()
            
            else:
                st.error(f"Failed to load templates: {response.status_code}")
        
        except Exception as e:
            st.error(f"Error loading templates: {str(e)}")
    
    def _render_plugin_discovery(self):
        """Render plugin discovery interface."""
        st.header("Plugin Discovery")
        st.markdown("Discover plugins that can help with your automation tasks")
        
        # Task description input
        task_description = st.text_area(
            "Describe what you want to accomplish:",
            placeholder="Example: Send notifications to Slack when something happens"
        )
        
        if st.button("🔍 Discover Plugins"):
            if task_description:
                with st.spinner("Discovering suitable plugins..."):
                    self._discover_plugins(task_description)
        
        # Show available plugins
        st.subheader("Available Plugins")
        try:
            response = requests.get(f"{self.extension_api}/plugins")
            if response.status_code == 200:
                data = response.json()
                plugins = data.get("plugins", {})
                
                for plugin_name, plugin_info in plugins.items():
                    with st.expander(f"📦 {plugin_name}"):
                        st.write(f"**Description:** {plugin_info.get('description', 'No description')}")
                        
                        capabilities = plugin_info.get("capabilities", [])
                        if capabilities:
                            st.write("**Capabilities:**")
                            for cap in capabilities:
                                st.write(f"• {cap}")
                        
                        inputs = plugin_info.get("inputs", [])
                        if inputs:
                            st.write("**Inputs:**")
                            for inp in inputs:
                                st.write(f"• {inp}")
                        
                        outputs = plugin_info.get("outputs", [])
                        if outputs:
                            st.write("**Outputs:**")
                            for out in outputs:
                                st.write(f"• {out}")
            
            else:
                st.error(f"Failed to load plugins: {response.status_code}")
        
        except Exception as e:
            st.error(f"Error loading plugins: {str(e)}")
    
    def _render_analytics(self):
        """Render analytics dashboard."""
        st.header("Automation Analytics")
        
        try:
            response = requests.get(f"{self.extension_api}/metrics")
            if response.status_code == 200:
                metrics = response.json()
                
                # Key metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Workflows", metrics["total_workflows"])
                
                with col2:
                    st.metric("Active Workflows", metrics["active_workflows"])
                
                with col3:
                    st.metric("Total Executions", metrics["total_executions"])
                
                with col4:
                    success_rate = metrics["success_rate"] * 100
                    st.metric("Overall Success Rate", f"{success_rate:.1f}%")
                
                # Execution history
                st.subheader("Recent Executions")
                history_response = requests.get(f"{self.extension_api}/execution-history?limit=10")
                if history_response.status_code == 200:
                    history_data = history_response.json()
                    executions = history_data.get("executions", [])
                    
                    if executions:
                        for execution in executions:
                            with st.container():
                                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                                
                                with col1:
                                    st.write(f"**{execution.get('workflow_id', 'Unknown')}**")
                                    st.write(f"Execution ID: {execution.get('execution_id', 'N/A')}")
                                
                                with col2:
                                    status = "✅ Success" if execution.get("success") else "❌ Failed"
                                    st.write(status)
                                
                                with col3:
                                    duration = execution.get("duration", 0)
                                    st.write(f"{duration:.1f}s")
                                
                                with col4:
                                    start_time = execution.get("start_time", "")
                                    if start_time:
                                        dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                                        st.write(dt.strftime("%H:%M:%S"))
                                
                                st.divider()
                    else:
                        st.info("No execution history available.")
            
            else:
                st.error(f"Failed to load metrics: {response.status_code}")
        
        except Exception as e:
            st.error(f"Error loading analytics: {str(e)}")
    
    def _analyze_workflow_prompt(self, prompt: str):
        """Analyze a workflow prompt and show insights."""
        try:
            response = requests.post(
                f"{self.extension_api}/discover",
                params={"task_description": prompt}
            )
            
            if response.status_code == 200:
                result = response.json()
                
                st.success("Workflow Analysis Complete!")
                
                # Show discovered plugins
                plugins = result.get("suitable_plugins", [])
                if plugins:
                    st.subheader("Recommended Plugins")
                    for plugin in plugins[:3]:  # Top 3
                        with st.container():
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.write(f"**{plugin['plugin']}**")
                                st.write(plugin['description'])
                                st.write(f"Matched capabilities: {', '.join(plugin['matched_capabilities'])}")
                            with col2:
                                score = plugin['match_score'] * 100
                                st.metric("Match", f"{score:.0f}%")
                            st.divider()
                
                # Show required capabilities
                capabilities = result.get("required_capabilities", [])
                if capabilities:
                    st.subheader("Required Capabilities")
                    for cap in capabilities:
                        st.write(f"• {cap}")
            
            else:
                st.error(f"Analysis failed: {response.status_code}")
        
        except Exception as e:
            st.error(f"Error analyzing workflow: {str(e)}")
    
    def _create_workflow(self, prompt: str, name: Optional[str] = None, triggers: Optional[List[Dict[str, Any]]] = None):
        """Create a new workflow."""
        try:
            payload = {
                "prompt": prompt,
                "name": name,
                "triggers": triggers
            }
            
            response = requests.post(f"{self.extension_api}/workflows", json=payload)
            
            if response.status_code == 200:
                result = response.json()
                workflow = result.get("workflow", {})
                
                st.success(f"Workflow '{workflow.get('name', 'Unnamed')}' created successfully!")
                
                # Show workflow details
                with st.expander("Workflow Details"):
                    st.json(workflow)
                
                # Show analysis insights
                analysis = result.get("analysis", {})
                if analysis:
                    st.subheader("AI Analysis")
                    st.write(f"**Intent:** {analysis.get('intent', 'Unknown')}")
                    
                    entities = analysis.get("entities", [])
                    if entities:
                        st.write(f"**Entities:** {', '.join(entities)}")
                    
                    template_used = analysis.get("template_used")
                    if template_used:
                        st.write(f"**Template Used:** {template_used}")
            
            else:
                st.error(f"Failed to create workflow: {response.status_code}")
                if response.text:
                    st.error(response.text)
        
        except Exception as e:
            st.error(f"Error creating workflow: {str(e)}")
    
    def _execute_workflow(self, workflow_id: str):
        """Execute a workflow."""
        try:
            payload = {
                "workflow_id": workflow_id,
                "input_data": {},
                "dry_run": False
            }
            
            response = requests.post(f"{self.extension_api}/workflows/{workflow_id}/execute", json=payload)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success"):
                    st.success(f"Workflow executed successfully!")
                    st.write(f"Execution ID: {result.get('execution_id')}")
                    st.write(f"Duration: {result.get('duration', 0):.1f} seconds")
                    st.write(f"Steps executed: {result.get('steps_executed', 0)}")
                else:
                    st.error(f"Workflow execution failed: {result.get('error', 'Unknown error')}")
            
            else:
                st.error(f"Failed to execute workflow: {response.status_code}")
        
        except Exception as e:
            st.error(f"Error executing workflow: {str(e)}")
    
    def _show_workflow_details(self, workflow: Dict[str, Any]):
        """Show detailed workflow information."""
        st.subheader(f"Workflow: {workflow['name']}")
        
        # Basic info
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**ID:** {workflow['id']}")
            st.write(f"**Status:** {workflow['status']}")
            st.write(f"**Created:** {workflow['created_at']}")
        
        with col2:
            st.write(f"**Executions:** {workflow['execution_count']}")
            success_rate = workflow['success_rate'] * 100
            st.write(f"**Success Rate:** {success_rate:.1f}%")
            st.write(f"**Updated:** {workflow['updated_at']}")
        
        # Description and prompt
        st.write(f"**Description:** {workflow['description']}")
        st.write(f"**Original Prompt:** {workflow['prompt']}")
        
        # Steps
        st.subheader("Workflow Steps")
        steps = workflow.get("steps", [])
        for i, step in enumerate(steps, 1):
            with st.expander(f"Step {i}: {step['id']}"):
                st.write(f"**Plugin:** {step['plugin']}")
                st.write(f"**Parameters:** {json.dumps(step['params'], indent=2)}")
                
                if step.get("conditions"):
                    st.write(f"**Conditions:** {json.dumps(step['conditions'], indent=2)}")
                
                if step.get("retry_config"):
                    st.write(f"**Retry Config:** {json.dumps(step['retry_config'], indent=2)}")
        
        # Actions
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("▶️ Execute Now"):
                self._execute_workflow(workflow["id"])
        
        with col2:
            new_status = st.selectbox("Change Status", ["active", "paused", "draft"])
            if st.button("Update Status"):
                self._update_workflow_status(workflow["id"], new_status)
        
        with col3:
            if st.button("🔧 Optimize"):
                self._optimize_workflow(workflow["id"])
    
    def _update_workflow_status(self, workflow_id: str, status: str):
        """Update workflow status."""
        try:
            response = requests.put(f"{self.extension_api}/workflows/{workflow_id}/status", params={"status": status})
            
            if response.status_code == 200:
                st.success(f"Workflow status updated to {status}")
                st.experimental_rerun()
            else:
                st.error(f"Failed to update status: {response.status_code}")
        
        except Exception as e:
            st.error(f"Error updating status: {str(e)}")
    
    def _optimize_workflow(self, workflow_id: str):
        """Optimize a workflow."""
        optimization_goal = st.selectbox("Optimization Goal", ["reliability", "speed", "cost", "accuracy"])
        
        if st.button("Apply Optimization"):
            try:
                response = requests.post(
                    f"{self.extension_api}/workflows/{workflow_id}/optimize",
                    params={"optimization_goal": optimization_goal}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    st.success("Optimization analysis complete!")
                    
                    # Show current performance
                    performance = result.get("current_performance", {})
                    st.subheader("Current Performance")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Executions", performance.get("execution_count", 0))
                    with col2:
                        success_rate = performance.get("success_rate", 0) * 100
                        st.metric("Success Rate", f"{success_rate:.1f}%")
                    with col3:
                        avg_duration = performance.get("avg_duration", 0)
                        st.metric("Avg Duration", f"{avg_duration:.1f}s")
                    
                    # Show optimizations
                    optimizations = result.get("optimizations", [])
                    if optimizations:
                        st.subheader("Recommended Optimizations")
                        for opt in optimizations:
                            st.write(f"**{opt['type']}:** {opt['description']}")
                            if opt.get("config"):
                                st.json(opt["config"])
                
                else:
                    st.error(f"Optimization failed: {response.status_code}")
            
            except Exception as e:
                st.error(f"Error optimizing workflow: {str(e)}")
    
    def _use_template(self, template_id: str, template: Dict[str, Any]):
        """Use a workflow template."""
        st.subheader(f"Using Template: {template['name']}")
        
        # Allow customization
        workflow_name = st.text_input("Workflow Name", value=template["name"])
        workflow_description = st.text_area("Description", value=template["description"])
        
        # Show template structure
        with st.expander("Template Structure"):
            st.json(template.get("template", {}))
        
        if st.button("Create from Template"):
            # Convert template to workflow creation prompt
            prompt = f"Create a workflow based on the {template['name']} template: {template['description']}"
            
            self._create_workflow(prompt, workflow_name)
    
    def _discover_plugins(self, task_description: str):
        """Discover plugins for a task."""
        try:
            response = requests.post(
                f"{self.extension_api}/discover",
                params={"task_description": task_description}
            )
            
            if response.status_code == 200:
                result = response.json()
                
                st.success("Plugin discovery complete!")
                
                plugins = result.get("suitable_plugins", [])
                if plugins:
                    st.subheader("Suitable Plugins")
                    for plugin in plugins:
                        with st.container():
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.write(f"**{plugin['plugin']}**")
                                st.write(plugin['description'])
                                
                                matched_caps = plugin.get('matched_capabilities', [])
                                if matched_caps:
                                    st.write(f"Matched capabilities: {', '.join(matched_caps)}")
                            
                            with col2:
                                score = plugin['match_score'] * 100
                                st.metric("Match Score", f"{score:.0f}%")
                            
                            st.divider()
                else:
                    st.info("No suitable plugins found for this task.")
            
            else:
                st.error(f"Plugin discovery failed: {response.status_code}")
        
        except Exception as e:
            st.error(f"Error discovering plugins: {str(e)}")


# Main entry point for Streamlit
def main():
    """Main entry point for the Automation Studio."""
    studio = AutomationStudio()
    studio.render()


if __name__ == "__main__":
    main()