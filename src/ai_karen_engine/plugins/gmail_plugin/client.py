import base64
from typing import Any, Dict, List, Optional

import httpx


class GmailClient:
    """Minimal Gmail API client using an access token."""

    def __init__(self, access_token: str, user_id: str = "me") -> None:
        self.access_token = access_token
        self.user_id = user_id
        self.base_url = "https://gmail.googleapis.com/gmail/v1"

    async def _request(self, method: str, endpoint: str, **kwargs: Any) -> Dict[str, Any]:
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.access_token}"
        url = f"{self.base_url}/users/{self.user_id}/{endpoint}"
        async with httpx.AsyncClient() as client:
            resp = await client.request(method, url, headers=headers, timeout=10, **kwargs)
            resp.raise_for_status()
            return resp.json()

    async def list_unread(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Return a list of unread messages."""
        data = await self._request(
            "GET",
            "messages",
            params={"q": "is:unread", "maxResults": limit, "labelIds": "INBOX"},
        )
        messages = data.get("messages", [])
        results: List[Dict[str, Any]] = []
        for msg in messages:
            mdata = await self._request("GET", f"messages/{msg['id']}")
            snippet = mdata.get("snippet")
            headers = {h["name"]: h["value"] for h in mdata.get("payload", {}).get("headers", [])}
            results.append(
                {
                    "from": headers.get("From", ""),
                    "subject": headers.get("Subject", ""),
                    "snippet": snippet,
                }
            )
        return results

    async def create_draft(self, recipient: str, subject: str, body: str) -> Optional[str]:
        """Create an email draft and return its ID."""
        message = f"To: {recipient}\r\nSubject: {subject}\r\n\r\n{body}"
        encoded = base64.urlsafe_b64encode(message.encode()).decode()
        data = await self._request(
            "POST",
            "drafts",
            json={"message": {"raw": encoded}},
            headers={"Content-Type": "application/json"},
        )
        return data.get("id")
