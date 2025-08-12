"""
Workflow Builder Extension - AI-Powered Automation

This extension provides the foundation for prompt-driven automation,
allowing users to create complex workflows using natural language.
"""

from ai_karen_engine.extensions.base import BaseExtension

try:
    from fastapi import APIRouter
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    APIRouter = object


class WorkflowBuilderExtension(BaseExtension):
    """
    AI-powered workflow builder extension.
    
    This extension demonstrates how to build complex automation workflows
    using natural language prompts and MCP tool discovery.
    """
    
    async def _initialize(self) -> None:
        """Initialize the Workflow Builder Extension."""
        self.logger.info("Workflow Builder Extension initializing...")
        
        # Initialize workflow storage
        self.workflows = {}
        self.workflow_executions = {}
        
        # Set up MCP tools for workflow building
        await self._setup_workflow_mcp_tools()
        
        self.logger.info("Workflow Builder Extension initialized successfully")
    
    async def _setup_workflow_mcp_tools(self) -> None:
        """Set up MCP tools for workflow building."""
        mcp_server = self.create_mcp_server()
        if mcp_server:
            # Register workflow creation tool
            await self.register_mcp_tool(
                name="create_workflow",
                handler=self._create_workflow_tool,
                schema={
                    "type": "object",
                    "properties": {
                        "description": {"type": "string", "description": "Natural language description of the workflow"},
                        "name": {"type": "string", "description": "Workflow name"},
                        "trigger": {"type": "string", "enum": ["manual", "scheduled", "webhook"], "default": "manual"}
                    },
                    "required": ["description", "name"]
                },
                description="Create a new workflow from natural language description"
            )
            
            # Register workflow execution tool
            await self.register_mcp_tool(
                name="execute_workflow",
                handler=self._execute_workflow_tool,
                schema={
                    "type": "object",
                    "properties": {
                        "workflow_id": {"type": "string", "description": "ID of the workflow to execute"},
                        "parameters": {"type": "object", "description": "Workflow execution parameters"}
                    },
                    "required": ["workflow_id"]
                },
                description="Execute a workflow with optional parameters"
            )
            
            # Register tool discovery for workflow building
            await self.register_mcp_tool(
                name="discover_automation_tools",
                handler=self._discover_automation_tools,
                schema={
                    "type": "object",
                    "properties": {
                        "category": {"type": "string", "description": "Tool category to filter by"}
                    }
                },
                description="Discover available tools for workflow automation"
            )
    
    async def _create_workflow_tool(self, description: str, name: str, trigger: str = "manual") -> dict:
        """MCP tool to create workflows from natural language."""
        workflow_id = f"workflow_{len(self.workflows) + 1}"
        
        # This is where the AI magic happens - parse natural language into workflow steps
        # For now, we'll create a simple mock workflow
        workflow = {
            "id": workflow_id,
            "name": name,
            "description": description,
            "trigger": trigger,
            "steps": await self._parse_workflow_description(description),
            "created_at": "2024-01-01T00:00:00Z",
            "status": "active"
        }
        
        self.workflows[workflow_id] = workflow
        
        return {
            "workflow_id": workflow_id,
            "name": name,
            "description": description,
            "steps_count": len(workflow["steps"]),
            "message": f"Workflow '{name}' created successfully"
        }
    
    async def _execute_workflow_tool(self, workflow_id: str, parameters: dict = None) -> dict:
        """MCP tool to execute workflows."""
        if workflow_id not in self.workflows:
            return {"error": f"Workflow {workflow_id} not found"}
        
        workflow = self.workflows[workflow_id]
        execution_id = f"exec_{len(self.workflow_executions) + 1}"
        
        # Execute workflow steps using plugin orchestration
        try:
            results = []
            for step in workflow["steps"]:
                # Use plugin orchestrator to execute each step
                result = await self.plugin_orchestrator.execute_plugin(
                    intent=step["plugin"],
                    params=step.get("parameters", {}),
                    user_context={"roles": ["user"]}
                )
                results.append({
                    "step": step["name"],
                    "result": result,
                    "status": "completed"
                })
            
            execution = {
                "id": execution_id,
                "workflow_id": workflow_id,
                "status": "completed",
                "results": results,
                "executed_at": "2024-01-01T00:00:00Z"
            }
            
            self.workflow_executions[execution_id] = execution
            
            return {
                "execution_id": execution_id,
                "workflow_id": workflow_id,
                "status": "completed",
                "steps_executed": len(results),
                "message": "Workflow executed successfully"
            }
            
        except Exception as e:
            return {
                "execution_id": execution_id,
                "workflow_id": workflow_id,
                "status": "failed",
                "error": str(e),
                "message": "Workflow execution failed"
            }
    
    async def _discover_automation_tools(self, category: str = None) -> dict:
        """MCP tool to discover available automation tools."""
        # Discover MCP tools from other extensions
        available_tools = await self.discover_mcp_tools()
        
        # Filter by category if specified
        if category:
            filtered_tools = {}
            for service, tools in available_tools.items():
                if category.lower() in service.lower():
                    filtered_tools[service] = tools
            available_tools = filtered_tools
        
        return {
            "category": category,
            "services_found": len(available_tools),
            "tools": available_tools,
            "message": f"Discovered {len(available_tools)} automation services"
        }
    
    async def _parse_workflow_description(self, description: str) -> list:
        """
        Parse natural language description into workflow steps.
        
        This is where the AI magic would happen - for now, we'll create
        a simple mock workflow based on keywords.
        """
        steps = []
        
        # Simple keyword-based parsing (in reality, this would use LLM)
        if "github" in description.lower():
            steps.append({
                "name": "Monitor GitHub",
                "plugin": "github_monitor",
                "parameters": {"repository": "main"}
            })
        
        if "test" in description.lower():
            steps.append({
                "name": "Run Tests",
                "plugin": "test_runner",
                "parameters": {"command": "npm test"}
            })
        
        if "slack" in description.lower() or "notify" in description.lower():
            steps.append({
                "name": "Send Notification",
                "plugin": "slack_notifier",
                "parameters": {"channel": "#general"}
            })
        
        # Default step if no keywords matched
        if not steps:
            steps.append({
                "name": "Hello World",
                "plugin": "hello_world",
                "parameters": {"message": "Workflow executed"}
            })
        
        return steps
    
    def create_api_router(self):
        """Create API routes for the Workflow Builder."""
        if not FASTAPI_AVAILABLE:
            return None
        
        router = APIRouter(prefix=f"/api/extensions/{self.manifest.name}")
        
        @router.get("/workflows")
        async def list_workflows():
            """List all workflows."""
            return {
                "workflows": list(self.workflows.values()),
                "total": len(self.workflows)
            }
        
        @router.post("/workflows")
        async def create_workflow(workflow_data: dict):
            """Create a new workflow."""
            return await self._create_workflow_tool(
                description=workflow_data.get("description", ""),
                name=workflow_data.get("name", "Untitled Workflow"),
                trigger=workflow_data.get("trigger", "manual")
            )
        
        @router.post("/workflows/{workflow_id}/execute")
        async def execute_workflow(workflow_id: str, parameters: dict = None):
            """Execute a workflow."""
            return await self._execute_workflow_tool(workflow_id, parameters or {})
        
        @router.get("/tools/discover")
        async def discover_tools(category: str = None):
            """Discover available automation tools."""
            return await self._discover_automation_tools(category)
        
        return router


# Export the extension class
__all__ = ["WorkflowBuilderExtension"]