"""
Webhook handlers for triggering workflows from external systems.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException

logger = logging.getLogger(__name__)


async def handle_workflow_webhook(
    workflow_id: str, 
    request: Request, 
    automation_extension
) -> Dict[str, Any]:
    """
    Handle webhook triggers for workflows.
    
    This endpoint allows external systems to trigger workflow execution
    by sending HTTP requests to /automation/webhook/{workflow_id}
    """
    try:
        # Get the workflow
        workflow = automation_extension.workflows.get(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found")
        
        # Check if workflow is active
        if workflow.status.value != "active":
            raise HTTPException(
                status_code=400, 
                detail=f"Workflow '{workflow_id}' is not active (status: {workflow.status.value})"
            )
        
        # Check if workflow has webhook triggers
        has_webhook_trigger = any(
            trigger.get("type") == "webhook" 
            for trigger in workflow.triggers
        )
        
        if not has_webhook_trigger:
            raise HTTPException(
                status_code=400,
                detail=f"Workflow '{workflow_id}' is not configured for webhook triggers"
            )
        
        # Parse webhook payload
        webhook_data = await _parse_webhook_payload(request)
        
        # Log webhook trigger
        logger.info(f"Webhook trigger received for workflow {workflow_id} from {request.client.host}")
        
        # Execute the workflow with webhook data as input
        execution_result = await automation_extension.execute_workflow(
            workflow_id=workflow_id,
            input_data={
                "webhook_data": webhook_data,
                "webhook_headers": dict(request.headers),
                "webhook_source": request.client.host,
                "webhook_timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Return execution result
        response = {
            "success": True,
            "message": f"Workflow '{workflow.name}' triggered successfully",
            "workflow_id": workflow_id,
            "execution_id": execution_result.get("execution_id"),
            "execution_success": execution_result.get("success", False),
            "webhook_timestamp": datetime.utcnow().isoformat()
        }
        
        if not execution_result.get("success"):
            response["execution_error"] = execution_result.get("error")
            response["message"] = f"Workflow '{workflow.name}' triggered but execution failed"
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling webhook for workflow {workflow_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error processing webhook: {str(e)}")


async def _parse_webhook_payload(request: Request) -> Dict[str, Any]:
    """Parse webhook payload from various content types."""
    try:
        content_type = request.headers.get("content-type", "").lower()
        
        if "application/json" in content_type:
            # JSON payload
            try:
                return await request.json()
            except Exception as e:
                logger.warning(f"Failed to parse JSON payload: {e}")
                return {"error": "Invalid JSON payload"}
        
        elif "application/x-www-form-urlencoded" in content_type:
            # Form data
            form_data = await request.form()
            return dict(form_data)
        
        elif "text/" in content_type:
            # Plain text
            text_data = await request.body()
            return {"text": text_data.decode("utf-8")}
        
        else:
            # Raw bytes
            raw_data = await request.body()
            return {
                "raw_data": raw_data.hex(),
                "content_type": content_type,
                "size": len(raw_data)
            }
    
    except Exception as e:
        logger.error(f"Error parsing webhook payload: {e}")
        return {"error": f"Failed to parse payload: {str(e)}"}


async def handle_github_webhook(
    workflow_id: str,
    request: Request,
    automation_extension
) -> Dict[str, Any]:
    """
    Specialized handler for GitHub webhooks.
    
    This handler understands GitHub webhook formats and can extract
    relevant information for workflow execution.
    """
    try:
        # Verify GitHub webhook signature if configured
        github_secret = automation_extension.context.config.get("github_webhook_secret")
        if github_secret:
            signature = request.headers.get("x-hub-signature-256")
            if not signature:
                raise HTTPException(status_code=401, detail="Missing GitHub signature")
            
            # Verify signature (simplified - in production, use proper HMAC verification)
            # This is a placeholder for proper GitHub webhook signature verification
            logger.info(f"GitHub webhook signature verification (placeholder): {signature}")
        
        # Parse GitHub webhook payload
        payload = await request.json()
        
        # Extract GitHub-specific information
        github_data = {
            "event_type": request.headers.get("x-github-event"),
            "delivery_id": request.headers.get("x-github-delivery"),
            "repository": payload.get("repository", {}).get("full_name"),
            "sender": payload.get("sender", {}).get("login"),
            "action": payload.get("action"),
            "payload": payload
        }
        
        # Log GitHub event
        logger.info(f"GitHub webhook: {github_data['event_type']} from {github_data['repository']}")
        
        # Execute workflow with GitHub-specific data
        execution_result = await automation_extension.execute_workflow(
            workflow_id=workflow_id,
            input_data={
                "github": github_data,
                "webhook_timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return {
            "success": True,
            "message": f"GitHub webhook processed for {github_data['repository']}",
            "event_type": github_data["event_type"],
            "execution_id": execution_result.get("execution_id"),
            "execution_success": execution_result.get("success", False)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling GitHub webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"GitHub webhook error: {str(e)}")


async def handle_slack_webhook(
    workflow_id: str,
    request: Request,
    automation_extension
) -> Dict[str, Any]:
    """
    Specialized handler for Slack webhooks and slash commands.
    """
    try:
        # Parse Slack payload (can be form-encoded or JSON)
        content_type = request.headers.get("content-type", "").lower()
        
        if "application/x-www-form-urlencoded" in content_type:
            # Slack slash command or interactive component
            form_data = await request.form()
            slack_data = dict(form_data)
            
            # Handle Slack slash command
            if "command" in slack_data:
                slack_data["type"] = "slash_command"
                slack_data["command_text"] = slack_data.get("text", "")
        else:
            # Slack webhook or event
            slack_data = await request.json()
        
        # Verify Slack token if configured
        slack_token = automation_extension.context.config.get("slack_verification_token")
        if slack_token:
            provided_token = slack_data.get("token")
            if provided_token != slack_token:
                raise HTTPException(status_code=401, detail="Invalid Slack token")
        
        # Extract Slack-specific information
        processed_data = {
            "slack_type": slack_data.get("type", "webhook"),
            "team_id": slack_data.get("team_id"),
            "channel_id": slack_data.get("channel_id"),
            "user_id": slack_data.get("user_id"),
            "user_name": slack_data.get("user_name"),
            "text": slack_data.get("text", ""),
            "payload": slack_data
        }
        
        # Log Slack event
        logger.info(f"Slack webhook: {processed_data['slack_type']} from user {processed_data['user_name']}")
        
        # Execute workflow with Slack-specific data
        execution_result = await automation_extension.execute_workflow(
            workflow_id=workflow_id,
            input_data={
                "slack": processed_data,
                "webhook_timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Return Slack-compatible response
        response = {
            "success": True,
            "message": f"Workflow triggered by Slack user {processed_data['user_name']}",
            "execution_id": execution_result.get("execution_id"),
            "execution_success": execution_result.get("success", False)
        }
        
        # For slash commands, return a user-visible response
        if processed_data["slack_type"] == "slash_command":
            if execution_result.get("success"):
                response["text"] = f"✅ Workflow '{workflow_id}' executed successfully!"
            else:
                response["text"] = f"❌ Workflow '{workflow_id}' failed: {execution_result.get('error', 'Unknown error')}"
            response["response_type"] = "ephemeral"  # Only visible to the user
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling Slack webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Slack webhook error: {str(e)}")


async def handle_generic_api_webhook(
    workflow_id: str,
    request: Request,
    automation_extension,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generic API webhook handler with optional authentication.
    """
    try:
        # Verify API key if provided
        if api_key:
            provided_key = request.headers.get("x-api-key") or request.query_params.get("api_key")
            if provided_key != api_key:
                raise HTTPException(status_code=401, detail="Invalid API key")
        
        # Parse payload
        payload = await _parse_webhook_payload(request)
        
        # Extract request metadata
        request_data = {
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
            "query_params": dict(request.query_params),
            "client_host": request.client.host,
            "payload": payload
        }
        
        # Execute workflow
        execution_result = await automation_extension.execute_workflow(
            workflow_id=workflow_id,
            input_data={
                "api_request": request_data,
                "webhook_timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return {
            "success": True,
            "message": "API webhook processed successfully",
            "workflow_id": workflow_id,
            "execution_id": execution_result.get("execution_id"),
            "execution_success": execution_result.get("success", False),
            "execution_duration": execution_result.get("duration", 0),
            "steps_executed": execution_result.get("steps_executed", 0)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling API webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"API webhook error: {str(e)}")


def register_webhook_routes(router, automation_extension):
    """Register all webhook routes with the FastAPI router."""
    
    @router.post("/webhook/{workflow_id}")
    async def workflow_webhook(workflow_id: str, request: Request):
        """Generic workflow webhook endpoint."""
        return await handle_workflow_webhook(workflow_id, request, automation_extension)
    
    @router.post("/webhook/github/{workflow_id}")
    async def github_webhook(workflow_id: str, request: Request):
        """GitHub-specific webhook endpoint."""
        return await handle_github_webhook(workflow_id, request, automation_extension)
    
    @router.post("/webhook/slack/{workflow_id}")
    async def slack_webhook(workflow_id: str, request: Request):
        """Slack-specific webhook endpoint."""
        return await handle_slack_webhook(workflow_id, request, automation_extension)
    
    @router.post("/webhook/api/{workflow_id}")
    async def api_webhook(workflow_id: str, request: Request, api_key: Optional[str] = None):
        """Generic API webhook with optional authentication."""
        return await handle_generic_api_webhook(workflow_id, request, automation_extension, api_key)