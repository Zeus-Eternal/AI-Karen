import pytest

from ai_karen_engine.plugins.gmail_plugin import handler


@pytest.mark.asyncio
async def test_compose_email_fallback(monkeypatch):
    async def fake_compose_email(self, recipient, subject, body):
        raise RuntimeError("service unavailable")

    async def fake_create_draft(self, recipient, subject, body):
        return "draft123"

    monkeypatch.setattr(handler.GmailService, "compose_email", fake_compose_email)
    monkeypatch.setattr(handler.GmailClient, "create_draft", fake_create_draft)

    result = await handler.run(
        {
            "action": "compose_email",
            "recipient": "user@example.com",
            "subject": "Hi",
            "body": "Hello",
            "access_token": "token",
        }
    )

    assert result["success"] is True
    assert result["draftId"] == "draft123"
