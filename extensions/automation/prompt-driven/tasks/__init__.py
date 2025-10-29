"""
Background tasks for the Prompt-Driven Automation Extension.
"""

from .background_tasks import execute_scheduled_workflows, discover_new_plugins

__all__ = ["execute_scheduled_workflows", "discover_new_plugins"]