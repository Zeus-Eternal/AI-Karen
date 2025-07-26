"""Gmail plugin for checking unread messages and composing emails."""

from .handler import run
from .gmail_service import GmailService

__all__ = ["run", "GmailService"]
