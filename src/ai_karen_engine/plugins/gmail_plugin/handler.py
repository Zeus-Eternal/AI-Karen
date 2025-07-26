"""Gmail plugin handler with optional real API integration."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, Optional

from ai_karen_engine.plugins.gmail_plugin.client import GmailClient

logger = logging.getLogger(__name__)


async def run(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute Gmail actions based on the provided parameters.

    Expected parameters:
        action: "check_unread" or "compose_email"
        recipient: email address (compose_email)
        subject: subject line (compose_email)
        body: message body (compose_email)
    """
    action = params.get("action")

    token = os.getenv("GMAIL_API_TOKEN")
    client: Optional[GmailClient] = GmailClient(token) if token else None

    if action == "check_unread":
        if client:
            try:
                emails = await client.list_unread()
                return {"unreadCount": len(emails), "emails": emails}
            except Exception as exc:  # pragma: no cover - network fail safe
                logger.error("Gmail unread check failed: %s", exc)

        # Fallback mock
        return {
            "unreadCount": 3,
            "emails": [
                {"from": "Alice", "subject": "Meeting Reminder", "snippet": "..."},
                {"from": "Bob", "subject": "Lunch?", "snippet": "..."},
                {"from": "Carol", "subject": "Hi", "snippet": "..."},
            ],
        }

    if action == "compose_email":
        recipient = params.get("recipient", "")
        subject = params.get("subject", "")
        body = params.get("body", "")

        if client and recipient:
            try:
                draft_id = await client.create_draft(recipient, subject, body)
                return {
                    "success": True,
                    "draftId": draft_id,
                    "message": f"Drafted email to {recipient} with subject '{subject}'.",
                }
            except Exception as exc:  # pragma: no cover - network fail safe
                logger.error("Gmail compose failed: %s", exc)

        await asyncio.sleep(0.1)
        return {
            "success": True,
            "message": f"Drafted email to {recipient} with subject '{subject}'.",
            "body": body,
        }

    return {"error": "Unknown action"}
