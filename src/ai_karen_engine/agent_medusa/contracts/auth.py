from enum import Enum
from typing import Dict, Set

class AgentPermission(str, Enum):
    """Agent system permissions."""
    # Agent management
    CREATE_AGENT = "create_agent"
    DELETE_AGENT = "delete_agent"
    TERMINATE_AGENT = "terminate_agent"
    VIEW_AGENT = "view_agent"
    MODIFY_AGENT = "modify_agent"
    
    # Execution
    EXECUTE_AGENT = "execute_agent"
    EXECUTE_STREAM = "execute_stream"
    CANCEL_REQUEST = "cancel_request"
    
    # Monitoring
    VIEW_METRICS = "view_metrics"
    VIEW_SYSTEM_METRICS = "view_system_metrics"
    VIEW_LIFECYCLE_EVENTS = "view_lifecycle_events"
    
    # Routing
    VIEW_ROUTING_RECOMMENDATIONS = "view_routing_recommendations"
    CONFIGURE_ROUTING = "configure_routing"

class AgentRole:
    """Agent system roles with associated permissions."""
    ROLES: Dict[str, Set[AgentPermission]] = {
        "viewer": {
            AgentPermission.VIEW_AGENT,
            AgentPermission.EXECUTE_AGENT,
            AgentPermission.VIEW_METRICS,
            AgentPermission.VIEW_ROUTING_RECOMMENDATIONS
        },
        "user": {
            AgentPermission.VIEW_AGENT,
            AgentPermission.EXECUTE_AGENT,
            AgentPermission.EXECUTE_STREAM,
            AgentPermission.CANCEL_REQUEST,
            AgentPermission.VIEW_METRICS,
            AgentPermission.VIEW_ROUTING_RECOMMENDATIONS
        },
        "developer": {
            AgentPermission.VIEW_AGENT,
            AgentPermission.EXECUTE_AGENT,
            AgentPermission.EXECUTE_STREAM,
            AgentPermission.CANCEL_REQUEST,
            AgentPermission.CREATE_AGENT,
            AgentPermission.MODIFY_AGENT,
            AgentPermission.VIEW_METRICS,
            AgentPermission.VIEW_ROUTING_RECOMMENDATIONS,
            AgentPermission.VIEW_LIFECYCLE_EVENTS
        },
        "admin": {
            # All permissions
            AgentPermission.CREATE_AGENT,
            AgentPermission.DELETE_AGENT,
            AgentPermission.TERMINATE_AGENT,
            AgentPermission.VIEW_AGENT,
            AgentPermission.MODIFY_AGENT,
            AgentPermission.EXECUTE_AGENT,
            AgentPermission.EXECUTE_STREAM,
            AgentPermission.CANCEL_REQUEST,
            AgentPermission.VIEW_METRICS,
            AgentPermission.VIEW_SYSTEM_METRICS,
            AgentPermission.VIEW_LIFECYCLE_EVENTS,
            AgentPermission.VIEW_ROUTING_RECOMMENDATIONS,
            AgentPermission.CONFIGURE_ROUTING
        }
    }
