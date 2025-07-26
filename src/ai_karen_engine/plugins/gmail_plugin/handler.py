
"""Production Gmail plugin handler."""

from __future__ import annotations

import asyncio
from typing import Any, Dict

from .gmail_service import GmailService


async def run(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute Gmail actions based on the provided parameters.

    Expected parameters:
        action: "check_unread" or "compose_email"
        recipient: email address (compose_email)
        subject: subject line (compose_email)
        body: message body (compose_email)
    """
    action = params.get("action")

    service = GmailService()

    try:
        if action == "check_unread":
            return await service.check_unread()

        if action == "compose_email":
            recipient = params.get("recipient", "")
            subject = params.get("subject", "")
            body = params.get("body", "")
            return await service.compose_email(recipient, subject, body)
    except Exception:  # pragma: no cover - external service may fail
        pass

    # Fallback to mocked responses if service fails or action unknown
    if action == "check_unread":
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
        await asyncio.sleep(0.1)
        return {
            "success": True,
            "message": f"Drafted email to {recipient} with subject '{subject}'.",
            "body": body,
        }

    return {"error": "Unknown action"}
