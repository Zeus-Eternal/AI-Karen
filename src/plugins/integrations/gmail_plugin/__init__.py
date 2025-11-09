"""Gmail plugin for checking unread messages and composing emails."""

from ai_karen_engine.plugins.gmail_plugin.gmail_service import GmailService
from ai_karen_engine.plugins.gmail_plugin.handler import run

__all__ = ["run", "GmailService"]
