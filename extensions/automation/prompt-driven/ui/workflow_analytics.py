"""
Workflow Analytics - Advanced analytics and monitoring for automation workflows.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
from typing import Dict, List, Any


class WorkflowAnalytics:
    """Advanced analytics dashboard for workflow monitoring."""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.extension_api = f"{api_base_url}/api/extensions/prompt-driven-automation"
    
    def render(self):
        """Render the analytics dashboard."""
        st.title("📊 Workflow Analytics")
        st.markdown("Advanced monitoring and insights for your automation workflows")
        
        # Load data
        workflows, executions, metrics = self._load_data()
        
        if not workflows and not executions:
            st.info("No data available yet. Create and run some workflows to see analytics.")
            return
        
        # Sidebar filters
        with st.sidebar:
            st.header("Filters")
            
            # Time range filter
            time_range = st.selectbox(
                "Time Range",
                ["Last 24 Hours", "Last 7 Days", "Last 30 Days", "All Time"]
            )
            
            # Workflow filter
            workflow_options = ["All Workflows"] + [w["name"] for w in workflows]
            selected_workflow = st.selectbox("Workflow", workflow_options)
            
            # Status filter
            status_filter = st.multiselect(
                "Execution Status",
                ["Success", "Failed"],
                default=["Success", "Failed"]
            )
        
        # Apply filters
        filtered_executions = self._apply_filters(executions, time_range, selected_workflow, status_filter, workflows)
        
        # Main dashboard
        self._render_overview_metrics(metrics, filtered_executions)
        
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_execution_trends(filtered_executions)
            self._render_workflow_performance(workflows, filtered_executions)
        
        with col2:
            self._render_success_rate_chart(filtered_executions)
            self._render_duration_analysis(filtered_executions)
        
        # Detailed tables
        self._render_workflow_details_table(workflows, filtered_executions)
        self._render_execution_history_table(filtered_executions)
        
        # Performance insights
        self._render_performance_insights(workflows, filtered_executions)
    
    def _load_data(self):
        """Load workflow and execution data."""
        workflows = []
        executions = []
        metrics = {}
        
        try:
            # Load workflows
            response = requests.get(f"{self.extension_api}/workflows")
            if response.status_code == 200:
                workflows = response.json().get("workflows", [])
            
            # Load execution history
            response = requests.get(f"{self.extension_api}/execution-history?limit=1000")
            if response.status_code == 200:
                executions = response.json().get("executions", [])
            
            # Load metrics
            response = requests.get(f"{self.extension_api}/metrics")
            if response.status_code == 200:
                metrics = response.json()
        
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
        
        return workflows, executions, metrics
    
    def _apply_filters(self, executions: List[Dict], time_range: str, selected_workflow: str, status_filter: List[str], workflows: List[Dict]):
        """Apply filters to execution data."""
        filtered = executions.copy()
        
        # Time range filter
        if time_range != "All Time":
            now = datetime.utcnow()
            if time_range == "Last 24 Hours":
                cutoff = now - timedelta(hours=24)
            elif time_range == "Last 7 Days":
                cutoff = now - timedelta(days=7)
            elif time_range == "Last 30 Days":
                cutoff = now - timedelta(days=30)
            
            filtered = [
                e for e in filtered
                if datetime.fromisoformat(e.get("start_time", "").replace("Z", "+00:00")) >= cutoff
            ]
        
        # Workflow filter
        if selected_workflow != "All Workflows":
            # Find workflow ID by name
            workflow_id = None
            for w in workflows:
                if w["name"] == selected_workflow:
                    workflow_id = w["id"]
                    break
            
            if workflow_id:
                filtered = [e for e in filtered if e.get("workflow_id") == workflow_id]
        
        # Status filter
        if status_filter:
            status_map = {"Success": True, "Failed": False}
            allowed_statuses = [status_map[s] for s in status_filter]
            filtered = [e for e in filtered if e.get("success") in allowed_statuses]
        
        return filtered
    
    def _render_overview_metrics(self, metrics: Dict, filtered_executions: List[Dict]):
        """Render overview metrics cards."""
        st.subheader("Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_executions = len(filtered_executions)
            st.metric("Total Executions", total_executions)
        
        with col2:
            successful_executions = len([e for e in filtered_executions if e.get("success")])
            success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0
            st.metric("Success Rate", f"{success_rate:.1f}%")
        
        with col3:
            if filtered_executions:
                avg_duration = sum(e.get("duration", 0) for e in filtered_executions) / len(filtered_executions)
                st.metric("Avg Duration", f"{avg_duration:.1f}s")
            else:
                st.metric("Avg Duration", "0s")
        
        with col4:
            failed_executions = len([e for e in filtered_executions if not e.get("success")])
            st.metric("Failed Executions", failed_executions)
    
    def _render_execution_trends(self, executions: List[Dict]):
        """Render execution trends over time."""
        st.subheader("Execution Trends")
        
        if not executions:
            st.info("No execution data available.")
            return
        
        # Prepare data
        df_data = []
        for execution in executions:
            start_time = execution.get("start_time", "")
            if start_time:
                dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                df_data.append({
                    "timestamp": dt,
                    "success": execution.get("success", False),
                    "duration": execution.get("duration", 0)
                })
        
        if not df_data:
            st.info("No valid execution data for trends.")
            return
        
        df = pd.DataFrame(df_data)
        df["date"] = df["timestamp"].dt.date
        
        # Daily execution counts
        daily_counts = df.groupby(["date", "success"]).size().reset_index(name="count")
        daily_counts["status"] = daily_counts["success"].map({True: "Success", False: "Failed"})
        
        fig = px.bar(
            daily_counts,
            x="date",
            y="count",
            color="status",
            title="Daily Execution Counts",
            color_discrete_map={"Success": "#00CC96", "Failed": "#FF6692"}
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_success_rate_chart(self, executions: List[Dict]):
        """Render success rate over time."""
        st.subheader("Success Rate Trends")
        
        if not executions:
            st.info("No execution data available.")
            return
        
        # Prepare data
        df_data = []
        for execution in executions:
            start_time = execution.get("start_time", "")
            if start_time:
                dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                df_data.append({
                    "timestamp": dt,
                    "success": execution.get("success", False)
                })
        
        if not df_data:
            st.info("No valid execution data for success rate.")
            return
        
        df = pd.DataFrame(df_data)
        df = df.sort_values("timestamp")
        
        # Calculate rolling success rate
        window_size = min(10, len(df))
        df["success_rate"] = df["success"].rolling(window=window_size, min_periods=1).mean() * 100
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["timestamp"],
            y=df["success_rate"],
            mode="lines+markers",
            name="Success Rate",
            line=dict(color="#00CC96", width=2)
        ))
        
        fig.update_layout(
            title="Success Rate Over Time",
            xaxis_title="Time",
            yaxis_title="Success Rate (%)",
            height=400,
            yaxis=dict(range=[0, 100])
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_workflow_performance(self, workflows: List[Dict], executions: List[Dict]):
        """Render workflow performance comparison."""
        st.subheader("Workflow Performance")
        
        if not workflows or not executions:
            st.info("No data available for workflow performance.")
            return
        
        # Calculate performance metrics per workflow
        workflow_metrics = {}
        for workflow in workflows:
            workflow_id = workflow["id"]
            workflow_executions = [e for e in executions if e.get("workflow_id") == workflow_id]
            
            if workflow_executions:
                total_executions = len(workflow_executions)
                successful_executions = len([e for e in workflow_executions if e.get("success")])
                success_rate = (successful_executions / total_executions) * 100
                avg_duration = sum(e.get("duration", 0) for e in workflow_executions) / total_executions
                
                workflow_metrics[workflow["name"]] = {
                    "executions": total_executions,
                    "success_rate": success_rate,
                    "avg_duration": avg_duration
                }
        
        if not workflow_metrics:
            st.info("No workflow execution data available.")
            return
        
        # Create performance chart
        df = pd.DataFrame.from_dict(workflow_metrics, orient="index").reset_index()
        df.columns = ["workflow", "executions", "success_rate", "avg_duration"]
        
        fig = px.scatter(
            df,
            x="avg_duration",
            y="success_rate",
            size="executions",
            hover_name="workflow",
            title="Workflow Performance (Duration vs Success Rate)",
            labels={
                "avg_duration": "Average Duration (seconds)",
                "success_rate": "Success Rate (%)"
            }
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_duration_analysis(self, executions: List[Dict]):
        """Render execution duration analysis."""
        st.subheader("Duration Analysis")
        
        if not executions:
            st.info("No execution data available.")
            return
        
        durations = [e.get("duration", 0) for e in executions if e.get("duration", 0) > 0]
        
        if not durations:
            st.info("No duration data available.")
            return
        
        # Duration distribution
        fig = px.histogram(
            x=durations,
            nbins=20,
            title="Execution Duration Distribution",
            labels={"x": "Duration (seconds)", "y": "Count"}
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Duration statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Min Duration", f"{min(durations):.1f}s")
        
        with col2:
            st.metric("Max Duration", f"{max(durations):.1f}s")
        
        with col3:
            avg_duration = sum(durations) / len(durations)
            st.metric("Avg Duration", f"{avg_duration:.1f}s")
        
        with col4:
            median_duration = sorted(durations)[len(durations) // 2]
            st.metric("Median Duration", f"{median_duration:.1f}s")
    
    def _render_workflow_details_table(self, workflows: List[Dict], executions: List[Dict]):
        """Render detailed workflow table."""
        st.subheader("Workflow Details")
        
        if not workflows:
            st.info("No workflows available.")
            return
        
        # Prepare workflow data with execution stats
        table_data = []
        for workflow in workflows:
            workflow_id = workflow["id"]
            workflow_executions = [e for e in executions if e.get("workflow_id") == workflow_id]
            
            total_executions = len(workflow_executions)
            successful_executions = len([e for e in workflow_executions if e.get("success")])
            success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0
            
            if workflow_executions:
                avg_duration = sum(e.get("duration", 0) for e in workflow_executions) / total_executions
                last_execution = max(workflow_executions, key=lambda x: x.get("start_time", ""))
                last_execution_time = last_execution.get("start_time", "Never")
            else:
                avg_duration = 0
                last_execution_time = "Never"
            
            table_data.append({
                "Name": workflow["name"],
                "Status": workflow["status"].title(),
                "Executions": total_executions,
                "Success Rate": f"{success_rate:.1f}%",
                "Avg Duration": f"{avg_duration:.1f}s",
                "Last Execution": last_execution_time,
                "Created": workflow["created_at"]
            })
        
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True)
    
    def _render_execution_history_table(self, executions: List[Dict]):
        """Render execution history table."""
        st.subheader("Recent Executions")
        
        if not executions:
            st.info("No execution history available.")
            return
        
        # Prepare execution data
        table_data = []
        for execution in executions[:50]:  # Show last 50 executions
            table_data.append({
                "Execution ID": execution.get("execution_id", "N/A"),
                "Workflow": execution.get("workflow_id", "N/A"),
                "Status": "✅ Success" if execution.get("success") else "❌ Failed",
                "Duration": f"{execution.get('duration', 0):.1f}s",
                "Steps": execution.get("steps_executed", 0),
                "Start Time": execution.get("start_time", "N/A"),
                "Error": execution.get("error", "") if not execution.get("success") else ""
            })
        
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True)
    
    def _render_performance_insights(self, workflows: List[Dict], executions: List[Dict]):
        """Render performance insights and recommendations."""
        st.subheader("Performance Insights")
        
        if not workflows or not executions:
            st.info("Insufficient data for insights.")
            return
        
        insights = []
        
        # Analyze workflow performance
        for workflow in workflows:
            workflow_id = workflow["id"]
            workflow_executions = [e for e in executions if e.get("workflow_id") == workflow_id]
            
            if not workflow_executions:
                continue
            
            total_executions = len(workflow_executions)
            successful_executions = len([e for e in workflow_executions if e.get("success")])
            success_rate = (successful_executions / total_executions) * 100
            avg_duration = sum(e.get("duration", 0) for e in workflow_executions) / total_executions
            
            # Generate insights
            if success_rate < 80:
                insights.append({
                    "type": "warning",
                    "workflow": workflow["name"],
                    "message": f"Low success rate ({success_rate:.1f}%). Consider adding retry configurations or reviewing step conditions."
                })
            
            if avg_duration > 300:  # > 5 minutes
                insights.append({
                    "type": "info",
                    "workflow": workflow["name"],
                    "message": f"Long average duration ({avg_duration:.1f}s). Consider optimizing steps or running them in parallel."
                })
            
            if total_executions > 100 and success_rate > 95:
                insights.append({
                    "type": "success",
                    "workflow": workflow["name"],
                    "message": f"Excellent performance! {total_executions} executions with {success_rate:.1f}% success rate."
                })
        
        # Display insights
        if insights:
            for insight in insights:
                if insight["type"] == "warning":
                    st.warning(f"**{insight['workflow']}**: {insight['message']}")
                elif insight["type"] == "info":
                    st.info(f"**{insight['workflow']}**: {insight['message']}")
                elif insight["type"] == "success":
                    st.success(f"**{insight['workflow']}**: {insight['message']}")
        else:
            st.info("No specific insights available. Keep running workflows to generate performance recommendations.")
        
        # General recommendations
        st.subheader("General Recommendations")
        
        total_executions = len(executions)
        if total_executions > 0:
            overall_success_rate = len([e for e in executions if e.get("success")]) / total_executions * 100
            
            recommendations = []
            
            if overall_success_rate < 90:
                recommendations.append("Consider implementing retry mechanisms for critical workflow steps.")
                recommendations.append("Review error patterns and add appropriate error handling.")
            
            if len(workflows) > 5:
                recommendations.append("Consider consolidating similar workflows to reduce maintenance overhead.")
            
            if any(e.get("duration", 0) > 600 for e in executions):  # > 10 minutes
                recommendations.append("Identify long-running workflows and optimize their performance.")
            
            recommendations.append("Regularly review and update workflow templates based on execution patterns.")
            recommendations.append("Set up monitoring alerts for critical workflow failures.")
            
            for i, rec in enumerate(recommendations, 1):
                st.write(f"{i}. {rec}")
        else:
            st.info("Start executing workflows to receive personalized recommendations.")


# Main entry point for Streamlit
def main():
    """Main entry point for Workflow Analytics."""
    analytics = WorkflowAnalytics()
    analytics.render()


if __name__ == "__main__":
    main()